"""Tab渲染代码 - 被app.py导入"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import re
import json
import os
import subprocess
import traceback as _tb


def render_tabs(tab1, tab2, tab3, tab4, tab5, C, audit_cars, audit_trend, audit_sections,
                func_daily, quality_issues, q_m9, q_b1, q_b2,
                paint_audit_trend, body_audit_trend, paint_issues, body_issues,
                stamp_issues, stamp_dpu, die_summary, latest_proc_date,
                color_match, body_dpu=None):

    # ========== Tab1: 整体概况 ==========
    with tab1:
        try:
            st.markdown("### 整体质量概况")
            if audit_cars:
                col1, col2 = st.columns(2)
                for i, card in enumerate(audit_cars):
                    with col1 if i % 2 == 0 else col2:
                        cls = "card-ng" if card["ng"] else "card-ok"
                        score_cls = "score-ng" if card["ng"] else "score-ok"
                        tag_cls = "tag-ng" if card["ng"] else "tag-ok"
                        status = "未达标" if card["ng"] else "达标"
                        st.markdown(f"""
                        <div class="card {cls}">
                            <h4 style="color:{C['text']};">{card['name']}</h4>
                            <p><span class="score-big {score_cls}">{card['score']}</span>
                            <span style="color:{C['sub']};font-size:16px;">分 / 目标 {card['target']}</span>
                            <span class="tag {tag_cls}" style="margin-left:12px;">{status}</span>
                            <span style="color:{C['sub']};font-size:12px;margin-left:8px;">({card['date']})</span></p>
                            <p>B类：<b style="color:{C['orange']};">{card['b']}</b>个 &nbsp;|&nbsp;
                            C类：<b>{card['c']}</b>个</p>
                            <div class="summary-box"><p style="margin:0;font-size:13px;color:{C['sub']};">📋 {card['detail']}</p></div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("AUDIT数据加载中...")
        except Exception as e:
            st.error(f"Tab1错误: {type(e).__name__}: {e}")
            st.code(_tb.format_exc())

    # ========== Tab2: 整车AUDIT ==========
    with tab2:
        try:
            st.markdown("### 整车AUDIT趋势")
            for car, data in audit_trend.items():
                st.markdown(f"#### {car}")
                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=data["dates"], y=data["scores"],
                        marker_color=[C["green"] if s <= t else C["red"] for s, t in zip(data["scores"], data["target"])],
                        text=data["scores"], textposition="auto", name="AUDIT分数", marker_line_width=0, opacity=0.85))
                    fig.add_trace(go.Scatter(x=data["dates"], y=data["target"],
                        mode="lines", line=dict(color=C["orange"], width=2, dash="dash"), name="目标"))
                    fig.update_layout(height=280, margin=dict(l=40, r=20, t=20, b=30), plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(gridcolor="#f1f5f9"), yaxis=dict(gridcolor="#f1f5f9", title="分数"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)))
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(x=data["dates"], y=data["b_count"],
                        marker_color=C["indigo"], text=data["b_count"], textposition="auto", marker_line_width=0, opacity=0.85))
                    fig2.update_layout(height=280, margin=dict(l=40, r=20, t=20, b=30), plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(gridcolor="#f1f5f9"), yaxis=dict(gridcolor="#f1f5f9", title="B类数量"), showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)
                st.markdown("---")

            st.markdown("### AUDIT TOP问题")
            _issues = []
            FEISHU_CMD = os.path.join(os.environ.get("APPDATA", ""), "npm", "feishu.cmd")
            for ds, sec in audit_sections[:7]:
                for tid, atok in re.findall(r'<bitable table-id="(.*?)" token="(.*?)"', sec):
                    try:
                        r = subprocess.run(f'"{FEISHU_CMD}" bitable records {atok} {tid} --page-size 10',
                            capture_output=True, timeout=15, shell=True)
                        d = json.loads(r.stdout.decode("utf-8", errors="replace"))
                        for rec in d.get("records", []):
                            f = rec.get("fields", {})
                            _issues.append({
                                "日期": ds,
                                "问题描述": str(f.get("问题描述") or ""),
                                "等级": str(f.get("问题权重") or ""),
                                "车号": str(f.get("车号") or ""),
                                "问题类型": str(f.get("问题类型") or ""),
                                "责任部门": ", ".join(f.get("责任部门", [])) if isinstance(f.get("责任部门"), list) else str(f.get("责任部门", "")),
                            })
                    except:
                        pass
            if _issues:
                st.dataframe(pd.DataFrame(_issues).fillna(""), use_container_width=True, hide_index=True)
            else:
                st.info("近期AUDIT精检无重点问题")
        except Exception as e:
            st.error(f"Tab2错误: {type(e).__name__}: {e}")
            st.code(_tb.format_exc())

    # ========== Tab3: 全功能评审 ==========
    with tab3:
        try:
            st.markdown("### 全功能评审状态")
            if func_daily:
                latest_func = func_daily[0]
                if latest_func.get("models"):
                    for model in latest_func["models"]:
                        tag_cls = "tag-ng" if model.get("ng") else "tag-ok"
                        status = "未达标" if model.get("ng") else "达标"
                        st.markdown(f"""
                        <div class="card {'card-ng' if model.get('ng') else 'card-ok'}">
                            <h4 style="color:{C['text']};">MS12 全功能评审 <span style="color:{C['sub']};font-size:12px;">({latest_func['date']})</span></h4>
                            <p>评审 <b>{model.get('count', 0)}</b> 台 &nbsp;|&nbsp;
                            B类 <b style="color:{C['orange']};">{model.get('b', 0)}</b> 项 &nbsp;|&nbsp;
                            C类 <b>{model.get('c', 0)}</b> 项</p>
                            <p><span class="score-big {'score-ng' if model.get('ng') else 'score-ok'}">{model.get('rate', 0):.2f}</span>
                            <span style="color:{C['sub']};font-size:16px;"> / 目标 {model.get('target', 0):.2f}</span>
                            <span class="tag {tag_cls}" style="margin-left:12px;">{status}</span></p>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("### 重点问题")
                all_fi = []
                for d in func_daily[:7]:
                    for iss in d.get("issues", []):
                        all_fi.append(iss)
                if all_fi:
                    cols = ["日期", "等级", "问题", "车型", "工厂"]
                    avail = [c for c in cols if c in all_fi[0]]
                    st.dataframe(pd.DataFrame(all_fi)[avail].fillna(""), use_container_width=True, hide_index=True)
                else:
                    st.info("近期无B类及以上重点问题")
            else:
                st.warning("全功能评审数据加载中...")
        except Exception as e:
            st.error(f"Tab3错误: {type(e).__name__}: {e}")
            st.code(_tb.format_exc())

    # ========== Tab4: 整车质量 ==========
    with tab4:
        try:
            st.markdown("### 整车FTT和DPU")
            col1, col2, col3 = st.columns(3)
            for i, (qdata, qname) in enumerate([(q_m9, "M9"), (q_b1, "B1"), (q_b2, "B2")]):
                with [col1, col2, col3][i]:
                    ftt_cls = "card-ok" if qdata["ftt"] >= qdata["ftt_target"] else "card-ng"
                    dpu_cls = "card-ok" if qdata["dpu"] <= qdata["dpu_target"] else "card-ng"
                    st.markdown(f"""
                    <div class="card {ftt_cls}" style="margin-bottom:8px;">
                        <h4 style="color:{C['text']};">{qname} FTT</h4>
                        <p><span class="score-big {'score-ok' if qdata['ftt']>=qdata['ftt_target'] else 'score-ng'}">{qdata['ftt']:.1f}%</span>
                        <span style="color:{C['sub']};font-size:14px;"> / 目标 {qdata['ftt_target']}%</span></p>
                    </div>
                    <div class="card {dpu_cls}">
                        <h4 style="color:{C['text']};">{qname} DPU</h4>
                        <p><span class="score-big {'score-ok' if qdata['dpu']<=qdata['dpu_target'] else 'score-ng'}">{qdata['dpu']:.3f}</span>
                        <span style="color:{C['sub']};font-size:14px;"> / 目标 {qdata['dpu_target']}</span></p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 重点升级问题")
            if quality_issues:
                cols = ["工厂", "问题描述", "升级原因", "责任部门"]
                avail = [c for c in cols if c in quality_issues[0]]
                st.dataframe(pd.DataFrame(quality_issues)[avail].fillna(""), use_container_width=True, hide_index=True)
            else:
                st.info("近期无重点升级问题")
        except Exception as e:
            st.error(f"Tab4错误: {type(e).__name__}: {e}")
            st.code(_tb.format_exc())

    # ========== Tab5: 过程质量 ==========
    with tab5:
        try:
            st.markdown("### 车身/涂装AUDIT趋势")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 涂装AUDIT")
                if paint_audit_trend["dates"]:
                    fig_p = go.Figure()
                    colors = [C["green"] if s <= paint_audit_trend["target"] else C["red"] for s in paint_audit_trend["scores"]]
                    fig_p.add_trace(go.Bar(x=paint_audit_trend["dates"], y=paint_audit_trend["scores"],
                        marker_color=colors, text=paint_audit_trend["scores"], textposition="auto", marker_line_width=0, opacity=0.85))
                    fig_p.add_hline(y=paint_audit_trend["target"], line_dash="dash", line_color=C["red"], annotation_text=f"目标 {paint_audit_trend['target']}")
                    fig_p.update_layout(height=280, margin=dict(l=40, r=20, t=20, b=30), plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(gridcolor="#f1f5f9", tickangle=-30), yaxis=dict(gridcolor="#f1f5f9", title="分数"), showlegend=False)
                    st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.info("暂无涂装AUDIT数据")
            with col2:
                st.markdown("#### 车身AUDIT")
                if body_audit_trend["dates"]:
                    fig_b = go.Figure()
                    colors = [C["green"] if s <= body_audit_trend["target"] else C["red"] for s in body_audit_trend["scores"]]
                    fig_b.add_trace(go.Bar(x=body_audit_trend["dates"], y=body_audit_trend["scores"],
                        marker_color=colors, text=body_audit_trend["scores"], textposition="auto", marker_line_width=0, opacity=0.85))
                    fig_b.add_hline(y=body_audit_trend["target"], line_dash="dash", line_color=C["red"], annotation_text=f"目标 {body_audit_trend['target']}")
                    fig_b.update_layout(height=280, margin=dict(l=40, r=20, t=20, b=30), plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(gridcolor="#f1f5f9", tickangle=-30), yaxis=dict(gridcolor="#f1f5f9", title="分数"), showlegend=False)
                    st.plotly_chart(fig_b, use_container_width=True)
                else:
                    st.info("暂无车身AUDIT数据")

            st.markdown("---")
            st.markdown("### 巡检抽检动态")
            t_p, t_b, t_s, t_c = st.tabs(["涂装", "车身", "冲压", "压铸"])

            with t_p:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**色差匹配进展**")
                    st.dataframe(pd.DataFrame(color_match), use_container_width=True, hide_index=True)
                with col2:
                    st.markdown("**涂装TOP问题**")
                    if paint_issues:
                        st.dataframe(pd.DataFrame(paint_issues).fillna(""), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂无涂装TOP问题")

            with t_b:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**车身巡检DPU**")
                    if body_dpu is not None:
                        ok = body_dpu <= 0.05
                        st.markdown(f"""
                        <div class="card {'card-ok' if ok else 'card-ng'}">
                            <p>单车DPU：<span class="score-big {'score-ok' if ok else 'score-ng'}">{body_dpu:.3f}</span>
                            &nbsp;<span class="tag {'tag-ok' if ok else 'tag-ng'}">{'达标' if ok else '未达标'}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("暂无车身DPU数据")
                with col2:
                    st.markdown("**车身TOP问题**")
                    if body_issues:
                        st.dataframe(pd.DataFrame(body_issues).fillna(""), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂无车身TOP问题")

            with t_s:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**冲压巡检DPU**")
                    if stamp_dpu is not None:
                        ok = stamp_dpu <= 0.05
                        st.markdown(f"""
                        <div class="card {'card-ok' if ok else 'card-ng'}">
                            <p>单车DPU：<span class="score-big {'score-ok' if ok else 'score-ng'}">{stamp_dpu:.3f}</span>
                            &nbsp;<span class="tag {'tag-ok' if ok else 'tag-ng'}">{'达标' if ok else '未达标'}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("暂无冲压DPU数据")
                with col2:
                    st.markdown("**冲压TOP问题**")
                    if stamp_issues:
                        st.dataframe(pd.DataFrame(stamp_issues).fillna(""), use_container_width=True, hide_index=True)
                    else:
                        st.info("暂无冲压TOP问题")

            with t_c:
                st.markdown("**压铸巡检状态**")
                if die_summary:
                    items_html = "".join([f"<p style='margin:4px 0;font-size:13px;'>✅ {item}</p>" for item in die_summary])
                    st.markdown(f"""
                    <div class="summary-box">
                        <p style="margin:0 0 8px;font-weight:600;font-size:14px;">压铸巡检结果（{latest_proc_date}）</p>
                        {items_html}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="summary-box">
                        <p style="margin:0;font-size:13px;">压铸业务：铝液成分 · 铝锭来料 · 机械性能 · X-RAY · 毛坯外观 · 机加抽检</p>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Tab5错误: {type(e).__name__}: {e}")
            st.code(_tb.format_exc())
