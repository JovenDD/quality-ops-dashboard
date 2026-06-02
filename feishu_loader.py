"""飞书数据获取与解析模块 - 实时从飞书文档拉取质量数据"""

import subprocess
import json
import re
import os
import streamlit as st
from datetime import datetime, timedelta

# feishu CLI 路径（Windows npm global）
FEISHU_CMD = os.path.join(os.environ.get("APPDATA", ""), "npm", "feishu.cmd")
if not os.path.exists(FEISHU_CMD):
    FEISHU_CMD = "feishu"  # fallback to PATH

# 飞书数据源URL
FEISHU_URLS = {
    "audit": "https://mi.feishu.cn/wiki/UYrDwlfqpiK6ODkMfSscD5SUn8f",
    "func_review": "https://mi.feishu.cn/wiki/U2iXwxA5mi7j4VkimbUchCKUnhe",
    "quality_m9": "https://mi.feishu.cn/wiki/Cd5iwXGA2iT0VOklTGRcuEnlnGc",
    "quality_b1": "https://mi.feishu.cn/docx/PCUHdrvcBoBbj8xq81qcsmTEnVd",
    "quality_b2": "https://mi.feishu.cn/wiki/I5iVw8sQcibHM8kDBzGc7cJOnjh",
    "process": "https://mi.feishu.cn/wiki/R4Mmwg3IpiDTrTk5RXCcLx2jnQg",
}


