#!/usr/bin/env python3
"""Generate bounded ACP theories, check provenance and run native Tamarin.
Python preview is a separate finite replay, never a Tamarin proof.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))
CASES = DATA['cases']
IDENT = re.compile(r'[a-z0-9._+-]+@[a-z0-9.-]+:[a-z0-9._+-]+\Z')
EXISTS = {'evaluation_reachable', 'provider_rejection_reachable',
          'receiver_evaluation_reachable', 'provider_release_reachable',
          'token_issue_reachable', 'chat_accept_reachable', 'denied_chat_reachable'}
SAFETY = {'spec_matches_reference', 'provider_matches_observation',
          'receiver_matches_observation', 'policy_budget_agreement',
          'provider_issue_requires_policy_allow', 'token_issue_requires_policy_allow',
          'chat_requires_policy_allow', 'chat_requires_token_issue', 'chat_requires_decryption'}
LEMMA_TYPES = {**{k:'exists-trace' for k in EXISTS}, **{k:'all-traces' for k in SAFETY}}
RESULT_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s+\((all-traces|exists-trace)\):\s*(verified|falsified|analysis incomplete)\b', re.M)

def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def write_json(path, obj): path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
def git(root, *args): return subprocess.check_output(['git','-C',str(root),*args])

def validate_repo(root):
    """Use the repository's existing checked decision bridge on original bytes."""
    root = root.resolve()
    commit = git(root,'rev-parse','HEAD').decode().strip()
    source = root / DATA['source_path']
    raw = source.read_bytes()
    lf = raw.replace(b'\r\n',b'\n')
    if not any(blob(x)==DATA['source_blob'] for x in (raw,lf,lf.replace(b'\n',b'\r\n'))):
        raise ValueError('Current matcher differs from the audited source')
    bridge_path = root/'proofs/decision_bridge/bridge.py'
    spec = importlib.util.spec_from_file_location('saga_acp_bridge',bridge_path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    results = {}
    for name, case in CASES.items():
        path = root/case['path']; data = path.read_bytes()
        if blob(data)!=case['blob']:
            raise ValueError(f'{name}: archived bytes do not match the audited Git blob')
        record=json.loads(data)
        ctx=mod.make_context(case['rules'], DATA['aid'], record['source_sha256'], record['base_commit'], 'acp-'+name)
        obs={'path':case['path'],'sha256':sha(data),'format':case['format']}
        if 'field' in case: obs['field']=case['field']
        pair=mod.build(ctx,obs)
        if pair['status']!='OK' or pair['spec']['budget']!=case['spec'] or pair['impl_observed']['budget']!=case['observed']:
            raise ValueError(f'{name}: checked bridge results differ from the audited inputs')
        results[name]=pair
    return {'repository_head':commit,'source_sha256':sha(raw),'bridge_sha256':sha(bridge_path.read_bytes()),'checked_decision_pairs':results}

def matching_rules(aid, rules):
    if not IDENT.fullmatch(aid): raise ValueError('Unsupported AID')
    matches=[]
    for r in rules:
        p,b=r['pattern'],r['budget']
        if type(b) is not int or b < -1: raise ValueError('Unsupported budget')
        if p=='*': rank,match=0,True
        elif IDENT.fullmatch(p):
            u,n=p.split(':'); rank,match=4*len(u)+8*len(n),p==aid
        elif p.endswith(':*') and IDENT.fullmatch(p[:-1]+'x'):
            u=p[:-2]; rank,match=4*len(u)+2,aid.split(':')[0]==u
        else: raise ValueError(f'Unsupported pattern: {p}')
        if match: matches.append((rank,b))
    if matches and sum(rank==max(x[0] for x in matches) for rank,_ in matches)>1:
        raise ValueError('Tied highest score')
    return matches

def bterm(b): return "'bneg1'" if b==-1 else f"'b{b}'"
def rterm(r): return "'rinit'" if r==-1 else f"'r{r}'"
def dterm(b): return "'allow'" if b>0 else "'deny'"

def generate(name, case):
    matches=matching_rules(DATA['aid'],case['rules'])
    term="'end'"
    for rank,b in reversed(matches): term=f'<<{rterm(rank)},{bterm(b)}>,{term}>'
    ranks=sorted({-1,0,70,*[r for r,b in matches]})
    # Encode concrete numeric comparison results, not policy outputs.
    facts=[f"!{'Higher' if r>s else 'NotHigher'}({rterm(r)},{rterm(s)})" for r in ranks if r>=0 for s in ranks]
    for b in sorted({-1,0,10,*[b for r,b in matches]}):
        facts.append(f'!Decision({bterm(b)},{dterm(b)})')
        facts.append(f"!{'ReceiverAllows' if b>=0 else 'ReceiverDenies'}({bterm(b)})")
        if b>0: facts.append(f'!Debit({bterm(b)},{bterm(b-1)})')
    substitutions={'THEORY':'Saga_ACP_'+name,'RULES':term,'FACTS':',\n    '.join(facts),
                   'IMPL_BEST':'best','SPEC':bterm(case['spec']),'SPEC_DEC':dterm(case['spec']),'OBS':bterm(case['observed'])}
    template=(HERE/'contact_policy.template.spthy').read_text(encoding='utf-8')
    for k,v in substitutions.items(): template=template.replace('@'+k+'@',v)
    if re.search(r'@[A-Z_]+@',template): raise ValueError('Unexpanded template')
    return template

def expected(case):
    allow=case['observed']>0; spec_allow=case['spec']>0
    same=case['spec']==case['observed']
    truth={k:True for k in SAFETY}
    truth['policy_budget_agreement']=same
    for k in ('provider_issue_requires_policy_allow','token_issue_requires_policy_allow','chat_requires_policy_allow'):
        truth[k]=not allow or spec_allow
    truth.update(evaluation_reachable=True,provider_rejection_reachable=not allow,
                 receiver_evaluation_reachable=allow,provider_release_reachable=allow,
                 token_issue_reachable=allow,chat_accept_reachable=allow,
                 denied_chat_reachable=allow and not spec_allow)
    return {k:{'type':LEMMA_TYPES[k],'expected':'verified' if v else 'falsified'} for k,v in sorted(truth.items())}

def finite_replay(case):
    """Concrete linear trace for the closed rulebook/one-OTK model.
    This is not a parser, Maude, or an independent symbolic proof engine.
    """
    events=[]
    rules=matching_rules(DATA['aid'],case['rules'])
    def scan(stage, fixed):
        best,current=-1,0
        for rank,b in rules:
            old=best
            select=rank>best
            if select:
                current=b
                if fixed: best=rank
            events.append({'event':'SelectRule' if select else 'SkipRule','stage':stage,'rank':rank,'budget':b,'best_before':old,'best_after':best,'result_budget':current})
        return current
    spec=scan('spec',True)
    events.append({'event':'SpecDecision','budget':spec,'decision':'allow' if spec>0 else 'deny'})
    events.append({'event':'AccessRequested'})
    provider=scan('provider',False)
    events.append({'event':'ProviderBudget','budget':provider})
    if (spec,provider)!=(case['spec'],case['observed']):
        raise ValueError('Finite replay disagrees with archived results')
    receiver=None
    if provider<=0:
        events.append({'event':'ProviderReject','budget':provider})
    else:
        events += [{'event':'ProviderIssue','otk':'k1'}, {'event':'ProviderDebit','before':provider,'after':provider-1}, {'event':'TokenRequest','otk':'k1'}]
        receiver=scan('receiver',False)
        events.append({'event':'ReceiverBudget','budget':receiver})
        if receiver<0: events.append({'event':'ReceiverReject'})
        else: events += [{'event':x,'token':'t1'} for x in ('TokenIssue','TokenReceive','ChatSend','ChatAccept')]
    return {'kind':'finite_concrete_replay_not_tamarin','spec_budget':spec,'provider_budget':provider,'receiver_budget':receiver,'events':events,'chat_accepted':'ChatAccept' in [e['event'] for e in events]}

def execute(cmd, directory, label, timeout):
    print(f'[{directory.name}] {label}',flush=True)
    result={'command':list(map(str,cmd)),'timeout':False,'exit_code':None}
    with (directory/(label+'.stdout.txt')).open('wb') as out, (directory/(label+'.stderr.txt')).open('wb') as err:
        try: result['exit_code']=subprocess.run(list(map(str,cmd)),stdout=out,stderr=err,timeout=timeout,check=False).returncode
        except subprocess.TimeoutExpired: result['timeout']=True
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root',type=Path,help='SAGA root; default when installed under proofs/acp_tamarin')
    ap.add_argument('--preview-only',action='store_true',help='generate and perform finite replay only, no native proof')
    ap.add_argument('--offline-preview',action='store_true',help='allow preview against transcribed archived inputs, without original Git bytes')
    ap.add_argument('--tamarin',default='tamarin-prover'); ap.add_argument('--timeout',type=int,default=600)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    if args.offline_preview and not args.preview_only: ap.error('--offline-preview requires --preview-only')
    root=args.repo_root or HERE.parent.parent
    provenance=None if args.offline_preview else validate_repo(root)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest=(args.output or HERE/'evidence'/stamp).resolve(); dest.mkdir(parents=True,exist_ok=False)
    inputs=dest/'inputs'; inputs.mkdir()
    for n in ('cases.json','contact_policy.template.spthy','run_model.py'): shutil.copyfile(HERE/n,inputs/n)
    write_json(inputs/'provenance.json',{'mode':'offline_transcription' if provenance is None else 'checked_repository_bridge','data':provenance})
    models=dest/'models';models.mkdir()
    previews={}
    for name,case in CASES.items():
        (models/(name+'.spthy')).write_text(generate(name,case),encoding='utf-8')
        previews[name]=finite_replay(case)
        print(f"{name}: reference={previews[name]['spec_budget']}, provider={previews[name]['provider_budget']}, receiver={previews[name]['receiver_budget']}, chat={previews[name]['chat_accepted']}")
    write_json(dest/'finite_replay.json',previews)
    write_json(dest/'expected_native_results.json',{n:expected(c) for n,c in CASES.items()})
    summary={'native_executed':False,'native_complete':False,'cases':{},'problems':[]}
    if not args.preview_only:
        tamarin=shutil.which(args.tamarin); maude=shutil.which('maude')
        if not tamarin or not maude:
            summary['problems'].append('Tamarin or Maude not found on PATH')
        else:
            summary['native_executed']=True
            summary['toolchain']={'tamarin_sha256':sha(Path(tamarin).resolve().read_bytes()),'maude_sha256':sha(Path(maude).resolve().read_bytes())}
            execute([tamarin,'--version'],dest,'tamarin-version',60)
            execute([maude,'--version'],dest,'maude-version',60)
            for name,case in CASES.items():
                d=dest/name;d.mkdir();model=models/(name+'.spthy')
                base=[tamarin,'--quit-on-warning','--derivcheck-timeout=30']
                parsed=execute(base+['--parse-only',model],d,'parse',args.timeout)
                row={'parse':parsed,'results':{}};summary['cases'][name]=row
                if parsed['exit_code']!=0 or parsed['timeout']:
                    summary['problems'].append(name+': parse failed');continue
                proof=execute(base+['--prove',f'--output={d/"proof.spthy"}',f'--output-json={d/"traces.json"}',f'--output-dot={d/"traces.dot"}',model],d,'verify',args.timeout)
                row['proof']=proof
                result_text=(d/'verify.stdout.txt').read_text(encoding='utf-8',errors='replace')
                triples=RESULT_RE.findall(result_text)
                row['results']={n:{'type':k,'actual':v} for n,k,v in triples}
                exp=expected(case)
                if proof['exit_code']!=0 or proof['timeout'] or len(triples)!=len(exp) or set(row['results'])!=set(exp):
                    summary['problems'].append(name+': incomplete, missing or unexpected results')
                for n,v in row['results'].items():
                    v['matches_expected']=n in exp and v['type']==exp[n]['type'] and v['actual']==exp[n]['expected']
                    if not v['matches_expected']: summary['problems'].append(name+'/'+n+': unexpected verdict')
                write_json(d/'results.json',row)
            summary['native_complete']=not summary['problems'] and len(summary['cases'])==len(CASES)
    write_json(dest/'summary.json',summary)
    write_json(dest/'manifest.json',{'artifacts_sha256':{str(p.relative_to(dest)):sha(p.read_bytes()) for p in sorted(dest.rglob('*')) if p.is_file()},'native_executed':summary['native_executed'],'native_complete':summary['native_complete']})
    print(f'Archive: {dest}\n'+('NATIVE PASS' if summary['native_complete'] else 'PREVIEW ONLY' if args.preview_only else 'NATIVE INCOMPLETE'))
    return 0 if args.preview_only or summary['native_complete'] else 1

if __name__=='__main__':
    sys.dont_write_bytecode=True
    raise SystemExit(main())
