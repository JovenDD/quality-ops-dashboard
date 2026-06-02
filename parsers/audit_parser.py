"""解析整车AUDIT日报"""
import re
from parsers import strip_html, extract_tables
import fallback_data as fb


def parse(markdown: str) -> dict:
    """解析AUDIT日报markdown，返回结构化数据"""
    if not markdown:
        return _fallback()

    try:
        # 按日期分割文档
        date_sections = _split_by_date(markdown)

        # 提取每个日期的数据
        all_cars = []  # 所有日期的车型数据
        all_issues = []

        for date_str, content in date_sections:
            cars = _extract_cars_for_date(content, date_str)
            all_cars.extend(cars)

            issues = _extract_issues_for_date(content, date_str)
            all_issues.extend(issues)

        # 构建trend数据（按车型分组，保留历史）
        trend = _build_trend(all_cars)

        # 每个车型取最新日期的数据用于概览卡片
        latest_cars = _get_latest_per_car(all_cars)

        return {
            "audit_cars": latest_cars if latest_cars else fb.AUDIT_CARS,
            "audit_trend": trend if trend else fb.AUDIT_TREND,
            "audit_issues": all_issues[:20] if all_issues else fb.AUDIT_ISSUES,
        }
    except Exception as e:
        print(f"AUDIT解析异常: {e}")
        return _fallback()


def _fallback() -> dict:
    return {
        "audit_cars": fb.AUDIT_CARS,
        "audit_trend": fb.AUDIT_TREND,
        "audit_issues": fb.AUDIT_ISSUES,
    }


def _split_by_date(md: str) -> list[tuple[str, str]]:
    """按日期header分割文档，返回 [(日期, 内容), ...]，最新日期在前"""
    # 匹配 # 2026/5/31 或 # 2026-5-31 格式
    parts = re.split(r'^#\s+(\d{4}[-/]\d{1,2}[-/]\d{1,2})', md, flags=re.MULTILINE)

    sections = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            date_str = parts[i].replace('-', '/')
            # 简化为 M/D 格式
            date_short = '/'.join(date_str.split('/')[1:])
            sections.append((date_short, parts[i + 1]))

    return sections


def _extract_cars_for_date(content: str, date: str) -> list[dict]:
    """从一个日期的content中提取各车型数据"""
    cars = []

    # 按车型section分割
    # MX11总体状态 包含: 一期状态、B1 MX11 base状态、B1 MX11-9状态、B2 MX11状态
    # MS12总体状态

    # 提取MS12数据
    ms12_match = re.search(r'MS12总体状态(.*?)(?=MX11总体状态|\Z)', content, re.DOTALL)
    if ms12_match:
        ms12_data = _parse_car_block(ms12_match.group(1), "MS12 (一期)")
        if ms12_data:
            ms12_data["date"] = date
            cars.append(ms12_data)

    # 提取MX11各变体数据
    mx11_match = re.search(r'MX11总体状态(.*?)(?=MS12总体状态|\Z)', content, re.DOTALL)
    if mx11_match:
        mx11_content = mx11_match.group(1)

        # 一期状态（通常无数据）
        # B1 MX11 base状态
        b1_base = re.search(r'B1\s*MX11\s*base状态(.*?)(?=B1\s*MX11.*?-9|B2\s*MX11|\Z)', mx11_content, re.DOTALL)
        if b1_base:
            data = _parse_car_block(b1_base.group(1), "B1 MX11 base")
            if data:
                data["date"] = date
                cars.append(data)

        # B1 MX11-9状态
        b1_9 = re.search(r'B1\s*MX11.*?-9状态(.*?)(?=B2\s*MX11|\Z)', mx11_content, re.DOTALL)
        if b1_9:
            data = _parse_car_block(b1_9.group(1), "B1 MX11-9")
            if data:
                data["date"] = date
                cars.append(data)

        # B2 MX11状态
        b2 = re.search(r'B2\s*MX11状态(.*?)(?=MS12|\Z)', mx11_content, re.DOTALL)
        if b2:
            data = _parse_car_block(b2.group(1), "B2 MX11")
            if data:
                data["date"] = date
                cars.append(data)

    return cars


