#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF工具集合 - 统一入口
包含PDF合并、数据提取、转图片合并等功能
"""

import sys
import os
from pathlib import Path


def show_menu():
    """显示功能菜单"""
    print("\n" + "="*50)
    print("🔧 PDF工具集合")
    print("="*50)
    print("1. PDF发票合并 - 将PDF发票和查验图片合并成一个PDF")
    print("2. PDF转图片合并 - 将多个PDF转换为图片并排列合并")
    print("3. 双拼PDF合并 - 将所有文件合并成一个PDF，每页放两个文件")
    print("0. 退出程序")
    print("="*50)


def run_pdf_merger():
    """运行PDF发票合并功能"""
    try:
        from pdf_merger import main as pdf_merger_main
        print("\n📄 启动PDF发票合并功能...")
        print("💡 将相同文件名的PDF发票和查验图片合并成A4布局的PDF文件")
        pdf_merger_main()
    except ImportError:
        print("❌ 错误：找不到pdf_merger模块")
    except Exception as e:
        print(f"❌ 运行PDF发票合并功能时出错：{e}")



def run_pdf_to_image_merger():
    """运行PDF转图片合并功能"""
    try:
        from pdf_to_image_merger import main as image_merger_main
        print("\n🖼️ 启动PDF转图片合并功能...")
        print("💡 将多个PDF文件转换为图片并按网格排列合并成一张大图")
        image_merger_main()
    except ImportError:
        print("❌ 错误：找不到pdf_to_image_merger模块")
        print("💡 提示：请确保已安装pdf2image和Pillow库")
        print("   运行命令：pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ 运行PDF转图片合并功能时出错：{e}")


def run_dual_layout_merger():
    """运行双拼PDF合并功能"""
    try:
        print("\n🔄 启动双拼PDF合并功能...")
        
        # 导入双拼合并器
        from dual_layout_merger import DualLayoutMerger
        
        # 创建合并器实例并运行
        merger = DualLayoutMerger()
        merger.process_all_files()
        
        print("✅ 双拼PDF合并完成！")
        
    except ImportError as e:
        print(f"❌ 导入双拼合并模块失败：{e}")
    except Exception as e:
        print(f"❌ 运行双拼PDF合并功能时出错：{e}")


def main():
    """主函数"""
    print("欢迎使用PDF工具集合！")
    
    while True:
        show_menu()
        
        try:
            choice = input("\n请选择功能 (0-3): ").strip()
            
            if choice == "0":
                print("\n👋 感谢使用，再见！")
                break
            elif choice == "1":
                run_pdf_merger()
            elif choice == "2":
                run_pdf_to_image_merger()
            elif choice == "3":
                run_dual_layout_merger()
            else:
                print("❌ 无效选择，请输入0-3之间的数字")
                
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 程序运行出错：{e}")
        
        # 询问是否继续
        if choice in ["1", "2", "3"]:
            try:
                continue_choice = input("\n是否继续使用其他功能？(y/n): ").lower().strip()
                if continue_choice not in ['y', 'yes', '是']:
                    print("\n👋 感谢使用，再见！")
                    break
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断，再见！")
                break


if __name__ == "__main__":
    main()