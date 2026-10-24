"""Bounded probes of unchanged upstream SAGA methods; no live services.

Uses real Agent initialization, original handlers/framing, local certificates and
original token cryptography. CA/provider certificate discovery and byte transport
are substituted. The Provider database and real TLS are not executed. A trace
barrier controls a legal thread schedule without replacing quota checks/debits.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import saga.config as config
import saga.common.crypto as sc
from saga.agent import Agent
from saga.local_agent import LocalAgent
from proofs.consumer_validation.fixtures import make_ca, make_material, b64

UPSTREAM = "7372111bea150e32cee390a616849316d2780bfc"
SOURCES = ["saga/agent.py", "saga/config.py", "saga/common/crypto.py",
           "saga/provider/provider.py", "saga/common/contact_policy.py"]


class CountingAgent(LocalAgent):
    task_finished_token = "<TASK_FINISHED>"

    def __init__(self):
        self.calls = 0
        self.lock = threading.Lock()

    def run(self, *args, **kwargs):
        with self.lock:
            self.calls += 1
        return None, "continue"


class MemoryConnection:
    def __init__(self, frames, peer_cert):
        self.incoming = b"".join(self.frame(frame) for frame in frames)
        self.peer_cert = peer_cert
        self.sent = []

    @staticmethod
    def frame(payload):
        encoded = json.dumps(payload).encode()
        return len(encoded).to_bytes(4, "big") + encoded

    def recv(self, size):
        result, self.incoming = self.incoming[:size], self.incoming[size:]
        return result

    def sendall(self, data):
        assert int.from_bytes(data[:4], "big") == len(data) - 4
        self.sent.append(json.loads(data[4:]))

    def getpeercert(self, binary_form=False):
        assert binary_form
        return self.peer_cert

    def shutdown(self, how):
        pass

    def close(self):
        pass


@contextmanager
def fixture():
    ca = make_ca()
    private, public = sc.generate_ed25519_keypair()
    provider = SimpleNamespace(SK_Prov=private, PK_Prov=public,
                              cert=ca.sign(public, {"COMMON_NAME": "probe-provider"}))
    rules = [{"pattern": "*", "budget": 10}]
    with tempfile.TemporaryDirectory(prefix="saga-qmax-") as temporary, \
            patch("saga.agent.get_SAGA_CA", return_value=ca), \
            patch.object(Agent, "get_provider_cert", return_value=provider.cert):
        agents = []
        materials = []
        for role in ("receiver", "initiator"):
            material, _, _ = make_material(f"{role}@example.com:agent", rules, ca, provider)
            directory = Path(temporary) / role
            directory.mkdir()
            agents.append(Agent(str(directory), material, CountingAgent()))
            materials.append(material)
        a, b = agents
        # Empty issuance connections do not run an LLM. Seed only the timing
        # record read by the native handler's logging epilogue.
        for endpoint in agents:
            for label in ("agent:llm_backend_recv", "agent:llm_backend_init"):
                endpoint.llm_monitor.start(label)
                endpoint.llm_monitor.stop(label)
        a_material, _ = materials
        base = {"card": copy.deepcopy(b.card), "stamp": b.stamp,
                "crt_u": b64(b.crt_u.public_bytes(sc.serialization.Encoding.PEM))}
        peer_cert = b.cert.public_bytes(sc.serialization.Encoding.DER)
        yield a, b, a_material, base, peer_cert


def issue(a, b, a_material, base, peer_cert, quota=50):
    initial = {**copy.deepcopy(base), "otk": a_material["otks"][0]}
    connection = MemoryConnection([initial], peer_cert)
    with patch.object(config, "Q_MAX", quota):
        a.handle_i_agent_connection(connection, ("127.0.0.1", 23456))
    assert len(connection.sent) == 1 and set(connection.sent[0]) == {"token"}
    token = connection.sent[0]["token"]
    public_otk = sc.bytesToPublicX25519Key(base64.b64decode(a_material["otks"][0]))
    shared = sc.HKDF(algorithm=sc.hashes.SHA256(), length=32, salt=None,
                     info=b"access-control-shdk-exchange").derive(b.sac.exchange(public_otk))
    b.store_received_token(a.aid, token, sc.decrypt_token(token, shared))
    assert a.token_is_valid(token, b.pac) == (quota != 0)
    return token, shared


def session(a, token, base, peer_cert, requests):
    frames = [{**copy.deepcopy(base), "token": token}]
    frames.extend({"msg": f"request-{number}", "token": token} for number in range(requests))
    connection = MemoryConnection(frames, peer_cert)
    a.handle_i_agent_connection(connection, ("127.0.0.1", 23456))
    return connection


def serial_control():
    with fixture() as (a, b, material, base, certificate):
        token, shared = issue(a, b, material, base, certificate)
        session(a, token, base, certificate, 51)
        result = {"issued_quota": 50, "requests_submitted": 51,
                  "backend_calls": a.local_agent.calls,
                  "remaining": a.active_tokens[token]["communication_quota"],
                  "encrypted_initial_quota": sc.decrypt_token(token, shared)["communication_quota"]}
        assert result["backend_calls"] == 50 and result["remaining"] == 0
        assert result["encrypted_initial_quota"] == 50
        return result


def parallel_last_credit():
    with fixture() as (a, b, material, base, certificate):
        token, _ = issue(a, b, material, base, certificate)
        session(a, token, base, certificate, 49)
        assert a.local_agent.calls == 49
        assert a.active_tokens[token]["communication_quota"] == 1
        barrier = threading.Barrier(2, timeout=5)
        checked = []
        paused_threads = set()
        errors = []
        debit_line = next(number for number, text in enumerate(
            (ROOT / "saga/agent.py").read_text(encoding="utf-8").splitlines(), 1)
            if text.strip() == "with self.active_tokens_lock:" and 600 <= number <= 610)

        def trace(frame, event, arg):
            if (event == "line" and frame.f_code is Agent.receive_conversation.__code__
                    and frame.f_lineno == debit_line
                    and threading.get_ident() not in paused_threads):
                # CPython can report the with-statement line again on exit.
                paused_threads.add(threading.get_ident())
                checked.append({"thread": threading.current_thread().name,
                                "remaining_after_successful_check":
                                a.active_tokens[token]["communication_quota"]})
                barrier.wait()
            return trace

        def worker():
            try:
                session(a, token, base, certificate, 1)
            except BaseException as error:
                errors.append(type(error).__name__ + ": " + str(error))

        threading.settrace(trace)
        workers = [threading.Thread(target=worker, name=f"connection-{i}", daemon=True)
                   for i in (1, 2)]
        try:
            for worker_thread in workers:
                worker_thread.start()
            for worker_thread in workers:
                worker_thread.join(10)
        finally:
            threading.settrace(None)
        assert not any(worker_thread.is_alive() for worker_thread in workers)
        assert not errors, errors
        result = {"issued_quota": 50, "sequential_backend_calls": 49,
                  "controlled_schedule": checked,
                  "total_backend_calls": a.local_agent.calls,
                  "remaining": a.active_tokens[token]["communication_quota"],
                  "errors": errors}
        assert len(checked) == 2 and all(item["remaining_after_successful_check"] == 1
                                       for item in checked)
        assert result["total_backend_calls"] == 51 and result["remaining"] == 0
        return result


def oversized_initial_quota():
    with fixture() as (a, b, material, base, certificate):
        token, _ = issue(a, b, material, base, certificate, quota=999)
        result = {"issuer_initial_quota": 999, "initiator_local_q_max": config.Q_MAX,
                  "initiator_stored_quota": b.received_tokens[token]["communication_quota"],
                  "initiator_validates_token": b.received_token_is_valid(token)}
        assert result["initiator_local_q_max"] == 50
        assert result["initiator_stored_quota"] == 999
        assert result["initiator_validates_token"]
        return result


def local_inflation_control():
    with fixture() as (a, b, material, base, certificate):
        token, shared = issue(a, b, material, base, certificate)
        b.received_tokens[token]["communication_quota"] = 999
        session(a, token, base, certificate, 51)
        result = {"initiator_modified_quota": 999, "receiver_backend_calls": a.local_agent.calls,
                  "receiver_remaining": a.active_tokens[token]["communication_quota"]}
        assert result["receiver_backend_calls"] == 50
        fresh = base64.b64encode(a.generate_token(b.pac, shared)).decode()
        result["new_ciphertext_with_valid_shared_key_accepted"] = a.token_is_valid(fresh, b.pac)
        assert not result["new_ciphertext_with_valid_shared_key_accepted"]
        return result


def delivery_gap():
    with fixture() as (a, b, material, base, certificate):
        token, _ = issue(a, b, material, base, certificate)
        # sendall completes in the substitute, but no request is delivered to A.
        connection = MemoryConnection([], certificate)
        b.initiate_conversation(connection, token, a.aid, "request-without-response")
        result = {"successful_local_writes": len(connection.sent),
                  "initiator_remaining": b.received_tokens[token]["communication_quota"],
                  "receiver_remaining": a.active_tokens[token]["communication_quota"],
                  "receiver_backend_calls": a.local_agent.calls}
        assert result == {"successful_local_writes": 1, "initiator_remaining": 49,
                          "receiver_remaining": 50, "receiver_backend_calls": 0}
        return result


def negative_configuration():
    with fixture() as (a, b, material, base, certificate):
        token, _ = issue(a, b, material, base, certificate, quota=-1)
        session(a, token, base, certificate, 2)
        result = {"configured_quota": -1, "backend_calls": a.local_agent.calls,
                  "remaining": a.active_tokens[token]["communication_quota"]}
        assert result["backend_calls"] == 1 and result["remaining"] == 0
        return result


def main():
    subprocess.run(["git", "diff", "--exit-code", UPSTREAM, "--", *SOURCES],
                   cwd=ROOT, check=True, capture_output=True)
    before = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
    native_errors = io.StringIO()
    with redirect_stdout(io.StringIO()), redirect_stderr(native_errors):
        cases = {"serial_control": serial_control(),
                 "parallel_last_credit": [parallel_last_credit() for _ in range(3)],
                 "oversized_initial_quota": oversized_initial_quota(),
                 "local_inflation_control": local_inflation_control(),
                 "delivery_gap": delivery_gap(),
                 "negative_configuration": negative_configuration()}
    assert not native_errors.getvalue(), native_errors.getvalue()
    after = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
    assert before == after
    result = {"upstream_commit": UPSTREAM, "python": sys.version, "executable": sys.executable,
              "source_sha256": before, "source_unchanged": True,
              "helper_sha256": hashlib.sha256((ROOT / "proofs/consumer_validation/fixtures.py").read_bytes()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "native_exception_output_empty": True,
              "scope": "Real native methods and local credential checks; substituted byte transport, "
                       "certificate discovery and counting backend; no Provider DB, live TLS, "
                       "real LLM, deployment claim or formal proof. Trace barrier selects a legal "
                       "schedule after native validation returns and before debit lock acquisition.",
              "cases": cases, "all_assertions_passed": True}
    output = Path(__file__).with_name("results.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_assertions_passed": True, "cases": cases, "results": str(output)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
