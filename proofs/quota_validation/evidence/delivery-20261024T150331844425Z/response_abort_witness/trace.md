# TLC 状态轨迹摘录

由本目录 stdout.log 提取；不是原生代码重放。

| 状态 | 到达动作 | B 余额 | A 余额 | 故障数 |
|---:|---|---:|---:|---:|
| 1 | Init | 2 | 2 | 0 |
| 2 | AEnter | 2 | 2 | 0 |
| 3 | BCheck | 2 | 2 | 0 |
| 4 | BSendReturn | 2 | 2 | 0 |
| 5 | AReceive | 2 | 2 | 0 |
| 6 | ACheck | 2 | 2 | 0 |
| 7 | ADebit | 2 | 1 | 0 |
| 8 | AbortResponse | 2 | 1 | 1 |
