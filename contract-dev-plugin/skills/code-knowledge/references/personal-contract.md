---
name: personal-contract
description: 记录签约领域内部涉及的销售合同、报价单、报价领域交互逻辑。
---

## 个性化报价撤回

**触发：** 报价单状态从正式版回退到调整中/已提交时，自动处理关联合同。(`CancelPersonalContractListener`)
- **已绑定报价单**：解除绑定关系，单报价单则作废合同，多报价单则回退到草稿。
- **历史未绑定**：检查合同字段 `billCodeList`，包含该报价单则取消合同。
- **级联更新**：同步更新正签合同的 `billCodeList` 和 `billCodeInfoList` 字段。

