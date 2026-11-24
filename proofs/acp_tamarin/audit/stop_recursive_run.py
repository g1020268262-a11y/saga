"""Stop only this module's diagnosed nonterminating search; retain its output."""
import json,os,signal,time
from pathlib import Path
archive=Path(__file__).resolve().parents[1]/'evidence/20261124T105749966670Z'
stopped=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit(): continue
    try: args=(proc/'cmdline').read_bytes().split(b'\0')
    except OSError: continue
    if b'proofs/acp_tamarin/run_model.py' in args and args[0].endswith(b'python3'):
        os.kill(int(proc.name),signal.SIGTERM); stopped.append({'pid':int(proc.name),'kind':'runner'})
    elif args and args[0].endswith(b'tamarin-prover') and any(str(archive).encode() in a for a in args):
        os.killpg(int(proc.name),signal.SIGKILL); stopped.append({'pid':int(proc.name),'kind':'native_search_group'})
record={'native_complete':False,'reason':'Recursive generic Scan search did not converge; BFS reachability probe also timed out after 45s. Stopped for structural search diagnosis, no verdict inferred.','stopped':stopped,'time_unix':time.time()}
(archive/'interrupted.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
