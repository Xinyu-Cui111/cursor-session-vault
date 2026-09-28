# hooks-templates（脱敏模板）

这里是给**新机器安装**用的副本，不是 Cursor 正在跑的那份。

## 为什么单独放模板

本机真正生效的文件在：

- `%USERPROFILE%\.cursor\hooks.json`
- `%USERPROFILE%\.cursor\hooks\save-session.cmd`
- `%USERPROFILE%\.cursor\hooks\save-session.py`

仓库里的模板已去掉真实盘符，默认写成 `C:\path\to\cursor-session-vault`。  
直接整夹覆盖 `~\.cursor` 而不改路径，归档会写到错误位置。

## 怎么装

1. 克隆本仓库到固定路径（以后尽量别挪）。
2. 把 `hooks-templates\hooks.json` 拷到 `%USERPROFILE%\.cursor\hooks.json`（若已有 hooks，请合并 `stop` / `sessionEnd` / `sessionStart` 段，不要盲目覆盖）。
3. 把 `hooks-templates\hooks\*` 拷到 `%USERPROFILE%\.cursor\hooks\`。
4. 编辑 `save-session.cmd` 和 `save-session.py` 里的 Vault 路径，或设置环境变量 `CURSOR_SESSION_VAULT`。
5. Cursor → Settings → Hooks → 开启；确认 `python` / `py` 在 PATH。
6. 按仓库根目录 [INSTALL.md](../INSTALL.md) 验收。

## 和仓库内 `.cursor` 的关系

公开包**不包含**会指向作者本机路径的全局 hooks。  
若你在本仓库里看到空的项目级 hooks，那是为了避免和用户级 hooks 重复存档。
