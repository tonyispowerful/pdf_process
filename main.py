from pdf_info_extract import process_pdfs

if __name__ == "__main__":
    process_pdfs()
    # 处理完成后，可以在数据库中查看提取结果, 也可以导出为 Excel 文件
    from db_manager import export_to_excel
    export_to_excel("标书数据.xlsx")

