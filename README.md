# 文档信息提取

## 更新日志
## 2025-8-04
- 实现了文本相似度识别的基础内容（未包含找出重复字段）
- 强烈建议对要处理的文件名中手动添加 招标/投标， 以保证识别正确

### 2025-07-25
- 因为效果不佳，删除了复杂内容字段提取逻辑

### 2025-07-16
- 增加了一些依赖，需要安装
- 优化了PDF信息提取逻辑，确保所有schema字段都被写入结果
- 增强了复杂内容字段（如质量保证方案）的提取能力, 现在会把包含相关关键词的文本整合在一起返回，
- 删除info_extract.py 将其整合到pdf_info_extract中，简化main.py逻辑
- 导出数据库信息时将会根据文件类型，分别输出到excel文件



## 快速开始

0. 安装相关依赖
1. 将要处理的 PDF 文件放到该项目 `pdfs` 文件夹中
2. 把poppler.zip解压到当前文件夹，具体形式如项目结构所示（这个做法后面也应该要改，现在将就用）
3. 安装Tesseract，这个效果一般，先将就着用（见末尾详细说明）
4. 运行 `python main.py` 开始处理
5. 后续使用处理的信息，要自己写，我只写到了把pdf读到mongodb里面，和导出到csv的逻辑

## 📁 项目结构

```
大创2024/
├── main.py                # 🚀 主程序入口
├── config.py              # ⚙️ 配置文件，数据库连接、工具路径设置
├── pdf_reader.py          # 📖 PDF文本提取
├── info_extractor.py      # 🔍 信息提取，使用NLP+正则表达式提取schema
├── db_manager.py          # 💾 数据库管理，MongoDB数据的增删改查
├── utils.py               # 🛠️ 工具函数，文本清理、金额提取、日期识别
├── pdfs/                  # 📂 存放待处理的PDF文件
├── poppler/               # 🖼️ PDF转图片工具
└── requirements.txt       # 📋 Python依赖包列表
```

## 🧩 模块功能说明

### 1. main.py - 主程序
- 自动判断文件类型（招标文件/投标文件）
- 数据验证和完整性检查
- 处理进度统计和错误处理
- 导出CSV结果

### 2. config.py - 配置管理
- 数据库连接配置（MongoDB）
- 自动检测Tesseract(这之前需要手动安装)和Poppler路径(poppler现在用的是解压压缩包的简陋办法)

### 3. pdf_reader.py - PDF文本提取
**功能**：PDF文本提取
```
PDF 文件
    ↓
pdfplumber 尝试提取文字
    ↓
如果提取失败（扫描件）
    ↓
poppler 将 PDF 页面转为图片 
    ↓
tesseract 对图片进行 OCR
    ↓
获得文字内容
```

### 4. info_extractor.py - schema信息提取
**功能**：从文本中提取结构化信息
**提取逻辑**：使用PaddleNLP进行智能实体识别（就是特征提取，比如招标公司，招标地址等等这种），传统正则匹配作为补充辅助
**增添schema**：如果要增添提取的schema，可以修改BIDDING_SCHEMA和TENDER_SCHEMA

### 5. db_manager.py - 数据库管理
**功能**：MongoDB数据操作的封装，用于数据库信息交互，（要读数据的话也可以调用这里面的函数）

### 6. similarity_detect.py - 检测文档相似度
**整体框架** 
similarity_detect.py
├── 【导入模块】
├── 【相似度算法函数】 (9个)
├── 【核心检测类】
└── 【报告生成函数】
    ├── 执行全文档相似度检测
    ├── 执行投标文件抄袭检测
    └── 生成最终报告导出为txt文档

通过9个办法加权计算相似度分数

### 7. utils.py - 工具函数库


## 🔧 依赖工具安装

### Tesseract OCR 安装

#### Windows 用户

**1. 下载 Tesseract**
- 官方下载地址：https://github.com/UB-Mannheim/tesseract/wiki
- 直接下载链接：https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe

**2. 安装步骤**
```
1. 双击下载的 .exe 文件
2. 选择安装路径（系统会自动检测以下路径）：
   - "C:\Program Files\Tesseract-OCR\tesseract.exe"
   - "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
   - "D:\Tesseract-OCR\tesseract.exe"
3. ⚠️ 重要：勾选 "Additional script data" 和 "Additional language data"中 CHINESE相关选项
4. 完成安装
```

**注意**：确保安装了支持中文的Tesseract，否则扫描型PDF无法正确识别中文内容。

