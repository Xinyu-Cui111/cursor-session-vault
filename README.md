# Cursor Session Vault

把 Cursor Agent 对话自动存成 Markdown，按项目归档。  
换电脑、换项目时还能翻得到；可选在每个项目根目录出现 `.agent-chats`（目录联接，不是拷贝）。

这不是 Skill，也不是业务 App。核心是：**用户级 Hooks + 本仓库当保险库**。

> 新电脑安装请先看 [INSTALL.md](INSTALL.md)。Hooks 模板说明：[hooks-templates/README.md](hooks-templates/README.md)。  
> 项目内镜像原理：[PROJECT_MIRROR.md](PROJECT_MIRROR.md)

## 你会得到什么

- Agent 一轮结束后，自动写入 `sessions/<项目名>/<日期>/…md`
- 正文可读（工具调用细节会省略）
- 开启镜像后，项目侧边栏能直接打开 `.agent-chats`
- `.agent-chats` 会自动进该项目的 `.gitignore`，避免把对话提交进 Git

| 场景 | 会存吗 |
|------|--------|
| 任意工作区，Hooks 已开且 Python 可用 | 会 |
| Hooks 关了 / 没装 Python | 不会 |

关掉项目内镜像：在 `config.json` 里设 `"project_mirror": { "enabled": false }`。

## 和 Cursor 其他能力的关系

| 能力 | 干什么 | 和本仓库 |
|------|--------|----------|
| Hooks | 在 stop / sessionEnd 等节点跑脚本 | **本方案靠它** |
| Skills / Rules | 教 Agent 怎么做事、守规矩 | 无关 |
| MCP | 接外部工具与数据 | 无关 |

记一句就够：想「事件发生时自动跑程序」→ Hooks。

## 仓库里有什么

```
cursor-session-vault/
  config.json / config.example.json
  sessions/                 归档目录（公开前请清空个人对话）
  INSTALL.md                约 10 分钟安装
  PROJECT_MIRROR.md         联接与排查
  SCHEMES.md                方案对照
  hooks-templates/          可复制到 ~/.cursor 的模板（若附带）
```

健康检查：跑仓库里的 `check-health.cmd`（或等价脚本），看 `sessions/_health.md` 是否刷新。

## 注意

- 对话里可能有密钥、路径、账号。公开仓库前务必清 `sessions/`，并用 example 配置。
- Hooks 脚本里的 Vault 路径要改成你本机实际位置。

## 许可

MIT（以仓库内 `LICENSE` 为准，若已添加）。
