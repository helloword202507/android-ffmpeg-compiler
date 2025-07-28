"""
Web服务器
"""

import json
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any

from flask import Flask, render_template, request, jsonify, send_from_directory, Response

from ..core import ConfigManager, EnvironmentManager, CompilerManager


class CompilationStatus:
    """编译状态管理"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置状态"""
        self.running = False
        self.completed = False
        self.success = False
        self.progress = 0
        self.status = ''
        self.error = None
    
    def update(self, **kwargs):
        """更新状态"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'running': self.running,
            'completed': self.completed,
            'success': self.success,
            'progress': self.progress,
            'status': self.status,
            'error': self.error
        }


class LogManager:
    """日志管理"""
    
    def __init__(self, max_lines: int = 1000):
        self.log_queue = queue.Queue()
        self.log_cache = []
        self.max_lines = max_lines
    
    def add_log(self, message: str, level: str = 'info'):
        """添加日志"""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': str(message).strip()
        }
        
        try:
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            pass
        
        self.log_cache.append(log_entry)
        
        if len(self.log_cache) > self.max_lines:
            self.log_cache = self.log_cache[-self.max_lines:]
    
    def get_logs(self) -> list:
        """获取所有日志"""
        return self.log_cache.copy()
    
    def clear_logs(self):
        """清空日志"""
        self.log_cache.clear()
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break


class WebServer:
    """Web服务器"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.build_dir = self.work_dir / "build"
        self.build_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.config_manager = ConfigManager(self.work_dir)
        self.env_manager = EnvironmentManager(self.work_dir)
        self.compiler_manager = CompilerManager(self.work_dir, self.build_dir)
        
        # 状态管理
        self.compilation_status = CompilationStatus()
        self.log_manager = LogManager()
        
        # 创建Flask应用
        self.app = Flask(__name__, 
                        static_folder=str(self.work_dir / "static"),
                        template_folder=str(self.work_dir / "static"))
        
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/')
        def index():
            return send_from_directory(self.app.static_folder, 'index.html')
        
        @self.app.route('/api/presets')
        def api_presets():
            presets = self.config_manager.load_presets()
            return jsonify(presets)
        
        @self.app.route('/api/preset/<preset_name>')
        def api_preset(preset_name):
            presets = self.config_manager.load_presets()
            if preset_name in presets:
                return jsonify(presets[preset_name])
            else:
                return jsonify({'error': '预设不存在'}), 404
        
        @self.app.route('/api/save-config', methods=['POST'])
        def api_save_config():
            try:
                data = request.get_json()
                config = self.config_manager._dict_to_config(data)
                success = self.config_manager.save_config(config)
                
                if success:
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'error': '保存失败'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/generate-script', methods=['POST'])
        def api_generate_script():
            try:
                data = request.get_json()
                config = self.config_manager._dict_to_config(data)
                
                script_path = self.compiler_manager.build_manager.generate_build_script(config)
                
                if script_path:
                    return jsonify({'success': True, 'script_path': str(script_path)})
                else:
                    return jsonify({'success': False, 'error': '脚本生成失败'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/start-compilation', methods=['POST'])
        def api_start_compilation():
            try:
                data = request.get_json()
                
                if self.compilation_status.running:
                    return jsonify({'success': False, 'error': '已有编译任务在运行'})
                
                self.compilation_status.reset()
                self.log_manager.clear_logs()
                
                config = self.config_manager._dict_to_config(data)
                success = self._start_compilation_async(config)
                
                if success:
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'error': '启动编译失败'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/compilation-status')
        def api_compilation_status():
            return jsonify(self.compilation_status.to_dict())
        
        @self.app.route('/api/logs')
        def api_logs():
            try:
                logs = self.log_manager.get_logs()
                return jsonify({'success': True, 'logs': logs})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/logs/stream')
        def api_logs_stream():
            def generate():
                yield "data: " + json.dumps({'type': 'connected'}) + "\n\n"
                
                while True:
                    try:
                        log_entry = self.log_manager.log_queue.get(timeout=1)
                        yield "data: " + json.dumps(log_entry) + "\n\n"
                    except queue.Empty:
                        yield "data: " + json.dumps({'type': 'heartbeat'}) + "\n\n"
                    except Exception:
                        break
            
            return Response(generate(), 
                           mimetype='text/event-stream',
                           headers={
                               'Cache-Control': 'no-cache',
                               'Connection': 'keep-alive',
                               'Access-Control-Allow-Origin': '*'
                           })
        
        @self.app.route('/api/logs/clear', methods=['POST'])
        def api_logs_clear():
            try:
                self.log_manager.clear_logs()
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def _start_compilation_async(self, config) -> bool:
        """异步启动编译"""
        def compile_worker():
            try:
                self._run_compilation_workflow(config)
            except Exception as e:
                self.compilation_status.update(
                    running=False,
                    completed=True,
                    success=False,
                    progress=0,
                    status='编译失败',
                    error=str(e)
                )
                self.log_manager.add_log(f"❌ 编译失败: {e}", 'error')
        
        compile_thread = threading.Thread(target=compile_worker)
        compile_thread.daemon = True
        compile_thread.start()
        
        return True
    
    def _run_compilation_workflow(self, config):
        """运行编译工作流"""
        self.compilation_status.update(
            running=True,
            completed=False,
            success=False,
            progress=0,
            status='初始化编译环境...',
            error=None
        )
        
        self.log_manager.add_log("🚀 开始FFmpeg Android编译", 'info')
        
        # 环境准备
        prep_steps = [
            (10, '检查编译环境...', self.env_manager.check_platform),
            (20, '设置MSYS2环境...', self.env_manager.setup_msys2),
            (30, '安装编译工具包...', self.env_manager.install_msys2_packages),
            (40, '准备FFmpeg源码...', self.env_manager.setup_ffmpeg),
            (50, '设置Android NDK...', self.env_manager.setup_ndk)
        ]
        
        for progress, status, step_func in prep_steps:
            self.compilation_status.update(progress=progress, status=status)
            self.log_manager.add_log(f"🔧 {status}", 'info')
            
            try:
                if not step_func():
                    if '安装编译工具包' in status:
                        self.log_manager.add_log(f"⚠️ {status}失败，但可以继续...", 'warning')
                        continue
                    raise Exception(f"{status}失败")
                self.log_manager.add_log(f"✅ {status}完成", 'success')
            except Exception as e:
                raise Exception(f"{status}失败: {e}")
        
        # 开始编译
        self.compilation_status.update(progress=60, status='开始编译...')
        
        msys2_bash_path = self.env_manager.get_msys2_bash_path()
        if not msys2_bash_path:
            raise Exception("找不到MSYS2 bash")
        
        success = self.compiler_manager.compile(
            config,
            msys2_bash_path,
            progress_callback=self._progress_callback,
            log_callback=self._log_callback
        )
        
        if success:
            self.compilation_status.update(
                running=False,
                completed=True,
                success=True,
                progress=100,
                status='编译完成！',
                error=None
            )
        else:
            raise Exception("编译过程失败")
    
    def _progress_callback(self, progress_info: Dict[str, Any]):
        """进度回调"""
        stage = progress_info.get('stage', '')
        message = progress_info.get('message', '')
        
        # 根据阶段计算进度
        stage_progress = {
            'configuring': 70,
            'building': 85,
            'installing': 95,
            'completed': 100
        }
        
        progress = stage_progress.get(stage, 60)
        self.compilation_status.update(progress=progress, status=message)
    
    def _log_callback(self, message: str, level: str = 'info'):
        """日志回调"""
        self.log_manager.add_log(message, level)
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """运行服务器"""
        print("🚀 启动 FFmpeg Android 编译配置器")
        print("=" * 50)
        print(f"📱 网页界面: http://localhost:{port}")
        print("🔧 配置文件: build/config.json")
        print("📝 编译脚本: build/build_ffmpeg.sh")
        print("=" * 50)
        print("💡 提示: 编译过程中的详细日志将显示在Web界面中")
        print("🔧 按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            print("\n👋 服务器已停止")