def fetch_feishu_doc(url: str) -> dict:
    """调用 feishu CLI 获取文档内容"""
    try:
        result = subprocess.run(
            f'"{FEISHU_CMD}" fetch "{url}"',
            capture_output=True, timeout=30, shell=True
        )
        stdout = result.stdout.decode('utf-8', errors='replace').strip()
        if result.returncode == 0 and stdout:
            return json.loads(stdout)
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
        return {"error": stderr or "fetch failed"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {e}"}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=300)
def load_all_data():
    """加载所有飞书数据源（缓存5分钟）"""
    data = {}
    for key, url in FEISHU_URLS.items():
        data[key] = fetch_feishu_doc(url)
    return data


def clean_markdown(md: str) -> str:
    """清理飞书markdown中的特殊标签"""
    md = re.sub(r'<cite[^>]*>.*?</cite>', '', md, flags=re.DOTALL)
    md = re.sub(r'<cite[^>]*/>', '', md)
    md = re.sub(r'<source[^>]*/>', '', md)
    md = re.sub(r'<readonly-block[^>]*>.*?</readonly-block>', '', md, flags=re.DOTALL)
    md = re.sub(r'<bitable[^>]*/>', '', md)
    md = re.sub(r'<sheet[^>]*/>', '', md)
    md = re.sub(r'<chart-refer[^>]*/>', '', md)
    md = re.sub(r'<grid>.*?</grid>', '', md, flags=re.DOTALL)
    md = re.sub(r'<callout[^>]*>', '', md)
    md = re.sub(r'</callout>', '', md)
    md = re.sub(r'<title>(.*?)</title>', r'# \1', md)
    return md.strip()


def parse_audit_data(data: dict) -> dict:
    """解析AUDIT日报数据，提取最新几天的状态"""
    md = data.get("markdown", "")
    result = {
        "title": "北京工厂整车Audit日报",
        "latest_date": "",
        "mx11": {"factories": {}},
        "ms12": {"score": 0, "target": 110, "b_count": 0, "c_count": 0, "sa_count": 0, "status": ""},
        "daily_trend": [],
        "todo_count": 0,
        "todo_done": 0,
    }

    # 提取代办信息
    todo_match = re.search(r'待办共计(\d+)项.*?已完成(\d+)项', md)
    if todo_match:
        result["todo_count"] = int(todo_match.group(1))
        result["todo_done"] = int(todo_match.group(2))

    # 按日期分割
    date_sections = re.split(r'\n# (2026/\d+/\d+)\n', md)
    dates_data = []

    for i in range(1, len(date_sections), 2):
        if i + 1 < len(date_sections):
            date_str = date_sections[i]
            content = date_sections[i + 1]

            day_data = {"date": date_str, "mx11": {}, "ms12": {}}

            # 解析MX11各工厂
            # 一期
            yiqi_match = re.search(r'一期状态.*?(?=\n###|\n## MS12)', content, re.DOTALL)
            if yiqi_match:
                yiqi_text = yiqi_match.group(0)
                score_m = re.search(r'单车(?:平均)?分数\s*(\d+)', yiqi_text)
                if score_m:
                    day_data["mx11"]["一期"] = {
                        "score": int(score_m.group(1)),
                        "target": 85,
                        "status": "达标" if int(score_m.group(1)) <= 85 else "未达标"
                    }

            # B1 base
            b1base_match = re.search(r'B1 (?:MX11 )?base状态.*?(?=\n### B1 (?:MX11-9|-9)|\n## MS12)', content, re.DOTALL)
            if b1base_match:
                b1_text = b1base_match.group(0)
                score_m = re.search(r'单车(?:平均)?分数\s*(\d+)', b1_text)
                b_m = re.search(r'B 类\s*(\d+)', b1_text)
                c_m = re.search(r'C 类\s*(\d+)', b1_text)
                if score_m:
                    day_data["mx11"]["B1-base"] = {
                        "score": int(score_m.group(1)),
                        "target": 85,
                        "b_count": int(b_m.group(1)) if b_m else 0,
                        "c_count": int(c_m.group(1)) if c_m else 0,
                        "status": "达标" if int(score_m.group(1)) <= 85 else "未达标"
                    }

            # B1 -9
            b19_match = re.search(r'B1 (?:MX11-9|-9)状态.*?(?=\n### B2|\n## MS12)', content, re.DOTALL)
            if b19_match:
                b19_text = b19_match.group(0)
                score_m = re.search(r'单车(?:平均)?分数\s*(\d+)', b19_text)
                b_m = re.search(r'B 类\s*(\d+)', b19_text)
                c_m = re.search(r'C 类\s*(\d+)', b19_text)
                if score_m:
                    day_data["mx11"]["B1-9"] = {
                        "score": int(score_m.group(1)),
                        "target": 110,
                        "b_count": int(b_m.group(1)) if b_m else 0,
                        "c_count": int(c_m.group(1)) if c_m else 0,
                        "status": "达标" if int(score_m.group(1)) <= 110 else "未达标"
                    }

            # B2
            b2_match = re.search(r'B2 (?:MX11)?状态.*?(?=\n## MS12)', content, re.DOTALL)
            if b2_match:
                b2_text = b2_match.group(0)
                score_m = re.search(r'单车(?:平均)?分数\s*(\d+)', b2_text)
                b_m = re.search(r'B 类\s*(\d+)', b2_text)
                c_m = re.search(r'C 类\s*(\d+)', b2_text)
                if score_m:
                    day_data["mx11"]["B2"] = {
                        "score": int(score_m.group(1)),
                        "target": 85,
                        "b_count": int(b_m.group(1)) if b_m else 0,
                        "c_count": int(c_m.group(1)) if c_m else 0,
                        "status": "达标" if int(score_m.group(1)) <= 85 else "未达标"
                    }

            # MS12
            ms12_match = re.search(r'MS12总体状态.*?(?=\n# 2026|\n# 历史|$)', content, re.DOTALL)
            if ms12_match:
                ms12_text = ms12_match.group(0)
                score_m = re.search(r'单车分数\s*([\d.]+)', ms12_text)
                b_m = re.search(r'B 类\s*([\d.]+)', ms12_text)
                c_m = re.search(r'C 类\s*([\d.]+)', ms12_text)
                target_m = re.search(r'目标\s*(\d+)', ms12_text)
                if score_m:
                    day_data["ms12"] = {
                        "score": float(score_m.group(1)),
                        "target": int(target_m.group(1)) if target_m else 110,
                        "b_count": float(b_m.group(1)) if b_m else 0,
                        "c_count": float(c_m.group(1)) if c_m else 0,
                        "status": "达标" if float(score_m.group(1)) <= (int(target_m.group(1)) if target_m else 110) else "未达标"
                    }

            dates_data.append(day_data)

    result["daily_trend"] = dates_data
    if dates_data:
        result["latest_date"] = dates_data[0]["date"]
        if dates_data[0].get("ms12"):
            result["ms12"] = dates_data[0]["ms12"]
        result["mx11"]["factories"] = dates_data[0].get("mx11", {})

    return result


def parse_func_review_data(data: dict) -> dict:
    """解析全功能评审数据"""
    md = data.get("markdown", "")
    result = {
        "title": "北京工厂全功能质量日报",
        "latest_date": "",
        "reviews": [],
        "issues": [],
        "smell_data": [],
    }

    # 按日期分割
    date_sections = re.split(r'\n# (2026[\.\s]+\d+\.\d+)\n', md)
    dates_data = []

    for i in range(1, len(date_sections), 2):
        if i + 1 < len(date_sections):
            date_str = date_sections[i].replace('.', '/').replace(' ', '')
            content = date_sections[i + 1]

            day_data = {"date": date_str, "models": [], "issues": []}

            # 解析各车型评审状态
            # MS12
            ms12_match = re.search(r'MS12.*?评审(\d+)台.*?无S/A类问题.*?B类\s*(\d+)\s*项.*?C类\s*(\d+)\s*项.*?单车B类及以上缺陷率([\d.]+).*?([\d.]+)目标', content, re.DOTALL)
            if ms12_match:
                day_data["models"].append({
                    "model": "MS12",
                    "count": int(ms12_match.group(1)),
                    "b_count": int(ms12_match.group(2)),
                    "c_count": int(ms12_match.group(3)),
                    "defect_rate": float(ms12_match.group(4)),
                    "target": float(ms12_match.group(5)),
                    "status": "达标" if float(ms12_match.group(4)) <= float(ms12_match.group(5)) else "未达标"
                })

            # 解析重点问题表格
            issue_rows = re.findall(r'\|\s*(\d+)\s*\|\s*(MS12|B1|B2|MX11)\s*\|\s*(M9|B1|B2)\s*\|\s*([SABC])\s*\|\s*(.*?)\s*\|\s*(新增|复发)\s*\|\s*(.*?)\s*\|', content)
            for row in issue_rows:
                day_data["issues"].append({
                    "no": row[0], "model": row[1], "factory": row[2],
                    "level": row[3], "desc": row[4], "type": row[5], "result": row[6]
                })

            # 气味评审
            smell_rows = re.findall(r'\|\s*(MS12|B1.*?)\s*\|\s*(.*?)\s*\|\s*([\d.]+)\s*\|\s*(.*?)\s*\|', content)
            for row in smell_rows:
                day_data["smell"].append({
                    "model": row[0], "vin": row[1], "level": float(row[2]), "type": row[3]
                }) if "smell" in day_data else None

            dates_data.append(day_data)

    result["reviews"] = dates_data
    if dates_data:
        result["latest_date"] = dates_data[0]["date"]
        result["issues"] = [i for d in dates_data for i in d.get("issues", [])]

    return result


def parse_vehicle_quality(data: dict, factory: str) -> dict:
    """解析整车质量数据（M9/B1/B2）"""
    md = data.get("markdown", "")
    result = {
        "factory": factory,
        "ftt": 0, "ftt_target": 85,
        "dpu": 0, "dpu_target": 0.15,
        "report_count": 0,
        "s_count": 0, "a_count": 0, "b_count": 0, "c_count": 0,
        "top_issues": [],
        "dept_dpu": [],
        "escalated": [],
    }

    # 提取FTT/DPU
    ftt_match = re.search(r'FTT[：:]\s*([\d.]+)%', md)
    dpu_match = re.search(r'DPU[：:]\s*([\d.]+)', md)
    report_match = re.search(r'报交\s*(\d+)\s*台', md)
    b_match = re.search(r'B 类\s*(\d+)\s*个', md)

    if ftt_match:
        result["ftt"] = float(ftt_match.group(1))
    if dpu_match:
        result["dpu"] = float(dpu_match.group(1))
    if report_match:
        result["report_count"] = int(report_match.group(1))
    if b_match:
        result["b_count"] = int(b_match.group(1))

    # 提取DPU达标情况
    dept_matches = re.findall(r'[🟢🔴🟡]\s*\**(\w+)\**\s*.*?DPU\s*([\d.]+).*?目标\s*([\d.]+)', md)
    for dept, dpu, target in dept_matches:
        result["dept_dpu"].append({
            "dept": dept, "dpu": float(dpu), "target": float(target),
            "status": "达标" if float(dpu) <= float(target) else "未达标"
        })

    # 提取重点升级问题
    escalated = re.findall(r'\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|', md)
    for row in escalated:
        if row[0] and '问题描述' not in row[0]:
            result["escalated"].append({
                "desc": row[0], "reason": row[1], "source": row[2],
                "reporter": row[3], "dept": row[4]
            })

    return result


def parse_process_quality(data: dict) -> dict:
    """解析过程质量数据"""
    md = data.get("markdown", "")
    result = {
        "title": "车身质量科抽检&巡检日报",
        "latest_section": "",
        "key_issues": [],
        "body_audit": {},
        "paint_audit": {},
        "color_match": {},
        "stamping": {},
        "die_casting": {},
    }

    # 提取最新日期段落
    latest_match = re.search(r'# (\d+/\d+(?:夜班|白班|))\n', md)
    if latest_match:
        result["latest_section"] = latest_match.group(1)

    # 提取今日重点问题
    issue_table = re.search(r'## 今日重点问题\s*\n\s*\|.*?\n\|[-|]+\|\n(.*?)(?=\n##|\n#|$)', md, re.DOTALL)
    if issue_table:
        rows = re.findall(r'\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|', issue_table.group(1))
        for row in rows[:10]:
            result["key_issues"].append({
                "no": row[0], "desc": row[1], "model": row[2]
            })

    # 提取车身AUDIT
    body_match = re.search(r'车身AUDIT.*?分数\s*([\d.]+).*?目标\s*([\d.]+)', md, re.DOTALL)
    if body_match:
        result["body_audit"] = {
            "score": float(body_match.group(1)),
            "target": float(body_match.group(2)),
            "status": "达标" if float(body_match.group(1)) <= float(body_match.group(2)) else "未达标"
        }

    # 提取涂装AUDIT
    paint_match = re.search(r'涂装AUDIT.*?分数\s*([\d.]+).*?目标\s*([\d.]+)', md, re.DOTALL)
    if paint_match:
        result["paint_audit"] = {
            "score": float(paint_match.group(1)),
            "target": float(paint_match.group(2)),
            "status": "达标" if float(paint_match.group(1)) <= float(paint_match.group(2)) else "未达标"
        }

    return result


def get_all_parsed_data():
    """获取并解析所有数据"""
    raw_data = load_all_data()
    parsed = {}

    if "audit" in raw_data and "error" not in raw_data["audit"]:
        parsed["audit"] = parse_audit_data(raw_data["audit"])
    else:
        parsed["audit"] = None

    if "func_review" in raw_data and "error" not in raw_data["func_review"]:
        parsed["func_review"] = parse_func_review_data(raw_data["func_review"])
    else:
        parsed["func_review"] = None

    for factory, key in [("M9", "quality_m9"), ("B1", "quality_b1"), ("B2", "quality_b2")]:
        if key in raw_data and "error" not in raw_data[key]:
            parsed[f"quality_{factory.lower()}"] = parse_vehicle_quality(raw_data[key], factory)
        else:
            parsed[f"quality_{factory.lower()}"] = None

    if "process" in raw_data and "error" not in raw_data["process"]:
        parsed["process"] = parse_process_quality(raw_data["process"])
    else:
        parsed["process"] = None

    parsed["_raw"] = raw_data
    return parsed
