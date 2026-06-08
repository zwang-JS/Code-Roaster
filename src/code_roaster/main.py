"""
CLI 入口与参数解析
==================
Code Roaster 的命令行主入口。
解析用户参数，编排配置检查、Git Diff 获取、
Agent 调用和流式输出的完整流程。
"""

import argparse
import time

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.color import Color, ColorSystem
from rich import box

from .config import check_config
from .tools import get_git_diff, get_diff_files
from .prompts import get_persona, get_available_personas, PERSONAS, REBUTTAL_INSTRUCTION
from .agent import RoasterAgent
from .history import save_review, show_history, show_stats

console = Console()

# ============================================================
# 预定义的 "CODE ROASTER" ASCII 艺术字
# 使用 Unicode 块字符风格，共 6 行，带精确间距
# ============================================================
_BANNER_LINES = [
    " ██████╗ ██████╗ ██████╗ ███████╗    ██████╗  ██████╗  █████╗ ███████╗████████╗███████╗██████╗ ",
    "██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔═══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗",
    "██║     ██║   ██║██║  ██║█████╗      ██████╔╝██║   ██║███████║███████╗   ██║   █████╗  ██████╔╝",
    "██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗██║   ██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗",
    "╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║╚██████╔╝██║  ██║███████║   ██║   ███████╗██║  ██║",
    " ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝",
]


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """
    将 HSL 颜色值转换为 RGB。

    Args:
        h: 色相 (0.0 ~ 360.0)
        s: 饱和度 (0.0 ~ 100.0)
        l: 亮度 (0.0 ~ 100.0)

    Returns:
        tuple: (r, g, b) 各分量 0-255
    """
    h = (h % 360.0) / 360.0
    s /= 100.0
    l /= 100.0

    if s == 0:
        r = g = b = l
    else:
        def _hue2rgb(p: float, q: float, t: float) -> float:
            if t < 0.0:
                t += 1.0
            if t > 1.0:
                t -= 1.0
            if t < 1.0 / 6.0:
                return p + (q - p) * 6.0 * t
            if t < 1.0 / 2.0:
                return q
            if t < 2.0 / 3.0:
                return p + (q - p) * (2.0 / 3.0 - t) * 6.0
            return p

        q = l * (1.0 + s) if l < 0.5 else l + s - l * s
        p = 2.0 * l - q
        r = _hue2rgb(p, q, h + 1.0 / 3.0)
        g = _hue2rgb(p, q, h)
        b = _hue2rgb(p, q, h - 1.0 / 3.0)

    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def show_banner():
    """
    在终端显示粗体像素风格的 "CODE ROASTER" ASCII 艺术字，
    带从左到右的彩虹颜色水平渐变效果。

    终端兼容性处理：
        - 支持真彩色（TrueColor）的终端 → 显示完整的彩虹渐变
        - 不支持真彩色的终端 → 降级为白色粗体显示

    技术实现：
        使用 rich 库的 Text 和 Color 类，逐字符应用颜色。
        不依赖任何第三方 ASCII 艺术字库（如 pyfiglet）。
    """
    # 检测终端是否支持真彩色
    use_truecolor = console.color_system in (
        ColorSystem.TRUECOLOR,
        ColorSystem.WINDOWS,
    )

    # 计算所有行中最宽的宽度，用于归一化渐变位置
    max_width = max(len(line) for line in _BANNER_LINES) if _BANNER_LINES else 1

    console.print()  # 顶部留白，视觉上更舒适

    if not use_truecolor:
        # --- 降级模式：白色粗体 ---
        for line in _BANNER_LINES:
            console.print(Text(line, style="bold white"))
    else:
        # --- 真彩色模式：彩虹渐变 ---
        # hue 从蓝色(240°) 渐变到红色(0°)，经过青(180°)→绿(120°)→黄(60°)
        for line in _BANNER_LINES:
            row_text = Text()
            for col_idx, ch in enumerate(line):
                if ch.strip():
                    # 计算该字符在整行中的水平位置比例 (0.0 ~ 1.0)
                    t = col_idx / max(max_width - 1, 1)
                    # hue 线性插值: 240° (蓝) → 0° (红)
                    hue = 240.0 - t * 240.0
                    r, g, b = _hsl_to_rgb(hue, 100.0, 50.0)
                    char_color = Color.from_rgb(r, g, b)
                    row_text.append(ch, style=char_color)
                else:
                    # 空格不加颜色，保持透明
                    row_text.append(ch)
            console.print(row_text)

    console.print()  # 底部留白


