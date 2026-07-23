"""
Main prompt agent — 图像分析 → 提示词提取工作流。

工作流：
  1. 如果 LLM 支持视觉 → 直接发送图片给 LLM，按 system_prompt 提取
  2. 如果 LLM 不支持视觉 → 调用本地视觉模型提取结构化信息，
     然后将本地模型结果发送给 LLM 润色 → 最终输出
"""

import base64
import io
import logging
import os
from typing import Dict, Optional

from PIL import Image

from config.providers import supports_vision_by_provider
from models.llm_client import call_llm_with_text, call_llm_with_image
from models.vision_model import describe_image_local
from skills.registry import registry
from utils.prompt_builder import parse_llm_response
from utils.image_utils import get_image_info

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "system_prompt.txt"
)


def load_system_prompt() -> str:
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load system prompt: {e}")
        return ""


def encode_image_to_base64(image_path: str) -> Optional[str]:
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            max_dim = 2048
            if max(img.size) > max_dim:
                ratio = max_dim / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            buf.seek(0)
            b64_str = base64.b64encode(buf.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        logger.error(f"Failed to encode image: {e}")
        return None


def _build_system_prompt(skill_name: Optional[str] = None) -> str:
    """拼接系统提示词 + 风格偏好指令。"""
    sp = load_system_prompt()
    if skill_name and skill_name != "默认（自动识别）":
        instruction = registry.get_instruction_for_skill(skill_name)
        if instruction:
            sp += "\n\n" + instruction
    return sp


# ──────────────────────────────────────────────
# 工作流 1：LLM 支持视觉 → 直接提取
# ──────────────────────────────────────────────

def _workflow_vision_llm(
    image_path: str,
    api_key: str,
    provider: str,
    model_name: str,
    skill_name: Optional[str] = None,
) -> Dict[str, str]:
    """LLM 本身支持视觉，一步到位。"""
    system_prompt = _build_system_prompt(skill_name)
    image_data = encode_image_to_base64(image_path)
    if not image_data:
        return {"error": "图片编码失败"}

    user_msg = (
        "请分析这张图片，按照规定的流程进行结构化分析，"
        "并输出分析摘要、正面提示词和负面提示词。"
    )

    response = call_llm_with_image(
        system_prompt=system_prompt,
        user_text=user_msg,
        image_base64=image_data,
        provider=provider,
        api_key=api_key,
        model_id=model_name,
    )

    if response.startswith("错误") or response.startswith("调用"):
        return {"error": response}
    return parse_llm_response(response)


# ──────────────────────────────────────────────
# 工作流 2：LLM 不支持视觉 → 本地视觉 + LLM 润色
# ──────────────────────────────────────────────

LOCAL_VISION_EXTRACT_PROMPT = """你是一个视觉辅助模型。请基于以下关于一张图片的描述，尽可能详细地提取出视觉信息。

请按以下格式输出（中文）：

## 全局概览
图片类型、整体色调、氛围

## 背景与环境
背景内容、环境元素、空间深度

## 人物动作与姿势
（若有）肢体动作、身体朝向；若无人则写"无人物"

## 人物表情
（若有）情绪状态、面部细节；若无人则写"无人物"

## 补充细节
服装、光照、色彩方案、艺术风格"""


def _workflow_local_vision(
    image_path: str,
    api_key: str,
    provider: str,
    model_name: str,
    skill_name: Optional[str] = None,
) -> Dict[str, str]:
    """
    本地视觉模型提取 → LLM 润色并转化为 SD 提示词。

    步骤：
      1. 本地模型（BLIP 等）描述图片 → 得到原始 caption
      2. 将 caption + 图片基本信息发给 LLM，让 LLM 做结构化分析
      3. 将 LLM 的分析结果 + system prompt 发给 LLM 润色 → 最终提示词
    """
    logger.info("Workflow: local vision → LLM polish")

    # ── 第 1 步：本地模型提取 ──
    local_desc = describe_image_local(image_path)
    img_info = get_image_info(image_path)

    if local_desc:
        raw_caption = local_desc
        logger.info(f"Local vision caption: {raw_caption}")
    else:
        raw_caption = None
        logger.warning("Local vision model unavailable, skipping local extraction")

    # ── 第 2 步：结构化提取（通过 LLM 文本通道）──
    if raw_caption:
        extraction_input = (
            f"图片尺寸：{img_info.get('width', '?')}x{img_info.get('height', '?')}\n"
            f"图片格式：{img_info.get('format', '?')}\n\n"
            f"视觉模型原始描述：{raw_caption}\n\n"
            "请根据以上信息，按格式输出结构化视觉分析。"
        )
        extraction = call_llm_with_text(
            system_prompt=LOCAL_VISION_EXTRACT_PROMPT,
            user_text=extraction_input,
            provider=provider,
            api_key=api_key,
            model_id=model_name,
        )
    else:
        extraction = (
            "全局概览：无法获取图片内容（本地视觉模型不可用）\n"
            "背景与环境：未知\n"
            "人物动作：未知\n"
            "人物表情：未知\n"
            f"图片尺寸：{img_info.get('width', '?')}x{img_info.get('height', '?')}"
        )

    # ── 第 3 步：LLM 润色 → SD 提示词 ──
    system_prompt = _build_system_prompt(skill_name)

    polish_input = (
        f"以下是一张图片的结构化分析结果：\n\n"
        f"{extraction}\n\n"
        f"请根据以上分析结果，输出完整的分析摘要（中文）、"
        f"正面提示词（Positive Prompt, 英文逗号分隔）和"
        f"负面提示词（Negative Prompt, 英文逗号分隔）。"
    )

    final_response = call_llm_with_text(
        system_prompt=system_prompt,
        user_text=polish_input,
        provider=provider,
        api_key=api_key,
        model_id=model_name,
    )

    if final_response.startswith("错误") or final_response.startswith("调用"):
        return {"error": final_response}
    return parse_llm_response(final_response)


# ──────────────────────────────────────────────
# 统一入口
# ──────────────────────────────────────────────

def analyze_image(
    image_path: str,
    api_key: str,
    provider: str = "openai",
    model_name: str = "GPT-4o",
    skill_name: Optional[str] = None,
    use_fallback: bool = True,
) -> Dict[str, str]:
    """
    主入口：分析图片并提取 SD 提示词。

    工作流选择：
      - 模型支持视觉 → _workflow_vision_llm（一步完成）
      - 模型不支持视觉 → _workflow_local_vision（本地视觉 + LLM 润色）
    """
    from utils.image_utils import validate_image
    is_valid, error_msg = validate_image(image_path)
    if not is_valid:
        return {"error": error_msg}

    if not api_key:
        return {"error": "请先在设置页面填写 API Key"}

    vision = supports_vision_by_provider(provider, model_name)

    if vision:
        logger.info(f"Workflow: vision LLM ({provider}/{model_name})")
        return _workflow_vision_llm(
            image_path, api_key, provider, model_name, skill_name
        )

    if use_fallback:
        logger.info(f"Workflow: local vision + LLM polish ({provider}/{model_name})")
        return _workflow_local_vision(
            image_path, api_key, provider, model_name, skill_name
        )

    return {
        "error": (
            f"模型 '{model_name}' 不支持图像输入，且已禁用本地视觉回退。"
            "请切换到支持视觉的模型（如 GPT-4o / Qwen VL），"
            "或在设置中启用本地视觉模块。"
        )
    }
