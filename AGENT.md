# AGENT.md — Code Roaster 开发者指南

> 本文档面向 AI Agent 和人类开发者，帮助你快速理解项目架构并进行二次开发。

---

## 📌 项目概览

**Code Roaster（赛博包工头）** 是一个基于大模型的命令行代码审查工具。核心流程：获取 `git diff` → 大模型生成毒舌点评 → Reflection 自省改进 → 流式终端输出。

**技术栈**: Python 3.8+ / OpenAI SDK / python-dotenv / Rich / Git

---

## 🏗️ 核心架构

```
用户命令行
    │
    ▼
main.py (CLI 入口)
    │
    ├──▶ config.py (配置检查 + 一键配置向导)
    │       └── .env 文件 → python-dotenv → 环境变量
    │
    ├──▶ tools.py (工具函数)
    │       └── subprocess → git diff HEAD / git diff --staged
    │
    ├──▶ agent.py (AI Agent)
    │       ├── prompts.py (性格提示词 + 反驳指令)
    │       ├── OpenAI Client / Anthropic SDK (双接口兼容)
    │       └── Reflection + Rebuttal 工作流:
    │            ① 生成初版点评
    │            ② 自我反思优化
    │            ③ 流式输出最终结果
    │            ④ 【反驳模式】用户与 AI 角色实时对线
    │
    ├──▶ history.py (审查历史 + 每周统计)
    │       └── ~/.code-roaster/history.json
    │
    └──▶ tui.py (Textual 终端 GUI)
            ├── 鼠标点击 / 复选框 / 下拉菜单
            ├── 流式审查输出
            └── 反驳模式（Input 组件 + 回合制对话）
```

### 模块职责与调用关系

| 模块 | 职责 | 被谁调用 |
|------|------|----------|
| `main.py` | CLI 入口、参数解析、流程编排、流式渲染、反驳对话循环 | 用户直接运行 |
| `config.py` | 加载 `.env`、配置校验、8 平台预设一键配置向导 | `main.py`、`tui.py` |
| `tools.py` | 执行 `git diff` / `git diff --staged`、按文件拆分 diff | `main.py`、`tui.py` |
| `prompts.py` | 存储各角色 system prompt、reflection prompt、反驳指令 | `agent.py`、`main.py`、`tui.py` |
| `agent.py` | 与大模型交互、Reflection 工作流、反驳流式输出、双 API 兼容 | `main.py`、`tui.py` |
| `history.py` | 审查记录保存/加载、历史回顾、每周统计 | `main.py`、`tui.py` |
| `tui.py` | Textual 终端 GUI：文件选择、审查、反驳、统计 | `roaster-tui` 命令 |

---

## 📐 代码规范

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块/文件名 | `snake_case` | `code_roaster`, `git_tools` |
| 函数名 | `snake_case`，动词开头 | `get_git_diff()`, `check_config()` |
| 类名 | `PascalCase` | `RoasterAgent` |
| 常量 | `UPPER_SNAKE_CASE` | `PERSONAS`, `PROJECT_ROOT` |
| 私有函数 | `_` 前缀 | `_show_onboarding()`, `_generate_roast()` |

### 文档字符串（Docstring）

所有公开函数和类必须包含 docstring，使用 Google 风格：

```python
def get_git_diff() -> str:
    """
    运行 `git diff HEAD` 获取当前未提交的代码改动。

    如果工作区干净（无改动），返回空字符串。
    如果不在 Git 仓库中或 Git 未安装，返回错误提示字符串。

    Returns:
        str: git diff 的输出文本，或错误提示信息
    """
```

### 类型注解

所有函数签名必须包含类型注解：

```python
def roast(self, diff_text: str) -> str:
    ...

def roast_stream(self, diff_text: str):
    """Yields str chunks."""
    ...
```

### 异常处理规范

- **永不裸奔**：所有 I/O 操作（文件、网络、子进程）必须用 try/except 包裹
- **优雅降级**：AI 调用失败时返回 None 或错误提示，不允许 crash
- **用户友好**：错误信息使用中文，清晰告知用户发生了什么以及如何解决

```python
# ✅ 正确示例
try:
    response = self.client.chat.completions.create(...)
except Exception as e:
    return None  # 让上层处理

# ❌ 错误示例
response = self.client.chat.completions.create(...)  # 可能崩溃
```

---

## 🛠️ 二次开发指南

### 如何添加新的 Persona

1. 打开 `src/code_roaster/prompts.py`
2. 在 `PERSONAS` 字典中添加新条目：

