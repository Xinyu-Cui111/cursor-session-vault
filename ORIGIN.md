# 本仓库是怎么成型的

一句话：一次「想备份 Cursor Agent 对话」的对话，从项目级钩子迭代成全局 Vault + 可切换方案 + 健康检查。

---

## 源聊天记录（已落在本仓库）

| 会话 | 文件 | 作用 |
|------|------|------|
| **成型主线** | [`sessions/2026-09-14/你好__5ab0dcdd.md`](sessions/2026-09-14/你好__5ab0dcdd.md) | 从「这是啥」→ 全局化 → 按日存放 → 去重 → 推荐方案 → README → 健康检查 → 提问时间戳 |
| 用法确认 | [`sessions/2026-09-14/知道当前项目是干嘛的吗__6d34528b.md`](sessions/2026-09-14/知道当前项目是干嘛的吗__6d34528b.md) | 在 CareerOS 工作区触发，验证全局存档已生效 |
| 旁证样本 | [`sessions/2026-09-14/只做学年论文线：P1→P2。__9075151a.md`](sessions/2026-09-14/只做学年论文线：P1→P2。__9075151a.md) | 论文项目对话被自动吸入 vault（非本仓库开发过程） |

复盘时优先读 **`你好__5ab0dcdd.md`**，那是产品决策与踩坑的完整时间线。

---

## 演进时间线（2026-09-14）

```
项目级 Hooks 存本仓库 sessions/
        │  需求：任意项目都要备份
        ▼
用户级 ~/.cursor/hooks.json + 写死 vault 路径
        │  需求：按日期归类
        ▼
sessions/{date}/{project}/…
        │  痛点：每轮全量再存 → 大量重复文件
        ▼
每天每对话只保留 1 份（覆盖写）
        │  需求：更好翻、更灵活
        ▼
recommended：{date}/{title}__{id}.md + config.json + SCHEMES.md + _index.jsonl
        │  需求：说明书 + 概念边界
        ▼
README（Vault ≠ Skill）
        │  需求：Hooks/Python 静默失败可发现
        ▼
_health 心跳 + check-health.cmd + save-session.cmd 找 Python
        │  需求：提问带时间
        ▼
Markdown 里 User 段上方显示时间戳
```

---

## 关键决策（可复用）

| 决策 | 选择 | 原因 |
|------|------|------|
| 作用域 | 用户级 Hooks，不是项目级 | 关掉 vault 打开别的项目也要继续存 |
| 本仓库角色 | 归档落点 + 配置/文档，不是业务 App | 避免和新项目的 `.cursor/hooks` 抢写 |
| 布局 | 配置驱动 `layout`，手册在 `SCHEMES.md` | 换方案改 JSON，少改脚本 |
| 去重 | 同一 layout 路径 overwrite | 人眼不会被时间戳副本淹没 |
| 静默失败 | 心跳文件 + 一键自检 | Hooks 关了时脚本跑不起来，没法弹窗 |

---

## 产物清单

| 产物 | 位置 |
|------|------|
| 用户级钩子 | `~/.cursor/hooks.json`、`~/.cursor/hooks/save-session.*` |
| 方案配置 | 本仓库 `config.json`、`SCHEMES.md` |
| 说明书 | `README.md` |
| 本成型说明 | `ORIGIN.md`（本文件） |
| 可复用 Skill | `.cursor/skills/session-vault/SKILL.md`（本仓库） |
| 0→1 提示词 + Playbook | `ZERO_TO_ONE.md`；个人 Skill `hooks-session-archive`（含 `prompt.md`） |

---

## 和「沉淀 Skill」的关系

- **存聊天** = 原材料（已经在做）
- **写 ORIGIN / README / SCHEMES** = 把决策固化成文档
- **写 Skill** = 教以后的 Agent：怎么查 vault、怎么换方案、怎么在别处复刻同一套路

不要把 Vault 本身当成 Skill；Skill 是「操作说明书」，Vault 是「自动落盘的保险库」。