def select_persona_interactive() -> str:
    """
    显示交互式 Persona 选择菜单，让用户手动选择审查性格。

    通过 rich 渲染一个带编号的菜单，用户输入数字选择。
    如果用户直接回车，默认选择第一个（toxic）。

    Returns:
        str: 用户选择的 persona key（如 "toxic", "professor" 等）
    """
    persona_keys = list(PERSONAS.keys())

    # 构建菜单面板
    menu_text = Text()
    menu_text.append("🎭  请选择代码审查性格\n\n", style="bold bright_cyan")

    for i, key in enumerate(persona_keys, 1):
        p = PERSONAS[key]
        menu_text.append(f"  [{i}] ", style="bold yellow")
        menu_text.append(f"{p['emoji']}  {p['name']}", style="bold white")
        menu_text.append(f"  —  {p['description']}\n", style="dim")

    menu_text.append(f"\n  输入数字 [1-{len(persona_keys)}] 选择", style="italic cyan")
    menu_text.append("，或直接回车使用默认", style="italic dim")

    console.print(Panel(menu_text, border_style="bright_cyan", box=box.ROUNDED))
    console.print()

    # 获取用户输入
    valid_choices = [str(i) for i in range(1, len(persona_keys) + 1)]
    try:
        choice = Prompt.ask(
            "请输入编号",
            choices=valid_choices,
            default="1",
            show_choices=False,
        )
    except KeyboardInterrupt:
        console.print("\n[dim]已取消选择，使用默认性格[/dim]")
        return persona_keys[0]

    idx = int(choice) - 1
    return persona_keys[idx]


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    available = get_available_personas()
    parser = argparse.ArgumentParser(
        prog="code-roaster",
        description=(
            "🔥 Code Roaster — 赛博包工头 🔥\n"
            "一款 AI 驱动的毒舌代码审查工具。\n"
            "自动获取 git diff，由大模型以不同角色风格对你的代码进行精准吐槽。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  roaster                         # 显示 Banner 后交互式选择性格\n"
            "  roaster -p toxic                # 大厂老油条模式\n"
            "  roaster -p professor            # 冷酷教授模式\n"
            "  roaster -p kfc                  # 疯狂星期四模式\n"
            "  roaster -p cheerleader          # 夸夸天使模式\n"
            "  roaster -p tieba                # 贴吧老哥模式\n"
            "  roaster --list-personas         # 列出所有性格\n"
        ),
    )

    parser.add_argument(
        "-p",
        "--persona",
        type=str,
        default=None,
        choices=available,
        help=(
            "选择审查性格。不指定则进入交互式选择菜单。"
            f" 可选: {', '.join(available)}"
        ),
    )

    parser.add_argument(
        "--list-personas",
        action="store_true",
        help="列出所有可用的审查性格",
    )

    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="跳过启动 Banner（适合脚本化使用）",
    )

    parser.add_argument(
        "--history",
        action="store_true",
        help="查看最近的审查历史记录",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="查看本周审查统计报表",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Code Roaster v1.3.0 — 赛博包工头",
    )

    return parser


def list_personas_simple():
    """简单列出所有可用性格。"""
    console.print()
    title = Text("🎭 Code Roaster 可用性格一览", style="bold bright_cyan")
    console.print(Panel(title, box=box.HEAVY, border_style="bright_cyan"))
    console.print()

    for key, p in PERSONAS.items():
        content = Text()
        content.append(f"{p['emoji']}  ", style="bold")
        content.append(f"{p['name']}", style="bold bright_yellow")
        content.append(f"  [{key}]\n", style="dim")
        content.append(f"    {p['description']}", style="white")
        console.print(Panel(content, border_style="blue"))

    console.print()


def show_loading_spinner(message: str = "赛博包工头正在审查你的代码..."):
    """显示加载动画。"""
    return console.status(f"[bold yellow]🔥 {message}[/bold yellow]", spinner="dots")


