"""
Gradio web UI for SD-AutoPromote.

两个标签页：
  📷 图片分析  — 上传图片 + 开始分析 + 结果展示
  ⚙️ 设置     — 选择 LLM 供应商 / API Key / 模型 / 风格技能
"""

import logging
from typing import Optional, Tuple

import gradio as gr

from agents.prompt_agent import analyze_image
from config.settings import config
from config.providers import (
    PROVIDERS,
    get_provider,
    get_model_choices,
    get_model_id,
)
from models.llm_client import fetch_available_models
from skills.registry import registry

logger = logging.getLogger(__name__)

SKILL_CHOICES = registry.get_skill_choices()

# ─── 供应商下拉选项 ──────────────────────────────
PROVIDER_CHOICES = []
for pid, p in PROVIDERS.items():
    PROVIDER_CHOICES.append(f"{p.name} ({pid})")


def _get_provider_id(choice: str) -> str:
    for pid, p in PROVIDERS.items():
        if choice == f"{p.name} ({pid})":
            return pid
    return "openai"


# ─── 分析回调 ─────────────────────────────────────

def on_analyze(
    image_file: Optional[object],
    provider_choice: str,
    api_key: str,
    model_choice: str,
    skill_name: str,
    use_fallback: bool,
) -> Tuple[str, str, str, str]:
    if image_file is None:
        return ("❌ 请先上传一张图片", "", "", "")

    try:
        file_path = image_file if isinstance(image_file, str) else image_file.name
    except Exception as e:
        return (f"❌ 文件上传错误: {str(e)}", "", "", "")

    ext = (file_path.rsplit(".", 1)[-1] if "." in file_path else "").lower()
    if ext not in ("png", "jpg", "jpeg"):
        return (f"❌ 不支持的格式: .{ext}，仅支持 PNG/JPG", "", "", "")

    provider_id = _get_provider_id(provider_choice)
    model_id = get_model_id(provider_id, model_choice)

    try:
        config.llm_provider = provider_id
        config.model_name = model_choice
        config.use_vision_fallback = use_fallback
        config.api_key = api_key

        result = analyze_image(
            image_path=file_path,
            api_key=api_key,
            provider=provider_id,
            model_name=model_choice,
            skill_name=skill_name,
            use_fallback=use_fallback,
        )

        if "error" in result:
            return (f"❌ {result['error']}", "", "", "")

        summary = result.get("analysis_summary", "无分析摘要")
        positive = result.get("positive_prompt", "无正面提示词")
        negative = result.get("negative_prompt", "无负面提示词")
        return ("✅ 分析完成！", summary, positive, negative)

    except Exception as e:
        logger.exception("Analysis failed")
        return (f"❌ 分析出错: {str(e)}", "", "", "")


# ─── 供应商切换 → 更新模型下拉 ─────────────────

def _on_provider_change(provider_choice: str):
    pid = _get_provider_id(provider_choice)
    models = get_model_choices(pid)
    if not models:
        return gr.update(choices=[""], value="")
    return gr.update(choices=models, value=models[0])



# ─── 刷新模型列表 ───────────────────────────────

def _on_refresh_models(provider_choice: str, api_key: str):
    """Call provider API to fetch available models, update dropdown."""
    pid = _get_provider_id(provider_choice)
    if not api_key:
        return gr.update(choices=[], value=""), "请先输入 API Key"
    
    models = fetch_available_models(pid, api_key)
    if not models:
        # 如果 API 拉取失败，回退到本地硬编码列表
        local = get_model_choices(pid)
        return gr.update(choices=local, value=local[0] if local else ""), "API 拉取失败，已回退到预设列表"
    
    return gr.update(choices=models, value=models[0]), f"已从 API 获取 {len(models)} 个模型"


# ─── 构建 UI ─────────────────────────────────────

def build_ui() -> gr.Blocks:
    with gr.Blocks(title=config.app_title) as app:
        gr.Markdown(
            """
            <div style="text-align:center;margin-bottom:1rem">
                <h1>🎨 SD-AutoPromote</h1>
                <p style="color:#666">从图片中自动提取 Stable Diffusion 提示词</p>
            </div>
            """
        )

        with gr.Tabs():
            # ===== 分析页 =====
            with gr.TabItem("📷 图片分析"):
                with gr.Row(equal_height=False):
                    with gr.Column(scale=1):
                        image_input = gr.Image(
                            label="上传图片 (PNG / JPG)",
                            type="filepath",
                            height=400,
                        )
                        analyze_btn = gr.Button(
                            "🚀 开始分析", variant="primary", size="lg"
                        )
                        status_output = gr.Textbox(
                            label="状态", interactive=False,
                        )

                    with gr.Column(scale=1):
                        with gr.Tabs():
                            with gr.TabItem("📋 分析摘要"):
                                summary_output = gr.Markdown(
                                    value="*等待分析结果...*",
                                )
                            with gr.TabItem("✅ 正面提示词"):
                                positive_output = gr.Textbox(
                                    label="Positive Prompt",
                                    lines=8, interactive=False,
                                )
                            with gr.TabItem("❌ 负面提示词"):
                                negative_output = gr.Textbox(
                                    label="Negative Prompt",
                                    lines=6, interactive=False,
                                )

            # ===== 设置页 =====
            with gr.TabItem("⚙️ 设置"):
                with gr.Group():
                    gr.Markdown("### LLM 配置")

                    provider_dropdown = gr.Dropdown(
                        choices=PROVIDER_CHOICES,
                        value=PROVIDER_CHOICES[0],
                        label="LLM 供应商",
                        info="选择要使用的 LLM 服务商",
                    )

                    api_key_input = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="sk-... / 粘贴你的 API Key",
                    )

                    with gr.Row():
                        model_dropdown = gr.Dropdown(
                            choices=get_model_choices("openai"),
                            value=get_model_choices("openai")[0],
                            label="模型",
                            scale=4,
                            info="选择该供应商下的模型，或点击右侧刷新按钮从 API 拉取最新列表",
                        )
                        refresh_btn = gr.Button("🔄 刷新", scale=1, min_width=80)

                    gr.Markdown("---")
                    gr.Markdown("### 🎯 风格偏好 (Skill)")

                    skill_dropdown = gr.Dropdown(
                        choices=SKILL_CHOICES,
                        value="默认（自动识别）",
                        label="图片风格偏好",
                        info="Agent 会根据你选择的风格调整提示词输出",
                    )

                    gr.Markdown("---")
                    gr.Markdown("### ⚙️ 高级设置")

                    fallback_checkbox = gr.Checkbox(
                        value=True,
                        label="启用本地视觉回退",
                        info="当所选模型不支持图片输入时，使用本地 AI 识别图片",
                    )

        # ─── 事件绑定 ────────────────────────────
        analyze_btn.click(
            fn=on_analyze,
            inputs=[
                image_input,
                provider_dropdown,
                api_key_input,
                model_dropdown,
                skill_dropdown,
                fallback_checkbox,
            ],
            outputs=[status_output, summary_output, positive_output, negative_output],
        )

        provider_dropdown.change(
            fn=_on_provider_change,
            inputs=[provider_dropdown],
            outputs=[model_dropdown],
        )

        refresh_btn.click(
            fn=_on_refresh_models,
            inputs=[provider_dropdown, api_key_input],
            outputs=[model_dropdown, status_output],
        )

    return app


def launch_ui(server_port: int = 7860, share: bool = False):
    app = build_ui()
    app.launch(
        server_name="127.0.0.1",
        server_port=server_port,
        share=share,
        show_error=True,
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="indigo"),
    )
