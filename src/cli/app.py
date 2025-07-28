"""
命令行应用
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..core import ConfigManager, EnvironmentManager, CompilerManager


class CLIApp:
    """命令行应用"""
    
    def __init__(self):
        self.work_dir = Path.cwd()
        self.build_dir = self.work_dir / "build"
        self.build_dir.mkdir(exist_ok=True)
        
        # 初始化核心组件
        self.config_manager = ConfigManager(self.work_dir)
        self.env_manager = EnvironmentManager(self.work_dir)
        self.compiler_manager = CompilerManager(self.work_dir, self.build_dir)
    
    def run(self, args: Optional[list] = None):
        """运行CLI应用"""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            if parsed_args.preset:
                return self._run_with_preset(parsed_args.preset)
            elif parsed_args.config:
                return self._run_with_config(parsed_args.config)
            else:
                return self._run_interactive()
        except KeyboardInterrupt:
            print("\n👋 已取消")
            return False
        except Exception as e:
            print(f"❌ 运行失败: {e}")
            return False
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """创建参数解析器"""
        parser = argparse.ArgumentParser(description='FFmpeg Android 编译配置器')
        parser.add_argument('--config', '-c', 
                           help='配置文件路径')
        parser.add_argument('--preset', '-p',
                           choices=['basic', 'standard', 'streaming', 'live', 'complete', 'minimal'],
                           help='使用预设配置')
        return parser
    
    def _run_with_preset(self, preset_name: str) -> bool:
        """使用预设配置运行"""
        print(f"🎯 使用预设配置: {preset_name}")
        
        config = self.config_manager.load_preset_config(preset_name)
        if not config:
            print(f"❌ 未找到预设配置: {preset_name}")
            return False
        
        return self._run_compilation(config)
    
    def _run_with_config(self, config_path: str) -> bool:
        """使用配置文件运行"""
        print(f"📋 使用配置文件: {config_path}")
        
        config = self.config_manager.load_config(Path(config_path))
        return self._run_compilation(config)
    
    def _run_interactive(self) -> bool:
        """交互式运行"""
        print("🎬 FFmpeg Android 编译配置器")
        print("=" * 50)
        
        # 显示预设选项
        presets = self.config_manager.load_presets()
        if presets:
            print("可用的预设配置:")
            for i, (key, preset) in enumerate(presets.items(), 1):
                print(f"{i}. {preset['name']} - {preset['description']}")
            
            choice = input(f"\n选择预设配置 (1-{len(presets)}) 或按回车使用默认配置: ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(presets):
                preset_key = list(presets.keys())[int(choice) - 1]
                config = self.config_manager.load_preset_config(preset_key)
                print(f"✅ 已选择预设: {presets[preset_key]['name']}")
            else:
                config = self.config_manager.get_default_config()
                print("✅ 使用默认配置")
        else:
            config = self.config_manager.get_default_config()
            print("✅ 使用默认配置")
        
        return self._run_compilation(config)
    
    def _run_compilation(self, config) -> bool:
        """运行编译"""
        try:
            # 显示配置摘要
            self.config_manager.print_config_summary(config)
            
            # 验证配置
            self.config_manager.validate_config(config)
            
            # 环境设置
            if not self._setup_environment():
                return False
            
            # 询问是否开始编译
            choice = input("是否立即开始编译 FFmpeg? (y/n): ").lower().strip()
            if choice not in ['y', 'yes', '是']:
                print("✅ 环境设置完成，您可以稍后手动运行编译")
                return True
            
            # 开始编译
            msys2_bash_path = self.env_manager.get_msys2_bash_path()
            if not msys2_bash_path:
                print("❌ 找不到MSYS2 bash")
                return False
            
            return self.compiler_manager.compile(
                config, 
                msys2_bash_path,
                log_callback=self._log_callback
            )
            
        except Exception as e:
            print(f"❌ 编译过程中出现错误: {e}")
            return False
    
    def _setup_environment(self) -> bool:
        """设置编译环境"""
        steps = [
            ("检查平台", self.env_manager.check_platform),
            ("设置MSYS2环境", self.env_manager.setup_msys2),
            ("安装MSYS2包", self.env_manager.install_msys2_packages),
            ("设置FFmpeg源码", self.env_manager.setup_ffmpeg),
            ("设置Android NDK", self.env_manager.setup_ndk)
        ]
        
        for step_name, step_func in steps:
            print(f"🔧 {step_name}...")
            try:
                if not step_func():
                    if step_name == "安装MSYS2包":
                        print(f"⚠️ {step_name}失败，但可以继续...")
                        continue
                    print(f"❌ {step_name}失败")
                    return False
                print(f"✅ {step_name}完成")
            except Exception as e:
                print(f"❌ {step_name}出错: {e}")
                return False
        
        return True
    
    def _log_callback(self, message: str, level: str = 'info'):
        """日志回调"""
        print(message)