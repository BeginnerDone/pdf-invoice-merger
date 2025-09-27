#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转图片合并工具
将多个PDF文件转换为图片并合并成一张大图
"""

import os
import io
import math
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import tempfile
import shutil


class PDFToImageMerger:
    """PDF转图片合并器"""
    
    def __init__(self, input_folder="input", output_folder="output"):
        """
        初始化PDF转图片合并器
        
        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        
        # 确保输出文件夹存在
        self.output_folder.mkdir(exist_ok=True)
        
        # 图片设置
        self.dpi = 200  # PDF转图片的DPI
        self.margin = 20  # 图片间距
        self.background_color = (255, 255, 255)  # 背景色（白色）
        self.border_color = (200, 200, 200)  # 边框色（浅灰色）
        self.border_width = 2  # 边框宽度
    
    def convert_pdf_to_images(self, pdf_path):
        """
        将PDF文件转换为图片列表
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            list: PIL Image对象列表
        """
        try:
            print(f"正在转换PDF: {pdf_path.name}")
            
            # 使用PyMuPDF打开PDF
            pdf_document = fitz.open(str(pdf_path))
            images = []
            
            # 计算缩放因子（基于DPI）
            zoom = self.dpi / 72.0  # 72是PDF的默认DPI
            mat = fitz.Matrix(zoom, zoom)
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # 将页面渲染为图片
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为PIL Image
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            
            pdf_document.close()
            print(f"  转换完成，共 {len(images)} 页")
            return images
            
        except Exception as e:
            print(f"转换PDF失败 {pdf_path.name}: {e}")
            return []
    
    def calculate_grid_layout(self, total_images, max_cols=4):
        """
        计算网格布局
        
        Args:
            total_images: 图片总数
            max_cols: 最大列数
            
        Returns:
            tuple: (行数, 列数)
        """
        if total_images <= max_cols:
            return 1, total_images
        
        cols = min(max_cols, total_images)
        rows = math.ceil(total_images / cols)
        return rows, cols
    
    def resize_image_proportionally(self, image, target_width, target_height):
        """
        按比例缩放图片
        
        Args:
            image: PIL Image对象
            target_width: 目标宽度
            target_height: 目标高度
            
        Returns:
            PIL Image: 缩放后的图片
        """
        # 计算缩放比例
        width_ratio = target_width / image.width
        height_ratio = target_height / image.height
        scale_ratio = min(width_ratio, height_ratio)
        
        # 计算新尺寸
        new_width = int(image.width * scale_ratio)
        new_height = int(image.height * scale_ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def add_image_label(self, image, label_text, font_size=24):
        """
        在图片上添加标签
        
        Args:
            image: PIL Image对象
            label_text: 标签文本
            font_size: 字体大小
            
        Returns:
            PIL Image: 添加标签后的图片
        """
        # 创建新图片，高度增加以容纳标签
        label_height = font_size + 20
        new_image = Image.new('RGB', 
                             (image.width, image.height + label_height), 
                             self.background_color)
        
        # 粘贴原图片
        new_image.paste(image, (0, label_height))
        
        # 添加标签
        draw = ImageDraw.Draw(new_image)
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except:
            # 如果找不到字体，使用默认字体
            font = ImageFont.load_default()
        
        # 计算文本位置（居中）
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (image.width - text_width) // 2
        text_y = 10
        
        # 绘制文本
        draw.text((text_x, text_y), label_text, fill=(0, 0, 0), font=font)
        
        return new_image
    
    def merge_images_to_grid(self, all_images, image_labels, output_path, 
                           cell_width=400, cell_height=500, max_cols=4):
        """
        将图片合并成网格布局
        
        Args:
            all_images: 所有图片列表
            image_labels: 图片标签列表
            output_path: 输出文件路径
            cell_width: 单元格宽度
            cell_height: 单元格高度
            max_cols: 最大列数
        """
        if not all_images:
            print("没有图片需要合并")
            return
        
        total_images = len(all_images)
        rows, cols = self.calculate_grid_layout(total_images, max_cols)
        
        print(f"布局: {rows}行 x {cols}列，共 {total_images} 张图片")
        
        # 计算画布尺寸
        canvas_width = cols * (cell_width + self.margin) + self.margin
        canvas_height = rows * (cell_height + self.margin) + self.margin
        
        # 创建画布
        canvas = Image.new('RGB', (canvas_width, canvas_height), self.background_color)
        
        # 放置图片
        for i, (image, label) in enumerate(zip(all_images, image_labels)):
            row = i // cols
            col = i % cols
            
            # 计算位置
            x = col * (cell_width + self.margin) + self.margin
            y = row * (cell_height + self.margin) + self.margin
            
            # 缩放图片
            resized_image = self.resize_image_proportionally(
                image, 
                cell_width - self.border_width * 2, 
                cell_height - self.border_width * 2 - 50  # 为标签留空间
            )
            
            # 添加标签
            labeled_image = self.add_image_label(resized_image, label)
            
            # 创建带边框的图片
            cell_image = Image.new('RGB', (cell_width, cell_height), self.border_color)
            
            # 计算居中位置
            paste_x = (cell_width - labeled_image.width) // 2
            paste_y = (cell_height - labeled_image.height) // 2
            
            # 粘贴图片到单元格
            cell_image.paste(labeled_image, (paste_x, paste_y))
            
            # 粘贴单元格到画布
            canvas.paste(cell_image, (x, y))
        
        # 保存合并后的图片
        canvas.save(output_path, 'PNG', quality=95)
        print(f"合并完成！输出文件: {output_path}")
        print(f"图片尺寸: {canvas_width} x {canvas_height} 像素")
    
    def process_pdfs_to_merged_image(self, max_cols=4, cell_width=400, cell_height=500):
        """
        处理所有PDF文件并合并成一张图片
        
        Args:
            max_cols: 最大列数
            cell_width: 单元格宽度
            cell_height: 单元格高度
        """
        if not self.input_folder.exists():
            print(f"输入文件夹不存在: {self.input_folder}")
            return
        
        # 获取所有PDF文件
        pdf_files = list(self.input_folder.glob("*.pdf"))
        if not pdf_files:
            print("未找到PDF文件")
            return
        
        print(f"找到 {len(pdf_files)} 个PDF文件")
        
        all_images = []
        image_labels = []
        
        # 转换所有PDF
        for pdf_file in sorted(pdf_files):
            images = self.convert_pdf_to_images(pdf_file)
            
            for i, image in enumerate(images):
                all_images.append(image)
                # 创建标签：文件名 + 页码
                if len(images) > 1:
                    label = f"{pdf_file.stem} (第{i+1}页)"
                else:
                    label = pdf_file.stem
                image_labels.append(label)
        
        if not all_images:
            print("没有成功转换的图片")
            return
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"merged_pdfs_{timestamp}.png"
        output_path = self.output_folder / output_filename
        
        # 合并图片
        self.merge_images_to_grid(
            all_images, 
            image_labels, 
            output_path,
            cell_width=cell_width,
            cell_height=cell_height,
            max_cols=max_cols
        )
        
        return output_path


def main():
    """主函数"""
    print("PDF转图片合并工具")
    print("=" * 30)
    
    # 获取用户设置
    try:
        max_cols = int(input("请输入每行最大列数 (默认4): ") or "4")
        cell_width = int(input("请输入单元格宽度 (默认400): ") or "400")
        cell_height = int(input("请输入单元格高度 (默认500): ") or "500")
    except ValueError:
        print("输入无效，使用默认设置")
        max_cols, cell_width, cell_height = 4, 400, 500
    
    # 创建合并器并处理
    merger = PDFToImageMerger()
    output_path = merger.process_pdfs_to_merged_image(
        max_cols=max_cols,
        cell_width=cell_width, 
        cell_height=cell_height
    )
    
    if output_path:
        print(f"\n✅ 处理完成！")
        print(f"输出文件: {output_path}")
    else:
        print("\n❌ 处理失败")


if __name__ == "__main__":
    main()