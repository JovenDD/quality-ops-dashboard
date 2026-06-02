"""解析全功能评审日报"""
import re
from parsers import strip_html, extract_tables
import fallback_data as fb


def parse(markdown: str) -> dict:
    """解析全功能评审日报markdown"""
    if not markdown:
        return _fallback()

    try:
        # 按日期分割
        date_sections = _split_by_date(markdown)

        all_issues = []
        for date_str, content in date_sections:
            issues = _extract_issues_for_date(content, date_str)
            all_issues.extend(issues)

        return {
            "func_issues": all_issues[:20] if all_issues else fb.FUNC_ISSUES,
            "defect_rate": fb.DEFECT_RATE,
        }
    except Exception as e:
        print(f"全功能评审解析异常: {e}")
        return _fallback()


def _fallback() -> dict:
    return {
        "func_issues": fb.FUNC_ISSUES,
        "defect_rate": fb.DEFECT_RATE,
    }


def _split_by_date(md: str) -> list[tuple[str, str]]:
    """按日期header分割文档"""
    # 匹配 # 2026.5.31 或 # 2026.5.30 格式
    parts = re.split(r'^#\s*(\d{4}\.\d{1,2}\.\d{1,2})', md, flags=re.MULTILINE)

    sections = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            date_str = parts[i]
            # 转换为 M/D 格式
            match = re.match(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', date_str)
            if match:
                date_short = f"{match.group(2)}/{match.group(3)}"
            else:
                date_short = date_str
            sections.append((date_short, parts[i + 1]))

    return sections


def _extract_issues_for_date(content: str, date: str) -> list[dict]:
    """从一个日期的content中提取问题"""
    issues = []
    tables = extract_tables(content)

    for table in tables:
        if len(table) < 2:
            continue

        headers = [strip_html(h).strip() for h in table[0]]

        # 检查是否是问题表格（13列格式）
        if len(headers) < 5:
            continue

        # 查找关键列的索引
        car_idx = _find_column_index(headers, ["车型"])
        factory_idx = _find_column_index(headers, ["工厂"])
        level_idx = _find_column_index(headers, ["问题等级", "等级"])
        desc_idx = _find_column_index(headers, ["问题描述", "问题"])
        status_idx = _find_column_index(headers, ["目前进展", "进展", "状态"])

        if desc_idx is None:
            continue

        for row in table[1:]:
            if len(row) <= desc_idx:
                continue

            desc = strip_html(row[desc_idx]).strip()
            if not desc:
                continue

            issues.append({
                "日期": date,
                "等级": strip_html(row[level_idx]).strip() if level_idx is not None and level_idx < len(row) else "",
                "问题": desc,
                "车型": strip_html(row[car_idx]).strip() if car_idx is not None and car_idx < len(row) else "",
                "工厂": strip_html(row[factory_idx]).strip() if factory_idx is not None and factory_idx < len(row) else "",
                "状态": strip_html(row[status_idx]).strip() if status_idx is not None and status_idx < len(row) else "",
            })

    return issues


def _find_column_index(headers: list, names: list) -> int | None:
    """查找列索引"""
    for name in names:
        for idx, h in enumerate(headers):
            if name in h:
                return idx
    return None
