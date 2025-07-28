#!/usr/bin/env python3
"""
FFmpeg Android 编译配置器 - 清理工具
"""

import argparse
from pathlib import Path
from src.utils import ProjectCleaner


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FFmpeg Android 编译配置器清理工具')
    parser.add_argument('--all', '-a', action='store_true', help='清理所有文件')
    parser.add_argument('--build', '-b', action='store_true', help='清理编译输出')
    parser.add_argument('--temp', '-t', action='store_true', help='清理临时文件')
    parser.add_argument('--cache', '-c', action='store_true', help='清理构建缓存')
    
    args = parser.parse_args()
    
    work_dir = Path.cwd()
    cleaner = ProjectCleaner(work_dir)
    
    if args.all:
        cleaner.clean_all()
    else:
        if args.build:
            cleaner.clean_build_outputs()
        if args.temp:
            cleaner.clean_temp_files()
        if args.cache:
            cleaner.clean_build_cache()
        
        # 如果没有指定任何选项，显示帮助
        if not any([args.build, args.temp, args.cache]):
            parser.print_help()
            print("\n💡 使用 --all 清理所有文件")


if __name__ == "__main__":
    main()