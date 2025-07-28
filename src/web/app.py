"""
Web应用
"""

import sys
import subprocess
import webbrowser
import threading
import time
from pathlib import Path

from .server import WebServer


class WebApp:
    """Web应用"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.server = WebServer(work_dir)
    
    def check_dependencies(self) -> bool:
        """检查依赖"""
        print("🔍 检查依赖...")
        
        try:
            import flask
            print("✅ Flask 已安装")
            return True
        except ImportError:
            print("❌ Flask 未安装")
            choice = input("是否现在安装Flask? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=True)
                    print("✅ Flask 安装成功")
                    return True
                except subprocess.CalledProcessError:
                    print("❌ Flask 安装失败")
                    return False
            else:
                return False
    
    def run(self, port: int = 5000, auto_open: bool = True):
        """运行Web应用"""
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 检查必要文件
        required_files = ["static/index.html", "config_presets.json"]
        missing_files = [f for f in required_files if not (self.work_dir / f).exists()]
        
        if missing_files:
            print("❌ 缺少必要文件:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        # 创建必要目录
        for dir_name in ["build", "logs"]:
            (self.work_dir / dir_name).mkdir(exist_ok=True)
        
        if auto_open:
            print(f"📱 浏览器将自动打开: http://localhost:{port}")
            
            def open_browser():
                time.sleep(2)
                webbrowser.open(f'http://localhost:{port}')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
        
        try:
            self.server.run(port=port)
            return True
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False