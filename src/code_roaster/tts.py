"""
TTS 语音播报模块
================
调用各操作系统自带的 TTS 引擎，对点评结果进行语音朗读。

支持的平台:
    - Windows: PowerShell + .NET SpeechSynthesizer（系统自带，支持中文）
    - macOS: say 命令（系统自带）
    - Linux: espeak 命令（需安装）

零额外 Python 依赖。
"""

import platform
import subprocess
import threading
import re


def _clean_for_speech(text: str) -> str:
    """
    清洗文本，移除 Rich 标记和 emoji，保留纯文本用于朗读。

    Args:
        text: 原始点评文本

    Returns:
        str: 清洗后的纯文本
    """
    # 移除 Rich 风格标记 [bold], [red], [/bold] 等
    text = re.sub(r'\[/?\w+\]', '', text)
    # 移除 ANSI 转义序列
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    # 移除常见符号，保留中文标点
    text = text.replace('**', '').replace('__', '')
    return text.strip()


def _speak_windows(text: str) -> None:
    """Windows: 通过 PowerShell 调 .NET SpeechSynthesizer。"""
    # 对单引号做转义
    safe_text = text.replace("'", "''")
    # 限制长度避免 PowerShell 命令行过长
    if len(safe_text) > 1000:
        safe_text = safe_text[:1000]

    ps_script = (
        f"Add-Type -AssemblyName System.Speech;"
        f"$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"$s.Speak('{safe_text}')"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass  # TTS 失败不应影响主流程


def _speak_mac(text: str) -> None:
    """macOS: 使用系统自带的 say 命令。"""
    try:
        subprocess.run(
            ["say", text[:1000]],
            capture_output=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass


def _speak_linux(text: str) -> None:
    """Linux: 尝试 espeak，如不可用则静默失败。"""
    try:
        subprocess.run(
            ["espeak", text[:1000]],
            capture_output=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass  # espeak 未安装也不影响使用


def speak(text: str) -> None:
    """
    在后台线程中朗读文本（非阻塞）。

    Args:
        text: 要朗读的文本（可含 emoji 和标记，会自动清洗）
    """
    cleaned = _clean_for_speech(text)
    if not cleaned:
        return

    system = platform.system()

    if system == "Windows":
        target = _speak_windows
    elif system == "Darwin":
        target = _speak_mac
    else:
        target = _speak_linux

    # 后台线程执行，不阻塞主流程
    thread = threading.Thread(target=target, args=(cleaned,), daemon=True)
    thread.start()
