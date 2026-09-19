# Deferred Paper Revision Notes

## 第五章：后续润色建议（仅记录，尚未执行）

以下建议用于后续统一排版与 artifact 整理。本轮不修改第五章，不移动或改写已有证据归档。

### 1. Evidence path normalization

- 当前引用：`proofs/evidence/authz-turepass-20260919T090826295518Z/`。
- 正式论文版本拟采用稳定的 artifact 标识：`proofs/evidence/turepass/` 或 `artifact/turepass/`；最终位置尚未选定。
- 原因：读者需要识别 artifact，而非依赖生成时间定位它。
- 整理时保留 manifest 中的真实时间、输入哈希和运行来源，以及稳定标识与原始归档之间的对应关系；不得覆盖历史来源。

### 2. Limitations paragraph compression

后续排版可压缩第五章限制段，正文保留：

> The formal model abstracts the matcher result.

其余 provenance 细节可移入 appendix，并保留必要交叉引用。尚无直接可执行的 matcher–ProVerif 集成、尚无生产服务复现这两项限制仍须清楚可见，不能因压缩而被删除或暗示已完成。

### 3. Terminology consistency

| 待统一的措辞 | 后续采用 |
|---|---|
| Attack Trace | Formal Reachability Witness |
| exploit execution | symbolic reachability consequence |
| matcher attack | authorization decision inconsistency |

仅记录全文统一要求，本轮不执行第五章或其他既有章节的批量替换。

### 4. Preserve current claim boundary

不得改写为：

> ProVerif proves the matcher vulnerability.

保留以下表述及其两层证据区分：

> The matcher inconsistency is demonstrated at implementation level, and ProVerif models its protocol-level consequence under explicit assumptions.

实现层不一致与形式化后果不得合并为一个证明。
