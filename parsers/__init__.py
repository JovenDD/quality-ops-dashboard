"""通用解析工具函数"""
import re
import sys
import os

# 将项目根目录加入path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def strip_html(text: str) -> str:
    """去除所有HTML标签，保留纯文本"""
    if not text:
        return ""
    text = re.sub(r'<cite[^>]*>.*?</cite>', '', text, flags=re.DOTALL)
    text = re.sub(r'<img[^>]*/?>', '', text)
    text = re.sub(r'<figure[^>]*>.*?</figure>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def extract_tables(html_text: str) -> list[list[list[str]]]:
    """从HTML中提取所有表格，返回 [[[cell, ...], ...], ...]"""
    tables = []
    table_pattern = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL)
    row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
    cell_pattern = re.compile(r'<t[dh][^>]*>(.*?)</t[dh]>', re.DOTALL)

    for table_match in table_pattern.finditer(html_text):
        rows = []
        for row_match in row_pattern.finditer(table_match.group(1)):
            cells = [strip_html(c.group(1)) for c in cell_pattern.finditer(row_match.group(1))]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables

def extract_table_as_dicts(html_text: str, header_row_idx: int = 0) -> list[dict]:
    """提取第一个表格并转为dict列表（第一行作为表头）"""
    tables = extract_tables(html_text)
    if not tables:
        return []
    table = tables[0]
    if len(table) < 2:
        return []
    headers = table[header_row_idx]
    return [dict(zip(headers, row)) for row in table[header_row_idx + 1:]]
