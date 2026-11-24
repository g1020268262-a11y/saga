#!/usr/bin/env python3
"""Verify native outputs and delivery integrity, not a replacement analyzer."""
import hashlib
import json
import re
from pathlib import Path
from run_model import generate, CASES, RESULT_RE, LEMMA_TYPES

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ARCHIVE=HERE/'evidence/20261124T111257499246Z'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    summary=json.loads((ARCHIVE/'summary.json').read_text())
    assert summary['native_complete'] and not summary['problems']
    results={}
    for case in CASES:
        d=ARCHIVE/case; row=summary['cases'][case]
        for command in ['parse','proof']:
            assert row[command]['exit_code']==0 and not row[command]['timeout']
        text=(d/'verify.stdout.txt').read_text()
        native={n:{'type':t,'actual':v} for n,t,v in RESULT_RE.findall(text)}
        assert set(native)==set(LEMMA_TYPES) and len(native)==16
        assert all(row['results'][n]['actual']==v['actual'] and row['results'][n]['matches_expected'] for n,v in native.items())
        for log in ['parse.stdout.txt','parse.stderr.txt','verify.stdout.txt','verify.stderr.txt']:
            assert not re.search(r'WARNING:|wellformedness checks failed|analysis incomplete', (d/log).read_text(),re.I)
        for name in ['proof.spthy','traces.json','traces.dot']:
            assert (d/name).stat().st_size>0
        assert (ARCHIVE/'models'/f'{case}.spthy').read_text()==generate(case,CASES[case])
        results[case]=native
    manifest=json.loads((ARCHIVE/'manifest.json').read_text())
    for p,expected in manifest['artifacts_sha256'].items():
        assert digest(ARCHIVE/p)==expected,p
    for item in json.loads((HERE/'audit/protected-files-before.json').read_text(encoding='utf-8-sig')):
        assert digest(ROOT/item['path'].replace('\\','/')).upper()==item['hash'],item['path']
    original=(HERE/'audit/initial-contact_policy.template.spthy').read_text()
    final=(HERE/'contact_policy.template.spthy').read_text()
    assert original.split('lemma evaluation_reachable:',1)[1]==final.split('lemma evaluation_reachable:',1)[1]
    trace=json.loads((ARCHIVE/'review/da-trace-review.json').read_text())
    assert all(trace['checks'].values())
    report={'native_results':64,'all_native_commands_succeeded':True,'original_lemmas_unchanged':True,
      'native_manifest_valid':True,'outside_module_unchanged':True,'da_native_trace_checks':trace['checks'],'actual_results':results}
    (HERE/'audit/delivery-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print('64 native results, original lemmas, native artifacts, D/A trace and protected files: PASS')

if __name__=='__main__': main()
