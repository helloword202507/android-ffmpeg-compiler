#!/usr/bin/env python3
"""
FFmpeg Android 编译配置器 - 主入口
支持命令行和Web界面两种模式
"""

import sys
import argparse
from pathlib import Path

from src.cli import CLIApp
from src.web import WebApp
from src.utils import ProjectCleaner


def show_usage_info():
    """显示使用信息"""
    print("\n" + "=" * 60)
    print("🎬 FFmpeg Android 编译配置器 v2.0")
    print("=" * 60)
    print("使用方式:")
    print("   1. 命令行模式: python main.py [选项]")
    print("   2. Web界面模式: python main.py --web")
    print("   3. 清理工具: python main.py --clean")
    print("")
    print("🌐 推荐使用Web界面:")
    print("   - 图形化配置界面")
    print("   - 预设配置选择")
    print("   - 一键编译功能")
    print("   - 实时编译状态")
    print("")
    print("📱 启动Web界面: python main.py --web")
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FFmpeg Android 编译配置器 v2.0')
    parser.add_argument('--config', '-c', 
                       help='配置文件路径')
    parser.add_argument('--preset', '-p',
                       choices=['basic', 'standard', 'streaming', 'live', 'complete', 'minimal'],
                       help='使用预设配置')
    parser.add_argument('--web', '-w', action='store_true',
                       help='启动Web配置界面')
    parser.add_argument('--clean', action='store_true',
                       help='清理临时文件和编译输出')
    parser.add_argument('--port', type=int, default=5000,
                       help='Web服务器端口 (默认: 5000)')
    
    args = parser.parse_args()
    
    work_dir = Path.cwd()
    
    # 清理模式
    if args.clean:
        cleaner = ProjectCleaner(work_dir)
        cleaner.clean_all()
        return 0
    
    # Web界面模式
    if args.web:
        web_app = WebApp(work_dir)
        success = web_app.run(port=args.port)
        return 0 if success else 1
    
    # 如果没有参数，显示使用信息并交互选择
    if len(sys.argv) == 1:
        show_usage_info()
        choice = input("\n选择模式 (1=命令行, 2=Web界面, 3=清理): ").strip()
        
        if choice == '2':
            web_app = WebApp(work_dir)
            success = web_app.run()
            return 0 if success else 1
        elif choice == '3':
            cleaner = ProjectCleaner(work_dir)
            cleaner.clean_all()
            return 0
        elif choice != '1':
            print("👋 已退出")
            return 0
    
    # 命令行模式
    cli_app = CLIApp()
    success = cli_app.run()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 已取消")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        sys.exit(1)