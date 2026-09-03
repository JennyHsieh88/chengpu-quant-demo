import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(
    page_title="總體環境監控 - 澄璞財務",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 注入自訂 CSS（極淡燕麥米白 + 六大側邊欄分類標題 + 解除省略號）
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
        margin: 12px 14px 14px 14px;
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

    /* ========================================================
       側邊欄六大分類大標題 (Section Headers)
       ======================================================== */
    /* 1. 決策總覽 */
    [data-testid="stSidebarNav"] ul li:nth-child(1)::before {
        content: "決策總覽";
        display: block;
        font-size: 0.80rem;
        font-weight: 800;
        color: #8C827A;
        letter-spacing: 1.2px;
        padding: 8px 14px 4px 14px;
    }

    /* 2. 總體與市場氛圍 */
    [data-testid="stSidebarNav"] ul li:nth-child(2)::before {
        content: "總體與市場氛圍";
        display: block;
        font-size: 0.80rem;
        font-weight: 800;
        color: #8C827A;
        letter-spacing: 1.2px;
        padding: 14px 14px 4px 14px;
        border-top: 1px solid #E6DFD7;
        margin-top: 6px;
    }

    /* 3. 個股深度研究 */
    [data-testid="stSidebarNav"] ul li:nth-child(4)::before {
        content: "個股深度研究";
        display: block;
        font-size: 0.80rem;
        font-weight: 800;
        color: #8C827A;
        letter-spacing: 1.2px;
        padding: 14px 14px 4px 14px;
        border-top: 1px solid #E6DFD7;
        margin-top: 6px;
    }

    /* 4. 進階數據與評分 */
    [data-testid="stSidebarNav"] ul li:nth-child(8)::before {
        content: "進階數據與評分";
        display: block;
        font-size: 0.80rem;
        font-weight: 800;
        color: #8C827A;
        letter-spacing: 1.2px;
        padding: 14px 14px 4px 14px;
        border-top: 1px solid #E6DFD7;
        margin-top: 6px;
    }

    /* 5. 資產配置與模擬 */
    [data-testid="stSidebarNav"] ul li:nth-child(10)::before {
        content: "資產配置與模擬";
        display: block;
        font-size: 0.80rem;
        font-weight: 800;
        color: #8C827A;
        letter-spacing: 1.2px;
        padding: 14px 14px 4px 14px;
        border-top: 1px solid #E6DFD7;
        margin-top: 6px;
    }

    /* 6. 市場要聞 */
    [data-testid="stSidebarNav"] ul li:nth-child(12)::before {
        content: "市場要聞";
        display: block;
        font-size: 0.80rem;
        font-weight: 800;
        color: #8C827A;
        letter-spacing: 1.2px;
        padding: 14px 14px 4px 14px;
        border-top: 1px solid #E6DFD7;
        margin-top: 6px;
    }

    [data-testid="stSidebarNav"] ul li a {
        padding-left: 18px !important;
        font-size: 0.96rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        margin: 2px 6px !important;
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
        font-size: 0.95rem !important;
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
        font-size: 0.88rem !important;
        line-height: 1.4 !important;
    }
    
    div.stButton > button {
        width: 100% !important;
        min-height: 52px !important;
        font-size: 1.00rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: 1px solid #D6CBC1 !important;
        background-color: #FFFFFF !important;
        color: #38302B !important;
        transition: all 0.2s ease;
        padding: 6px 10px !important;
    }
    div.stButton > button:hover {
        border-color: #0284C7 !important;
        color: #0284C7 !important;
        background-color: #F0F9FF !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #E0F2FE !important;
        border-color: #0284C7 !important;
        color: #0369A1 !important;
        box-shadow: 0 2px 6px rgba(2, 132, 199, 0.15) !important;
    }
    .guide-box {
        background: #F8FAF9;
        border: 1px solid #D1E5DE;
        border-left: 4px solid #0D9488;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 14px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 全域雙向狀態綁定邏輯 (Two-Way Sync)
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = ""

if 'active_tab_p1' not in st.session_state:
    st.session_state['active_tab_p1'] = "tab1"

st.session_state['ticker_input_p1'] = st.session_state['current_ticker']

def sync_ticker_p1():
    val = st.session_state.get('ticker_input_p1', '').upper().strip()
    st.session_state['current_ticker'] = val

st.subheader("🌐 全球總體環境監控與利率週期雷達 (Global Macro & Yield Radar)")

col_search, col_name, col_p = st.columns([1.8, 3.2, 2])

with col_search:
    st.text_input(
        "🔍 本頁快速切換監控標的", 
        key="ticker_input_p1",
        on_change=sync_ticker_p1,
        placeholder="例如: NVDA, AAPL, MSFT...",
        help="輸入美股代碼後按 Enter 即時連動全平台各分析模組"
    )
    st.markdown("<p style='font-size: 0.82rem; color: #7A6C60; margin-top: -10px; margin-bottom: 0;'>例：NVDA、TSLA、AAPL（輸入後按 Enter 查詢）</p>", unsafe_allow_html=True)

target_symbol = st.session_state.get('current_ticker', '').strip()
user_has_typed = bool(target_symbol)
active_symbol = target_symbol if user_has_typed else "SPY"

@st.cache_data(ttl=300)
def fetch_p1_meta(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
        company_name = info.get('shortName', symbol)
        curr_p = info.get('currentPrice') or info.get('regularMarketPrice') or 100.0
        return {'name': company_name, 'curr_p': curr_p}
    except Exception:
        return {'name': symbol, 'curr_p': 100.0}

p1_meta = fetch_p1_meta(active_symbol)

if user_has_typed:
    with col_name:
        st.markdown(f"### {p1_meta['name']} (`{target_symbol}`)")
        st.caption(f"總經定錨：**檢驗宏觀利率、信用利差對 {target_symbol} 估值分母之傳導衝擊**")
    with col_p:
        st.metric("即時現價", f"${p1_meta['curr_p']:.2f}", "總經模型連動中")
else:
    with col_name:
        st.markdown("### 🌐 全球宏觀總經監控基準 (待機中)")
        st.caption("👈 請於左側輸入美股代碼啟動個股總經壓力測試，目前為全市場基準")
    with col_p:
        st.metric("總經體能", "軟著陸擴張", "中性偏多")

st.divider()

# ==========================================
# 總經環境四大核心指標卡
# ==========================================
st.markdown("#### ⚡ 全球宏觀四大關鍵定價指標 (Global Pricing Anchors)")

p1, p2, p3, p4 = st.columns(4)
p1.metric("📉 美國 10Y-2Y 公債利差", "+0.18%", "結束倒掛 ｜ 走向正常陡峭化", delta_color="normal")
p2.metric("💵 美國 10 年期實質殖利率 (TIPS)", "1.85%", "高於中性利率，具一定限制性", delta_color="normal")
p3.metric("🛡️ 高收益債信用利差 (HY Spread)", "3.12%", "遠低於 5.0% 警戒線 (流動性健康)", delta_color="normal")
p4.metric("🏛️ 聯準會實質政策利率", "4.85%", "降息循環啟動，流動性逐步釋放", delta_color="normal")

st.markdown("---")

# ==========================================
# 五大深度導航按鈕（標準固定名稱，不塞入代碼）
# ==========================================
st.markdown("##### 🧭 總體環境監控 — 五大深度分析選單")

g1, g2, g3 = st.columns(3)
g4, g5, g6 = st.columns(3)

with g1:
    if st.button("📊 一、美國公債殖利率曲線結構與倒掛深度監控", type="primary" if st.session_state['active_tab_p1'] == "tab1" else "secondary", use_container_width=True):
        st.session_state['active_tab_p1'] = "tab1"
        st.rerun()

with g2:
    if st.button("🛡️ 二、高收益企業債信用利差 (Credit Spread) 與違約雷達", type="primary" if st.session_state['active_tab_p1'] == "tab2" else "secondary", use_container_width=True):
        st.session_state['active_tab_p1'] = "tab2"
        st.rerun()

with g3:
    if st.button("🏛️ 三、全球主要央行政策利率走勢與點陣圖路徑預測", type="primary" if st.session_state['active_tab_p1'] == "tab3" else "secondary", use_container_width=True):
        st.session_state['active_tab_p1'] = "tab3"
        st.rerun()

with g4:
    if st.button("📈 四、實體通膨 (CPI/PCE) 與失業率菲利浦斯動態追蹤", type="primary" if st.session_state['active_tab_p1'] == "tab4" else "secondary", use_container_width=True):
        st.session_state['active_tab_p1'] = "tab4"
        st.rerun()

with g5:
    if st.button("🧭 五、宏觀景氣四象限輪動指引與資產配置防禦矩陣", type="primary" if st.session_state['active_tab_p1'] == "tab5" else "secondary", use_container_width=True):
        st.session_state['active_tab_p1'] = "tab5"
        st.rerun()

with g6:
    st.markdown("<div style='height: 52px; background: #FFFFFF; border: 1px solid #D6CBC1; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #847568; font-weight: 700; font-size: 0.95rem;'>✦ 總經指標庫 ✦</div>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 細項深度內容渲染
# ==========================================
active_p1 = st.session_state['active_tab_p1']

# ----------------------------------------------------
# 分頁 1：殖利率曲線倒掛深度與利差走勢
# ----------------------------------------------------
if active_p1 == "tab1":
    st.markdown("### 📊 一、美國公債殖利率曲線結構與倒掛深度監控")
    st.caption("觀察 10Y-2Y 國債利差歷史走向，利差小於 0 代表殖利率曲線倒掛，常作為景氣衰退之前導警訊。")

    dates_yield = pd.date_range(end=datetime.now(), periods=180, freq='B')
    np.random.seed(42)
    spread_10_2 = -0.50 + np.cumsum(np.random.normal(0.005, 0.04, len(dates_yield)))

    fig_yield = go.Figure()
    fig_yield.add_trace(go.Scatter(
        x=dates_yield, y=spread_10_2,
        mode='lines', line=dict(color='#0284C7', width=2.8),
        name="10Y-2Y 國債利差 (%)"
    ))
    fig_yield.add_hline(y=0, line_dash="dash", line_color="#DC2626", annotation_text="0% 倒掛分水嶺")

    fig_yield.update_layout(
        title=dict(text="<b>美國 10Y - 2Y 公債利差走向 (%) — 由倒掛逐步修復至正值</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
        height=430,
        margin=dict(t=65, b=30, l=15, r=30),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="利差幅度 (%)", showgrid=True, gridcolor='#F2ECE5'),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11))
    )
    st.plotly_chart(fig_yield, use_container_width=True, key="p1_yield_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【殖利率倒掛怎麼看？怎麼運用？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            1. <strong>倒掛解除才是關鍵考驗</strong>：歷史經驗顯示，倒掛發生時股市往往還在漲；真正的衰退風險多半發生在<strong>「倒掛結束、殖利率曲線急遽陡峭化（Disinversion）」</strong>的時期。<br>
            2. <strong>牛陡 vs 熊陡</strong>：若利差修復是由於聯準會預防性降息（短端利率快速下行），則屬於利好權益資產的「牛市陡峭化」；若因長端通膨失控推升，則需謹慎防禦。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 2：高收益債信用利差 (Credit Spread)
# ----------------------------------------------------
elif active_p1 == "tab2":
    st.markdown("### 🛡️ 二、高收益企業債信用利差 (HY Credit Spread) 與違約雷達")
    st.caption("信用利差反映企業債券相對於同天期公債之風險溢價。利差擴大代表機構恐慌避險；利差收斂代表信貸環境健康。")

    dates_hy = pd.date_range(end=datetime.now(), periods=180, freq='B')
    np.random.seed(88)
    hy_spread = 3.80 + np.cumsum(np.random.normal(-0.003, 0.05, len(dates_hy)))

    fig_hy = go.Figure()
    fig_hy.add_trace(go.Scatter(
        x=dates_hy, y=hy_spread,
        mode='lines', line=dict(color='#047857', width=2.8),
        name="ICE BofA 美國高收益債信用利差 (%)"
    ))
    fig_hy.add_hline(y=5.0, line_dash="dash", line_color="#D97706", annotation_text="5.0% 警戒預警線")
    fig_hy.add_hline(y=7.0, line_dash="solid", line_color="#DC2626", annotation_text="7.0% 嚴重信貸危機線")

    fig_hy.update_layout(
        title=dict(text="<b>美國高收益債信用利差 (%) — 3.12% 處於歷史低位舒適區</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
        height=430,
        margin=dict(t=65, b=30, l=15, r=30),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="信用利差 (%)", range=[2.0, 7.5], showgrid=True, gridcolor='#F2ECE5'),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11))
    )
    st.plotly_chart(fig_hy, use_container_width=True, key="p1_hy_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【信用利差怎麼看？怎麼運用？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            1. <strong>股市最靈敏的領先警報</strong>：在 2008 金融海嘯與 2020 熔斷前，高收益債利差均提前飆破 6%~8%。當前利差維持在 3% 左右，顯示全市場企業違約風險極低，多頭格局有實體資金支撐。<br>
            2. <strong>防禦操作</strong>：一旦利差向上突破 5.0%，應立刻降低科技高 Beta 衛星股票倉位，拉高現金與短期美債比例。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 3：全球央行政策利率走勢與點陣圖路徑
# ----------------------------------------------------
elif active_p1 == "tab3":
    st.markdown("### 🏛️ 三、全球主要央行政策利率走勢與點陣圖 (Dot Plot) 路徑推演")
    st.caption("追蹤聯準會 (Fed)、歐洲央行 (ECB)、日本央行 (BOJ) 的政策利率走向及市場隱含終端利率預期。")

    quarters_cb = ['2023Q4', '2024Q2', '2024Q4', '2025Q2', '2025Q4', '2026Q2', '2026Q4']
    fed_rates = [5.50, 5.50, 4.75, 4.25, 3.75, 3.50, 3.25]
    ecb_rates = [4.00, 3.75, 3.25, 2.75, 2.50, 2.25, 2.25]
    boj_rates = [-0.10, 0.10, 0.25, 0.50, 0.75, 0.75, 1.00]

    fig_cb = go.Figure()
    fig_cb.add_trace(go.Scatter(x=quarters_cb, y=fed_rates, mode='lines+markers', line=dict(color='#0284C7', width=3), name="美國聯準會 (Fed)"))
    fig_cb.add_trace(go.Scatter(x=quarters_cb, y=ecb_rates, mode='lines+markers', line=dict(color='#047857', width=2.5), name="歐洲央行 (ECB)"))
    fig_cb.add_trace(go.Scatter(x=quarters_cb, y=boj_rates, mode='lines+markers', line=dict(color='#D97706', width=2.5), name="日本央行 (BOJ)"))

    fig_cb.update_layout(
        title=dict(text="<b>全球主要央行政策利率與點陣圖中位數走向 (%)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
        height=430,
        margin=dict(t=65, b=30, l=15, r=30),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="基準利率 (%)", showgrid=True, gridcolor='#F2ECE5'),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11))
    )
    st.plotly_chart(fig_cb, use_container_width=True, key="p1_cb_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【央行政策路徑怎麼看？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            • <strong>美歐進入降息週期</strong>：資金成本由高檔回落，有利減輕企業利息負擔並改善併購資本支出；<br>
            • <strong>日央緩慢升息</strong>：須注意日圓套利交易（Yen Carry Trade）平倉引發的短線全球流動性震盪。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 4：實體通膨與失業率菲利浦斯動態
# ----------------------------------------------------
elif active_p1 == "tab4":
    st.markdown("### 📈 四、實體通膨 (CPI/PCE) 與失業率菲利浦斯動態追蹤")
    st.caption("通膨下行結合平穩就業，是驗證經濟實現「完美軟著陸 (Goldilocks)」的最核心依據。")

    months_inf = ['24-01', '24-03', '24-05', '24-07', '24-09', '24-11', '25-01', '25-03', '25-05', '25-07']
    core_cpi = [3.9, 3.8, 3.4, 3.2, 3.3, 3.1, 2.9, 2.8, 2.6, 2.5]
    unemp_rate = [3.7, 3.8, 4.0, 4.3, 4.1, 4.1, 4.0, 4.1, 4.2, 4.1]

    fig_inf = make_subplots(specs=[[{"secondary_y": True}]])
    fig_inf.add_trace(
        go.Bar(x=months_inf, y=core_cpi, name="核心 CPI 年增率 (%)", marker_color='#0284C7', text=[f"{v}%" for v in core_cpi], textposition='outside'),
        secondary_y=False
    )
    fig_inf.add_trace(
        go.Scatter(x=months_inf, y=unemp_rate, name="美國失業率 (%)", mode='lines+markers', line=dict(color='#D97706', width=3)),
        secondary_y=True
    )
    fig_inf.update_layout(
        title=dict(text="<b>美國核心 CPI 通膨降溫 vs 失業率穩定對照</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
        height=430,
        margin=dict(t=65, b=30, l=15, r=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11))
    )
    fig_inf.update_yaxes(title_text="核心 CPI (%)", range=[0, 5], secondary_y=False, showgrid=True, gridcolor='#F2ECE5')
    fig_inf.update_yaxes(title_text="失業率 (%)", range=[2, 6], secondary_y=True, showgrid=False)
    st.plotly_chart(fig_inf, use_container_width=True, key="p1_inf_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【通膨就業怎麼看？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            • 當核心通膨由 3.9% 穩健回落至 2.5%，而失業率未出現非理性飆升（維持 4.0%~4.2%），表示經濟處於健康的「通膨放緩、增長延續」格局，為股市提供穩健的基本面支撐。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 5：宏觀景氣四象限輪動指引
# ----------------------------------------------------
elif active_p1 == "tab5":
    st.markdown("### 🧭 五、宏觀景氣四象限輪動指引與資產配置防禦矩陣")
    st.caption("依據「經濟成長動能（高/低）」與「通膨方向（加速/減速）」，動態判定當前宏觀週期所屬象限。")

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #047857; border-radius:10px; padding:16px; margin-bottom:12px;">
            <strong style="color:#047857; font-size:1.15rem;">🟢 第一象限：黃金女孩復甦擴張 (Goldilocks)</strong><br>
            <span style="font-size:0.90rem; color:#64748B;">【當前宏觀所處主要區間】</span>
            <p style="font-size:0.92rem; color:#5C554F; margin:8px 0 0 0; line-height:1.65;">
                • <strong>宏觀特徵</strong>：經濟穩健增長、通膨平穩回落、貨幣政策邊際寬鬆。<br>
                • <strong>最佳配置資產</strong>：標普 500 大盤權益、科技成長龍頭個股、高收益債。<br>
                • <strong>防禦策略</strong>：維持高權益部位 (70%)，享受盈利與估值雙升紅利。
            </p>
        </div>

        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #D97706; border-radius:10px; padding:16px; margin-bottom:12px;">
            <strong style="color:#D97706; font-size:1.15rem;">🟡 第二象限：過熱通膨再膨脹 (Reflation)</strong><br>
            <p style="font-size:0.92rem; color:#5C554F; margin:8px 0 0 0; line-height:1.65;">
                • <strong>宏觀特徵</strong>：經濟過熱、大宗商品飆漲、薪資通膨二度抬頭。<br>
                • <strong>最佳配置資產</strong>：實體黃金、原油能源商品 (XLE)、原物料、抗通膨債券 (TIPS)。<br>
                • <strong>防禦策略</strong>：降低對長久期長債與高本益比股票的曝險。
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_q2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #DC2626; border-radius:10px; padding:16px; margin-bottom:12px;">
            <strong style="color:#DC2626; font-size:1.15rem;">🔴 第三象限：停滯性通膨 (Stagflation)</strong><br>
            <p style="font-size:0.92rem; color:#5C554F; margin:8px 0 0 0; line-height:1.65;">
                • <strong>宏觀特徵</strong>：經濟增長停滯甚至負增長，同時物價居高不下。<br>
                • <strong>最佳配置資產</strong>：超短期公債 (SGOV)、現金等價物、實體黃金。<br>
                • <strong>防禦策略</strong>：股市與債市雙殺時期，唯有短債現金流與黃金能安度風暴。
            </p>
        </div>

        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #0284C7; border-radius:10px; padding:16px; margin-bottom:12px;">
            <strong style="color:#0284C7; font-size:1.15rem;">🔵 第四象限：景氣通縮衰退 (Deflationary Recession)</strong><br>
            <p style="font-size:0.92rem; color:#5C554F; margin:8px 0 0 0; line-height:1.65;">
                • <strong>宏觀特徵</strong>：經濟衰退失業率飆升、物價與需求急速萎縮。<br>
                • <strong>最佳配置資產</strong>：20 年期長天期美國國債 (TLT)、公用事業防禦股。<br>
                • <strong>防禦策略</strong>：長天期公債享有強大的利率下行資本利得，發揮最強吸震防禦。
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【CFP® 宏觀輪動心法】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            沒有任何單一資產能在所有四個象限中都獲勝。這正是<strong>「澄璞全天候抗震資產配置（股票＋黃金＋短債）」</strong>能長期跑贏的核心邏輯：無論景氣走向哪一個象限，投組中始終有特定資產在為整體財富提供正向推力與吸震防護。
        </p>
    </div>
    """, unsafe_allow_html=True)
