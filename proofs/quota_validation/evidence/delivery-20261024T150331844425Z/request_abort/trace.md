# TLC 状态轨迹摘录

由本目录 stdout.log 提取；不是原生代码重放。

| 状态 | 到达动作 | B 余额 | A 余额 | 故障数 |
|---:|---|---:|---:|---:|
| 1 | Init | 50 | 50 | 0 |
| 2 | AEnter | 50 | 50 | 0 |
| 3 | BCheck | 50 | 50 | 0 |
| 4 | BSendReturn | 50 | 50 | 0 |
| 5 | BDebit | 49 | 50 | 0 |
| 6 | AbortRequest | 49 | 50 | 1 |
| 7 | AReadError | 49 | 50 | 1 |
| 8 | BReceiveError | 49 | 50 | 1 |
