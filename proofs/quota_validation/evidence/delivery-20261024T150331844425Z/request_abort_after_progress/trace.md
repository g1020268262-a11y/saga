# TLC 状态轨迹摘录

由本目录 stdout.log 提取；不是原生代码重放。

| 状态 | 到达动作 | B 余额 | A 余额 | 故障数 |
|---:|---|---:|---:|---:|
| 1 | Init | 50 | 50 | 0 |
| 2 | AEnter | 50 | 50 | 0 |
| 3 | BCheck | 50 | 50 | 0 |
| 4 | BSendReturn | 50 | 50 | 0 |
| 5 | BDebit | 49 | 50 | 0 |
| 6 | AReceive | 49 | 50 | 0 |
| 7 | ACheck | 49 | 50 | 0 |
| 8 | ADebit | 49 | 49 | 0 |
| 9 | ABackend | 49 | 49 | 0 |
| 10 | AReplyReturn | 49 | 49 | 0 |
| 11 | BReceiveResponse | 49 | 49 | 0 |
| 12 | BCheck | 49 | 49 | 0 |
| 13 | BSendReturn | 49 | 49 | 0 |
| 14 | BDebit | 48 | 49 | 0 |
| 15 | AbortRequest | 48 | 49 | 1 |
| 16 | AReadError | 48 | 49 | 1 |
| 17 | BReceiveError | 48 | 49 | 1 |
