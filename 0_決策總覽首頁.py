import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf

# 頁面配置
st.set_page_config(
    page_title="澄璞財務 - 機構多維度投資終端",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 全域自訂 CSS 樣式：純 CSS 原生置頂品牌卡片
# ==========================================
st.markdown("""
<style>
    /* 1. 全域基礎字體與行高放大 */
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-size: 1.06rem !important;
        line-height: 1.6 !important;
    }

    /* 2. 在左側導航欄最上方自動渲染專屬品牌卡片 (精緻排版) */
    [data-testid="stSidebarNav"]::before {
        content: "澄璞財務顧問工作室\\A Jenny 筱筑 CFP®\\A 有「筱」陪伴\\A 攜手「筑」夢";
        white-space: pre-wrap;
        display: block;
        margin: 12px 14px 18px 14px;
        padding: 16px 12px;
        background: linear-gradient(135deg, #1E3A8A 0%, #0D9488 100%);
        border-radius: 10px;
        color: #FFFFFF;
        text-align: center;
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.65;
        letter-spacing: 0.6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* 3. 核心指標卡片 (Metric) 數值放大 */
    [data-testid="stMetricValue"] {
        font-size: clamp(1.45rem, 2.0vw, 1.85rem) !important;
        font-weight: 700 !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.25 !important;
    }

    /* 4. 指標卡片標籤解除截斷 */
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] p {
        font-size: 1.02rem !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 全域狀態初始化與即時回呼同步
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = "MSFT"

if 'ticker_input' not in st.session_state:
    st.session_state['ticker_input'] = st.session_state['current_ticker']

def update_ticker():
    val = st.session_state.get('ticker_input', '').upper().strip()
    if val:
        st.session_state['current_ticker'] = val

# ==========================================
# 全域核心標的設定區
# ==========================================
st.title("🖥️ Institutional Multi-Layer Terminal (機構全維度決策總覽)")

col_in, col_info, col_price = st.columns([1.6, 3.4, 2])

with col_in:
    st.text_input(
        "🔍 全域分析標的代碼 (Ticker)", 
        key="ticker_input",
        on_change=update_ticker,
        help="輸入美股代碼 (例如 AAPL, NVDA, TSLA, MSFT, ISRG) 後按 Enter"
    )

target_symbol = st.session_state['current_ticker']

# 取得標的資訊與即時運算
@st.cache_data(ttl=300)
def fetch_cockpit_data(symbol: str):
    stock = yf.Ticker(symbol)
    info = stock.info or {}
    hist = stock.history(period="6mo")
    if not hist.empty:
        hist.index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
    
    # 宏觀數據快照
    try:
        vix_df = yf.Ticker("^VIX").history(period="5d")
        vix_val = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 16.5
    except Exception:
        vix_val = 16.5
        
    try:
        tnx_df = yf.Ticker("^TNX").history(period="5d")
        tnx_val = float(tnx_df['Close'].iloc[-1]) if not tnx_df.empty else 4.25
    except Exception:
        tnx_val = 4.25
        
    try:
        dxy_df = yf.Ticker("DX-Y.NYB").history(period="5d")
        dxy_val = float(dxy_df['Close'].iloc[-1]) if not dxy_df.empty else 104.2
    except Exception:
        dxy_val = 104.2

    # 動態計算 6 維度雷達分數
    # 1. 基本面質量
    roe_val = (info.get('returnOnEquity', 0) or 0.15) * 100
    op_margin_val = (info.get('operatingMargins', 0) or 0.20) * 100
    score_fund = np.clip((roe_val * 1.5) + (op_margin_val * 1.2), 35, 96)

    # 2. 技術動量
    if not hist.empty and len(hist) > 20:
        c = hist['Close']
        roc_20 = ((c.iloc[-1] - c.iloc[-20]) / c.iloc[-20]) * 100
        ema_20 = c.ewm(span=20, adjust=False).mean().iloc[-1]
        score_tech = np.clip(55 + (roc_20 * 1.8) + (15 if c.iloc[-1] > ema_20 else -10), 20, 95)
    else:
        score_tech = 65.0

    # 3. 估值空間
    mean_target = info.get('targetMeanPrice')
    curr_p_temp = info.get('currentPrice') or info.get('regularMarketPrice') or (float(hist['Close'].iloc[-1]) if not hist.empty else 100.0)
    if mean_target and curr_p_temp > 0:
        upside = ((mean_target - curr_p_temp) / curr_p_temp) * 100
        score_val = np.clip(50 + (upside * 1.4), 25, 95)
    else:
        score_val = 70.0

    # 4. 法人籌碼
    inst_own = (info.get('heldPercentInstitutions', 0) or 0.65) * 100
    short_ratio = info.get('shortRatio', 2.0) or 2.0
    score_flow = np.clip(inst_own * 0.8 + (10 - min(10, short_ratio)) * 3.0, 30, 95)

    # 5. 宏觀環境
    score_macro = np.clip(85 - (vix_val - 15) * 1.5, 30, 90)

    # 6. ESG / 護城河韌性
    score_esg = 82.5 if info.get('marketCap', 0) > 2e10 else 72.0

    radar_scores = [round(float(score_fund), 1), round(float(score_tech), 1), round(float(score_val), 1), round(float(score_flow), 1), round(float(score_macro), 1), round(float(score_esg), 1)]

    return info, hist, vix_val, tnx_val, dxy_val, radar_scores

info, hist, vix_val, tnx_val, dxy_val, radar_values = fetch_cockpit_data(target_symbol)

company_name = info.get('shortName', target_symbol)
sector = info.get('sector', 'N/A')
industry = info.get('industry', 'N/A')
curr_price = info.get('currentPrice') or info.get('regularMarketPrice') or (float(hist['Close'].iloc[-1]) if not hist.empty else 0.0)
prev_close = info.get('previousClose') or curr_price
chg_pct = ((curr_price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

with col_info:
    st.markdown(f"### {company_name} (`{target_symbol}`)")
    st.caption(f"板塊：**{sector}** ｜ 細分行業：**{industry}** ｜ 交易所：**{info.get('exchange', 'NASDAQ')}**")

with col_price:
    if curr_price > 0:
        st.metric("即時股價", f"${curr_price:.2f}", f"{chg_pct:+.2f}%")
    else:
        st.metric("即時股價", "載入中...")

st.divider()

# ==========================================
# 視覺區塊 1：全市場即時體溫與標的位階 (Top Status Bar)
# ==========================================
st.markdown("#### 🌡️ 全球市場體溫與標的關鍵位階 (Market Pulse)")
m_c1, m_c2, m_c3, m_c4 = st.columns(4)

high_52 = info.get('fiftyTwoWeekHigh', curr_price * 1.1)
low_52 = info.get('fiftyTwoWeekLow', curr_price * 0.8)
pos_52 = ((curr_price - low_52) / (high_52 - low_52) * 100) if high_52 > low_52 else 50.0

m_c1.metric("⚡ VIX 恐慌指數", f"{vix_val:.2f}", "平穩低波動" if vix_val < 20 else "避險警戒", delta_color="normal" if vix_val < 20 else "inverse")
m_c2.metric("🏛️ 10年期美債殖利率", f"{tnx_val:.2f}%", "無風險利率基準")
m_c3.metric("💵 美元指數 (DXY)", f"{dxy_val:.2f}", "全球流動性定錨")
m_c4.metric(f"📍 {target_symbol} 52週位階", f"{pos_52:.1f}%", f"最低 ${low_52:.1f} ｜ 最高 ${high_52:.1f}")

st.markdown("---")

# ==========================================
# 視覺區塊 2：左側快速走勢 + 右側 360° 決策總覽
# ==========================================
row2_left, row2_right = st.columns([1.4, 1])

with row2_left:
    st.markdown(f"#### 📈 {target_symbol} 近半年量價趨勢與 VWAP 成本線")
    if not hist.empty:
        tp = (hist['High'] + hist['Low'] + hist['Close']) / 3.0
        cum_vol = hist['Volume'].cumsum().replace(0, np.nan)
        hist['VWAP'] = (tp * hist['Volume']).cumsum() / cum_vol
        
        fig_quick = go.Figure()
        fig_quick.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
            name=f"{target_symbol} K線"
        ))
        fig_quick.add_trace(go.Scatter(
            x=hist.index, y=hist['VWAP'],
            line=dict(color='#E74C3C', width=2),
            name="VWAP 機構均價"
        ))
        fig_quick.update_layout(
            height=400,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="交易日期",
            yaxis_title="股價 ($ USD)",
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig_quick, use_container_width=True, key=f"quick_chart_{target_symbol}")
    else:
        st.info(f"⚠️ 正在加載 {target_symbol} 歷史數據...")

with row2_right:
    st.markdown(f"#### 🎯 {target_symbol} 360° 全維度量化評分雷達")
    
    radar_categories = ['基本面質量', '技術動量', '估值安全', '法人籌碼', '宏觀流動', 'ESG永續']
    master_quick_score = round(sum(radar_values) / len(radar_values), 1)

    fig_radar_cockpit = go.Figure()
    fig_radar_cockpit.add_trace(go.Scatterpolar(
        r=radar_values,
        theta=radar_categories,
        fill='toself',
        fillcolor='rgba(46, 204, 113, 0.25)',
        line=dict(color='#2ECC71', width=2.5),
        name=target_symbol
    ))
    fig_radar_cockpit.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=320,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False
    )
    st.plotly_chart(fig_radar_cockpit, use_container_width=True, key=f"radar_chart_{target_symbol}")
    
    status_text = "強力看多 (Overweight)" if master_quick_score >= 80 else ("逢低佈局 (Accumulate)" if master_quick_score >= 65 else "中性防守 (Neutral)")
    st.success(f"""
    🏆 **{target_symbol} 全維度總分：`{master_quick_score} / 100`（{status_text}）**
    - 點選左側 **「1~9」模組** 即可進入各項深度分析與完整操盤計畫。
    """)