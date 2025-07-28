# 🎬 FFmpeg Android 编译配置

一个用于简化FFmpeg Android库编译的图形化配置工具，支持命令行和Web界面两种使用模式。

## ✨ 特性

- 🖥️ **双模式支持**: 命令行模式和Web图形界面
- 📱 **多架构支持**: arm64-v8a, armeabi-v7a, x86, x86_64
- 🎯 **预设配置**: 提供6种预设配置，满足不同使用场景
- ⚙️ **灵活配置**: 支持自定义编解码器、格式、协议等
- 🚀 **一键编译**: 自动化编译流程，简化操作
- 🧹 **清理工具**: 内置清理工具，管理编译产物
- 📊 **实时状态**: Web界面实时显示编译进度

## 📦 预设配置

| 预设 | 描述 | 适用场景 |
|------|------|----------|
| **最小版** | 仅包含基本H.264解码功能 | 简单播放器 |
| **基础版** | 常用编解码器和格式支持 | 基本视频播放应用 |
| **标准版** | 包含常用编解码器，适合大多数应用 | 通用移动应用 |
| **流媒体版** | 专为流媒体播放优化 | 在线视频播放 |
| **直播版** | 支持实时编码和推流协议 | 直播应用 |
| **完整版** | 包含所有功能的完整版本 | 专业视频处理 |

## 🚀 快速开始

### 环境要求

- Python 3.7+
- Android NDK
- MSYS2 (Windows)
- FFmpeg 源码

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用方式

#### 1. Web界面模式 (推荐)

```bash
# 启动Web界面
python main.py --web

# 或使用快速启动脚本
python start_web.py
```

然后在浏览器中访问 `http://localhost:5000`

#### 2. 命令行模式

```bash
# 使用预设配置
python main.py --preset standard

# 使用自定义配置文件
python main.py --config my_config.json

# 交互式选择
python main.py
```

#### 3. 清理工具

```bash
# 清理所有文件
python main.py --clean

# 或使用专用清理脚本
python clean.py --all
```

## 📁 项目结构

```
ffmpeg-android-builder/
├── main.py                 # 主入口文件
├── start_web.py           # Web界面快速启动
├── clean.py               # 清理工具
├── config_presets.json    # 预设配置文件
├── src/                   # 源码目录
│   ├── cli/              # 命令行界面模块
│   ├── web/              # Web界面模块
│   ├── core/             # 核心功能模块
│   └── utils/            # 工具模块
├── static/               # Web界面静态资源
├── build/                # 编译输出目录
├── logs/                 # 日志文件
├── android-ndk/          # Android NDK
├── ffmpeg/               # FFmpeg源码
└── msys64/               # MSYS2环境
```

## ⚙️ 配置说明

### 基本配置

- **Android API**: 目标Android API级别 (最低16)
- **输出类型**: shared (动态库) 或 static (静态库)
- **目标架构**: 支持的CPU架构

### 编解码器配置

- **解码器**: 支持的视频/音频解码器
- **编码器**: 支持的视频/音频编码器
- **复用器**: 支持的容器格式输出
- **解复用器**: 支持的容器格式输入

### 网络协议

支持配置各种网络协议，如HTTP、HTTPS、RTMP、HLS等

### 优化选项

- **禁用汇编**: 禁用汇编优化以提高兼容性
- **启用PIC**: 启用位置无关代码
- **禁用调试**: 移除调试信息减小体积
- **启用小体积**: 优化编译以减小最终库大小

## 🛠️ 开发说明

### 核心模块

- **ConfigManager**: 配置管理，支持预设和自定义配置
- **EnvironmentManager**: 环境检查和设置
- **BuildManager**: 编译流程管理
- **CompilerManager**: 编译器调用和参数生成

### Web界面

基于Flask构建的Web界面，提供：
- 图形化配置界面
- 预设配置选择
- 实时编译状态
- 日志查看功能

### 命令行界面

提供完整的命令行操作支持：
- 交互式配置
- 批处理模式
- 配置文件支持

## 📝 使用示例

### Web界面配置

1. 启动Web界面: `python main.py --web`
2. 在浏览器中打开配置页面
3. 选择预设配置或自定义配置
4. 点击"开始编译"按钮
5. 查看实时编译进度和日志

### 命令行配置

```bash
# 使用标准预设
python main.py --preset standard

# 使用自定义配置
python main.py --config custom_config.json

# 清理编译产物
python main.py --clean
```

## 🧹 清理工具

```bash
# 清理所有文件
python clean.py --all

# 仅清理编译输出
python clean.py --build

# 仅清理临时文件
python clean.py --temp

# 仅清理构建缓存
python clean.py --cache
```

## MSYS2 中运行
web 生成脚本后 ``` build_ffmpeg.sh ``` 在msys2中运行


## 📋 常见问题

### Q: 编译失败怎么办？
A: 检查环境配置，确保Android NDK和MSYS2正确安装，查看logs目录下的日志文件。

### Q: 如何添加自定义编解码器？
A: 在Web界面的自定义配置中添加，或修改配置JSON文件。

### Q: 支持哪些Android版本？
A: 支持Android API 16+，推荐使用API 21+。

### Q: 如何减小编译后的库大小？
A: 使用"最小版"预设，或启用"小体积优化"选项。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🔗 相关链接

- [FFmpeg官网](https://ffmpeg.org/)
- [Android NDK文档](https://developer.android.com/ndk)
- [MSYS2官网](https://www.msys2.org/)

---

**注意**: 首次使用前请确保已正确安装和配置所有依赖环境。