"""
Code Roaster TUI — 终端用户界面
===============================
基于 Textual 框架的交互式代码审查界面。
支持鼠标点击、键盘操作、实时流式输出。

启动方式:
    roaster-tui
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Button,
    Select,
    Static,
    Label,
    Checkbox,
)
from textual import work

from .config import check_config
from .tools import get_diff_files, get_git_diff
from .prompts import PERSONAS, get_persona
from .agent import RoasterAgent
from .history import save_review


class FileCheckbox(Checkbox):
    """带文件名和统计的复选框。"""

    def __init__(self, filename: str, added: int, removed: int) -> None:
        label = f"{filename}  (+{added}/-{removed})"
        super().__init__(label, value=True)
        self.file_filename = filename


class RoasterTUI(App):
    """Code Roaster 终端 UI 主应用。"""

    CSS = """
    Screen {
        layout: horizontal;
    }

    #sidebar {
        width: 38;
        border: solid $primary;
        padding: 1;
    }

    #sidebar > Label {
        margin-top: 1;
        text-style: bold;
        color: $accent;
    }

    #sidebar > Button {
        width: 100%;
        margin-top: 1;
    }

    #file-list {
        height: auto;
        max-height: 16;
        border: solid $surface;
        padding: 0 1;
        margin-top: 1;
    }

    #main-panel {
        border: solid $primary;
        padding: 1 2;
    }

    #result {
        height: 100%;
        border: solid $surface-lighten-1;
        padding: 1;
    }

    Button#btn-roast {
        background: $error;
        color: $text;
    }

    Button#btn-roast:hover {
        background: $error-lighten-1;
    }

    Button#btn-stats {
        background: $primary;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text-disabled;
    }
    """

    BINDINGS = [
        ("r", "start_roast", "开始审查"),
        ("s", "show_stats", "查看统计"),
        ("q", "quit", "退出"),
    ]

    def __init__(self, config: dict) -> None:
        super().__init__()
        self._config = config
        self._diff_files: list[dict] = []
        self._roast_accumulated: str = ""

    def compose(self) -> ComposeResult:
        """构建 UI 布局。"""
        yield Header(show_clock=True)

        with Horizontal():
            # --- 左侧边栏 ---
            with Vertical(id="sidebar"):
                yield Label("🎭 审查性格")
                persona_options = [
                    (f"{p['emoji']} {p['name']}", key)
                    for key, p in PERSONAS.items()
                ]
                yield Select(
                    options=persona_options,
                    value="toxic",
                    id="persona-select",
                )

                yield Label("📁 待审查文件")
                yield ScrollableContainer(id="file-list")

                yield Button("🔥 开始审查 (R)", id="btn-roast", variant="error")
                yield Button("📊 查看统计 (S)", id="btn-stats", variant="primary")

            # --- 右侧主面板 ---
            with Vertical(id="main-panel"):
                yield Label("💬 审查结果", id="result-title")
                yield ScrollableContainer(
                    Static("准备就绪。点击 [开始审查] 或按 R 键。", id="result"),
                    id="result-scroll",
                )

        yield Footer()

    def on_mount(self) -> None:
        """应用挂载后：加载文件列表、注册按钮回调。"""
        self._load_files()
        self.query_one("#btn-roast", Button).can_focus = True
        self.query_one("#btn-stats", Button).can_focus = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """按钮点击事件分发。"""
        if event.button.id == "btn-roast":
            self.action_start_roast()
        elif event.button.id == "btn-stats":
            self.action_show_stats()

    # ================================================================
    # 文件加载
    # ================================================================

    def _load_files(self) -> None:
        """加载 git diff 文件列表并渲染复选框。"""
        self._diff_files = get_diff_files()

        file_list = self.query_one("#file-list", ScrollableContainer)
        # 清除旧内容（保留可能存在的 loading 提示）
        file_list.remove_children()

        if not self._diff_files:
            raw = get_git_diff()
            if raw.startswith("❌") or raw.startswith("⚠️"):
                file_list.mount(Static(raw[:200], id="file-error"))
            else:
                file_list.mount(Static("📭 没有未提交的代码改动", id="file-empty"))
            return

        for f in self._diff_files:
            cb = FileCheckbox(f["filename"], f["added"], f["removed"])
            file_list.mount(cb)

    # ================================================================
    # 审查动作
    # ================================================================

    def action_start_roast(self) -> None:
        """触发代码审查。"""
        # 收集选中的文件
        file_list = self.query_one("#file-list", ScrollableContainer)
        checkboxes = file_list.query(FileCheckbox)
        selected = [cb for cb in checkboxes if cb.value]

        if not selected:
            self._set_result("⚠️ 请至少选择一个文件进行审查。")
            return

        # 收集选中的 diff
        selected_names = {cb.file_filename for cb in selected}
        selected_diffs = [
            f["diff_text"]
            for f in self._diff_files
            if f["filename"] in selected_names
        ]
        combined_diff = "\n\n".join(selected_diffs)

        # 获取选择的 persona
        persona_select = self.query_one("#persona-select", Select)
        persona_name: str = persona_select.value or "toxic"  # type: ignore[assignment]
        persona = get_persona(persona_name)

        # 更新 UI 状态
        self._roast_accumulated = ""
        self._set_result("🔥 赛博包工头正在审查你的代码...\n")
        self.query_one("#btn-roast", Button).disabled = True

        # 启动后台工作线程
        self.do_roast(
            combined_diff,
            persona_name,
            persona["emoji"],
            list(selected_names),
        )

    @work(exclusive=True, thread=True)
    def do_roast(
        self,
        diff_text: str,
        persona_name: str,
        persona_emoji: str,
        selected_files: list[str],
    ) -> None:
        """后台线程：执行审查并流式更新 UI。"""
        try:
            agent = RoasterAgent(self._config, persona_name)

            for chunk in agent.roast_stream(diff_text):
                self._roast_accumulated += chunk
                # 从工作线程安全更新 UI
                self.call_from_thread(self._update_result)
        except Exception as e:
            self.call_from_thread(
                self._set_result,
                f"❌ 审查出错: {e}",
            )
        finally:
            # 保存历史记录
            if self._roast_accumulated:
                save_review(
                    persona_name,
                    persona_emoji,
                    selected_files,
                    self._roast_accumulated,
                )
            # 重新启用按钮
            self.call_from_thread(
                self._reenable_button,
            )

    # ================================================================
    # UI 更新（从线程安全调用）
    # ================================================================

    def _update_result(self) -> None:
        """更新结果显示区域。"""
        result = self.query_one("#result", Static)
        result.update(self._roast_accumulated)
        # 自动滚动到底部
        scroll = self.query_one("#result-scroll", ScrollableContainer)
        scroll.scroll_end(animate=False)

    def _set_result(self, text: str) -> None:
        """设置结果文本（非线程场景）。"""
        result = self.query_one("#result", Static)
        result.update(text)

    def _reenable_button(self) -> None:
        """重新启用审查按钮。"""
        self.query_one("#btn-roast", Button).disabled = False

    # ================================================================
    # 统计
    # ================================================================

    def action_show_stats(self) -> None:
        """显示审查统计（弹窗模式）。"""
        stats_text = self._build_stats_text()
        self._set_result(stats_text)

    def _build_stats_text(self) -> str:
        """构建统计文本。"""
        import json
        from datetime import datetime, timedelta

        history_file = Path.home() / ".code-roaster" / "history.json"
        if not history_file.exists():
            return "📊 还没有审查记录。"

        try:
            data = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            return "📊 无法读取历史记录。"

        if not data:
            return "📊 还没有审查记录。"

        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        weekly = []
        persona_counts = {}
        for r in data:
            try:
                dt = datetime.fromisoformat(r["time"])
                if dt >= week_start:
                    weekly.append(r)
                    p = r.get("persona", "?")
                    persona_counts[p] = persona_counts.get(p, 0) + 1
            except Exception:
                pass

        lines = [
            "═══════════════════════════════",
            "  📊 Code Roaster 统计报表",
            "═══════════════════════════════",
            "",
            f"  📅 本周: {week_start.strftime('%m/%d')} - {now.strftime('%m/%d')}",
            f"  🔥 本周被骂: {len(weekly)} 次",
            f"  📚 历史总计: {len(data)} 次",
            "",
        ]

        if persona_counts:
            lines.append("  🎭 本周 Persona 排行:")
            sorted_p = sorted(persona_counts.items(), key=lambda x: x[1], reverse=True)
            for name, count in sorted_p:
                bar = "█" * min(count, 15)
                lines.append(f"    {name:<12} {count}次  {bar}")

        lines.append("")
        lines.append("═══════════════════════════════")
        return "\n".join(lines)


def main():
    """TUI 入口点。"""
    # 检查/配置 API Key
    config = check_config()

    # 启动 Textual 应用
    app = RoasterTUI(config)
    app.run()


if __name__ == "__main__":
    main()
