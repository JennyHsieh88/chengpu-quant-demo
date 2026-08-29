import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面基本配置
st.set_page_config(
    page_title="澄璞財務投資終端",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 全域 CSS 樣式：品牌卡片 + 隱藏 Streamlit 工具列與浮水印
st.markdown("""
<style>
/* 1. 全域基礎字體與行高 */
html, body, [class*="css"], .stMarkdown, p, div, span, label {
    font-size: 1.02rem !important;
    line-height: 1.5 !important;
}

/* 2. 左側導航欄上方專屬品牌卡片 */
[data-testid="stSidebarNav"]::before {
    content: "澄璞財務顧問工作室\\A JennyHsieh CFP®\\A 筱筑";
    white-space: pre-wrap;
    display: block;
    margin: 12px 14px 18px 14px;
    padding: 16px 12px;
    background: linear-gradient(135deg, #1E3A8A 0%, #0D9488 100%);
    color: #FFFFFF;
    font-weight: 700;
    font-size: 1.05rem;
    line-height: 1.6;
    text-align: center;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 3. 徹底隱藏開發者徽章、頂部選單、頁尾浮水印 */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}
.viewerBadge_container__1QSob,
.viewerBadge_link__1S137,
[data-testid="stStatusWidget"],
[data-testid="manage-app-button"],
.stAppDeployButton,
[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# 3. 頁面標題與主架構
st.markdown("### 🖥️ Institutional Multi-Layer Terminal (機構全維度決策總覽)")

# 標的代碼輸入區
col_input, col_info, col_price = st.columns([1.2, 1.8, 1])

with col_input:
    ticker = st.text_input("🔍 全域分析標的代碼 (Ticker)", value="MSFT").upper().strip()

# 資料抓取與緩存
@st.cache_data(ttl=3600)
def load_market_data(symbol):
    try:
        t = yf.Ticker(symbol)
        info = t.info
        hist = t.history(period="1y")
        return info, hist
    except Exception:
        return {}, pd.DataFrame()

info_data, hist_data = load_market_data(ticker)

# 標的即時狀態呈現
with col_info:
    short_name = info_data.get('shortName', ticker)
    sector = info_data.get('sector', 'N/A')
    industry = info_data.get('industry', 'N/A')
    exchange = info_data.get('exchange', 'N/A')
    st.markdown(f"**{short_name} ( `{ticker}` )**")
    st.caption(f"板塊：{sector} ｜ 細分行業：{industry} ｜ 交易所：{exchange}")

with col_price:
    current_price = info_data.get('currentPrice') or info_data.get('regularMarketPrice')
    prev_close = info_data.get('previousClose')
    
    if current_price:
        pct_change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
        st.metric(
            label="即時股價",
            value=f"${current_price:,.2f}",
            delta=f"{pct_change:+.2f}%"
        )
    else:
        st.metric(label="即時股價", value="載入中...")

st.divider()

# 4. 全球市場體溫與標的關鍵位階 (Market Pulse)
st.markdown("#### 🌡️ 全球市場體溫與標的關鍵位階 (Market Pulse)")

@st.cache_data(ttl=3600)
def load_macro_pulse():
    indices = {"^VIX": "VIX 恐慌指數", "^TNX": "10年期美債殖利率", "DX-Y.NYB": "美元指數 (DXY)"}
    data = {}
    for sym, name in indices.items():
        try:
            t = yf.Ticker(sym)
            p = t.history(period="5d")['Close'].iloc[-1]
            data[name] = p
        except Exception:
            data[name] = None
    return data

macro_data = load_macro_pulse()

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    vix = macro_data.get("VIX 恐慌指數")
    val = f"{vix:.2f}" if vix else "N/A"
    st.metric("⚡ VIX 恐慌指數", val)
    if vix and vix < 20:
        st.caption("🟢 市場低恐慌")
    elif vix:
        st.caption("🟡 市場情緒緊繃")

with m_col2:
    tnx = macro_data.get("10年期美債殖利率")
    val = f"{tnx:.2f}%" if tnx else "N/A"
    st.metric("🏛️ 10年期美債殖利率", val)
    st.caption("無風險利率基準")

with m_col3:
    dxy = macro_data.get("美元指數 (DXY)")
    val = f"{dxy:.2f}" if dxy else "N/A"
    st.metric("💵 美元指數 (DXY)", val)
    st.caption("全球流動性指標")

with m_col4:
    fifty_two_high = info_data.get('fiftyTwoWeekHigh')
    fifty_two_low = info_data.get('fiftyTwoWeekLow')
    if current_price and fifty_two_high and fifty_two_low and (fifty_two_high > fifty_two_low):
        pct_range = (current_price - fifty_two_low) / (fifty_two_high - fifty_two_low) * 100
        st.metric(f"📍 {ticker} 52週位階", f"{pct_range:.1f}%")
        st.caption(f"區間: ${fifty_two_low:.2f} - ${fifty_two_high:.2f}")
    else:
        st.metric(f"📍 {ticker} 52週位階", "N/A")

st.divider()

# 5. 導引與版權提示
st.info("""
💡 **導航指引**：請透過左側功能清單進入各模組進行深度分析。
* 開放模組：**0 決策首頁**、**1 全球總經環境**、**2 市場氛圍與流動性**。
* 核心進階模組（3~11 號）為 PRO 授權版本專屬功能。
""")
