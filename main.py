"""
SD-AutoPromote - 从图片中自动提取 Stable Diffusion 提示词

基于 LangChain + Python 3.12 的图像分析 & 提示词工程工具。
支持 OpenAI 和 DeepSeek，通过 Gradio 提供交互界面。
"""

import argparse
import logging
import sys
import os


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="SD-AutoPromote - 图像提示词提取工具"
    )
    parser.add_argument(
        "--port", type=int, default=7860,
        help="Web UI 端口号 (默认: 7860)"
    )
    parser.add_argument(
        "--share", action="store_true",
        help="生成公开分享链接 (通过 Gradio share)"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="开启调试日志"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已开启")
    
    logger.info("=" * 50)
    logger.info("  SD-AutoPromote 启动中...")
    logger.info(f"  端口: {args.port}")
    logger.info(f"  分享: {'开启' if args.share else '关闭'}")
    logger.info("=" * 50)
    
    try:
        from ui.gradio_app import launch_ui
        launch_ui(server_port=args.port, share=args.share)
    except ImportError as e:
        logger.error(f"导入失败: {e}")
        logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
