"""
工具函数模块
"""

import subprocess
import sys
from typing import Optional, Union, List


def get_safe_encoding() -> str:
    """获取安全的编码格式"""
    try:
        "测试".encode('utf-8').decode('utf-8')
        return 'utf-8'
    except (UnicodeEncodeError, UnicodeDecodeError):
        return sys.getdefaultencoding()


def safe_decode(data: bytes, encoding: Optional[str] = None) -> str:
    """安全解码字节数据"""
    if encoding is None:
        encoding = get_safe_encoding()
    
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        encodings = ['utf-8', 'gbk', 'cp936', 'latin1']
        for enc in encodings:
            if enc != encoding:
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    continue
        
        return data.decode(encoding, errors='replace')


def run_command_safe(cmd: Union[str, List[str]], **kwargs) -> subprocess.CompletedProcess:
    """安全执行命令"""
    safe_kwargs = {
        'capture_output': True,
        'text': True,
        'encoding': get_safe_encoding(),
        'errors': 'replace'
    }
    safe_kwargs.update(kwargs)
    
    try:
        return subprocess.run(cmd, **safe_kwargs)
    except Exception as e:
        if safe_kwargs.get('encoding') == 'utf-8':
            safe_kwargs['encoding'] = sys.getdefaultencoding()
            return subprocess.run(cmd, **safe_kwargs)
        else:
            raise e


def create_safe_popen(cmd: Union[str, List[str]], **kwargs) -> subprocess.Popen:
    """创建安全的Popen对象"""
    safe_kwargs = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.STDOUT,
        'text': True,
        'encoding': get_safe_encoding(),
        'errors': 'replace',
        'bufsize': 1
    }
    safe_kwargs.update(kwargs)
    
    return subprocess.Popen(cmd, **safe_kwargs)


def safe_readline(process: subprocess.Popen) -> Optional[str]:
    """安全读取进程输出行"""
    try:
        line = process.stdout.readline()
        return line if line else None
    except UnicodeDecodeError:
        return "⚠️ [编码错误 - 无法显示此行]\n"


def clean_output_line(line: str) -> str:
    """清理输出行"""
    if not line:
        return line
    
    cleaned = ''.join(char for char in line if char.isprintable() or char in '\n\t\r')
    return cleaned.strip()