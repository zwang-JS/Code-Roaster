"""
审查历史与统计模块
==================
管理每次代码审查的记录，支持历史回顾和每周统计。

存储位置: ~/.code-roaster/history.json
每条记录包含：时间、Persona、文件列表、点评内容
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

# 用户数据目录
_HISTORY_DIR = Path.home() / ".code-roaster"
_HISTORY_FILE = _HISTORY_DIR / "history.json"

# 最多保留的记录数
_MAX_RECORDS = 200


def _ensure_dir() -> None:
    """确保历史记录目录存在。"""
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_review(persona_name: str, persona_emoji: str, files: list[str],
                roast_text: str) -> None:
    """
    保存一条审查记录。

    Args:
        persona_name: 使用的 Persona 名称
        persona_emoji: Persona 图标
        files: 被审查的文件名列表
        roast_text: AI 生成的点评文本
    """
    _ensure_dir()

    records = _load_all()

    record = {
        "time": datetime.now().astimezone().isoformat(),
        "persona": persona_name,
        "persona_emoji": persona_emoji,
        "files": files,
        "roast": roast_text[:500],  # 只保留前 500 字
    }
    records.append(record)

    # 只保留最近 _MAX_RECORDS 条
    if len(records) > _MAX_RECORDS:
        records = records[-_MAX_RECORDS:]

    try:
        # 简单文件锁：重试 3 次避免并发写冲突
        for attempt in range(3):
            try:
                _HISTORY_FILE.write_text(
                    json.dumps(records, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                break
            except (OSError, PermissionError):
                if attempt < 2:
                    time.sleep(0.1)
    except Exception:
        pass  # 保存失败不影响主流程


def _load_all() -> list[dict]:
    """加载全部历史记录。"""
    _ensure_dir()
    if not _HISTORY_FILE.exists():
        return []
    try:
        data = _HISTORY_FILE.read_text(encoding="utf-8")
        return json.loads(data) if data.strip() else []
    except (json.JSONDecodeError, Exception):
        return []


def _parse_time(time_str: str):
    """
    解析 ISO 时间字符串为 naive datetime。

    兼容带时区和不带时区的格式，始终返回无时区的 datetime，
    避免和 datetime.now()（naive）比较时出错。

    Args:
        time_str: ISO 格式的时间字符串

    Returns:
        datetime | None: 解析成功返回 naive datetime，失败返回 None
    """
    try:
        dt = datetime.fromisoformat(time_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


def show_history(limit: int = 20) -> None:
    """
    在终端显示最近 N 条审查记录。

    Args:
        limit: 显示条数，默认 20
    """
    records = _load_all()
    if not records:
        console.print(
            Panel(
                "[dim]还没有任何审查记录。[/dim]\n运行 [bold]roaster[/bold] 开始你的第一次被骂之旅吧！",
                title="📋 审查历史",
                border_style="cyan",
            )
        )
        return

    recent = records[-limit:]

    console.print()
    console.print(
        Panel(
            Text(f"📋 最近 {len(recent)} 条审查记录", style="bold bright_cyan"),
            box=box.HEAVY,
            border_style="bright_cyan",
        )
    )
    console.print()

    for i, r in enumerate(reversed(recent), 1):
        try:
            dt = _parse_time(r["time"])
            time_str = dt.strftime("%m/%d %H:%M") if dt else r.get("time", "?")
        except Exception:
            time_str = r.get("time", "?")

        files_str = ", ".join(r.get("files", ["?"])[:3])
        if len(r.get("files", [])) > 3:
            files_str += f" 等 {len(r['files'])} 个文件"

        preview = r.get("roast", "")[:80].replace("\n", " ")

        console.print(
            Panel(
                Text(
                    f"{r.get('persona_emoji', '')}  [{r.get('persona', '?')}]  {time_str}\n"
                    f"📁 {files_str}\n"
                    f"💬 {preview}...",
                    style="white",
                ),
                border_style="blue",
            )
        )

    console.print()


def show_stats() -> None:
    """
    显示本周审查统计报表。

    统计维度:
        - 本周被骂次数
        - 涉及文件数
        - 各 Persona 使用频率
    """
    records = _load_all()
    if not records:
        console.print(
            Panel(
                "[dim]还没有任何审查记录。[/dim]",
                title="📊 审查统计",
                border_style="cyan",
            )
        )
        return

    # 筛选本周记录
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    weekly = []
    for r in records:
        dt = _parse_time(r["time"])
        if dt is not None and dt >= week_start:
            weekly.append(r)

    # 统计数据
    total_reviews = len(weekly)
    all_time_reviews = len(records)

    # 统计 Persona 使用次数
    persona_counts = {}
    for r in weekly:
        p = r.get("persona", "unknown")
        persona_counts[p] = persona_counts.get(p, 0) + 1

    # 统计所有时间的 Persona 排名
    all_persona_counts = {}
    for r in records:
        p = r.get("persona", "unknown")
        all_persona_counts[p] = all_persona_counts.get(p, 0) + 1

    # 找出最爱 Persona
    favorite = max(all_persona_counts, key=all_persona_counts.get) if all_persona_counts else "?"

    console.print()
    console.print(
        Panel(
            Text("📊 审查统计报表", style="bold bright_cyan"),
            box=box.HEAVY,
            border_style="bright_cyan",
        )
    )
    console.print()

    # 概览面板
    overview = Text()
    overview.append(f"📅 本周范围: ", style="dim")
    overview.append(f"{week_start.strftime('%m/%d')} - {now.strftime('%m/%d')}\n\n", style="white")
    overview.append(f"🔥 本周被骂: ", style="dim")
    overview.append(f"{total_reviews} 次\n", style="bold bright_yellow")
    overview.append(f"📚 历史总计: ", style="dim")
    overview.append(f"{all_time_reviews} 次\n", style="white")
    overview.append(f"❤️  最爱角色: ", style="dim")
    overview.append(f"{favorite}\n", style="bold bright_magenta")

    console.print(Panel(overview, title="📋 概览", border_style="blue"))
    console.print()

    # Persona 使用排行表
    if persona_counts:
        table = Table(title="🎭 本周 Persona 使用排行", box=box.ROUNDED, border_style="blue")
        table.add_column("Persona", style="bold")
        table.add_column("次数", justify="right", style="bright_yellow")
        table.add_column("占比", justify="right", style="cyan")
        table.add_column("活跃度", style="dim")

        sorted_personas = sorted(persona_counts.items(), key=lambda x: x[1], reverse=True)
        for name, count in sorted_personas:
            pct = count / total_reviews * 100 if total_reviews > 0 else 0
            bar = "█" * min(int(count), 20)
            table.add_row(name, str(count), f"{pct:.0f}%", bar)

        console.print(table)
        console.print()

    # 空记录提示
    if total_reviews == 0:
        console.print(
            Panel(
                "[dim]本周还没有审查记录，快去改点代码然后跑 [bold]roaster[/bold] 吧！[/dim]",
                border_style="yellow",
            )
        )

    console.print()
    console.print(
        Panel(
            f"📁 历史记录文件: [dim]{_HISTORY_FILE}[/dim]",
            border_style="dim",
        )
    )
    console.print()
