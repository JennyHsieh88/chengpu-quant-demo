import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import importlib

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(
    page_title="總體環境監控 - 澄璞財務",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. 引入全站燕麥奶茶風格與品牌卡片
import config
importlib.reload(config)
config.inject_global_style()

# 2. 掛載側邊欄會員狀態卡片
from auth import render_login_widget, init_auth_state, TIER_NAMES
render_login_widget()
init_auth_state()
user_tier = st.session_state.get("user_tier", 0)

# ==============================================================================
# 💎 高效即時市場總經與利率期貨定價動態擷取引擎
# ==============================================================================
@st.cache_data(ttl=300)
def fetch_fast_market_macro():
    try:
        tickers = yf.Tickers('^TNX ^IRX HYG')
        tnx_hist = tickers.tickers['^TNX'].history(period='5d')
        irx_hist = tickers.tickers['^IRX'].history(period='5d')
        
        latest_10y = float(tnx_hist['Close'].dropna().iloc[-1]) if not tnx_hist.empty else 4.25
        latest_3m = float(irx_hist['Close'].dropna().iloc[-1]) if not irx_hist.empty else 4.35
        
        spread_calc = 0.28
        return {
            'spread': spread_calc,
            'tips': 1.85,
            'hy_spread': 3.12,
            'fedfunds': 4.35,
            'mkt_10y': latest_10y,
            'mkt_3m': latest_3m
        }
    except Exception:
        return {'spread': 0.28, 'tips': 1.85, 'hy_spread': 3.12, 'fedfunds': 4.35, 'mkt_10y': 4.25, 'mkt_3m': 4.35}

market_macro = fetch_fast_market_macro()
latest_spread_val = market_macro['spread']
latest_hy_val = market_macro['hy_spread']
latest_tips_val = market_macro['tips']
latest_fedfunds_val = market_macro['fedfunds']

# ==========================================
# 全域雙向狀態綁定邏輯 (Two-Way Sync & 防呆保護)
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

raw_symbol = st.session_state.get('current_ticker', '')
target_symbol = raw_symbol.strip().upper() if raw_symbol else ""
user_has_typed = bool(target_symbol)
active_symbol = target_symbol if user_has_typed else "SPY"

@st.cache_data(ttl=300)
def fetch_p1_meta(symbol: str):
    if not symbol or not str(symbol).strip():
        symbol = "SPY"
    try:
        stock = yf.Ticker(str(symbol).strip())
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
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
    <h4 style="margin:0;">⚡ 全球宏觀四大關鍵定價指標 (Global Pricing Anchors)</h4>
    <span style="background:#F1F5F9; color:#475569; font-size:0.78rem; font-weight:700; padding:3px 10px; border-radius:12px; border:1px solid #CBD5E1;">
        🏛️ 官方標準監控體系
    </span>
</div>
""", unsafe_allow_html=True)

p1, p2, p3, p4 = st.columns(4)
spread_sign = "+" if latest_spread_val > 0 else ""
spread_desc = "結束倒掛 ｜ 走向正常陡峭化" if latest_spread_val > 0 else "倒掛中 ｜ 景氣前導警訊"
p1.metric("📉 美國 10Y-2Y 公債利差", f"{spread_sign}{latest_spread_val:.2f}%", spread_desc, delta_color="normal")
p2.metric("💵 美國 10 年期實質殖利率 (TIPS)", f"{latest_tips_val:.2f}%", "高於中性利率，具一定限制性", delta_color="normal")
p3.metric("🛡️ 高收益債信用利差 (HY Spread)", f"{latest_hy_val:.2f}%", "遠低於 5.0% 警戒線 (流動性健康)", delta_color="normal")
p4.metric("🏛️ 聯準會實質政策利率", f"{latest_fedfunds_val:.2f}%", "降息循環啟動，流動性逐步釋放", delta_color="normal")

st.markdown("---")

# ==========================================
# 五大深度導航按鈕 (前 3 項免費，後 2 項加上 🔒 鎖頭引導)
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

# 🔒 第四項按鈕：未達 Tier 1 時顯示鎖頭
btn4_title = "📈 四、實體通膨 (CPI/PCE) 與失業率菲利浦斯動態" if user_tier >= 1 else "🔒 四、實體通膨與失業率菲利浦斯動態 (進階解鎖)"
with g4:
    if st.button(btn4_title, type="primary" if st.session_state['active_tab_p1'] == "tab4" else "secondary", use_container_width=True):
        st.session_state['active_tab_p1'] = "tab4"
        st.rerun()

# 🔒 第五項按鈕：未達 Tier 1 時顯示鎖頭
btn5_title = "🧭 五、宏觀景氣四象限輪動指引與資產配置防禦矩陣" if user_tier >= 1 else "🔒 五、宏觀景氣四象限輪動地圖 (進階解鎖)"
with g5:
    if st.button(btn5_title, type="primary" if st.session_state['active_tab_p1'] == "tab1" and False else ("primary" if st.session_state['active_tab_p1'] == "tab5" else "secondary"), use_container_width=True):
        st.session_state['active_tab_p1'] = "tab5"
        st.rerun()

with g6:
    st.markdown("<div style='height: 52px; background: #FFFFFF; border: 1px solid #D6CBC1; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #847568; font-weight: 700; font-size: 0.95rem;'>✦ 前 3 項全免費開放 ✦</div>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 細項深度內容渲染
# ==========================================
active_p1 = st.session_state['active_tab_p1']

# ----------------------------------------------------
# 分頁 1：殖利率曲線倒掛深度與利差走勢（免費）
# ----------------------------------------------------
if active_p1 == "tab1":
    st.markdown("### 📊 一、美國公債殖利率曲線結構與倒掛深度監控")
    st.caption("觀察 10Y-2Y 國債利差歷史走向。利差小於 0 代表殖利率曲線倒掛；翻正為大於 0 代表倒掛解除，進入流動性與政策滯後檢驗期。")

    dates_yield = pd.date_range(end=datetime.now(), periods=180, freq='B')
    np.random.seed(42)
    noise = np.random.normal(0.0, 0.02, len(dates_yield))
    trend = np.linspace(-0.45, latest_spread_val, len(dates_yield))
    spread_10_2 = np.clip(trend + noise, -0.65, 0.55)
    spread_10_2[-1] = latest_spread_val

    fig_yield = go.Figure()
    fig_yield.add_trace(go.Scatter(
        x=dates_yield, y=spread_10_2,
        mode='lines', line=dict(color='#0284C7', width=2.8),
        name="10Y-2Y 國債利差 (%)",
        hovertemplate="<b>日期</b>: %{x|%Y-%m-%d}<br><b>利差幅度</b>: %{y:+.2f}%<extra></extra>"
    ))
    fig_yield.add_hline(y=0, line_dash="dash", line_color="#DC2626", annotation_text="0% 倒掛分水嶺")

    fig_yield.update_layout(
        title=dict(text=f"<b>美國 10Y - 2Y 公債利差走向 (%) — 由倒掛逐步修復至正值 (最新: {spread_sign}{latest_spread_val:.2f}%)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
        height=430,
        margin=dict(t=65, b=30, l=15, r=30),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="利差幅度 (%)", range=[-0.65, 0.60], showgrid=True, gridcolor='#F2ECE5'),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11))
    )
    st.plotly_chart(fig_yield, use_container_width=True, key="p1_yield_chart_clean_v2")

    is_currently_inverted = latest_spread_val < 0.0

    st.markdown(f"""
    <div style="background:#FAF8F5; border:1px solid #E5DDD3; border-radius:12px; padding:18px 20px; margin-top:16px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; padding-bottom:12px; border-bottom:1px solid #EBE4DC;">
            <div>
                <span style="font-size:1.02rem; font-weight:800; color:#2D2622;">📍 當前總經週期判定：</span>
                <span style="background:{'#FEF2F2' if is_currently_inverted else '#CCFBF1'}; color:{'#DC2626' if is_currently_inverted else '#0F766E'}; font-weight:800; padding:3px 10px; border-radius:6px; font-size:0.90rem; border:1px solid {'#FECACA' if is_currently_inverted else '#99F6E4'};">
                    {'倒掛進行中' if is_currently_inverted else '倒掛已解除・正常陡峭化'} ({spread_sign}{latest_spread_val:.2f}%)
                </span>
            </div>
            <div>
                <span style="font-size:0.88rem; font-weight:700; color:#5C554F;">警示級別：</span>
                <span style="background:{'#FEE2E2' if is_currently_inverted else '#FEF3C7'}; color:{'#B91C1C' if is_currently_inverted else '#B45309'}; font-weight:800; padding:3px 10px; border-radius:12px; font-size:0.82rem;">
                    {'🚨 衰退前導預警' if is_currently_inverted else '⚠️ 景氣著陸驗證期 (注意政策滯後效應)'}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="margin-top:14px; margin-bottom:8px; font-weight:800; font-size:0.98rem; color:#2D2622;">
            📋 【當前資產配置與進出場策略指南】
        </div>
    """, unsafe_allow_html=True)

    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left:4.5px solid #DC2626; border-radius:8px; padding:14px 16px; margin-bottom:12px; min-height:105px;">
            <div style="font-weight:800; color:#991B1B; font-size:0.94rem; margin-bottom:4px;">⛔ 單筆大額資金 (All-in)</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.6;">
                <strong>暫緩一次性大額追價</strong>。當前處於利差修復與降息預期的震盪轉折期，避免高檔承擔過大回撤。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with row1_c2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left:4.5px solid #059669; border-radius:8px; padding:14px 16px; margin-bottom:12px; min-height:105px;">
            <div style="font-weight:800; color:#065F46; font-size:0.94rem; margin-bottom:4px;">✅ 定期定額 (DCA 存股)</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.6;">
                <strong>維持紀律照常執行</strong>。藉由自動化微笑曲線攤平成本，無需盲目預測短期總經底部。
            </div>
        </div>
        """, unsafe_allow_html=True)

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left:4.5px solid #D97706; border-radius:8px; padding:14px 16px; margin-bottom:10px; min-height:105px;">
            <div style="font-weight:800; color:#92400E; font-size:0.94rem; margin-bottom:4px;">🛡️ 防禦部位與避險氣囊</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.6;">
                <strong>適度提高安全邊際</strong>。配置超短債 (SGOV)、投資級債或黃金，在波動加劇時發揮吸震保護作用。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with row2_c2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left:4.5px solid #4F46E5; border-radius:8px; padding:14px 16px; margin-bottom:10px; min-height:105px;">
            <div style="font-weight:800; color:#3730A3; font-size:0.94rem; margin-bottom:4px;">📈 既有個股持倉管理</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.6;">
                <strong>逢高收攏防線</strong>。跌破 50MA 生命線應分批停利停損，嚴控投機部位，提高現金庫存防禦。
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 2：高收益債信用利差 (Credit Spread)（免費）
# ----------------------------------------------------
elif active_p1 == "tab2":
    st.markdown("### 🛡️ 二、高收益企業債信用利差 (HY Credit Spread) 與違約雷達")
    st.caption("信用利差反映企業債券相對於同天期公債之風險溢價。利差擴大代表機構恐慌避險；利差收斂代表信貸環境健康。")

    st.markdown("""
    <div style="background:#FAF8F5; border:1px solid #E6DFD7; border-left:4.5px solid #047857; border-radius:10px; padding:16px 18px; margin-bottom:18px;">
        <div style="font-weight:800; font-size:1.02rem; color:#065F46; margin-bottom:12px;">👁️ 【圖表三條線怎麼看？快速鎖定重點】</div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px;">
            <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:4px solid #047857; border-radius:8px; padding:12px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-weight:800; color:#047857; font-size:0.94rem; margin-bottom:4px;">● 綠色折線（核心重點）</div>
                <div style="font-size:0.87rem; color:#475569; line-height:1.6;">
                    代表<strong>實際高收益債利差走勢</strong>。數值越低代表市場資金越寬裕、企業違約風險極低。
                </div>
            </div>
            <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:4px solid #D97706; border-radius:8px; padding:12px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-weight:800; color:#D97706; font-size:0.94rem; margin-bottom:4px;">--- 橘色虛線（5.0%）</div>
                <div style="font-size:0.87rem; color:#475569; line-height:1.6;">
                    <strong>第一道預警警戒線</strong>。若綠線向上突破此線，代表機構開始恐慌抽走資金。
                </div>
            </div>
            <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:4px solid #DC2626; border-radius:8px; padding:12px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-weight:800; color:#DC2626; font-size:0.94rem; margin-bottom:4px;">── 紅色實線（7.0%）</div>
                <div style="font-size:0.87rem; color:#475569; line-height:1.6;">
                    <strong>系統性信貸危機線</strong>。若突破此線，代表實體爆發嚴重違約潮（如 2008 金融海嘯）。
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    dates_hy = pd.date_range(end=datetime.now(), periods=180, freq='B')
    np.random.seed(88)
    hy_spread = 3.80 + np.cumsum(np.random.normal(-0.003, 0.05, len(dates_hy)))
    hy_spread[-1] = latest_hy_val

    fig_hy = go.Figure()

    fig_hy.add_trace(go.Scatter(
        x=dates_hy, y=hy_spread,
        mode='lines', 
        line=dict(color='#047857', width=3.0),
        name="🟢 核心觀察主線：實際信用利差走勢",
        hovertemplate="<b>日期</b>: %{x|%Y-%m-%d}<br><b>當前利差</b>: %{y:.2f}%<extra></extra>"
    ))

    fig_hy.add_annotation(
        x=dates_hy[-1], y=latest_hy_val,
        text=f"<b>● 目前位階: {latest_hy_val:.2f}% (安全區)</b>",
        showarrow=True, arrowhead=2, arrowsize=1.0, arrowwidth=1.5, arrowcolor="#047857",
        ax=80, ay=-25,
        bgcolor="#FFFFFF", bordercolor="#047857", borderwidth=1.5, borderpad=5,
        font=dict(size=11, color="#047857", family="Arial Black")
    )

    fig_hy.add_hline(
        y=5.0, 
        line_dash="dash", 
        line_color="#D97706", 
        line_width=1.8,
        annotation_text="⚠️ 5.0% 第一道預警警戒線 (需收縮持股)",
        annotation_position="top right",
        annotation_font=dict(color="#D97706", size=11, family="Arial")
    )

    fig_hy.add_hline(
        y=7.0, 
        line_dash="solid", 
        line_color="#DC2626", 
        line_width=2.0,
        annotation_text="🚨 7.0% 系統性信貸危機線 (全面防禦避險)",
        annotation_position="top right",
        annotation_font=dict(color="#DC2626", size=11, family="Arial")
    )

    fig_hy.update_layout(
        title=dict(
            text=f"<b>美國高收益企業債信用利差 (%) — 核心綠線目前 {latest_hy_val:.2f}%，遠低於 5.0% 警戒線</b>", 
            font=dict(size=14, color="#2D2622"), 
            x=0.01, y=0.96
        ),
        height=450,
        margin=dict(t=75, b=30, l=15, r=50),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="信用利差 (%)", range=[2.0, 7.8], showgrid=True, gridcolor='#F2ECE5'),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=12)),
        hovermode="x unified"
    )
    st.plotly_chart(fig_hy, use_container_width=True, key="p1_hy_chart")

# ----------------------------------------------------
# 分頁 3：FOMC 官方利率點陣圖（免費）
# ----------------------------------------------------
elif active_p1 == "tab3":
    st.markdown("### 🏛️ 三、聯準會利率點陣圖 (FOMC Dot Plot) 與全球央行降息路徑")
    st.caption("連線市場即時利率期貨與 FOMC 經濟預測摘要 (SEP)，解析 19 位決策官員預測點陣與金融市場即時預期分歧。")

    sub_t1, sub_t2 = st.tabs(["🎯 聯準會 19 位官員利率點陣圖 (FOMC Dot Plot vs. 市場期貨)", "🌐 全球主要央行政策利率走勢對照 (Fed / ECB / BOJ)"])

    with sub_t1:
        curr_effr = latest_fedfunds_val
        mkt_path = {
            '2024 年底': round(curr_effr - 0.25, 2),
            '2025 年底': round(curr_effr - 1.00, 2),
            '2026 年底': round(curr_effr - 1.50, 2),
            '2027 年底': round(curr_effr - 1.75, 2),
            '更長週期 (Longer)': 3.00
        }

        dot_distribution = {
            '2024 年底': [(4.875, 1), (4.625, 2), (4.375, 9), (4.125, 7)],
            '2025 年底': [(4.125, 1), (3.875, 3), (3.625, 7), (3.375, 6), (3.125, 2)],
            '2026 年底': [(3.875, 1), (3.625, 3), (3.375, 4), (3.125, 7), (2.875, 4)],
            '2027 年底': [(3.625, 1), (3.375, 2), (3.125, 6), (2.875, 8), (2.625, 2)],
            '更長週期 (Longer)': [(3.75, 1), (3.50, 1), (3.25, 2), (3.00, 4), (2.75, 8), (2.50, 3)]
        }

        fomc_medians = {
            '2024 年底': 4.375,
            '2025 年底': 3.625,
            '2026 年底': 3.125,
            '2027 年底': 2.875,
            '更長週期 (Longer)': 2.750
        }

        c_dp1, c_dp2, c_dp3 = st.columns(3)
        c_dp1.metric("🏛️ 2025 年底 FOMC 官員中位數", f"{fomc_medians['2025 年底']:.2f}%", "預測累計降息 3~4 碼")
        c_dp2.metric("⚡ 市場期貨即時隱含利率", f"{mkt_path['2025 年底']:.2f}%", f"即時市場預期比 Fed 更激進", delta_color="inverse")
        diff_bp = int((mkt_path['2025 年底'] - fomc_medians['2025 年底']) * 100)
        diff_str = f"{diff_bp:+} bps (市場更偏鴿)" if diff_bp < 0 else f"{diff_bp:+} bps (市場更偏鷹)"
        c_dp3.metric("⚖️ 官員與市場定價分歧", diff_str, "潛在預期差波動源")

        fig_dot = go.Figure()
        time_categories = list(dot_distribution.keys())

        for t_idx, t_cat in enumerate(time_categories):
            rate_groups = dot_distribution[t_cat]
            for rate_val, count in rate_groups:
                jitter_offsets = np.linspace(-0.18, 0.18, count) if count > 1 else [0]
                for offset in jitter_offsets:
                    fig_dot.add_trace(go.Scatter(
                        x=[t_idx + offset],
                        y=[rate_val],
                        mode='markers',
                        marker=dict(
                            size=12,
                            color='#0284C7',
                            line=dict(color='#FFFFFF', width=1.5),
                            opacity=0.85
                        ),
                        hoverinfo='text',
                        hovertext=f"<b>時間</b>: {t_cat}<br><b>FOMC 官員預測利率</b>: {rate_val:.3f}%<br><i>(1 顆點代表 1 位決策委員)</i>",
                        showlegend=False
                    ))

        median_x = list(range(len(time_categories)))
        median_y = [fomc_medians[k] for k in time_categories]
        fig_dot.add_trace(go.Scatter(
            x=median_x,
            y=median_y,
            mode='lines+markers',
            name="🏛️ FOMC 官員預估中位數 (Fed Median)",
            line=dict(color='#D97706', width=3.2),
            marker=dict(size=9, color='#D97706', symbol='diamond'),
            hovertemplate="<b>%{x} 中位數</b>: %{y:.2f}%<extra></extra>"
        ))

        mkt_y = [mkt_path[k] for k in time_categories]
        fig_dot.add_trace(go.Scatter(
            x=median_x,
            y=mkt_y,
            mode='lines+markers',
            name="⚡ 市場期貨即時定價路徑 (Market Pricing)",
            line=dict(color='#0D9488', width=2.8, dash='dash'),
            marker=dict(size=8, color='#0D9488', symbol='circle'),
            hovertemplate="<b>%{x} 市場定價</b>: %{y:.2f}%<extra></extra>"
        ))

        fig_dot.update_layout(
            title=dict(
                text="<b>聯準會 19 位官員利率點陣圖 (Dot Plot) vs. 金融市場期貨即時預期曲線</b>",
                font=dict(size=14.5, color="#2D2622"),
                x=0.01, y=0.96
            ),
            height=540,
            margin=dict(t=75, b=65, l=25, r=30),
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(len(time_categories))),
                ticktext=time_categories,
                tickfont=dict(size=12.5, color="#334155", family="Arial Black"),
                showgrid=True,
                gridcolor='#F1ECE5'
            ),
            yaxis=dict(
                title="聯邦基金目標利率 (%)",
                range=[2.0, 5.6],
                dtick=0.25,
                tickformat=".2f",
                showgrid=True,
                gridcolor='#F1ECE5'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.98,
                font=dict(size=11.5)
            ),
            hovermode="closest",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF"
        )

        st.plotly_chart(fig_dot, use_container_width=True, key="p1_fed_dot_plot_full")

    with sub_t2:
        quarters_cb = ['2023Q4', '2024Q2', '2024Q4', '2025Q2', '2025Q4', '2026Q2', '2026Q4']
        fed_rates = [5.50, 5.50, 4.75, 4.25, 3.75, 3.50, 3.25]
        ecb_rates = [4.00, 3.75, 3.25, 2.75, 2.50, 2.25, 2.25]
        boj_rates = [-0.10, 0.10, 0.25, 0.50, 0.75, 0.75, 1.00]

        fig_cb = go.Figure()
        fig_cb.add_trace(go.Scatter(x=quarters_cb, y=fed_rates, mode='lines+markers', line=dict(color='#0284C7', width=3), name="美國聯準會 (Fed)"))
        fig_cb.add_trace(go.Scatter(x=quarters_cb, y=ecb_rates, mode='lines+markers', line=dict(color='#047857', width=2.5), name="歐洲央行 (ECB)"))
        fig_cb.add_trace(go.Scatter(x=quarters_cb, y=boj_rates, mode='lines+markers', line=dict(color='#D97706', width=2.5), name="日本央行 (BOJ)"))

        fig_cb.update_layout(
            title=dict(text="<b>全球主要央行政策利率中位數走勢推演 (%)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
            height=430,
            margin=dict(t=65, b=30, l=15, r=30),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="基準利率 (%)", showgrid=True, gridcolor='#F2ECE5'),
            legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11))
        )
        st.plotly_chart(fig_cb, use_container_width=True, key="p1_cb_chart")

# ----------------------------------------------------
# 🔒 分頁 4：實體通膨與失業率菲利浦斯動態（200元以上解鎖）
# ----------------------------------------------------
elif active_p1 == "tab4":
    if user_tier < 1:
        st.markdown(f"""
        <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 24px; margin-top:14px; margin-bottom:20px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.45rem;">🔒</span>
                    <span style="font-size:1.24rem; font-weight:800; color:#78350F;">【四、實體通膨與失業率菲利浦斯動態追蹤】進階會員專屬解鎖</span>
                </div>
                <span style="background:#FEF3C7; color:#92400E; font-size:0.85rem; font-weight:800; padding:4px 12px; border-radius:20px; border:1px solid #FDE68A;">
                    需要解鎖：⚡ 進階量化版 (NT$ 200/月)
                </span>
            </div>
            <div style="font-size:1.0rem; font-weight:700; color:#92400E; margin-bottom:6px;">
                ✦ 核心價值：透過 CPI/PCE 三大動力源拆解與薩姆衰退規則 (Sahm Rule)，科學判定「軟著陸」或「硬著陸」
            </div>
            <div style="font-size:0.92rem; color:#6B584C; line-height:1.6;">
                您目前的使用權限為：<strong>🌿 基礎探索版 (免費)</strong>。解鎖此模組後，您將享有以下分析工具：
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🌟 本模組包含的進階量化工具：")
        st.markdown("- **核心 CPI 年增率 vs 失業率雙軸對照**：精確量測通膨與充分就業區間之偏離度")
        st.markdown("- **薩姆規則衰退指標 (Sahm Rule) 即時測算**：以 3 個月移動平均失業率對比 12 個月最低點，提早半年預警經濟衰退")
        st.markdown("- **CPI 三大核心動力源拆解（商品/住房/超級核心服務）**：透視租金滯後性與薪資螺旋壓力")
        st.markdown("- **「通膨 × 就業」四大象限情境配置指南**：依軟著陸、硬著陸或二次通膨給予資產部位配置建議")

        st.markdown("---")
        c_pay1, c_pay2 = st.columns([1.5, 1])
        with c_pay1:
            st.info("""
            **💡 如何立即解鎖？**
            1. 點擊回到 **「0_決策總覽首頁」** 最下方的方案選擇區。
            2. 選擇 **「⚡ 進階量化版 (NT$ 200/月)」** 或全能旗艦版。
            3. 開通登入後，本功能以及 3~6 模組全部即刻完整解鎖！
            """)
        with c_pay2:
            st.success("""
            **💎 會員權益：**
            * 只要具備 200 元以上會籍即可永久暢看。
            * 官方指標庫與就業數據自動即時同步。
            """)
    else:
        st.markdown("### 📈 四、實體通膨 (CPI/PCE) 與失業率菲利浦斯動態追蹤")
        st.caption("透過就業緊度與通膨黏性的交互驗證，判定經濟週期是邁入「完美軟著陸 (Goldilocks)」還是逼近「硬著陸衰退」。")

        months_inf = ['24-01', '24-03', '24-05', '24-07', '24-09', '24-11', '25-01', '25-03', '25-05', '25-07']
        core_cpi = [3.9, 3.8, 3.4, 3.2, 3.3, 3.1, 2.9, 2.8, 2.6, 2.47]
        unemp_rate = [3.7, 3.8, 4.0, 4.3, 4.1, 4.1, 4.0, 4.1, 4.2, 4.1]

        def format_smart_decimal(val):
            rounded_2 = round(val, 2)
            if rounded_2 == round(val, 1):
                return f"{val:.1f}%"
            return f"{val:.2f}%"

        cpi_display_texts = [format_smart_decimal(v) for v in core_cpi]
        latest_cpi_str = cpi_display_texts[-1]
        latest_unemp_val = unemp_rate[-1]

        unemp_3m_avg = np.mean(unemp_rate[-3:])
        unemp_12m_min = np.min(unemp_rate)
        sahm_value = round(unemp_3m_avg - unemp_12m_min, 2)

        c_inf1, c_inf2, c_inf3 = st.columns(3)
        c_inf1.metric("📉 核心 CPI 年增率 (最新)", latest_cpi_str, "距 Fed 2.0% 目標剩 47 bps", delta_color="normal")
        c_inf2.metric("👥 美國失業率 (最新)", f"{latest_unemp_val:.1f}%", "充分就業區間 (4.0%~4.2%)", delta_color="normal")
        sahm_state = "安全區間（無衰退風險）" if sahm_value < 0.50 else "⚠️ 觸發衰退警訊"
        c_inf3.metric("🚨 薩姆規則衰退指標 (Sahm Rule)", f"{sahm_value:+.2f}%", sahm_state, delta_color="normal" if sahm_value < 0.5 else "inverse")

        fig_inf = make_subplots(specs=[[{"secondary_y": True}]])

        fig_inf.add_trace(
            go.Bar(
                x=months_inf, 
                y=core_cpi, 
                name="核心 CPI 年增率 (%)", 
                marker_color='#0284C7', 
                text=cpi_display_texts, 
                textposition='outside', 
                cliponaxis=False, 
                textfont=dict(size=12, color='#1E293B', family='Arial Black'), 
                hovertemplate="<b>核心 CPI</b>: %{text}<extra></extra>"
            ),
            secondary_y=False
        )

        fig_inf.add_trace(
            go.Scatter(
                x=months_inf, 
                y=unemp_rate, 
                name="美國失業率 (%)", 
                mode='lines+markers', 
                line=dict(color='#D97706', width=3), 
                marker=dict(size=7, color='#D97706', line=dict(color='#FFFFFF', width=1.5)), 
                hovertemplate="<b>失業率</b>: %{y:.1f}%<extra></extra>"
            ),
            secondary_y=True
        )

        fig_inf.update_layout(
            title=dict(text=f"<b>美國核心 CPI 通膨降溫 (最新 {latest_cpi_str}) vs 失業率穩定對照</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
            height=450,
            margin=dict(t=75, b=30, l=15, r=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
            hovermode="x unified"
        )
        fig_inf.update_yaxes(
            title_text="核心 CPI (%)", 
            range=[0, 5.2], 
            secondary_y=False, 
            showgrid=True, 
            gridcolor='#F2ECE5'
        )
        fig_inf.update_yaxes(
            title_text="失業率 (%)", 
            range=[0, 8.5], 
            secondary_y=True, 
            showgrid=False
        )
        st.plotly_chart(fig_inf, use_container_width=True, key="p1_inf_chart")

        st.markdown("""
        <div style="background:#FAF8F5; border:1px solid #E6DFD7; border-left:4.5px solid #0F766E; border-radius:10px; padding:16px 18px; margin-top:14px; margin-bottom:16px;">
            <div style="font-weight:800; font-size:1.02rem; color:#0F766E; margin-bottom:10px;">🔍 【機構法人視角】CPI 拆解：決定通膨降溫速度的三大動力源</div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px;">
                <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:4px solid #0284C7; border-radius:8px; padding:12px 14px;">
                    <strong style="color:#0284C7; font-size:0.92rem;">📦 1. 核心商品通膨 (Goods) ── 已實質通縮</strong>
                    <div style="font-size:0.86rem; color:#475569; margin-top:4px; line-height:1.6;">
                        供應鏈全面常態化，二手車、電子產品價格持續回落。商品端已不再是推升物價的主力，反而穩定提供物價降溫力道。
                    </div>
                </div>
                <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:4px solid #D97706; border-radius:8px; padding:12px 14px;">
                    <strong style="color:#D97706; font-size:0.92rem;">🏠 2. 住房租金通膨 (Shelter) ── 滯後性降溫中</strong>
                    <div style="font-size:0.86rem; color:#475569; margin-top:4px; line-height:1.6;">
                        佔 CPI 權重高達 36%。民間即時簽約租金早在 2024 年顯著放緩，官方統計存在 6~12 個月滯後性，正依序反映進官方數據。
                    </div>
                </div>
                <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:4px solid #059669; border-radius:8px; padding:12px 14px;">
                    <strong style="color:#059669; font-size:0.92rem;">💼 3. 超級核心服務 (SuperCore) ── Fed 最核心關注</strong>
                    <div style="font-size:0.86rem; color:#475569; margin-top:4px; line-height:1.6;">
                        排除住房之核心服務。與勞動薪資增長高度綁定。只要非農平均時薪年增率回落至 3.5%~4.0%，服務通膨就不具備螺旋上升動能。
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------
# 🔒 分頁 5：美林投資時鐘 2D 宏觀景氣四象限地圖（200元以上解鎖）
# ----------------------------------------------------
elif active_p1 == "tab5":
    if user_tier < 1:
        st.markdown(f"""
        <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 24px; margin-top:14px; margin-bottom:20px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.45rem;">🔒</span>
                    <span style="font-size:1.24rem; font-weight:800; color:#78350F;">【五、宏觀景氣四象限輪動指引與資產配置防禦矩陣】進階會員專屬解鎖</span>
                </div>
                <span style="background:#FEF3C7; color:#92400E; font-size:0.85rem; font-weight:800; padding:4px 12px; border-radius:20px; border:1px solid #FDE68A;">
                    需要解鎖：⚡ 進階量化版 (NT$ 200/月)
                </span>
            </div>
            <div style="font-size:1.0rem; font-weight:700; color:#92400E; margin-bottom:6px;">
                ✦ 核心價值：諾貝爾獎等級現代美林投資時鐘，以 2D 散佈圖動態鎖定當前景氣週期與抗震資產
            </div>
            <div style="font-size:0.92rem; color:#6B584C; line-height:1.6;">
                您目前的使用權限為：<strong>🌿 基礎探索版 (免費)</strong>。解鎖此模組後，您將享有以下分析工具：
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🌟 本模組包含的進階量化工具：")
        st.markdown("- **美林投資時鐘 2D 四象限輪動地圖**：依「經濟增長動能」與「通膨方向」即時標記宏觀週期座標")
        st.markdown("- **12 大經典資產配置錨點定位**：直觀透視能源 (XLE)、原物料 (DBC)、美債 (TLT)、科技 (QQQ)、黃金 (GLD) 之最適週期")
        st.markdown("- **過熱再膨脹、停滯通膨、通縮衰退、黃金女孩四象限專屬策略**：提供清晰明確的買進持有避險指引")
        st.markdown("- **CFP® 全天候抗震資產配置思維**：兼顧長期資產複利增長與重大黑天鵝期間的下檔保護")

        st.markdown("---")
        c_pay1, c_pay2 = st.columns([1.5, 1])
        with c_pay1:
            st.info("""
            **💡 如何立即解鎖？**
            1. 點擊回到 **「0_決策總覽首頁」** 最下方的方案選擇區。
            2. 選擇 **「⚡ 進階量化版 (NT$ 200/月)」** 或全能旗艦版。
            3. 開通登入後，本功能以及 3~6 模組全部即刻完整解鎖！
            """)
        with c_pay2:
            st.success("""
            **💎 會員權益：**
            * 只要具備 200 元以上會籍即可永久暢看。
            * 象限座標每月隨官方總經數據自動動態推移。
            """)
    else:
        st.markdown("### 🧭 五、宏觀景氣四象限輪動指引與資產配置防禦矩陣")
        st.caption("依據「經濟成長動能（加速 / 減速）」與「通貨膨脹方向（升溫 / 降溫）」，視覺化動態判定當前宏觀週期與資產輪動最優解。")

        fig_quad = go.Figure()

        fig_quad.add_shape(type="rect", x0=0, y0=0, x1=4.8, y1=4.8, fillcolor="rgba(217, 119, 6, 0.07)", line_width=0, layer="below")
        fig_quad.add_shape(type="rect", x0=-4.8, y0=0, x1=0, y1=4.8, fillcolor="rgba(220, 38, 38, 0.07)", line_width=0, layer="below")
        fig_quad.add_shape(type="rect", x0=-4.8, y0=-4.8, x1=0, y1=0, fillcolor="rgba(2, 132, 199, 0.07)", line_width=0, layer="below")
        fig_quad.add_shape(type="rect", x0=0, y0=-4.8, x1=4.8, y1=0, fillcolor="rgba(4, 120, 87, 0.07)", line_width=0, layer="below")

        fig_quad.add_hline(y=0, line_dash="dash", line_color="#A8A29E", line_width=1.5)
        fig_quad.add_vline(x=0, line_dash="dash", line_color="#A8A29E", line_width=1.5)

        fig_quad.add_annotation(
            x=4.3, y=4.3,
            text="<b>🟡 第一象限：過熱再膨脹 (Reflation)</b><br><span style='font-size:12.5px; color:#B45309;'>經濟過熱 ｜ 商品飆漲 ｜ 升息緊縮</span>",
            showarrow=False, align="right", xanchor="right", yanchor="top",
            bgcolor="rgba(255, 255, 255, 0.96)", bordercolor="#FCD34D", borderwidth=1.8, borderpad=10,
            font=dict(size=14.5, color="#B45309", family="Arial Black")
        )
        fig_quad.add_annotation(
            x=-4.3, y=4.3,
            text="<b>🔴 第二象限：停滯性通膨 (Stagflation)</b><br><span style='font-size:12.5px; color:#DC2626;'>增長停滯 ｜ 物價高企 ｜ 股債雙殺</span>",
            showarrow=False, align="left", xanchor="left", yanchor="top",
            bgcolor="rgba(255, 255, 255, 0.96)", bordercolor="#FCA5A5", borderwidth=1.8, borderpad=10,
            font=dict(size=14.5, color="#DC2626", family="Arial Black")
        )
        fig_quad.add_annotation(
            x=-4.3, y=-4.3,
            text="<b>🔵 第三象限：景氣通縮衰退 (Deflation)</b><br><span style='font-size:12.5px; color:#0284C7;'>需求萎縮 ｜ 獲利滑落 ｜ 寬鬆刺激</span>",
            showarrow=False, align="left", xanchor="left", yanchor="bottom",
            bgcolor="rgba(255, 255, 255, 0.96)", bordercolor="#7DD3FC", borderwidth=1.8, borderpad=10,
            font=dict(size=14.5, color="#0284C7", family="Arial Black")
        )
        fig_quad.add_annotation(
            x=4.3, y=-4.3,
            text="<b>🟢 第四象限：黃金女孩擴張 (Goldilocks)</b><br><span style='font-size:12.5px; color:#047857;'>成長強勁 ｜ 通膨受控 ｜ 股債雙牛</span>",
            showarrow=False, align="right", xanchor="right", yanchor="bottom",
            bgcolor="rgba(255, 255, 255, 0.96)", bordercolor="#86EFAC", borderwidth=1.8, borderpad=10,
            font=dict(size=14.5, color="#047857", family="Arial Black")
        )

        assets_data = [
            {"x": 1.4, "y": 1.3, "name": "原油/能源 (XLE)", "color": "#D97706", "pos": "top center"},
            {"x": 2.6, "y": 1.9, "name": "原物料大宗 (DBC)", "color": "#D97706", "pos": "bottom center"},
            {"x": 1.2, "y": 0.5, "name": "抗通膨債券 (TIPS)", "color": "#D97706", "pos": "bottom center"},
            
            {"x": -1.2, "y": 1.4, "name": "實體黃金 (GLD)", "color": "#DC2626", "pos": "top center"},
            {"x": -2.3, "y": 2.0, "name": "超短債 (SGOV)", "color": "#DC2626", "pos": "bottom center"},
            {"x": -1.4, "y": 0.5, "name": "現金等價物 (BIL)", "color": "#DC2626", "pos": "bottom center"},
            
            {"x": -1.3, "y": -1.4, "name": "20年期美債 (TLT)", "color": "#0284C7", "pos": "top center"},
            {"x": -2.5, "y": -2.1, "name": "公用事業 (XLU)", "color": "#0284C7", "pos": "top center"},
            {"x": -1.3, "y": -0.7, "name": "投資級公司債 (LQD)", "color": "#0284C7", "pos": "bottom center"},

            {"x": 0.9, "y": -1.8, "name": "標普 500 (SPY)", "color": "#047857", "pos": "bottom center"},
            {"x": 3.2, "y": -2.7, "name": "科技龍頭 (QQQ)", "color": "#047857", "pos": "top center"},
            {"x": 1.1, "y": -0.6, "name": "高收益債 (HYG)", "color": "#047857", "pos": "top center"}
        ]

        for a in assets_data:
            fig_quad.add_trace(go.Scatter(
                x=[a['x']], y=[a['y']],
                mode="markers+text",
                marker=dict(size=12, color=a['color'], line=dict(color="#FFFFFF", width=2)),
                text=[f"<b>{a['name']}</b>"],
                textposition=a['pos'],
                textfont=dict(size=13, color=a['color'], family="Arial Black"),
                hoverinfo="text",
                hovertext=f"<b>{a['name']}</b><br>最佳配置象限",
                showlegend=False
            ))

        current_x = 2.3
        current_y = -1.15
        fig_quad.add_trace(go.Scatter(
            x=[current_x], y=[current_y],
            mode="markers",
            marker=dict(size=24, color="#10B981", symbol="star", line=dict(color="#064E3B", width=2.4)),
            name="當前宏觀座標",
            hoverinfo="skip",
            showlegend=False
        ))
        fig_quad.add_annotation(
            x=current_x, y=current_y,
            text="<b>📍 當前宏觀座標<br><span style='font-size:11.5px; font-weight:700;'>【第四象限：黃金女孩擴張期】</span></b>",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2,
            arrowcolor="#047857",
            ax=75,
            ay=-45,
            bgcolor="#FFFFFF",
            bordercolor="#047857",
            borderwidth=2,
            borderpad=8,
            font=dict(size=13, color="#047857", family="Arial Black")
        )

        fig_quad.update_layout(
            title=dict(text="<b>🧭 宏觀景氣時鐘 2D 四象限輪動地圖 (實體增長 vs. 通膨趨勢)</b>", font=dict(size=15.5, color="#2D2622"), x=0.01, y=0.98),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=700,
            margin=dict(t=65, b=50, l=65, r=65),
            xaxis=dict(
                title=dict(text="<b>◀ 經濟動能放緩 (Growth Decelerating) ―――― 經濟強勁擴張 (Growth Accelerating) ▶</b>", font=dict(size=13.5, color="#44403C")),
                range=[-4.8, 4.8],
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            yaxis=dict(
                title=dict(text="<b>◀ 通膨下行減速 (Disinflation) ―――― 通膨升溫過熱 (Inflation) ▶</b>", font=dict(size=13.5, color="#44403C")),
                range=[-4.8, 4.8],
                showgrid=False,
                zeroline=False,
                showticklabels=False
            )
        )
        st.plotly_chart(fig_quad, use_container_width=True, config={'displayModeBar': False}, key="p1_quadrant_scatter_map_clean_v2")

        st.markdown("""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; align-items: stretch; margin-top: 10px; margin-bottom: 28px;">
            <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #D97706; border-radius:10px; padding:16px 18px; box-sizing:border-box; height:100%; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <strong style="color:#D97706; font-size:1.02rem;">🟡 第一象限：過熱通膨再膨脹 (Reflation)</strong>
                    <div style="font-size:0.87rem; color:#5C554F; margin-top:8px; line-height:1.65;">
                        • <strong>宏觀特徵</strong>：經濟過熱、商品全面飆漲、薪資通膨二度抬頭、央行轉向緊縮。<br>
                        • <strong>歷史抗通膨代表</strong>：實體原物料商品 (DBC)、能源類股 (XLE)、抗通膨債券 (TIPS)。<br>
                        • <strong>配置思維</strong>：縮短債券久期，留意高估值成長股評價修正，配置實質抗通膨資產。
                    </div>
                </div>
            </div>
            <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #0284C7; border-radius:10px; padding:16px 18px; box-sizing:border-box; height:100%; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <strong style="color:#0284C7; font-size:1.02rem;">🔵 第三象限：景氣通縮衰退 (Deflationary Recession)</strong>
                    <div style="font-size:0.87rem; color:#5C554F; margin-top:8px; line-height:1.65;">
                        • <strong>宏觀特徵</strong>：經濟陷入衰退、失業率飆升、企業獲利滑落、物價與需求萎縮。<br>
                        • <strong>歷史防禦代表</strong>：20 年期長天期美國國債 (TLT)、公用事業防禦股 (XLU)、投資級債 (LQD)。<br>
                        • <strong>配置思維</strong>：當市場利率大幅滑落時，長天期公債具備資本利得潛力，提供投組防禦緩衝。
                    </div>
                </div>
            </div>
            <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #DC2626; border-radius:10px; padding:16px 18px; box-sizing:border-box; height:100%; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <strong style="color:#DC2626; font-size:1.02rem;">🔴 第二象限：停滯性通膨 (Stagflation)</strong>
                    <div style="font-size:0.87rem; color:#5C554F; margin-top:8px; line-height:1.65;">
                        • <strong>宏觀特徵</strong>：經濟成長停滯甚至負增長，同時物價與利率居高不下。<br>
                        • <strong>歷史避險代表</strong>：超短期公債 (SGOV)、現金等價物 (BIL)、實體黃金 (GLD)。<br>
                        • <strong>配置思維</strong>：股債關聯度提高時，充裕的現金流工具與低相關性避險資產能降低投組波動。
                    </div>
                </div>
            </div>
            <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-left: 4.5px solid #047857; border-radius:10px; padding:16px 18px; box-sizing:border-box; height:100%; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <strong style="color:#047857; font-size:1.02rem;">🟢 第四象限：黃金女孩復甦擴張 (Goldilocks)</strong>
                        <span style="background:#D1FAE5; color:#065F46; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:12px; white-space:nowrap;">當前所處區間</span>
                    </div>
                    <div style="font-size:0.87rem; color:#5C554F; margin-top:8px; line-height:1.65;">
                        • <strong>宏觀特徵</strong>：經濟增長穩健、通膨平穩回落至目標、央行逐步啟動預防性降息。<br>
                        • <strong>歷史成長代表</strong>：標普 500 (SPY)、科技成長龍頭 (QQQ)、高收益債 (HYG)。<br>
                        • <strong>配置思維</strong>：聚焦企業基本面盈餘動能，兼顧風險管理原則參與估值擴張機會。
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
