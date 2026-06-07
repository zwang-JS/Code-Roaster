# 🔥 Code Roaster — 赛博包工头

> AI 驱动的毒舌代码审查工具 — 让你的每一次 commit 都变成公开处刑。

**Code Roaster** 是一款开源的命令行工具，通过 AI 大模型自动审查你的 `git diff`，以多种毒舌角色风格对你的代码进行精准又扎心的吐槽。它不会帮你修 bug，但会让你记住每一个 bug——以一种你终生难忘的方式。

---

## ✨ 功能特性

- 🎭 **多性格切换**：内置 4 种毒舌角色（大厂老油条、冷酷教授、阴阳同事、疯狂星期四），一键切换不同吐槽风格
- 🧠 **Reflection 反思机制**：两轮 AI 自省 — 先生成初版点评，再自我批评改进，确保吐槽质量层层递进
- 🔑 **钱包自理**：完全开源，你需要在自己的电脑上配置自己的大模型 API Key（支持 DeepSeek、OpenAI、智谱等所有 OpenAI 兼容接口）
- 📺 **流式打字机效果**：终端实时渲染 AI 输出，配合 Rich 库的彩色排版，观感拉满
- 🐍 **纯 Python 实现**：Python 3.8+ 即可运行，依赖极简，二次开发门槛低

---

## 🚀 快速开始

### 环境要求

- **Python 3.8+**
- **Git**（用于获取代码变更）
- 一个大模型 API Key（DeepSeek / OpenAI / 智谱 等均支持）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/code-roaster.git
cd code-roaster

# 2. 安装依赖
pip install -r requirements.txt
```

### 配置 API Key

Code Roaster 使用 `.env` 文件管理你的 API 密钥，**不会将你的 Key 上传到任何地方**。

```bash
# 3. 复制环境变量模板
cp .env.example .env

# 4. 编辑 .env 文件，填入你的真实 API Key
# Windows 用户可以用记事本打开 .env 文件编辑
```

`.env` 文件内容示例（以 DeepSeek 为例）：

```env
ROASTER_BASE_URL=https://api.deepseek.com/v1
ROASTER_API_KEY=sk-your-real-api-key-here
ROASTER_MODEL=deepseek-chat
```

<details>
<summary>📋 其他平台的配置方法（点击展开）</summary>

**OpenAI:**
```env
ROASTER_BASE_URL=https://api.openai.com/v1
ROASTER_API_KEY=sk-your-openai-api-key
ROASTER_MODEL=gpt-4o-mini
```

**智谱 AI (GLM):**
```env
ROASTER_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ROASTER_API_KEY=your-zhipu-api-key
ROASTER_MODEL=glm-4-flash
```

**Moonshot (月之暗面):**
```env
ROASTER_BASE_URL=https://api.moonshot.cn/v1
ROASTER_API_KEY=your-moonshot-api-key
ROASTER_MODEL=moonshot-v1-8k
```

任何兼容 OpenAI 接口格式的平台都可以使用，只需修改 `ROASTER_BASE_URL` 和 `ROASTER_MODEL` 即可。
</details>

### 基本使用

```bash
# 在任意 Git 仓库中，确保你有未提交的代码改动
# 然后运行：

# 默认模式 — 大厂老油条（toxic）
python -m code_roaster.main

# 指定性格
python -m code_roaster.main -p professor    # 冷酷教授
python -m code_roaster.main -p coworker     # 阴阳同事
python -m code_roaster.main -p kfc          # 疯狂星期四

# 查看所有可用性格
python -m code_roaster.main --list-personas