```python
PERSONAS = {
    # ... 已有性格 ...

    "pirate": {
        "name": "海盗船长",
        "emoji": "🏴‍☠️",
        "description": "用海盗口吻点评代码的暴躁船长",
        "system_prompt": (
            "你是一个在大海上漂泊了 30 年的海盗船长，不知为何被拉来 review 代码。\n"
            "你的任务：审查以下 git diff 代码变更。\n\n"
            "要求：\n"
            "1. 必须精准指出至少一个真正的代码 Bug 或逻辑硬伤\n"
            "2. 用海盗口吻（哟嚯嚯、小的们、走跳板等）吐槽\n"
            "3. 总点评字数控制在 250 字以内\n"
            "4. 用中文输出（但保留海盗语气词）"
        ),
        "reflection_prompt": (
            "你刚才对一段代码进行了点评。现在请你进行严格的自我反思。\n\n"
            "请检查：\n"
            "1. 海盗口吻够不够浓烈？有没有「哟嚯嚯」「走跳板」这些经典海盗用语？\n"
            "2. 暴躁程度够不够？\n"
            "3. 你是不是真的指出了代码的硬伤？\n\n"
            "现在，请重新生成一个【终极破防版】的点评。更海盗、更暴躁。"
            "字数控制在 250 字以内。"
        ),
        "no_diff_message": (
            "哟嚯嚯！没有代码改动？你是想让船长走跳板吗？\n"
            "快给老子写点东西出来，不然把你丢进海里喂鲨鱼！"
        ),
    },
}
```

3. 新 Persona 的 key（如 `"pirate"`）会自动出现在 `--persona` 参数的可选值中（通过 `get_available_personas()`）
4. 无需修改任何其他文件，即可通过 `-p pirate` 使用

**Persona 配置字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 角色中文名称，显示在终端标题 |
| `emoji` | `str` | 角色图标，用于终端装饰 |
| `description` | `str` | 一句话角色描述，用于 `--list-personas` |
| `system_prompt` | `str` | 角色的系统提示词，定义语气和行为 |
| `reflection_prompt` | `str` | 反思阶段的提示词，用于自我改进 |
| `no_diff_message` | `str` | 当没有代码改动时的角色专属吐槽 |

> **反驳模式** 使用全局 `REBUTTAL_INSTRUCTION`（在 `prompts.py` 中定义）追加到各角色的 system prompt 末尾。无需为每个角色单独写反驳指令。

### 反驳模式原理

审查完成后，用户可输入反驳理由，AI 保持角色语气进行回怼：

```
CLI 流程:
  roast 流式输出 → 保存 history → Prompt.ask("不服来辩？")
  → 用户输入 → agent.rebuttal_stream(conversation) → 流式回怼
  → 循环（最多 10 回合）→ 空输入 / "算了" / Ctrl+C 退出

TUI 流程:
  roast 完成 → _start_rebuttal() 显示 Input 组件
  → on_input_submitted → _do_rebuttal worker 线程
  → 流式回怼 → _show_rebuttal_input 显示下一轮输入
  → 重复至空输入 / 退出关键词 / 10 回合上限
```

**关键实现细节：**
- `conversation` 是完整的 messages 列表 `[{role, content}, ...]`，每轮追加 user + assistant 两条
- `agent.rebuttal_stream(messages)` 接收预构建的 messages，直接发给 API
- Anthropic 接口会自动从 messages 中分离 `system` role
- 空回复保护：AI 返回空内容时不加入对话历史，避免格式异常
- TUI 中反驳内容不另存 history（原始 roast 已由 `do_roast` 保存）

### 如何支持新的大模型 API

本项目使用 OpenAI 兼容接口，任何提供 `/v1/chat/completions` 端点的平台均可直接使用，无需修改代码。

**开箱即用的平台：**
- DeepSeek、OpenAI、智谱 AI、Moonshot、通义千问、Ollama 本地模型 等

**如需适配非 OpenAI 兼容接口（如 Anthropic Claude 原生 API）：**

1. 在 `src/code_roaster/agent.py` 中添加新的客户端初始化逻辑
2. 抽象出一个 `BaseAgent` 基类，让 `OpenAIRoasterAgent` 和 `ClaudeRoasterAgent` 继承
3. 在 `main.py` 中根据配置选择对应的 Agent 实现

```python
# 未来架构示意
class BaseRoasterAgent(ABC):
    @abstractmethod
    def roast_stream(self, diff_text: str): ...

class OpenAIRoasterAgent(BaseRoasterAgent):
    # 当前实现

class ClaudeRoasterAgent(BaseRoasterAgent):
    # 使用 Anthropic SDK 的实现
```

### 如何添加新的工具函数

1. 在 `src/code_roaster/tools.py` 中添加新函数：

```python
def get_git_diff_staged() -> str:
    """
    获取已暂存（git add 后）的代码改动。

    Returns:
        str: git diff --staged 的输出文本
    """
    ...
```

2. 在 `main.py` 中调用新函数，将结果传递给 Agent
3. 在 `prompts.py` 的提示词中说明有哪些工具信息可用

