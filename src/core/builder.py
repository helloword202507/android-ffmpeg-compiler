"""
构建脚本生成模块
"""

import time
from pathlib import Path
from typing import Dict, List, Optional
from .config import BuildConfig


class ArchitectureConfig:
    """架构配置"""
    
    CONFIGS = {
        "arm64-v8a": {
            "target": "aarch64-linux-android",
            "arch_name": "aarch64", 
            "cpu": "armv8-a",
            "extra_cflags": ""
        },
        "armeabi-v7a": {
            "target": "armv7a-linux-androideabi",
            "arch_name": "arm",
            "cpu": "armv7-a", 
            "extra_cflags": "-mfpu=neon -mfloat-abi=softfp"
        },
        "x86": {
            "target": "i686-linux-android",
            "arch_name": "x86",
            "cpu": "i686",
            "extra_cflags": ""
        },
        "x86_64": {
            "target": "x86_64-linux-android",
            "arch_name": "x86_64", 
            "cpu": "x86-64",
            "extra_cflags": ""
        }
    }
    
    @classmethod
    def get_config(cls, arch: str) -> Dict[str, str]:
        """获取架构配置"""
        if arch not in cls.CONFIGS:
            raise ValueError(f"不支持的架构: {arch}")
        return cls.CONFIGS[arch]
    
    @classmethod
    def get_supported_archs(cls) -> List[str]:
        """获取支持的架构列表"""
        return list(cls.CONFIGS.keys())