def _parse_car_block(text: str, car_name: str) -> dict | None:
    """从车型文本块中提取数据"""
    # 去掉HTML标签
    clean = strip_html(text)

    # 提取分数（支持小数）
    score_match = re.search(r'(?:单车)?(?:平均)?分数\s*([\d.]+)\s*分', clean)
    if not score_match:
        # 尝试其他模式
        score_match = re.search(r'([\d.]+)\s*分', clean)
    if not score_match:
        return None

    score = float(score_match.group(1))

    # 提取目标（根据车型设置固定目标值）
    # B2 MX11目标85，其他目标110
    target = 85 if "B2" in car_name else 110

    # 提取B类数量
    b_match = re.search(r'[Bb]\s*类\s*([\d.]+)\s*个', clean)
    b_count = float(b_match.group(1)) if b_match else 0

    # 提取C类数量
    c_match = re.search(r'[Cc]\s*类\s*([\d.]+)\s*个', clean)
    c_count = float(c_match.group(1)) if c_match else 0

    # 构建详情
    ng = score > target
    status = "未达标" if ng else "达标"
    detail = f"分数{score}分，目标{target}，{status}。B类{b_count}个，C类{c_count}个"

    return {
        "name": car_name,
        "date": "",  # 由调用方设置
        "score": score,
        "target": target,
        "b": b_count,
        "c": c_count,
        "detail": detail,
    }


def _extract_issues_for_date(content: str, date: str) -> list[dict]:
    """从一个日期的content中提取问题表格"""
    issues = []
    tables = extract_tables(content)

    for table in tables:
        if len(table) < 2:
            continue

        headers = [strip_html(h).strip() for h in table[0]]

        # 检查是否是问题表格
        if not any('问题' in h or '等级' in h or '车型' in h for h in headers):
            continue

        for row in table[1:]:
            if len(row) < 3:
                continue

            # 构建字典
            row_dict = {}
            for idx, h in enumerate(headers):
                if idx < len(row):
                    row_dict[h] = strip_html(row[idx]).strip()

            issues.append({
                "日期": date,
                "车型": row_dict.get("车型", ""),
                "等级": row_dict.get("等级", row_dict.get("严重等级", row_dict.get("问题等级", ""))),
                "问题": row_dict.get("问题", row_dict.get("问题描述", "")),
                "频次": row_dict.get("频次", ""),
                "原因": row_dict.get("原因", row_dict.get("原因分析", "")),
            })

    return issues


def _get_latest_per_car(cars: list[dict]) -> list[dict]:
    """获取每个车型的最新数据"""
    latest = {}
    for car in cars:
        name = car["name"]
        if name not in latest or car["date"] > latest[name]["date"]:
            latest[name] = car
    return list(latest.values())


def _build_trend(cars: list[dict]) -> dict:
    """从所有日期的车型数据构建趋势数据"""
    trend = {}

    for car in cars:
        name = car["name"]
        if name not in trend:
            trend[name] = {"d": [], "s": [], "t": [], "b": []}

        trend[name]["d"].append(car["date"])
        trend[name]["s"].append(car["score"])
        trend[name]["t"].append(car["target"])
        trend[name]["b"].append(car["b"])

    # 按日期排序（从早到晚）
    for name in trend:
        combined = list(zip(trend[name]["d"], trend[name]["s"], trend[name]["t"], trend[name]["b"]))
        combined.sort(key=lambda x: x[0])
        trend[name]["d"] = [x[0] for x in combined]
        trend[name]["s"] = [x[1] for x in combined]
        trend[name]["t"] = [x[2] for x in combined]
        trend[name]["b"] = [x[3] for x in combined]

    return trend
