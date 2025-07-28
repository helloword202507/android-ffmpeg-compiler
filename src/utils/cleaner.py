"""
项目清理工具
"""

import shutil
from pathlib import Path


class ProjectCleaner:
    """项目清理器"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        
        # 定义需要清理的目录和文件
        self.cleanup_dirs = [
            "build",
            "logs", 
            "__pycache__",
            "src/__pycache__"
        ]
        
        self.cleanup_patterns = [
            "ffmpeg-android-*",
            "*.pyc",
            "*.pyo"
        ]
    
    def clean_build_outputs(self):
        """清理编译输出"""
        print("🧹 清理编译输出...")
        
        # 清理编译输出目录
        for pattern in ["ffmpeg-android-*"]:
            for path in self.work_dir.glob(pattern):
                if path.is_dir():
                    print(f"删除目录: {path}")
                    shutil.rmtree(path)
        
        print("✅ 编译输出清理完成")
    
    def clean_temp_files(self):
        """清理临时文件"""
        print("🧹 清理临时文件...")
        
        # 清理Python缓存
        for pattern in ["__pycache__", "*.pyc", "*.pyo"]:
            for path in self.work_dir.rglob(pattern):
                if path.is_dir():
                    print(f"删除目录: {path}")
                    shutil.rmtree(path)
                elif path.is_file():
                    print(f"删除文件: {path}")
                    path.unlink()
        
        # 清理日志目录
        logs_dir = self.work_dir / "logs"
        if logs_dir.exists():
            print(f"删除目录: {logs_dir}")
            shutil.rmtree(logs_dir)
        
        print("✅ 临时文件清理完成")
    
    def clean_build_cache(self):
        """清理构建缓存"""
        print("🧹 清理构建缓存...")
        
        build_dir = self.work_dir / "build"
        if build_dir.exists():
            print(f"删除目录: {build_dir}")
            shutil.rmtree(build_dir)
        
        print("✅ 构建缓存清理完成")
    
    def clean_all(self):
        """清理所有"""
        print("🧹 开始全面清理...")
        self.clean_temp_files()
        self.clean_build_cache()
        self.clean_build_outputs()
        print("🎉 清理完成！")