# 查看帮助
python -m code_roaster.main --help
```

---

## 🎭 Persona 介绍

### 🚬 大厂老油条 `toxic`（默认）

> "你这个代码的颗粒度太粗了，完全没有对齐业务闭环的打法。"

典型的互联网大厂 P8+ 老员工，满嘴「赋能」「对齐」「闭环」「抓手」「底层逻辑」。极度刻薄，疯狂制造焦虑，让你读完代码审查后想立刻打开招聘软件。

**适用场景**：当你需要有人用最扎心的方式告诉你代码写得像屎一样。

---

### 🎓 冷酷教授 `professor`

> "这位同学，你的代码我看了三遍，每一遍都在刷新我对'不合格'的认知。"

带了 20 年研究生的计算机系教授，对代码有洁癖般的追求。动不动就威胁你延毕、把代码抄 100 遍、周一去他办公室答辩。

**适用场景**：怀念校园时光？让教授来告诉你什么叫学术级别的羞辱。

---

### 😊 阴阳同事 `coworker`

> "哇～你这个命名方式真的好有创意呀！没事的呀反正以后也不是我维护～"

表面笑嘻嘻，内心骂咧咧。每个夸奖后面都藏着一把刀。用最温柔的语气说最阴阳怪气的话，让你被骂了还想说谢谢。

**适用场景**：模拟真实职场中那个让你又爱又恨的「好同事」。

---

### 🍗 疯狂星期四 `kfc`

> "你这代码……能跑就行吧。对了，今天星期四，V 我 50 吃肯德基。"

世界上最敷衍的 code reviewer。大脑 90% 的算力都在计算距离星期四还有几天。虽然很敷衍，但莫名其妙总能指出你代码里的致命 bug。

**适用场景**：星期四。以及任何你想摆烂但又需要有人 review 代码的时刻。

---

## 🔧 高级用法

### 自定义 Persona

你可以在 `src/code_roaster/prompts.py` 中添加新的性格。只需在 `PERSONAS` 字典中新增一个条目：

```python
PERSONAS = {
    # ... 已有性格 ...

    "grandma": {
        "name": "唠叨外婆",
        "emoji": "👵",
        "description": "总是担心你加班不吃饭的唠叨外婆",
        "system_prompt": (
            "你是一位关心孙子的外婆……（此处写角色设定）"
        ),
        "reflection_prompt": (
            "检查你刚才的回答……（此处写反思提示词）"
        ),
        "no_diff_message": "乖孙，代码都没改就不要折腾了，来喝碗汤。",
    },
}
```

然后在 `prompts.py` 中确保 `get_available_personas()` 返回的列表包含 `"grandma"`，就可以通过 `-p grandma` 使用了。

### 切换不同的大模型

只需修改 `.env` 文件中的三个变量：

| 变量 | 说明 |
|------|------|
| `ROASTER_BASE_URL` | API 端点地址 |
| `ROASTER_API_KEY` | 你的 API 密钥 |
| `ROASTER_MODEL` | 模型名称 |

不同模型的吐槽质量会有差异，建议使用 `deepseek-chat`（性价比高）或 `gpt-4o`（质量最佳）。

---

## ❓ 常见问题

<details>
<summary><b>Q: 运行时提示 "ModuleNotFoundError: No module named 'code_roaster'"</b></summary>

确保你在 `code-roaster` 项目根目录下运行命令。如果仍然报错，尝试：
```bash
export PYTHONPATH="src:$PYTHONPATH"   # Linux/Mac
set PYTHONPATH=src;%PYTHONPATH%       # Windows CMD
$env:PYTHONPATH = "src;$env:PYTHONPATH"  # Windows PowerShell
```
</details>

<details>
<summary><b>Q: 运行时显示新手指引，但我已经配置了 .env</b></summary>

检查以下几点：
1. `.env` 文件是否在项目根目录（`code-roaster/` 下）
2. `.env` 中 `ROASTER_API_KEY` 是否真的填了值（不是 `your_own_api_key_here`）
3. 变量名是否正确（注意是 `ROASTER_API_KEY` 不是 `OPENAI_API_KEY`）
</details>

<details>
<summary><b>Q: 提示 "当前目录不是一个 Git 仓库"</b></summary>

Code Roaster 依赖 `git diff` 获取代码变更。请确保：
1. 你在一个 Git 仓库目录中运行
2. 如果没有 Git 仓库，先初始化：`git init && git add -A && git commit -m "init"`
</details>

<details>
<summary><b>Q: 网络连接失败 / API 调用超时</b></summary>

1. 检查 `ROASTER_BASE_URL` 是否正确
2. 如果你在国内使用 OpenAI，可能需要配置代理
3. 尝试换用 DeepSeek（国内可直接访问）
</details>

<details>
<summary><b>Q: 点评内容不够毒舌 / 不够精准？</b></summary>

1. 尝试换用更强的模型（如 `deepseek-chat` → `gpt-4o`）
2. 增大 `agent.py` 中的 `temperature` 参数（当前为 0.85-0.9）
3. 在 `prompts.py` 中自定义提示词，让角色更毒舌
</details>

---

## 🤝 贡献指南

欢迎一切形式的贡献！无论是提 Issue、发 PR，还是帮忙完善文档。

### 贡献方式

1. **Fork** 本仓库
2. 创建你的特性分支：`git checkout -b feature/amazing-feature`
3. 提交你的改动：`git commit -m 'feat: add amazing feature'`
4. 推送到远程分支：`git push origin feature/amazing-feature`
5. 发起 **Pull Request**

### Issue 规范

- 🐛 Bug 报告：请附上运行环境（操作系统、Python 版本）、复现步骤和错误截图
- 💡 功能建议：请描述使用场景和你期望的效果
- 🎭 新 Persona 建议：请提供角色设定和一段示例吐槽

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

简而言之：你可以自由使用、修改、分发本项目的代码，但需要保留原始版权声明。作者不对使用本工具造成的任何心理创伤负责 😈

---

## ⚠️ 免责声明

Code Roaster 生成的点评内容由 AI 大模型自动生成，不代表项目作者的立场。点评内容可能包含夸张、讽刺、阴阳怪气的表达，仅供娱乐和技术交流。**请理性看待 AI 生成的代码审查意见**，对于实际代码质量问题，建议结合人工 Review 和自动化测试综合判断。

---

<p align="center">
  <b>Made with 💀 by developers who hate bad code</b>
</p>
