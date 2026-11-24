import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_model import execute
dest=Path(__file__).resolve().parent/'bfs-probe'
dest.mkdir(exist_ok=False)
model=Path(__file__).resolve().parents[1]/'evidence/20261124T105749966670Z/models/da.spthy'
print(execute(['tamarin-prover','--quit-on-warning','--derivcheck-timeout=30',
 '--stop-on-trace=BFS','--prove=evaluation_reachable',f'--output={dest / "proof.spthy"}',
 str(model),'+RTS','-N2','-RTS'],dest,'verify',45))
