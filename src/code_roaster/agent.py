"""
Agent 大脑
=========
实现 RoasterAgent 类，负责与大模型交互，
并实现 Reflection（反思）机制以提升点评质量。
"""

from openai import OpenAI

from .prompts import get_persona


class RoasterAgent:
    """
    代码审查 Agent，支持 Reflection 工作流。

    工作流程：
    1. 生成阶段：将 git diff 发给大模型，生成初版点评
    2. 反思阶段：将初版点评反馈给大模型，让其自我批评并改进
    3. 最终返回反思迭代后的点评

    Attributes:
        client: OpenAI 兼容客户端实例
        model: 使用的模型名称
        persona: 当前性格配置字典
    """

    def __init__(self, config: dict, persona_name: str):
        """
        初始化 RoasterAgent。

        Args:
            config: 配置字典，包含 base_url, api_key, model
            persona_name: 性格名称 (toxic, professor, coworker, kfc)
        """
        self.client = OpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
        )
        self.model = config["model"]
        self.persona = get_persona(persona_name)
        self.persona_name = persona_name

    def roast(self, diff_text: str) -> str:
        """
        对代码变更执行毒舌审查（非流式，返回完整文本）。

        Args:
            diff_text: git diff 的文本输出

        Returns:
            str: 反思后的终极点评文本
        """
        # 第一步：生成初版点评
        first_pass = self._generate_roast(diff_text)

        if first_pass is None:
            return "😵 大模型调用失败，也许它也被你的代码吓跑了..."

        # 第二步：反思并生成改进版
        refined = self._reflect_and_refine(diff_text, first_pass)

        if refined is None:
            # 反思失败，返回初版
            return first_pass

        return refined

    def roast_stream(self, diff_text: str):
        """
        对代码变更执行毒舌审查（流式输出）。

        先执行生成和反思两个非流式阶段，
        最后以流式方式输出反思后的点评，
        实现打字机效果。

        Args:
            diff_text: git diff 的文本输出

        Yields:
            str: 流式输出的文本片段
        """
        # 第一步：生成初版点评（非流式）
        first_pass = self._generate_roast(diff_text)

        if first_pass is None:
            yield "😵 大模型调用失败，也许它也被你的代码吓跑了..."
            return

        # 第二步：构建反思请求的消息
        messages = [
            {"role": "system", "content": self.persona["system_prompt"]},
            {"role": "user", "content": f"以下是需要审查的代码变更：\n\n```diff\n{diff_text}\n```"},
            {"role": "assistant", "content": first_pass},
            {"role": "user", "content": self.persona["reflection_prompt"]},
        ]

        # 第三步：流式输出反思后的结果
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.9,
                max_tokens=500,
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content

        except Exception as e:
            # 流式调用失败，回退到返回初版
            yield first_pass
            yield f"\n\n(反思阶段出错: {str(e)}，以上为初版点评)"

    def _generate_roast(self, diff_text: str) -> str | None:
        """
        第一阶段：生成初版毒舌点评。

        Args:
            diff_text: git diff 文本

        Returns:
            str | None: 初版点评文本，失败时返回 None
        """
        messages = [
            {"role": "system", "content": self.persona["system_prompt"]},
            {"role": "user", "content": f"以下是需要审查的代码变更：\n\n```diff\n{diff_text}\n```"},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.85,
                max_tokens=500,
                stream=False,
            )

            content = response.choices[0].message.content
            return content.strip() if content else None

        except Exception as e:
            # 不在这里崩溃，返回 None 让上层处理
            return None

    def _reflect_and_refine(self, diff_text: str, first_pass: str) -> str | None:
        """
        第二阶段：反思初版点评并生成改进版。

        将初版点评和反思提示词一起发给模型，
        让模型自我批评后重新生成更高质量的点评。

        Args:
            diff_text: git diff 文本
            first_pass: 初版点评文本

        Returns:
            str | None: 改进后的点评文本，失败时返回 None
        """
        messages = [
            {"role": "system", "content": self.persona["system_prompt"]},
            {"role": "user", "content": f"以下是需要审查的代码变更：\n\n```diff\n{diff_text}\n```"},
            {"role": "assistant", "content": first_pass},
            {"role": "user", "content": self.persona["reflection_prompt"]},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.9,
                max_tokens=500,
                stream=False,
            )

            content = response.choices[0].message.content
            return content.strip() if content else None

        except Exception:
            # 反思失败不阻塞，返回 None 让上层使用初版
            return None
