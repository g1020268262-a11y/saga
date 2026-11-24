#!/usr/bin/env python3
"""Extract and check a native Tamarin graph, never synthesize a protocol trace."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('archive',type=Path)
    args=ap.parse_args()
    source=args.archive/'da/traces.json'
    graphs=json.loads(source.read_text(encoding='utf-8'))['graphs']
    matches=[g for g in graphs if '_chat_requires_policy_allow-' in g['jgLabel']]
    assert len(matches)==1
    graph=matches[0]
    nodes={n['jgnId']:n for n in graph['jgNodes'] if n['jgnType']=='isProtocolRule'}
    incoming={n:set() for n in nodes}
    for e in graph['jgEdges']:
        a=e['jgeSource'].split(':')[0]; b=e['jgeTarget'].split(':')[0]
        if a in nodes and b in nodes and a!=b: incoming[b].add(a)
    order=[]
    while len(order)<len(nodes):
        available=[n for n in nodes if n not in order and incoming[n]<=set(order)]
        assert available,'Native graph contains a cycle'
        order.append(sorted(available)[0])
    steps=[]
    for i,n in enumerate(order,1):
        node=nodes[n]; m=node['jgnMetadata']
        steps.append({'step':i,'native_node':n,'rule':node['jgnLabel'],
          'premises':m['jgnPrems'],'actions':m['jgnActs'],'conclusions':m['jgnConcs']})
    rules=[s['rule'] for s in steps]
    assert rules==['Setup','Spec_Select_Better_0','Skip_Rule_1','Spec_Finish',
      'Provider_Start','Impl_Select_Better_0','Impl_Select_Better_1','Provider_Finish',
      'Provider_Release','Sender_Request_Token','Receiver_Start',
      'Impl_Select_Better_0','Impl_Select_Better_1','Receiver_Finish',
      'Receiver_Issue_Token','Sender_Decrypt_Token','Sender_Send_Chat','Receiver_Accept_Chat']
    actions=[a for s in steps for a in s['actions']]
    event=lambda name: next(a for a in actions if a['jgnFactName']==name)
    const=lambda t:t['jgnConst']
    for stage in ['provider_eval','receiver']:
        selects=[a['jgnFactTerms'][2:] for a in actions if a['jgnFactName']=='SelectRule' and const(a['jgnFactTerms'][1])==f"'{stage}'"]
        assert [[const(t) for t in pair] for pair in selects]==[["'r70'","'bneg1'"],["'r0'","'b10'"]]
    assert [const(t) for t in event('SpecDecision')['jgnFactTerms'][-2:]]==["'bneg1'","'deny'"]
    for name in ['ProviderBudget','ReceiverBudget']:
        assert const(event(name)['jgnFactTerms'][-1])=="'b10'"
    assert [const(t) for t in event('ProviderDebit')['jgnFactTerms'][-2:]]==["'b10'","'b9'"]
    canonical=lambda x:json.dumps(x,sort_keys=True)
    token_events=[event(name)['jgnFactTerms'] for name in ['TokenIssue','TokenReceive','ChatAccept']]
    assert len({canonical(a[:4]) for a in token_events})==1
    # Check the same OTK leaves Provider storage and is consumed at the receiver.
    fact=lambda step,name,which:next(f for f in steps[step-1][which] if f['jgnFactName']==name)
    issued_otk=event('ProviderIssue')['jgnFactTerms'][3]
    assert canonical(issued_otk)==canonical(fact(9,'ProviderUnusedOTK','premises')['jgnFactTerms'][2])
    assert canonical(issued_otk)==canonical(fact(15,'ReceiverUnusedOTK','premises')['jgnFactTerms'][2])
    target=args.archive/'review';target.mkdir(exist_ok=True)
    (target/'da-attack.native.json').write_text(json.dumps({'graphs':[graph]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    review={'kind':'topological_linearization_of_native_tamarin_counterexample',
      'source':'../da/traces.json','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'native_graph_label':graph['jgLabel'],'steps':steps,
      'checks':{'complete_18_step_execution':True,'both_implementation_scans_overwrite_deny':True,
      'spec_denies':True,'provider_debit_10_to_9':True,'same_OTK_issued_and_consumed':True,
      'same_session_identity_and_ciphertext_issued_decrypted_accepted':True}}
    (target/'da-trace-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# D/A 原生反例逐步核对','',
      '本表直接读取 Tamarin 原生 JSON 图并按事实依赖进行拓扑排序；不使用 finite_replay.json。',
      '原生节点 ID 是节点标识，不是数值时间。此表是一种合法线性展开。','',
      '| 步骤 | 原生节点 | 原生规则 | 原生事件 |','|---:|---|---|---|']
    for s in steps:
        events='<br>'.join('`'+a['jgnFactShow']+'`' for a in s['actions'])
        lines.append(f"| {s['step']} | `{s['native_node']}` | `{s['rule']}` | {events} |")
    lines+=['','所有逐步一致性检查通过。完整前提、事件和后继事实见 da-trace-review.json。',
      'da-attack.native.json 是原生图的精确子集；联合 DOT 原始输出保留在 ../da/traces.dot。']
    (target/'DA_TRACE.zh-CN.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'native_nodes':len(steps),'all_checks':True,'graph':graph['jgLabel']}))

if __name__=='__main__': main()
