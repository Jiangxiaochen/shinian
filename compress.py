import os
import shutil

from PIL import Image
from pathlib import Path
import piexif
from tqdm import tqdm  # 进度条支持


def safe_get_exif(img):
    """安全获取EXIF数据"""
    try:
        if 'exif' in img.info:
            return piexif.load(img.info['exif'])
        return None
    except Exception as e:
        print(f"EXIF解析警告: {str(e)}")
        return None


def compress_images(src_folder="images",
                    dest_folder="compressed",
                    quality=85,
                    max_size=(1920, 1920)):
    """
    增强版图片压缩脚本
    改进点：
    - 安全的EXIF处理
    - 进度显示
    - 错误恢复机制
    """
    src_path = Path(src_folder)
    dest_path = src_path.parent / dest_folder
    print("hh")
    dest_path.mkdir(parents=True, exist_ok=True)

    # 获取所有图片文件
    all_files = [f for f in src_path.rglob('*') if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')]
    print(all_files)
    for src_file in tqdm(all_files, desc="处理进度"):
        rel_path = src_file.relative_to(src_path)
        dest_file = dest_path / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src_file) as img:
                # 保留原始模式（避免RGBA转换问题）
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert('RGB')

                # 安全获取EXIF
                exif_dict = safe_get_exif(img)
                orientation = 1

                # 处理方向信息
                if exif_dict and '0th' in exif_dict:
                    orientation = exif_dict['0th'].get(piexif.ImageIFD.Orientation, 1)

                # 根据方向调整图片（不修改原始文件）
                if orientation > 1:
                    img = ImageOps.exif_transpose(img)

                # 调整尺寸
                if max_size:
                    img.thumbnail(max_size, Image.LANCZOS)

                # 保存设置
                save_kwargs = {
                    'quality': quality,
                    'optimize': True,
                    'subsampling': '4:2:0'  # 适合JPEG的色度抽样
                }

                # 保留有效EXIF
                if exif_dict:
                    try:
                        # 清除已处理的Orientation标签
                        exif_dict['0th'][piexif.ImageIFD.Orientation] = 1
                        save_kwargs['exif'] = piexif.dump(exif_dict)
                    except Exception as e:
                        print(f"EXIF保存警告: {src_file} - {str(e)}")

                # 保存文件
                img.save(dest_file,** save_kwargs)

        except Exception as e:
                print(f"\n处理失败: {src_file} - {str(e)}")
                # 复制原始文件作为后备
                shutil.copy(src_file, dest_file)
                continue

if __name__ == "__main__":
# 安装依赖：pip install pillow piexif tqdm
    compress_images(
        quality=85,
        max_size=(1920, 1920)
    )