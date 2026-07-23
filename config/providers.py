"""LLM 供应商与模型定义。"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ModelInfo:
    """单个模型的信息。"""
    id: str
    name: str
    vision: bool = False


@dataclass
class ProviderInfo:
    """LLM 供应商信息。"""
    id: str
    name: str
    base_url: str
    models: List[ModelInfo]
    api_key_prefix: str = ""  # 提示用户 API Key 的格式


# ==============================
# 供应商与模型列表（按需扩展）
# ==============================

PROVIDERS: Dict[str, ProviderInfo] = {}

# --- OpenAI ---
PROVIDERS["openai"] = ProviderInfo(
    id="openai",
    name="OpenAI",
    base_url="https://api.openai.com/v1",
    api_key_prefix="sk-",
    models=[
        ModelInfo("gpt-4o", "GPT-4o", vision=True),
        ModelInfo("gpt-4o-mini", "GPT-4o Mini", vision=True),
        ModelInfo("gpt-4-turbo", "GPT-4 Turbo", vision=True),
        ModelInfo("gpt-4", "GPT-4"),
        ModelInfo("gpt-3.5-turbo", "GPT-3.5 Turbo"),
    ],
)

# --- DeepSeek ---
PROVIDERS["deepseek"] = ProviderInfo(
    id="deepseek",
    name="DeepSeek",
    base_url="https://api.deepseek.com/v1",
    api_key_prefix="sk-",
    models=[
        ModelInfo("deepseek-chat", "DeepSeek Chat"),
        ModelInfo("deepseek-reasoner", "DeepSeek Reasoner"),
    ],
)

# --- Moonshot / Kimi ---
PROVIDERS["moonshot"] = ProviderInfo(
    id="moonshot",
    name="Moonshot (Kimi)",
    base_url="https://api.moonshot.cn/v1",
    api_key_prefix="sk-",
    models=[
        ModelInfo("moonshot-v1-8k", "moonshot-v1-8k"),
        ModelInfo("moonshot-v1-32k", "moonshot-v1-32k"),
        ModelInfo("moonshot-v1-128k", "moonshot-v1-128k"),
    ],
)

# --- Qwen (通义千问 / 阿里云) ---
PROVIDERS["qwen"] = ProviderInfo(
    id="qwen",
    name="Qwen (通义千问)",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key_prefix="sk-",
    models=[
        ModelInfo("qwen-turbo", "Qwen Turbo"),
        ModelInfo("qwen-plus", "Qwen Plus"),
        ModelInfo("qwen-max", "Qwen Max"),
        ModelInfo("qwen-vl-plus", "Qwen VL Plus", vision=True),
        ModelInfo("qwen-vl-max", "Qwen VL Max", vision=True),
    ],
)

# --- GLM (智谱) ---
PROVIDERS["glm"] = ProviderInfo(
    id="glm",
    name="GLM (智谱)",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key_prefix="",
    models=[
        ModelInfo("glm-4-plus", "GLM-4-Plus"),
        ModelInfo("glm-4-flash", "GLM-4-Flash"),
        ModelInfo("glm-4v-plus", "GLM-4V-Plus", vision=True),
    ],
)

# --- xAI / Grok ---
PROVIDERS["grok"] = ProviderInfo(
    id="grok",
    name="xAI (Grok)",
    base_url="https://api.x.ai/v1",
    api_key_prefix="xai-",
    models=[
        ModelInfo("grok-2-latest", "Grok-2"),
        ModelInfo("grok-2-vision-latest", "Grok-2 Vision", vision=True),
        ModelInfo("grok-3-latest", "Grok-3"),
        ModelInfo("grok-3-vision-latest", "Grok-3 Vision", vision=True),
    ],
)

# --- Together AI ---
PROVIDERS["together"] = ProviderInfo(
    id="together",
    name="Together AI",
    base_url="https://api.together.xyz/v1",
    api_key_prefix="",
    models=[
        ModelInfo("meta-llama/Llama-3.3-70B-Instruct-Turbo", "Llama 3.3 70B"),
        ModelInfo("mistralai/Mixtral-8x22B-Instruct-v0.1", "Mixtral 8x22B"),
    ],
)

# --- 自定义 OpenAI 兼容 ---
PROVIDERS["custom"] = ProviderInfo(
    id="custom",
    name="自定义 (兼容 OpenAI)",
    base_url="",
    api_key_prefix="",
    models=[
        ModelInfo("", "自定义 - 手动输入模型名"),
    ],
)


def get_provider(provider_id: str) -> Optional[ProviderInfo]:
    return PROVIDERS.get(provider_id)


def get_provider_choices() -> List[str]:
    """返回 UI 下拉框用的供应商选项列表。"""
    return [f"{p.name} ({p.id})" for p in PROVIDERS.values()]


def get_provider_id_from_choice(choice: str) -> str:
    """从 UI 选择文本解析出 provider id。"""
    for pid, p in PROVIDERS.items():
        if choice == f"{p.name} ({pid})":
            return pid
    return "openai"


def get_model_choices(provider_id: str) -> List[str]:
    """返回某供应商的模型列表。"""
    p = PROVIDERS.get(provider_id)
    if not p:
        return []
    return [m.name for m in p.models]


def get_model_id(provider_id: str, model_name: str) -> str:
    """从 UI 显示的模型名反查模型 ID。"""
    p = PROVIDERS.get(provider_id)
    if not p:
        return model_name
    for m in p.models:
        if m.name == model_name:
            return m.id
    return model_name


def supports_vision_by_provider(provider_id: str, model_name: str) -> bool:
    """判断某个模型是否支持视觉。"""
    p = PROVIDERS.get(provider_id)
    if not p:
        return False
    model_id = get_model_id(provider_id, model_name)
    for m in p.models:
        if m.id == model_id or m.name == model_name:
            return m.vision
    return False
