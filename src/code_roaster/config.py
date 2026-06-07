"""
配置管理与用户引导中心
======================
负责加载 .env 环境变量，检查配置完整性，
并在缺少 API Key 时提供友好的新手指引。
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
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


def check_config() -> dict:
    """
    检查配置是否完整。

    如果 ROASTER_API_KEY 未设置或为空，打印新手指引并退出程序。
    如果 .env 文件不存在，也会提供创建指引。

    Returns:
        dict: 包含 base_url, api_key, model 的配置字典
    """
    api_key = os.getenv("ROASTER_API_KEY", "").strip()
    base_url = os.getenv("ROASTER_BASE_URL", "https://api.deepseek.com/v1").strip()
    model = os.getenv("ROASTER_MODEL", "deepseek-chat").strip()

    if not api_key:
        _show_onboarding()
        sys.exit(0)

    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }


def _show_onboarding():
    """使用 Rich 库渲染一个精美的新手配置引导界面。"""
    # 标题
    title = Text("🔥 欢迎使用 Code Roaster — 赛博包工头 🔥", style="bold bright_yellow")
    console.print()
    console.print(Panel(title, box=box.HEAVY, border_style="bright_yellow"))
    console.print()

    # 介绍
    intro = Text(
        "看起来你是第一次运行 Code Roaster！\n"
        "在使用之前，需要先配置你的大模型 API Key。\n"
        "别担心，这很简单，跟着下面的步骤走就行 👇",
        style="white",
    )
    console.print(Panel(intro, title="👋 新手指引", border_style="cyan"))
    console.print()

    # 步骤 1：创建 .env 文件
    step1 = Panel(
        Text(
            f"在项目根目录创建一个名为 [bold].env[/bold] 的文件：\n\n"
            f"   📁 路径: [bold cyan]{PROJECT_ROOT / '.env'}[/bold cyan]\n\n"
            f"   💡 提示: 你可以直接复制 [bold].env.example[/bold] 并重命名为 [bold].env[/bold]",
            style="white",
        ),
        title="📝 步骤 1：创建 .env 文件",
        border_style="green",
    )
    console.print(step1)
    console.print()

    # 步骤 2：获取 API Key
    step2_content = Text(
        "去以下任一平台注册账号并申请你的 API Key：\n\n", style="white"
    )
    step2_content.append("  🔹 ", style="bright_blue")
    step2_content.append("DeepSeek", style="bold bright_blue")
    step2_content.append(" — https://platform.deepseek.com\n", style="dim")

    step2_content.append("  🔹 ", style="bright_green")
    step2_content.append("OpenAI", style="bold bright_green")
    step2_content.append("  — https://platform.openai.com\n", style="dim")

    step2_content.append("  🔹 ", style="bright_magenta")
    step2_content.append("智谱 AI", style="bold bright_magenta")
    step2_content.append(" — https://open.bigmodel.cn\n", style="dim")

    step2_content.append("  🔹 ", style="bright_cyan")
    step2_content.append("其他兼容 OpenAI 接口的平台", style="bold bright_cyan")
    step2_content.append(" 也都支持！\n\n", style="dim")

    step2_content.append("💰 这些平台新用户通常都有免费额度，放心冲！", style="bright_yellow")

    step2 = Panel(step2_content, title="🔑 步骤 2：获取 API Key", border_style="green")
    console.print(step2)
    console.print()

    # 步骤 3：写入配置
    step3_content = Text(
        "打开你创建的 .env 文件，填入以下内容：\n\n",
        style="white",
    )
    step3_content.append("  ROASTER_BASE_URL=https://api.deepseek.com/v1\n", style="dim")
    step3_content.append("  ROASTER_API_KEY=", style="dim")
    step3_content.append("sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n", style="bold red")
    step3_content.append("  ROASTER_MODEL=deepseek-chat\n\n", style="dim")
    step3_content.append(
        "⚠️  请把 API Key 替换成你自己的真实 Key！\n"
        "⚠️  如果你用的是 OpenAI，记得同步修改 BASE_URL 和 MODEL！",
        style="bright_yellow",
    )

    step3 = Panel(step3_content, title="✏️  步骤 3：写入配置", border_style="green")
    console.print(step3)
    console.print()

    # 步骤 4：重新运行
    step4 = Panel(
        Text(
            "配置完成后，在终端重新运行：\n\n"
            "   [bold cyan]python -m code_roaster.main[/bold cyan]\n\n"
            "就可以让赛博包工头来点评你的代码啦！🎉",
            style="white",
        ),
        title="🚀 步骤 4：重新运行",
        border_style="green",
    )
    console.print(step4)
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
    table.add_row("通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-turbo")

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
