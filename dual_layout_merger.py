#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双拼PDF合并工具
将input文件夹中的所有文件（PDF和图片）合并成一个PDF，每页A4纸上放置两个文件
"""

import os
import json
import math
from pathlib import Path
from datetime import datetime
from PIL import Image
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io


class DualLayoutMerger:
    """双拼布局PDF合并器"""
    
    def __init__(self, config_path="config.json"):
        """
        初始化双拼合并器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.input_folder = Path(self.config.get("input_folder", "input"))
        self.output_folder = Path(self.config.get("output_folder", "output"))
        
        # 支持的文件格式
        self.supported_image_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
        self.supported_pdf_format = '.pdf'
        
        # A4纸张设置（单位：点，1英寸=72点）
        self.page_width, self.page_height = A4  # 595.2 x 841.9 点
        self.margin = 20  # 页边距
        self.gap = 10     # 两个文件之间的间隙
        
        # 计算每个文件的可用区域（上下排列）
        self.cell_width = self.page_width - 2 * self.margin
        self.cell_height = (self.page_height - 2 * self.margin - self.gap) / 2
        
        # 确保输出文件夹存在
        self.output_folder.mkdir(exist_ok=True)
        
        print(f"📄 双拼PDF合并器初始化完成")
        print(f"📁 输入文件夹: {self.input_folder}")
        print(f"📁 输出文件夹: {self.output_folder}")
        print(f"📐 A4页面尺寸: {self.page_width:.1f} x {self.page_height:.1f} 点")
        print(f"📐 单个文件区域: {self.cell_width:.1f} x {self.cell_height:.1f} 点")
    
    def load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ 配置文件 {config_path} 不存在，使用默认配置")
            return {"input_folder": "input", "output_folder": "output"}
        except json.JSONDecodeError:
            print(f"⚠️ 配置文件 {config_path} 格式错误，使用默认配置")
            return {"input_folder": "input", "output_folder": "output"}
    
    def get_all_files(self):
        """获取input文件夹中的所有支持的文件"""
        if not self.input_folder.exists():
            print(f"❌ 输入文件夹 {self.input_folder} 不存在")
            return []
        
        all_files = []
        
        # 扫描所有文件
        for file_path in self.input_folder.iterdir():
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                if file_ext in self.supported_image_formats or file_ext == self.supported_pdf_format:
                    all_files.append(file_path)
        
        # 按文件名排序，确保输出顺序一致
        all_files.sort(key=lambda x: x.name.lower())
        
        print(f"📋 找到 {len(all_files)} 个支持的文件:")
        for i, file_path in enumerate(all_files, 1):
            file_type = "PDF" if file_path.suffix.lower() == '.pdf' else "图片"
            print(f"   {i:2d}. {file_path.name} ({file_type})")
        
        return all_files
    
    def pdf_to_image(self, pdf_path, page_num=0, dpi=150):
        """
        将PDF页面转换为PIL图片
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页面编号（默认第一页）
            dpi: 转换分辨率
            
        Returns:
            PIL.Image对象
        """
        try:
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                page_num = 0  # 如果页面不存在，使用第一页
            
            page = doc[page_num]
            # 计算缩放因子
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 转换为PIL图片
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            doc.close()
            return img
        except Exception as e:
            print(f"❌ 转换PDF {pdf_path.name} 时出错: {e}")
            return None
    
    def load_image(self, image_path):
        """
        加载图片文件
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            PIL.Image对象
        """
        try:
            img = Image.open(image_path)
            # 转换为RGB模式（确保兼容性）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
        except Exception as e:
            print(f"❌ 加载图片 {image_path.name} 时出错: {e}")
            return None
    
    def resize_image_to_fit(self, img, max_width, max_height, maintain_aspect=True):
        """
        调整图片大小以适应指定区域
        
        Args:
            img: PIL图片对象
            max_width: 最大宽度
            max_height: 最大高度
            maintain_aspect: 是否保持宽高比
            
        Returns:
            调整后的PIL图片对象
        """
        if not img:
            return None
        
        original_width, original_height = img.size
        
        if maintain_aspect:
            # 计算缩放比例，保持宽高比
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = min(width_ratio, height_ratio)
            
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
        else:
            new_width = int(max_width)
            new_height = int(max_height)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def process_file_to_image(self, file_path):
        """
        处理文件（PDF或图片）并转换为适合的图片
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理后的PIL图片对象
        """
        file_ext = file_path.suffix.lower()
        
        if file_ext == self.supported_pdf_format:
            # 处理PDF文件
            img = self.pdf_to_image(file_path)
        else:
            # 处理图片文件
            img = self.load_image(file_path)
        
        if img:
            # 调整图片大小以适应单元格
            img = self.resize_image_to_fit(img, self.cell_width, self.cell_height)
        
        return img
    
    def create_dual_layout_pdf(self, all_files, output_path):
        """
        创建双拼布局的PDF文件
        
        Args:
            all_files: 所有文件路径列表
            output_path: 输出PDF路径
        """
        if not all_files:
            print("❌ 没有找到可处理的文件")
            return
        
        print(f"\n🔄 开始创建双拼PDF: {output_path.name}")
        
        # 创建PDF画布
        c = canvas.Canvas(str(output_path), pagesize=A4)
        
        # 计算需要的页数
        total_pages = math.ceil(len(all_files) / 2)
        print(f"📄 总共需要 {total_pages} 页，处理 {len(all_files)} 个文件")
        
        for page_num in range(total_pages):
            print(f"📝 正在处理第 {page_num + 1}/{total_pages} 页...")
            
            # 获取当前页的两个文件
            file_index_1 = page_num * 2
            file_index_2 = page_num * 2 + 1
            
            # 处理上方文件
            if file_index_1 < len(all_files):
                file_path_1 = all_files[file_index_1]
                print(f"   📄 上方: {file_path_1.name}")
                img_1 = self.process_file_to_image(file_path_1)
                
                if img_1:
                    # 计算上方位置（居中对齐）
                    img_width_1, img_height_1 = img_1.size
                    x_1 = self.margin + (self.cell_width - img_width_1) / 2
                    y_1 = self.margin + self.cell_height + self.gap + (self.cell_height - img_height_1) / 2
                    
                    # 将PIL图片转换为ReportLab可用的格式
                    img_buffer_1 = io.BytesIO()
                    img_1.save(img_buffer_1, format='PNG')
                    img_buffer_1.seek(0)
                    
                    # 在PDF中绘制图片
                    c.drawImage(ImageReader(img_buffer_1), x_1, y_1, 
                              width=img_width_1, height=img_height_1)
                    
                    # 添加文件名标签
                    c.setFont("Helvetica", 8)
                    c.drawString(self.margin, self.page_height - self.margin + 5, file_path_1.name)
            
            # 处理下方文件
            if file_index_2 < len(all_files):
                file_path_2 = all_files[file_index_2]
                print(f"   📄 下方: {file_path_2.name}")
                img_2 = self.process_file_to_image(file_path_2)
                
                if img_2:
                    # 计算下方位置（居中对齐）
                    img_width_2, img_height_2 = img_2.size
                    x_2 = self.margin + (self.cell_width - img_width_2) / 2
                    y_2 = self.margin + (self.cell_height - img_height_2) / 2
                    
                    # 将PIL图片转换为ReportLab可用的格式
                    img_buffer_2 = io.BytesIO()
                    img_2.save(img_buffer_2, format='PNG')
                    img_buffer_2.seek(0)
                    
                    # 在PDF中绘制图片
                    c.drawImage(ImageReader(img_buffer_2), x_2, y_2, 
                              width=img_width_2, height=img_height_2)
                    
                    # 添加文件名标签
                    c.setFont("Helvetica", 8)
                    c.drawString(self.margin, self.margin - 15, file_path_2.name)
            
            # 绘制分隔线（可选）
            c.setStrokeColorRGB(0.8, 0.8, 0.8)  # 浅灰色
            c.setLineWidth(1)
            center_y = self.margin + self.cell_height + self.gap / 2
            c.line(self.margin, center_y, self.page_width - self.margin, center_y)
            
            # 如果不是最后一页，创建新页面
            if page_num < total_pages - 1:
                c.showPage()
        
        # 保存PDF
        c.save()
        print(f"✅ 双拼PDF创建完成: {output_path}")
    
    def process_all_files(self):
        """处理所有文件并创建双拼PDF"""
        print("\n🚀 开始双拼PDF合并处理...")
        
        # 获取所有文件
        all_files = self.get_all_files()
        
        if not all_files:
            print("❌ 没有找到可处理的文件")
            return
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"dual_layout_merged_{timestamp}.pdf"
        output_path = self.output_folder / output_filename
        
        # 创建双拼PDF
        self.create_dual_layout_pdf(all_files, output_path)
        
        print(f"\n🎉 处理完成！")
        print(f"📊 统计信息:")
        print(f"   📁 处理文件数: {len(all_files)}")
        print(f"   📄 生成页数: {math.ceil(len(all_files) / 2)}")
        print(f"   💾 输出文件: {output_path}")


def main():
    """主函数"""
    print("🔧 双拼PDF合并工具")
    print("=" * 50)
    
    try:
        merger = DualLayoutMerger()
        merger.process_all_files()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()