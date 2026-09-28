#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Session Vault health check — run anytime (double-click check-health.cmd)."""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

VAULT = Path(os.environ.get("CURSOR_SESSION_VAULT", r"C:\path\to\cursor-session-vault"))
HOOKS_JSON = Path.home() / ".cursor" / "hooks.json"
HOOK_SCRIPT = Path.home() / ".cursor" / "hooks" / "save-session.py"
HOOK_CMD = Path.home() / ".cursor" / "hooks" / "save-session.cmd"
HEALTH_JSON = VAULT / "sessions" / "_health.json"
HEALTH_MD = VAULT / "sessions" / "_health.md"
STALE_HOURS = 48


def ok(msg: str) -> tuple[str, str]:
    return ("OK", msg)


def warn(msg: str) -> tuple[str, str]:
    return ("WARN", msg)


def fail(msg: str) -> tuple[str, str]:
    return ("FAIL", msg)


def parse_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


def check_python() -> tuple[str, str]:
    py = shutil.which("python") or shutil.which("py")
    if not py:
        return fail("PATH 中找不到 python / py。安装 Python 3 并勾选 Add to PATH。")
    return ok(f"找到解释器: {py} (runtime {sys.version.split()[0]})")


def check_hooks_config() -> tuple[str, str]:
    if not HOOKS_JSON.is_file():
        return fail(f"缺少用户级钩子配置: {HOOKS_JSON}")
    try:
        data = json.loads(HOOKS_JSON.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return fail(f"hooks.json 无法解析: {exc}")
    hooks = (data or {}).get("hooks") or {}
    needed = ("stop", "sessionEnd")
    missing = [k for k in needed if not hooks.get(k)]
    if missing:
        return fail(f"hooks.json 缺少事件: {', '.join(missing)}")
    has_start = bool(hooks.get("sessionStart"))
    extra = "含 sessionStart 心跳" if has_start else "建议加上 sessionStart 便于发现 Hooks 是否在跑"
    return ok(f"用户级 hooks 已配置 stop/sessionEnd；{extra}")


def check_hook_files() -> tuple[str, str]:
    missing = [str(p) for p in (HOOK_SCRIPT, HOOK_CMD) if not p.is_file()]
    if missing:
        return fail("缺少钩子脚本: " + "; ".join(missing))
    return ok("save-session.py / save-session.cmd 存在")


def check_vault() -> tuple[str, str]:
    cfg = VAULT / "config.json"
    if not VAULT.is_dir():
        return fail(f"Vault 目录不存在: {VAULT}")
    if not cfg.is_file():
        return warn(f"缺少 config.json（将用脚本默认值）: {cfg}")
    return ok(f"Vault 就绪: {VAULT}")


def check_heartbeat() -> tuple[str, str]:
    if not HEALTH_JSON.is_file():
        return warn(
            "还没有 _health.json。请新开/继续一次 Agent 对话触发钩子；"
            "若聊完仍没有，多半是 Settings→Hooks 未启用或未加载用户钩子。"
        )
    try:
        data = json.loads(HEALTH_JSON.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return fail("_health.json 损坏，可删除后重聊一轮生成")
    if data.get("ok") is False:
        return fail(f"健康文件报错: {data.get('status')} — {data.get('message')}")
    last_hook = parse_time(data.get("last_hook_at") or data.get("checked_at"))
    last_save = parse_time(data.get("last_save_at"))
    bits = [
        f"status={data.get('status')}",
        f"last_hook_at={data.get('last_hook_at') or '—'}",
        f"last_save_at={data.get('last_save_at') or '—'}",
    ]
    if last_hook and datetime.now() - last_hook > timedelta(hours=STALE_HOURS):
        return warn(
            "超过 "
            f"{STALE_HOURS}h 没有钩子心跳。若这段时间你用过 Agent，请检查 Settings→Hooks。"
            f" ({'; '.join(bits)})"
        )
    if last_hook and not last_save:
        return warn("有钩子心跳但尚未成功存档: " + "; ".join(bits))
    return ok("心跳正常: " + "; ".join(bits))


def main() -> int:
    checks = [
        ("Python", check_python),
        ("hooks.json", check_hooks_config),
        ("钩子脚本", check_hook_files),
        ("Vault", check_vault),
        ("心跳", check_heartbeat),
    ]
    rows: list[tuple[str, str, str]] = []
    worst = 0  # 0 ok, 1 warn, 2 fail
    for name, fn in checks:
        level, msg = fn()
        rows.append((name, level, msg))
        if level == "FAIL":
            worst = 2
        elif level == "WARN" and worst < 1:
            worst = 1

    lines = [
        "# Session Vault 自检报告",
        "",
        f"- generated_at: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- vault: `{VAULT}`",
        "",
        "| 检查项 | 结果 | 说明 |",
        "|--------|------|------|",
    ]
    for name, level, msg in rows:
        lines.append(f"| {name} | **{level}** | {msg} |")
    lines.extend(
        [
            "",
            "## 若 FAIL / WARN 怎么处理",
            "",
            "1. **Python** → 安装/修复 PATH，开新终端执行 `python --version`",
            "2. **hooks.json / 脚本** → 不应缺失；可让 Agent 按本仓库 README 重建用户级钩子",
            "3. **心跳缺失或过期** → Cursor Settings → Hooks 打开；确认能看到用户级 stop/sessionEnd；",
            "   然后任意项目聊一句 Agent，再看 `sessions/_health.md`",
            "4. 仍不行 → Output 面板选 Hooks 通道查看报错",
            "",
        ]
    )
    report = "\n".join(lines)
    print(report)
    try:
        (VAULT / "sessions").mkdir(parents=True, exist_ok=True)
        (VAULT / "sessions" / "_health_check.md").write_text(report, encoding="utf-8")
        # Keep _health.md pointing humans at latest check summary when failing.
        if worst == 2:
            HEALTH_MD.write_text(
                report
                + "\n> 由 check-health 写入：当前存在 FAIL，存档可能不可用。\n",
                encoding="utf-8",
            )
    except OSError as exc:
        print(f"(无法写报告文件: {exc})", file=sys.stderr)

    return worst


if __name__ == "__main__":
    raise SystemExit(main())
