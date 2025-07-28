"""
配置管理模块
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class OptimizationConfig:
    """优化配置"""
    disableAsm: bool = True
    enablePic: bool = True
    disableDebug: bool = True
    disableDoc: bool = True
    disablePrograms: bool = True
    enableSmall: bool = False


@dataclass
class BuildConfig:
    """构建配置"""
    api: int = 21
    outputType: str = "shared"  # shared or static
    architectures: list = None
    decoders: list = None
    encoders: list = None
    muxers: list = None
    demuxers: list = None
    protocols: list = None
    filters: list = None
    optimizations: OptimizationConfig = None
    
    def __post_init__(self):
        if self.architectures is None:
            self.architectures = ["arm64-v8a", "armeabi-v7a"]
        if self.decoders is None:
            self.decoders = ["h264", "aac", "mp3"]
        if self.encoders is None:
            self.encoders = []
        if self.muxers is None:
            self.muxers = ["mp4"]
        if self.demuxers is None:
            self.demuxers = ["mov", "mp4"]
        if self.protocols is None:
            self.protocols = ["file", "http", "https"]
        if self.filters is None:
            self.filters = []
        if self.optimizations is None:
            self.optimizations = OptimizationConfig()


class ConfigManager:
    """配置管理器"""
    
    SUPPORTED_ARCHITECTURES = ["arm64-v8a", "armeabi-v7a", "x86", "x86_64"]
    SUPPORTED_OUTPUT_TYPES = ["shared", "static"]
    
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.build_dir = self.work_dir / "build"
        self.config_file = self.build_dir / "config.json"
        self.presets_file = self.work_dir / "config_presets.json"
    
    def load_config(self, config_path: Optional[Path] = None) -> BuildConfig:
        """加载配置"""
        config_file = config_path or self.config_file
        
        if not config_file.exists():
            return self.get_default_config()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._dict_to_config(data)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return self.get_default_config()
    
    def save_config(self, config: BuildConfig, config_path: Optional[Path] = None) -> bool:
        """保存配置"""
        config_file = config_path or self.config_file
        
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_to_dict(config), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_default_config(self) -> BuildConfig:
        """获取默认配置"""
        return BuildConfig()
    
    def load_presets(self) -> Dict[str, Any]:
        """加载预设配置"""
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('presets', {})
        except Exception:
            return {}
    
    def load_preset_config(self, preset_name: str) -> Optional[BuildConfig]:
        """加载预设配置"""
        presets = self.load_presets()
        
        if preset_name not in presets:
            return None
        
        preset_data = presets[preset_name]['config']
        return self._dict_to_config(preset_data)
    
    def validate_config(self, config: BuildConfig) -> bool:
        """验证配置"""
        # 验证架构
        for arch in config.architectures:
            if arch not in self.SUPPORTED_ARCHITECTURES:
                raise ValueError(f"不支持的架构: {arch}")
        
        # 验证输出类型
        if config.outputType not in self.SUPPORTED_OUTPUT_TYPES:
            raise ValueError(f"不支持的输出类型: {config.outputType}")
        
        # 验证API级别
        if config.api < 16:
            raise ValueError(f"API级别必须大于等于16: {config.api}")
        
        return True
    
    def _config_to_dict(self, config: BuildConfig) -> Dict[str, Any]:
        """配置对象转字典"""
        data = asdict(config)
        # 转换嵌套的dataclass
        if isinstance(data['optimizations'], dict):
            pass  # 已经是字典
        else:
            data['optimizations'] = asdict(data['optimizations'])
        return data
    
    def _dict_to_config(self, data: Dict[str, Any]) -> BuildConfig:
        """字典转配置对象"""
        # 字段名映射（保持驼峰命名）
        field_mapping = {
            'outputType': 'outputType'
        }
        
        # 优化选项字段名映射（保持驼峰命名）
        opt_field_mapping = {
            'disableAsm': 'disableAsm',
            'enablePic': 'enablePic',
            'disableDebug': 'disableDebug',
            'disableDoc': 'disableDoc',
            'disablePrograms': 'disablePrograms',
            'enableSmall': 'enableSmall'
        }
        
        # 转换主配置字段名
        config_data = {}
        for key, value in data.items():
            new_key = field_mapping.get(key, key)
            config_data[new_key] = value
        
        # 处理优化配置
        opt_data = config_data.get('optimizations', {})
        if isinstance(opt_data, dict):
            # 转换优化选项字段名
            converted_opt_data = {}
            for key, value in opt_data.items():
                new_key = opt_field_mapping.get(key, key)
                converted_opt_data[new_key] = value
            optimizations = OptimizationConfig(**converted_opt_data)
        else:
            optimizations = OptimizationConfig()
        
        config_data['optimizations'] = optimizations
        
        # 移除不支持的字段（preset字段仅用于前端显示）
        unsupported_fields = ['preset']
        for field in unsupported_fields:
            config_data.pop(field, None)
        
        return BuildConfig(**config_data)
    
    def print_config_summary(self, config: BuildConfig):
        """打印配置摘要"""
        print("\n📋 编译配置摘要:")
        print("=" * 30)
        print(f"Android API: {config.api}")
        print(f"输出类型: {config.outputType}")
        print(f"目标架构: {', '.join(config.architectures)}")
        print(f"解码器: {', '.join(config.decoders)}")
        print(f"编码器: {', '.join(config.encoders)}")
        print(f"复用器: {', '.join(config.muxers)}")
        print(f"解复用器: {', '.join(config.demuxers)}")
        print(f"协议: {', '.join(config.protocols)}")
        print(f"滤镜: {', '.join(config.filters)}")
        print("=" * 30)