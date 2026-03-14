---
name: contract-database-tables
description: 签约领域数据库表结构参考，开发时查阅表结构和分表规则
---

# 签约领域数据库表结构

## 表清单

| 表名 | 用途 | 分表 |
|------|------|------|
| `contract` | 合同主表 | 否 |
| `contract_node` | 合同节点记录 | 否 |
| `contract_log` | 合同操作日志 | 否 |
| `contract_user` | 合同签约用户 | 否 |
| `contract_field_sharding` | 合同扩展字段 | 是，10 张表 |
| `contract_relation` | 合同关联关系 | 否 |
| `contract_quotation_relation` | 合同-报价单关联 | 否 |
| `contract_city_company_info` | 城市公司配置 | 否 |

---

## contract（合同主表）

核心业务主表，存储合同基本信息。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_code` | varchar(32) | 合同唯一编号（业务主键） |
| `contract_no` | varchar(32) | 合同编号（展示用） |
| `project_order_id` | varchar(64) | 项目订单号 |
| `change_order_id` | varchar(64) | 变更单号 |
| `type` | tinyint | 合同类型（见 ContractTypeEnum） |
| `status` | int | 合同状态（见 ContractStatusEnum） |
| `amount` | decimal(11,2) | 合同金额 |
| `platform_instance_id` | bigint | 协议平台实例 ID |
| `relate_contract_code` | varchar(128) | 关联合同编号（逗号分隔） |
| `sign_channel_type` | tinyint | 签署方式（见 sign_channel_type 枚举） |
| `user_sign_status` | tinyint | 用户签署状态：0 未签署，1 已签署 |
| `user_sign_type` | tinyint | 用户签署方式：1 确认，2 签字 |
| `user_confirm_status` | tinyint | 用户确认状态：0 未确认，1 已确认 |
| `user_query_status` | tinyint | 用户查询状态：0 不可见，1 可见 |
| `audit_type` | tinyint | 审核类型（见 audit_type 枚举） |
| `business_type` | tinyint | 业务类型：1 家装 |
| `pdf_generation_mode` | int | PDF 模式（见 pdf_generation_mode 枚举） |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

### 合同类型枚举（type）

| 值 | 类型 |
|----|------|
| 1 | 认购合同 |
| 2 | 设计合同 |
| 3 | 正签合同（套餐正式合同） |
| 4 | 套餐变更协议 |
| 5 | 解约协议 |
| 6 | 整装首期款合同 |
| 7 | 套餐施工图纸 |
| 8 | 销售合同（个性化主材合同） |
| 9 | 木作首期款协议 |
| 10 | 其他主材首期款协议 |
| 11 | 设计变更协议 |
| 12 | 授权协议书 |
| 13 | 家电首期款协议 |
| 14 | 家居首期款协议 |
| 15 | 定制首期款协议 |
| 16 | 软装首期款协议 |
| 17 | 门窗首期款协议 |
| 18 | 销售合同（零售） |
| 19 | 销售变更补充协议 |
| 20 | 资金存管协议 |
| 21 | 门窗暖首期款协议 |
| 22 | 全案合同概要 |
| 23 | 图纸报价 |
| 24 | 其他附件 |
| 25 | K3 首期款协议 |
| 26 | K5 首期款协议 |
| 27 | K7 首期款协议 |
| 28 | 授权委托书 |
| 29 | 补充协议 |
| 30 | 和解协议 |

### 合同状态枚举（status）

| 值 | 状态 |
|----|------|
| 1 | 起草中 |
| 2 | 待确认 |
| 3 | 已确认 |
| 4 | 待签署 |
| 5 | 待提交审核 |
| 6 | 审核中 |
| 7 | 待盖公司章 |
| 8 | 已签署 |
| 9 | 已取消 |
| 10 | 已驳回 |
| 11 | 待盖第三方章 |

### 签署方式枚举（sign_channel_type）

| 值 | 方式 |
|----|------|
| 1 | 线上 |
| 2 | 线下 |

### 审核类型枚举（audit_type）

| 值 | 类型 |
|----|------|
| 0 | 不需要审核 |
| 1 | 签前审核 |
| 2 | 签后审核 |

### PDF 生成模式枚举（pdf_generation_mode）

| 值 | 模式 |
|----|------|
| 1 | 有版式 |
| 2 | 无版式 |

---

## contract_node（合同节点表）

记录合同流转过程中的关键时间节点。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_code` | varchar(32) | 关联合同编号 |
| `node_type` | tinyint | 节点类型 |
| `fire_time` | bigint | 发生时间（时间戳） |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

