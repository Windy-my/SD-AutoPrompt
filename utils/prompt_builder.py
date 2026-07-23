"""Prompt builder utilities for formatting analysis output."""

import re
from typing import Dict


def parse_llm_response(text: str) -> Dict[str, str]:
    """
    Parse LLM response into structured sections.

    Strategy:
      1. Find section headers (### / ## / **header**) and extract content
         until the next header or end of text.
      2. If nothing matches, use entire text as positive_prompt fallback.
    """
    result = {
        "analysis_summary": "",
        "positive_prompt": "",
        "negative_prompt": "",
        "raw_response": text,
    }
    if not text:
        return result

    # Remove markdown code fences that may wrap the output
    text = re.sub(r"```(?:markdown)?\s*\n?", "", text)

    # Define sections and their known header strings
    sections = [
        ("analysis_summary", [
            "### 分析摘要", "## 分析摘要",
            "### Analysis Summary", "## Analysis Summary",
        ]),
        ("positive_prompt", [
            "### 正面提示词", "## 正面提示词",
            "### Positive Prompt", "## Positive Prompt",
        ]),
        ("negative_prompt", [
            "### 负面提示词", "## 负面提示词",
            "### Negative Prompt", "## Negative Prompt",
        ]),
    ]

    # Collect all known header strings for boundary detection
    known_headers = set()
    for _, headers in sections:
        for h in headers:
            known_headers.add(h)

    def is_header(line: str) -> bool:
        s = line.strip()
        if not s:
            return False
        # Check if it matches any known header or generic ##/### line
        for kh in known_headers:
            if s == kh or s.startswith(kh):
                return True
        if re.match(r"^#{2,3}\s+\S", s):
            return True
        return False

    # Extract each section
    for key, headers in sections:
        for h in headers:
            if h not in text:
                continue
            # Split at header, take everything after it
            after = text.split(h, 1)[1]
            content_lines = []
            for line in after.split("\n"):
                if is_header(line):
                    break
                if line.strip().startswith("```"):
                    break
                content_lines.append(line)
            value = "\n".join(content_lines).strip().rstrip("```").strip()
            if value:
                result[key] = value
                break

    # Fallback: if positive_prompt still empty, use raw text as positive
    if not result["positive_prompt"]:
        cleaned = "\n".join(
            l for l in text.split("\n")
            if not is_header(l) and "```" not in l
        ).strip()
        result["positive_prompt"] = cleaned or text.strip()

    return result


def build_skill_system_prompt(skill_style: str) -> str:
    style_prompts = {
        "写实摄影": "\n用户偏向**写实摄影风格**：\n- 使用 photorealistic, highly detailed, sharp focus 等关键词\n- 强调光影的真实性和物理准确性\n- 保留皮肤的天然纹理和细节\n- 避免过度完美的 CGI 感\n- 构图参考专业摄影的取景方式\n",
        "二次元/动漫": "\n用户偏向**二次元动漫风格**：\n- 使用 anime style, cel shading, manga 等关键词\n- 线条清晰，色彩明快\n- 角色具有典型的动漫面部比例（大眼睛等）\n- 强调平面美感，避免过度写实的阴影和纹理\n- 可以加入 anime screentone, vibrant colors 等修饰\n",
        "赛博朋克": "\n用户偏向**赛博朋克风格**：\n- 使用 cyberpunk, neon lights, futuristic city 等关键词\n- 强调霓虹灯光（蓝紫色/粉紫色为主）\n- 包含高科技/低生活的对比元素\n- 阴暗潮湿的未来都市氛围\n- 可以加入 holographic, rain reflection, dark atmosphere\n",
        "油画/古典": "\n用户偏向**油画古典风格**：\n- 使用 oil painting, classical art, Renaissance 等关键词\n- 强调笔触感和画布纹理\n- 暖色调为主，光影柔和（chiaroscuro）\n- 构图参考古典绘画\n- 可以加入 impasto, rich textures, dramatic lighting\n",
        "水彩/手绘": "\n用户偏向**水彩手绘风格**：\n- 使用 watercolor, hand-drawn, sketch 等关键词\n- 色彩透明柔和，边缘自然晕染\n- 纸纹理明显\n- 避免锐利边缘和完全覆盖的颜色\n- 可以加入 soft washes, paper texture, artistic\n",
        "3D 渲染": "\n用户偏向**3D 渲染风格**：\n- 使用 3D render, CGI, octane render 等关键词\n- 强调材质质感（金属、玻璃、皮肤次表面散射等）\n- 光影精确，全局照明效果\n- 可以加入 subsurface scattering, ray tracing, volumetric lighting\n",
    }
    return style_prompts.get(skill_style, "")
