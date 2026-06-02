"""
飞书数据加载器 — 云端兼容版
支持Streamlit Cloud部署，直接调用飞书Open API
"""

import requests
import time
import streamlit as st

# 飞书文档URL映射
FEISHU_DOCS = {
    "audit": "https://mi.feishu.cn/wiki/UYrDwlfqpiK6ODkMfSscD5SUn8f",
    "func_review": "https://mi.feishu.cn/wiki/U2iXwxA5mi7j4VkimbUchCKUnhe",
    "quality_m9": "https://mi.feishu.cn/wiki/Cd5iwXGA2iT0VOklTGRcuEnlnGc",
    "quality_b1": "https://mi.feishu.cn/docx/PCUHdrvcBoBbj8xq81qcsmTEnVd",
    "quality_b2": "https://mi.feishu.cn/wiki/I5iVw8sQcibHM8kDBzGc7cJOnjh",
    "process": "https://mi.feishu.cn/wiki/R4Mmwg3IpiDTrTk5RXCcLx2jnQg",
}


def get_tenant_token():
    """获取飞书tenant_access_token"""
    try:
        app_id = st.secrets.get("app_id", "")
        app_secret = st.secrets.get("app_secret", "")
        if not app_id or not app_secret:
            return None
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("tenant_access_token")
    except Exception:
        pass
    return None


def extract_token_from_url(url):
    """从URL提取token"""
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else ""


def resolve_wiki_token(token, headers):
    """将wiki token解析为文档token"""
    try:
        resp = requests.get(
            f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={token}",
            headers=headers, timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            node = data.get("data", {}).get("node", {})
            return node.get("obj_token", token), node.get("obj_type", "docx")
    except Exception:
        pass
    return token, "docx"


def fetch_doc_content(url, token):
    """获取飞书文档内容"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    doc_token = extract_token_from_url(url)

    # 如果是wiki URL，先解析
    if "/wiki/" in url:
        doc_token, obj_type = resolve_wiki_token(doc_token, headers)

    # 获取文档纯文本内容
    try:
        resp = requests.get(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content",
            headers=headers, timeout=30
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("content", "")
    except Exception:
        pass

    # 备用：获取文档块列表
    try:
        resp = requests.get(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks",
            headers=headers, timeout=30,
            params={"page_size": 500}
        )
        data = resp.json()
        if data.get("code") == 0:
            blocks = data.get("data", {}).get("items", [])
            text_parts = []
            for block in blocks:
                block_type = block.get("block_type")
                # 文本块
                if block_type in (1, 2, 3, 4, 5):  # page/text/heading1-3
                    elements = block.get("text", {}).get("elements", [])
                    for elem in elements:
                        if "text_run" in elem:
                            text_parts.append(elem["text_run"].get("content", ""))
            return "\n".join(text_parts)
    except Exception:
        pass

    return ""


@st.cache_data(ttl=300, show_spinner="正在从飞书拉取数据...")
def load_all_data():
    """加载所有飞书文档数据"""
    token = get_tenant_token()
    if not token:
        return None

    result = {}
    for key, url in FEISHU_DOCS.items():
        content = fetch_doc_content(url, token)
        result[key] = {
            "type": "docx",
            "title": "",
            "token": extract_token_from_url(url),
            "modified_time": "",
            "markdown": content
        }

    return result
