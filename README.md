# 🔥 Code Roaster — 赛博包工头

> AI 驱动的毒舌代码审查工具 — 让你的每一次 commit 都变成公开处刑。

**Code Roaster** 是一款开源的命令行工具，通过 AI 大模型自动审查你的 `git diff`，以多种毒舌角色风格对你的代码进行精准又扎心的吐槽。它不会帮你修 bug，但会让你记住每一个 bug——以一种你终生难忘的方式。

---

## ✨ 功能特性

- 🎭 **多性格切换**：内置 8 种毒舌角色（大厂老油条、冷酷教授、阴阳同事、疯狂星期四、夸夸天使、贴吧老哥），一键切换不同吐槽风格
- 🎨 **像素风 Banner**：启动时显示彩色渐变的 "CODE ROASTER" ASCII 艺术字，仪式感拉满
- 🧠 **Reflection 反思机制**：两轮 AI 自省 — 先生成初版点评，再自我批评改进，确保吐槽质量层层递进
- 🔑 **钱包自理**：完全开源，你需要在自己的电脑上配置自己的大模型 API Key（支持 DeepSeek、OpenAI、智谱等所有 OpenAI 兼容接口）
- 🖥️ **TUI 图形界面**：基于 Textual 框架的终端 GUI，鼠标点击、复选框、下拉菜单，长得像桌面应用
- 📺 **流式打字机效果**：终端实时渲染 AI 输出，配合 Rich 库的彩色排版，观感拉满
- 🐍 **纯 Python 实现**：Python 3.8+ 即可运行，依赖极简，二次开发门槛低

---

## 🚀 快速开始（三步上手）

### 前置要求

- **Python 3.8+**（`python --version` 检查）
- **Git**（`git --version` 检查）
- 一个大模型 API Key（去 [DeepSeek](https://platform.deepseek.com) 免费注册即可）

### 三步搞定

```bash
# 1. 克隆并进入项目
git clone https://github.com/zwang-JS/Code-Roaster.git
cd Code-Roaster

# 2. 一键安装（自动装好依赖 + 注册 roaster 命令）
pip install -e .

# 3. 在任意 Git 仓库里直接运行
roaster
```

**首次运行会自动弹出配置向导**，跟着提示选择平台、粘贴 API Key，`.env` 文件自动生成，完全不用手动编辑。

### 基本使用

```bash
# 终端图形界面（推荐！）— 鼠标勾选文件、下拉选性格
roaster-tui

# 经典命令行 — Banner + 性格菜单
roaster

# 指定性格
roaster -p toxic         # 大厂老油条
roaster -p professor     # 冷酷教授
roaster -p kfc           # 疯狂星期四
roaster -p cheerleader   # 夸夸天使
roaster -p tieba         # 贴吧老哥
roaster -p ceo           # 霸道总裁
roaster -p luxun         # 鲁迅先生
roaster -p beijing       # 京爷

# 跳过 Banner（脚本化使用）
roaster --no-banner -p toxic

# 查看所有性格
roaster --list-personas

# 帮助
roaster --help
```

---

## 🎭 Persona 介绍

### 🚬 大厂老油条 `toxic`

> "你这个代码的颗粒度太粗了，完全没有对齐业务闭环的打法。"

典型的互联网大厂 P8+ 老员工，满嘴「赋能」「对齐」「闭环」「抓手」「底层逻辑」。极度刻薄，疯狂制造焦虑，让你读完代码审查后想立刻打开招聘软件。

**适用场景**：当你需要有人用最扎心的方式告诉你代码写得像屎一样。

---

### 🎓 冷酷教授 `professor`

> "这位同学，你的代码我看了三遍，每一遍都在刷新我对'不合格'的认知。"

带了 20 年研究生的计算机系教授，对代码有洁癖般的追求。动不动就威胁你延毕、把代码抄 100 遍、周一去他办公室答辩。

**适用场景**：怀念校园时光？让教授来告诉你什么叫学术级别的羞辱。

---

### 🍗 疯狂星期四 `kfc`

> "你这代码……能跑就行吧。对了，今天星期四，V 我 50 吃肯德基。"

世界上最敷衍的 code reviewer。大脑 90% 的算力都在计算距离星期四还有几天。虽然很敷衍，但莫名其妙总能指出你代码里的致命 bug。

**适用场景**：星期四。以及任何你想摆烂但又需要有人 review 代码的时刻。

---

### 🌈 夸夸天使 `cheerleader`

> "天哪！！！你这个缩进也太完美了吧！！！而且你居然记得写注释！！！你简直是代码界的天才！！！虽然这里有个小小的空指针但我知道你肯定下一秒就能修好！！！"

世界上最有正能量的代码审查员。无论你的代码有多烂，她都能找到夸你的角度。她会把你的烂代码形容成「潜力无限的创意表达」，让你在被指出 bug 的同时感到被爱与希望包围。

**适用场景**：当你的代码被其他 persona 骂得怀疑人生后，需要一点温暖和治愈。

---

### 🎭 贴吧老哥 `tieba`

> "老铁你这代码写的，蚌埠住了😅 变量名起得属实抽象，这波啊这波是面向bug编程，典中典！"

来自百度贴吧资深吧友，满嘴抽象话和网络流行梗。说话随意粗犷，像在吧里水帖。虽然嘴臭，但真心想让代码变好。你永远不知道他下一句会蹦出什么贴吧金句。

**适用场景**：当你怀念互联网的古早味道，想让贴吧老哥用最接地气的方式毒打你的代码。

---

### 🏯 霸道总裁 `ceo`

> "很好，你成功引起了我的注意。上一个敢在我项目里这样写代码的人，他的公司已经破产了。"

身家千亿的霸道总裁，用霸总语录包装代码审查。「天凉了让这个类破产吧」「给这个 Bug 一个亿的修复预算」「你是第一个敢在我面前写这种代码的女人/男人」。

**适用场景**：想让代码问题听起来像一场商业危机，或者单纯想体验被霸总壁咚式骂醒的感觉。

---

### 📜 鲁迅先生 `luxun`

> "我翻开这代码一看，歪歪斜斜的每行都写着「能跑就行」。我横竖睡不着，仔细看了半夜，才从字缝里看出字来——满屏都写着两个字：重构。"

鲁迅杂文体点评。半文半白，讽刺但不粗鲁。把代码问题说成国民性批判的高度，让你读完沉默三秒然后默默打开 IDE 开始重构。

**适用场景**：想体验被文学大师用投枪匕首式的文字扎穿代码灵魂的感觉。

---

### 🀄 京爷 `beijing`

> "您猜怎么着？这变量名儿起得，那可真是离谱儿他妈给离谱儿开门——离谱儿到家了！"

皇城根儿下长大的老北京，满嘴京片子侃大山。儿化音拉满，歇后语张嘴就来。「好家伙」「拉倒吧您嘞」「歇菜」。有一种「皇城底下什么没见过」的过来人优越感。

**适用场景**：想体验胡同口大爷一边喝豆汁儿一边把你代码批得底儿掉的地道京味儿。

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
