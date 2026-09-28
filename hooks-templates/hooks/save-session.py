#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TEMPLATE: copy to %USERPROFILE%\.cursor\hooks\save-session.py
# Then set DEFAULT_VAULT (below) or env CURSOR_SESSION_VAULT to your clone path.
"""
Global Cursor session vault (config-driven).

Hooks: ~/.cursor/hooks.json → this script
Config: <vault>/config.json  (see <vault>/SCHEMES.md)
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_VAULT = Path(r"C:\path\to\cursor-session-vault")

DEFAULT_CONFIG: dict[str, Any] = {
    "scheme": "project_date",
    "layout": "{project}/{date}/{title}__{id}.md",
    "on": ["stop", "sessionEnd"],
    "title_from": "first_user_line",
    "dedupe": "overwrite",
    "index": True,
    "frontmatter": True,
    "debug": False,
    "title_max_len": 40,
    "project_mirror": {
        "enabled": True,
        "mode": "junction",
        "dir": ".agent-chats",
        "gitignore": True,
    },
}


def vault_root() -> Path:
    raw = os.environ.get("CURSOR_SESSION_VAULT", "").strip()
    return Path(raw) if raw else DEFAULT_VAULT


def sessions_root() -> Path:
    out = vault_root() / "sessions"
    out.mkdir(parents=True, exist_ok=True)
    return out


def log_path() -> Path:
    return sessions_root() / "_hook.log"


def log(msg: str) -> None:
    try:
        with log_path().open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")
    except OSError:
        pass


def write_health(update: dict[str, Any]) -> None:
    """Human + machine readable heartbeat so silent failures are visible."""
    path_json = sessions_root() / "_health.json"
    path_md = sessions_root() / "_health.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data: dict[str, Any] = {}
    if path_json.is_file():
        try:
            data = json.loads(path_json.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                data = {}
        except (OSError, json.JSONDecodeError):
            data = {}
    data.update(update)
    data["checked_at"] = now
    data.setdefault("vault", str(vault_root()))
    data.setdefault("python", sys.version.split()[0])
    try:
        path_json.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        ok = bool(data.get("ok", True))
        status = data.get("status") or ("ok" if ok else "error")
        lines = [
            f"# Session Vault 健康状态：{'正常' if ok else '异常'}",
            "",
            f"- status: `{status}`",
            f"- checked_at: `{now}`",
            f"- last_hook_at: `{data.get('last_hook_at') or '—'}`",
            f"- last_save_at: `{data.get('last_save_at') or '—'}`",
            f"- last_event: `{data.get('last_event') or '—'}`",
            f"- last_path: `{data.get('last_path') or '—'}`",
            f"- python: `{data.get('python') or '—'}`",
            f"- vault: `{data.get('vault') or '—'}`",
            "",
            "## 怎么判断坏了",
            "",
            "1. 刚用 Agent 聊完一轮，但 `last_hook_at` / `last_save_at` 没刷新 → Hooks 可能没开，或钩子没跑到。",
            "2. status 为 `python_not_found` → Python 不在 PATH。",
            "3. 双击仓库里的 `check-health.cmd` 做完整自检。",
            "",
        ]
        if data.get("message"):
            lines[1:1] = ["", str(data["message"]), ""]
        path_md.write_text("\n".join(lines), encoding="utf-8")
    except OSError as exc:
        log(f"health write failed: {exc}")


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    path = vault_root() / "config.json"
    try:
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if not str(k).startswith("_")})
    except FileNotFoundError:
        pass
    except (OSError, json.JSONDecodeError) as exc:
        log(f"config load failed: {exc}; using defaults")
    env_debug = os.environ.get("CURSOR_SESSION_VAULT_DEBUG", "").strip().lower()
    if env_debug in {"1", "true", "yes"}:
        cfg["debug"] = True
    return cfg


def read_stdin() -> dict[str, Any]:
    raw_bytes = sys.stdin.buffer.read()
    raw = raw_bytes.decode("utf-8-sig", errors="replace").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log(f"invalid stdin json: {raw[:200]!r}")
        return {}


def safe_slug(text: str, fallback: str = "unknown", max_len: int = 80) -> str:
    text = (text or "").strip()
    if not text:
        return fallback
    text = re.sub(r'[\\/:*?"<>|]+', "_", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("._-")
    return text or fallback


def workspace_slug(payload: dict[str, Any]) -> str:
    roots = payload.get("workspace_roots") or []
    names: list[str] = []
    for raw in roots:
        try:
            names.append(Path(str(raw)).name or "root")
        except Exception:  # noqa: BLE001
            names.append("root")
    if not names:
        return "no-workspace"
    if len(names) == 1:
        return safe_slug(names[0], "workspace")
    return safe_slug("+".join(names), "multi-root")


def day_slug(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y-%m-%d")


def strip_tags(text: str) -> str:
    text = re.sub(r"<timestamp>.*?</timestamp>\s*", "", text, flags=re.S)
    text = re.sub(r"</?user_query>", "", text)
    return text.strip()


def extract_timestamp(text: str) -> str | None:
    m = re.search(r"<timestamp>\s*(.*?)\s*</timestamp>", text or "", flags=re.S)
    if not m:
        return None
    raw = m.group(1).strip()
    # e.g. "Monday, Sep 14, 2026, 11:52 AM (UTC+8)" -> "2026-09-14 11:52"
    try:
        cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", raw).strip()
        dt = datetime.strptime(cleaned, "%A, %b %d, %Y, %I:%M %p")
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return raw


def extract_text_blocks(content: Any) -> list[str]:
    if content is None:
        return []
    if isinstance(content, str):
        return [content] if content.strip() else []
    if isinstance(content, dict):
        if content.get("type") == "text" and isinstance(content.get("text"), str):
            return [content["text"]]
        return []
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            parts.extend(extract_text_blocks(item))
        return parts
    return []


def first_user_title(records: list[dict[str, Any]], max_len: int = 40) -> str:
    for rec in records:
        if rec.get("role") != "user":
            continue
        message = rec.get("message") or {}
        texts = extract_text_blocks(message.get("content"))
        for text in texts:
            cleaned = strip_tags(text)
            if cleaned:
                line = cleaned.splitlines()[0].strip()
                return safe_slug(line, "untitled", max_len=max_len)
    return "untitled"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError as exc:
        log(f"cannot read transcript {path}: {exc}")
    return records


def resolve_transcript(payload: dict[str, Any]) -> Path | None:
    candidates = [
        payload.get("transcript_path"),
        payload.get("agent_transcript_path"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(str(raw))
        if path.is_file():
            return path
        if path.is_dir():
            matches = sorted(path.glob("*.jsonl"))
            if matches:
                return matches[0]
    cid = payload.get("conversation_id") or payload.get("session_id")
    if not cid:
        return None
    home = Path.home() / ".cursor" / "projects"
    if not home.is_dir():
        return None
    for jsonl in home.rglob(f"{cid}.jsonl"):
        if "subagents" in jsonl.parts:
            continue
        return jsonl
    return None


def layout_tokens(
    *,
    payload: dict[str, Any],
    conversation_id: str,
    event_name: str,
    title: str,
    now: datetime,
    cfg: dict[str, Any],
) -> dict[str, str]:
    max_len = int(cfg.get("title_max_len") or 40)
    return {
        "date": day_slug(now),
        "project": workspace_slug(payload),
        "id": conversation_id[:8] if conversation_id != "unknown" else "noid",
        "title": safe_slug(title, "untitled", max_len=max_len),
        "event": safe_slug(event_name, "unknown", max_len=32),
    }


def resolve_out_path(layout: str, tokens: dict[str, str], now: datetime, dedupe: str) -> Path:
    path = layout
    for key, value in tokens.items():
        path = path.replace("{" + key + "}", value)
    if "{" in path or "}" in path:
        raise ValueError(f"unresolved layout placeholders: {path}")
    out = sessions_root() / path
    if dedupe == "snapshot":
        stamp = now.strftime("%H%M%S")
        out = out.with_name(f"{out.stem}_{tokens.get('event', 'evt')}_{stamp}{out.suffix or '.md'}")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def render_body(records: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for rec in records:
        role = rec.get("role")
        if role == "user":
            texts = extract_text_blocks((rec.get("message") or {}).get("content"))
            stamp = None
            bodies: list[str] = []
            for t in texts:
                if stamp is None:
                    stamp = extract_timestamp(t)
                cleaned = strip_tags(t)
                if cleaned:
                    bodies.append(cleaned)
            body = "\n\n".join(bodies)
            if body:
                lines.append("## User")
                lines.append("")
                if stamp:
                    lines.append(f"`{stamp}`")
                    lines.append("")
                lines.append(body)
                lines.append("")
        elif role == "assistant":
            texts = extract_text_blocks((rec.get("message") or {}).get("content"))
            body_parts = [strip_tags(t) for t in texts if strip_tags(t)]
            if body_parts:
                lines.extend(["## Assistant", "", "\n\n".join(body_parts), ""])
        elif rec.get("type") == "turn_ended":
            status = rec.get("status") or ""
            lines.extend(["", f"_turn_ended: {status}_", ""])
    return "\n".join(lines).rstrip()


def render_markdown(
    *,
    conversation_id: str,
    event_name: str,
    payload: dict[str, Any],
    records: list[dict[str, Any]],
    source: str,
    title: str,
    cfg: dict[str, Any],
    now: datetime,
) -> str:
    body = render_body(records)
    roots = payload.get("workspace_roots") or []
    saved_at = now.strftime("%Y-%m-%d %H:%M:%S")
    if cfg.get("frontmatter", True):
        fm = {
            "title": title,
            "conversation_id": conversation_id,
            "date": day_slug(now),
            "project": workspace_slug(payload),
            "hook_event": event_name,
            "model": payload.get("model") or "",
            "saved_at": saved_at,
            "scheme": cfg.get("scheme") or "",
        }
        if roots:
            fm["workspace_roots"] = list(map(str, roots))
        fm_lines = ["---"]
        for k, v in fm.items():
            fm_lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        fm_lines.extend(["---", "", f"# {title}", "", body, ""])
        return "\n".join(fm_lines)
    lines = [
        f"# {title}",
        "",
        f"- saved_at: `{saved_at}`",
        f"- conversation_id: `{conversation_id}`",
        f"- hook_event: `{event_name}`",
        f"- model: `{payload.get('model') or ''}`",
        f"- source: `{source}`",
        f"- project: `{workspace_slug(payload)}`",
        "",
        "---",
        "",
        body,
        "",
    ]
    return "\n".join(lines)


CONV_START = "<!-- conv:{id} -->"
CONV_END = "<!-- /conv:{id} -->"


def write_section_file(path: Path, conversation_id: str, title: str, section_md: str, now: datetime) -> None:
    start = CONV_START.format(id=conversation_id)
    end = CONV_END.format(id=conversation_id)
    block = f"{start}\n## {title}\n\n{section_md.rstrip()}\n{end}\n"
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        pattern = re.compile(
            re.escape(start) + r".*?" + re.escape(end) + r"\n?",
            flags=re.S,
        )
        if pattern.search(text):
            text = pattern.sub(block, text, count=1)
        else:
            text = text.rstrip() + "\n\n" + block
    else:
        header = f"# {day_slug(now)}\n\n"
        text = header + block
    path.write_text(text, encoding="utf-8")


def update_index(entry: dict[str, Any]) -> None:
    index_path = sessions_root() / "_index.jsonl"
    cid = entry.get("conversation_id")
    date = entry.get("date")
    rows: list[dict[str, Any]] = []
    if index_path.is_file():
        for line in index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("conversation_id") == cid and row.get("date") == date:
                continue
            rows.append(row)
    rows.append(entry)
    with index_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def workspace_root_paths(payload: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    for raw in payload.get("workspace_roots") or []:
        try:
            p = Path(str(raw)).expanduser()
            if p.is_dir():
                roots.append(p.resolve())
        except OSError:
            continue
    return roots


def _is_reparse_dir(path: Path) -> bool:
    """True if path is a Windows junction/symlink directory."""
    if not path.exists():
        return False
    try:
        if path.is_symlink():
            return True
    except OSError:
        pass
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
        GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
        GetFileAttributesW.restype = wintypes.DWORD
        attrs = GetFileAttributesW(str(path))
        if attrs == 0xFFFFFFFF:
            return False
        # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        return bool(attrs & 0x400)
    except Exception:  # noqa: BLE001
        return False


def _remove_link_or_empty(path: Path) -> bool:
    """Remove a junction/symlink or empty directory. Refuse non-empty real dirs."""
    if not path.exists() and not path.is_symlink():
        return True
    if _is_reparse_dir(path) or path.is_symlink():
        try:
            path.rmdir()
            return True
        except OSError as exc:
            log(f"mirror remove link failed: {path}: {exc}")
            return False
    if path.is_dir():
        try:
            if any(path.iterdir()):
                log(f"mirror skip: {path} is a non-empty real directory")
                return False
            path.rmdir()
            return True
        except OSError as exc:
            log(f"mirror remove empty dir failed: {path}: {exc}")
            return False
    return False


def ensure_gitignore_entry(project_root: Path, name: str) -> None:
    gi = project_root / ".gitignore"
    line = name if name.endswith("/") else f"{name}/"
    try:
        if gi.is_file():
            text = gi.read_text(encoding="utf-8")
            existing = {ln.strip() for ln in text.splitlines()}
            if line in existing or name in existing or f"/{line}" in existing:
                return
            sep = "" if text.endswith("\n") or not text else "\n"
            gi.write_text(text + sep + f"\n# Cursor Session Vault project mirror\n{line}\n", encoding="utf-8")
        else:
            gi.write_text(f"# Cursor Session Vault project mirror\n{line}\n", encoding="utf-8")
    except OSError as exc:
        log(f"gitignore update failed in {project_root}: {exc}")


def ensure_project_mirror(
    payload: dict[str, Any],
    project_slug: str,
    cfg: dict[str, Any],
) -> None:
    """
    Scheme A: project folder gets `.agent-chats` junction → vault/sessions/{project}/
    so chats are visible in the project tree without duplicating files.
    """
    mirror_cfg = cfg.get("project_mirror")
    if not isinstance(mirror_cfg, dict) or not mirror_cfg.get("enabled", False):
        return
    mode = str(mirror_cfg.get("mode") or "junction").lower()
    if mode not in {"junction", "symlink"}:
        log(f"mirror mode {mode!r} not implemented; use junction")
        return
    link_name = str(mirror_cfg.get("dir") or ".agent-chats").strip() or ".agent-chats"
    if "/" in link_name or "\\" in link_name:
        log(f"mirror dir must be a single folder name, got {link_name!r}")
        return

    target = sessions_root() / project_slug
    target.mkdir(parents=True, exist_ok=True)

    for root in workspace_root_paths(payload):
        # Never create a mirror link inside the vault repo root itself in a way that nests weirdly;
        # still OK to link vault/.agent-chats → sessions/{slug}.
        link = root / link_name
        try:
            if link.exists() or link.is_symlink() or _is_reparse_dir(link):
                try:
                    if link.resolve() == target.resolve():
                        if mirror_cfg.get("gitignore", True):
                            ensure_gitignore_entry(root, link_name)
                        continue
                except OSError:
                    pass
                if not _remove_link_or_empty(link):
                    continue

            if os.name == "nt":
                # Directory junction: no admin required for local dirs.
                completed = __import__("subprocess").run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if completed.returncode != 0:
                    log(
                        "mirror mklink failed "
                        f"rc={completed.returncode} out={completed.stdout!r} err={completed.stderr!r}"
                    )
                    continue
            else:
                link.symlink_to(target, target_is_directory=True)

            if mirror_cfg.get("gitignore", True):
                ensure_gitignore_entry(root, link_name)
            log(f"mirror ok: {link} -> {target}")
        except OSError as exc:
            log(f"mirror error for {root}: {exc}")


def save_session(payload: dict[str, Any], cfg: dict[str, Any]) -> Path | None:
    event_name = str(payload.get("hook_event_name") or "unknown")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Heartbeat for any hook fire (proves Settings→Hooks is actually invoking us).
    write_health(
        {
            "ok": True,
            "status": "hook_alive",
            "last_hook_at": now_str,
            "last_event": event_name,
            "message": "钩子已触发。若之后没有 last_save_at 更新，可能是本轮被 on 过滤或 transcript 为空。",
        }
    )

    if event_name == "sessionStart":
        log("sessionStart heartbeat")
        return None

    allowed = cfg.get("on") or DEFAULT_CONFIG["on"]
    if isinstance(allowed, list) and allowed and event_name not in allowed:
        log(f"skip event {event_name} (on={allowed})")
        return None

    conversation_id = str(
        payload.get("conversation_id")
        or payload.get("session_id")
        or "unknown"
    )
    transcript = resolve_transcript(payload)
    records = load_jsonl(transcript) if transcript else []

    if conversation_id == "unknown" and not records:
        log("skip empty payload")
        write_health(
            {
                "ok": False,
                "status": "empty_payload",
                "last_hook_at": now_str,
                "last_event": event_name,
                "message": "钩子触发了但 payload/transcript 为空（常见于 BOM/解析问题或会话尚未产生记录）。",
            }
        )
        return None

    now = datetime.now()
    max_len = int(cfg.get("title_max_len") or 40)
    title = first_user_title(records, max_len=max_len)
    tokens = layout_tokens(
        payload=payload,
        conversation_id=conversation_id,
        event_name=event_name,
        title=title,
        now=now,
        cfg=cfg,
    )
    dedupe = str(cfg.get("dedupe") or "overwrite")
    layout = str(cfg.get("layout") or DEFAULT_CONFIG["layout"])
    out_path = resolve_out_path(layout, tokens, now, dedupe)

    md = render_markdown(
        conversation_id=conversation_id,
        event_name=event_name,
        payload=payload,
        records=records,
        source=str(transcript) if transcript else "(none)",
        title=title,
        cfg=cfg,
        now=now,
    )

    if dedupe == "section":
        write_section_file(out_path, conversation_id, title, render_body(records), now)
    else:
        out_path.write_text(md, encoding="utf-8")

    if cfg.get("debug"):
        debug_dir = out_path.parent / "_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        stamp = now.strftime("%Y%m%d-%H%M%S")
        (debug_dir / f"{stamp}_{tokens['id']}_{event_name}.hook.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    rel = out_path.relative_to(sessions_root()).as_posix()
    if cfg.get("index", True):
        update_index(
            {
                "conversation_id": conversation_id,
                "id": tokens["id"],
                "title": title,
                "date": tokens["date"],
                "project": tokens["project"],
                "path": rel,
                "hook_event": event_name,
                "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "scheme": cfg.get("scheme") or "",
            }
        )

    write_health(
        {
            "ok": True,
            "status": "saved",
            "last_hook_at": now_str,
            "last_save_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "last_event": event_name,
            "last_path": rel,
            "message": "最近一次存档成功。",
        }
    )
    try:
        ensure_project_mirror(payload, tokens["project"], cfg)
    except Exception as exc:  # noqa: BLE001
        log(f"mirror failed: {exc}")
    log(f"saved {rel} scheme={cfg.get('scheme')} from {transcript}")
    return out_path


def main() -> None:
    payload = read_stdin()
    cfg = load_config()
    try:
        save_session(payload, cfg)
    except Exception as exc:  # noqa: BLE001
        log(f"error: {exc}")
        write_health(
            {
                "ok": False,
                "status": "error",
                "message": f"存档脚本异常: {exc}",
                "last_event": str(payload.get("hook_event_name") or ""),
            }
        )
    sys.stdout.write("{}\n")


if __name__ == "__main__":
    main()
