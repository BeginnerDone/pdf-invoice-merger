# PDF发票合并工具

将指定文件夹内文件名相同的PDF发票和发票查验图片合并成一个A4大小、上下铺布局的PDF文件。

## 功能特点

- 🔍 **智能匹配**: 自动匹配相同文件名的PDF和图片
- 📄 **A4布局**: 上半部分显示PDF发票，下半部分显示查验图片
- 🖼️ **多格式支持**: 支持PNG、JPG、JPEG、BMP、TIFF、GIF等图片格式
- ⚙️ **可配置**: 通过config.json自定义输入输出文件夹
- 📦 **批量处理**: 一次处理多个文件对

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 准备文件

将PDF发票和对应的查验图片放入 `input` 文件夹，确保文件名相同（扩展名可以不同）：

```
input/
├── 发票001.pdf
├── 发票001.png
├── 发票002.pdf
└── 发票002.jpg
```

### 2. 运行程序

```bash
python pdf_merger.py
```

### 3. 查看结果

合并后的PDF文件将保存在 `output` 文件夹中：

```
output/
├── 发票001_merged.pdf
└── 发票002_merged.pdf
```

## 配置说明

编辑 `config.json` 文件可以自定义设置：

```json
{
  "input_folder": "input",     // 输入文件夹路径
  "output_folder": "output"    // 输出文件夹路径
}
```

## 项目结构

```
pdf-invoice-merger/
├── pdf_merger.py      # 主程序文件
├── config.json        # 配置文件
├── requirements.txt   # 依赖包列表
├── README.md         # 说明文档
├── input/            # 输入文件夹
└── output/           # 输出文件夹
```

## 注意事项

- 确保PDF文件和图片文件的文件名完全相同（不包括扩展名）
- 程序会自动创建输出文件夹
- 支持中文文件名
- 如果PDF有多页，只会使用第一页

## 错误处理

程序会自动处理以下情况：
- 配置文件不存在或格式错误时使用默认配置
- 跳过无法处理的文件并继续处理其他文件
- 显示详细的处理进度和错误信息