# 安装（约 10 分钟）

目标：另一台电脑也能「全局自动存档 + 项目里看得见 `.agent-chats`」。

原理：[PROJECT_MIRROR.md](PROJECT_MIRROR.md) · Hooks 模板说明：[hooks-templates/README.md](hooks-templates/README.md) · 总说明：[README.md](README.md)

## 重要：hooks 模板 ≠ 正在运行的 hooks

仓库里的 `hooks-templates/` 是**脱敏模板**（路径写成 `C:\path\to\cursor-session-vault`）。  
本机真正生效的是 `%USERPROFILE%\.cursor\` 下那一套。安装时请拷贝模板并改路径，不要假设克隆下来就能直接存档。

也可用环境变量 `CURSOR_SESSION_VAULT` 指向你的克隆目录，不必改脚本里的默认值。

## 新电脑从零

1. 克隆本仓库到固定路径。
2. 复制 `config.example.json` → `config.json`（按需改）。
3. 按 [hooks-templates/README.md](hooks-templates/README.md) 安装到 `~\.cursor\`，改好 Vault 路径。
4. Cursor → Settings → Hooks → 开启；确认 `python` / `py` 可用。
5. 按下面「验一下」走一遍。

## 本机已装过时（只验收）

1. `config.json`：`project_date` 布局，`project_mirror.enabled` 为 `true`。
2. 用户级 Hooks 已指向本仓库；Hooks 开关已开。
3. 验一下：
   - 打开别的项目，Agent 聊一轮并结束
   - 本仓库出现 `sessions\<项目名>\<今天>\*.md`
   - 该项目根目录出现 `.agent-chats\`（联接）
   - 再聊一轮 → **同一文件被更新**
   - 跑 `check-health.cmd`，无 FAIL

## 常见问题

| 现象 | 先查 |
|------|------|
| 完全不存 | Hooks 是否开启；Python；模板路径是否仍是占位符 |
| 总库存了，项目里没有 | `project_mirror.enabled`；建联接权限 |
| 对话进了 Git | 项目 `.gitignore` 是否含 `.agent-chats/` |

更细排查：[PROJECT_MIRROR.md](PROJECT_MIRROR.md)。