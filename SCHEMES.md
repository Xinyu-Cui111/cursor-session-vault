# 会话存档管理方案手册

改方案时：编辑本仓库根目录的 `config.json`，保存后下一轮钩子生效（一般无需改 hooks 脚本）。  
当前启用方案看 `config.json` 的 `scheme` / `layout` 字段。

---

## 快速切换

在 `config.json` 里改 `layout`（以及可选的 `on` / `dedupe`）即可。

| 方案代号 | `layout` 示例 | 适合 |
|----------|---------------|------|
| **project_date**（当前） | `{project}/{date}/{title}__{id}.md` | 先按项目归档 + 项目内 `.agent-chats` 联接 |
| recommended | `{date}/{title}__{id}.md` | 仅总库按天浏览 |
| flat_id | `{id}.md` | 极简扁平，靠 frontmatter / index 检索 |
| daily_digest | `{date}.md` | 一天一份日记，多段对话写进同一文件 |
| legacy_id | `{date}/{project}/{id}.md` | 旧版：日期 → 项目 → 短 id |

`layout` 可用占位符：

| 占位符 | 含义 | 例 |
|--------|------|----|
| `{date}` | 当天 `YYYY-MM-DD` | `2026-09-14` |
| `{project}` | 工作区文件夹名 | `cursor-session-vault` |
| `{id}` | conversation_id 前 8 位 | `5ab0dcdd` |
| `{title}` | 首条用户消息首行（消毒后） | `你好` |
| `{event}` | 钩子事件名 | `stop` / `sessionEnd` |

输出根目录固定为：`sessions/`（相对本 vault）。

---

## 方案详解

### 1. project_date — 先项目再日期（**当前默认**）

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

```
sessions/
  定时开机/
    2026-09-28/
      标题__a597cd93.md
```

每个打开过 Agent 的工作区根目录还会出现：

```
<项目>/
  .agent-chats/          ← Windows 目录联接 → vault/sessions/<项目名>/
  .gitignore             ← 自动追加忽略 .agent-chats/
```

- **优点**：总库按项目清晰；项目侧边栏也能直接打开本项目对话（不占双份磁盘）  
- **缺点**：想「看今天所有项目对话」要进多个项目目录（可查 `_index.jsonl`）  
- **何时换**：多项目并行、且希望在项目里看到聊天记录（方案 A）

从旧的「按天平铺」迁到本布局，可在 vault 根目录运行一次：

```text
python migrate-to-project-layout.py
```

### 2. recommended — 按天 + 可读标题（旧默认）

```json
{
  "scheme": "recommended",
  "layout": "{date}/{title}__{id}.md",
  "on": ["stop", "sessionEnd"],
  "dedupe": "overwrite",
  "index": true,
  "frontmatter": true
}
```

```
sessions/
  2026-09-14/
    你好__5ab0dcdd.md
  _index.jsonl
```

- **优点**：按日翻找自然；文件名可读；`__{id}` 避免同标题冲突  
- **缺点**：跨项目挤在同一天；项目目录里看不到对话  
- **何时换**：只在总库按天浏览、关闭 `project_mirror` 时

### 3. flat_id — 全局扁平

```json
{
  "scheme": "flat_id",
  "layout": "{id}.md",
  "index": true,
  "frontmatter": true
}
```

```
sessions/
  5ab0dcdd.md
  _index.jsonl
```

- **优点**：路径最短；同一 conversation 永远同一文件（跨天也覆盖）  
- **缺点**：目录里全是 id，必须靠 index / 编辑器搜索标题  
- **何时换**：对话量小，或主要用脚本/`_index.jsonl` 查询

### 4. daily_digest — 一日一记

```json
{
  "scheme": "daily_digest",
  "layout": "{date}.md",
  "dedupe": "section",
  "on": ["sessionEnd"]
}
```

```
sessions/
  2026-09-14.md
```

- **优点**：最简洁；适合日记式回顾  
- **缺点**：单文件会变长；多对话靠文件内 section 分隔  
- **实现要点**：`dedupe: "section"` 时按 `conversation_id` 替换当日文件中的对应段落；建议 `on` 只用 `sessionEnd` 减少写入  
- **何时换**：更在意「今天聊了什么」而不是「某个对话全文文件」

### 5. legacy_id — 旧版日期/项目/id

```json
{
  "scheme": "legacy_id",
  "layout": "{date}/{project}/{id}.md"
}
```

- **优点**：与早期目录兼容  
- **缺点**：文件名不直观  
- **何时换**：需要兼容旧脚本或旧肌肉记忆时

---

## 触发与去重（所有方案共用）

### `on` — 何时写入

| 值 | 含义 |
|----|------|
| `["stop", "sessionEnd"]` | 每轮结束 + 关会话都更新（实时备份，推荐） |
| `["sessionEnd"]` | 仅关会话时写入（更干净；中途崩溃可能少最后几轮） |
| `["stop"]` | 仅每轮结束 |

对应 Cursor 钩子仍挂在 `~/.cursor/hooks.json`；脚本内会按 `on` **过滤**，不必每次改 hooks。

### `dedupe` — 如何避免重复文件

| 值 | 含义 |
|----|------|
| `overwrite` | 同一 layout 路径覆盖写（推荐方案默认） |
| `section` | 用于 `{date}.md`：按 conversation 更新文件内一节 |
| `snapshot` | 每次另存 `..._{event}_{timestamp}.md`（占空间，仅排障用） |

### 其它开关

| 字段 | 含义 |
|------|------|
| `index` | 是否维护 `sessions/_index.jsonl`（一行一条会话元数据） |
| `frontmatter` | Markdown 是否带 YAML 头（title / id / project / date…） |
| `debug` | `true` 时在同目录 `_debug/` 写钩子原始 JSON |
| `title_max_len` | `{title}` 最大字符数（默认 40） |
| `project_mirror` | 见下表：把总库项目目录「映」到各工作区 |

#### `project_mirror`（方案 A）

| 字段 | 含义 | 默认 |
|------|------|------|
| `enabled` | 是否在项目根创建联接目录 | `true` |
| `mode` | `junction`（Windows 目录联接） | `junction` |
| `dir` | 项目里的文件夹名（单层） | `.agent-chats` |
| `gitignore` | 自动把该目录写入项目 `.gitignore` | `true` |

关闭项目内可见：`"project_mirror": { "enabled": false }`。

也可用环境变量临时覆盖：

- `CURSOR_SESSION_VAULT` — vault 根目录  
- `CURSOR_SESSION_VAULT_DEBUG=1` — 等同 `debug: true`

---

## 切换步骤 checklist

1. 打开 `SCHEMES.md`，选定方案  
2. 把对应 JSON 片段合并进 `config.json`（至少改 `scheme` + `layout`）  
3. 可选：改 `on` / `dedupe` / `index`  
4. 新开或继续任意 Agent 对话，跑完一轮  
5. 看 `sessions/` 与 `sessions/_hook.log` 是否符合预期  

**注意**：改 layout 不会自动迁移旧文件；旧目录可手动留着或删掉。新对话按新 layout 写入。

---

## 与 Hooks 层的关系（勿混淆）

| 层级 | 管什么 |
|------|--------|
| `~/.cursor/hooks.json` | 全局是否跑存档脚本（stop / sessionEnd） |
| 本仓库 `config.json` | 存哪儿、叫什么、是否去重、写不写 index |
| 本文件 `SCHEMES.md` | 方案说明与切换手册 |

作用域（项目级 vs 用户级）、command vs prompt 钩子等，见 `README.md`。
