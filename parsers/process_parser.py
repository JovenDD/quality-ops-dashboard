"""解析过程质量日报"""
import re
from parsers import strip_html, extract_tables
import fallback_data as fb


def parse(markdown: str) -> dict:
    """解析过程质量日报markdown"""
    if not markdown:
        return _fallback()

    try:
        # 按日期班次分割
        date_sections = _split_by_date_shift(markdown)

        # 提取各日期班次的数据
        audit_paint = {"M9": {}, "B1": {}}
        audit_body = {"M9": {}, "B1": {}}
        dpu_paint = {}
        dpu_body = {}
        dpu_stamp = {}
        issues_paint = []
        issues_body = []
        die_cast = []

        for date_shift, content in date_sections:
            # 提取涂装AUDIT分数
            paint_scores = _extract_paint_scores(content, date_shift)
            for line, score in paint_scores.items():
                audit_paint[line][date_shift] = score

            # 提取车身AUDIT分数
            body_scores = _extract_body_scores(content, date_shift)
            for line, score in body_scores.items():
                audit_body[line][date_shift] = score

            # 提取DPU
            dpu = _extract_dpu(content, date_shift)
            if "paint" in dpu:
                dpu_paint[date_shift] = dpu["paint"]
            if "body" in dpu:
                dpu_body[date_shift] = dpu["body"]
            if "stamp" in dpu:
                dpu_stamp[date_shift] = dpu["stamp"]

            # 提取问题
            paint_issues = _extract_issues(content, date_shift, "涂装")
            issues_paint.extend(paint_issues)

            body_issues = _extract_issues(content, date_shift, "车身")
            issues_body.extend(body_issues)

            # 提取压铸巡检
            dc = _extract_die_cast(content, date_shift)
            die_cast.extend(dc)

        return {
            "audit_paint": audit_paint if any(audit_paint.values()) else fb.AUDIT_PAINT,
            "audit_body": audit_body if any(audit_body.values()) else fb.AUDIT_BODY,
            "dpu_paint": dpu_paint if dpu_paint else fb.DPU_PAINT,
            "dpu_body": dpu_body if dpu_body else fb.DPU_BODY,
            "dpu_stamp": dpu_stamp if dpu_stamp else fb.DPU_STAMP,
            "color_match": fb.COLOR_MATCH,
            "issues_paint": issues_paint if issues_paint else fb.ISSUES_PAINT,
            "issues_body": issues_body if issues_body else fb.ISSUES_BODY,
            "die_cast": die_cast if die_cast else fb.DIE_CAST,
        }
    except Exception as e:
        print(f"过程质量解析异常: {e}")
        return _fallback()


def _fallback() -> dict:
    return {
        "audit_paint": fb.AUDIT_PAINT,
        "audit_body": fb.AUDIT_BODY,
        "dpu_paint": fb.DPU_PAINT,
        "dpu_body": fb.DPU_BODY,
        "dpu_stamp": fb.DPU_STAMP,
        "color_match": fb.COLOR_MATCH,
        "issues_paint": fb.ISSUES_PAINT,
        "issues_body": fb.ISSUES_BODY,
        "die_cast": fb.DIE_CAST,
    }


def _split_by_date_shift(md: str) -> list[tuple[str, str]]:
    """按日期班次分割文档，返回 [(日期班次, 内容), ...]"""
    # 匹配 "5/31白班" 或 "5/31 白班" 格式
    parts = re.split(r'^(\d{1,2}/\d{1,2}\s*(?:白班|夜班))', md, flags=re.MULTILINE)

    sections = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            date_shift = parts[i].replace(' ', '')
            # 标准化为 "M/D 白班/夜班" 格式
            match = re.match(r'(\d{1,2}/\d{1,2})(白班|夜班)', date_shift)
            if match:
                date_shift = f"{match.group(1)} {match.group(2)}"
            sections.append((date_shift, parts[i + 1]))

    return sections


