#!/usr/bin/env python3
"""Read-only source/archived experiment cross-check, not symbolic verification."""
import ast
import fnmatch
import hashlib
import json
from pathlib import Path
from run_model import DATA, CASES, matching_rules

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'audit'

def main():
    path=ROOT/DATA['source_path']
    raw=path.read_bytes()
    tree=ast.parse(raw.decode('utf-8'))
    names={'check_aid','pattern_specificity_component','aid_specificity','match'}
    definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(definitions)==4
    namespace={'fnmatch':fnmatch}
    exec(compile(ast.Module(body=definitions,type_ignores=[]),str(path),'exec'),namespace)
    observations={}
    for name,case in CASES.items():
        actual=namespace['match'](case['rules'],DATA['aid'])
        assert actual==case['observed']
        scores=[namespace['aid_specificity'](r['pattern']) for r in case['rules']]
        assert list(zip(scores,[r['budget'] for r in case['rules']]))==matching_rules(DATA['aid'],case['rules'])
        observations[name]={'actual_matcher_budget':actual,'scores':scores,'ordered_rules':case['rules']}
    consumer='proofs/consumer_validation/evidence/20260926T070021921746Z-d64c8064'
    experiments={}
    for case in ['aa','dd','da']:
        p=ROOT/consumer/'cases'/case/'result.json'
        result=json.loads(p.read_text(encoding='utf-8'))
        experiments[case]={'path':str(p.relative_to(ROOT)).replace('\\','/'),
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'pair':result['pair'],'http_status':result['http']['status'],
            'assertions':[{'name':a['name'],'actual':a['actual'],'status':a['status']} for a in result['assertions']],
            'remaining_counter':result['after']['counter'],
            'active_token_count':len(result['after']['active_tokens'])}
        assert all(a['status']=='pass' for a in result['assertions'])
    report={'kind':'source_method_reexecution_and_historical_experiment_review_not_tamarin',
       'source_path':DATA['source_path'],'source_sha256':hashlib.sha256(raw).hexdigest(),
       'execution':'Original AST function definitions, unmodified; only logger/package imports excluded. Actual fnmatch module is used.',
       'matcher_cases':observations,'historical_consumer_experiments':experiments}
    (OUT/'source-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Four production matcher reexecutions agree with pinned observations; three historical consumer controls reviewed.')

if __name__=='__main__': main()
