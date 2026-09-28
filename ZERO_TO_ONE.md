# 从 0 到 1：剪成同款 Session Vault

可复制提示词 + 验收标准。Agent 执行时优先加载个人 Skill：`hooks-session-archive`（含同文 `prompt.md`）。

本仓库是参考实现；成型史见 [`ORIGIN.md`](ORIGIN.md)。

---

## 一键提示词（复制到新对话）

```text
按「Cursor Session Vault」从 0 到 1 搭一套全局 Agent 会话保险库。先读技能 hooks-session-archive（若无该 skill，就严格按下列规格做）。

## 目标
用【用户级 Cursor Hooks】在任意项目的 Agent 对话结束时，自动把对话存成可读 Markdown，统一写入一个 Vault 仓库。关掉 Vault 仓库、打开别的项目也要继续存。

## 我的路径（按需改）
- Vault 根目录：C:\path\to\cursor-session-vault
- OS：Windows

## 必须交付
1) Vault 仓库：README.md、SCHEMES.md、config.json、check-health.cmd + check-health.py、sessions/、空的 .cursor/hooks.json（防双写）
2) 用户级：~/.cursor/hooks.json（与现有 hooks 合并，勿覆盖其它钩子）+ hooks/save-session.cmd + hooks/save-session.py
3) 默认 config：layout="{date}/{title}__{id}.md"，on=["stop","sessionEnd"]，dedupe=overwrite，index=true，frontmatter=true
4) 脚本：stdin UTF-8 去 BOM；读 transcript jsonl；写 Markdown（User 上方带提问时间）；按 config layout 落盘；同路径覆盖不堆重复；维护 _index.jsonl 与 _health 心跳；找不到 Python 时写健康失败；钩子退出码对 Cursor 友好（stdout 给 {}）
5) SCHEMES.md 写清可切换方案：recommended / project_date / flat_id / daily_digest
6) README 写清：这是 Vault+Hooks，不是 Skill；新项目对话存到 Vault 而不是新项目目录

## 验收
- 打开另一个项目聊一轮 → Vault 的 sessions/当天/ 出现文件
- 同对话再聊一轮 → 仍更新同一文件
- check-health 无 FAIL；_health.md 时间随聊天刷新

## 参考（若本机已有）
优先对照并改编：C:\path\to\cursor-session-vault 与 ~/.cursor/hooks/save-session.py
有则复制再改 DEFAULT_VAULT，不要从零臆造行为差异。

现在直接实现，做完列出改动的文件路径与验收步骤。
```

### 短版（本机已有本仓库时）

```text
对照 C:\path\to\cursor-session-vault 与 ~/.cursor/hooks/save-session.*，在【新路径：___】从 0 复制一套全局 Session Vault。合并进现有 ~/.cursor/hooks.json，改好 DEFAULT_VAULT，补 README/SCHEMES/config/健康检查。验收：其它项目聊一轮能写入新 vault，且同对话不产生重复文件。用技能 hooks-session-archive。
```

---

## 架构一眼看懂

```
任意项目 Agent
    → ~/.cursor/hooks.json（用户级）
    → save-session.cmd → save-session.py
    → 读 <vault>/config.json
    → 写 <vault>/sessions/… + _index.jsonl + _health.*
```

| 层级 | 职责 |
|------|------|
| 用户级 Hooks | 会不会自动跑 |
| Vault `config.json` | 存哪儿、叫什么、何时写 |
| Vault 仓库本身 | 归档落点 + 说明书，不是业务 App |

---

## 最小文件集

**Vault**

- `config.json` / `README.md` / `SCHEMES.md`
- `check-health.cmd` + `check-health.py`
- `.cursor/hooks.json`（空，防双写）

**本机**

- `~/.cursor/hooks.json`
- `~/.cursor/hooks/save-session.cmd`
- `~/.cursor/hooks/save-session.py`

---

## 推荐默认 config

```json
{
  "scheme": "recommended",
  "layout": "{date}/{title}__{id}.md",
  "on": ["stop", "sessionEnd"],
  "dedupe": "overwrite",
  "index": true,
  "frontmatter": true,
  "debug": false,
  "title_max_len": 40
}
```

换方案只改 `config.json`，手册见 `SCHEMES.md`。

---

## 验收 checklist

- [ ] Settings → Hooks 开启
- [ ] 另一项目 Agent 聊一轮后，`sessions/YYYY-MM-DD/` 有文件
- [ ] 同对话第二轮只更新同一文件
- [ ] `_health.md` 时间刷新
- [ ] `check-health.cmd` 无 FAIL

---

## 相关沉淀

| 文件 | 用途 |
|------|------|
| `ORIGIN.md` | 本仓库怎么聊出来的 |
| `.cursor/skills/session-vault/` | 在本仓库内查档 / 换方案 |
| `~/.cursor/skills/hooks-session-archive/` | 0→1 再建一套（Skill + prompt） |