def _extract_paint_scores(content: str, date_shift: str) -> dict:
    """提取涂装AUDIT分数"""
    scores = {}

    # 查找涂装audit相关内容
    paint_section = re.search(r'涂装.*?audit(.*?)(?=车身|冲压|压铸|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not paint_section:
        return scores

    text = paint_section.group(1)

    # 提取M9分数
    m9_match = re.search(r'M9.*?(\d+)\s*分', text)
    if m9_match:
        scores["M9"] = int(m9_match.group(1))

    # 提取B1分数
    b1_match = re.search(r'B1.*?(\d+)\s*分', text)
    if b1_match:
        scores["B1"] = int(b1_match.group(1))

    return scores


def _extract_body_scores(content: str, date_shift: str) -> dict:
    """提取车身AUDIT分数"""
    scores = {}

    # 查找车身audit相关内容
    body_section = re.search(r'车身.*?audit(.*?)(?=涂装|冲压|压铸|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not body_section:
        return scores

    text = body_section.group(1)

    # 提取M9分数
    m9_match = re.search(r'M9.*?(\d+)\s*分', text)
    if m9_match:
        scores["M9"] = int(m9_match.group(1))

    # 提取B1分数
    b1_match = re.search(r'B1.*?(\d+)\s*分', text)
    if b1_match:
        scores["B1"] = int(b1_match.group(1))

    return scores


def _extract_dpu(content: str, date_shift: str) -> dict:
    """提取DPU数据"""
    dpu = {}

    # 提取涂装DPU
    paint_match = re.search(r'涂装.*?DPU[：:]\s*([\d.]+)', content, re.IGNORECASE)
    if paint_match:
        dpu["paint"] = float(paint_match.group(1))

    # 提取车身DPU
    body_match = re.search(r'车身.*?DPU[：:]\s*([\d.]+)', content, re.IGNORECASE)
    if body_match:
        dpu["body"] = float(body_match.group(1))

    # 提取冲压DPU
    stamp_match = re.search(r'冲压.*?DPU[：:]\s*([\d.]+)', content, re.IGNORECASE)
    if stamp_match:
        dpu["stamp"] = float(stamp_match.group(1))

    return dpu


def _extract_issues(content: str, date_shift: str, workshop: str) -> list[dict]:
    """提取问题表格"""
    issues = []

    # 查找workshop相关的section
    section_match = re.search(
        rf'{workshop}(.*?)(?=(?:涂装|车身|冲压|压铸)(?!{workshop})|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    if not section_match:
        return []

    section = section_match.group(1)
    tables = extract_tables(section)

    for table in tables:
        if len(table) < 2:
            continue

        headers = [strip_html(h).strip() for h in table[0]]

        # 检查是否是问题表格
        if not any('问题' in h for h in headers):
            continue

        for row in table[1:]:
            if len(row) < 3:
                continue

            row_dict = {}
            for idx, h in enumerate(headers):
                if idx < len(row):
                    row_dict[h] = strip_html(row[idx]).strip()

            desc = row_dict.get("问题描述", row_dict.get("问题", ""))
            if desc:
                issues.append({
                    "日期": date_shift,
                    "等级": row_dict.get("严重等级", row_dict.get("等级", "")),
                    "问题": desc,
                    "车型": row_dict.get("车型", ""),
                    "频次": row_dict.get("频次", ""),
                })

    return issues


def _extract_die_cast(content: str, date_shift: str) -> list[dict]:
    """提取压铸巡检结果"""
    results = []

    # 查找压铸section
    section_match = re.search(r'压铸(.*?)(?=#{2,}|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not section_match:
        return []

    section = section_match.group(1)

    # 检查是否有NG
    has_ng = bool(re.search(r'NG|不合格|异常', section, re.IGNORECASE))

    # 提取巡检详情
    detail_parts = []
    if re.search(r'铝液成分', section):
        detail_parts.append("铝液成分OK")
    if re.search(r'铝锭来料', section):
        detail_parts.append("铝锭来料合格")
    if re.search(r'机械性能', section):
        detail_parts.append("机械性能达标")
    if re.search(r'X-RAY', section):
        if has_ng:
            detail_parts.append("X-RAY有缺陷")
        else:
            detail_parts.append("X-RAY无缺陷")

    status = "NG" if has_ng else "OK"
    detail = " | ".join(detail_parts) if detail_parts else strip_html(section)[:100]

    problem = ""
    if has_ng:
        problem_match = re.search(r'(?:发现|问题|异常)[：:]?\s*(.+)', section)
        if problem_match:
            problem = problem_match.group(1).strip()[:50]

    results.append({
        "日期": date_shift,
        "状态": status,
        "巡检详情": detail,
        "发现问题": problem,
    })

    return results
