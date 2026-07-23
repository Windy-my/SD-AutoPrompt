"""LLM client — 统一调用多供应商 LLM。

所有 OpenAI 兼容接口（DeepSeek / Moonshot / Qwen / GLM / Grok / Together 等）
均通过 langchain_openai.ChatOpenAI 调用，仅 base_url 和 model 不同。
"""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import config
from config.providers import get_provider

def fetch_available_models(provider: str, api_key: str) -> list:
    """
    Call the provider''s /v1/models endpoint to list available models.
    Works with any OpenAI-compatible API.
    Returns list of model IDs, or empty list on failure.
    """
    prov = get_provider(provider)
    if not prov or not api_key:
        return []

    base_url = prov.base_url
    if not base_url:
        return []

    import requests

    url = f"{base_url.rstrip('/')}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        models = [item["id"] for item in data.get("data", [])]
        models = [m for m in models if not m.startswith("ft:")]
        models.sort()
        return models
    except Exception:
        return []



def create_llm(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    temperature: float = 0.1,
) -> Optional[ChatOpenAI]:
    """
    创建 ChatOpenAI 实例。

    所有 OpenAI 兼容的供应商都共用 ChatOpenAI，
    区别仅在于 base_url 和 model 参数。
    """
    provider = provider or config.llm_provider
    api_key = api_key or config.api_key
    model_id = model_id or config.get_model_id()

    if not api_key:
        return None

    prov = get_provider(provider)
    if not prov:
        return None

    base_url = prov.base_url
    if provider == "custom":
        # 自定义供应商使用用户输入的 base_url
        from config.settings import config as cfg
        # 对于 custom，model_id 已经是原始输入
        pass

    return ChatOpenAI(
        model=model_id,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )


def call_llm_with_text(
    system_prompt: str,
    user_text: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
) -> str:
    """纯文本调用 LLM。"""
    llm = create_llm(provider, api_key, model_id)
    if not llm:
        return "错误：API Key 未配置，请在设置页面填写 API Key"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_text),
    ]

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"调用 LLM 时出错: {str(e)}"


def call_llm_with_image(
    system_prompt: str,
    user_text: str,
    image_base64: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
) -> str:
    """
    多模态调用 LLM（图片 + 文本）。

    所有 OpenAI 兼容的供应商统一使用 image_url 格式。
    """
    llm = create_llm(provider, api_key, model_id)
    if not llm:
        return "错误：API Key 未配置，请在设置页面填写 API Key"

    content_parts = [
        {"type": "text", "text": user_text},
        {
            "type": "image_url",
            "image_url": {
                "url": image_base64,
                "detail": "high",
            },
        },
    ]

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=content_parts),
    ]

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"调用多模态 LLM 时出错: {str(e)}"
