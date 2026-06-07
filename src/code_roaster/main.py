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
from rich import box

from .config import check_config
from .tools import get_git_diff
from .prompts import get_persona, get_available_personas
from .agent import RoasterAgent

console = Console()


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
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
            "  python -m code_roaster.main                  # 默认毒舌老油条\n"
            "  python -m code_roaster.main -p professor     # 冷酷教授模式\n"
            "  python -m code_roaster.main -p coworker      # 阴阳同事模式\n"
            "  python -m code_roaster.main -p kfc           # 疯狂星期四模式\n"
            "  python -m code_roaster.main --list-personas  # 列出所有性格\n"
        ),
    )

    parser.add_argument(
        "-p",
        "--persona",
        type=str,
        default="toxic",
        choices=get_available_personas(),
        help="选择审查性格 (默认: toxic)",
    )

    parser.add_argument(
        "--list-personas",
        action="store_true",
        help="列出所有可用的审查性格",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Code Roaster v1.0.0 — 赛博包工头",
    )

    return parser


def list_personas_simple():
    """简单列出所有可用性格。"""
    from .prompts import PERSONAS

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


def main():
    """主函数 — CLI 入口点。"""
    parser = build_parser()
    args = parser.parse_args()

    # --list-personas 标志
    if args.list_personas:
        list_personas_simple()
        return

    # 步骤 1：检查配置（如果未配置会优雅退出）
    config = check_config()

    persona = get_persona(args.persona)

    # 打印标题
    console.print()
    header = Text(
        f"{persona['emoji']}  Code Roaster — 赛博包工头 [{persona['name']}模式] {persona['emoji']}",
        style="bold bright_yellow",
    )
    console.print(Panel(header, box=box.HEAVY, border_style="bright_yellow"))
    console.print()

    # 步骤 2：获取 git diff
    with show_loading_spinner("正在获取代码变更..."):
        diff_text = get_git_diff()
        time.sleep(0.3)  # 给用户一点动画观看时间

    # 步骤 3：处理空 diff
    if not diff_text or diff_text.startswith("❌") or diff_text.startswith("⚠️") or diff_text.startswith("📭"):
        if diff_text.startswith("❌") or diff_text.startswith("⚠️") or diff_text.startswith("📭"):
            console.print(Panel(Text(diff_text, style="red"), border_style="red", title="出错了"))
        else:
            # diff 为空，打印性格专属的摸鱼嘲讽
            console.print(
                Panel(
                    Text(persona["no_diff_message"], style="bright_yellow"),
                    border_style="yellow",
                    title=f"{persona['emoji']} {persona['name']} 说",
                )
            )
        return

    # 步骤 4：实例化 Agent 并流式输出
    agent = RoasterAgent(config, args.persona)

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

    try:
        with Live(output_panel, console=console, refresh_per_second=20, transient=False) as live:
            accumulated = ""
            for chunk in agent.roast_stream(diff_text):
                accumulated += chunk
                # 更新 panel 内容
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


if __name__ == "__main__":
    main()