### 历史记录数据结构

审查记录保存在 `~/.code-roaster/history.json`，每条记录格式：

```json
{
  "time": "2026-06-08T14:30:00.123456+08:00",
  "persona": "toxic",
  "persona_emoji": "🚬",
  "files": ["src/auth.py", "src/utils.py"],
  "roast": "点评内容前 500 字..."
}
```

- 时间戳使用 `astimezone().isoformat()` 含时区信息
- `_parse_time()` 函数统一剥离时区做比较，兼容新旧格式
- 最多保留 200 条记录
- 写操作有 3 次重试机制防并发冲突

---

## 💻 开发流程

### 本地开发环境搭建

```bash
# 1. 克隆并进入项目
git clone https://github.com/YOUR_USERNAME/code-roaster.git
cd code-roaster

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装为可编辑包（可选，方便调试）
pip install -e .

# 5. 配置 .env
cp .env.example .env
# 编辑 .env 填入真实 API Key

# 6. 在 Git 仓库中做一些代码修改，然后运行
python -m code_roaster.main -p toxic
```

### 测试方法

当前项目采用手动测试方式：

```bash
# 测试 1：无 .env 文件 → 应显示新手指引
rm .env && python -m code_roaster.main

# 测试 2：非 Git 目录 → 应显示错误提示
cd /tmp && python -m code_roaster.main

# 测试 3：干净工作区 → 应显示摸鱼嘲讽
git add -A && git commit -m "test"
python -m code_roaster.main

# 测试 4：有改动 → 应正常生成点评
echo "test" >> some_file.py
python -m code_roaster.main -p toxic
python -m code_roaster.main -p professor
python -m code_roaster.main -p coworker
python -m code_roaster.main -p kfc

# 测试 5：--list-personas
python -m code_roaster.main --list-personas
```

### 提交 PR 的流程

1. **Fork** 主仓库到你的 GitHub 账号
2. 创建特性分支：`git checkout -b feat/my-feature`
3. 编写代码，遵循上方代码规范
4. 本地测试通过后提交：
   ```bash
   git add -A
   git commit -m "feat: 简要描述你的改动

   详细说明：
   - 改动点 1
   - 改动点 2"
   ```
5. 推送到你的 Fork：`git push origin feat/my-feature`
6. 在 GitHub 上创建 Pull Request，填写清晰的 PR 描述

**Commit 信息规范（Conventional Commits）：**
- `feat:` — 新功能
- `fix:` — Bug 修复
- `docs:` — 文档更新
- `refactor:` — 代码重构
- `style:` — 格式调整
- `test:` — 测试相关

---

## 🔮 已知限制与未来规划

### 已解决（原限制）

1. ~~仅支持 OpenAI 兼容接口~~ → **已支持 Anthropic Claude 原生 API**（v1.3.0+）
2. ~~单文件 diff~~ → **已支持多文件拆分 + 交互式勾选**（CLI + TUI 均有）
3. ~~无历史记录~~ → **已支持审查历史 + 每周统计**（`~/.code-roaster/history.json`）
4. ~~无 TUI~~ → **已支持 Textual 终端 GUI**（`roaster-tui`）
5. ~~单次输出~~ → **已支持反驳模式**：审查后可与 AI 角色实时多轮对线

### 当前限制

1. **仅支持 git diff HEAD**：暂不支持审查指定 commit、PR diff 等
2. **无智能截断**：超长 diff 可能导致 token 超限
3. **无缓存机制**：相同 diff 重复调用浪费 API 额度
4. **串行 Reflection**：生成和反思是串行的，增加了一倍 API 调用成本
5. **TUI 反驳模式**：已实现但暂不支持文件列表传参到反驳会话

### 未来规划

- [ ] 支持审查指定 commit 范围（`git diff HEAD~3`、`--staged` 等）
- [ ] 支持 GitHub PR Review 集成（GitHub Action）
- [ ] 智能 diff 截断，超长 diff 自动分块审查
- [ ] 本地 diff 缓存，避免重复 API 调用
- [ ] 生成分享卡片（JSON → Pillow 渲染图片）
- [ ] 代码心理侧写（从代码反推作者性格）
- [ ] VSCode 插件
- [ ] 盲盒 Persona（随机抽取隐藏角色）
- [ ] 毒舌 Commit Message 生成器

---

## 👤 维护者信息

**项目维护者**: Code Roaster Contributors

**响应时间**: Issue 通常在 48 小时内回复，PR 在 1 周内 Review。

**联系方式**:
- GitHub Issues: [https://github.com/YOUR_USERNAME/code-roaster/issues](https://github.com/YOUR_USERNAME/code-roaster/issues)
- 欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License — 详见项目根目录 LICENSE 文件。
