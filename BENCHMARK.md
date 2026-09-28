# cursor-session-vault · 对标三句话

> 日期：2026-09-28 · 第 3 步

## 对标 A

- 名称 / 链接：[cursor-chat-bulk-export](https://github.com/anasabbasdev/cursor-chat-bulk-export)（扩展：按工作区导出 Markdown）
- **他们强在哪**：手动挑选会话、干净导出、带 INDEX；适合一次性备份/交作业。
- **我们场景强在哪**：**Hooks 自动存**、按项目布局、`.agent-chats` 联接所见即所得，不用每次点导出。
- **下一刀偷师哪一点**：给总库加一份极简 `sessions/_README.md` 或强化 INDEX 可读性（日期/标题/项目一览），接近他们的 INDEX 体验。

## 对标 B

- 名称 / 链接：[cursor-history](https://github.com/S2thend/cursor-history)（CLI：浏览/搜索/导出/备份）
- **他们强在哪**：搜索、全量备份还原、跨工作区迁移，工具面完整。
- **我们场景强在哪**：零日常操作成本（开聊即存）+ 健康检查心跳，偏「保险库」不是「档案馆管理器」。
- **下一刀偷师哪一点**：在 `check-health` 增加一项抽查——随机/指定业务项目是否存在有效 `.agent-chats` 联接（INSTALL 里已写过可选增强）。

## 映射回产品卡

下一刀改为：**check-health 增加「项目镜像联接」抽查**（与此前可选增强一致）。
