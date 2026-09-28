# cursor-session-vault · 产品卡

> 路径：`C:\path\to\cursor-session-vault`  
> 所属区：基础设施  
> 更新日期：2026-09-28（第 2 步收口）

## 1. 一句话

靠用户级 Cursor Hooks，把任意项目的 Agent 对话自动存成 Markdown 总库，并在项目内用 `.agent-chats` 联接看得见。

## 2. 类型

基础设施 / 本地工具

## 3. 当前状态

**可交付**：安装与验收收敛在 [INSTALL.md](INSTALL.md)。

## 4. 怎么用（最短路径）

→ **[INSTALL.md](INSTALL.md)**（约 10 分钟）  
原理：[PROJECT_MIRROR.md](PROJECT_MIRROR.md) · 自检：`check-health.cmd`

## 5. 不做边界

- 不是 Skill；Vault 内保持空 hooks  
- `.agent-chats` 是联接不是拷贝  

## 6. 依赖与风险

- Python + Hooks 开启  
- 对话可能含密钥 → 勿公开 sessions  

## 7. 对标

见 [BENCHMARK.md](BENCHMARK.md)（第 3 步已完成）。

## 8. 下一刀（只写一条）

`check-health` 增加抽查：业务项目是否存在有效 `.agent-chats` 联接。

## 台账摘要

| 价值 1-5 | 完成度 1-5 | 建议动作 |
|----------|------------|----------|
| 5 | 5 | 收口成工具 |
