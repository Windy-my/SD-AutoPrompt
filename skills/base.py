"""Base skill definitions for style preferences."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Skill:
    """A skill/profile representing a user's style preference."""
    
    name: str          # Display name (e.g., "写实摄影")
    id: str            # Internal ID (e.g., "realistic")
    description: str   # Short description
    prompt_instruction: str  # Additional instruction appended to system prompt
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "description": self.description,
        }


# Built-in style skills
BUILTIN_SKILLS = {
    "realistic": Skill(
        name="写实摄影",
        id="realistic",
        description="以真实摄影为基准，强调光影、纹理和自然感",
        prompt_instruction="""
【用户风格偏好：写实摄影】
- 使用 photorealistic, highly detailed, sharp focus 等关键词
- 强调光影的真实性和物理准确性
- 保留皮肤的天然纹理和细节
- 避免过度完美的 CGI 感
- 构图参考专业摄影的取景方式
""",
    ),
    "anime": Skill(
        name="二次元/动漫",
        id="anime",
        description="二次元动漫风格，线条清晰，色彩明快",
        prompt_instruction="""
【用户风格偏好：二次元/动漫】
- 使用 anime style, cel shading, manga influence 等关键词
- 线条清晰，色彩明快
- 角色具有典型的动漫面部比例（大眼睛等）
- 强调平面美感，避免过度写实的阴影和纹理
- 可以加入 vibrant colors, clean lineart 等修饰
""",
    ),
    "cyberpunk": Skill(
        name="赛博朋克",
        id="cyberpunk",
        description="赛博朋克风格，霓虹灯光、未来都市",
        prompt_instruction="""
【用户风格偏好：赛博朋克】
- 使用 cyberpunk, neon lights, futuristic city 等关键词
- 强调霓虹灯光（蓝紫色/粉紫色为主）
- 包含高科技/低生活的对比元素
- 阴暗潮湿的未来都市氛围
- 可以加入 holographic, rain reflection, dark atmosphere
""",
    ),
    "oil_painting": Skill(
        name="油画/古典",
        id="oil_painting",
        description="油画古典风格，温暖色调，笔触感",
        prompt_instruction="""
【用户风格偏好：油画/古典】
- 使用 oil painting, classical art, Renaissance 等关键词
- 强调笔触感和画布纹理
- 暖色调为主，光影柔和（chiaroscuro）
- 构图参考古典绘画
- 可以加入 impasto, rich textures, dramatic lighting
""",
    ),
    "watercolor": Skill(
        name="水彩/手绘",
        id="watercolor",
        description="水彩手绘风格，色彩透明柔和",
        prompt_instruction="""
【用户风格偏好：水彩/手绘】
- 使用 watercolor, hand-drawn, sketch 等关键词
- 色彩透明柔和，边缘自然晕染
- 纸纹理明显
- 避免锐利边缘和完全覆盖的颜色
- 可以加入 soft washes, paper texture, artistic
""",
    ),
    "render_3d": Skill(
        name="3D 渲染",
        id="render_3d",
        description="3D 渲染风格，材质质感丰富",
        prompt_instruction="""
【用户风格偏好：3D 渲染】
- 使用 3D render, CGI, octane render 等关键词
- 强调材质质感（金属、玻璃、皮肤次表面散射等）
- 光影精确，全局照明效果
- 可以加入 subsurface scattering, ray tracing, volumetric lighting
""",
    ),
}
