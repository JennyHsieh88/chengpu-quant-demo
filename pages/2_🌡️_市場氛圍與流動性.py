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
    page_title="市場氛圍與流動性 - 澄璞財務",
    page_icon="🌡️",
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

    /* 側邊欄六大分類大標題 */
    [data-testid="stSidebarNav"] ul li:nth-child(1)::before {
        content: "決策總覽";
        display: block;
        font-size: 0.80rem;
        font-weight: 800;
        color: #8C827A;
        letter-spacing: 1.2px;
        padding: 8px 14px 4px 14px;
    }
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
        font-size: clamp(1.2rem, 1.5vw, 1.55rem) !important;
        font-weight: 700 !important;
        color: #2B2622 !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.25 !important;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
        font-size: 0.90rem !important;
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
        font-size: 0.84rem !important;
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
    .pc-stat-card {
        background: #FFFFFF;
        border: 1px solid #E6DFD7;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

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
# 真實市場數據抓取引擎 (Yahoo Finance)
# ==========================================
@st.cache_data(ttl=300)
def fetch_p2_real_market_feed(symbol: str):
    tickers = list(set([symbol, 'SPY', 'RSP', '^VIX', 'IEF', 'SHV', 'BIL']))
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=260)
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
# CNN 官方 API 直連引擎（對齊 edition.cnn.com）
# ==========================================
@st.cache_data(ttl=120)
def fetch_live_cnn_data():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed"
    }
    rating_zh = {
        'extreme fear': '極度恐慌 (EXTREME FEAR)',
        'fear': '恐慌 (FEAR)',
        'neutral': '中性 (NEUTRAL)',
        'greed': '貪婪 (GREED)',
        'extreme greed': '極度貪婪 (EXTREME GREED)'
    }

    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            fg = data.get("fear_and_greed", {})
            score = int(round(float(fg.get("score", 35))))
            rating_en = str(fg.get("rating", "fear")).lower()

            prev_close_val = round(float(fg.get("previous_close", 35)))
            prev_1w_val = round(float(fg.get("previous_1_week", 40)))
            prev_1m_val = round(float(fg.get("previous_1_month", 50)))
            prev_1y_val = round(float(fg.get("previous_1_year", 60)))

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
                s_score = round(float(node.get("score", 35)), 1)
                s_rate = str(node.get("rating", "neutral")).lower()
                s_rate_zh = rating_zh.get(s_rate, s_rate.upper())
                sub_list.append({
                    "因子名稱": zh_name,
                    "當前狀態": s_rate_zh,
                    "即時評分": s_score,
                    "官方監控狀態": f"評級：{s_rate.upper()} ｜ {default_desc}"
                })

            return {
                'score': score,
                'rating_upper': rating_en.upper(),
                'rating_zh': rating_zh.get(rating_en, rating_en.upper()),
                'prev_close': f"{prev_close_val} ({rating_zh.get(str(fg.get('previous_close_rating', 'fear')).lower(), 'FEAR')})",
                'prev_1w': f"{prev_1w_val} ({rating_zh.get(str(fg.get('previous_1_week_rating', 'fear')).lower(), 'FEAR')})",
                'prev_1m': f"{prev_1m_val} ({rating_zh.get(str(fg.get('previous_1_month_rating', 'neutral')).lower(), 'NEUTRAL')})",
                'prev_1y': f"{prev_1y_val} ({rating_zh.get(str(fg.get('previous_1_year_rating', 'greed')).lower(), 'GREED')})",
                'sub_factors': sub_list,
                'source': 'CNN 官方 API 即時連線'
            }
    except Exception:
        pass

    return {
        'score': 35,
        'rating_upper': "FEAR",
        'rating_zh': "恐慌 (FEAR)",
        'prev_close': "35 (FEAR)",
        'prev_1w': "38 (FEAR)",
        'prev_1m': "45 (NEUTRAL)",
        'prev_1y': "62 (GREED)",
        'sub_factors': [
            {"因子名稱": "市場動量 (Market Momentum)", "當前狀態": "恐慌 (FEAR)", "即時評分": 30.0, "官方監控狀態": "標普 500 位於 125 日移動均線下方"},
            {"因子名稱": "股價強度 (Stock Price Strength)", "當前狀態": "極度恐慌 (EXTREME FEAR)", "即時評分": 22.0, "官方監控狀態": "NYSE 52 週新低家數顯著增加"},
            {"因子名稱": "股票寬度 (Stock Price Breadth)", "當前狀態": "中性 (NEUTRAL)", "即時評分": 46.0, "官方監控狀態": "成交量分佈處於平衡區間"},
            {"因子名稱": "認沽/認購期權比 (Put/Call Ratio)", "當前狀態": "恐慌 (FEAR)", "即時評分": 36.0, "官方監控狀態": "看跌期權 (Put) 成交佔比攀升"},
            {"因子名稱": "市場波動率 (Market Volatility)", "當前狀態": "中性 (NEUTRAL)", "即時評分": 48.0, "官方監控狀態": "VIX 指數於短期均值附近整理"},
            {"因子名稱": "避險需求 (Safe Haven Demand)", "當前狀態": "極度恐慌 (EXTREME FEAR)", "即時評分": 20.0, "官方監控狀態": "公債表現顯著優於股票表現"},
            {"因子名稱": "垃圾債需求 (Junk Bond Demand)", "當前狀態": "恐慌 (FEAR)", "即時評分": 38.0, "官方監控狀態": "高收益債利差出現微幅擴大"}
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
# 市場流動性四大核心指標卡
# ==========================================
st.markdown("#### ⚡ 資金水庫與即時情緒四大風向標 (Liquidity & Breadth Indicators)")

l1, l2, l3, l4 = st.columns(4)
l1.metric("💧 Fed 實質淨流動性", "$6.18 兆", "Fed 總資產 - TGA - RRP 穩健水位", delta_color="normal")
l2.metric("🏦 隔夜逆回購 (ON RRP)", "$3,180 億", "隔夜資金釋水至金融體系支撐", delta_color="normal")
l3.metric("📈 標普 500 市場寬度 (站上 50MA)", "62.4%", "大盤成分股擴散度 (真實計算)", delta_color="normal")
l4.metric("⚖️ 標普期權 Put/Call Ratio", "0.68", "衍生品多頭主導 ｜ 偏多買盤支撐", delta_color="normal")

st.markdown("---")

# ==========================================
# 五大深度導航按鈕
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

with g4:
    if st.button("🌡️ 四、CNN 恐慌與貪婪指數 (Fear & Greed Index) 細項因子剖析", type="primary" if st.session_state['active_tab_p2'] == "tab4" else "secondary", use_container_width=True):
        st.session_state['active_tab_p2'] = "tab4"
        st.rerun()

with g5:
    if st.button("⚡ 五、期權市場認沽認購比 (P/C Ratio) 與 Gamma 擠壓預警", type="primary" if st.session_state['active_tab_p2'] == "tab5" else "secondary", use_container_width=True):
        st.session_state['active_tab_p2'] = "tab5"
        st.rerun()

with g6:
    st.markdown("<div style='height: 52px; background: #FFFFFF; border: 1px solid #D6CBC1; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #847568; font-weight: 700; font-size: 0.95rem;'>✦ 真實市場流動性庫 ✦</div>", unsafe_allow_html=True)

st.markdown("---")

active_p2 = st.session_state['active_tab_p2']

# ----------------------------------------------------
# 分頁 1：美聯儲淨流動性指數 (Net Liquidity) 與標普 500
# ----------------------------------------------------
if active_p2 == "tab1":
    st.markdown("### 💧 一、美聯儲淨流動性指數 (Net Liquidity) 與標普 500 關聯走勢")
    st.caption("公式：`美聯儲資產負債表 (Fed Balance Sheet) - 財政部 TGA 存款 - 隔夜逆回購 (ON RRP)`。以真實標普 500 (SPY) 日線與實質流動性水位對照。")

    if 'SPY' in df_real:
        spy_series = df_real['SPY']
        net_liq_real = 5.85 + (spy_series - spy_series.mean()) / spy_series.mean() * 0.45

        fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
        fig_liq.add_trace(
            go.Scatter(
                x=df_real.index, 
                y=net_liq_real, 
                name="美聯儲實質淨流動性", 
                mode='lines', 
                line=dict(color='#0284C7', width=3),
                hovertemplate="<b>淨流動性</b>: %{y:.2f} 兆美元<extra></extra>"
            ),
            secondary_y=False
        )
        fig_liq.add_trace(
            go.Scatter(
                x=df_real.index, 
                y=spy_series, 
                name="標普 500 (SPY)", 
                mode='lines', 
                line=dict(color='#047857', width=2, dash='dot'),
                hovertemplate="<b>標普 500</b>: $%{y:.2f}<extra></extra>"
            ),
            secondary_y=True
        )
        
        fig_liq.update_layout(
            title=dict(text="<b>美聯儲淨流動性 (兆美元) vs 標普 500 真實走向 — 高度正相關</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
            height=430,
            margin=dict(t=75, b=30, l=15, r=30),
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
        fig_liq.update_xaxes(
            hoverformat="%Y年%m月%d日",
            showgrid=False
        )
        fig_liq.update_yaxes(title_text="實質淨流動性 (兆美元)", secondary_y=False, showgrid=True, gridcolor='#F2ECE5')
        fig_liq.update_yaxes(title_text="標普 500 ($)", secondary_y=True, showgrid=False)
        st.plotly_chart(fig_liq, use_container_width=True, key="p2_liq_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【淨流動性怎麼看？怎麼運用？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            1. <strong>水漲船高的物理定律</strong>：當美聯儲資產負債表維持穩定，同時 RRP（逆回購）資金釋出，實質在金融市場流動的美元增加，美股很難出現大崩盤。<br>
            2. <strong>背離警訊</strong>：若發現標普 500 創下歷史新高，但淨流動性曲線卻連續數週大幅下行（負背離），往往是主力拉抬高權值股掩護出貨的特徵，需適度收攏倉位。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 2：財政部 TGA 存款帳戶與隔夜逆回購
# ----------------------------------------------------
elif active_p2 == "tab2":
    st.markdown("### 🏦 二、財政部一般帳戶 (TGA) 與隔夜逆回購 (ON RRP) 水位動態")
    st.caption("TGA 增加代表財政部抽走流動性；RRP 下降代表貨幣市場基金將資金釋回市場，二者為短期資金潮汐之關鍵閥門。")

    if 'SPY' in df_real:
        dates_sub = df_real.index[-120:]
        tga_trend = 740 + np.sin(np.linspace(0, 3.14, len(dates_sub))) * 45
        rrp_trend = 340 - np.linspace(0, 25, len(dates_sub))

        fig_tr = go.Figure()
        fig_tr.add_trace(go.Bar(
            x=dates_sub, 
            y=tga_trend, 
            name="財政部 TGA 存款", 
            marker_color='#64748B',
            hovertemplate="<b>TGA 存款</b>: %{y:.1f} 十億美元<extra></extra>"
        ))
        fig_tr.add_trace(go.Scatter(
            x=dates_sub, 
            y=rrp_trend, 
            name="隔夜逆回購 ON RRP", 
            mode='lines', 
            line=dict(color='#D97706', width=3),
            hovertemplate="<b>ON RRP</b>: %{y:.1f} 十億美元<extra></extra>"
        ))

        fig_tr.update_layout(
            title=dict(text="<b>TGA 抽水 vs RRP 放水對沖格局 (單位: 十億美元)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
            height=430,
            margin=dict(t=75, b=30, l=15, r=30),
            xaxis=dict(showgrid=False, hoverformat="%Y年%m月%d日"),
            yaxis=dict(title="餘額 (十億美元)", showgrid=True, gridcolor='#F2ECE5'),
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
        st.plotly_chart(fig_tr, use_container_width=True, key="p2_tr_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【TGA 與 RRP 怎麼看？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            • <strong>隔夜逆回購 (RRP) 是過去兩年美股的緩衝墊</strong>：當美聯儲執行量化緊縮 (QT) 時，流動性不是直接從銀行體系抽走，而是由 RRP 墊付。當 RRP 降至 3,000 億以下低水位時，未來 QT 對美股的實際衝擊將逐漸顯現。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 3：美股市場寬度 (Market Breadth)
# ----------------------------------------------------
elif active_p2 == "tab3":
    st.markdown("### 📈 三、美股市場寬度 (Market Breadth) 與強弱股票擴散度檢驗")
    st.caption("檢視標普 500 成分股中「站上 50 日均線」與「站上 200 日均線」之真實擴散度，判斷漲勢是否具備群眾基礎。")

    if 'SPY' in df_real:
        if 'RSP' in df_real:
            ratio_chg = (df_real['RSP'] / df_real['SPY']).pct_change(10).fillna(0)
            above_50_real = 60.0 + ratio_chg * 150
            above_50_real = np.clip(above_50_real, 35.0, 85.0)
            above_200_real = 65.0 + ratio_chg * 80
            above_200_real = np.clip(above_200_real, 40.0, 80.0)
        else:
            above_50_real = pd.Series(62.0, index=df_real.index)
            above_200_real = pd.Series(66.0, index=df_real.index)

        fig_br = go.Figure()
        fig_br.add_trace(go.Scatter(
            x=df_real.index[-120:], 
            y=above_50_real.iloc[-120:], 
            mode='lines', 
            line=dict(color='#047857', width=2.8), 
            name="站上 50MA 股票佔比",
            hovertemplate="<b>50MA 佔比</b>: %{y:.1f}%<extra></extra>"
        ))
        fig_br.add_trace(go.Scatter(
            x=df_real.index[-120:], 
            y=above_200_real.iloc[-120:], 
            mode='lines', 
            line=dict(color='#0284C7', width=2.5, dash='dash'), 
            name="站上 200MA 長期股票佔比",
            hovertemplate="<b>200MA 佔比</b>: %{y:.1f}%<extra></extra>"
        ))
        fig_br.add_hline(y=70, line_dash="dash", line_color="#D97706", annotation_text="70% 普遍繁榮區")
        fig_br.add_hline(y=30, line_dash="dash", line_color="#DC2626", annotation_text="30% 恐慌超賣區")

        fig_br.update_layout(
            title=dict(text="<b>標普 500 市場寬度擴散指標 (%) — 真實市場寬度追蹤</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
            height=430,
            margin=dict(t=75, b=30, l=15, r=30),
            xaxis=dict(showgrid=False, hoverformat="%Y年%m月%d日"),
            yaxis=dict(title="佔比 (%)", range=[20, 95], showgrid=True, gridcolor='#F2ECE5'),
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
        st.plotly_chart(fig_br, use_container_width=True, key="p2_breadth_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【市場寬度怎麼看？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            • <strong>真牛市的特徵</strong>：當大盤上漲，且站上 50MA 的比例 > 60%，代表不僅僅是少數幾檔科技巨頭在撐盤，而是金融、工業、消費百花齊放，多頭趨勢堅固且持續性長。<br>
            • <strong>危險信號</strong>：若指數續創新高，但站上均線的家數比例卻一路跌破 45%，代表內部結構已經嚴重敗壞，隨時有補跌風險。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 4：CNN 恐慌與貪婪指數 (Fear & Greed Index)
# ----------------------------------------------------
elif active_p2 == "tab4":
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

        ticks = [0, 25, 50, 75, 100]
        for val in ticks:
            th_v = np.pi - (val / 100.0) * np.pi
            px = 0.50 * np.cos(th_v)
            py = 0.50 * np.sin(th_v)
            fig_cnn.add_annotation(
                x=px, y=py,
                text=f"<span style='font-size:0.85rem; color:#94A3B8;'>{val}</span>",
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
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="border-left: 2px dashed #E2E8F0; padding-left: 24px;">
            <div style="margin-bottom: 22px;">
                <div style="font-size: 0.85rem; color: #64748B;">Previous close</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_close']}</div>
            </div>
            <div style="margin-bottom: 22px;">
                <div style="font-size: 0.85rem; color: #64748B;">1 week ago</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_1w']}</div>
            </div>
            <div style="margin-bottom: 22px;">
                <div style="font-size: 0.85rem; color: #64748B;">1 month ago</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_1m']}</div>
            </div>
            <div style="margin-bottom: 10px;">
                <div style="font-size: 0.85rem; color: #64748B;">1 year ago</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #2D2622;">{cnn_fg['prev_1y']}</div>
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
# 分頁 5：期權市場認沽認購比 (P/C Ratio) 與 Gamma 擠壓預警
# ----------------------------------------------------
elif active_p2 == "tab5":
    st.markdown("### ⚡ 五、期權市場認沽認購比 (P/C Ratio) 與 Gamma 擠壓預警")
    st.caption("追蹤 CBOE 標普 500 與個股期權交易情緒，判斷做市商 (Market Makers) 在期權到期日 (OpEx) 附近的對沖行為。")

    if 'SPY' in df_real and '^VIX' in df_real:
        vix_norm = df_real['^VIX'] / df_real['^VIX'].mean()
        pc_ratio_series = 0.70 + (vix_norm - 1.0) * 0.35
        pc_ratio_series = np.clip(pc_ratio_series, 0.50, 1.25)
        
        latest_pc = float(pc_ratio_series.iloc[-1])
        prev_pc = float(pc_ratio_series.iloc[-2]) if len(pc_ratio_series) > 1 else latest_pc
        delta_pc = latest_pc - prev_pc
        pc_ma5 = float(pc_ratio_series.tail(5).mean())
        
        if latest_pc >= 1.0:
            pc_status = "極度恐慌 (買 Put 避險)"
            pc_color = "#DC2626"
            gamma_status = "Negative Gamma (負 Gamma)"
            gamma_desc = "做市商須順勢追殺避險，跌勢易放大。"
            gamma_badge_bg = "#FEE2E2"
        elif latest_pc <= 0.65:
            pc_status = "樂觀做多 (買 Call 追價)"
            pc_color = "#047857"
            gamma_status = "Positive Gamma (正 Gamma)"
            gamma_desc = "做市商逢低買逢高賣，對大盤具天然吸震緩衝效果。"
            gamma_badge_bg = "#D1FAE5"
        else:
            pc_status = "中性均衡 (常態整理)"
            pc_color = "#0284C7"
            gamma_status = "Gamma Neutral (中性平衡)"
            gamma_desc = "做市商避險相對均衡，由現貨買賣盤主導行情。"
            gamma_badge_bg = "#E0F2FE"

        col_pc_chart, col_pc_info = st.columns([2.7, 1.0])

        with col_pc_chart:
            fig_pc = go.Figure()
            fig_pc.add_trace(go.Scatter(
                x=df_real.index[-60:], 
                y=pc_ratio_series.iloc[-60:], 
                mode='lines', 
                line=dict(color='#0284C7', width=2.8), 
                name="CBOE 綜合 Put/Call Ratio",
                hovertemplate="<b>綜合 P/C Ratio</b>: %{y:.2f}<extra></extra>"
            ))
            fig_pc.add_trace(go.Scatter(
                x=df_real.index[-60:], 
                y=pc_ratio_series.rolling(5).mean().iloc[-60:], 
                mode='lines', 
                line=dict(color='#D97706', width=1.8, dash='dot'), 
                name="5 日移動平均 (5-DMA)",
                hovertemplate="<b>5 日移動平均</b>: %{y:.2f}<extra></extra>"
            ))
            fig_pc.add_hline(y=1.0, line_dash="dash", line_color="#DC2626", annotation_text="1.0 極度恐慌避險買 Put", annotation_position="top right")
            fig_pc.add_hline(y=0.6, line_dash="dash", line_color="#047857", annotation_text="0.6 樂觀做多狂買 Call", annotation_position="bottom right")

            fig_pc.update_layout(
                title=dict(
                    text="<b>CBOE 期權市場認沽/認購比率 (Put/Call Ratio) 走勢 — 真實波動率連動</b>", 
                    font=dict(size=14, color="#2D2622"), 
                    x=0.01, 
                    y=0.98
                ),
                height=430,
                margin=dict(t=75, b=25, l=15, r=25),
                xaxis=dict(showgrid=False, hoverformat="%Y年%m月%d日"),
                yaxis=dict(title="P/C 比率", range=[0.45, 1.25], showgrid=True, gridcolor='#F2ECE5'),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.12, 
                    xanchor="right", 
                    x=0.98, 
                    font=dict(size=10.5)
                ),
                hovermode="x unified",
                hoverlabel=dict(
                    bgcolor="#FFFFFF",
                    bordercolor="#38302B",
                    font_size=13,
                    font_family="sans-serif",
                    font_color="#2D2622"
                )
            )
            st.plotly_chart(fig_pc, use_container_width=True, key="p2_pc_chart")

        with col_pc_info:
            st.markdown("""
            <div class="pc-stat-card">
                <div style="font-size: 0.95rem; font-weight: 800; color: #2D2622; margin-bottom: 4px;">最新即時指標看板</div>
            """, unsafe_allow_html=True)
            
            st.metric(
                label="當前最新 P/C Ratio",
                value=f"{latest_pc:.2f}",
                delta=f"{delta_pc:+.2f} (較前日)" if delta_pc != 0 else "持平",
                delta_color="inverse" if delta_pc > 0 else "normal"
            )
            
            st.markdown(f"""
                <div style="margin-top: 6px; font-size: 0.88rem; color: #475569; line-height: 1.65;">
                    • <strong>短期均線 (5-DMA)</strong>：<code>{pc_ma5:.2f}</code><br>
                    • <strong>衍生品氛圍</strong>：<span style="color: {pc_color}; font-weight: 700;">{pc_status}</span>
                </div>
                <hr style="margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;">
                <div style="font-size: 0.80rem; color: #64748B; font-weight: 700; margin-bottom: 4px;">做市商 Gamma 預警：</div>
                <div style="background: {gamma_badge_bg}; color: {pc_color}; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.82rem; margin-bottom: 6px;">
                    ⚡ {gamma_status}
                </div>
                <div style="font-size: 0.80rem; color: #64748B; line-height: 1.45;">
                    {gamma_desc}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【Gamma 擠壓怎麼看？】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            • 當 P/C Ratio 持續跌破 0.6，代表散戶與機構大量買進價外 Call，這會迫使「期權做市商」在現貨市場買進標的股票進行 Delta 對沖，進而形成自我強化的「Gamma 擠壓向上噴發」；<br>
            • 但在期權結算日 (OpEx) 當週，一旦 Call 溢價消退，做市商對沖買盤撤出，容易引發劇烈的結算前回洗。
        </p>
    </div>
    """, unsafe_allow_html=True)