### 节点类型枚举（node_type）

| 值 | 节点 |
|----|------|
| 1 | 创建时间 |
| 2 | 发起时间 |
| 3 | 最新提交审核时间 |
| 4 | 最新审核通过时间 |
| 5 | 用户确认时间 |
| 6 | 申请用章时间 |
| 7 | 用户签署完成时间 |
| 8 | 盖公司章时间 |
| 9 | 最终完成时间 |
| 10 | 作废时间 |

### 特性

- **唯一性约束**：同一合同的每种节点类型只存在一条记录
- 更新操作会覆盖 `fire_time`，而非新增

---

## contract_log（合同日志表）

记录合同操作日志。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_code` | varchar(32) | 合同编号 |
| `type` | tinyint | 动作类型 |
| `content` | varchar(3000) | 日志内容 |
| `remark` | varchar(3000) | 备注 |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

### 日志类型枚举（type）

| 值 | 类型 |
|----|------|
| 1 | 状态变更 |
| 2 | 提交审核 |
| 3 | 审核驳回 |
| 4 | 用户已签署 |

---

## contract_user（合同用户表）

存储合同签约人信息。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_code` | varchar(32) | 合同编号 |
| `role_type` | tinyint | 用户类型（见 role_type 枚举） |
| `name` | varchar(64) | 姓名 |
| `phone` | varchar(16) | 手机号 |
| `is_sign` | tinyint | 是否签约人：0 否，1 是 |
| `is_auth` | tinyint | 是否已认证：0 否，1 是 |
| `certificate_type` | tinyint | 证件类型：1 身份证，2 护照 |
| `certificate_no` | varchar(32) | 证件号码 |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

### 用户类型枚举（role_type）

| 值 | 类型 |
|----|------|
| 1 | 业主 |
| 2 | 代理人 |
| 3 | 公司代办人 |

---

## contract_field_sharding（合同字段表）

存储合同扩展字段，**分表存储**。

### 分表规则

```
表名: contract_field_sharding_{N}, N ∈ [0, 9]
计算公式: contractCode 中的数字部分 % 10
```

**示例**：
- `C1767173898135504` → `1767173898135504 % 10 = 4` → `contract_field_sharding_4`

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_code` | varchar(32) | 合同编号 |
| `field_key` | varchar(64) | 字段名称 |
| `field_value` | varchar(4096) | 字段值 |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

### 索引

- `idx_contract_code` - 按合同号查询
- `idx_field_key` - 按字段名查询
- `idx_k_v_status` - 复合索引 (field_key, field_value, del_status)

---

## contract_relation（合同关联关系表）

存储合同之间的关联关系。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_code` | varchar(32) | 合同编号 |
| `relate_contract_code` | varchar(32) | 关联合同编号 |
| `relation_type` | tinyint | 关联类型 |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

---

## contract_quotation_relation（合同-报价单关联表）

存储合同与报价单/子单的绑定关系。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `contract_code` | varchar(32) | 合同编号 |
| `bill_code` | varchar(32) | 报价单号/子单号 |
| `bind_type` | int | 绑定单据类型（见 bind_type 枚举） |
| `company_code` | varchar(32) | 分公司编码 |
| `status` | int | 关联状态：1 已关联，2 已取消 |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

### 绑定单据类型枚举（bind_type）

| 值 | 类型 |
|----|------|
| 1 | 报价单号 |
| 2 | 变更单号 |
| 3 | 子单号 |

---

## contract_city_company_info（城市公司配置表）

存储各城市公司的合同配置信息。

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `gb_code` | int | 城市编码 |
| `company_code` | varchar(128) | 公司编码 |
| `business_type` | tinyint | 业务类型：1 家装，2 团装 |
| `contract_type` | int | 合同类型 |
| `sign_channel_type` | tinyint | 签署方式：1 线上，2 线下 |
| `audit_type` | int | 审核类型：0 不需审核，1 签前审核，2 签后审核 |
| `form_id` | int | 表单 ID（版式） |
| `form_key` | varchar(128) | 表单 key |
| `seal_code` | varchar(128) | 图章 code |
| `process_mode` | tinyint | 流程模式：1-2.0，2-2.5 |
| `del_status` | tinyint | 删除状态：0 未删除，1 已删除 |
| `ctime` | datetime | 创建时间 |
| `mtime` | datetime | 更新时间 |

### 索引

- `idx_gb_code` - 按城市编码查询
- `idx_company_code` - 按公司编码查询
