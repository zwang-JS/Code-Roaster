"""
Agent 大脑
=========
实现 RoasterAgent 类，负责与大模型交互，
并实现 Reflection（反思）机制以提升点评质量。

支持的 API 类型:
    - openai:     OpenAI 兼容接口（DeepSeek, OpenAI, 智谱, Ollama 等）
    - anthropic:  Anthropic Claude 原生 API
"""

from openai import OpenAI

from .prompts import get_persona

# Anthropic SDK 为可选依赖，使用时才导入
_ANTHROPIC_AVAILABLE = False
_Anthropic = None
try:
    from anthropic import Anthropic as _Ant

    _Anthropic = _Ant
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    pass


class RoasterAgent:
    """
    代码审查 Agent，支持 Reflection 工作流，兼容 OpenAI 和 Anthropic 两种接口。

    工作流程：
    1. 生成阶段：将 git diff 发给大模型，生成初版点评
    2. 反思阶段：将初版点评反馈给大模型，让其自我批评并改进
    3. 最终返回反思迭代后的点评
    """

    def __init__(self, config: dict, persona_name: str):
        """
        初始化 RoasterAgent。

        Args:
            config: 配置字典，包含 api_type, base_url, api_key, model
            persona_name: 性格名称
        """
        self.api_type = config.get("api_type", "openai")
        self.model = config["model"]
        self.persona = get_persona(persona_name)
        self.persona_name = persona_name

        if self.api_type == "anthropic":
            if not _ANTHROPIC_AVAILABLE:
                raise ImportError(
                    "使用 Anthropic API 需要安装 anthropic SDK。\n"
                    "请运行: pip install anthropic"
                )
            self.client = _Anthropic(api_key=config["api_key"], timeout=60.0)
        else:
            # OpenAI 兼容接口（默认）
            self.client = OpenAI(
                base_url=config["base_url"],
                api_key=config["api_key"],
                timeout=60.0,
            )

    # ================================================================
    # 公开方法
    # ================================================================

    def roast(self, diff_text: str) -> str:
        """对代码变更执行毒舌审查（非流式，返回完整文本）。"""
        first_pass = self._generate_roast(diff_text)
        if first_pass is None:
            return "😵 大模型调用失败，也许它也被你的代码吓跑了..."

        refined = self._reflect_and_refine(diff_text, first_pass)
        return refined if refined is not None else first_pass

    def roast_stream(self, diff_text: str):
        """
        对代码变更执行毒舌审查（流式输出）。

        第一、二阶段非流式（内部处理），最终反思结果流式输出。
        """
        first_pass = self._generate_roast(diff_text)
        if first_pass is None:
            yield "😵 大模型调用失败，也许它也被你的代码吓跑了..."
            return

        # 构建反思消息
        user_messages = [
            f"以下是需要审查的代码变更：\n\n```diff\n{diff_text}\n```",
            first_pass,
            self.persona["reflection_prompt"],
        ]

        try:
            if self.api_type == "anthropic":
                yield from self._stream_anthropic(user_messages)
            else:
                yield from self._stream_openai(user_messages)
        except Exception as e:
            yield first_pass
            yield f"\n\n(反思阶段出错: {str(e)}，以上为初版点评)"

    def rebuttal_stream(self, messages: list[dict]):
        """
        反驳模式：将完整对话历史发给 AI，流式返回 AI 的回怼。

        与 roast_stream 不同，此方法接收预构建的 messages 列表
        （已包含 system prompt、diff、roast 结果及所有对线轮次）。

        Args:
            messages: 完整的对话消息列表，格式为：
                [{"role": "system", "content": "..."},
                 {"role": "user", "content": "..."},
                 {"role": "assistant", "content": "..."}, ...]

        Yields:
            str: AI 回复的文本片段（流式）
        """
        try:
            if self.api_type == "anthropic":
                yield from self._rebuttal_stream_anthropic(messages)
            else:
                yield from self._rebuttal_stream_openai(messages)
        except Exception as e:
            yield f"(反驳失败: {str(e)})"

    # ================================================================
    # 内部：生成 & 反思（非流式）
    # ================================================================

    def _generate_roast(self, diff_text: str) -> str | None:
        """第一阶段：生成初版毒舌点评。"""
        user_messages = [
            f"以下是需要审查的代码变更：\n\n```diff\n{diff_text}\n```",
        ]

        try:
            if self.api_type == "anthropic":
                return self._call_anthropic(user_messages, temperature=0.85)
            else:
                return self._call_openai(user_messages, temperature=0.85)
        except Exception:
            return None

    def _reflect_and_refine(self, diff_text: str, first_pass: str) -> str | None:
        """第二阶段：反思初版点评并生成改进版。"""
        user_messages = [
            f"以下是需要审查的代码变更：\n\n```diff\n{diff_text}\n```",
            first_pass,
            self.persona["reflection_prompt"],
        ]

        try:
            if self.api_type == "anthropic":
                return self._call_anthropic(user_messages, temperature=0.9)
            else:
                return self._call_openai(user_messages, temperature=0.9)
        except Exception:
            return None

    # ================================================================
    # OpenAI 兼容接口实现
    # ================================================================

    def _call_openai(self, user_messages: list[str], temperature: float) -> str | None:
        """OpenAI 兼容接口：非流式调用。"""
        messages = [{"role": "system", "content": self.persona["system_prompt"]}]
        roles = ["user", "assistant", "user"]
        for i, msg in enumerate(user_messages):
            role = roles[i] if i < len(roles) else "user"
            messages.append({"role": role, "content": msg})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=500,
            stream=False,
        )
        content = response.choices[0].message.content
        return content.strip() if content else None

    def _stream_openai(self, user_messages: list[str]):
        """OpenAI 兼容接口：流式输出。"""
        messages = [{"role": "system", "content": self.persona["system_prompt"]}]
        roles = ["user", "assistant", "user"]
        for i, msg in enumerate(user_messages):
            role = roles[i] if i < len(roles) else "user"
            messages.append({"role": role, "content": msg})

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.9,
            max_tokens=500,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

    # ================================================================
    # Anthropic Claude 原生 API 实现
    # ================================================================

    def _call_anthropic(self, user_messages: list[str], temperature: float) -> str | None:
        """Anthropic API：非流式调用。"""
        messages = self._build_anthropic_messages(user_messages)

        response = self.client.messages.create(
            model=self.model,
            messages=messages,
            system=self.persona["system_prompt"],
            temperature=temperature,
            max_tokens=500,
        )
        # Anthropic 返回的 content 是列表，取第一段文本
        if response.content and len(response.content) > 0:
            return response.content[0].text.strip()
        return None

    def _stream_anthropic(self, user_messages: list[str]):
        """Anthropic API：流式输出。"""
        messages = self._build_anthropic_messages(user_messages)

        with self.client.messages.stream(
            model=self.model,
            messages=messages,
            system=self.persona["system_prompt"],
            temperature=0.9,
            max_tokens=500,
        ) as stream:
            for text in stream.text_stream:
                yield text

    @staticmethod
    def _build_anthropic_messages(user_messages: list[str]) -> list[dict]:
        """
        将用户消息列表转换为 Anthropic 消息格式。

        Anthropic 的消息格式要求 user 和 assistant 交替，
        且没有 system role（system prompt 作为独立参数传入）。
        """
        messages = []
        roles = ["user", "assistant", "user"]
        for i, msg in enumerate(user_messages):
            role = roles[i] if i < len(roles) else "user"
            messages.append({"role": role, "content": msg})
        return messages

    # ================================================================
    # 内部：反驳模式流式实现
    # ================================================================

    def _rebuttal_stream_openai(self, messages: list[dict]):
        """OpenAI 兼容接口：反驳模式流式输出。

        messages 已包含完整的对话历史（system + user + assistant 交替）。
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.95,
            max_tokens=400,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

    def _rebuttal_stream_anthropic(self, messages: list[dict]):
        """Anthropic API：反驳模式流式输出。

        将 system role 从 messages 中分离，作为独立参数传入。
        """
        # 分离 system prompt
        system_prompt = ""
        anthropic_msgs: list[dict] = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                anthropic_msgs.append(m)

        if not system_prompt:
            system_prompt = self.persona["system_prompt"]

        with self.client.messages.stream(
            model=self.model,
            messages=anthropic_msgs,
            system=system_prompt,
            temperature=0.95,
            max_tokens=400,
        ) as stream:
            for text in stream.text_stream:
                yield text
