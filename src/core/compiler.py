"""
编译管理模块
"""

import subprocess
from pathlib import Path
from typing import Optional, Callable
from .config import BuildConfig
from .builder import BuildManager
from .utils import create_safe_popen, safe_readline, clean_output_line


class CompilerManager:
    """编译管理器"""
    
    def __init__(self, work_dir: Path, build_dir: Path):
        self.work_dir = Path(work_dir)
        self.build_dir = Path(build_dir)
        self.build_manager = BuildManager(work_dir, build_dir)
    
    def compile(self, config: BuildConfig, msys2_bash_path: str, 
                progress_callback: Optional[Callable] = None,
                log_callback: Optional[Callable] = None) -> bool:
        """执行编译"""
        try:
            # 生成构建脚本
            script_path = self.build_manager.generate_build_script(config)
            if not script_path:
                return False
            
            # 执行编译
            return self._run_compilation(script_path, msys2_bash_path, 
                                       progress_callback, log_callback)
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ 编译失败: {e}", 'error')
            return False
    
    def _run_compilation(self, script_path: Path, msys2_bash_path: str,
                        progress_callback: Optional[Callable] = None,
                        log_callback: Optional[Callable] = None) -> bool:
        """运行编译脚本"""
        try:
            if log_callback:
                log_callback("🚀 开始编译...", 'info')
            
            # 构建命令
            script_name = script_path.name
            cmd = f'"{msys2_bash_path}" -lc "cd \'{self.work_dir}\' && chmod +x build/{script_name} && ./build/{script_name}"'
            
            # 启动进程
            process = create_safe_popen(cmd, shell=True, cwd=self.work_dir)
            
            # 实时读取输出
            while True:
                output = safe_readline(process)
                if output == '' and process.poll() is not None:
                    break
                if output:
                    clean_line = clean_output_line(output)
                    if clean_line and log_callback:
                        # 根据内容判断日志级别
                        level = self._determine_log_level(clean_line)
                        log_callback(clean_line, level)
                        
                        # 更新进度
                        if progress_callback:
                            progress_info = self._parse_progress(clean_line)
                            if progress_info:
                                progress_callback(progress_info)
            
            return_code = process.poll()
            
            if return_code == 0:
                if log_callback:
                    log_callback("✅ 编译成功完成！", 'success')
                self._show_compilation_results(log_callback)
                return True
            else:
                if log_callback:
                    log_callback(f"❌ 编译失败，退出码: {return_code}", 'error')
                return False
                
        except Exception as e:
            if log_callback:
                log_callback(f"❌ 执行编译时出错: {e}", 'error')
            return False
    
    def _determine_log_level(self, line: str) -> str:
        """确定日志级别"""
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['error', 'failed', 'fatal']):
            return 'error'
        elif any(keyword in line_lower for keyword in ['warning', 'warn']):
            return 'warning'
        elif any(keyword in line_lower for keyword in ['success', 'completed', 'done']):
            return 'success'
        else:
            return 'info'
    
    def _parse_progress(self, line: str) -> Optional[dict]:
        """解析进度信息"""
        line_lower = line.lower()
        
        # 检测架构编译开始
        for i, arch in enumerate(['arm64-v8a', 'armeabi-v7a', 'x86', 'x86_64']):
            if f'开始编译架构: {arch}' in line:
                return {
                    'stage': 'compiling',
                    'arch': arch,
                    'message': f'正在编译架构: {arch}'
                }
        
        # 检测编译阶段
        if 'configure' in line_lower and 'ffmpeg' in line_lower:
            return {
                'stage': 'configuring',
                'message': '配置FFmpeg...'
            }
        elif 'make -j' in line_lower or 'compiling' in line_lower:
            return {
                'stage': 'building',
                'message': '编译中...'
            }
        elif 'make install' in line_lower or 'installing' in line_lower:
            return {
                'stage': 'installing',
                'message': '安装库文件...'
            }
        elif '编译成功' in line:
            return {
                'stage': 'completed',
                'message': '编译完成'
            }
        
        return None
    
    def _show_compilation_results(self, log_callback: Optional[Callable] = None):
        """显示编译结果"""
        if not log_callback:
            return
        
        log_callback("=" * 50, 'info')
        log_callback("编译结果:", 'info')
        log_callback("=" * 50, 'info')
        
        # 检查输出目录
        output_dirs = list(self.work_dir.glob("ffmpeg-android-*"))
        
        if output_dirs:
            for output_dir in output_dirs:
                if output_dir.is_dir():
                    lib_dir = output_dir / "lib"
                    if lib_dir.exists():
                        arch = output_dir.name.replace('ffmpeg-android-', '')
                        log_callback(f"架构: {arch}", 'info')
                        log_callback(f"输出目录: {output_dir}", 'info')
                        
                        # 列出生成的库文件
                        so_files = list(lib_dir.glob("*.so"))
                        if so_files:
                            log_callback("生成的库文件:", 'info')
                            for so_file in so_files:
                                file_size = so_file.stat().st_size / (1024 * 1024)
                                log_callback(f"  - {so_file.name} ({file_size:.1f} MB)", 'info')
                        else:
                            log_callback("  警告: 未找到 .so 文件", 'warning')
        else:
            log_callback("未找到编译输出目录", 'warning')
        
        log_callback("使用说明:", 'info')
        log_callback("1. 将 lib/ 目录中的 .so 文件复制到 Android 项目的 src/main/jniLibs/对应架构目录", 'info')
        log_callback("2. 将 include/ 目录中的头文件复制到 Android 项目的 src/main/cpp/include/", 'info')
        log_callback("3. 在 CMakeLists.txt 中配置链接这些库", 'info')