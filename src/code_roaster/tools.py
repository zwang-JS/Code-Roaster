"""
工具箱
======
提供与 Git 仓库交互的工具函数，用于获取代码变更。
"""

import subprocess
import sys


def get_git_diff() -> str:
    """
    运行 `git diff HEAD` 获取当前未提交的代码改动。

    如果工作区干净（无改动），返回空字符串。
    如果不在 Git 仓库中或 Git 未安装，返回错误提示字符串。

    Returns:
        str: git diff 的输出文本，或错误提示信息
    """
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

        if result.returncode != 0:
            # Git 返回错误（比如不在仓库中、没有提交记录等）
            stderr = (result.stderr or "").strip()
            if "not a git repository" in stderr.lower():
                return (
                    "❌ 当前目录不是一个 Git 仓库。\n"
                    "   请在 Git 项目目录下运行 Code Roaster。\n"
                    "   还没有初始化？试试: git init && git add -A && git commit -m 'init'"
                )
            if "unknown revision" in stderr.lower() or "ambiguous argument" in stderr.lower():
                return (
                    "📭 当前仓库还没有任何提交记录。\n"
                    "   请先做一次 commit: git add -A && git commit -m 'init'"
                )
            return f"⚠️  Git 命令执行出错:\n{stderr}"

        diff_text = (result.stdout or "").strip()
        return diff_text if diff_text else ""

    except FileNotFoundError:
        return (
            "❌ 未检测到 Git。\n"
            "   Code Roaster 依赖 Git 来获取代码变更。\n"
            "   请先安装 Git: https://git-scm.com/downloads"
        )
    except subprocess.TimeoutExpired:
        return "⚠️  Git diff 执行超时，请检查仓库大小或网络状态。"
    except Exception as e:
        return f"⚠️  执行 git diff 时发生未知错误: {str(e)}"


def get_git_diff_staged() -> str:
    """
    运行 `git diff --staged` 获取已暂存（git add 后）的代码改动。

    Returns:
        str: git diff --staged 的输出文本，或错误提示信息
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            if "not a git repository" in stderr.lower():
                return "❌ 当前目录不是一个 Git 仓库。"
            return f"⚠️  Git 命令执行出错:\n{stderr}"

        diff_text = (result.stdout or "").strip()
        return diff_text if diff_text else ""

    except FileNotFoundError:
        return "❌ 未检测到 Git，请先安装 Git。"
    except subprocess.TimeoutExpired:
        return "⚠️  Git diff 执行超时。"
    except Exception as e:
        return f"⚠️  未知错误: {str(e)}"
