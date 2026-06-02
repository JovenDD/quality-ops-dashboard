"""解析整车质量日报"""
import re
from parsers import strip_html, extract_tables
import fallback_data as fb


def parse(markdown: str) -> dict:
    """解析整车质量日报markdown"""
    if not markdown:
        return _fallback()

    try:
        issues = _extract_issues(markdown)
        return {
            "quality_issues": issues if issues else fb.QUALITY_ISSUES,
            "ftt": fb.FTT,
            "dpu_whole": fb.DPU_WHOLE,
        }
    except Exception as e:
        print(f"整车质量解析异常: {e}")
        return _fallback()


def _fallback() -> dict:
    return {
        "quality_issues": fb.QUALITY_ISSUES,
        "ftt": fb.FTT,
        "dpu_whole": fb.DPU_WHOLE,
    }


def _extract_issues(md: str) -> list[dict]:
    """提取重点升级问题"""
    issues = []

    # 提取文档日期
    doc_date = _extract_doc_date(md)

    # 查找重点升级问题section
    section_match = re.search(r'重点升级问题(.*?)(?=#{2,}|\Z)', md, re.DOTALL | re.IGNORECASE)
    if not section_match:
        # 尝试从整个文档提取
        section_content = md
    else:
        section_content = section_match.group(1)

    tables = extract_tables(section_content)

    for table in tables:
        if len(table) < 2:
            continue

        headers = [strip_html(h).strip() for h in table[0]]

        # 检查是否是问题表格
        if not any('问题' in h for h in headers):
            continue

        # 查找列索引
        desc_idx = _find_column_index(headers, ["问题描述", "问题"])
        measure_idx = _find_column_index(headers, ["整改措施", "措施"])
        dept_idx = _find_column_index(headers, ["责任人/部门", "责任部门", "部门"])
        progress_idx = _find_column_index(headers, ["最新进展", "进展"])

        if desc_idx is None:
            continue

        for row in table[1:]:
            if len(row) <= desc_idx:
                continue

            desc = strip_html(row[desc_idx]).strip()
            if not desc:
                continue

            # 提取缺陷数（可能在问题描述中）
            defect_count = ""
            count_match = re.search(r'缺陷数[：:]\s*(\d+)', desc)
            if count_match:
                defect_count = count_match.group(1)
                desc = desc[:count_match.start()].strip()

            issues.append({
                "日期": doc_date,
                "问题": desc,
                "缺陷数": defect_count,
                "升级原因": "",  # 这个文档没有升级原因列
                "责任部门": strip_html(row[dept_idx]).strip() if dept_idx is not None and dept_idx < len(row) else "",
            })

    return issues[:20]


def _extract_doc_date(md: str) -> str:
    """从文档中提取日期"""
    # 匹配 "截至5-29日" 或 "截至5/29" 等格式
    match = re.search(r'截至\s*(\d{1,2})[-/月](\d{1,2})', md)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    # 匹配 "# 5/29" 格式
    match = re.search(r'#\s*(\d{1,2})/(\d{1,2})', md)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    # 匹配 "2026/5/29" 格式
    match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', md)
    if match:
        return f"{match.group(2)}/{match.group(3)}"

    return ""


def _find_column_index(headers: list, names: list) -> int | None:
    """查找列索引"""
    for name in names:
        for idx, h in enumerate(headers):
            if name in h:
                return idx
    return None
