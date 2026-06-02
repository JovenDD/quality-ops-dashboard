# 质量运营看板

小米汽车质量运营部 — 质量数据看板

## 部署到Streamlit Cloud

1. Fork此仓库到你的GitHub
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 选择此仓库，主文件填 `dashboard.py`
4. 在Settings → Secrets 中添加飞书凭证：
```toml
app_id = "你的飞书AppID"
app_secret = "你的飞书AppSecret"
```
5. 点击Deploy

## 本地运行

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```