def select_files_interactive(diff_files: list) -> tuple:
    """
    显示文件选择菜单，让用户选择要审查的文件。

    当 git diff 包含多个文件改动时使用。
    支持: 单文件、多文件（空格分隔）、全部审查。

    Args:
        diff_files: get_diff_files() 返回的文件列表

    Returns:
        tuple: (合并后的 diff 文本, 选中文件名列表)，
               用户取消时返回 (None, None)
    """
    console.print()
    menu = Text()
    menu.append("📁 检测到多个文件改动，请选择要审查的文件：\n\n", style="bold bright_cyan")

    for i, f in enumerate(diff_files, 1):
        menu.append(f"  [{i}] ", style="bold yellow")
        menu.append(f"{f['filename']}", style="bold white")
        menu.append(f"  +{f['added']}/-{f['removed']}\n", style="dim")

    menu.append(f"\n  [a] ", style="bold yellow")
    menu.append("全部审查", style="bold white")
    menu.append(f"  ({len(diff_files)} 个文件)\n", style="dim")
    menu.append(f"\n  输入编号（空格分隔多个），或直接回车审查全部", style="italic dim")

    console.print(Panel(menu, border_style="bright_cyan", box=box.ROUNDED))
    console.print()

    try:
        raw = Prompt.ask("请输入编号", default="a", show_default=False)
    except KeyboardInterrupt:
        return None, None

    raw = raw.strip()

    if raw.lower() == "a" or not raw:
        selected = diff_files
    else:
        try:
            indices = [int(x.strip()) - 1 for x in raw.split()]
            selected = [diff_files[i] for i in indices if 0 <= i < len(diff_files)]
        except (ValueError, IndexError):
            console.print("[yellow]输入无效，默认审查全部。[/yellow]")
            selected = diff_files

    if not selected:
        return None, None

    diff_text = "\n\n".join(f["diff_text"] for f in selected)
    filenames = [f["filename"] for f in selected]
    return diff_text, filenames


