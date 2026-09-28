# 项目内对话镜像（方案 A）— 原理 · 使用 · 复现

> 本文说明：**为什么对话会同时出现在总库和每个项目的 `.agent-chats` 里**，以及如何维护、关闭或在另一台电脑复现。  
> 总库路径：`C:\path\to\cursor-session-vault`  
> 相关配置：根目录 `config.json` · 方案表 `SCHEMES.md` · 总说明书 `README.md`

---

## 1. 一句话

对话的**唯一正文**只写在 Vault 的 `sessions/{项目名}/` 里；  
每个业务项目根目录下的 `.agent-chats` 是 **Windows 目录联接（junction）**，指向那份目录——侧边栏能打开，但**不是拷贝两份文件**。

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│  Cursor（任意项目里的 Agent 对话）                        │
│    stop / sessionEnd 生命周期                             │
└───────────────────────────┬─────────────────────────────┘
                            │ stdin JSON（含 transcript 路径、
                            │ conversation_id、workspace_roots）
                            ▼
┌─────────────────────────────────────────────────────────┐
│  用户级 Hooks（全机一份，不是某个项目里的）                 │
│  ~/.cursor/hooks.json                                     │
│       → hooks\save-session.cmd                            │
│       → hooks\save-session.py                             │
└───────────────────────────┬─────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
┌──────────────────────┐          ┌──────────────────────────┐
│ Vault 写正文          │          │ 项目镜像（方案 A）         │
│ sessions/             │          │ 对每个 workspace_root：    │
│   {project}/          │◄─junction─│   .agent-chats  ─────────┤
│     {date}/           │          │   并写入 .gitignore       │
│       {title}__{id}.md│          └──────────────────────────┘
│ _index.jsonl          │
│ _health.md            │
└──────────────────────┘
```

### 为什么不用「项目级 Hooks 再写一份」？

| 做法 | 问题 |
|------|------|
| 每个项目再挂一套会写入的 hooks | 与用户级钩子**双写**、难维护、易分叉 |
| 只拷贝 Markdown 到项目 | 占双倍空间，易和总库不一致 |
| **总库 + junction（本方案）** | 一份正文；项目里能看；gitignore 防泄密进 Git |

Vault 仓库自己的 `.cursor/hooks.json` 必须保持**空钩子**，防止打开本仓库时再跑一套存档逻辑。

---

## 3. 关键组件与职责

| 位置 | 职责 |
|------|------|
| `~/.cursor/hooks.json` | 声明在 `sessionStart` / `stop` / `sessionEnd` 跑存档命令 |
| `~/.cursor/hooks/save-session.cmd` | 找到 `python`/`py`，把 stdin 交给 `.py` |
| `~/.cursor/hooks/save-session.py` | 读 transcript → 渲染 Markdown → 按 layout 落盘 → **建联接** |
| 本仓库 `config.json` | `layout`、`on`、`dedupe`、`project_mirror` 等 |
| 本仓库 `sessions/` | 所有项目对话的权威存储 |
| 业务项目 `.agent-chats/` | 联接窗口（可删，下次存档会再建） |
| `migrate-to-project-layout.py` | 一次性：把旧的 `sessions/日期/*.md` 迁到 `sessions/项目/日期/` |

### `config.json` 与镜像相关的字段

```json
{
  "scheme": "project_date",
  "layout": "{project}/{date}/{title}__{id}.md",
  "project_mirror": {
    "enabled": true,
    "mode": "junction",
    "dir": ".agent-chats",
    "gitignore": true
  }
}
```

| 字段 | 含义 |
|------|------|
| `layout` 里的 `{project}` | 取自钩子 payload 的 `workspace_roots` 文件夹名（经消毒） |
| `project_mirror.enabled` | 是否在项目里建联接 |
| `mode` | Windows 用 `junction`（本地目录联接，一般**不需要管理员**） |
| `dir` | 联接文件夹名，必须是单层名（不要写成 `a/b`） |
| `gitignore` | 自动把该目录追加进项目 `.gitignore` |

环境变量（可选）：

- `CURSOR_SESSION_VAULT` — 覆盖默认 Vault 根路径  
- `CURSOR_SESSION_VAULT_DEBUG=1` — 打开 debug 落盘  

---

## 4. 存档脚本在干什么（实现要点）

文件：`C:\Users\hexinying\.cursor\hooks\save-session.py`

### 4.1 触发与过滤

1. Cursor 把钩子事件 JSON 从 stdin 传入（脚本按 **UTF-8 去 BOM** 解析）。  
2. 任意事件先写 `_health` 心跳，证明 Hooks 真的跑到了。  
3. `sessionStart` 只心跳，不写会话文件。  
4. 仅当 `hook_event_name` ∈ `config.on`（默认 `stop`、`sessionEnd`）才存档。

### 4.2 读对话

优先：`transcript_path` / `agent_transcript_path`；  
否则按 `conversation_id` 在 `~/.cursor/projects/**` 下找 `*.jsonl`（跳过 `subagents`）。

解析 jsonl 中 `user` / `assistant` 文本块，渲染成 Markdown（可带 YAML frontmatter）。

### 4.3 写总库

`layout` 占位符替换后落到：

```text
<vault>/sessions/{project}/{date}/{title}__{id}.md
```

`dedupe: overwrite` → 同一路径覆盖，不每轮堆新文件。  
并更新 `sessions/_index.jsonl`。

### 4.4 建项目联接（方案 A 核心）

成功写盘后调用 `ensure_project_mirror(...)`：

1. 解析 `workspace_roots` → 每个存在的项目根目录。  
2. 目标目录：`<vault>/sessions/{project_slug}/`（没有则创建）。  
3. 联接路径：`<项目根>/{dir}`，默认 `.agent-chats`。  
4. 若联接已存在且已指向正确目标 → 跳过；指错或空目录则可重建。  
5. **拒绝删除非空真实目录**（防止误伤用户自己建的文件夹）。  
6. Windows：`cmd /c mklink /J ".agent-chats" "<vault>\sessions\<project>"`。  
7. 若 `gitignore: true`，向项目 `.gitignore` 追加 `.agent-chats/`。

联接与符号链接的区别（直观理解）：

- **Junction**：Windows 目录联接，对资源管理器 / Cursor 就像普通文件夹；两边看到的是同一批文件。  
- 删联接本身（`rmdir .agent-chats`）**不会**删掉 Vault 里的正文；删联接里面的文件则会删总库内容（因为是同一文件系统对象）。

---

## 5. 日常使用

### 5.1 在项目里看对话

打开任意业务项目（例如 `D:\works\unattended-pc`）侧边栏：

```text
.agent-chats/
  2026-09-28/
    某标题__a597cd93.md
```

若没有该文件夹：在该项目里用 Agent **再聊一轮并等结束**（触发 `stop`），钩子会自动创建。

### 5.2 在总库里看全部

```text
C:\path\to\cursor-session-vault\sessions\
  定时开机\...
  CareerOS\...
  _index.jsonl
  _health.md
```

### 5.3 常见操作

| 需求 | 做法 |
|------|------|
| 改存档路径结构 | 改 `config.json` 的 `layout`（见 `SCHEMES.md`） |
| 关掉项目内 `.agent-chats` | `"project_mirror": { "enabled": false }` |
| 换联接文件夹名 | 改 `project_mirror.dir`（如 `对话记录`），下一轮存档生效；可手动删旧联接 |
| 检查钩子是否正常 | 看 `sessions/_health.md`，或运行 `check-health.cmd` |
| 取消某次错误联接 | 在项目里 `rmdir .agent-chats`（只去联接，不动总库） |

### 5.4 安全

对话里可能有密码、Cookie、校园网账号等。  
`.agent-chats/` 必须被 gitignore；**不要**强制 `git add -f` 进去。  
总库若同步到网盘 / Git，同样注意脱敏或保持私有。

---

## 6. 从零复现（另一台电脑 / 重装）

可对照本仓库 `ZERO_TO_ONE.md`，以及用户技能 `hooks-session-archive`。精简清单：

### A. 准备 Vault 仓库

1. 复制或新建本目录结构：`config.json`、`sessions/`、`check-health.*`、空的 `.cursor/hooks.json`、`SCHEMES.md`、本文。  
2. `config.json` 使用 `project_date` + `project_mirror`（见上文）。  
3. 如有旧「按天」目录，运行：

```powershell
cd C:\path\to\cursor-session-vault
python migrate-to-project-layout.py
```

### B. 安装用户级 Hooks

1. 将 `save-session.cmd` / `save-session.py` 放到 `~/.cursor/hooks/`。  
2. 编辑 `~/.cursor/hooks.json`，**合并**（勿抹掉其它钩子）：

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{ "command": "hooks\\save-session.cmd", "timeout": 15 }],
    "stop": [{ "command": "hooks\\save-session.cmd", "timeout": 30 }],
    "sessionEnd": [{ "command": "hooks\\save-session.cmd", "timeout": 30 }]
  }
}
```

3. 脚本内 `DEFAULT_VAULT` 或环境变量 `CURSOR_SESSION_VAULT` 指向本机 Vault 路径。  
4. Cursor **Settings → Hooks** 开启。  
5. 本机 PATH 能找到 `python` 或 `py`。

### C. 验收

1. 打开**非 Vault** 的项目，Agent 发一句，等一轮结束。  
2. Vault 出现：`sessions/<项目名>/<今天>/…md`。  
3. 该项目根目录出现 `.agent-chats`，打开内容与总库一致。  
4. 再聊一轮 → **同一 md 被更新**，不堆副本。  
5. `sessions/_health.md` 的 `last_save_at` 已刷新。  
6. 项目 `.gitignore` 含 `.agent-chats/`。

### D. 禁止事项（复现时）

- 不要在 Vault 项目再挂会写入的 hooks（双写）。  
- 不要默认 `dedupe: snapshot` 狂产生时间戳文件。  
- 不要把 Vault 叫成 Skill；Skill 只是「教人怎么搭」的说明，真正干活的是 Hooks + 本仓库。

---

## 7. 故障排查

| 现象 | 排查 |
|------|------|
| 总库没有新文件 | Settings→Hooks；`_health.md`；Python 是否在 PATH；`sessions/_hook.log` |
| 总库有、项目无 `.agent-chats` | `project_mirror.enabled` 是否 true；看 `_hook.log` 里 `mirror ok` / `mklink failed` |
| 联接指错目录 | 删掉项目里的 `.agent-chats`（`rmdir`），再触发一轮存档 |
| 提示无法创建联接 | 目标路径是否存在；是否已有**同名非空真实文件夹**占位 |
| 旧对话还在日期目录下 | 再跑一次 `migrate-to-project-layout.py` |

手动测试联接（PowerShell）：

```powershell
$target = "C:\path\to\cursor-session-vault\sessions\定时开机"
$link   = "D:\works\unattended-pc\.agent-chats"
cmd /c "mklink /J `"$link`" `"$target`""
```

---

## 8. 相关文件索引

| 文件 | 说明 |
|------|------|
| 本文 `PROJECT_MIRROR.md` | 方案 A 原理 / 使用 / 复现 |
| `README.md` | Vault 总说明书 |
| `SCHEMES.md` | 各种 layout 切换 |
| `config.json` | 当前生效配置 |
| `migrate-to-project-layout.py` | 旧布局迁移 |
| `ZERO_TO_ONE.md` | 从零搭建备忘 |
| `~/.cursor/hooks/save-session.py` | 实现代码（含 `ensure_project_mirror`） |
| `~/.cursor/skills/hooks-session-archive/SKILL.md` | 教 Agent 复刻整套 Vault 的技能 |

---

## 9. 设计取舍（给以后改代码的人）

1. **正文只写 Vault**：项目侧永远是「窗口」，避免双源真相。  
2. **Junction 优先于 copy**：省空间、自动一致。  
3. **gitignore 默认开**：对话含敏感信息是常态。  
4. **钩子失败也要对 Cursor 成功退出**（`echo {}`）：存档挂了不能阻断 Agent。  
5. **改 layout 不自动搬家**：用迁移脚本显式处理，避免静默打乱用户已有路径。
