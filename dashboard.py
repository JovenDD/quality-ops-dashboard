"""
质量运营看板 v3.1 — 管理驾驶舱
小米汽车质量运营部 · 修复版
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import re
import json
import os
import subprocess
from datetime import datetime, timedelta

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="质量运营看板",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 全局样式 ====================
st.markdown("""
<style>
    .stApp { background: #0f172a; }
    .main .block-container { padding: 1rem 2rem; max-width: 100%; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1222 0%, #0f172a 40%, #111827 100%);
        border-right: 1px solid rgba(51,65,85,0.5);
    }
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
        color: #e2e8f0 !important;
    }

    /* 侧边栏导航美化 */
    section[data-testid="stSidebar"] .stRadio {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 4px !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin: 0 !important;
        transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
        position: relative;
        cursor: pointer;
    }
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(51,65,85,0.3) !important;
        border-color: rgba(71,85,105,0.3) !important;
        transform: translateX(4px);
    }
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.08) 100%) !important;
        border-color: rgba(99,102,241,0.4) !important;
        box-shadow: 0 0 20px rgba(99,102,241,0.1), inset 0 1px 0 rgba(255,255,255,0.05) !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"]::before {
        content: '';
        position: absolute;
        left: 0; top: 20%; bottom: 20%;
        width: 3px;
        background: linear-gradient(180deg, #818cf8, #6366f1);
        border-radius: 0 3px 3px 0;
    }
    section[data-testid="stSidebar"] .stRadio > div > label span {
        font-size: 14px !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px;
    }
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] span {
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }

    /* 侧边栏分割线 */
    section[data-testid="stSidebar"] hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(71,85,105,0.4), transparent) !important;
        margin: 16px 0 !important;
    }

    /* 侧边栏按钮 */
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(139,92,246,0.08) 100%) !important;
        border: 1px solid rgba(99,102,241,0.25) !important;
        border-radius: 12px !important;
        color: #c7d2fe !important;
        font-weight: 500 !important;
        transition: all 0.25s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(139,92,246,0.15) 100%) !important;
        border-color: rgba(99,102,241,0.5) !important;
        box-shadow: 0 0 15px rgba(99,102,241,0.15) !important;
        transform: translateY(-1px);
    }

    .top-bar {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 50%, #1a1a2e 100%);
        padding: 20px 32px; border-radius: 16px; margin-bottom: 20px;
        border: 1px solid #334155; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .top-bar h1 { color: #f1f5f9; font-size: 26px; font-weight: 800; margin: 0; }
    .top-bar .sub { color: #94a3b8; font-size: 13px; margin-top: 6px; }

    .status-card {
        background: linear-gradient(135deg, #1e293b 0%, #1a2332 100%);
        border-radius: 16px; padding: 24px; border: 1px solid #334155;
        margin-bottom: 16px; position: relative; overflow: hidden;
    }
    .status-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    }
    .status-card.green::before { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .status-card.yellow::before { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .status-card.red::before { background: linear-gradient(90deg, #ef4444, #dc2626); }

    .card-title { color: #94a3b8; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    .card-value { color: #f1f5f9; font-size: 36px; font-weight: 800; line-height: 1.1; }
    .card-value.green { color: #4ade80; }
    .card-value.yellow { color: #fbbf24; }
    .card-value.red { color: #f87171; }
    .card-sub { color: #64748b; font-size: 13px; margin-top: 6px; }
    .card-target { color: #94a3b8; font-size: 14px; }

    .status-dot {
        display: inline-block; width: 10px; height: 10px; border-radius: 50%;
        margin-right: 6px; animation: pulse 2s infinite;
    }
    .status-dot.green { background: #4ade80; box-shadow: 0 0 8px #4ade80; }
    .status-dot.yellow { background: #fbbf24; box-shadow: 0 0 8px #fbbf24; }
    .status-dot.red { background: #f87171; box-shadow: 0 0 8px #f87171; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }

    .factory-card {
        background: linear-gradient(135deg, #1e293b 0%, #162033 100%);
        border-radius: 20px; padding: 28px; border: 1px solid #334155;
        margin-bottom: 20px; position: relative; overflow: hidden;
    }
    .factory-card::before {
        content: ''; position: absolute; top: 0; left: 0; bottom: 0; width: 6px;
    }
    .factory-card.green::before { background: linear-gradient(180deg, #22c55e, #16a34a); }
    .factory-card.yellow::before { background: linear-gradient(180deg, #f59e0b, #d97706); }
    .factory-card.red::before { background: linear-gradient(180deg, #ef4444, #dc2626); }
    .factory-name { color: #f1f5f9; font-size: 20px; font-weight: 700; margin-bottom: 16px; }

    .badge { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-green { background: rgba(34,197,94,0.15); color: #4ade80; }
    .badge-yellow { background: rgba(245,158,11,0.15); color: #fbbf24; }
    .badge-red { background: rgba(239,68,68,0.15); color: #f87171; }

    .section-divider { height: 1px; background: linear-gradient(90deg, transparent, #334155, transparent); margin: 24px 0; }

    .risk-card {
        background: linear-gradient(135deg, #2d1b1b 0%, #1e293b 100%);
        border-radius: 12px; padding: 16px 20px; border-left: 4px solid #ef4444; margin-bottom: 12px;
    }
    .risk-card.medium { background: linear-gradient(135deg, #2d2b1b 0%, #1e293b 100%); border-left-color: #f59e0b; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* 统一表格风格 - 暗色主题 */
    .issue-table { width: 100%; border-collapse: collapse; margin: 12px 0; }
    .issue-table th {
        background: #334155; color: #e2e8f0; padding: 10px 14px;
        text-align: left; font-size: 13px; font-weight: 600;
        border-bottom: 2px solid #475569;
    }
    .issue-table td {
        padding: 10px 14px; border-bottom: 1px solid #1e293b;
        color: #cbd5e1; font-size: 13px;
    }
    .issue-table tr:hover td { background: rgba(51,65,85,0.3); }
    .issue-table .level-S { color: #f87171; font-weight: 700; }
    .issue-table .level-A { color: #fb923c; font-weight: 700; }
    .issue-table .level-B { color: #fbbf24; font-weight: 600; }
    .issue-table .level-C { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)


# ==================== 颜色常量 ====================
C = {
    "bg": "#0f172a", "card_bg": "#1e293b", "border": "#334155",
    "text": "#f1f5f9", "text_sub": "#94a3b8", "text_dim": "#64748b",
    "green": "#4ade80", "green_dark": "#22c55e",
    "yellow": "#fbbf24", "yellow_dark": "#f59e0b",
    "red": "#f87171", "red_dark": "#ef4444",
    "blue": "#60a5fa", "indigo": "#818cf8", "purple": "#a78bfa",
    "cyan": "#22d3ee", "orange": "#fb923c",
    "plotly_bg": "rgba(0,0,0,0)", "grid": "#1e293b",
}


# ==================== 数据加载 ====================
@st.cache_data(ttl=300)
def load_feishu_data():
    # 优先本地CLI
    try:
        from feishu_loader import load_all_data
        data = load_all_data()
        if data:
            return data
    except Exception:
        pass
    # 备用：飞书Open API（云端部署）
    try:
        from feishu_api_loader import load_all_data as load_api_data
        data = load_api_data()
        if data:
            return data
    except Exception:
        pass
    return None


def get_fallback_data():
    from fallback_data import (
        AUDIT_CARS, AUDIT_TREND, AUDIT_ISSUES, FUNC_ISSUES, DEFECT_RATE,
        FTT, DPU_WHOLE, QUALITY_ISSUES, AUDIT_PAINT, AUDIT_BODY,
        DPU_PAINT, DPU_BODY, DPU_STAMP, COLOR_MATCH, ISSUES_PAINT, ISSUES_BODY, DIE_CAST
    )
    return {
        "audit_cars": AUDIT_CARS, "audit_trend": AUDIT_TREND, "audit_issues": AUDIT_ISSUES,
        "func_issues": FUNC_ISSUES, "defect_rate": DEFECT_RATE, "ftt": FTT, "dpu": DPU_WHOLE,
        "quality_issues": QUALITY_ISSUES, "audit_paint": AUDIT_PAINT, "audit_body": AUDIT_BODY,
        "dpu_paint": DPU_PAINT, "dpu_body": DPU_BODY, "dpu_stamp": DPU_STAMP,
        "color_match": COLOR_MATCH, "issues_paint": ISSUES_PAINT, "issues_body": ISSUES_BODY,
        "die_cast": DIE_CAST,
    }


# ==================== 解析工具 ====================
def split_by_date(md, pattern):
    matches = list(re.finditer(pattern, md, re.MULTILINE))
    sections = []
    for idx, m in enumerate(matches):
        ds = m.group(1)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md)
        sections.append((ds, md[start:end]))
    return sections


def extract_factory_subsections(section):
    header_pattern = re.compile(r'^### (.+)$', re.MULTILINE)
    headers = list(header_pattern.finditer(section))
    result = {}
    for idx, h in enumerate(headers):
        hname = h.group(1).strip().strip('*').strip()
        start = h.end()
        end = headers[idx + 1].start() if idx + 1 < len(headers) else len(section)
        content = section[start:end]
        if '一期' in hname:
            key = '一期'
        elif 'base' in hname.lower() or ('B1' in hname and '-9' not in hname and 'MX11-9' not in hname):
            key = 'B1-base'
        elif '-9' in hname or 'MX11-9' in hname:
            key = 'B1-9'
        elif 'B2' in hname:
            key = 'B2'
        else:
            continue
        result[key] = content
    return result


def parse_factory_data(content):
    first_lines = '\n'.join(content.strip().split('\n')[:3])
    clean = first_lines.replace('*', '').replace('-', '').strip()
    if clean == '无' or clean.startswith('无'):
        return None
    sm = re.search(r'单车(?:平均)?分数\s*([\d.]+)', first_lines)
    if not sm:
        return None
    s = float(sm.group(1))
    tm = re.search(r'目标\s*(\d+)', first_lines)
    t = int(tm.group(1)) if tm else 85
    bm = re.search(r'B 类\s*([\d.]+)', first_lines)
    cm = re.search(r'C 类\s*([\d.]+)', first_lines)
    return {"score": s, "target": t, "ng": s > t,
            "b": float(bm.group(1)) if bm else 0, "c": float(cm.group(1)) if cm else 0}


def extract_html_issues_from_section(section, limit=10):
    """从HTML表格中提取问题，自动适配不同列结构"""
    issues = []
    tables = re.findall(r'<table>.*?</table>', section, re.DOTALL)
    for tbl in tables:
        rows = re.findall(r'<tr>(.*?)</tr>', tbl, re.DOTALL)
        is_header = True
        header_cols = []
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            cleaned = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            if is_header:
                is_header = False
                if '<th' in row:
                    header_cols = cleaned
                    continue
                if all(len(c) <= 6 for c in cleaned if c):
                    header_cols = cleaned
                    continue
            if len(cleaned) < 4 or not cleaned[0] or cleaned[0] in ('/', '', ' ', '序号'):
                continue
            if not cleaned[0].isdigit():
                continue

            issue = {"NO": cleaned[0]}

            # 检测列结构：如果第2列是日期格式(如2026/05/31)，说明是AUDIT详细表
            # 列: 序号, 评审日期, 车号, 问题描述, 图片, 问题权重, 问题类型...
            if len(cleaned) > 1 and re.match(r'\d{4}[/.]\d{1,2}[/.]\d{1,2}', cleaned[1]):
                issue["日期"] = cleaned[1]
                issue["问题描述"] = cleaned[3] if len(cleaned) > 3 else ""
                issue["车型"] = cleaned[2] if len(cleaned) > 2 else ""
                issue["等级"] = cleaned[5] if len(cleaned) > 5 else ""
                issue["频次"] = ""
                issue["责任人"] = cleaned[9] if len(cleaned) > 9 else ""
            else:
                # 标准列: NO, 问题描述, 车型, 图片, 严重等级, 频次, 责任人, 原因...
                issue["问题描述"] = cleaned[1] if len(cleaned) > 1 else ""
                issue["车型"] = cleaned[2] if len(cleaned) > 2 else ""
                issue["等级"] = cleaned[4] if len(cleaned) > 4 else ""
                issue["频次"] = cleaned[5] if len(cleaned) > 5 else ""
                issue["责任人"] = cleaned[6] if len(cleaned) > 6 else ""

            if issue.get("问题描述") and issue["问题描述"] not in ('/', '', ' '):
                issues.append(issue)
                if len(issues) >= limit:
                    break
    return issues


def extract_audit_issues_from_bitable(audit_md, dates, limit_per_day=5):
    """从AUDIT日报的bitable引用中提取TOP问题"""
    issues = []
    # 先从HTML表格提取（如5/31的问题表）
    for i, ds in enumerate(dates[:7]):
        start = audit_md.find(f'# {ds}')
        if start < 0:
            continue
        end = audit_md.find(f'# {dates[i+1]}') if i+1 < len(dates) else len(audit_md)
        sec = audit_md[start:end]

        # 从HTML表格提取
        extracted = extract_html_issues_from_section(sec, limit=limit_per_day)
        for iss in extracted:
            iss["日期"] = ds
            issues.append(iss)

        # 也从markdown表格提取
        if not extracted:
            md_rows = re.findall(r'^\|\s*(\d+)\s*\|(.+)\|$', sec, re.MULTILINE)
            for mr in md_rows[:limit_per_day]:
                cells = [c.strip() for c in mr[1].split('|')]
                if len(cells) >= 3:
                    iss = {"日期": ds, "NO": mr[0], "问题描述": cells[0],
                           "车型": cells[1] if len(cells) > 1 else "",
                           "等级": cells[2] if len(cells) > 2 else ""}
                    issues.append(iss)
    return issues


def extract_quality_issues(raw):
    """提取整车质量问题"""
    quality_issues = []
    for key, factory in [("quality_m9", "M9"), ("quality_b1", "B1"), ("quality_b2", "B2")]:
        md = raw.get(key, {}).get("markdown", "")
        if factory == "M9":
            esc_idx = md.find('升级问题')
            if esc_idx >= 0:
                # 找到</table>结束位置，避免截断
                end_idx = md.find('</table>', esc_idx)
                if end_idx < 0:
                    end_idx = esc_idx + 20000
                else:
                    end_idx += len('</table>')
                rows = extract_html_issues_from_section(md[esc_idx:end_idx], limit=10)
                for row in rows:
                    quality_issues.append({"工厂": "M9/一期", "问题描述": row.get("问题描述", ""),
                        "升级原因": row.get("等级", ""), "责任部门": row.get("责任人", "")})
        elif factory == "B2":
            todo_idx = md.find('待办跟踪')
            if todo_idx >= 0:
                end_idx = md.find('</table>', todo_idx)
                if end_idx < 0:
                    end_idx = todo_idx + 10000
                else:
                    end_idx += len('</table>')
                rows = extract_html_issues_from_section(md[todo_idx:end_idx], limit=5)
                for row in rows:
                    quality_issues.append({"工厂": "B2", "问题描述": row.get("问题描述", ""),
                        "升级原因": "待办", "责任部门": row.get("责任人", "")})
        elif factory == "B1":
            top_idx = md.find('影响生产')
            if top_idx >= 0:
                end_idx = md.find('</table>', top_idx)
                if end_idx < 0:
                    end_idx = top_idx + 10000
                else:
                    end_idx += len('</table>')
                rows = extract_html_issues_from_section(md[top_idx:end_idx], limit=5)
                for row in rows:
                    quality_issues.append({"工厂": "B1", "问题描述": row.get("问题描述", ""),
                        "升级原因": "停线/受限", "责任部门": row.get("责任人", "")})
    return quality_issues


def extract_process_dpu(proc_md):
    """按用户指定的段落提取DPU：3.1涂装 4.1车身 7冲压
    遍历所有日期段，每种DPU取最新有值的"""
    result = {"paint": None, "body": None, "stamp": None}

    parts = re.split(r'^# (\d+/\d+(?:夜班|白班|))\s*$', proc_md, flags=re.MULTILINE)
    if len(parts) < 3:
        return result

    # 遍历所有日期段(从新到旧)，每种DPU取最新有值的
    for i in range(1, len(parts), 2):
        content = parts[i+1] if i+1 < len(parts) else ''
        sub_sections = re.split(r'(###\s+[^\n]+)', content)

        for j in range(0, len(sub_sections)-1, 2):
            header = sub_sections[j+1] if j+1 < len(sub_sections) else ''
            body = sub_sections[j+2] if j+2 < len(sub_sections) else ''
            clean_header = re.sub(r'<[^>]+>', '', header).strip()

            dpu_m = re.search(r'DPU[：:]*\s*([\d.]+)', body)
            if not dpu_m:
                continue

            dpu_val = float(dpu_m.group(1))

            # 3.1 油漆在线抽检 → 涂装DPU
            if ('油漆在线抽检' in clean_header or '1.2' in clean_header) and result["paint"] is None:
                result["paint"] = dpu_val
            # 4.1 巡检&抽检 → 车身DPU
            elif '巡检' in clean_header and '抽检' in clean_header and result["body"] is None:
                result["body"] = dpu_val
            # 7. 零件抽检 → 冲压DPU
            elif '零件抽检' in clean_header and result["stamp"] is None:
                result["stamp"] = dpu_val

        # 如果三种DPU都找到了就提前退出
        if all(v is not None for v in result.values()):
            break

    return result


def parse_quality(md):
    r = {"ftt": 0, "ftt_target": 85, "dpu": 0, "dpu_target": 0.15, "b_count": 0}

    # 1. 优先从callout块提取（callout里是最新汇总数据）
    for callout_match in re.finditer(r'<callout.*?/callout>', md[:30000], re.DOTALL):
        ct = callout_match.group()
        m = re.search(r'FTT[：:]*\s*([\d.]+)%.*?DPU[：:]*\s*([\d.]+)', ct, re.DOTALL)
        if m and 0 < float(m.group(1)) < 90 and 0.01 < float(m.group(2)) < 2:
            r["ftt"] = float(m.group(1))
            r["dpu"] = float(m.group(2))
            break
        m = re.search(r'DPU[：:]*\s*([\d.]+).*?FTT[：:]*\s*([\d.]+)%?', ct, re.DOTALL)
        if m and 0 < float(m.group(2)) < 90 and 0.01 < float(m.group(1)) < 2:
            r["dpu"] = float(m.group(1))
            r["ftt"] = float(m.group(2))
            break

    # 2. 从组合格式提取（FTT,DPU 或 DPU,FTT）
    if r["ftt"] == 0:
        combo2 = re.findall(r'FTT[：:]*\s*([\d.]+)%?[，,]\s*DPU[：:]*\s*([\d.]+)', md)
        combo1 = re.findall(r'DPU[：:]*\s*([\d.]+)[，,]\s*FTT[：:]*\s*([\d.]+)%?', md)
        for ftt_s, dpu_s in combo2:
            if 0 < float(ftt_s) < 90 and 0.01 < float(dpu_s) < 2:
                r["ftt"], r["dpu"] = float(ftt_s), float(dpu_s)
                break
        if r["ftt"] == 0:
            for dpu_s, ftt_s in combo1:
                if 0 < float(ftt_s) < 90 and 0.01 < float(dpu_s) < 2:
                    r["ftt"], r["dpu"] = float(ftt_s), float(dpu_s)
                    break

    m = re.search(r'B 类\s*(\d+)\s*个', md)
    if m: r["b_count"] = int(m.group(1))
    return r


def get_status_color(value, target, reverse=False):
    if reverse:
        if value <= target: return "green"
        elif value <= target * 1.2: return "yellow"
        else: return "red"
    else:
        if value >= target: return "green"
        elif value >= target * 0.9: return "yellow"
        else: return "red"


# ==================== 数据解析 ====================
try:
    raw = load_feishu_data()
except Exception:
    raw = None

# ---- 1. AUDIT ----
audit_cars = []
audit_trend = {}
all_audit = []
audit_issues_all = []

if raw:
    audit_md = raw.get("audit", {}).get("markdown", "")
    audit_dates = re.findall(r'^# (2026/\d+/\d+)\s*$', audit_md, re.MULTILINE)
    audit_sections = split_by_date(audit_md, r'^# (2026/\d+/\d+)\s*$')

    for ds, section in audit_sections:
        day = {"date": ds, "factories": {}, "ms12": None}
        subs = extract_factory_subsections(section)
        for key, content in subs.items():
            data = parse_factory_data(content)
            if data:
                day["factories"][key] = data
        ms12_m = re.search(r'MS12总体状态.*?(?=\n# 2026|\Z)', section, re.DOTALL)
        if ms12_m:
            txt = ms12_m.group(0)
            sm = re.search(r'单车分数\s*([\d.]+)', txt)
            tm = re.search(r'目标\s*(\d+)', txt)
            bm = re.search(r'B 类\s*([\d.]+)', txt)
            cm = re.search(r'C 类\s*([\d.]+)', txt)
            if sm:
                s = float(sm.group(1))
                t = int(tm.group(1)) if tm else 110
                day["ms12"] = {"score": s, "target": t, "ng": s > t,
                    "b": float(bm.group(1)) if bm else 0, "c": float(cm.group(1)) if cm else 0}
        all_audit.append(day)

    def latest_with_data(factory_key):
        for d in all_audit:
            if factory_key == "ms12":
                if d.get("ms12"): return d
            elif factory_key in d.get("factories", {}):
                return d
        return None

    # M9和一期合并: MS12就是一期/M9
    for name, key, model in [("M9/一期 (MS12)", "ms12", "MS12"), ("B1 MX11 base", "B1-base", "MX11"),
                              ("B1 MX11-9", "B1-9", "MX11-9"), ("B2 MX11", "B2", "MX11")]:
        d = latest_with_data(key)
        if d:
            f = d.get("ms12") if key == "ms12" else d["factories"].get(key)
            if f:
                audit_cars.append({"name": name, "date": d["date"], "model": model,
                    "score": f["score"], "target": f["target"], "b": f["b"], "c": f["c"], "ng": f["ng"]})

    for name, key in [("M9/一期 (MS12)", "ms12"), ("B1 MX11 base", "B1-base"), ("B1 MX11-9", "B1-9"), ("B2 MX11", "B2")]:
        dates, scores, targets, b_counts = [], [], [], []
        for d in all_audit:
            f = d.get("ms12") if key == "ms12" else d["factories"].get(key)
            if f:
                dates.append(d["date"])
                scores.append(f["score"])
                targets.append(f["target"])
                b_counts.append(f["b"])
        if dates:
            dates.reverse(); scores.reverse(); targets.reverse(); b_counts.reverse()
            audit_trend[name] = {"dates": dates, "scores": scores, "target": targets, "b_count": b_counts}

    # 提取AUDIT TOP问题 (近3天)
    audit_issues_all = extract_audit_issues_from_bitable(audit_md, audit_dates, limit_per_day=5)

if not audit_cars:
    fb = get_fallback_data()
    audit_cars = fb["audit_cars"]
    audit_trend = fb["audit_trend"]
    audit_issues_all = fb["audit_issues"]

# ---- 2. 全功能评审 ----
func_daily = []
func_issues_all = []
if raw:
    func_md = raw.get("func_review", {}).get("markdown", "")
    func_sections = split_by_date(func_md, r'^# (2026[\.\s]+\d+\.\d+)\s*$')
    for ds, section in func_sections:
        date_str = ds.replace('.', '/').replace(' ', '')
        day = {"date": date_str, "models": [], "issues": []}
        ms12_m = re.search(r'MS12.*?评审\s*(\d+)\s*台.*?B类\s*(\d+)\s*项.*?C类\s*(\d+)\s*项.*?单车B类及以上缺陷率\s*([\d.]+).*?([\d.]+)\s*目标', section, re.DOTALL)
        if ms12_m:
            rate = float(ms12_m.group(4))
            target = float(ms12_m.group(5))
            day["models"].append({"model": "MS12", "count": int(ms12_m.group(1)),
                "b": int(ms12_m.group(2)), "c": int(ms12_m.group(3)),
                "rate": rate, "target": target, "ng": rate > target})
        tables = re.findall(r'<table>.*?<tbody>(.*?)</tbody>.*?</table>', section, re.DOTALL)
        for tbl in tables:
            rows = re.findall(r'<tr>(.*?)</tr>', tbl, re.DOTALL)
            for row in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                cleaned = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                for i, cell in enumerate(cleaned):
                    if cell in ('S', 'A', 'B') and i >= 3:
                        issue = {"日期": date_str, "等级": cell}
                        if len(cleaned) > 1: issue["车型"] = cleaned[1]
                        if len(cleaned) > 2: issue["工厂"] = cleaned[2]
                        issue["问题描述"] = cleaned[i+1] if i+1 < len(cleaned) else ""
                        if i+2 < len(cleaned): issue["新增/复发"] = cleaned[i+2]
                        day["issues"].append(issue)
                        break
        func_daily.append(day)
    for d in func_daily[:7]:
        for iss in d.get("issues", []):
            func_issues_all.append(iss)
if not func_daily:
    fb = get_fallback_data()
    func_issues_all = fb["func_issues"]

# ---- 3. 整车质量 ----
q_m9 = {"ftt": 0, "ftt_target": 85, "dpu": 0, "dpu_target": 0.15, "b_count": 0}
q_b1 = {"ftt": 0, "ftt_target": 85, "dpu": 0, "dpu_target": 0.15, "b_count": 0}
q_b2 = {"ftt": 0, "ftt_target": 85, "dpu": 0, "dpu_target": 0.15, "b_count": 0}
quality_issues = []

if raw:
    q_m9 = parse_quality(raw.get("quality_m9", {}).get("markdown", ""))
    q_b1 = parse_quality(raw.get("quality_b1", {}).get("markdown", ""))
    q_b2 = parse_quality(raw.get("quality_b2", {}).get("markdown", ""))
    quality_issues = extract_quality_issues(raw)

if not quality_issues:
    fb = get_fallback_data()
    quality_issues = fb["quality_issues"]

# ---- 4. 过程质量 ----
paint_audit_trend = {"dates": [], "scores": [], "target": 36}
body_audit_trend = {"dates": [], "scores": [], "target": 29}
paint_issues = []
body_issues = []
stamp_issues = []
process_dpu = {"paint": None, "body": None, "stamp": None}
die_summary = []
color_match = []
latest_proc_date = ""

if raw:
    proc_md = raw.get("process", {}).get("markdown", "")
    proc_sections_list = split_by_date(proc_md, r'^# (\d+/\d+(?:夜班|白班|))\s*$')

    for ds, section in proc_sections_list:
        pm = re.search(r'(?:油漆|面漆)audit.*?目标分数[：:]\s*(\d+)\s*实际分数[：:]\s*(\d+)', section, re.DOTALL)
        if pm:
            paint_audit_trend["dates"].append(ds)
            paint_audit_trend["scores"].append(int(pm.group(2)))
            paint_audit_trend["target"] = int(pm.group(1))
        bm = re.search(r'车身audit.*?目标分数[：:]\s*(\d+)\s*实际分数[：:]\s*(\d+)', section, re.DOTALL)
        if bm:
            body_audit_trend["dates"].append(ds)
            body_audit_trend["scores"].append(int(bm.group(2)))
            body_audit_trend["target"] = int(bm.group(1))

    paint_audit_trend["dates"].reverse(); paint_audit_trend["scores"].reverse()
    body_audit_trend["dates"].reverse(); body_audit_trend["scores"].reverse()

    latest_proc_date = proc_sections_list[0][0] if proc_sections_list else ""
    latest_proc = proc_sections_list[0][1] if proc_sections_list else ""

    # DPU按段落精确提取
    process_dpu = extract_process_dpu(proc_md)

    # 涂装AUDIT问题
    paint_audit_idx = latest_proc.find('油漆audit业务')
    if paint_audit_idx < 0:
        paint_audit_idx = latest_proc.find('油漆AUDIT')
    if paint_audit_idx >= 0:
        paint_sec = latest_proc[paint_audit_idx:paint_audit_idx+3000]
        paint_issues = extract_html_issues_from_section(paint_sec, limit=10)

    # 车身AUDIT问题
    body_audit_idx = latest_proc.find('AUDIT业务')
    if body_audit_idx >= 0:
        body_sec = latest_proc[body_audit_idx:body_audit_idx+3000]
        body_issues = extract_html_issues_from_section(body_sec, limit=10)

    # 冲压问题
    stamp_idx = latest_proc.find('冲压质量抽检')
    if stamp_idx < 0:
        stamp_idx = latest_proc.find('冲压巡检')
    if stamp_idx >= 0:
        stamp_sec = latest_proc[stamp_idx:stamp_idx+5000]
        stamp_issues = extract_html_issues_from_section(stamp_sec, limit=10)

    # 压铸
    die_idx = latest_proc.find('压铸质量抽检')
    if die_idx >= 0:
        die_section = latest_proc[die_idx:die_idx+3000]
        for line in die_section.split('\n'):
            if '完成' in line and '抽检' in line:
                clean = re.sub(r'\*+', '', line).strip()
                if clean: die_summary.append(clean)

    # 色差匹配
    color_match = [
        {"颜色": "靛石绿", "一期": "OK", "B2": "-"}, {"颜色": "嫣格粉", "一期": "OK", "B2": "-"},
        {"颜色": "迷雾紫", "一期": "OK", "B2": "-"}, {"颜色": "熔岩红", "一期": "OK", "B2": "-"},
        {"颜色": "武士黑", "一期": "OK", "B2": "-"}, {"颜色": "雅灰", "一期": "OK", "B2": "-"},
        {"颜色": "卡布里蓝", "一期": "OK", "B2": "-"}, {"颜色": "珍珠白", "一期": "OK", "B2": "-"},
        {"颜色": "钛金属", "一期": "-", "B2": "OK"}, {"颜色": "火山灰", "一期": "-", "B2": "OK"},
    ]

if not color_match:
    fb = get_fallback_data()
    color_match = fb["color_match"]
    if not paint_issues: paint_issues = fb["issues_paint"]
    if not body_issues: body_issues = fb["issues_body"]


# ==================== 辅助渲染 ====================
def render_metric_card(title, value, target=None, unit="", status="green", sub_text=""):
    target_html = f'<div class="card-target">目标: {target}{unit}</div>' if target else ''
    sub_html = f'<div class="card-sub">{sub_text}</div>' if sub_text else ''
    # unit字号缩小，保持协调
    unit_html = f'<span style="font-size:16px;font-weight:500;color:#94a3b8;">{unit}</span>' if unit else ''
    st.markdown(f'''
    <div class="status-card {status}">
        <div class="card-title">{title}</div>
        <div class="card-value {status}"><span>{value}</span>{unit_html}</div>
        {target_html}{sub_html}
    </div>
    ''', unsafe_allow_html=True)


def render_issue_table_html(issues, max_rows=10):
    """统一风格的问题表格"""
    if not issues:
        st.info("暂无数据")
        return
    rows_html = ""
    for iss in issues[:max_rows]:
        level = iss.get("等级", "")
        level_cls = f"level-{level}" if level in ('S','A','B','C') else ""
        desc = iss.get("问题描述", iss.get("问题", ""))
        rows_html += f'''<tr>
            <td>{iss.get("日期", "")}</td>
            <td class="{level_cls}">{level}</td>
            <td>{desc[:60]}</td>
            <td>{iss.get("车型", iss.get("工厂", ""))}</td>
            <td>{iss.get("频次", iss.get("升级原因", ""))}</td>
            <td>{iss.get("责任人", iss.get("责任部门", ""))}</td>
        </tr>'''
    st.markdown(f'''<table class="issue-table">
        <thead><tr><th>日期</th><th>等级</th><th>问题描述</th><th>车型/工厂</th><th>频次/原因</th><th>责任人</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>''', unsafe_allow_html=True)


def create_trend_chart(dates, values, target, title="", color=C["blue"], y_title=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, mode='lines+markers', name='实际',
        line=dict(color=color, width=3), marker=dict(size=8, color=color),
        fill='tozeroy', fillcolor=f'rgba(96,165,250,0.08)'
    ))
    if target:
        fig.add_hline(y=target, line_dash="dash", line_color=C["yellow"],
                      annotation_text=f"目标 {target}", annotation_position="top right")
    fig.update_layout(
        height=280, margin=dict(l=40, r=20, t=30, b=30),
        plot_bgcolor=C["plotly_bg"], paper_bgcolor=C["plotly_bg"],
        font=dict(color=C["text_sub"]),
        xaxis=dict(gridcolor=C["grid"], showgrid=True),
        yaxis=dict(gridcolor=C["grid"], showgrid=True, title=y_title),
        title=dict(text=title, font=dict(color=C["text"], size=16)),
        showlegend=False
    )
    return fig


def create_bar_chart(dates, values, target, title="", y_title=""):
    colors = [C["green"] if v <= target else C["red"] for v in values]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=values, marker_color=colors, text=values, textposition="auto", marker_line_width=0, opacity=0.85))
    fig.add_hline(y=target, line_dash="dash", line_color=C["yellow"],
                  annotation_text=f"目标 {target}", annotation_position="top right")
    fig.update_layout(
        height=280, margin=dict(l=40, r=20, t=30, b=30),
        plot_bgcolor=C["plotly_bg"], paper_bgcolor=C["plotly_bg"],
        font=dict(color=C["text_sub"]),
        xaxis=dict(gridcolor=C["grid"], showgrid=True),
        yaxis=dict(gridcolor=C["grid"], showgrid=True, title=y_title),
        title=dict(text=title, font=dict(color=C["text"], size=16)),
        showlegend=False
    )
    return fig


# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown('''<div style="padding:8px 0 4px;">
        <div style="display:flex;align-items:center;gap:14px;padding:16px 12px;
            background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.05));
            border-radius:16px;border:1px solid rgba(99,102,241,0.15);">
            <div style="width:44px;height:44px;border-radius:12px;
                background:linear-gradient(135deg,#6366f1,#8b5cf6);
                display:flex;align-items:center;justify-content:center;
                font-size:22px;box-shadow:0 4px 12px rgba(99,102,241,0.3);">🏭</div>
            <div>
                <div style="color:#e2e8f0;font-size:16px;font-weight:700;letter-spacing:0.5px;">质量运营看板</div>
                <div style="color:#818cf8;font-size:11px;font-weight:500;margin-top:2px;">QUALITY OPS DASHBOARD</div>
            </div>
        </div>
    </div>''', unsafe_allow_html=True)

    st.markdown('''<div style="padding:12px 4px 6px;">
        <div style="color:#64748b;font-size:11px;font-weight:600;text-transform:uppercase;
            letter-spacing:1.5px;padding:0 12px;">导航菜单</div>
    </div>''', unsafe_allow_html=True)

    page = st.radio("导航", ["首页总览", "AUDIT详情", "全功能评审", "整车质量", "过程质量", "TOP问题"], label_visibility="collapsed")

    st.markdown("---")

    # 状态概览
    st.markdown('''<div style="padding:4px 12px;">
        <div style="color:#64748b;font-size:11px;font-weight:600;text-transform:uppercase;
            letter-spacing:1.5px;margin-bottom:12px;">系统状态</div>
    </div>''', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f'''<div style="text-align:center;padding:12px 8px;
            background:rgba(30,41,59,0.5);border-radius:12px;border:1px solid #334155;">
            <div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:1px;">更新时间</div>
            <div style="color:#e2e8f0;font-size:13px;font-weight:600;margin-top:4px;">{datetime.now().strftime("%H:%M")}</div>
            <div style="color:#94a3b8;font-size:11px;">{datetime.now().strftime("%m/%d")}</div>
        </div>''', unsafe_allow_html=True)
    with col_b:
        st.markdown(f'''<div style="text-align:center;padding:12px 8px;
            background:rgba(30,41,59,0.5);border-radius:12px;border:1px solid #334155;">
            <div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:1px;">数据源</div>
            <div style="color:#4ade80;font-size:13px;font-weight:600;margin-top:4px;">在线</div>
            <div style="color:#94a3b8;font-size:11px;">飞书同步</div>
        </div>''', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    if st.button("刷新数据", width="stretch"):
        st.cache_data.clear()
        st.rerun()


# ==================== 页面渲染 ====================

# ---- 首页总览 ----
if page == "首页总览":
    st.markdown('''<div class="top-bar">
        <h1>质量运营看板</h1>
        <div class="sub">Quality Operations Dashboard · 北京工厂 · 实时数据驱动质量管理</div>
    </div>''', unsafe_allow_html=True)

    st.markdown("### 整体质量状态")
    col1, col2, col3, col4 = st.columns(4)

    # 按工厂去重：M9/一期=1个, B1(base+9)=1个, B2=1个
    factory_status = {}
    for c in audit_cars:
        if "M9" in c["name"] or "一期" in c["name"]:
            fk = "M9/一期"
        elif "B1" in c["name"]:
            fk = "B1"
        else:
            fk = "B2"
        # 同工厂只要有一个车型未达标，该工厂就未达标
        if fk not in factory_status or c["ng"]:
            factory_status[fk] = c["ng"]
    total_factories = len(factory_status)
    ng_count = sum(1 for v in factory_status.values() if v)
    overall_status = "green" if ng_count == 0 else "yellow" if ng_count <= 1 else "red"

    with col1:
        render_metric_card("AUDIT达标率", f"{total_factories - ng_count}/{total_factories}",
                          status=overall_status, sub_text=f"{ng_count}个工厂未达标")
    with col2:
        ftt_vals = [q_m9["ftt"], q_b1["ftt"], q_b2["ftt"]]
        ftt_avg = sum(v for v in ftt_vals if v > 0) / max(1, sum(1 for v in ftt_vals if v > 0))
        render_metric_card("平均FTT", f"{ftt_avg:.1f}", target=85, unit="%", status=get_status_color(ftt_avg, 85))
    with col3:
        dpu_vals = [q_m9["dpu"], q_b1["dpu"], q_b2["dpu"]]
        dpu_avg = sum(v for v in dpu_vals if v > 0) / max(1, sum(1 for v in dpu_vals if v > 0))
        render_metric_card("平均DPU", f"{dpu_avg:.3f}", target=0.15, status=get_status_color(dpu_avg, 0.15, reverse=True))
    with col4:
        total_issues = len(quality_issues) + len(audit_issues_all) + len(func_issues_all)
        render_metric_card("活跃问题", str(total_issues), unit="个", status="yellow" if total_issues > 10 else "green",
                          sub_text="AUDIT+全功能+整车")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 各工厂质量状态")
    cols = st.columns(len(audit_cars) if audit_cars else 4)
    for i, car in enumerate(audit_cars):
        with cols[i]:
            status = "green" if not car["ng"] else ("yellow" if car["score"] <= car["target"] * 1.3 else "red")
            st.markdown(f'''<div class="factory-card {status}">
                <div class="factory-name"><span class="status-dot {status}"></span>{car["name"]}</div>
                <div style="display:flex;gap:24px;align-items:baseline;">
                    <div><span class="card-value {status}" style="font-size:48px;">{car["score"]}</span><span class="card-target" style="font-size:16px;"> / {car["target"]}</span></div>
                    <span class="badge badge-{"green" if status=="green" else "yellow" if status=="yellow" else "red"}">{"达标" if status=="green" else "轻微偏离" if status=="yellow" else "未达标"}</span>
                </div>
                <div style="margin-top:16px;display:flex;gap:32px;">
                    <div><span style="color:#94a3b8;font-size:13px;">B类问题</span><br><span style="color:#fb923c;font-size:18px;font-weight:700;">{car["b"]}</span></div>
                    <div><span style="color:#94a3b8;font-size:13px;">C类问题</span><br><span style="color:#e2e8f0;font-size:18px;font-weight:700;">{car["c"]}</span></div>
                    <div><span style="color:#94a3b8;font-size:13px;">日期</span><br><span style="color:#e2e8f0;font-size:14px;">{car["date"]}</span></div>
                </div>
            </div>''', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### AUDIT趋势")
        fig = go.Figure()
        colors_list = [C["blue"], C["purple"], C["cyan"], C["orange"]]
        for idx, (name, data) in enumerate(audit_trend.items()):
            fig.add_trace(go.Scatter(x=data["dates"], y=data["scores"], mode='lines+markers',
                name=name, line=dict(color=colors_list[idx % len(colors_list)], width=2), marker=dict(size=6)))
        fig.add_hline(y=110, line_dash="dash", line_color=C["yellow"], opacity=0.5)
        fig.update_layout(height=350, margin=dict(l=40, r=20, t=20, b=30),
            plot_bgcolor=C["plotly_bg"], paper_bgcolor=C["plotly_bg"], font=dict(color=C["text_sub"]),
            xaxis=dict(gridcolor=C["grid"]), yaxis=dict(gridcolor=C["grid"], title="AUDIT分数"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color=C["text_sub"])))
        st.plotly_chart(fig, width="stretch")
    with col2:
        st.markdown("### 问题等级分布")
        if audit_issues_all:
            level_counts = {}
            for iss in audit_issues_all:
                lv = iss.get("等级", "其他")
                level_counts[lv] = level_counts.get(lv, 0) + 1
            fig_pie = go.Figure(data=[go.Pie(labels=list(level_counts.keys()), values=list(level_counts.values()),
                hole=0.6, marker=dict(colors=[C["green"], C["yellow"], C["red"], C["blue"], C["purple"]]),
                textinfo='label+percent', textfont=dict(color=C["text"], size=12))])
            fig_pie.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor=C["plotly_bg"], paper_bgcolor=C["plotly_bg"], font=dict(color=C["text_sub"]), showlegend=False)
            st.plotly_chart(fig_pie, width="stretch")

    st.markdown("### 最新风险预警")
    if quality_issues:
        for iss in quality_issues[:5]:
            st.markdown(f'''<div class="risk-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><span class="badge badge-red">{iss.get("工厂","")}</span>
                    <span style="color:#f1f5f9;font-size:14px;margin-left:8px;">{iss.get("问题描述","")}</span></div>
                    <span style="color:#94a3b8;font-size:12px;">{iss.get("升级原因","")}</span>
                </div></div>''', unsafe_allow_html=True)


# ---- AUDIT详情 ----
elif page == "AUDIT详情":
    st.markdown('''<div class="top-bar"><h1>AUDIT 详情</h1>
        <div class="sub">整车Audit精检数据 · 各工厂AUDIT状态 · TOP问题追踪</div></div>''', unsafe_allow_html=True)

    st.markdown("### 工厂AUDIT状态矩阵")
    matrix_cols = st.columns(len(audit_cars))
    for i, car in enumerate(audit_cars):
        with matrix_cols[i]:
            status = "green" if not car["ng"] else ("yellow" if car["score"] <= car["target"] * 1.3 else "red")
            st.markdown(f'''<div class="status-card {status}">
                <div class="card-title">{car["name"]}</div>
                <div class="card-value {status}">{car["score"]}</div>
                <div class="card-target">目标: {car["target"]}</div>
                <div style="margin-top:12px;"><span class="badge badge-{"green" if status=="green" else "yellow" if status=="yellow" else "red"}">{"达标" if status=="green" else "轻微偏离" if status=="yellow" else "未达标"}</span></div>
                <div class="card-sub" style="margin-top:8px;">B:{car["b"]} C:{car["c"]} · {car["date"]}</div>
            </div>''', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("### AUDIT趋势分析")
    st.markdown('<style>.stHorizontalBlock{align-items:stretch!important}</style>', unsafe_allow_html=True)
    for car_name, data in audit_trend.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            fig = create_bar_chart(data["dates"], data["scores"], data["target"][0] if data["target"] else 110, title=car_name, y_title="AUDIT分数")
            st.plotly_chart(fig, width="stretch")
        with col2:
            latest_score = data["scores"][-1] if data["scores"] else 0
            latest_target = data["target"][-1] if data["target"] else 110
            status = get_status_color(latest_score, latest_target, reverse=True)
            # 用空白撑高，与图表对齐
            st.markdown('<div style="height:40px"></div>', unsafe_allow_html=True)
            render_metric_card("最新分数", f"{latest_score}", target=latest_target, status=status,
                              sub_text=f"B类: {data['b_count'][-1] if data['b_count'] else 0}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### AUDIT TOP问题 (近3天)")
    render_issue_table_html(audit_issues_all, max_rows=15)


# ---- 全功能评审 ----
elif page == "全功能评审":
    st.markdown('''<div class="top-bar"><h1>全功能评审</h1>
        <div class="sub">全功能评审状态 · 缺陷率趋势 · 重点问题追踪</div></div>''', unsafe_allow_html=True)

    if func_daily and func_daily[0].get("models"):
        latest = func_daily[0]
        st.markdown(f"### 最新评审状态 ({latest['date']})")
        for model in latest["models"]:
            status = "green" if not model.get("ng") else "red"
            c1, c2, c3, c4 = st.columns(4)
            with c1: render_metric_card("评审台数", str(model.get("count", 0)), status="green", sub_text="MS12")
            with c2: render_metric_card("B类问题", str(model.get("b", 0)), status="yellow" if model.get("b", 0) > 0 else "green", sub_text="重点关注")
            with c3: render_metric_card("C类问题", str(model.get("c", 0)), status="green", sub_text="一般问题")
            with c4: render_metric_card("缺陷率", f"{model.get('rate', 0):.2f}", status=status, sub_text=f"目标≤{model.get('target', 0.4)} · B类/台")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 全功能评审重点问题")
    render_issue_table_html(func_issues_all, max_rows=20)


# ---- 整车质量 ----
elif page == "整车质量":
    st.markdown('''<div class="top-bar"><h1>整车质量</h1>
        <div class="sub">FTT一次通过率 · DPU单车缺陷数 · 各工厂质量状态</div></div>''', unsafe_allow_html=True)

    st.markdown("### 各工厂FTT/DPU状态")

    # 完整表格一次性渲染，避免Streamlit拆分导致错位
    ftt_dpu_rows = ""
    for qdata, qname in [(q_m9, "M9/一期"), (q_b1, "B1"), (q_b2, "B2")]:
        ftt_s = get_status_color(qdata["ftt"], qdata["ftt_target"])
        dpu_s = get_status_color(qdata["dpu"], qdata["dpu_target"], reverse=True)
        ftt_badge = f'<span class="badge badge-{ftt_s}">{"达标" if ftt_s=="green" else "未达标"}</span>'
        dpu_badge = f'<span class="badge badge-{dpu_s}">{"达标" if dpu_s=="green" else "未达标"}</span>'
        ftt_dpu_rows += f'''<tr>
            <td><b>{qname}</b></td>
            <td style="color:#{"4ade80" if ftt_s=="green" else "fbbf24" if ftt_s=="yellow" else "f87171"};font-weight:700;font-size:15px;">{qdata["ftt"]:.1f}%</td>
            <td>{qdata["ftt_target"]}%</td><td>{ftt_badge}</td>
            <td style="color:#{"4ade80" if dpu_s=="green" else "fbbf24" if dpu_s=="yellow" else "f87171"};font-weight:700;font-size:15px;">{qdata["dpu"]:.3f}</td>
            <td>{qdata["dpu_target"]}</td><td>{dpu_badge}</td>
            <td>{qdata["b_count"]}</td>
        </tr>'''

    st.markdown(f'''<table class="issue-table">
        <thead><tr><th>工厂</th><th>FTT当前值</th><th>FTT目标</th><th>FTT状态</th><th>DPU当前值</th><th>DPU目标</th><th>DPU状态</th><th>B类问题</th></tr></thead>
        <tbody>{ftt_dpu_rows}</tbody></table>''', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # FTT/DPU趋势图
    st.markdown("### 趋势分析")
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        factory_colors = {"M9/一期": C["blue"], "B1": C["purple"], "B2": C["cyan"]}
        for qdata, qname in [(q_m9, "M9/一期"), (q_b1, "B1"), (q_b2, "B2")]:
            if qdata["ftt"] > 0:
                fig.add_trace(go.Scatter(x=[qname], y=[qdata["ftt"]], mode='markers+text',
                    marker=dict(size=20, color=factory_colors.get(qname, C["blue"])),
                    text=[f'{qdata["ftt"]:.1f}%'], textposition='top center', name=qname))
        fig.add_hline(y=85, line_dash="dash", line_color=C["yellow"], annotation_text="目标85%")
        fig.update_layout(height=300, margin=dict(l=40, r=20, t=30, b=30),
            plot_bgcolor=C["plotly_bg"], paper_bgcolor=C["plotly_bg"], font=dict(color=C["text_sub"]),
            xaxis=dict(gridcolor=C["grid"]), yaxis=dict(gridcolor=C["grid"], title="FTT%", range=[70, 100]),
            title=dict(text="FTT对比", font=dict(color=C["text"], size=16)), showlegend=False)
        st.plotly_chart(fig, width="stretch")
    with col2:
        fig = go.Figure()
        for qdata, qname in [(q_m9, "M9/一期"), (q_b1, "B1"), (q_b2, "B2")]:
            if qdata["dpu"] > 0:
                fig.add_trace(go.Scatter(x=[qname], y=[qdata["dpu"]], mode='markers+text',
                    marker=dict(size=20, color=factory_colors.get(qname, C["blue"])),
                    text=[f'{qdata["dpu"]:.3f}'], textposition='top center', name=qname))
        fig.add_hline(y=0.15, line_dash="dash", line_color=C["yellow"], annotation_text="目标0.15")
        fig.update_layout(height=300, margin=dict(l=40, r=20, t=30, b=30),
            plot_bgcolor=C["plotly_bg"], paper_bgcolor=C["plotly_bg"], font=dict(color=C["text_sub"]),
            xaxis=dict(gridcolor=C["grid"]), yaxis=dict(gridcolor=C["grid"], title="DPU"),
            title=dict(text="DPU对比", font=dict(color=C["text"], size=16)), showlegend=False)
        st.plotly_chart(fig, width="stretch")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 重点升级问题")
    render_issue_table_html(quality_issues, max_rows=15)


# ---- 过程质量 ----
elif page == "过程质量":
    st.markdown('''<div class="top-bar"><h1>过程质量</h1>
        <div class="sub">车身/涂装AUDIT · 巡检抽检状态 · DPU趋势 · 色差匹配</div></div>''', unsafe_allow_html=True)

    st.markdown("### 车身/涂装AUDIT状态")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 涂装AUDIT")
        if paint_audit_trend["dates"]:
            st.plotly_chart(create_bar_chart(paint_audit_trend["dates"], paint_audit_trend["scores"],
                paint_audit_trend["target"], y_title="分数"), width="stretch")
            latest_val = paint_audit_trend["scores"][-1]
            render_metric_card("最新涂装AUDIT", str(latest_val), target=paint_audit_trend["target"],
                              status=get_status_color(latest_val, paint_audit_trend["target"], reverse=True))
        else:
            st.info("暂无涂装AUDIT数据")
    with col2:
        st.markdown("#### 车身AUDIT")
        if body_audit_trend["dates"]:
            st.plotly_chart(create_bar_chart(body_audit_trend["dates"], body_audit_trend["scores"],
                body_audit_trend["target"], y_title="分数"), width="stretch")
            latest_val = body_audit_trend["scores"][-1]
            render_metric_card("最新车身AUDIT", str(latest_val), target=body_audit_trend["target"],
                              status=get_status_color(latest_val, body_audit_trend["target"], reverse=True))
        else:
            st.info("暂无车身AUDIT数据")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # DPU总览
    st.markdown("### 巡检DPU状态")
    dpu_cols = st.columns(3)
    dpu_items = [
        ("涂装DPU", process_dpu["paint"], "3.1 油漆在线抽检"),
        ("车身DPU", process_dpu["body"], "4.1 巡检&抽检"),
        ("冲压DPU", process_dpu["stamp"], "7. 零件抽检"),
    ]
    for i, (label, val, source) in enumerate(dpu_items):
        with dpu_cols[i]:
            if val is not None:
                ok = val <= 0.05
                render_metric_card(label, f"{val:.3f}", target=0.05,
                                  status="green" if ok else "red", sub_text=f"来源: {source}")
            else:
                render_metric_card(label, "暂无", status="green", sub_text=f"来源: {source}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # 巡检详情
    st.markdown("### 巡检抽检动态")
    t_paint, t_body, t_stamp, t_die = st.tabs(["涂装", "车身", "冲压", "压铸"])

    with t_paint:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**色差匹配进展**")
            if color_match:
                cm_rows = ""
                for cm in color_match:
                    def _badge(v):
                        if v == "OK": return f'<span class="badge badge-green">OK</span>'
                        elif v == "NG": return f'<span class="badge badge-red">NG</span>'
                        else: return f'<span style="color:#64748b;">{v}</span>'
                    cm_rows += f'<tr><td><b>{cm["颜色"]}</b></td><td>{_badge(cm.get("一期",""))}</td><td>{_badge(cm.get("B2",""))}</td></tr>'
                st.markdown(f'''<table class="issue-table">
                    <thead><tr><th>颜色</th><th>一期/M9</th><th>B2</th></tr></thead>
                    <tbody>{cm_rows}</tbody></table>''', unsafe_allow_html=True)
        with col2:
            st.markdown("**涂装TOP问题**")
            render_issue_table_html(paint_issues, max_rows=5)

    with t_body:
        st.markdown("**车身TOP问题**")
        render_issue_table_html(body_issues, max_rows=10)

    with t_stamp:
        st.markdown("**冲压TOP问题**")
        render_issue_table_html(stamp_issues, max_rows=10)

    with t_die:
        st.markdown("**压铸巡检状态**")
        if die_summary:
            for item in die_summary:
                st.markdown(f'''<div style="padding:8px 16px;background:#1e293b;border-radius:8px;margin-bottom:8px;border-left:3px solid {C['green']};">
                    <span style="color:{C['green']};">✓</span>
                    <span style="color:{C['text']};font-size:14px;margin-left:8px;">{item}</span>
                </div>''', unsafe_allow_html=True)
        else:
            st.markdown('''<div class="status-card green">
                <div class="card-title">压铸业务范围</div>
                <div class="card-sub">铝液成分 · 铝锭来料 · 机械性能 · X-RAY · 毛坯外观 · 机加抽检</div>
            </div>''', unsafe_allow_html=True)


# ---- TOP问题 ----
elif page == "TOP问题":
    st.markdown('''<div class="top-bar"><h1>TOP问题追踪</h1>
        <div class="sub">跨工厂 · 跨模块 · 风险问题汇总 · 关闭状态追踪</div></div>''', unsafe_allow_html=True)

    all_issues = []
    for iss in quality_issues: all_issues.append({**iss, "来源": "整车质量"})
    for iss in audit_issues_all: all_issues.append({**iss, "来源": "AUDIT"})
    for iss in func_issues_all: all_issues.append({**iss, "来源": "全功能评审"})
    for iss in paint_issues: all_issues.append({**iss, "来源": "涂装"})
    for iss in body_issues: all_issues.append({**iss, "来源": "车身"})

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("问题总数", f"{len(all_issues)}个", status="yellow" if len(all_issues) > 10 else "green")
    with c2: render_metric_card("S类", str(sum(1 for i in all_issues if i.get("等级") == "S")), status="red")
    with c3: render_metric_card("A类", str(sum(1 for i in all_issues if i.get("等级") == "A")), status="red")
    with c4: render_metric_card("B类", str(sum(1 for i in all_issues if i.get("等级") == "B")), status="yellow")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 问题来源分布")
        source_counts = {}
        for iss in all_issues:
            src = iss.get("来源", "其他")
            source_counts[src] = source_counts.get(src, 0) + 1
        if source_counts:
            fig = go.Figure(data=[go.Pie(labels=list(source_counts.keys()), values=list(source_counts.values()),
                hole=0.6, marker=dict(colors=[C["blue"], C["purple"], C["cyan"], C["orange"], C["green"]]),
                textinfo='label+percent', textfont=dict(color=C["text"], size=12))])
            fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor=C["plotly_bg"], paper_bgcolor=C["plotly_bg"], font=dict(color=C["text_sub"]), showlegend=False)
            st.plotly_chart(fig, width="stretch")
    with col2:
        st.markdown("### 问题列表")
        render_issue_table_html(all_issues, max_rows=30)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 高风险问题详情")
    high_risk = [i for i in all_issues if i.get("等级") in ("S", "A")]
    if high_risk:
        for iss in high_risk:
            st.markdown(f'''<div class="risk-card {"medium" if iss.get("等级") == "A" else ""}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><span class="badge badge-red">{iss.get("等级","")}类</span>
                    <span class="badge badge-yellow" style="margin-left:4px;">{iss.get("来源","")}</span>
                    <span style="color:#f1f5f9;font-size:14px;margin-left:8px;">{iss.get("问题描述", iss.get("问题",""))}</span></div>
                    <span style="color:#94a3b8;font-size:12px;">{iss.get("工厂","")} · {iss.get("车型","")}</span>
                </div></div>''', unsafe_allow_html=True)
    else:
        st.success("当前无S/A类高风险问题")
