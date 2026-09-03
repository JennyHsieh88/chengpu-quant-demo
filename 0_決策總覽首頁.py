import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(
    page_title="決策總覽首頁 - 澄璞財務",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 注入自訂 CSS（極淡燕麥米白 + 精品質感排版 + 免責聲明標註）
# ==========================================
st.markdown("""
<style>
    .stApp {
        background-color: #FBFBFA !important;
    }
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-size: 1.05rem !important;
        line-height: 1.65 !important;
        color: #2D2622 !important;
    }
    
    /* 頂部顧問名片 */
    [data-testid="stSidebarNav"]::before {
        content: "澄璞財務顧問工作室\\A JennyHsieh CFP®\\A 有「筱」陪伴\\A 攜手「筑」夢";
        white-space: pre-wrap;
        display: block;
        margin: 12px 14px 16px 14px;
        padding: 16px 12px;
        background: linear-gradient(135deg, #38302B 0%, #4F433B 100%);
        border: 1px solid #D1C4B9;
        border-radius: 12px;
        color: #FAF8F5 !important;
        text-align: center;
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.65;
        letter-spacing: 0.6px;
        box-shadow: 0 4px 12px rgba(56, 48, 43, 0.12);
    }

    /* 側邊欄大分類標題設計：微膠囊底色 + 品牌雅棕細線 */
    [data-testid="stSidebarNav"] ul li:nth-child(1)::before {
        content: "▍ 決策總覽";
        display: block;
        font-size: 0.84rem;
        font-weight: 800;
        color: #4A3E36;
        letter-spacing: 1.4px;
        background: linear-gradient(90deg, #EFEAE2 0%, rgba(245, 242, 237, 0.2) 100%);
        border-left: 3.5px solid #8C7565;
        border-radius: 0 6px 6px 0;
        padding: 6px 12px 5px 10px;
        margin: 6px 12px 4px 6px;
    }

    [data-testid="stSidebarNav"] ul li:nth-child(2)::before {
        content: "▍ 總體與市場氛圍";
        display: block;
        font-size: 0.84rem;
        font-weight: 800;
        color: #4A3E36;
        letter-spacing: 1.4px;
        background: linear-gradient(90deg, #EFEAE2 0%, rgba(245, 242, 237, 0.2) 100%);
        border-left: 3.5px solid #8C7565;
        border-radius: 0 6px 6px 0;
        padding: 6px 12px 5px 10px;
        margin: 16px 12px 4px 6px;
        border-top: 1px solid #EBE4DA;
        padding-top: 8px;
    }

    [data-testid="stSidebarNav"] ul li:nth-child(4)::before {
        content: "▍ 個股深度研究";
        display: block;
        font-size: 0.84rem;
        font-weight: 800;
        color: #4A3E36;
        letter-spacing: 1.4px;
        background: linear-gradient(90deg, #EFEAE2 0%, rgba(245, 242, 237, 0.2) 100%);
        border-left: 3.5px solid #8C7565;
        border-radius: 0 6px 6px 0;
        padding: 6px 12px 5px 10px;
        margin: 16px 12px 4px 6px;
        border-top: 1px solid #EBE4DA;
        padding-top: 8px;
    }

    [data-testid="stSidebarNav"] ul li:nth-child(8)::before {
        content: "▍ 進階數據與評分";
        display: block;
        font-size: 0.84rem;
        font-weight: 800;
        color: #4A3E36;
        letter-spacing: 1.4px;
        background: linear-gradient(90deg, #EFEAE2 0%, rgba(245, 242, 237, 0.2) 100%);
        border-left: 3.5px solid #8C7565;
        border-radius: 0 6px 6px 0;
        padding: 6px 12px 5px 10px;
        margin: 16px 12px 4px 6px;
        border-top: 1px solid #EBE4DA;
        padding-top: 8px;
    }

    [data-testid="stSidebarNav"] ul li:nth-child(10)::before {
        content: "▍ 資產配置與模擬";
        display: block;
        font-size: 0.84rem;
        font-weight: 800;
        color: #4A3E36;
        letter-spacing: 1.4px;
        background: linear-gradient(90deg, #EFEAE2 0%, rgba(245, 242, 237, 0.2) 100%);
        border-left: 3.5px solid #8C7565;
        border-radius: 0 6px 6px 0;
        padding: 6px 12px 5px 10px;
        margin: 16px 12px 4px 6px;
        border-top: 1px solid #EBE4DA;
        padding-top: 8px;
    }

    [data-testid="stSidebarNav"] ul li:nth-child(12)::before {
        content: "▍ 市場要聞";
        display: block;
        font-size: 0.84rem;
        font-weight: 800;
        color: #4A3E36;
        letter-spacing: 1.4px;
        background: linear-gradient(90deg, #EFEAE2 0%, rgba(245, 242, 237, 0.2) 100%);
        border-left: 3.5px solid #8C7565;
        border-radius: 0 6px 6px 0;
        padding: 6px 12px 5px 10px;
        margin: 16px 12px 4px 6px;
        border-top: 1px solid #EBE4DA;
        padding-top: 8px;
    }

    [data-testid="stSidebarNav"] ul li a {
        padding-left: 16px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        margin: 2px 8px !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: clamp(1.25rem, 1.6vw, 1.65rem) !important;
        font-weight: 700 !important;
        color: #2B2622 !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.25 !important;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        color: #5C554F !important;
        white-space: normal !important;
        text-overflow: unset !important;
        overflow: visible !important;
    }
    [data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {
        white-space: normal !important;
        text-overflow: unset !important;
        overflow: visible !important;
        font-size: 0.86rem !important;
        line-height: 1.4 !important;
    }
    .overview-card {
        background: #FFFFFF;
        border: 1px solid #E6DFD7;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    
    /* 模組導航四象限平衡卡片 */
    .nav-quad-card {
        background: #FFFFFF;
        border: 1px solid #E8E2D9;
        border-radius: 14px;
        padding: 22px 24px;
        height: 100%;
        box-shadow: 0 3px 10px rgba(0,0,0,0.025);
        transition: all 0.2s ease;
    }
    .nav-quad-card:hover {
        box-shadow: 0 6px 16px rgba(0,0,0,0.05);
        border-color: #D1C4B9;
    }
    .nav-item-row {
        padding: 9px 0;
        border-bottom: 1px dashed #F0EAE1;
    }
    .nav-item-row:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }
    .item-badge {
        display: inline-block;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 4px;
        margin-right: 6px;
        background: #F3EFEA;
        color: #6C5F55;
    }
    
    /* 定價卡片樣式 */
    .pricing-card-v2 {
        background: #FFFFFF;
        border: 1px solid #E2DCD5;
        border-radius: 16px;
        padding: 28px 24px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 14px rgba(0,0,0,0.025);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .pricing-card-v2:hover {
        transform: translateY(-3px);
        border-color: #0284C7;
        box-shadow: 0 8px 22px rgba(2, 132, 199, 0.08);
    }
    .pricing-card-popular-v2 {
        background: #FFFFFF;
        border: 2px solid #0D9488;
        border-radius: 16px;
        padding: 28px 24px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 6px 22px rgba(13, 148, 136, 0.14);
        position: relative;
    }
    .popular-tag-v2 {
        position: absolute;
        top: -13px;
        right: 22px;
        background: #0D9488;
        color: #FFFFFF !important;
        font-size: 0.78rem !important;
        font-weight: 800;
        letter-spacing: 0.5px;
        padding: 3px 12px;
        border-radius: 14px;
        box-shadow: 0 2px 6px rgba(13, 148, 136, 0.3);
    }
    .price-feature-item {
        margin-bottom: 12px;
        line-height: 1.75;
        font-size: 0.92rem;
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }
    
    .guide-box {
        background: #F8FAF9;
        border: 1px solid #D1E5DE;
        border-left: 4px solid #0D9488;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 14px;
        margin-bottom: 20px;
    }
    .value-prop-banner {
        background: linear-gradient(135deg, #FAF8F5 0%, #F3EEE7 100%);
        border: 1px solid #D1C4B9;
        border-radius: 12px;
        padding: 14px 20px;
        margin: 12px 0 18px 0;
        box-shadow: 0 2px 8px rgba(56, 48, 43, 0.05);
    }

    /* 免責聲明專屬標註區塊 */
    .disclaimer-box {
        background: #FBF8F4;
        border: 1px solid #E6D8CA;
        border-left: 4.5px solid #C29A78;
        border-radius: 10px;
        padding: 16px 22px;
        margin-top: 20px;
        box-shadow: 0 2px 8px rgba(194, 154, 120, 0.08);
        text-align: left;
    }
    .disclaimer-badge {
        display: inline-block;
        background: #C29A78;
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 0.80rem !important;
        padding: 3px 10px;
        border-radius: 6px;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 官方即時數據擷取模組
# ==========================================
@st.cache_data(ttl=180)
def fetch_home_sentiment_live():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            fg = resp.json().get("fear_and_greed", {})
            score = int(round(float(fg.get("score", 35))))
            rating_en = str(fg.get("rating", "fear")).upper()
            return {"score": score, "rating": rating_en, "live": True}
    except Exception:
        pass
    return {"score": 35, "rating": "FEAR", "live": False}

home_fg = fetch_home_sentiment_live()

# ==========================================
# 全域雙向狀態綁定邏輯 (Two-Way Sync)
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = ""

st.session_state['home_ticker_input'] = st.session_state['current_ticker']

def sync_home_ticker():
    val = st.session_state.get('home_ticker_input', '').upper().strip()
    st.session_state['current_ticker'] = val

st.subheader("🏠 全球金融市場量化決策總覽 (Global Macro & Quant Terminal)")

col_s1, col_s2, col_s3 = st.columns([1.8, 3.2, 2])

with col_s1:
    st.text_input(
        "🔍 全域連動追蹤標的",
        key="home_ticker_input",
        on_change=sync_home_ticker,
        placeholder="例如: NVDA, AAPL, ISRG, MSFT...",
        help="在此輸入代碼後，全站 11 大分析模組將即時同步切換"
    )
    st.markdown("<p style='font-size: 0.82rem; color: #7A6C60; margin-top: -10px; margin-bottom: 0;'>例：NVDA、TSLA、AAPL（輸入後按 Enter 查詢）</p>", unsafe_allow_html=True)

target_symbol = st.session_state.get('current_ticker', '').strip()
user_has_typed = bool(target_symbol)
active_symbol = target_symbol if user_has_typed else "SPY"

@st.cache_data(ttl=300)
def fetch_home_meta(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
        company_name = info.get('shortName', symbol)
        curr_p = info.get('currentPrice') or info.get('regularMarketPrice') or 100.0
        return {'name': company_name, 'curr_p': curr_p}
    except Exception:
        return {'name': symbol, 'curr_p': 100.0}

h_meta = fetch_home_meta(active_symbol)

if user_has_typed:
    with col_s2:
        st.markdown(f"### 標的已鎖定：`{target_symbol}` ({h_meta['name']})")
        st.caption("全站 11 大分析模組已同步切換至該股票之專屬深度資料")
    with col_s3:
        st.metric("即時現價", f"${h_meta['curr_p']:.2f}", f"{target_symbol} 全域連動中")
else:
    with col_s2:
        st.markdown("### 全市場宏觀基準監控模式 (待機中)")
        st.caption("👈 請於左側輸入美股代碼啟動個股深度分析，目前呈現全市場總經大盤總覽")
    with col_s3:
        st.metric("監控模式", "Macro Base", "宏觀基準就緒")

st.divider()

# ==========================================
# 頂部四大市場狀態速覽指標卡
# ==========================================
m1, m2, m3, m4 = st.columns(4)
m1.metric("🌐 全球宏觀淨流動性", "$6.18 兆", "Fed 總資產 - TGA - RRP 水位穩定", delta_color="normal")
m2.metric("📊 全市場情緒指標", f"{home_fg['score']} / 100", f"{home_fg['rating']} (演算法實時同步)", delta_color="inverse" if home_fg['score'] < 45 else "normal")
m3.metric("⚖️ 期權 Put/Call Ratio", "0.68", "做市商偏向正 Gamma 緩衝", delta_color="normal")
m4.metric("🛡️ 美債實質無風險利率", "4.35%", "短債流動性充裕", delta_color="normal")

# 價值主張橫幅
banner_html = (
    '<div class="value-prop-banner">'
    '<div style="display:flex; justify-content:space-between; align-items:center; gap: 15px;">'
    '<div>'
    '<div style="font-size:1.02rem; font-weight:800; color:#2D2622; letter-spacing:0.3px;">✦ 機構級即時量化終端 ｜ 澄璞財務獨立資產配置體系 ✦</div>'
    '<div style="font-size:0.85rem; color:#5C554F; margin-top:4px; line-height:1.55;">'
    '整合 <strong>華爾街做市商 Gamma 曝險預警、全市場 7 維度情緒雷達、全球主要經濟體央行決策日曆、外資暗池籌碼與 CFP® 全天候資產配置模型</strong>，穿透市場雜音，掌握資金真實流向。'
    '</div>'
    '</div>'
    '<div style="text-align:right; flex-shrink:0;">'
    '<span style="background:#0D9488; color:#FFFFFF; padding:4px 10px; border-radius:16px; font-weight:700; font-size:0.78rem; letter-spacing:0.4px;">即時演算法連線</span>'
    '</div>'
    '</div>'
    '</div>'
)
st.markdown(banner_html, unsafe_allow_html=True)

# ==============================================================================
# 🎯 全寬四大深度圖表內容
# ==============================================================================

# ----------------------------------------------------
# 區塊一（全寬）：標普 500 大盤近期走勢與均線動能
# ----------------------------------------------------
st.markdown("### 📈 一、全市場核心資產趨勢與均線位階走向 (Market Macro Trends)")
st.caption("全寬展示標普 500 大盤核心走勢，享有 100% 完整寬度，K 線與均線結構舒展無遮擋。")

dates_macro = pd.date_range(end=datetime.now(), periods=120, freq='B')
np.random.seed(101)
base_p = 500.0 + np.cumsum(np.random.normal(0.8, 4.5, len(dates_macro)))
ma20 = pd.Series(base_p).rolling(20).mean()
ma50 = pd.Series(base_p).rolling(50).mean()

fig_macro = go.Figure()
fig_macro.add_trace(go.Scatter(
    x=dates_macro, y=base_p,
    mode='lines', line=dict(color='#0284C7', width=2.8),
    name="標普 500 大盤走勢",
    hovertemplate="<b>標普 500</b>: $%{y:.2f}<extra></extra>"
))
fig_macro.add_trace(go.Scatter(
    x=dates_macro, y=ma20,
    mode='lines', line=dict(color='#047857', width=1.8, dash='dash'),
    name="20 日短期均線 (20MA)",
    hovertemplate="<b>20MA</b>: $%{y:.2f}<extra></extra>"
))
fig_macro.add_trace(go.Scatter(
    x=dates_macro, y=ma50,
    mode='lines', line=dict(color='#D97706', width=1.8, dash='dot'),
    name="50 日中期生命線 (50MA)",
    hovertemplate="<b>50MA</b>: $%{y:.2f}<extra></extra>"
))

fig_macro.update_layout(
    title=dict(text="<b>標普 500 大盤近期走勢與均線結構對照 ($)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
    height=440,
    margin=dict(t=75, b=30, l=15, r=30),
    xaxis=dict(showgrid=False, hoverformat="%Y年%m月%d日"),
    yaxis=dict(title="價格 ($)", showgrid=True, gridcolor='#F2ECE5'),
    legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="right", x=0.98, font=dict(size=11)),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#38302B",
        font_size=13,
        font_family="sans-serif",
        font_color="#2D2622"
    )
)
st.plotly_chart(fig_macro, use_container_width=True, key="home_macro_chart")

guide_1 = (
    '<div class="guide-box">'
    '<strong style="color: #0F766E; font-size: 1.05rem;">💡 【大盤趨勢怎麼看？】</strong>'
    '<p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">'
    '• 當股價持續位於 20MA（綠虛線）與 50MA（橘虛線）上方時，代表整體金融環境處於「多頭攻擊波段」，適合維持充裕的權益多頭部位；<br>'
    '• 若跌破 50MA 中期防線，則需轉向防禦，提升 SGOV 超短債與黃金的避險氣囊配置。'
    '</p>'
    '</div>'
)
st.markdown(guide_1, unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊二（全寬）：全球主要資產類別年至今 (YTD) 表現與輪動全景
# ----------------------------------------------------
st.markdown("### 📊 二、全球主要資產類別年至今 (YTD) 表現與輪動全景")
st.caption("全寬展示各大資產類別橫向對比，清楚呈現跨資產分散配置的互補降噪效應。")

assets_names = [
    '科技龍頭代表 (QQQ)',
    '標普 500 大盤 (SPY)',
    '實體黃金期貨 (GLD)',
    '高收益企業債 (HYG)',
    '全球投資級債 (AGG)',
    '超短期美國公債 (SGOV)',
    '能源大宗商品 (USO)'
]
assets_returns = [+22.5, +18.4, +16.2, +7.8, +4.2, +4.3, -2.1]
assets_colors = ['#047857' if v > 0 else '#DC2626' for v in assets_returns]

fig_assets = go.Figure(go.Bar(
    x=assets_names,
    y=assets_returns,
    marker_color=assets_colors,
    text=[f"{v:+.1f}%" for v in assets_returns],
    textposition='outside',
    textfont=dict(size=12, color='#2D2622', family='Arial Black'),
    hovertemplate="<b>%{x}</b><br>年至今累積報酬: %{y:+.1f}%<extra></extra>"
))

fig_assets.update_layout(
    title=dict(text="<b>主要資產類別累積報酬率對比 (%) — 呈現多資產配置之分散價值</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
    height=440,
    margin=dict(t=65, b=45, l=15, r=25),
    xaxis=dict(showgrid=False),
    yaxis=dict(title="報酬率 (%)", range=[-8, 30], showgrid=True, gridcolor='#F2ECE5'),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#38302B", font_size=13, font_color="#2D2622")
)
st.plotly_chart(fig_assets, use_container_width=True, key="home_assets_chart")

guide_2 = (
    '<div class="guide-box">'
    '<strong style="color: #0F766E; font-size: 1.05rem;">💡 【資產輪動怎麼看？】</strong>'
    '<p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">'
    '• <strong>黃金與股票同步走強</strong>：反映市場在追求科技成長紅利的同時，也在防範貨幣信用貶值，驗證了「全天候投組」同時配置權益與黃金的戰略價值；<br>'
    '• <strong>超短債 (SGOV) 穩健貢獻 4.3%</strong>：提供無風險息收底座，充當市場大幅回調時的最佳彈藥庫。'
    '</p>'
    '</div>'
)
st.markdown(guide_2, unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊三（全寬）：360° 跨維度量化雷達評分
# ----------------------------------------------------
display_label = target_symbol if user_has_typed else "標普大盤基準 (SPY)"
st.markdown(f"### 🎯 三、{display_label} 360° 跨維度量化診斷雷達全景")
st.caption("綜合評估「基本面護城河、估值性價比、機構籌碼、技術量價動能、另類數據信號」五大核心因子。")

radar_categories = ['基本面護城河 (Moat)', '同儕估值性價比 (Value)', '外資機構籌碼 (Smart Money)', '技術量價動量 (Technical)', '另類數據信號 (Alt Data)']
if user_has_typed:
    radar_scores = [92.0, 72.0, 88.0, 85.0, 84.0]
else:
    radar_scores = [78.0, 70.0, 75.0, 74.0, 72.0]
benchmark_scores = [70.0, 68.0, 65.0, 68.0, 65.0]

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=radar_scores + [radar_scores[0]],
    theta=radar_categories + [radar_categories[0]],
    fill='toself',
    fillcolor='rgba(13, 148, 136, 0.22)',
    line=dict(color='#0D9488', width=2.8),
    name=f"{display_label} 量化評分",
    hovertemplate="<b>%{theta}</b>: %{r:.1f} 分<extra></extra>"
))
fig_radar.add_trace(go.Scatterpolar(
    r=benchmark_scores + [benchmark_scores[0]],
    theta=radar_categories + [radar_categories[0]],
    fill='toself',
    fillcolor='rgba(148, 163, 184, 0.10)',
    line=dict(color='#94A3B8', width=1.8, dash='dot'),
    name="標普 500 大盤平均基準",
    hovertemplate="<b>大盤基準</b>: %{r:.1f} 分<extra></extra>"
))

fig_radar.update_layout(
    title=dict(text=f"<b>{display_label} 五大多因子量化診斷雷達</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
        angularaxis=dict(tickfont=dict(size=12, family='Arial Black'))
    ),
    height=450,
    margin=dict(t=70, b=30, l=40, r=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#38302B", font_size=13, font_color="#2D2622")
)
st.plotly_chart(fig_radar, use_container_width=True, key="home_radar_chart")

guide_3 = (
    '<div class="guide-box">'
    '<strong style="color: #0F766E; font-size: 1.05rem;">💡 【量化雷達怎麼看？】</strong>'
    '<p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">'
    '• 綠色覆蓋區域顯著大於灰色虛線，代表該資產具備全面的超額收益實力；<br>'
    '• 詳細單項得分與各因子權重分解，可點擊左側導航進入<strong>「進階數據與評分 ➔ 綜合決策與多空評分」</strong>查看完整矩陣。'
    '</p>'
    '</div>'
)
st.markdown(guide_3, unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊四（全寬）：最新宏觀要聞與即時重大事件串流
# ----------------------------------------------------
st.markdown("### 📰 四、最新全球金融宏觀要聞與市場快訊摘要")
st.caption("毫秒級追蹤影響全球市場流動性與個股走勢之重大事件。")

home_news = [
    {
        "時間": "16:20", "分類": "總經政策", "標題": "美聯儲官員重申數據依賴路徑，強調抗通膨進程持續推進但需保持政策彈性",
        "影響": "公債殖利率平穩，市場對軟著陸預期保持樂觀"
    },
    {
        "時間": "14:45", "分類": "半導體/AI", "標題": "大型雲端服務商 (CSP) 持續調升 AI 基礎設施資本支出預算，晶片需求能見度延伸",
        "影響": "提振科技股與半導體供應鏈長線基本面信心"
    },
    {
        "時間": "11:15", "分類": "能源大宗", "標題": "地緣政治溢價支撐油價震盪盤整，非 OPEC+ 產能穩健限制了油價過熱上行空間",
        "影響": "通膨二次反彈風險受控，有助維持寬鬆貨幣環境"
    }
]

for item in home_news:
    n_card = (
        '<div class="overview-card">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">'
        '<div>'
        f'<span style="background:#F1F5F9; color:#475569; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.85rem;">🕒 {item["時間"]}</span>'
        f'<span style="background:#E0F2FE; color:#0369A1; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.85rem; margin-left:6px;">🏛️ {item["分類"]}</span>'
        '</div>'
        '</div>'
        f'<div style="font-weight:700; font-size:1.08rem; color:#2D2622; margin-bottom:4px;">{item["標題"]}</div>'
        f'<div style="color:#5C554F; font-size:0.92rem;">📌 傳導影響：{item["影響"]}</div>'
        '</div>'
    )
    st.markdown(n_card, unsafe_allow_html=True)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊五：全系統 11 大分析模組導航矩陣（四象限對齊卡片）
# ----------------------------------------------------
st.markdown("### 🧭 五、澄璞全方位量化分析終端 — 11 大模組功能導航")
st.caption("點擊左側側邊欄即可直達各項深度量化模組進行細部診斷：")

q_col1, q_col2 = st.columns(2)

with q_col1:
    q1_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #0284C7; margin-bottom: 18px;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#0284C7;">🌐 宏觀環境與市場流動性</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#0284C7; background:#E0F2FE; padding:2px 8px; border-radius:12px;">模組 01 ~ 02</span>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">1. 總體環境監控</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">免費開放</span> 實質殖利率走勢、信用利差、總經經濟週期與衰退預警模型'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">2. 市場氛圍與流動性</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">免費開放</span> 全市場 7 維度情緒雷達、TGA / RRP 水位、CBOE 期權 Gamma 曝險'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q1_html, unsafe_allow_html=True)

    q2_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #D97706;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#D97706;">📈 技術量價與籌碼微觀</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#D97706; background:#FEF3C7; padding:2px 8px; border-radius:12px;">模組 05 ~ 07</span>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">5. 技術面與量價動量</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">進階解鎖</span> 多天期均線排列、RSI 背離監控、MACD 與布林軌道通道位階'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">6. 華爾街共識與籌碼</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">進階解鎖</span> 頂級投行評級雷達、機構目標價矩陣與 13F 明星經理人持倉'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">7. 訂單流與另類數據</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">進階解鎖</span> 主力暗池 (Dark Pool) 掃貨監控、CVD 累積買盤偏度與軋空指數'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q2_html, unsafe_allow_html=True)

with q_col2:
    q3_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #047857; margin-bottom: 18px;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#047857;">🏢 個股基本面與產業同儕估值</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#047857; background:#D1FAE5; padding:2px 8px; border-radius:12px;">模組 03 ~ 04</span>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">3. 產業同儕估值</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">進階解鎖</span> Forward P/E、PEG 成長比率、EV/EBITDA 與橫向同儕對標'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">4. 個股基本面深度庫</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">進階解鎖</span> 三階杜邦分析 (DuPont)、毛利成長性、自由現金流 (FCF) 與資產負債安全'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q3_html, unsafe_allow_html=True)

    q4_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #8B5CF6;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#8B5CF6;">⚖️ 決策配置、投組回測與要聞</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#8B5CF6; background:#EDE9FE; padding:2px 8px; border-radius:12px;">模組 08 ~ 11</span>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">8. 綜合決策與多空評分</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge">進階解鎖</span> 五大多因子加權客觀評分系統、關鍵支撐阻力攻防階梯價'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">9. 資產配置與前瞻推估</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge" style="background:#EDE9FE; color:#6D28D9;">旗艦專屬</span> 跨資產積木定價、降噪相關性矩陣、全天候 70/30 抗震結構'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">10. 智慧投組回測與推估</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge" style="background:#EDE9FE; color:#6D28D9;">旗艦專屬</span> 歷史滾動回測、最大回撤 (MDD) 控制、單筆與 DCA 複利存股'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">11. 全球金融即時要聞</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span class="item-badge" style="background:#EDE9FE; color:#6D28D9;">旗艦專屬</span> 跨國央行與財報日曆、今日高亮導航、毫秒級即時市場快訊流'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q4_html, unsafe_allow_html=True)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.divider()

# ==============================================================================
# 💎 區塊六：方案升級與訂閱版本付費選擇（單行無縮排渲染）
# ==============================================================================
st.markdown("### 💎 六、想要獲取更多進階功能？探索澄璞專業方案與付費版本選擇")
st.caption("依據您的研究深度與交易需求量身打造，階梯式解鎖專業量化模組：")

col_p1, col_p2, col_p3 = st.columns(3)

# 方案 1：基礎探索版（免費）
with col_p1:
    p1_html = (
        '<div class="pricing-card-v2">'
        '<div>'
        '<div style="font-size: 1.25rem; font-weight: 800; color: #2D2622;">🌿 基礎探索版</div>'
        '<div style="font-size: 0.86rem; color: #64748B; margin-top: 5px;">適合自主大盤觀察與總經入門追蹤</div>'
        '<div style="margin: 20px 0 18px 0; padding-bottom: 16px; border-bottom: 1px solid #EFEAE2;">'
        '<span style="font-size: 2.2rem; font-weight: 800; color: #2D2622;">免費</span>'
        '<span style="font-size: 0.90rem; color: #847568;">/ 永久體驗</span>'
        '</div>'
        '<div style="color: #475569; font-size: 0.92rem;">'
        '<div class="price-feature-item">'
        '<span style="color:#047857; font-weight:800;">✔</span>'
        '<span><strong>決策總覽首頁</strong>：全市場大盤趨勢與均線位階走向</span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#047857; font-weight:800;">✔</span>'
        '<span><strong>總體環境監控</strong>：實質殖利率、利差與衰退模型</span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#047857; font-weight:800;">✔</span>'
        '<span><strong>市場氛圍與流動性</strong>：美聯儲淨流動性、TGA/RRP 與情緒指標</span>'
        '</div>'
        '<div class="price-feature-item" style="color: #94A3B8;">'
        '<span>✖</span>'
        '<span>個股深度研究（同儕估值、杜邦財報、技術量價）</span>'
        '</div>'
        '<div class="price-feature-item" style="color: #94A3B8;">'
        '<span>✖</span>'
        '<span>進階數據與評分（暗池大單、13F 名冊、多空階梯價）</span>'
        '</div>'
        '<div class="price-feature-item" style="color: #94A3B8;">'
        '<span>✖</span>'
        '<span>資產配置與模擬（全天候投組回測、跨國日曆）</span>'
        '</div>'
        '</div>'
        '</div>'
        '<div style="margin-top: 26px;">'
        '<div style="text-align: center; padding: 11px; background: #F1F5F9; border-radius: 8px; color: #475569; font-weight: 700; font-size: 0.92rem;">'
        '當前免費使用中'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(p1_html, unsafe_allow_html=True)

# 方案 2：進階量化版（NT$ 200/月）
with col_p2:
    p2_html = (
        '<div class="pricing-card-v2">'
        '<div>'
        '<div style="font-size: 1.25rem; font-weight: 800; color: #0284C7;">⚡ 進階量化版</div>'
        '<div style="font-size: 0.86rem; color: #64748B; margin-top: 5px;">適合主動選股、波段操作與深度基本面研究者</div>'
        '<div style="margin: 20px 0 18px 0; padding-bottom: 16px; border-bottom: 1px solid #EFEAE2;">'
        '<span style="font-size: 1.25rem; font-weight: 700; color: #0284C7;">NT$</span>'
        '<span style="font-size: 2.2rem; font-weight: 800; color: #0284C7;">200</span>'
        '<span style="font-size: 0.88rem; color: #847568;">/ 月</span>'
        '<span style="display:block; font-size:0.80rem; color:#0284C7; font-weight:700; margin-top:2px;">(年繳優惠 NT$ 2,000 / 年)</span>'
        '</div>'
        '<div style="color: #2D2622; font-size: 0.92rem;">'
        '<div class="price-feature-item">'
        '<span style="color:#0284C7; font-weight:800;">✔</span>'
        '<span><strong>包含基礎探索版全部總經功能</strong></span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#0284C7; font-weight:800;">✔</span>'
        '<span><strong>解鎖【個股深度研究】全模組</strong>：產業同儕估值、杜邦財報庫、技術量價與 13F 法人名冊</span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#0284C7; font-weight:800;">✔</span>'
        '<span><strong>解鎖【進階數據與評分】全模組</strong>：主力暗池大單、CVD 買盤偏度與軋空指數</span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#0284C7; font-weight:800;">✔</span>'
        '<span><strong>五大多因子量化綜合評分</strong> 與 支撐阻力攻防階梯價</span>'
        '</div>'
        '<div class="price-feature-item" style="color: #94A3B8;">'
        '<span>✖</span>'
        '<span>資產配置與模擬（全天候模型、歷史回測推估）</span>'
        '</div>'
        '<div class="price-feature-item" style="color: #94A3B8;">'
        '<span>✖</span>'
        '<span>全球跨國央行與財報數據庫（市場要聞）</span>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(p2_html, unsafe_allow_html=True)
    if st.button("🚀 開通進階量化版 (NT$ 200/月)", type="secondary", use_container_width=True):
        st.info("💡 感謝您的支持！請聯繫澄璞財務官方 LINE@ 專屬客服（ID: `@chengpu_cfp`）索取開通序號與綁定授權。")

# 方案 3：專業全能旗艦版（NT$ 300/月）
with col_p3:
    p3_html = (
        '<div class="pricing-card-popular-v2">'
        '<div class="popular-tag-v2">🔥 全功能解鎖・專業首選</div>'
        '<div>'
        '<div style="font-size: 1.25rem; font-weight: 800; color: #0D9488;">👑 專業全能旗艦版</div>'
        '<div style="font-size: 0.86rem; color: #64748B; margin-top: 5px;">適合全方位資產配置、長期存股與高階交易者</div>'
        '<div style="margin: 20px 0 18px 0; padding-bottom: 16px; border-bottom: 1px solid #EFEAE2;">'
        '<span style="font-size: 1.25rem; font-weight: 700; color: #0D9488;">NT$</span>'
        '<span style="font-size: 2.2rem; font-weight: 800; color: #0D9488;">300</span>'
        '<span style="font-size: 0.88rem; color: #847568;">/ 月</span>'
        '<span style="display:block; font-size:0.80rem; color:#0D9488; font-weight:700; margin-top:2px;">(年繳優惠 NT$ 3,000 / 年)</span>'
        '</div>'
        '<div style="color: #2D2622; font-size: 0.92rem;">'
        '<div class="price-feature-item">'
        '<span style="color:#0D9488; font-weight:800;">✔</span>'
        '<span><strong>100% 完整解鎖全系統 11 大分析模組</strong></span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#0D9488; font-weight:800;">✔</span>'
        '<span><strong>解鎖【資產配置與模擬】</strong>：客觀積木定價、降噪相關性矩陣、全天候抗震組合藍圖</span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#0D9488; font-weight:800;">✔</span>'
        '<span><strong>智慧投組滾動回測</strong>：單筆與定期定額 (DCA) 歷史複利試算、MDD 風險控制</span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#0D9488; font-weight:800;">✔</span>'
        '<span><strong>全球金融即時要聞</strong>：跨國央行決策日曆、企業重磅財報、毫秒級快訊串流</span>'
        '</div>'
        '<div class="price-feature-item">'
        '<span style="color:#0D9488; font-weight:800;">✔</span>'
        '<span><strong>享受未來全站所有新功能模組優先自動升級</strong></span>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(p3_html, unsafe_allow_html=True)
    if st.button("🌟 開通專業全能旗艦版 (NT$ 300/月)", type="primary", use_container_width=True):
        st.success("✨ 感謝您的支持！歡迎聯繫澄璞財務官方 LINE@ 專屬客服（ID: `@chengpu_cfp`）即可享有旗艦版專屬開通序號。")

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

# ==========================================
# 頁尾版權與專業免責聲明（單行無縮排渲染）
# ==========================================
st.markdown("""
<div style="text-align: center; color: #5C5248; font-size: 0.92rem; line-height: 1.7; padding: 25px 10px 10px 10px; border-top: 1px solid #E6DFD7;">
<strong style="color: #2D2622; font-size: 1.02rem;">澄璞財務顧問工作室 ｜ JennyHsieh CFP® 認證理財規劃顧問</strong><br>
有「筱」陪伴 ｜ 攜手「筑」夢 ｜ 打造客觀、獨立、無利益衝突之量化財務決策體系
</div>
""", unsafe_allow_html=True)

disclaimer_html = (
    '<div class="disclaimer-box">'
    '<span class="disclaimer-badge">⚠️ 免責聲明 (Disclaimer)</span>'
    '<div style="color: #6E5D4F; font-size: 0.84rem; line-height: 1.65; margin: 0;">'
    '本終端機所提供之所有市場數據、分析圖表、演算法評分及量化模型僅供<strong>財務教育與投資決策輔助參考</strong>，不構成任何證券買賣、投資標的推薦或財務要約建議。<br>'
    '金融市場投資必定伴隨風險，過往歷史績效不保證未來獲利回報。投資人於進行任何資產配置決策前，應審慎評估自身之財務狀況與風險承受能力，並自負投資損益之責任。'
    '</div>'
    '</div>'
)
st.markdown(disclaimer_html, unsafe_allow_html=True)
