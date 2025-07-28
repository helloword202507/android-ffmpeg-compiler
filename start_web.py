#!/usr/bin/env python3
"""
FFmpeg Android 编译配置器 - 快速启动Web界面
"""

import subprocess
import sys

def main():
    """主函数"""
    print("🎬 FFmpeg Android 编译配置器 v2.0")
    print("🚀 启动Web界面...")
    
    try:
        subprocess.run([sys.executable, "main.py", "--web"], check=True)
    except KeyboardInterrupt:
        print("\n👋 已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()