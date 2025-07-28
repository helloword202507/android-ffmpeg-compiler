"""
环境管理模块
"""

import os
import sys
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, List
from .utils import run_command_safe, create_safe_popen


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.ffmpeg_dir = self.work_dir / "ffmpeg"
        self.ndk_dir = self.work_dir / "android-ndk"
        self.msys2_dir = self.work_dir / "msys64"
        
        # NDK配置
        self.ndk_version = "r27d"
        self.ndk_url = f"https://googledownloads.cn/android/repository/android-ndk-{self.ndk_version}-windows.zip"
        
        # MSYS2配置
        self.msys2_url = "https://github.com/msys2/msys2-installer/releases/latest/download/msys2-base-x86_64-latest.sfx.exe"
    
    def check_platform(self) -> bool:
        """检查平台支持"""
        if not sys.platform.startswith('win'):
            raise RuntimeError(f"仅支持Windows平台，当前平台: {sys.platform}")
        return True
    
    def check_git(self) -> bool:
        """检查Git安装"""
        try:
            result = run_command_safe(['git', '--version'])
            if result.returncode == 0:
                print(f"Git已安装: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        print("Git未安装，请先安装Git for Windows")
        print("下载地址: https://git-scm.windows.com/")
        return False
    
    def setup_msys2(self) -> bool:
        """设置MSYS2环境"""
        print("=== 设置MSYS2环境 ===")
        
        if self.msys2_dir.exists():
            print("MSYS2目录已存在")
            return True
        
        # 检查系统已安装的MSYS2
        msys2_paths = [
            Path("C:/msys64"),
            Path("C:/tools/msys64"),
            Path(os.path.expanduser("~/msys64"))
        ]
        
        for path in msys2_paths:
            if path.exists():
                print(f"发现已安装的MSYS2: {path}")
                try:
                    if hasattr(os, 'symlink'):
                        os.symlink(str(path), str(self.msys2_dir))
                    else:
                        shutil.copytree(str(path), str(self.msys2_dir))
                    return True
                except Exception as e:
                    print(f"链接MSYS2失败: {e}")
        
        print("未找到MSYS2安装，请手动安装MSYS2")
        print("下载地址: https://www.msys2.org/")
        return False
    
    def install_msys2_packages(self) -> bool:
        """安装MSYS2包"""
        print("=== 安装MSYS2构建工具 ===")
        
        msys2_bash = self._find_msys2_bash()
        if not msys2_bash:
            print("找不到MSYS2 bash")
            return False
        
        packages = [
            "base-devel",
            "mingw-w64-x86_64-toolchain", 
            "mingw-w64-x86_64-yasm",
            "mingw-w64-x86_64-nasm",
            "mingw-w64-x86_64-pkg-config",
            "make",
            "diffutils"
        ]
        
        # 更新包数据库
        if not self._run_pacman_command(msys2_bash, "pacman -Sy --noconfirm"):
            print("更新MSYS2包数据库失败")
            return False
        
        # 安装包
        for package in packages:
            if not self._run_pacman_command(msys2_bash, f"pacman -S --noconfirm {package}"):
                print(f"安装包 {package} 失败")
                return False
        
        print("MSYS2构建工具安装完成")
        return True
    
    def setup_ffmpeg(self) -> bool:
        """设置FFmpeg源码"""
        print("=== 设置FFmpeg源码 ===")
        
        if not self.check_git():
            return False
        
        if self.ffmpeg_dir.exists():
            print("FFmpeg目录已存在，检查是否为有效的git仓库...")
            if (self.ffmpeg_dir / ".git").exists():
                print("更新现有的FFmpeg仓库...")
                result = run_command_safe("git pull", cwd=self.ffmpeg_dir, shell=True)
                if result.returncode != 0:
                    print("更新失败，重新克隆...")
                    shutil.rmtree(self.ffmpeg_dir)
                    return self._clone_ffmpeg()
                return True
            else:
                print("目录存在但不是git仓库，删除后重新克隆...")
                shutil.rmtree(self.ffmpeg_dir)
        
        return self._clone_ffmpeg()
    
    def setup_ndk(self) -> bool:
        """设置Android NDK"""
        print("=== 设置Android NDK ===")
        
        self.check_platform()
        ndk_filename = f"android-ndk-{self.ndk_version}-windows.zip"
        ndk_path = self.work_dir / ndk_filename
        
        if self.ndk_dir.exists():
            print("Android NDK目录已存在")
            return True
        
        # 下载NDK
        if not ndk_path.exists():
            print(f"从 {self.ndk_url} 下载NDK...")
            if not self._download_file(self.ndk_url, ndk_path):
                print("NDK下载失败")
                return False
        
        # 解压NDK
        print("正在解压Android NDK...")
        try:
            with zipfile.ZipFile(ndk_path, 'r') as zip_ref:
                zip_ref.extractall(self.work_dir)
            
            # 重命名解压后的目录
            extracted_dir = self.work_dir / f"android-ndk-{self.ndk_version}"
            if extracted_dir.exists():
                extracted_dir.rename(self.ndk_dir)
            
            print("Android NDK解压完成")
            ndk_path.unlink()  # 删除压缩包
            return True
            
        except Exception as e:
            print(f"解压失败: {e}")
            return False
    
    def get_msys2_bash_path(self) -> Optional[str]:
        """获取MSYS2 bash路径"""
        return self._find_msys2_bash()
    
    def _find_msys2_bash(self) -> Optional[str]:
        """查找MSYS2 bash路径"""
        possible_paths = [
            self.msys2_dir / "usr" / "bin" / "bash.exe",
            Path("C:/msys64/usr/bin/bash.exe")
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        return None
    
    def _run_pacman_command(self, msys2_bash: str, command: str) -> bool:
        """运行pacman命令"""
        cmd = f'"{msys2_bash}" -lc "{command}"'
        result = run_command_safe(cmd, shell=True)
        return result.returncode == 0
    
    def _clone_ffmpeg(self) -> bool:
        """克隆FFmpeg源码"""
        print("正在克隆FFmpeg源码...")
        
        sources = [
            "https://gitee.com/mirrors/ffmpeg.git",
            "https://github.com/FFmpeg/FFmpeg.git"
        ]
        
        for source in sources:
            print(f"尝试从 {source} 克隆...")
            cmd = f"git clone {source} ffmpeg --depth 1"
            result = run_command_safe(cmd, cwd=self.work_dir, shell=True)
            if result.returncode == 0:
                return True
            print(f"从 {source} 克隆失败，尝试下一个源...")
        
        print("所有源都无法访问，请检查网络连接")
        return False
    
    def _download_file(self, url: str, filename: Path) -> bool:
        """下载文件"""
        print(f"正在下载: {url}")
        try:
            def progress_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded * 100) // total_size)
                    print(f"\r下载进度: {percent}%", end='', flush=True)
            
            urllib.request.urlretrieve(url, filename, progress_hook)
            print(f"\n下载完成: {filename}")
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False