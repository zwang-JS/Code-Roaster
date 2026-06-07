"""
配置管理与用户引导中心
======================
负责加载 .env 环境变量，检查配置完整性，
并在缺少 API Key 时提供一键式交互配置向导。
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich import box

# 项目根目录（code-roaster/）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 加载 .env 文件
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()  # 尝试从当前工作目录加载

console = Console()

# ------------------------------------------------------------
# 平台预设：BASE_URL 和默认 MODEL
# ------------------------------------------------------------
_PLATFORM_PRESETS = {
    "1": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "2": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "3": {
        "name": "智谱 AI (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
    "4": {
        "name": "自定义（手动输入）",
        "base_url": None,
        "model": None,
    },
}


def check_config() -> dict:
    """
    检查配置是否完整。

    如果 ROASTER_API_KEY 未设置或为空，自动启动交互式配置向导。
    向导完成后会创建 .env 文件并退出，用户需重新运行。

    Returns:
        dict: 包含 base_url, api_key, model 的配置字典
    """
    api_key = os.getenv("ROASTER_API_KEY", "").strip()
    base_url = os.getenv("ROASTER_BASE_URL", "https://api.deepseek.com/v1").strip()
    model = os.getenv("ROASTER_MODEL", "deepseek-chat").strip()

    if not api_key:
        # 检查是否在交互式终端中
        if sys.stdin.isatty():
            setup_wizard()
        else:
            _show_onboarding()
        sys.exit(0)

    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }


def setup_wizard():
    """
    交互式配置向导 —— 一键配齐 .env。

    引导用户：
    1. 选择大模型平台（DeepSeek / OpenAI / 智谱 / 自定义）
    2. 输入 API Key
    3. 自动写入 .env 文件
    """
    # -- 欢迎 --
    console.print()
    console.print()
    console.print(
        Panel(
            "🔥 欢迎使用 Code Roaster — 赛博包工头！🔥",
            style="bold bright_yellow",
            box=box.HEAVY,
            border_style="bright_yellow",
        )
    )
    console.print()
    console.print(
        Panel(
            "检测到你是第一次使用，需要配置大模型 API Key。\n"
            "别紧张，跟着下面的提示一步步来，30 秒搞定 ✨",
            title="👋 一键配置向导",
            border_style="cyan",
        )
    )
    console.print()

    # -- 步骤 1：选择平台 --
    platform_text = Text()
    platform_text.append("请选择你要使用的大模型平台：\n\n", style="white")
    for key, preset in _PLATFORM_PRESETS.items():
        platform_text.append(
            f"  [{key}] {preset['name']}\n",
            style="white",
        )

    console.print(
        Panel(platform_text, title="🔌 步骤 1/3：选择平台", border_style="green")
    )
    console.print()

    try:
        choice = Prompt.ask(
            "请输入编号",
            choices=list(_PLATFORM_PRESETS.keys()),
            default="1",
            show_choices=False,
        )
    except KeyboardInterrupt:
        console.print("\n[dim]已取消，下次再来配置吧～[/dim]")
        return

    preset = _PLATFORM_PRESETS[choice]

    # -- 步骤 2：输入 API Key --
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"你选择了 [bold]{preset['name']}[/bold]\n\n"
                f"请粘贴你的 API Key（输入时不显示，这是正常的）："
            ),
            title="🔑 步骤 2/4：输入 API Key",
            border_style="green",
        )
    )
    console.print()

    try:
        # password=True 让输入不可见
        api_key = Prompt.ask("API Key", password=True)
    except KeyboardInterrupt:
        console.print("\n[dim]已取消[/dim]")
        return

    if not api_key.strip():
        console.print("[yellow]API Key 为空，配置取消。[/yellow]")
        return

    # -- 步骤 3：输入/确认 BASE_URL --
    base_url = preset["base_url"]
    if choice == "4" or base_url is None:
        console.print()
        console.print(
            Panel(
                Text("请输入 API 端点地址。如果你不确定，直接回车使用默认值即可。"),
                title="🔗 步骤 3/4：API 端点地址",
                border_style="green",
            )
        )
        base_url = Prompt.ask(
            "BASE_URL",
            default="https://api.openai.com/v1",
        )
    else:
        console.print()
        console.print(
            Panel(
                Text.from_markup(
                    f"API 端点地址已自动填入: [bold cyan]{base_url}[/bold cyan]"
                ),
                title="🔗 步骤 3/4：API 端点地址（自动）",
                border_style="green",
            )
        )
        custom_url = Prompt.ask(
            "如需修改请输入新地址，否则直接回车",
            default="",
        )
        if custom_url.strip():
            base_url = custom_url.strip()

    # -- 步骤 4：输入模型名称 --
    default_model = preset["model"] or "gpt-4o-mini"
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"请输入模型名称。\n"
                f"当前平台 [bold]{preset['name']}[/bold] 推荐使用 [bold cyan]{default_model}[/bold cyan]\n\n"
                f"你也可以输入其他模型名称（如 deepseek-chat、gpt-4o、glm-4-flash 等）。"
            ),
            title="🧠 步骤 4/4：模型名称",
            border_style="green",
        )
    )
    model = Prompt.ask(
        "MODEL",
        default=default_model,
    )

    # -- 写入 .env --
    console.print()
    env_path = PROJECT_ROOT / ".env"

    try:
        # 直接写入 .env 文件
        env_content = (
            f"# Code Roaster 配置文件\n"
            f"# 由交互式配置向导自动生成\n\n"
            f"ROASTER_BASE_URL={base_url}\n"
            f"ROASTER_API_KEY={api_key}\n"
            f"ROASTER_MODEL={model}\n"
        )
        env_path.write_text(env_content, encoding="utf-8")

        # 重新加载环境变量
        load_dotenv(env_path, override=True)

        # 用 console.print 直接渲染 Rich 标记，避免 Text 不解析的问题
        console.print(
            Panel(
                f"✅ 配置完成！\n\n"
                f"   平台: [bold]{preset['name']}[/bold]\n"
                f"   模型: [bold]{model}[/bold]\n"
                f"   Key:  [dim]{api_key[:8]}...{api_key[-4:]}[/dim]\n\n"
                f"配置文件已保存到: [bold cyan]{env_path}[/bold cyan]",
                title="🎉 配置成功",
                border_style="bright_green",
            )
        )
        console.print()
        console.print(
            Panel(
                "现在重新运行 [bold cyan]roaster[/bold cyan] 就可以开始使用了！🚀",
                border_style="bright_cyan",
            )
        )
        console.print()

    except Exception as e:
        console.print(f"\n[red]写入配置文件失败: {e}[/red]")
        console.print("[yellow]请手动创建 .env 文件。[/yellow]")


def _show_onboarding():
    """
    降级兜底 —— 静态新手指引（非交互式终端中使用）。

    当终端不支持交互（如管道、重定向）时，打印文字指引。
    """
    title = Text("🔥 欢迎使用 Code Roaster — 赛博包工头 🔥", style="bold bright_yellow")
    console.print()
    console.print(Panel(title, box=box.HEAVY, border_style="bright_yellow"))
    console.print()

    intro = (
        "看起来你是第一次运行 Code Roaster！\n"
        "在使用之前，需要先配置你的大模型 API Key。\n"
        "请在你的终端中交互式运行 [bold]roaster[/bold] 来启动一键配置向导。\n\n"
        "或者手动配置：\n"
        "1. 在项目根目录创建 .env 文件\n"
        "2. 写入以下内容并替换为你的真实 Key：\n\n"
        "   ROASTER_BASE_URL=https://api.deepseek.com/v1\n"
        "   ROASTER_API_KEY=你的Key\n"
        "   ROASTER_MODEL=deepseek-chat"
    )
    console.print(Panel(intro, title="👋 新手指引", border_style="cyan"))
    console.print()

    # 支持的平台速查表
    table = Table(title="📋 常用平台配置速查", box=box.ROUNDED, border_style="blue")
    table.add_column("平台", style="bold", no_wrap=True)
    table.add_column("BASE_URL", style="dim")
    table.add_column("MODEL 示例")

    table.add_row("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat")
    table.add_row("OpenAI", "https://api.openai.com/v1", "gpt-4o / gpt-4o-mini")
    table.add_row("智谱 AI", "https://open.bigmodel.cn/api/paas/v4", "glm-4-flash")
    table.add_row("Moonshot", "https://api.moonshot.cn/v1", "moonshot-v1-8k")
    table.add_row(
        "通义千问",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "qwen-turbo",
    )

    console.print(table)
    console.print()


def get_config() -> dict:
    """
    获取当前配置（不检查是否完整，用于内部使用）。

    Returns:
        dict: 包含 base_url, api_key, model 的配置字典
    """
    return {
        "base_url": os.getenv("ROASTER_BASE_URL", "https://api.deepseek.com/v1").strip(),
        "api_key": os.getenv("ROASTER_API_KEY", "").strip(),
        "model": os.getenv("ROASTER_MODEL", "deepseek-chat").strip(),
    }
