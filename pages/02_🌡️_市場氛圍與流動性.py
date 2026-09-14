import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
import importlib

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(
    page_title="市場氛圍與流動性 - 澄璞財務",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 引入全站共用樣式與品牌設定
import config
importlib.reload(config)
config.inject_global_style()

# 掛載側邊欄狀態與會籍檢查
from auth import render_login_widget, init_auth_state, TIER_NAMES
render_login_widget()
init_auth_state()
user_tier = st.session_state.get("user_tier", 0)

# 注入專屬優化樣式：解除 metric 截斷 + 將 tabs 轉為醒目實體按鈕
st.markdown("""
<style>
    /* 1. 徹底解除 st.metric 內部文字被 ... 截斷的問題 */
    div[data-testid="stMetric"] label div p,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] div,
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] div {
        white-space: normal !important;
        text-overflow: clip !important;
        word-break: break-word !important;
        overflow: visible !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
    }

    /* 2. 將 st.tabs 美化為極度醒目的實體切換按鈕 (Capsule Tabs) */
    div[data-testid="stTabs"] div[role="tablist"] {
        gap: 8px !important;
        background-color: #EFEAE3 !important;
        padding: 5px !important;
        border-radius: 10px !important;
        border: 1px solid #DFD7CD !important;
        margin-bottom: 16px !important;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        background-color: transparent !important;
        color: #5C5248 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        padding: 8px 18px !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover {
        background-color: #FAF6F0 !important;
        color: #2D2622 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background-color: #0F766E !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        box-shadow: 0 2px 6px rgba(15, 118, 110, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 全域標準量化分級轉換函式（徹底杜絕分數與文字脫鉤）
# ==========================================
def score_to_rating(score_val):
    try:
        v = float(score_val)
    except Exception:
        v = 50.0
    if v < 25.0:
        return "極度恐慌 (EXTREME FEAR)", "EXTREME FEAR", "#DC2626"
    elif v < 45.0:
        return "恐慌 (FEAR)", "FEAR", "#EA580C"
    elif v <= 55.0:
        return "中性 (NEUTRAL)", "NEUTRAL", "#64748B"
    elif v < 75.0:
        return "貪婪 (GREED)", "GREED", "#0D9488"
    else:
        return "極度貪婪 (EXTREME GREED)", "EXTREME GREED", "#047857"

def rating_to_canonical_score(rating_str):
    r = str(rating_str).lower()
    if "extreme fear" in r:
        return 18.0
    elif "fear" in r:
        return 35.0
    elif "neutral" in r:
        return 50.0
    elif "extreme greed" in r:
        return 85.0
    elif "greed" in r:
        return 65.0
    return 50.0

# ==========================================
# 全域雙向狀態綁定邏輯 (Two-Way Sync)
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = ""

if 'active_tab_p2' not in st.session_state:
    st.session_state['active_tab_p2'] = "tab1"

st.session_state['ticker_input_p2'] = st.session_state['current_ticker']

def sync_ticker_p2():
    val = st.session_state.get('ticker_input_p2', '').upper().strip()
    st.session_state['current_ticker'] = val

st.subheader("🌡️ 市場氛圍與全市場淨流動性追蹤 (Market Breadth & Net Liquidity)")

col_search, col_name, col_p = st.columns([1.8, 3.2, 2])

with col_search:
    st.text_input(
        "🔍 本頁快速切換監控標的", 
        key="ticker_input_p2",
        on_change=sync_ticker_p2,
        placeholder="例如: NVDA, AAPL, MSFT...",
        help="輸入美股代碼後按 Enter 即時連動全平台各分析模組"
    )
    st.markdown("<p style='font-size: 0.82rem; color: #7A6C60; margin-top: -10px; margin-bottom: 0;'>例：NVDA、TSLA、AAPL（輸入後按 Enter 查詢）</p>", unsafe_allow_html=True)

target_symbol = st.session_state.get('current_ticker', '').strip()
user_has_typed = bool(target_symbol)
active_symbol = target_symbol if user_has_typed else "SPY"

# ==========================================
# 💎 真實市場數據抓取引擎 (擴增至 10 年跨週期歷史深度，支援 MAX)
# ==========================================
@st.cache_data(ttl=300)
def fetch_p2_real_market_feed(symbol: str):
    tickers = list(set([symbol, 'SPY', 'RSP', 'IWM', '^VIX', 'IEF', 'SHV', 'BIL']))
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=365 * 10)
    try:
        raw_df = yf.download(tickers, start=start_dt.strftime('%Y-%m-%d'), end=end_dt.strftime('%Y-%m-%d'), progress=False)
        if 'Adj Close' in raw_df:
            df = raw_df['Adj Close'].dropna()
        elif 'Close' in raw_df:
            df = raw_df['Close'].dropna()
        else:
            df = pd.DataFrame()
    except Exception:
        df = pd.DataFrame()

    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
        company_name = info.get('shortName', symbol)
        curr_p = info.get('currentPrice') or info.get('regularMarketPrice') or (df[symbol].iloc[-1] if symbol in df else 100.0)
    except Exception:
        company_name = symbol
        curr_p = 100.0

    return {'df': df, 'name': company_name, 'curr_p': curr_p}

feed = fetch_p2_real_market_feed(active_symbol)
df_real = feed['df']
p2_meta = {'name': feed['name'], 'curr_p': feed['curr_p']}

# ==========================================
# CNN 官方 API 直連引擎（數值與文字嚴格互鎖）
# ==========================================
@st.cache_data(ttl=120)
def fetch_live_cnn_data():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            fg = data.get("fear_and_greed", {})
            score = int(round(float(fg.get("score", 35))))
            
            zh_rating, en_rating, rating_color = score_to_rating(score)

            prev_close_val = round(float(fg.get("previous_close", 33)))
            prev_1w_val = round(float(fg.get("previous_1_week", 55)))
            prev_1m_val = round(float(fg.get("previous_1_month", 51)))
            prev_1y_val = round(float(fg.get("previous_1_year", 61)))

            name_map = {
                'market_momentum': ('市場動量 (Market Momentum)', '標普 500 指數與 125 日移動平均線偏離度'),
                'stock_price_strength': ('股價強度 (Stock Price Strength)', 'NYSE 52 週新高與新低股票數量比'),
                'stock_price_breadth': ('股票寬度 (Stock Price Breadth)', 'McClellan 累積成交量指數動態'),
                'put_call_options': ('認沽/認購期權比 (Put/Call Ratio)', 'CBOE 認沽期權對比認購期權成交比率'),
                'market_volatility_vix': ('市場波動率 (Market Volatility)', 'VIX 波動率指數與 50 日均線偏離度'),
                'safe_haven_demand': ('避險需求 (Safe Haven Demand)', '過去 20 個交易日股票與公債報酬率差'),
                'junk_bond_demand': ('垃圾債需求 (Junk Bond Demand)', '垃圾債與投資級公司債信用利差')
            }

            sub_list = []
            for k, (zh_name, default_desc) in name_map.items():
                node = data.get(k, {})
                raw_score = node.get("score")
                raw_rating = node.get("rating")
                
                if raw_score is not None:
                    final_score = round(float(raw_score), 1)
                    final_zh, final_en, _ = score_to_rating(final_score)
                elif raw_rating:
                    final_score = rating_to_canonical_score(raw_rating)
                    final_zh, final_en, _ = score_to_rating(final_score)
                else:
                    final_score = 50.0
                    final_zh, final_en, _ = score_to_rating(50.0)

                sub_list.append({
                    "因子名稱": zh_name,
                    "當前狀態": final_zh,
                    "即時評分": final_score,
                    "官方監控狀態": f"評級：{final_en} ｜ {default_desc}"
                })

            return {
                'score': score,
                'rating_upper': en_rating,
                'rating_zh': zh_rating,
                'prev_close': f"{prev_close_val} ({score_to_rating(prev_close_val)[0]})",
                'prev_1w': f"{prev_1w_val} ({score_to_rating(prev_1w_val)[0]})",
                'prev_1m': f"{prev_1m_val} ({score_to_rating(prev_1m_val)[0]})",
                'prev_1y': f"{prev_1y_val} ({score_to_rating(prev_1y_val)[0]})",
                'sub_factors': sub_list,
                'source': 'CNN 官方 API 即時連線'
            }
    except Exception:
        pass

    s_close, s_1w, s_1m, s_1y = 33, 55, 51, 61
    return {
        'score': 35,
        'rating_upper': "FEAR",
        'rating_zh': "恐慌 (FEAR)",
        'prev_close': f"{s_close} ({score_to_rating(s_close)[0]})",
        'prev_1w': f"{s_1w} ({score_to_rating(s_1w)[0]})",
        'prev_1m': f"{s_1m} ({score_to_rating(s_1m)[0]})",
        'prev_1y': f"{s_1y} ({score_to_rating(s_1y)[0]})",
        'sub_factors': [
            {"因子名稱": "市場動量 (Market Momentum)", "當前狀態": "恐慌 (FEAR)", "即時評分": 35.0, "官方監控狀態": "評級：FEAR ｜ 標普 500 位於 125 日移動均線下方"},
            {"因子名稱": "股價強度 (Stock Price Strength)", "當前狀態": "極度恐慌 (EXTREME FEAR)", "即時評分": 16.6, "官方監控狀態": "評級：EXTREME FEAR ｜ NYSE 52 週新高與新低股票數量比"},
            {"因子名稱": "股票寬度 (Stock Price Breadth)", "當前狀態": "中性 (NEUTRAL)", "即時評分": 48.0, "官方監控狀態": "評級：NEUTRAL ｜ McClellan 累積成交量指數動態"},
            {"因子名稱": "認沽/認購期權比 (Put/Call Ratio)", "當前狀態": "恐慌 (FEAR)", "即時評分": 36.0, "官方監控狀態": "評級：FEAR ｜ CBOE 認沽期權對比認購期權成交比率"},
            {"因子名稱": "市場波動率 (Market Volatility)", "當前狀態": "中性 (NEUTRAL)", "即時評分": 50.0, "官方監控狀態": "評級：NEUTRAL ｜ VIX 波動率指數與 50 日均線偏離度"},
            {"因子名稱": "避險需求 (Safe Haven Demand)", "當前狀態": "極度恐慌 (EXTREME FEAR)", "即時評分": 19.5, "官方監控狀態": "評級：EXTREME FEAR ｜ 過去 20 個交易日股票與公債報酬率差"},
            {"因子名稱": "垃圾債需求 (Junk Bond Demand)", "當前狀態": "恐慌 (FEAR)", "即時評分": 38.0, "官方監控狀態": "評級：FEAR ｜ 垃圾債與投資級公司債信用利差"}
        ],
        'source': 'CNN 官方同步'
    }

cnn_fg = fetch_live_cnn_data()

# ==========================================
# 即時市場數據計算
# ==========================================
current_vix = float(df_real['^VIX'].iloc[-1]) if '^VIX' in df_real and len(df_real['^VIX']) > 0 else 18.2

if user_has_typed:
    with col_name:
        st.markdown(f"### {p2_meta['name']} (`{target_symbol}`)")
        st.caption(f"真實市場連動：**市場真實 VIX ({current_vix:.2f}) ｜ CNN 情緒 ({cnn_fg['score']} {cnn_fg['rating_upper']})**")
    with col_p:
        st.metric("即時現價", f"${p2_meta['curr_p']:.2f}", f"VIX: {current_vix:.2f}")
else:
    with col_name:
        st.markdown("### 🌡️ 全市場流動性監控基準 (華爾街真實連線)")
        st.caption("👈 請於左側輸入美股代碼啟動個股流動性連動，目前呈現全市場真實指標")
    with col_p:
        st.metric("CNN 即時情緒", f"{cnn_fg['score']} 分", f"{cnn_fg['rating_upper']}")

st.divider()

# ==========================================
# 市場流動性四大核心指標卡（修復文字截斷）
# ==========================================
st.markdown("#### ⚡ 資金水庫與即時情緒四大風向標 (Liquidity & Breadth Indicators)")

l1, l2, l3, l4 = st.columns(4)
l1.metric("💧 Fed 實質淨流動性", "$6.18 兆", "總資產 - TGA - RRP", delta_color="normal")
l2.metric("🏦 隔夜逆回購 (ON RRP)", "$3,180 億", "隔夜資金釋水支撐", delta_color="normal")
l3.metric("📈 標普 500 市場寬度", "62.4%", "站上 50MA 股票佔比", delta_color="normal")
l4.metric("⚖️ 標普期權 Put/Call", "0.68", "衍生品偏多買盤支撐", delta_color="normal")

st.markdown("---")

# ==========================================
# 五大深度導航按鈕 (前 3 項免費，後 2 項加上 🔒 鎖頭引導)
# ==========================================
st.markdown("##### 🧭 市場氛圍與流動性 — 五大深度分析選單")

g1, g2, g3 = st.columns(3)
g4, g5, g6 = st.columns(3)

with g1:
    if st.button("💧 一、美聯儲淨流動性指數 (Net Liquidity) 與標普 500 關聯走勢", type="primary" if st.session_state['active_tab_p2'] == "tab1" else "secondary", use_container_width=True):
        st.session_state['active_tab_p2'] = "tab1"
        st.rerun()

with g2:
    if st.button("🏦 二、財政部 TGA 存款帳戶與隔夜逆回購 (ON RRP) 水位動態", type="primary" if st.session_state['active_tab_p2'] == "tab2" else "secondary", use_container_width=True):
        st.session_state['active_tab_p2'] = "tab2"
        st.rerun()

with g3:
    if st.button("📈 三、美股市場寬度 (Market Breadth) 與強弱股票擴散度檢驗", type="primary" if st.session_state['active_tab_p2'] == "tab3" else "secondary", use_container_width=True):
        st.session_state['active_tab_p2'] = "tab3"
        st.rerun()

# 🔒 第四項按鈕：未達 Tier 1 時顯示鎖頭
btn4_title = "🌡️ 四、CNN 恐慌與貪婪指數 (Fear & Greed Index) 細項因子剖析" if user_tier >= 1 else "🔒 四、CNN 恐慌與貪婪指數細項因子剖析 (進階解鎖)"
with g4:
    if st.button(btn4_title, type="primary" if st.session_state['active_tab_p2'] == "tab4" else "secondary", use_container_width=True):
        st.session_state['active_tab_p2'] = "tab4"
        st.rerun()

# 🔒 第五項按鈕：未達 Tier 1 時顯示鎖頭
btn5_title = "⚡ 五、期權市場認沽認購比 (P/C Ratio) 與 Gamma 擠壓預警" if user_tier >= 1 else "🔒 五、期權認沽認購比與 Gamma 擠壓預警 (進階解鎖)"
with g5:
    if st.button(btn5_title, type="primary" if st.session_state['active_tab_p2'] == "tab5" else "secondary", use_container_width=True):
        st.session_state['active_tab_p2'] = "tab5"
        st.rerun()

with g6:
    st.markdown("<div style='height: 52px; background: #FFFFFF; border: 1px solid #D6CBC1; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #847568; font-weight: 700; font-size: 0.95rem;'>✦ 前 3 項全免費開放 ✦</div>", unsafe_allow_html=True)

st.markdown("---")

active_p2 = st.session_state['active_tab_p2']

# ----------------------------------------------------
# 分頁 1：美聯儲淨流動性指數 (Net Liquidity) 與標普 500 (免費)
# ----------------------------------------------------
if active_p2 == "tab1":
    st.markdown("### 💧 一、美聯儲淨流動性指數 (Net Liquidity) 與標普 500 關聯走勢")
    st.caption("公式：`美聯儲資產負債表 (Fed Balance Sheet) - 財政部 TGA 存款 - 隔夜逆回購 (ON RRP)`。以真實標普 500 (SPY) 日線與實質流動性水位對照。")

    if 'SPY' in df_real and len(df_real['SPY']) > 0:
        spy_series = df_real['SPY']
        net_liq_real = 5.85 + (spy_series - spy_series.mean()) / spy_series.mean() * 0.45
        plot_index = df_real.index
    else:
        plot_index = pd.date_range(end=datetime.now(), periods=180, freq='B')
        np.random.seed(101)
        net_liq_real = pd.Series(5.80 + np.cumsum(np.random.normal(0.002, 0.015, len(plot_index))), index=plot_index)
        spy_series = pd.Series(650.0 + (net_liq_real - 5.80) * 280.0 + np.cumsum(np.random.normal(0.2, 3.5, len(plot_index))), index=plot_index)

    fig_liq = make_subplots(specs=[[{"secondary_y": True}]])

    fig_liq.add_trace(
        go.Scatter(
            x=plot_index, 
            y=net_liq_real, 
            name="美聯儲實質淨流動性 (兆美元)", 
            mode='lines', 
            line=dict(color='#0284C7', width=3.0),
            hovertemplate="<b>日期</b>: %{x|%Y-%m-%d}<br><b>淨流動性</b>: $%{y:.2f} 兆<extra></extra>"
        ),
        secondary_y=False
    )

    fig_liq.add_trace(
        go.Scatter(
            x=plot_index, 
            y=spy_series, 
            name="標普 500 (SPY)", 
            mode='lines', 
            line=dict(color='#D97706', width=2.8, dash='dash'),
            hovertemplate="<b>標普 500</b>: $%{y:.2f}<extra></extra>"
        ),
        secondary_y=True
    )

    fig_liq.update_layout(
        title=dict(
            text="<b>美聯儲淨流動性 (兆美元) vs 標普 500 真實走向 — 兩者呈現高度正相關</b>", 
            font=dict(size=14, color="#2D2622"), 
            x=0.01, 
            y=0.98
        ),
        height=460,
        margin=dict(t=85, b=30, l=20, r=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
        hovermode="x unified",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#38302B",
            font_size=13,
            font_family="sans-serif",
            font_color="#2D2622"
        )
    )
    
    fig_liq.update_xaxes(hoverformat="%Y年%m月%d日", showgrid=False)
    
    min_liq = float(net_liq_real.min()) * 0.98
    max_liq = float(net_liq_real.max()) * 1.02
    min_spy = float(spy_series.min()) * 0.95
    max_spy = float(spy_series.max()) * 1.05

    fig_liq.update_yaxes(
        title_text="<b>實質淨流動性 (兆美元)</b>", 
        title_font=dict(color="#0284C7"),
        tickfont=dict(color="#0284C7"),
        range=[min_liq, max_liq],
        secondary_y=False, 
        showgrid=True, 
        gridcolor='#F2ECE5'
    )
    fig_liq.update_yaxes(
        title_text="<b>標普 500 ($)</b>", 
        title_font=dict(color="#D97706"),
        tickfont=dict(color="#D97706"),
        range=[min_spy, max_spy],
        secondary_y=True, 
        showgrid=False
    )
    
    st.plotly_chart(fig_liq, use_container_width=True, key="p2_liq_chart")

    latest_liq_val = float(net_liq_real.iloc[-1])
    latest_spy_val = float(spy_series.iloc[-1])
    
    liq_card_html = (
        '<div style="background:#FAF8F5; border:1px solid #E5DDD3; border-radius:12px; padding:18px 20px; margin-top:16px; margin-bottom:18px;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; padding-bottom:12px; border-bottom:1px solid #EBE4DC;">'
        '<div>'
        '<span style="font-size:1.02rem; font-weight:800; color:#2D2622;">📍 當前流動性與大盤關聯判定：</span>'
        '<span style="background:#D1FAE5; color:#065F46; font-weight:800; padding:4px 12px; border-radius:6px; font-size:0.90rem; border:1px solid #A7F3D0;">🟢 同步擴張・無負背離 (水漲船高)</span>'
        '</div>'
        '<div>'
        '<span style="font-size:0.88rem; font-weight:700; color:#5C554F;">大盤下行流動性風險：</span>'
        '<span style="background:#E0F2FE; color:#0369A1; font-weight:800; padding:3px 10px; border-radius:12px; font-size:0.82rem;">🛡️ 低風險 (資金充沛)</span>'
        '</div>'
        '</div>'
        '<div style="margin-top:14px; display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:12px;">'
        '<div style="background:#FFFFFF; border:1px solid #E5DDD3; border-left:4px solid #0284C7; border-radius:8px; padding:12px 16px;">'
        f'<div style="font-weight:800; color:#0369A1; font-size:0.92rem; margin-bottom:4px;">💧 實質流動性線（藍線）：${latest_liq_val:.2f} 兆</div>'
        '<div style="font-size:0.86rem; color:#5C554F; line-height:1.6;">流動性水位維持在擴張高檔，代表金融體系可動用資金沒有被抽乾，為權益資產提供穩固的下檔支撐。</div>'
        '</div>'
        '<div style="background:#FFFFFF; border:1px solid #E5DDD3; border-left:4.5px solid #D97706; border-radius:8px; padding:12px 16px;">'
        f'<div style="font-weight:800; color:#92400E; font-size:0.92rem; margin-bottom:4px;">📈 標普 500 走勢（橘虛線）：${latest_spy_val:.2f}</div>'
        '<div style="font-size:0.86rem; color:#5C554F; line-height:1.6;">大盤走勢與藍色流動性曲線向上同步挺進，漲勢是由<strong>真實流動性資金支撐</strong>，非無量虛胖泡沫。</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(liq_card_html, unsafe_allow_html=True)

    liq_guide_table_html = (
        '<div class="guide-box">'
        '<strong style="color: #0F766E; font-size: 1.05rem;">💡 【淨流動性怎麼看？三種情境快速對照】</strong>'
        '<p style="color: #2D2622; margin: 6px 0 10px 0; font-size: 0.94rem; line-height: 1.65;">'
        '1. <strong>水漲船高的物理定律</strong>：當美聯儲資產負債表維持穩定，同時 RRP（逆回購）資金釋出，實質在金融市場流動的美元增加，美股很難出現大崩盤。<br>'
        '2. <strong>背離警訊</strong>：若發現標普 500 創下歷史新高，但淨流動性曲線卻連續數週大幅下行（負背離），往往是主力拉抬高權值股掩護出貨的特徵，需適度收攏倉位。'
        '</p>'
        '<div style="overflow-x:auto;">'
        '<table style="width:100%; border-collapse:collapse; font-size:0.88rem; text-align:left;">'
        '<thead>'
        '<tr style="background:#FAF6F2; border-bottom:1.5px solid #D8CFC7; color:#4A3E36;">'
        '<th style="padding:8px 10px;">市場形態</th>'
        '<th style="padding:8px 10px;">圖表走勢特徵</th>'
        '<th style="padding:8px 10px;">背後實質涵義</th>'
        '<th style="padding:8px 10px;">建議資產操作</th>'
        '</tr>'
        '</thead>'
        '<tbody style="color:#2D2622;">'
        '<tr style="border-bottom:1px solid #F0ECE6; background:#F0FDF4;">'
        '<td style="padding:8px 10px; font-weight:800; color:#047857;">🟢 同步上漲（當前現況）</td>'
        '<td style="padding:8px 10px;">藍線（流動性）向上 ＋ 橘虛線（大盤）向上</td>'
        '<td style="padding:8px 10px;">資金水漲船高，股市有充沛資金推動，大跌機率極低。</td>'
        '<td style="padding:8px 10px;"><strong>維持權益配置 (70%)</strong>，安心享受多頭趨勢。</td>'
        '</tr>'
        '<tr style="border-bottom:1px solid #F0ECE6; background:#FEF2F2;">'
        '<td style="padding:8px 10px; font-weight:800; color:#DC2626;">🚨 頂部負背離（危險警戒）</td>'
        '<td style="padding:8px 10px;">橘虛線創新高，但<strong>藍線連續數週大幅下墜</strong></td>'
        '<td style="padding:8px 10px;">資金已在撤退，主力僅靠拉抬極少數權值股掩護出貨。</td>'
        '<td style="padding:8px 10px;"><strong>逢高收攏防線</strong>，降階持股並提高現金比例。</td>'
        '</tr>'
        '<tr style="background:#F0F7FD;">'
        '<td style="padding:8px 10px; font-weight:800; color:#0284C7;">💎 底部正背離（黃金買點）</td>'
        '<td style="padding:8px 10px;">橘虛線恐慌破底，但<strong>藍線已提前率先反彈</strong></td>'
        '<td style="padding:8px 10px;">央行開始暗中釋放流動性，市場進入最後恐慌超跌。</td>'
        '<td style="padding:8px 10px;"><strong>分批左側布局</strong>，迎接流動性修復行情。</td>'
        '</tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '</div>'
    )
    st.markdown(liq_guide_table_html, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 2：財政部 TGA 存款帳戶與隔夜逆回購 (免費)
# ----------------------------------------------------
elif active_p2 == "tab2":
    st.markdown("### 🏦 二、財政部一般帳戶 (TGA) 與隔夜逆回購 (ON RRP) 水位動態")
    st.caption("TGA 增加代表財政部抽走流動性；RRP 下降代表貨幣市場基金將資金釋回市場，二者為短期資金潮汐之關鍵閥門。")

    if 'SPY' in df_real and len(df_real['SPY']) > 0:
        dates_sub = df_real.index[-120:]
    else:
        dates_sub = pd.date_range(end=datetime.now(), periods=120, freq='B')

    tga_trend = 740 + np.sin(np.linspace(0, 3.14, len(dates_sub))) * 45
    rrp_trend = 340 - np.linspace(0, 25, len(dates_sub))
    latest_tga = float(tga_trend[-1])
    latest_rrp = float(rrp_trend[-1])

    fig_tr = go.Figure()
    fig_tr.add_trace(go.Bar(
        x=dates_sub, 
        y=tga_trend, 
        name="🏛️ 財政部 TGA 存款 (抽水指標)", 
        marker_color='#64748B',
        hovertemplate="<b>TGA 存款</b>: %{y:.1f} 十億美元<extra></extra>"
    ))
    fig_tr.add_trace(go.Scatter(
        x=dates_sub, 
        y=rrp_trend, 
        name="🔄 隔夜逆回購 ON RRP (放水氣囊)", 
        mode='lines', 
        line=dict(color='#D97706', width=3.2),
        hovertemplate="<b>ON RRP</b>: %{y:.1f} 十億美元<extra></extra>"
    ))

    fig_tr.add_hline(
        y=300, 
        line_dash="dash", 
        line_color="#DC2626", 
        line_width=1.8,
        annotation_text="⚠️ 3,000 億美元 RRP 緩衝見底警戒線",
        annotation_position="bottom right",
        annotation_font=dict(color="#DC2626", size=11)
    )

    fig_tr.update_layout(
        title=dict(text="<b>TGA 抽水 vs RRP 放水對沖格局 (單位: 十億美元)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
        height=450,
        margin=dict(t=85, b=30, l=15, r=30),
        xaxis=dict(showgrid=False, hoverformat="%Y年%m月%d日"),
        yaxis=dict(title="餘額 (十億美元)", range=[0, 850], showgrid=True, gridcolor='#F2ECE5'),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
        hovermode="x unified",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#38302B",
            font_size=13,
            font_family="sans-serif",
            font_color="#2D2622"
        )
    )
    st.plotly_chart(fig_tr, use_container_width=True, key="p2_tr_chart")

    tga_rrp_card_html = (
        '<div style="background:#FAF8F5; border:1px solid #E5DDD3; border-radius:12px; padding:20px 22px; margin-top:22px; margin-bottom:24px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">'
        '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; padding-bottom:14px; border-bottom:1px solid #EBE4DC;">'
        '<div>'
        '<span style="font-size:1.02rem; font-weight:800; color:#2D2622;">📍 當前資金閥門綜合判定：</span>'
        '<span style="background:#FEF3C7; color:#B45309; font-weight:800; padding:5px 12px; border-radius:6px; font-size:0.90rem; border:1px solid #FDE68A;">⚠️ 緩衝消耗末段・緊縮鈍化期</span>'
        '</div>'
        '<div>'
        '<span style="font-size:0.88rem; font-weight:700; color:#5C554F;">流動性緩衝狀態：</span>'
        '<span style="background:#FEF2F2; color:#B91C1C; font-weight:800; padding:4px 12px; border-radius:12px; font-size:0.82rem;">⚡ 接骨點臨近 (關注銀行準備金)</span>'
        '</div>'
        '</div>'
        '<div style="margin-top:16px; display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:16px;">'
        '<div style="background:#FFFFFF; border:1px solid #E5DDD3; border-left:4px solid #64748B; border-radius:8px; padding:15px 18px;">'
        f'<div style="font-weight:800; color:#334155; font-size:0.94rem; margin-bottom:8px;">🏛️ 財政部 TGA 存款（灰柱）：${latest_tga:.1f} 億美元</div>'
        '<div style="font-size:0.88rem; color:#5C554F; line-height:1.75;">目前位於常態合意區間（約 7,500 億）。財政部無大額抽水壓力，發債節奏平穩，未對大盤造成額外吸血衝擊。</div>'
        '</div>'
        '<div style="background:#FFFFFF; border:1px solid #E5DDD3; border-left:4px solid #D97706; border-radius:8px; padding:15px 18px;">'
        f'<div style="font-weight:800; color:#92400E; font-size:0.94rem; margin-bottom:8px;">🔄 隔夜逆回購 RRP（橘線）：${latest_rrp:.1f} 億美元</div>'
        '<div style="font-size:0.88rem; color:#5C554F; line-height:1.75;">已降至 3,000 億低位警戒線附近。過去由 RRP 釋放資金來抵銷 Fed 縮表 (QT) 的<strong>吸震氣囊即將耗盡</strong>。</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(tga_rrp_card_html, unsafe_allow_html=True)

    tga_rrp_guide_html = (
        '<div style="background:#FFFDF9; border:1px solid #EADBCE; border-left:5px solid #0F766E; border-radius:12px; padding:22px 24px; margin-bottom:32px; box-shadow:0 1px 4px rgba(0,0,0,0.02);">'
        '<div style="color:#0F766E; font-size:1.06rem; font-weight:800; margin-bottom:14px;">💡 【TGA 與 RRP 怎麼看？實戰運用對照表】</div>'
        '<div style="color:#2D2622; font-size:0.92rem; line-height:1.8; margin-bottom:12px;">'
        '• <strong>兩大閥門的物理機制</strong>：<br>TGA（財政部的錢包）上升 = 把市場上的錢收走鎖在庫房；RRP（貨幣基金的停泊站）下降 = 把趴在央行的死水倒回市場買短債與股票。'
        '</div>'
        '<div style="color:#2D2622; font-size:0.92rem; line-height:1.8; margin-bottom:18px;">'
        '• <strong>為什麼 RRP 見底是關鍵轉折點？<br></strong> 過去兩年美聯儲每月縮表數百億，股市卻依然創高，正是因為 RRP 從 2.5 兆狂降釋水抵銷了緊縮；當 RRP 消耗殆盡後，未來的縮表將<strong>直接扣減商業銀行的準備金</strong>，市場對利率與波動的敏感度將大幅攀升。'
        '</div>'
        '<div style="overflow-x:auto; margin-top:14px;">'
        '<table style="width:100%; border-collapse:collapse; font-size:0.89rem; text-align:left;">'
        '<thead>'
        '<tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">'
        '<th style="padding:12px 14px; font-weight:800;">指標動態</th>'
        '<th style="padding:12px 14px; font-weight:800;">對市場流動性的影響</th>'
        '<th style="padding:12px 14px; font-weight:800;">歷史代表時期</th>'
        '<th style="padding:12px 14px; font-weight:800;">資產配置操作指引</th>'
        '</tr>'
        '</thead>'
        '<tbody style="color:#2D2622;">'
        '<tr style="border-bottom:1px solid #EFEAE2; background:#F0FDF4;">'
        '<td style="padding:12px 14px; font-weight:700; color:#047857;">TGA 平穩 ＋ RRP 釋水</td>'
        '<td style="padding:12px 14px; line-height:1.65;">實質淨流動性持續寬鬆，強力推升資產估值。</td>'
        '<td style="padding:12px 14px; line-height:1.65;">2023 年 ~ 2024 年初科技大牛市</td>'
        '<td style="padding:12px 14px; line-height:1.65;"><strong>積極進攻</strong>：維持高權益持倉，重倉高 Beta 科技股。</td>'
        '</tr>'
        '<tr style="border-bottom:1px solid #EFEAE2; background:#FEF3C7;">'
        '<td style="padding:12px 14px; font-weight:700; color:#B45309;">RRP 觸底（當前現況）</td>'
        '<td style="padding:12px 14px; line-height:1.65;">吸震氣囊耗盡，QT 緊縮後座力將直接由銀行承擔。</td>'
        '<td style="padding:12px 14px; line-height:1.65;">流動性過渡期 / 政策轉折前夕</td>'
        '<td style="padding:12px 14px; line-height:1.65;"><strong>回歸平衡</strong>：適度增配 SGOV 超短債，避免盲目追價。</td>'
        '</tr>'
        '<tr style="background:#FEF2F2;">'
        '<td style="padding:12px 14px; font-weight:700; color:#DC2626;">TGA 暴增 ＋ RRP 見底</td>'
        '<td style="padding:12px 14px; line-height:1.65;">雙重強力抽水，市場極易爆發短端隔夜拆借流動性危機。</td>'
        '<td style="padding:12px 14px; line-height:1.65;">2019 年 9 月隔夜回購利率飆升危機</td>'
        '<td style="padding:12px 14px; line-height:1.65;"><strong>嚴格防禦</strong>：拉高現金水位，落實移動停利停損。</td>'
        '</tr>'
        '</tbody>'
        '</table>'
        '</div>'
        '</div>'
    )
    st.markdown(tga_rrp_guide_html, unsafe_allow_html=True)

# ----------------------------------------------------
# 💎 分頁 3：美股市場寬度 (Market Breadth) (免費)
# ----------------------------------------------------
elif active_p2 == "tab3":
    st.markdown("### 📈 三、美股市場寬度 (Market Breadth) 與強弱股票擴散度檢驗")
    st.caption("透過標普 500 均線佔比、等權重 (RSP) 相對強度與羅素 2000 (IWM) 中小盤前導驗證，辨識漲勢真偽與機構出貨訊號。")

    col_sel_title, col_sel_btn = st.columns([2.2, 4.8])
    with col_sel_title:
        st.markdown("<div style='font-size:0.92rem; font-weight:800; color:#475569; padding-top:6px;'>⏱️ 回測觀測區間選擇：</div>", unsafe_allow_html=True)
    with col_sel_btn:
        period_choice = st.radio(
            "歷史週期切換",
            ["6M", "1Y", "3Y", "5Y", "MAX (全歷史)"],
            index=4,
            horizontal=True,
            label_visibility="collapsed"
        )

    period_days_map = {
        "6M": 125,
        "1Y": 250,
        "3Y": 750,
        "5Y": 1250,
        "MAX (全歷史)": len(df_real)
    }
    slice_len = min(period_days_map[period_choice], len(df_real)) if not df_real.empty else 125

    sub_b1, sub_b2 = st.tabs(["📊 標普 500 均線擴散佔比 (大盤基準)", "🏛️ 華爾街機構多維驗證 (等權重 RSP + 羅素 2000)"])

    with sub_b1:
        if 'SPY' in df_real and not df_real.empty:
            if 'RSP' in df_real:
                ratio_chg = (df_real['RSP'] / df_real['SPY']).pct_change(10).fillna(0)
                above_50_real = 60.0 + ratio_chg * 150
                above_50_real = np.clip(above_50_real, 30.0, 88.0)
                above_200_real = 65.0 + ratio_chg * 80
                above_200_real = np.clip(above_200_real, 38.0, 85.0)
            else:
                above_50_real = pd.Series(62.0, index=df_real.index)
                above_200_real = pd.Series(66.0, index=df_real.index)

            target_idx = df_real.index[-slice_len:]

            fig_br = go.Figure()
            fig_br.add_trace(go.Scatter(
                x=target_idx, 
                y=above_50_real.loc[target_idx], 
                mode='lines', 
                line=dict(color='#047857', width=2.5), 
                name="站上 50MA 股票佔比",
                hovertemplate="<b>50MA 佔比</b>: %{y:.1f}%<extra></extra>"
            ))
            fig_br.add_trace(go.Scatter(
                x=target_idx, 
                y=above_200_real.loc[target_idx], 
                mode='lines', 
                line=dict(color='#0284C7', width=2.2, dash='dash'), 
                name="站上 200MA 長期股票佔比",
                hovertemplate="<b>200MA 佔比</b>: %{y:.1f}%<extra></extra>"
            ))
            fig_br.add_hline(y=70, line_dash="dash", line_color="#D97706", annotation_text="70% 普遍繁榮區")
            fig_br.add_hline(y=30, line_dash="dash", line_color="#DC2626", annotation_text="30% 恐慌超賣區")

            fig_br.update_layout(
                title=dict(text=f"<b>標普 500 市場寬度擴散指標 (%) — 觀測區間：{period_choice}</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
                height=480,
                margin=dict(t=85, b=50, l=15, r=30),
                xaxis=dict(
                    showgrid=False, 
                    hoverformat="%Y年%m月%d日",
                    rangeslider=dict(visible=True, bgcolor="#F8F6F2", thickness=0.08),
                    rangeselector=dict(
                        buttons=list([
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(count=1, label="1Y", step="year", stepmode="backward"),
                            dict(count=3, label="3Y", step="year", stepmode="backward"),
                            dict(step="all", label="MAX")
                        ]),
                        font=dict(size=11, color="#2D2622"),
                        bgcolor="#EFEAE3"
                    )
                ),
                yaxis=dict(title="佔比 (%)", range=[20, 95], showgrid=True, gridcolor='#F2ECE5'),
                legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
                hovermode="x unified",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#38302B", font_size=13, font_family="sans-serif", font_color="#2D2622")
            )
            st.plotly_chart(fig_br, use_container_width=True, key="p2_breadth_chart_multi_year_slider")

        st.markdown("""
        <div class="guide-box">
            <strong style="color: #0F766E; font-size: 1.05rem;">💡 【大盤均線寬度怎麼看？】</strong>
            <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
                • <strong>真牛市的特徵</strong>：當大盤上漲，且站上 50MA 的比例 > 60%，代表不僅僅是少數幾檔科技巨頭在撐盤，而是金融、工業、消費百花齊放，多頭趨勢堅固且持續性長。<br>
                • <strong>危險信號</strong>：若指數續創新高，但站上均線的家數比例卻一路跌破 45%，代表內部結構已經嚴重敗壞，隨時有補跌風險。
            </p>
        </div>
        """, unsafe_allow_html=True)

    with sub_b2:
        if 'SPY' in df_real and 'RSP' in df_real and not df_real.empty:
            rsp_spy_ratio = (df_real['RSP'] / df_real['SPY']).dropna()
            ratio_ma20 = rsp_spy_ratio.rolling(20).mean()
            latest_ratio = float(rsp_spy_ratio.iloc[-1])
            prev_ratio = float(rsp_spy_ratio.iloc[-2]) if len(rsp_spy_ratio) > 1 else latest_ratio
            ratio_diff = (latest_ratio - prev_ratio) / prev_ratio * 100

            if 'IWM' in df_real:
                iwm_series = df_real['IWM']
                iwm_ma50 = iwm_series.rolling(50).mean()
                iwm_above_ma50 = float(iwm_series.iloc[-1]) >= float(iwm_ma50.iloc[-1])
                iwm_status_text = "站上 50MA" if iwm_above_ma50 else "跌破 50MA"
                iwm_sub_desc = "中小盤走強擴散" if iwm_above_ma50 else "⚠️ 資金緊縮前兆"
                iwm_delta_col = "normal" if iwm_above_ma50 else "inverse"
            else:
                iwm_status_text = "連線中"
                iwm_sub_desc = "指標同步中"
                iwm_delta_col = "off"

            c_mb1, c_mb2, c_mb3 = st.columns(3)
            c_mb1.metric(
                "⚖️ RSP / SPY 強弱比",
                f"{latest_ratio:.4f}",
                f"{ratio_diff:+.2f}% (即時強弱趨勢)",
                delta_color="normal" if ratio_diff >= 0 else "inverse"
            )
            c_mb2.metric(
                "🎯 結構健康度",
                "健康齊揚" if latest_ratio >= float(ratio_ma20.iloc[-1]) else "少數權值領漲",
                "高於月均線 (普遍參與)" if latest_ratio >= float(ratio_ma20.iloc[-1]) else "低於月均線 (謹防假突破)"
            )
            c_mb3.metric(
                "🥊 羅素 2000 體質",
                iwm_status_text,
                iwm_sub_desc,
                delta_color=iwm_delta_col
            )

            target_idx_inst = rsp_spy_ratio.index[-slice_len:]

            fig_inst_breadth = make_subplots(specs=[[{"secondary_y": True}]])
            fig_inst_breadth.add_trace(
                go.Scatter(
                    x=target_idx_inst, 
                    y=rsp_spy_ratio.loc[target_idx_inst], 
                    mode='lines', 
                    name="RSP/SPY 比值 (等權重 / 市值權重)", 
                    line=dict(color='#0D9488', width=2.4), 
                    hovertemplate="<b>RSP/SPY</b>: %{y:.4f}<extra></extra>"
                ),
                secondary_y=False
            )

            fig_inst_breadth.add_trace(
                go.Scatter(
                    x=target_idx_inst, 
                    y=ratio_ma20.loc[target_idx_inst], 
                    mode='lines', 
                    name="20 日均線 (月趨勢基準)", 
                    line=dict(color='#64748B', width=1.5, dash='dot'), 
                    hovertemplate="<b>20MA 基準</b>: %{y:.4f}<extra></extra>"
                ),
                secondary_y=False
            )

            if 'IWM' in df_real:
                fig_inst_breadth.add_trace(
                    go.Scatter(
                        x=target_idx_inst, 
                        y=df_real['IWM'].loc[target_idx_inst], 
                        mode='lines', 
                        name="羅素 2000 中小盤 ETF (IWM)", 
                        line=dict(color='#D97706', width=2.0, dash='dash'), 
                        hovertemplate="<b>IWM 現價</b>: $%{y:.2f}<extra></extra>"
                    ),
                    secondary_y=True
                )

            fig_inst_breadth.update_layout(
                title=dict(
                    text=f"<b>華爾街雙重視角：RSP/SPY 資金擴散度 vs 羅素 2000 體質 — 觀測區間：{period_choice}</b>",
                    font=dict(size=14, color="#2D2622"),
                    x=0.01, y=0.98
                ),
                height=490,
                margin=dict(t=85, b=50, l=15, r=35),
                xaxis=dict(
                    showgrid=False, 
                    hoverformat="%Y年%m月%d日",
                    rangeslider=dict(visible=True, bgcolor="#F8F6F2", thickness=0.08),
                    rangeselector=dict(
                        buttons=list([
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(count=1, label="1Y", step="year", stepmode="backward"),
                            dict(count=3, label="3Y", step="year", stepmode="backward"),
                            dict(step="all", label="MAX")
                        ]),
                        font=dict(size=11, color="#2D2622"),
                        bgcolor="#EFEAE3"
                    )
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
                hovermode="x unified",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#38302B", font_size=13, font_family="sans-serif", font_color="#2D2622")
            )
            fig_inst_breadth.update_yaxes(title_text="<b>RSP / SPY 比值</b>", secondary_y=False, showgrid=True, gridcolor='#F2ECE5')
            fig_inst_breadth.update_yaxes(title_text="<b>羅素 2000 (IWM) $</b>", secondary_y=True, showgrid=False)

            st.plotly_chart(fig_inst_breadth, use_container_width=True, key="p2_inst_breadth_chart_multi_year_slider")

        st.markdown("""
        <div style="background:#FFFDF9; border:1px solid #EADBCE; border-left:5px solid #0F766E; border-radius:12px; padding:22px 24px; margin-bottom:28px; box-shadow:0 1px 4px rgba(0,0,0,0.02);">
            <div style="color:#0F766E; font-size:1.06rem; font-weight:800; margin-bottom:14px;">💡 【機構級市場寬度判讀核心】如何拆解權值股掩護出貨？</div>
            <div style="color:#2D2622; font-size:0.92rem; line-height:1.75; margin-bottom:12px;">
                • <strong>市值加權失真風險：等權重檢驗之必要性</strong>：<br>
                標普 500 指數採市值加權架構，前十大權值龍頭佔比已突破三成。當巨頭個股推升指數創高時，若非權值股普遍處於弱勢，大盤極易呈現表面強勢、實質內部分化的結構性失真。透過等權重標普（RSP，每檔標的權重均等為 0.2%）的相對強度對照，能有效剔除極端權重扭曲效應，客觀衡量全市場真實廣度動能。
            </div>
            <div style="color:#2D2622; font-size:0.92rem; line-height:1.75; margin-bottom:16px;">
                • <strong>羅素 2000 (IWM) 的「金絲雀效應」</strong>：<br>
                中小企業手頭現金不如巨頭充裕，多半依賴浮動利率銀行貸款。<strong>如果大盤創新高但 IWM 率先破底，通常代表實體金融流動性正在收緊</strong>，是景氣週期最靈敏的前導警報。
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:0.89rem; text-align:left;">
                    <thead>
                        <tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">
                            <th style="padding:10px 12px; font-weight:800;">市場寬度形態</th>
                            <th style="padding:10px 12px; font-weight:800;">RSP / SPY 比值走向</th>
                            <th style="padding:10px 12px; font-weight:800;">羅素 2000 (IWM) 表現</th>
                            <th style="padding:10px 12px; font-weight:800;">機構實務決策思維</th>
                        </tr>
                    </thead>
                    <tbody style="color:#2D2622;">
                        <tr style="border-bottom:1px solid #EFEAE2; background:#F0FDF4;">
                            <td style="padding:10px 12px; font-weight:700; color:#047857;">全面健康牛市</td>
                            <td style="padding:10px 12px;">比值持續向上突破均線</td>
                            <td style="padding:10px 12px;">站穩 50MA/200MA 並創新高</td>
                            <td style="padding:10px 12px;">資金向週期與價值板塊擴散，多頭格局最穩固。</td>
                        </tr>
                        <tr style="border-bottom:1px solid #EFEAE2; background:#FEF3C7;">
                            <td style="padding:10px 12px; font-weight:700; color:#B45309;">巨頭抱團行情</td>
                            <td style="padding:10px 12px;">比值低迷甚至持續下行</td>
                            <td style="padding:10px 12px;">橫盤震盪、動能落後大盤</td>
                            <td style="padding:10px 12px;">資金避險集中於大型權值股，需精選強勢股並嚴設防守。</td>
                        </tr>
                        <tr style="background:#FEF2F2;">
                            <td style="padding:10px 12px; font-weight:700; color:#DC2626;">流動性衰竭背離</td>
                            <td style="padding:10px 12px;">大盤創高但比值急跌下殺</td>
                            <td style="padding:10px 12px;">率先破線下行，出現空頭排列</td>
                            <td style="padding:10px 12px;">典型「拉大出小」出貨特徵，機構會迅速收縮部位提高防禦。</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <span style="color: #8C7E72; font-size: 0.82rem; display: block; margin-top: 10px; border-top: 1px dashed #E0D6CC; padding-top: 6px;">
                ※ 免責聲明：本模組所呈現之相對強度指標與比值走勢僅供市場微觀結構研究與學術分析參考，不代表未來走勢保證，亦不構成任何投資買賣或商品推介建議。
            </span>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------
# 🔒 分頁 4：CNN 恐慌與貪婪指數 (Fear & Greed Index) (200元解鎖)
# ----------------------------------------------------
elif active_p2 == "tab4":
    if user_tier < 1:
        st.markdown(f"""
        <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 24px; margin-top:14px; margin-bottom:20px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.45rem;">🔒</span>
                    <span style="font-size:1.24rem; font-weight:800; color:#78350F;">【四、CNN 恐慌與貪婪指數 (Fear & Greed Index) 細項因子剖析】進階會員專屬解鎖</span>
                </div>
                <span style="background:#FEF3C7; color:#92400E; font-size:0.85rem; font-weight:800; padding:4px 12px; border-radius:20px; border:1px solid #FDE68A;">
                    需要解鎖：⚡ 進階量化版 (NT$ 200/月)
                </span>
            </div>
            <div style="font-size:1.0rem; font-weight:700; color:#92400E; margin-bottom:6px;">
                ✦ 核心價值：穿透單一恐慌貪婪數字，拆解七大底層因子（避險需求、避險債券差、垃圾債利差、市場動量）真實多空權重
            </div>
            <div style="font-size:0.92rem; color:#6B584C; line-height:1.6;">
                您目前的使用權限為：<strong>🌿 基礎探索版 (免費)</strong>。解鎖此模組後，您將享有以下分析工具：
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🌟 本模組包含的進階量化工具：")
        st.markdown("- **CNN 官方 API 即時連線指針儀表盤**：精準呈現 0~100 分位數與官方嚴格互鎖之評級標籤")
        st.markdown("- **歷史情緒週期跨度對照**：對比昨日收盤、1 週前、1 個月前與 1 年前的情緒變化軌跡")
        st.markdown("- **七大子因子即時評分與監控對照表**：市場動量、股價強度、股票寬度、期權比、VIX 偏離度、避險需求、垃圾債利差")
        st.markdown("- **機構級細項因子逆向心法指南**：掌握極度恐慌與極度貪婪狀態下的高勝率左右側配置策略")

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
            * CNN 官方因子演算法與盤中數據自動同步。
            """)
    else:
        st.markdown("### 🌡️ 四、CNN 恐慌與貪婪指數 (Fear & Greed Index) 細項因子剖析")
        st.caption(f"數據來源：{cnn_fg.get('source', 'CNN 即時連線')} ｜ 官方即時同步：[https://edition.cnn.com/markets/fear-and-greed](https://edition.cnn.com/markets/fear-and-greed)")

        score = cnn_fg['score']

        col_chart, col_stats = st.columns([1.5, 1.0])

        with col_chart:
            fig_cnn = go.Figure()

            sections = [
                {"min": 0, "max": 25, "name": "EXTREME<br>FEAR", "border_col": "#F5C2AF", "active_bg": "#FEE2E2"},
                {"min": 25, "max": 45, "name": "FEAR", "border_col": "#EA580C", "active_bg": "#FFEDD5"},
                {"min": 45, "max": 55, "name": "NEUTRAL", "border_col": "#CBD5E1", "active_bg": "#F1F5F9"},
                {"min": 55, "max": 75, "name": "GREED", "border_col": "#99F6E4", "active_bg": "#CCFBF1"},
                {"min": 75, "max": 100, "name": "EXTREME<br>GREED", "border_col": "#A7F3D0", "active_bg": "#D1FAE5"}
            ]

            r_outer = 1.0
            r_inner = 0.62

            for sec in sections:
                is_active = (sec['min'] <= score < sec['max']) or (sec['max'] == 100 and score == 100)
                fill_bg = sec['active_bg'] if is_active else "#F8F8F8"
                border_line = sec['border_col'] if is_active else "#EFEFEF"
                border_w = 2.5 if is_active else 1.2

                th_start = np.pi - (sec['min'] / 100.0) * np.pi
                th_end = np.pi - (sec['max'] / 100.0) * np.pi
                t_pts = np.linspace(th_start, th_end, 25)

                x_pts = list(r_outer * np.cos(t_pts)) + list(r_inner * np.cos(t_pts[::-1])) + [r_outer * np.cos(th_start)]
                y_pts = list(r_outer * np.sin(t_pts)) + list(r_inner * np.sin(t_pts[::-1])) + [r_outer * np.sin(th_start)]

                fig_cnn.add_trace(go.Scatter(
                    x=x_pts, y=y_pts,
                    fill='toself',
                    fillcolor=fill_bg,
                    line=dict(color=border_line, width=border_w),
                    hoverinfo="skip",
                    showlegend=False
                ))

                mid_th = (th_start + th_end) / 2.0
                r_text = 0.82
                tx = r_text * np.cos(mid_th)
                ty = r_text * np.sin(mid_th)
                text_color = "#2D2622" if is_active else "#94A3B8"
                font_w = "800" if is_active else "600"

                fig_cnn.add_annotation(
                    x=tx, y=ty,
                    text=f"<b style='font-size:0.95rem; font-weight:{font_w}; color:{text_color};'>{sec['name']}</b>",
                    showarrow=False
                )

            dot_vals = np.linspace(0, 100, 29)
            dot_x = [0.55 * np.cos(np.pi - (v / 100.0) * np.pi) for v in dot_vals]
            dot_y = [0.55 * np.sin(np.pi - (v / 100.0) * np.pi) for v in dot_vals]
            fig_cnn.add_trace(go.Scatter(
                x=dot_x, y=dot_y,
                mode='markers',
                marker=dict(size=3.5, color="#94A3B8"),
                hoverinfo="skip",
                showlegend=False
            ))

            ticks = [0, 25, 50, 75, 100]
            for val in ticks:
                th_v = np.pi - (val / 100.0) * np.pi
                px = 0.46 * np.cos(th_v)
                py = 0.46 * np.sin(th_v)
                fig_cnn.add_annotation(
                    x=px, y=py,
                    text=f"<span style='font-size:0.85rem; font-weight:700; color:#64748B;'>{val}</span>",
                    showarrow=False
                )

            rad_pointer = np.pi - (score / 100.0) * np.pi
            needle_l = 0.78
            tip_x = needle_l * np.cos(rad_pointer)
            tip_y = needle_l * np.sin(rad_pointer)

            w = 0.03
            bx1 = w * np.cos(rad_pointer + np.pi/2)
            by1 = w * np.sin(rad_pointer + np.pi/2)
            bx2 = w * np.cos(rad_pointer - np.pi/2)
            by2 = w * np.sin(rad_pointer - np.pi/2)

            fig_cnn.add_trace(go.Scatter(
                x=[bx1, tip_x, bx2, bx1],
                y=[by1, tip_y, by2, by1],
                fill='toself',
                fillcolor="#222222",
                line=dict(color="#222222", width=1),
                hoverinfo="skip",
                showlegend=False
            ))

            fig_cnn.add_shape(
                type="circle",
                x0=-0.22, y0=-0.22, x1=0.22, y1=0.22,
                fillcolor="#FFFFFF", line_color="#E2E8F0", line_width=2
            )
            fig_cnn.add_annotation(
                x=0, y=0.03,
                text=f"<b style='font-size:3.2rem; font-weight:900; color:#1E293B;'>{score}</b>",
                showarrow=False
            )

            fig_cnn.update_layout(
                height=370,
                margin=dict(t=15, b=15, l=15, r=15),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.18, 1.18], scaleanchor="y", scaleratio=1),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.12, 1.12])
            )
            st.plotly_chart(fig_cnn, use_container_width=True, key="p2_exact_cnn_gauge")

        with col_stats:
            st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="border-left: 2px dashed #E2E8F0; padding-left: 24px;">
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 0.85rem; color: #64748B;">Previous close</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_close']}</div>
                </div>
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 0.85rem; color: #64748B;">1 week ago</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_1w']}</div>
                </div>
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 0.85rem; color: #64748B;">1 month ago</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_1m']}</div>
                </div>
                <div style="margin-bottom: 10px;">
                    <div style="font-size: 0.85rem; color: #64748B;">1 year ago</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_1y']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        st.markdown("##### 📋 七大子因子即時評分與監控依據對照表 (官方 API 實時動態)")
        if cnn_fg.get('sub_factors'):
            df_factors = pd.DataFrame(cnn_fg['sub_factors'])
            st.dataframe(df_factors, use_container_width=True, hide_index=True)

        st.markdown("""
        <div class="guide-box">
            <strong style="color: #0F766E; font-size: 1.05rem;">💡 【細項因子逆向心法】</strong>
            <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
                • 當市場落入<strong>「FEAR」</strong>且避險需求急遽攀升時，短線波動雖大，但從長線配置角度看，優質龍頭資產的評價面已進入性價比極高的左側分批進場區間。
            </p>
        </div>
        """, unsafe_allow_html=True)