def main():
    """主函数 — CLI 入口点。"""
    parser = build_parser()
    args = parser.parse_args()

    # --list-personas 标志
    if args.list_personas:
        list_personas_simple()
        return

    # --history：查看审查历史
    if args.history:
        show_history()
        return

    # --stats：查看统计报表
    if args.stats:
        show_stats()
        return

    # 步骤 0：显示 Banner（除非用户跳过）
    if not args.no_banner:
        show_banner()

    # 步骤 1：检查配置（如果未配置会启动交互式向导，然后优雅退出）
    config = check_config()

    # 步骤 2：如果未通过 -p 指定性格，进入交互式选择
    if args.persona is None:
        persona_name = select_persona_interactive()
    else:
        persona_name = args.persona

    persona = get_persona(persona_name)

    # 打印模式标题
    console.print()
    header = Text(
        f"{persona['emoji']}  Code Roaster — 赛博包工头 [{persona['name']}模式] {persona['emoji']}",
        style="bold bright_yellow",
    )
    console.print(Panel(header, box=box.HEAVY, border_style="bright_yellow"))
    console.print()

    # 步骤 3：获取 git diff（按文件拆分）
    with show_loading_spinner("正在获取代码变更..."):
        diff_files = get_diff_files()
        time.sleep(0.3)

    # 步骤 4：处理空 diff / 错误
    if not diff_files:
        raw_diff = get_git_diff()
        if raw_diff.startswith("❌") or raw_diff.startswith("⚠️") or raw_diff.startswith("📭"):
            console.print(Panel(Text(raw_diff, style="red"), border_style="red", title="出错了"))
        else:
            console.print(
                Panel(
                    Text(persona["no_diff_message"], style="bright_yellow"),
                    border_style="yellow",
                    title=f"{persona['emoji']} {persona['name']} 说",
                )
            )
        return

    # 步骤 5：多文件时让用户选择审查范围
    if len(diff_files) == 1:
        diff_text = diff_files[0]["diff_text"]
        selected_files = [diff_files[0]["filename"]]
    else:
        diff_text, selected_files = select_files_interactive(diff_files)
        if diff_text is None:
            return

    # 步骤 6：实例化 Agent 并流式输出
    agent = RoasterAgent(config, persona_name)

    console.print()
    console.print(
        Panel(
            Text("以下是赛博包工头的毒舌点评 ↓", style="dim italic"),
            border_style="dim",
        )
    )
    console.print()

    # 构建最终输出面板
    output_text = Text("")
    output_panel = Panel(
        output_text,
        title=f"{persona['emoji']} {persona['name']} 的点评",
        border_style="bright_red",
        box=box.ROUNDED,
    )

    accumulated = ""
    try:
        with Live(output_panel, console=console, refresh_per_second=20, transient=False) as live:
            for chunk in agent.roast_stream(diff_text):
                accumulated += chunk
                new_text = Text(accumulated, style="white")
                live.update(
                    Panel(
                        new_text,
                        title=f"{persona['emoji']} {persona['name']} 的点评",
                        border_style="bright_red",
                        box=box.ROUNDED,
                    )
                )

    except KeyboardInterrupt:
        console.print("\n[dim]赛博包工头被你无情打断...[/dim]")
        return
    except Exception as e:
        console.print(f"\n[red]出错了: {e}[/red]")
        return

    console.print()
    console.print(
        Panel(
            Text("💀 以上点评由 AI 生成，请勿过度代入，理性看待代码问题 💀", style="dim italic"),
            border_style="dim",
        )
    )
    console.print()

    # 步骤 7：保存审查记录到历史
    if accumulated:
        save_review(persona_name, persona["emoji"], selected_files, accumulated)

    # ================================================================
    # 步骤 8：反驳模式 — 用户与 AI 对线
    # ================================================================
    console.print()
    try:
        user_input = Prompt.ask(
            f"💬  {persona['emoji']} 不服来辩！输入反驳（直接回车跳过）",
            default="",
            show_default=False,
        )
    except KeyboardInterrupt:
        return

    if not user_input.strip():
        return

    # 构建对话历史（system prompt + diff + roast + 后续对线轮次）
    rebuttal_system = persona["system_prompt"] + REBUTTAL_INSTRUCTION
    conversation: list[dict] = [
        {"role": "system", "content": rebuttal_system},
        {"role": "user", "content": f"以下是需要审查的代码变更：\n\n```diff\n{diff_text}\n```"},
        {"role": "assistant", "content": accumulated},
    ]

    round_num = 1
    while user_input.strip():
        # 退出关键词
        if user_input.strip().lower() in ("quit", "exit", "退出", "算了", "不说了"):
            console.print(f"\n[dim]{persona['emoji']} 对方退出了对线...[/dim]")
            break

        conversation.append({"role": "user", "content": user_input.strip()})

        # 流式输出 AI 回怼
        console.print()
        response_accumulated = ""

        try:
            with Live(
                Panel(Text(""), border_style="bright_magenta", box=box.ROUNDED),
                console=console,
                refresh_per_second=20,
                transient=False,
            ) as live:
                for chunk in agent.rebuttal_stream(conversation):
                    response_accumulated += chunk
                    live.update(
                        Panel(
                            Text(response_accumulated, style="white"),
                            title=f"{persona['emoji']} {persona['name']} 回怼 (第{round_num}回合)",
                            border_style="bright_magenta",
                            box=box.ROUNDED,
                        )
                    )
        except KeyboardInterrupt:
            console.print("\n[dim]对线被强行终止...[/dim]")
            break
        except Exception as e:
            console.print(f"\n[red]对线出错: {e}[/red]")
            break

        conversation.append({"role": "assistant", "content": response_accumulated})

        # 下一轮输入
        console.print()
        round_num += 1
        try:
            user_input = Prompt.ask(
                f"💬  {persona['emoji']} 继续反驳（回车退出）",
                default="",
                show_default=False,
            )
        except KeyboardInterrupt:
            break

    console.print()
    console.print(
        Panel(
            Text(
                f"🏁 对线结束 — 共计 {round_num} 回合。程序员 vs {persona['name']}：互不相让！",
                style="dim italic",
            ),
            border_style="dim",
        )
    )
    console.print()


if __name__ == "__main__":
    main()
