#!/usr/bin/env python3
"""
手动修复视频文件的工具脚本
用途：处理 rename_movies.py 无法处理的文件

工作流程：
1. Faststart（移动 moov atom 到文件开头）
2. 从 label/cover 文件夹查找已有封面
3. 重新嵌入封面（因为 ffmpeg 会删掉原有封面）

用法: python manual_fix.py "视频文件路径"
"""

import os
import sys
import re
import subprocess

# 封面目录（相对于脚本所在的 rename/ 的上级目录）
COVER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cover')

def extract_code(filename):
    """从文件名提取番号"""
    clean_name = filename.upper()
    
    # FC2 格式
    fc2_match = re.search(r'FC2[-_]?(?:PPV)?[-_]?(\d+)', clean_name)
    if fc2_match:
        return f"FC2-{fc2_match.group(1)}"
    
    # 标准格式: LETTERS-DIGITS
    match = re.search(r'^([A-Z]+)-?0*(\d+)', clean_name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    return None

def find_cover(code):
    """在 cover 文件夹查找匹配的封面"""
    if not os.path.exists(COVER_DIR):
        return None
    
    # 优先精确匹配 CODE
    for filename in os.listdir(COVER_DIR):
        if filename.upper().startswith(code.upper() + ' ') or filename.upper().startswith(code.upper() + '.'):
            return os.path.join(COVER_DIR, filename)
    
    # 模糊匹配
    for filename in os.listdir(COVER_DIR):
        if code.upper() in filename.upper() and filename.lower().endswith('.jpg'):
            return os.path.join(COVER_DIR, filename)
    
    return None

def apply_faststart(mp4_path):
    """应用 faststart (移动 moov atom 到开头)"""
    print("正在应用 faststart...")
    
    directory = os.path.dirname(mp4_path)
    filename = os.path.basename(mp4_path)
    temp_path = os.path.join(directory, f"_temp_{filename}")
    
    cmd = [
        'ffmpeg', '-y', '-i', mp4_path,
        '-c', 'copy',
        '-movflags', '+faststart',
        temp_path
    ]
    
    try:
        # 使用 utf-8 避免编码问题
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
        
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            os.remove(mp4_path)
            os.rename(temp_path, mp4_path)
            print("✓ Faststart 完成!")
            return True
        else:
            print(f"Faststart 失败")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    except FileNotFoundError:
        print("未找到 ffmpeg，请确保已安装并添加到 PATH")
        return False
    except Exception as e:
        print(f"错误: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def embed_cover(mp4_path, cover_path):
    """嵌入封面到 MP4 文件"""
    try:
        from mutagen.mp4 import MP4, MP4Cover
    except ImportError:
        print("缺少 mutagen 库，请运行: pip install mutagen")
        return False
    
    print(f"正在嵌入封面: {os.path.basename(cover_path)}")
    try:
        video = MP4(mp4_path)
        with open(cover_path, 'rb') as f:
            video['covr'] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]
        video.save()
        print("✓ 封面嵌入成功!")
        return True
    except Exception as e:
        print(f"嵌入失败: {e}")
        return False

def process_file(mp4_path, progress_callback=None):
    """处理单个文件：faststart + 重新嵌入封面"""
    filename = os.path.basename(mp4_path)
    code = extract_code(filename)
    
    print(f"\n{'='*50}")
    print(f"文件: {filename}")
    
    if not code:
        code = input("无法自动提取番号，请手动输入: ").strip().upper()
    else:
        print(f"番号: {code}")
    
    # 1. 查找封面
    if progress_callback: progress_callback(20, "Looking for cover...")
    cover_path = find_cover(code)
    if not cover_path:
        print(f"⚠ 未找到 {code} 的封面，跳过处理")
        # 显示可能相关的封面
        prefix = code.split('-')[0] if '-' in code else code[:4]
        related = [f for f in os.listdir(COVER_DIR) if prefix in f.upper()][:5]
        if related:
            print(f"  相关封面: {related}")
        return False
    
    print(f"找到封面: {os.path.basename(cover_path)}")
    
    # 2. Faststart
    if progress_callback: progress_callback(60, "Running Faststart...")
    if not apply_faststart(mp4_path):
        return False
    
    # 3. 重新嵌入封面
    if progress_callback: progress_callback(90, "Embedding cover...")
    if not embed_cover(mp4_path, cover_path):
        return False
    
    print("✓ 处理完成!")
    if progress_callback: progress_callback(100, "Done.")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python manual_fix.py <视频文件路径>")
        print("\n功能: Faststart + 重新嵌入封面")
        print("  - 从 label/cover 文件夹查找已有封面")
        print("  - 运行 ffmpeg faststart")
        print("  - 重新嵌入封面")
        sys.exit(1)
    
    mp4_path = sys.argv[1]
    
    if not os.path.exists(mp4_path):
        print(f"文件不存在: {mp4_path}")
        sys.exit(1)
    
    if not mp4_path.lower().endswith('.mp4'):
        print("只支持 MP4 文件")
        sys.exit(1)
    
    process_file(mp4_path)

if __name__ == '__main__':
    main()