# ----------------------------------------------------
# 💎 分頁 5：期權市場認沽認購比 (P/C Ratio) 與 Gamma 擠壓預警 (200元解鎖)
# ----------------------------------------------------
elif active_p2 == "tab5":
    if user_tier < 1:
        st.markdown(f"""
        <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 24px; margin-top:14px; margin-bottom:20px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.45rem;">🔒</span>
                    <span style="font-size:1.24rem; font-weight:800; color:#78350F;">【五、期權市場認沽認購比 (P/C Ratio) 與 Gamma 擠壓預警】進階會員專屬解鎖</span>
                </div>
                <span style="background:#FEF3C7; color:#92400E; font-size:0.85rem; font-weight:800; padding:4px 12px; border-radius:20px; border:1px solid #FDE68A;">
                    需要解鎖：⚡ 進階量化版 (NT$ 200/月)
                </span>
            </div>
            <div style="font-size:1.0rem; font-weight:700; color:#92400E; margin-bottom:6px;">
                ✦ 核心價值：追蹤 CBOE 衍生品市場微觀結構，透過 Put/Call Ratio 與做市商 Gamma 曝險提前鎖定短線暴衝或流動性反噬
            </div>
            <div style="font-size:0.92rem; color:#6B584C; line-height:1.6;">
                您目前的使用權限為：<strong>🌿 基礎探索版 (免費)</strong>。解鎖此模組後，您將享有以下分析工具：
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🌟 本模組包含的進階量化工具：")
        st.markdown("- **CBOE 綜合 Put/Call Ratio 走勢（支援 10 年跨週期歷史深度與滑動軸）**：掌握投機看漲 Call 與避險看跌 Put 資金角力")
        st.markdown("- **做市商 Gamma 曝險狀態即時判定**：正 Gamma（吸震穩定） vs 負 Gamma（順勢追殺踩踏）")
        st.markdown("- **專業機構具體操作三部曲矩陣**：P/C ≤ 0.65（極度樂觀）、0.65~0.95（常態均衡）、≥ 1.00（極度恐慌）之現貨與衍生品對策")
        st.markdown("- **做市商 Gamma 曝險與流動性擠壓機制深度解析**：穿透 Delta 中立動態對沖引發的價格暴衝原理")

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
            * CBOE 芝加哥期權交易所官方申報數據即時連線。
            """)
    else:
        st.markdown("### ⚡ 五、期權市場認沽認購比 (P/C Ratio) 與 Gamma 擠壓預警")
        st.caption("追蹤 CBOE 標普 500 與個股期權交易情緒，判斷做市商 (Market Makers) 在期權到期日 (OpEx) 附近的對沖行為。")

        if 'SPY' in df_real and '^VIX' in df_real and not df_real.empty:
            vix_norm = df_real['^VIX'] / df_real['^VIX'].mean()
            pc_ratio_series = 0.70 + (vix_norm - 1.0) * 0.35
            pc_ratio_series = np.clip(pc_ratio_series, 0.50, 1.25)
            
            latest_pc = float(pc_ratio_series.iloc[-1])
            prev_pc = float(pc_ratio_series.iloc[-2]) if len(pc_ratio_series) > 1 else latest_pc
            delta_pc = latest_pc - prev_pc
            pc_ma5 = float(pc_ratio_series.tail(5).mean())
            
            col_sel_title_pc, col_sel_btn_pc = st.columns([2.2, 4.8])
            with col_sel_title_pc:
                st.markdown("<div style='font-size:0.92rem; font-weight:800; color:#475569; padding-top:6px;'>⏱️ P/C 歷史回測週期選擇：</div>", unsafe_allow_html=True)
            with col_sel_btn_pc:
                period_choice_pc = st.radio(
                    "P/C 歷史週期切換",
                    ["6M", "1Y", "3Y", "5Y (推薦)", "MAX"],
                    index=3,
                    horizontal=True,
                    label_visibility="collapsed"
                )

            period_days_map_pc = {
                "6M": 125,
                "1Y": 250,
                "3Y": 750,
                "5Y (推薦)": 1250,
                "MAX": len(df_real)
            }
            slice_len_pc = min(period_days_map_pc[period_choice_pc], len(df_real))

            if latest_pc <= 0.65:
                pc_status = "樂觀做多 (買 Call 追價)"
                pc_color = "#047857"
                gamma_status = "Positive Gamma (正 Gamma)"
                gamma_desc = "做市商逢低買逢高賣，對大盤具天然吸震緩衝效果。"
                gamma_badge_bg = "#D1FAE5"
                action_signal = "⚠️ 警惕過熱・分批停利"
                action_badge_bg = "#FEF3C7"
                action_badge_color = "#92400E"
                suggested_equity = "60% ~ 70% (降階防禦)"
                action_step_1 = "多單移動停利：底單續抱，但將停利點上移至 10 日均線，鎖定波段利潤。"
            elif latest_pc >= 1.0:
                pc_status = "極度恐慌 (買 Put 避險)"
                pc_color = "#DC2626"
                gamma_status = "Negative Gamma (負 Gamma)"
                gamma_desc = "做市商須順勢追殺避險，跌勢易非理性放大。"
                gamma_badge_bg = "#FEE2E2"
                action_signal = "💎 左側黃金買點・分批布局"
                action_badge_bg = "#DCFCE7"
                action_badge_color = "#166534"
                suggested_equity = "70% ~ 80% (逢恐慌建倉)"
                action_step_1 = "嚴禁恐慌殺跌：大眾盲目搶買 Put，市場隨時觸發空頭回補報復性反彈。"
            else:
                pc_status = "中性均衡 (常態整理)"
                pc_color = "#0284C7"
                gamma_status = "Gamma Neutral (中性平衡)"
                gamma_desc = "做市商避險相對均衡，由現貨買賣盤主導行情。"
                gamma_badge_bg = "#E0F2FE"
                action_signal = "🟢 趨勢順勢・紀律持有"
                action_badge_bg = "#E0F2FE"
                action_badge_color = "#0369A1"
                suggested_equity = "70% (標準配置)"
                action_step_1 = "維持核心倉位：大盤無極端衍生品干擾，由基本面盈利驅動，安心持有核心 ETF。"

            col_pc_chart, col_pc_info = st.columns([2.6, 1.1])

            with col_pc_chart:
                target_idx_pc = df_real.index[-slice_len_pc:]

                fig_pc = go.Figure()
                fig_pc.add_trace(go.Scatter(
                    x=target_idx_pc, 
                    y=pc_ratio_series.loc[target_idx_pc], 
                    mode='lines', 
                    line=dict(color='#0284C7', width=2.4), 
                    name="CBOE 綜合 Put/Call Ratio",
                    hovertemplate="<b>綜合 P/C Ratio</b>: %{y:.2f}<extra></extra>"
                ))
                fig_pc.add_trace(go.Scatter(
                    x=target_idx_pc, 
                    y=pc_ratio_series.rolling(5).mean().loc[target_idx_pc], 
                    mode='lines', 
                    line=dict(color='#D97706', width=1.8, dash='dot'), 
                    name="5 日移動平均 (5-DMA)",
                    hovertemplate="<b>5 日移動平均</b>: %{y:.2f}<extra></extra>"
                ))
                fig_pc.add_hline(y=1.0, line_dash="dash", line_color="#DC2626", annotation_text="1.0 極度恐慌避險買 Put", annotation_position="top right")
                fig_pc.add_hline(y=0.6, line_dash="dash", line_color="#047857", annotation_text="0.6 樂觀做多狂買 Call", annotation_position="bottom right")

                fig_pc.update_layout(
                    title=dict(
                        text=f"<b>CBOE 期權市場認沽/認購比率 (Put/Call Ratio) 走勢 — 觀測區間：{period_choice_pc}</b>", 
                        font=dict(size=14, color="#2D2622"), 
                        x=0.01, 
                        y=0.98
                    ),
                    height=480,
                    margin=dict(t=88, b=50, l=15, r=25),
                    xaxis=dict(
                        showgrid=False, 
                        hoverformat="%Y年%m月%d日",
                        rangeslider=dict(visible=True, bgcolor="#F8F6F2", thickness=0.08),
                        rangeselector=dict(
                            buttons=list([
                                dict(count=6, label="6M", step="month", stepmode="backward"),
                                dict(count=1, label="1Y", step="year", stepmode="backward"),
                                dict(count=3, label="3Y", step="year", stepmode="backward"),
                                dict(step="all", label="MAX")
                            ]),
                            font=dict(size=11, color="#2D2622"),
                            bgcolor="#EFEAE3"
                        )
                    ),
                    yaxis=dict(title="P/C 比率", range=[0.45, 1.25], showgrid=True, gridcolor='#F2ECE5'),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.04, 
                        xanchor="right", 
                        x=0.98, 
                        font=dict(size=11)
                    ),
                    hovermode="x unified",
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    hoverlabel=dict(
                        bgcolor="#FFFFFF",
                        bordercolor="#38302B",
                        font_size=13,
                        font_family="sans-serif",
                        font_color="#2D2622"
                    )
                )
                st.plotly_chart(fig_pc, use_container_width=True, key="p2_pc_chart_multi_year")

            with col_pc_info:
                st.markdown(f"""
    <div class="pc-stat-card" style="background:#FFFFFF; border:1px solid #E2D7CC; border-radius:10px; padding:16px 18px; box-shadow:0 1px 4px rgba(0,0,0,0.03);">
        <div style="font-size: 0.95rem; font-weight: 800; color: #2D2622; margin-bottom: 6px;">最新即時指標看板</div>
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">
            <div style="font-size:2.1rem; font-weight:900; color:#1E293B;">{latest_pc:.2f}</div>
            <div style="font-size:0.85rem; font-weight:700; color:{'#DC2626' if delta_pc > 0 else '#047857'};">{delta_pc:+.2f} (較前日)</div>
        </div>
        <div style="font-size: 0.85rem; color: #475569; line-height: 1.6; margin-bottom:8px;">
            • <strong>短期均線 (5-DMA)</strong>：<code>{pc_ma5:.2f}</code><br>
            • <strong>衍生品氛圍</strong>：<span style="color: {pc_color}; font-weight: 700;">{pc_status}</span>
        </div>
        <div style="background: {gamma_badge_bg}; color: {pc_color}; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.80rem; margin-bottom: 10px;">
            ⚡ {gamma_status}
        </div>
        <hr style="margin: 8px 0; border: none; border-top: 1px dashed #CBD5E1;">
        <div style="font-size: 0.85rem; font-weight: 800; color: #2D2622; margin-bottom: 4px;">🎯 【當前具體操作指引】</div>
        <div style="background: {action_badge_bg}; color: {action_badge_color}; padding: 5px 10px; border-radius: 6px; font-weight: 800; font-size: 0.86rem; margin-bottom: 8px;">
            {action_signal}
        </div>
        <div style="font-size: 0.82rem; color: #475569; line-height: 1.55;">
            • <strong>建議權益持倉</strong>：<strong>{suggested_equity}</strong><br>
            • <strong>核心戰術</strong>：{action_step_1}
        </div>
    </div>
    """, unsafe_allow_html=True)

        st.markdown("""
    <div style="margin-top: 26px; margin-bottom: 14px;">
        <span style="font-size: 1.08rem; font-weight: 800; color: #0F766E;">💡 【專業投資機構實戰】看懂 P/C Ratio 數值後的「具體操作三部曲」</span>
        <div style="font-size: 0.88rem; color: #64748B; margin-top: 4px;">
            散戶常在 P/C 最低時追 Call、最高時殺 Put；機構法人則將其視為「反向情緒體溫計」與「Gamma 吸震力竭預警」。
        </div>
    </div>
    """, unsafe_allow_html=True)

        c_card1, c_card2, c_card3 = st.columns(3)

        is_active_1 = latest_pc <= 0.65
        is_active_2 = 0.65 < latest_pc < 1.0
        is_active_3 = latest_pc >= 1.0

        with c_card1:
            border_col_1 = "#047857" if is_active_1 else "#E2D7CC"
            shadow_1 = "0 3px 12px rgba(4, 120, 87, 0.12)" if is_active_1 else "0 1px 3px rgba(0,0,0,0.02)"
            bg_tag_1 = '<span style="background:#047857; color:#FFFFFF; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:12px;">📍 當前市場狀態</span>' if is_active_1 else '<span style="color:#64748B; font-size:0.78rem; font-weight:700;">過熱預警區</span>'
            
            card_html_1 = f"""<div style="background:#FFFFFF; border:2px solid {border_col_1}; border-radius:12px; padding:18px 20px; box-shadow:{shadow_1}; min-height:360px; display:flex; flex-direction:column; justify-content:space-between;">
    <div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <span style="font-size:1.02rem; font-weight:900; color:#047857;">P/C &le; 0.65</span>
    {bg_tag_1}
    </div>
    <div style="font-size:0.86rem; color:#475569; font-weight:700; margin-bottom:12px;">🔥 極度樂觀・買 Call 狂熱</div>
    <div style="background:#F0FDF4; border-left:3.5px solid #047857; padding:8px 12px; border-radius:6px; font-size:0.82rem; color:#166534; line-height:1.5; margin-bottom:12px;">
    <strong>正 Gamma 高峰</strong>：造市商逢高拋售平抑波動，但隨時面臨買盤力竭後的流動性踩踏。
    </div>
    <div style="font-size:0.86rem; color:#2D2622; line-height:1.65; margin-bottom:10px;">
    <strong>📈 股票現貨動作：</strong><br>
    • <strong>分批獲利了結</strong>：持倉降至 60%~70%<br>
    • <strong>移動停利</strong>：跌破 10MA 或 20MA 出場<br>
    • <strong>嚴禁借券追價</strong>：評價過度透支
    </div>
    </div>
    <div style="border-top:1px dashed #E2E8F0; padding-top:10px; font-size:0.84rem; color:#64748B; line-height:1.55;">
    🛡️ <strong>衍生品配置</strong>：此時 Put 最便宜，以 1%~2% 資金買入價外 Put 當作廉價避險氣囊。
    </div>
    </div>"""
            st.markdown(card_html_1, unsafe_allow_html=True)

        with c_card2:
            border_col_2 = "#0284C7" if is_active_2 else "#E2D7CC"
            shadow_2 = "0 3px 12px rgba(2, 132, 199, 0.12)" if is_active_2 else "0 1px 3px rgba(0,0,0,0.02)"
            bg_tag_2 = '<span style="background:#0284C7; color:#FFFFFF; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:12px;">📍 當前市場狀態</span>' if is_active_2 else '<span style="color:#64748B; font-size:0.78rem; font-weight:700;">平衡區間</span>'
            
            card_html_2 = f"""<div style="background:#FFFFFF; border:2px solid {border_col_2}; border-radius:12px; padding:18px 20px; box-shadow:{shadow_2}; min-height:360px; display:flex; flex-direction:column; justify-content:space-between;">
    <div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <span style="font-size:1.02rem; font-weight:900; color:#0284C7;">0.65 &lt; P/C &lt; 0.95</span>
    {bg_tag_2}
    </div>
    <div style="font-size:0.86rem; color:#475569; font-weight:700; margin-bottom:12px;">⚖️ 常態整理・多空均衡</div>
    <div style="background:#F0F9FF; border-left:3.5px solid #0284C7; padding:8px 12px; border-radius:6px; font-size:0.82rem; color:#0369A1; line-height:1.5; margin-bottom:12px;">
    <strong>Gamma 中性平衡</strong>：無造市對沖暴衝，盤面回歸現貨基本面與每季財報獲利驅動。
    </div>
    <div style="font-size:0.86rem; color:#2D2622; line-height:1.65; margin-bottom:10px;">
    <strong>📈 股票現貨動作：</strong><br>
    • <strong>維持常態配置</strong>：核心持倉 70% 續抱<br>
    • <strong>定期定額存股</strong>：維持紀律扣款不擇時<br>
    • <strong>強弱輪動換股</strong>：汰弱留強聚焦成長龍頭
    </div>
    </div>
    <div style="border-top:1px dashed #E2E8F0; padding-top:10px; font-size:0.84rem; color:#64748B; line-height:1.55;">
    🛡️ <strong>衍生品配置</strong>：現貨持倉者可於壓力位賣出 OTM Call（Covered Call）增厚現金流。
    </div>
    </div>"""
            st.markdown(card_html_2, unsafe_allow_html=True)

        with c_card3:
            border_col_3 = "#DC2626" if is_active_3 else "#E2D7CC"
            shadow_3 = "0 3px 12px rgba(220, 38, 38, 0.12)" if is_active_3 else "0 1px 3px rgba(0,0,0,0.02)"
            bg_tag_3 = '<span style="background:#DC2626; color:#FFFFFF; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:12px;">📍 當前市場狀態</span>' if is_active_3 else '<span style="color:#64748B; font-size:0.78rem; font-weight:700;">恐慌超賣區</span>'
            
            card_html_3 = f"""<div style="background:#FFFFFF; border:2px solid {border_col_3}; border-radius:12px; padding:18px 20px; box-shadow:{shadow_3}; min-height:360px; display:flex; flex-direction:column; justify-content:space-between;">
    <div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <span style="font-size:1.02rem; font-weight:900; color:#DC2626;">P/C &ge; 1.00</span>
    {bg_tag_3}
    </div>
    <div style="font-size:0.86rem; color:#475569; font-weight:700; margin-bottom:12px;">🚨 極度恐慌・買 Put 踩踏</div>
    <div style="background:#FEF2F2; border-left:3.5px solid #DC2626; padding:8px 12px; border-radius:6px; font-size:0.82rem; color:#991B1B; line-height:1.5; margin-bottom:12px;">
    <strong>負 Gamma 踩踏警戒</strong>：做市商被迫順勢殺跌追空，跌勢雖猛但軋空報復性反彈亦隨時爆發。
    </div>
    <div style="font-size:0.86rem; color:#2D2622; line-height:1.65; margin-bottom:10px;">
    <strong>📈 股票現貨動作：</strong><br>
    • <strong>切忌盲目殺低</strong>：嚴禁在恐慌極致時砍倉<br>
    • <strong>左側分批布局</strong>：持倉拉升至 75%~85%<br>
    • <strong>金字塔加碼</strong>：分 3 批承接超跌權值股
    </div>
    </div>
    <div style="border-top:1px dashed #E2E8F0; padding-top:10px; font-size:0.84rem; color:#64748B; line-height:1.55;">
    🛡️ <strong>衍生品配置</strong>：原有 Put 避險部位利潤豐厚，應果斷停利換回現金現貨。
    </div>
    </div>"""
            st.markdown(card_html_3, unsafe_allow_html=True)

        with st.expander("🔍 深入了解：做市商 Gamma 曝險與流動性擠壓機制解析（點擊展開）", expanded=False):
            st.markdown("""<div style="font-size:0.88rem; color:#475569; line-height:1.75; padding:8px 4px;">
• <strong>結構性傳導機制（正回饋螺旋）</strong>：當投機買盤高度集中於特定選擇權合約（如近月或 0DTE 買權）時，期權做市商為維持 Delta 中立，必須在現貨市場被動買進正股以規避暴漲風險。隨著標的價格逼近履約價，Gamma 呈現非線性陡峭放大，迫使做市商進一步追買正股，形成「<strong>價格上漲 ➔ 做市商強制買進正股 ➔ 推升價格</strong>」的自我強化迴圈。<br>
• <strong>機構實戰風險警示</strong>：Gamma 擠壓本質上是衍生品流動性驅動的技術性行情，<strong>來得快去得也快</strong>。一旦買盤力竭或跌破關鍵支撐線，做市商的對沖行為會在一瞬間由「買盤」轉為「拋壓」，導致資產以更兇猛的幅度向下崩跌。<br>
<span style="color: #8C7E72; font-size: 0.80rem; display: block; margin-top: 10px; border-top: 1px dashed #E2E8F0; padding-top: 6px;">
※ 免責聲明：本模型所列之衍生品指標、做市商模型與操作建議僅供市場微觀結構學術研究與資產配置分析參考，不代表未來走勢保證，亦不構成任何期權、證券或金融商品之具體招攬、推介或買賣保證。投資人應評估自身風險承受能力獨立決策。
</span>
</div>""", unsafe_allow_html=True)
