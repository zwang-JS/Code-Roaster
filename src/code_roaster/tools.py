"""
工具箱
======
提供与 Git 仓库交互的工具函数，用于获取代码变更。
"""

import re
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


def get_diff_files() -> list[dict]:
    """
    将 `git diff HEAD` 的输出按文件拆分为独立 diff 块。

    解析 diff 输出中的 `diff --git a/... b/...` 标记来分割文件。
    同时提取每个文件的增删行数统计。

    Returns:
        list[dict]: 每个元素包含:
            - filename: 文件名
            - diff_text: 该文件的完整 diff 文本
            - added: 新增行数 (int)
            - removed: 删除行数 (int)
    """
    full_diff = get_git_diff()

    # 如果 diff 是错误信息或为空，直接返回空列表
    if not full_diff or full_diff.startswith("❌") or full_diff.startswith("⚠️") or full_diff.startswith("📭"):
        return []

    # 按 diff --git 标记分割
    # 格式: diff --git a/path/to/file b/path/to/file
    chunks = re.split(r'\n(?=diff --git )', full_diff)

    files = []
    for chunk in chunks:
        if not chunk.strip():
            continue

        # 提取文件名
        match = re.search(r'diff --git a/(.+) b/(.+)', chunk)
        if not match:
            continue
        filename = match.group(1)

        # 统计增删行数
        added = len(re.findall(r'^\+(?!\+\+)', chunk, re.MULTILINE))
        removed = len(re.findall(r'^-(?!--)', chunk, re.MULTILINE))

        files.append({
            "filename": filename,
            "diff_text": chunk.strip(),
            "added": added,
            "removed": removed,
        })

    return files
