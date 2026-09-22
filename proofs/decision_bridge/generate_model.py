"""Frozen byte-template derivation: only the two scenario inserts are generated."""
import json
from bridge import MODEL, VERSION, digest, generate, relative_file

TEMPLATE_SHA256 = "e6ffbd5acebd3aa1f05ea7942c4f7eb23d4469357c7a01fea082de2b2e8ab121"


def derive_model(result_bytes):
    result = json.loads(result_bytes)
    fragment = generate(result)
    if fragment is None:
        raise ValueError("Frozen consequence template requires Deny/Allow decision pair")
    source = relative_file(MODEL).read_bytes()
    if digest(source) != TEMPLATE_SHA256:
        raise ValueError("Frozen template hash mismatch")
    eol = b"\r\n" if b"\r\n" in source else b"\n"
    statements = [line for line in fragment.splitlines() if line.startswith("insert ")]
    if len(statements) != 2:
        raise ValueError("Expected exactly two derived scenario inserts")
    block = eol.join(b"  " + line.encode("ascii") for line in statements) + eol
    if source.count(block) != 1:
        raise ValueError("Scenario block missing or ambiguous")
    # Deliberately equal to the old case: decisions are now computed, not hand supplied.
    body = source.replace(block, block, 1)
    if body != source:
        raise ValueError("Unexpected change outside scenario derivation")
    header = (f"(* Derived by {VERSION}; no Python refinement claim.\n"
              f"evaluation_fingerprint: {result['evaluation_fingerprint']}\n"
              f"bridge_result_sha256: {digest(result_bytes)}\n"
              f"source_model: {MODEL}\nsource_model_sha256: {TEMPLATE_SHA256}\n"
              "Scenario inserts checked against the independently derived decision pair.\n*)\n").encode("ascii")
    return header + body
