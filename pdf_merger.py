#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF发票合并工具
将指定文件夹内文件名相同的PDF发票和发票查验图片合并成一个A4大小、上下铺布局的PDF文件
"""

import os
import json
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io

class PDFInvoiceMerger:
    def __init__(self, config_path="config.json"):
        """初始化PDF合并器"""
        self.config = self.load_config(config_path)
        self.input_folder = Path(self.config.get("input_folder", "input"))
        self.output_folder = Path(self.config.get("output_folder", "output"))
        self.supported_image_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
        
        # 确保输出文件夹存在
        self.output_folder.mkdir(exist_ok=True)
    
    def load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_path} 不存在，使用默认配置")
            return {"input_folder": "input", "output_folder": "output"}
        except json.JSONDecodeError:
            print(f"配置文件 {config_path} 格式错误，使用默认配置")
            return {"input_folder": "input", "output_folder": "output"}
    
    def get_file_pairs(self):
        """获取文件名相同的PDF和图片文件对"""
        if not self.input_folder.exists():
            print(f"输入文件夹 {self.input_folder} 不存在")
            return []
        
        pdf_files = {}
        image_files = {}
        
        # 扫描所有文件
        for file_path in self.input_folder.iterdir():
            if file_path.is_file():
                name_without_ext = file_path.stem
                
                if file_path.suffix.lower() == '.pdf':
                    pdf_files[name_without_ext] = file_path
                elif file_path.suffix.lower() in self.supported_image_formats:
                    image_files[name_without_ext] = file_path
        
        # 找到匹配的文件对
        pairs = []
        for name in pdf_files:
            if name in image_files:
                pairs.append((pdf_files[name], image_files[name]))
                print(f"找到匹配文件对: {name}")
        
        if not pairs:
            print("未找到匹配的PDF和图片文件对")
        
        return pairs
    
    def pdf_to_image(self, pdf_path):
        """将PDF转换为图片"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]  # 取第一页
            
            # 设置缩放比例以获得高质量图片
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 转换为PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            doc.close()
            return img
        except Exception as e:
            print(f"PDF转换失败 {pdf_path}: {e}")
            return None
    
    def resize_image_to_fit(self, img, max_width, max_height):
        """调整图片大小以适应指定区域，保持宽高比"""
        img_width, img_height = img.size
        
        # 计算缩放比例
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale = min(width_ratio, height_ratio)
        
        # 计算新尺寸
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def merge_pdf_and_image(self, pdf_path, image_path, output_path):
        """合并PDF和图片到A4页面"""
        try:
            # A4尺寸 (595.27 x 841.89 points)
            page_width, page_height = A4
            
            # 创建新的PDF
            c = canvas.Canvas(str(output_path), pagesize=A4)
            
            # 上半部分放PDF，下半部分放图片
            half_height = page_height / 2
            margin = 20  # 边距
            
            # 处理PDF
            pdf_img = self.pdf_to_image(pdf_path)
            if pdf_img:
                # 调整PDF图片大小适应上半部分
                pdf_resized = self.resize_image_to_fit(
                    pdf_img, 
                    page_width - 2 * margin, 
                    half_height - margin
                )
                
                # 计算PDF图片位置（居中）
                pdf_x = (page_width - pdf_resized.width) / 2
                pdf_y = half_height + (half_height - pdf_resized.height) / 2
                
                # 将PIL图片转换为ReportLab可用的格式
                pdf_buffer = io.BytesIO()
                pdf_img.save(pdf_buffer, format='PNG')
                pdf_buffer.seek(0)
                pdf_reader = ImageReader(pdf_buffer)
                
                c.drawImage(pdf_reader, pdf_x, pdf_y, 
                           width=pdf_resized.width, height=pdf_resized.height)
            
            # 处理查验图片
            verify_img = Image.open(image_path)
            verify_resized = self.resize_image_to_fit(
                verify_img, 
                page_width - 2 * margin, 
                half_height - margin
            )
            
            # 计算查验图片位置（居中）
            verify_x = (page_width - verify_resized.width) / 2
            verify_y = (half_height - verify_resized.height) / 2
            
            # 将PIL图片转换为ReportLab可用的格式
            verify_buffer = io.BytesIO()
            verify_img.save(verify_buffer, format='PNG')
            verify_buffer.seek(0)
            verify_reader = ImageReader(verify_buffer)
            
            c.drawImage(verify_reader, verify_x, verify_y, 
                       width=verify_resized.width, height=verify_resized.height)
            
            # 添加分割线
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.setLineWidth(1)
            c.line(margin, half_height, page_width - margin, half_height)
            
            # 添加标签
            c.setFont("Helvetica", 12)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawString(margin, page_height - 15, "发票原件")
            c.drawString(margin, half_height - 15, "查验结果")
            
            c.save()
            print(f"合并完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"合并失败 {pdf_path} + {image_path}: {e}")
            return False
    
    def process_all(self):
        """处理所有匹配的文件对"""
        pairs = self.get_file_pairs()
        
        if not pairs:
            print("没有找到需要处理的文件")
            return
        
        success_count = 0
        total_count = len(pairs)
        
        print(f"开始处理 {total_count} 个文件对...")
        
        for pdf_path, image_path in pairs:
            output_filename = f"{pdf_path.stem}_merged.pdf"
            output_path = self.output_folder / output_filename
            
            if self.merge_pdf_and_image(pdf_path, image_path, output_path):
                success_count += 1
        
        print(f"\n处理完成！成功: {success_count}/{total_count}")
        print(f"输出文件夹: {self.output_folder.absolute()}")

def main():
    """主函数"""
    print("PDF发票合并工具")
    print("=" * 30)
    
    merger = PDFInvoiceMerger()
    merger.process_all()

if __name__ == "__main__":
    main()