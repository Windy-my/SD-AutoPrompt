# SD-AutoPromote 🎨

**从图片中自动提取 Stable Diffusion 提示词**

SD-AutoPromote 是一个基于 LangChain + Python 3.12 的图像分析工具，能够自动从用户上传的图片中提取视觉信息，并生成高质量、结构化、可直接用于 **Stable Diffusion** 的英文提示词（Prompt）。

---

## 功能特性

- **多 LLM 供应商支持**：OpenAI、DeepSeek、Qwen（通义千问）、GLM（智谱）、Moonshot（Kimi）、xAI（Grok）、Together AI 等，统一兼容 OpenAI API 格式
- **API Key + 模型选择**：输入 API Key 后自动拉取该供应商的可用模型列表，无需手动输入模型名
- **结构化图像分析**：从背景/环境、人物动作/姿势、人物表情、补充细节四个维度提取视觉信息
- **风格偏好 (Skill) 模块**：内置 6 种风格（写实摄影、二次元/动漫、赛博朋克、油画/古典、水彩/手绘、3D 渲染），Agent 会根据偏好调整提示词
- **视觉回退机制**：如果 LLM 不支持图片输入，自动调用本地视觉模型（BLIP）做图像描述，再交由 LLM 润色
- **交互式 Web UI**：基于 Gradio，上传图片即用，无需编写代码
- **支持 PNG / JPG** 格式

---

## 快速开始

### 环境要求

- Python 3.12+
- Windows / Linux / macOS

### 1. 克隆项目

```bash
git clone https://github.com/your-username/SD-AutoPromote.git
cd SD-AutoPromote
```

### 2. 创建虚拟环境（可选但推荐）

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

核心依赖：`langchain`、`gradio`、`Pillow`、`requests`

### 4. 启动

```bash
python main.py --port 7860
```

打开浏览器访问 **http://127.0.0.1:7860**

### 5. 使用

1. 切换到 **⚙️ 设置** 标签页
2. 选择 **LLM 供应商**（如 OpenAI、DeepSeek、Qwen 等）
3. 填写你的 **API Key**
4. 点击 **🔄 刷新** 按钮，自动从 API 拉取可用模型
5. 选择 **模型**（如 GPT-4o、Qwen VL Plus 等）
6. 可选：选择 **风格偏好**（如写实摄影、二次元等）
7. 切换到 **📷 图片分析** 标签页
8. 上传图片（PNG / JPG）
9. 点击 **🚀 开始分析**

---

## 工作流说明

### 如果 LLM 支持图片输入（如 GPT-4o、Qwen VL Plus 等）

```
上传图片 → 直接发送给 LLM → LLM 按系统提示词结构化分析 → 输出提示词
```

一步到位，效果最佳。

### 如果 LLM 不支持图片输入（如 DeepSeek Chat、Moonshot 等）

```
上传图片 → 本地视觉模型 (BLIP) 提取场景描述
        → LLM 做结构化分析（背景/环境/动作/表情）
        → LLM 润色并输出最终提示词
```

此时需要额外安装本地视觉模型依赖并下载模型权重。

#### 安装本地视觉模型依赖

```bash
# 安装 torch 和 transformers
.\venv\Scripts\python.exe -m pip install torch transformers accelerate
```

#### 下载本地视觉模型

由于 HuggingFace 在国内访问不稳定，建议使用镜像站下载：

```bash
# 创建缓存目录
mkdir .model_cache

# 使用 hf-mirror.com 镜像下载 BLIP 模型（约 1GB）
cd .model_cache
git lfs install
git clone https://hf-mirror.com/Salesforce/blip-image-captioning-base

# 回到项目根目录
cd ..
```

程序会自动在以下位置查找模型：

1. `.model_cache/blip-image-captioning-base/`（用户下载路径）
2. `.model_cache/models--Salesforce--blip-image-captioning-base/snapshots/`（HuggingFace Hub 缓存路径）
3. `blip-image-captioning-base/`（项目根目录）

如果未找到本地模型，程序不会卡死或报错，而是**优雅降级**——仅用图片基本信息（尺寸、格式）请求 LLM 自行推理。但此时效果取决于 LLM 自身的推理能力。

---

## 项目结构

```
SD-AutoPromote/
├── main.py                  # 启动入口
├── requirements.txt         # Python 依赖
├── system_prompt.txt        # 系统提示词（分析标准）
├── .gitignore
├── config/
│   ├── settings.py          # 应用配置
│   └── providers.py         # LLM 供应商与模型定义
├── agents/
│   └── prompt_agent.py      # 核心工作流调度
├── models/
│   ├── llm_client.py        # LLM 调用封装
│   └── vision_model.py      # 本地视觉模型（回退方案）
├── skills/
│   ├── base.py              # Skill 定义
│   └── registry.py          # Skill 注册表
├── utils/
│   ├── image_utils.py       # 图片处理工具
│   └── prompt_builder.py    # 提示词解析与构建
├── ui/
│   └── gradio_app.py        # Gradio Web UI
├── .model_cache/            # (自动创建) 视觉模型缓存
└── venv/                    # (可选) Python 虚拟环境
```

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--port` | Web UI 端口号 | `7860` |
| `--share` | 生成公开分享链接（通过 Gradio share） | 关闭 |
| `--debug` | 开启调试日志 | 关闭 |

示例：

```bash
# 指定端口
python main.py --port 8080

# 生成公开链接（可用于临时分享给他人）
python main.py --share

# 调试模式
python main.py --debug
```

---

## 支持的 LLM 供应商

| 供应商 | API 格式 | 视觉模型 |
|--------|----------|----------|
| **OpenAI** | 标准 OpenAI API | GPT-4o / GPT-4o Mini / GPT-4 Turbo |
| **DeepSeek** | OpenAI 兼容 | — |
| **Moonshot / Kimi** | OpenAI 兼容 | — |
| **Qwen (通义千问)** | OpenAI 兼容 | Qwen VL Plus / Qwen VL Max |
| **GLM (智谱)** | OpenAI 兼容 | GLM-4V-Plus |
| **xAI (Grok)** | OpenAI 兼容 | Grok-2 Vision / Grok-3 Vision |
| **Together AI** | OpenAI 兼容 | — |
| **自定义** | OpenAI 兼容 | 取决于模型 |

> 所有供应商均通过 OpenAI 兼容 API 调用。你只需要在 UI 中填入 API Key，点击「刷新」即可自动获取可用模型列表。

---

## 常见问题

### Q: 上传图片后状态显示"分析完成"但没有输出？

检查 LLM 返回的原始内容是否被正确解析。可以在终端查看日志中的完整响应。

### Q: 本地视觉模型下载失败怎么办？

确保 `git lfs` 已安装，或使用浏览器直接下载模型文件放到 `.model_cache/blip-image-captioning-base/` 目录下。

### Q: 如何添加自定义风格偏好？

编辑 `skills/base.py` 中的 `BUILTIN_SKILLS` 字典，添加新的 `Skill` 对象即可。

---

## License

MIT