class ScriptGenerator:
    """脚本生成器"""
    
    def __init__(self):
        pass
    
    def generate_header(self, config: BuildConfig) -> str:
        """生成脚本头部"""
        arch_list = ' '.join(config.architectures)
        
        # 生成架构配置
        arch_config_lines = ["declare -A ARCH_CONFIG"]
        for arch, arch_config in ArchitectureConfig.CONFIGS.items():
            arch_config_lines.append(
                f'ARCH_CONFIG[{arch}]="{arch_config["target"]} {arch_config["arch_name"]} {arch_config["cpu"]}"'
            )
        arch_config_script = '\n'.join(arch_config_lines)
        
        return f'''#!/bin/bash
# FFmpeg Android 多架构编译脚本
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

set -e

# 架构配置
{arch_config_script}

# 要编译的架构
ARCHS="{arch_list}"
API={config.api}

echo "========================================="
echo "FFmpeg Android 编译"
echo "========================================="
echo "目标架构: $ARCHS"
echo "Android API: $API"
echo "输出类型: {config.outputType}"
echo "解码器: {', '.join(config.decoders)}"
echo "编码器: {', '.join(config.encoders)}"
echo "滤镜: {', '.join(config.filters)}"
echo "========================================="'''
    
    def generate_environment_setup(self) -> str:
        """生成环境设置"""
        return '''
# 基础设置
export WORK_DIR="$(pwd)"
export NDK_ROOT="$WORK_DIR/android-ndk"
export TOOLCHAIN="$NDK_ROOT/toolchains/llvm/prebuilt/windows-x86_64"

# 转换Windows路径为MSYS2路径
export NDK_ROOT=$(cygpath -u "$NDK_ROOT")
export TOOLCHAIN=$(cygpath -u "$TOOLCHAIN")

# 检查环境
if [ ! -d "$NDK_ROOT" ]; then
    echo "错误: Android NDK 目录不存在: $NDK_ROOT"
    exit 1
fi

if [ ! -d "$TOOLCHAIN" ]; then
    echo "错误: 工具链目录不存在: $TOOLCHAIN"
    exit 1
fi

if [ ! -d "ffmpeg" ]; then
    echo "错误: FFmpeg 源码目录不存在"
    exit 1
fi'''
    
    def generate_build_function(self, config: BuildConfig) -> str:
        """生成构建函数"""
        configure_cmd = self._generate_configure_command(config)
        
        return f'''
# 编译函数
build_for_arch() {{
    local ARCH=$1
    local CONFIG=(${{ARCH_CONFIG[$ARCH]}})
    local TARGET=${{CONFIG[0]}}
    local ARCH_NAME=${{CONFIG[1]}}
    local CPU=${{CONFIG[2]}}
    
    echo "========================================="
    echo "开始编译架构: $ARCH"
    echo "目标: $TARGET"
    echo "CPU: $CPU"
    echo "========================================="
    
    # 设置输出目录
    export PREFIX="$WORK_DIR/ffmpeg-android-$ARCH"
    
    # 设置编译器
    export CC="$TOOLCHAIN/bin/${{TARGET}}{config.api}-clang"
    export CXX="$TOOLCHAIN/bin/${{TARGET}}{config.api}-clang++"
    export AR="$TOOLCHAIN/bin/llvm-ar"
    export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
    export STRIP="$TOOLCHAIN/bin/llvm-strip"
    export NM="$TOOLCHAIN/bin/llvm-nm"
    
    # 添加mingw64到PATH
    export PATH="/mingw64/bin:$PATH"
    
    # 设置主机编译器
    export HOSTCC="gcc"
    export HOSTCXX="g++"
    
    # 检查编译器
    if [ ! -f "$CC" ]; then
        echo "错误: 编译器不存在: $CC"
        return 1
    fi
    
    echo "使用编译器: $CC"
    echo "输出目录: $PREFIX"
    
    # 进入ffmpeg目录
    cd ffmpeg
    
    # 清理
    make distclean 2>/dev/null || true
    
    # 架构特定配置
    local EXTRA_CFLAGS=""
    case $ARCH in
        "armeabi-v7a")
            EXTRA_CFLAGS="-mfpu=neon -mfloat-abi=softfp"
            ;;
    esac
    
{configure_cmd}
    
    echo "配置完成，开始编译 $ARCH..."
    
    # 编译和安装
    make -j$(nproc)
    make install
    
    echo "$ARCH 编译成功！"
    echo "库文件位置: $PREFIX"
    ls -la "$PREFIX/lib/" 2>/dev/null || true
    
    # 返回上级目录
    cd ..
}}'''
    
    def generate_footer(self, config: BuildConfig) -> str:
        """生成脚本尾部"""
        arch_count = len(config.architectures)
        
        return f'''
# 编译所有架构
for ARCH in $ARCHS; do
    if [[ ! ${{ARCH_CONFIG[$ARCH]+_}} ]]; then
        echo "错误: 不支持的架构 $ARCH"
        echo "支持的架构: ${{!ARCH_CONFIG[@]}}"
        exit 1
    fi
    
    build_for_arch $ARCH
    echo ""
done

echo "========================================="
echo "所有架构编译完成！"
echo "========================================="

# 显示编译结果
for ARCH in $ARCHS; do
    PREFIX="$WORK_DIR/ffmpeg-android-$ARCH"
    if [ -d "$PREFIX" ]; then
        echo "$ARCH: $PREFIX"
        echo "  库文件数量: $(ls "$PREFIX/lib/"*.so 2>/dev/null | wc -l)"
        echo "  头文件数量: $(find "$PREFIX/include" -name "*.h" 2>/dev/null | wc -l)"
    fi
done

echo ""
echo "编译完成！已生成 {arch_count} 个架构的库文件"'''
    
    def _generate_configure_command(self, config: BuildConfig) -> str:
        """生成configure命令"""
        lines = ['    # 配置命令', '    ./configure \\']
        
        # 基础配置
        base_options = [
            '--prefix="$PREFIX"',
            '--enable-cross-compile',
            '--target-os=android',
            '--arch=$ARCH_NAME',
            '--cpu=$CPU',
            '--cc="$CC"',
            '--cxx="$CXX"',
            '--ar="$AR"',
            '--ranlib="$RANLIB"',
            '--strip="$STRIP"',
            '--nm="$NM"',
            '--host-cc="$HOSTCC"',
            '--sysroot="$TOOLCHAIN/sysroot"',
            '--extra-cflags="$EXTRA_CFLAGS"'
        ]
        
        for option in base_options:
            lines.append(f'        {option} \\')
        
        # 输出类型配置
        is_shared = config.outputType == 'shared'
        lines.append(f'        --{"enable" if is_shared else "disable"}-shared \\')
        lines.append(f'        --{"disable" if is_shared else "enable"}-static \\')
        
        # 优化选项
        opt = config.optimizations
        if opt.disableAsm:
            lines.append('        --disable-asm \\')
        if opt.enablePic:
            lines.append('        --enable-pic \\')
        if opt.disableDebug:
            lines.append('        --disable-debug \\')
        if opt.disableDoc:
            lines.append('        --disable-doc \\')
        if opt.disablePrograms:
            lines.append('        --disable-programs \\')
        if opt.enableSmall:
            lines.append('        --enable-small \\')
        
        # 固定优化选项
        lines.extend([
            '        --disable-symver \\',
            '        --disable-everything \\'
        ])
        
        # 组件配置
        component_types = [
            (config.decoders, 'decoder'),
            (config.encoders, 'encoder'), 
            (config.muxers, 'muxer'),
            (config.demuxers, 'demuxer'),
            (config.protocols, 'protocol'),
            (config.filters, 'filter')
        ]
        
        for components, flag_prefix in component_types:
            for component in components:
                lines.append(f'        --enable-{flag_prefix}={component} \\')
        
        # 移除最后一行的反斜杠
        if lines and lines[-1].endswith(' \\'):
            lines[-1] = lines[-1].rstrip(' \\')
        
        return '\n'.join(lines)


class BuildManager:
    """构建管理器"""
    
    def __init__(self, work_dir: Path, build_dir: Path):
        self.work_dir = Path(work_dir)
        self.build_dir = Path(build_dir)
        self.generator = ScriptGenerator()
    
    def generate_build_script(self, config: BuildConfig) -> Optional[Path]:
        """生成构建脚本"""
        try:
            print("📝 生成编译脚本...")
            
            # 生成脚本内容
            script_parts = [
                self.generator.generate_header(config),
                self.generator.generate_environment_setup(),
                self.generator.generate_build_function(config),
                self.generator.generate_footer(config)
            ]
            
            script_content = '\n'.join(script_parts)
            
            # 保存脚本
            script_path = self.build_dir / "build_ffmpeg.sh"
            self._save_script(script_path, script_content)
            
            print(f"✅ 编译脚本已生成: {script_path}")
            return script_path
            
        except Exception as e:
            print(f"❌ 生成编译脚本失败: {e}")
            return None
    
    def _save_script(self, script_path: Path, content: str) -> None:
        """保存脚本文件"""
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)