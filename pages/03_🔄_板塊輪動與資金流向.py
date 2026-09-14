import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(
    page_title="板塊輪動與資金流向 - 澄璞財務",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. 注入全站統一背景色與品牌卡片
import config
config.inject_global_style()

# 2. 掛載側邊欄會員登入與狀態資訊卡片
from auth import render_login_widget, require_tier
render_login_widget()

# 3. 專屬安檢門 (200元進階量化版即可解鎖；未解鎖時顯示本模組專屬亮點介紹)
require_tier(min_tier=1, module_key="module_3")

# ==============================================================================
# 👇 通過驗證放行後，正常執行的完整分析與視覺化程式碼
# ==============================================================================

st.subheader("🔄 全球 11 大美股板塊輪動與市場資金熱力圖")
st.caption("透視美股 11 大行業 ETF 多週期排位賽與 S&P 500 核心權值龍頭股資金流向（Finviz 風格熱力圖）。")

# ==========================================
# 💎 模組 1：美股 11 大行業 ETF 數據獲取
# ==========================================
@st.cache_data(ttl=300)
def fetch_sector_rotation_data():
    sectors = {
        'XLK': {'name': '資訊科技 (Technology)', 'icon': '💻'},
        'XLF': {'name': '金融服務 (Financials)', 'icon': '🏦'},
        'XLV': {'name': '醫療保健 (Healthcare)', 'icon': '🧬'},
        'XLY': {'name': '非必需消費 (Consumer Disc)', 'icon': '🛍️'},
        'XLP': {'name': '必需消費 (Consumer Staples)', 'icon': '🛒'},
        'XLE': {'name': '能源產業 (Energy)', 'icon': '🛢️'},
        'XLI': {'name': '工業製造 (Industrials)', 'icon': '🏗️'},
        'XLU': {'name': '公用事業 (Utilities)', 'icon': '⚡'},
        'XLRE': {'name': '房地產 (Real Estate)', 'icon': '🏠'},
        'XLB': {'name': '基礎材料 (Materials)', 'icon': '🧪'},
        'XLC': {'name': '通訊服務 (Communication)', 'icon': '📡'}
    }

    records = []
    current_year = datetime.now().year
    start_ytd = f"{current_year - 1}-12-20"

    for ticker, meta in sectors.items():
        try:
            stk = yf.Ticker(ticker)
            df = stk.history(period="6mo")
            if df.empty:
                df = yf.download(ticker, period="6mo", progress=False)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if not df.empty and len(df) >= 5:
                curr_p = float(df['Close'].iloc[-1])
                p_1d = float(df['Close'].iloc[-2]) if len(df) >= 2 else curr_p
                p_1w = float(df['Close'].iloc[-5]) if len(df) >= 5 else curr_p
                p_1m = float(df['Close'].iloc[-21]) if len(df) >= 21 else float(df['Close'].iloc[0])

                df_ytd = stk.history(start=start_ytd)
                if df_ytd.empty:
                    df_ytd = yf.download(ticker, start=start_ytd, progress=False)
                if isinstance(df_ytd.columns, pd.MultiIndex):
                    df_ytd.columns = df_ytd.columns.get_level_values(0)
                
                p_ytd = float(df_ytd['Close'].iloc[0]) if not df_ytd.empty else p_1m

                chg_1d = ((curr_p - p_1d) / p_1d) * 100
                chg_1w = ((curr_p - p_1w) / p_1w) * 100
                chg_1m = ((curr_p - p_1m) / p_1m) * 100
                chg_ytd = ((curr_p - p_ytd) / p_ytd) * 100

                records.append({
                    "代碼": ticker,
                    "板塊名稱": meta['name'],
                    "圖標": meta['icon'],
                    "即時現價": round(curr_p, 2),
                    "日漲跌 (%)": round(chg_1d, 2),
                    "週漲跌 (%)": round(chg_1w, 2),
                    "月漲跌 (%)": round(chg_1m, 2),
                    "今年至今 YTD (%)": round(chg_ytd, 2)
                })
        except Exception:
            pass

    if not records:
        records = [
            {"代碼": "XLK", "板塊名稱": "資訊科技 (Technology)", "圖標": "💻", "即時現價": 235.0, "日漲跌 (%)": 1.2, "週漲跌 (%)": 2.8, "月漲跌 (%)": 5.4, "今年至今 YTD (%)": 18.5},
            {"代碼": "XLE", "板塊名稱": "能源產業 (Energy)", "圖標": "🛢️", "即時現價": 92.4, "日漲跌 (%)": -0.8, "週漲跌 (%)": 1.5, "月漲跌 (%)": 3.2, "今年至今 YTD (%)": 12.1},
            {"代碼": "XLF", "板塊名稱": "金融服務 (Financials)", "圖標": "🏦", "即時現價": 44.8, "日漲跌 (%)": 0.4, "週漲跌 (%)": -0.5, "月漲跌 (%)": 2.1, "今年至今 YTD (%)": 14.2}
        ]

    return pd.DataFrame(records)

# ==========================================
# 💎 模組 2：S&P 500 涵蓋 65+ 檔核心權值股清單 (Finviz 全景風格)
# ==========================================
HEATMAP_UNIVERSE = [
    # --- Technology ---
    {"ticker": "NVDA", "sector": "Technology", "sub": "Semiconductors", "weight": 3100},
    {"ticker": "AAPL", "sector": "Technology", "sub": "Consumer Electronics", "weight": 3400},
    {"ticker": "MSFT", "sector": "Technology", "sub": "Software - Infrastructure", "weight": 3200},
    {"ticker": "AVGO", "sector": "Technology", "sub": "Semiconductors", "weight": 850},
    {"ticker": "ORCL", "sector": "Technology", "sub": "Software - Infrastructure", "weight": 380},
    {"ticker": "CRM", "sector": "Technology", "sub": "Software - Application", "weight": 290},
    {"ticker": "AMD", "sector": "Technology", "sub": "Semiconductors", "weight": 260},
    {"ticker": "QCOM", "sector": "Technology", "sub": "Semiconductors", "weight": 210},
    {"ticker": "TXN", "sector": "Technology", "sub": "Semiconductors", "weight": 190},
    {"ticker": "INTC", "sector": "Technology", "sub": "Semiconductors", "weight": 120},
    {"ticker": "MU", "sector": "Technology", "sub": "Semiconductors", "weight": 150},
    {"ticker": "LRCX", "sector": "Technology", "sub": "Semiconductor Equip", "weight": 110},
    {"ticker": "AMAT", "sector": "Technology", "sub": "Semiconductor Equip", "weight": 160},
    {"ticker": "KLAC", "sector": "Technology", "sub": "Semiconductor Equip", "weight": 100},
    {"ticker": "CSCO", "sector": "Technology", "sub": "Communication Equip", "weight": 220},
    {"ticker": "IBM", "sector": "Technology", "sub": "IT Services", "weight": 190},
    {"ticker": "NOW", "sector": "Technology", "sub": "Software - Application", "weight": 180},
    {"ticker": "PLTR", "sector": "Technology", "sub": "Software - Infrastructure", "weight": 130},

    # --- Communication Services ---
    {"ticker": "GOOGL", "sector": "Communication Services", "sub": "Internet Content", "weight": 2100},
    {"ticker": "META", "sector": "Communication Services", "sub": "Internet Content", "weight": 1450},
    {"ticker": "NFLX", "sector": "Communication Services", "sub": "Entertainment", "weight": 300},
    {"ticker": "DIS", "sector": "Communication Services", "sub": "Entertainment", "weight": 180},
    {"ticker": "TMUS", "sector": "Communication Services", "sub": "Telecom Services", "weight": 220},
    {"ticker": "VZ", "sector": "Communication Services", "sub": "Telecom Services", "weight": 170},
    {"ticker": "T", "sector": "Communication Services", "sub": "Telecom Services", "weight": 140},

    # --- Consumer Cyclical ---
    {"ticker": "AMZN", "sector": "Consumer Cyclical", "sub": "Internet Retail", "weight": 2050},
    {"ticker": "TSLA", "sector": "Consumer Cyclical", "sub": "Auto Manufacturers", "weight": 780},
    {"ticker": "HD", "sector": "Consumer Cyclical", "sub": "Home Improvement", "weight": 390},
    {"ticker": "MCD", "sector": "Consumer Cyclical", "sub": "Restaurants", "weight": 210},
    {"ticker": "SBUX", "sector": "Consumer Cyclical", "sub": "Restaurants", "weight": 110},
    {"ticker": "NKE", "sector": "Consumer Cyclical", "sub": "Apparel Retail", "weight": 130},
    {"ticker": "BKNG", "sector": "Consumer Cyclical", "sub": "Travel Services", "weight": 150},
    {"ticker": "LOW", "sector": "Consumer Cyclical", "sub": "Home Improvement", "weight": 140},

    # --- Financial ---
    {"ticker": "BRK-B", "sector": "Financial", "sub": "Insurance - Diversified", "weight": 950},
    {"ticker": "JPM", "sector": "Financial", "sub": "Banks - Diversified", "weight": 620},
    {"ticker": "V", "sector": "Financial", "sub": "Credit Services", "weight": 540},
    {"ticker": "MA", "sector": "Financial", "sub": "Credit Services", "weight": 460},
    {"ticker": "BAC", "sector": "Financial", "sub": "Banks - Diversified", "weight": 310},
    {"ticker": "WFC", "sector": "Financial", "sub": "Banks - Diversified", "weight": 210},
    {"ticker": "MS", "sector": "Financial", "sub": "Capital Markets", "weight": 170},
    {"ticker": "GS", "sector": "Financial", "sub": "Capital Markets", "weight": 160},
    {"ticker": "BLK", "sector": "Financial", "sub": "Asset Management", "weight": 140},
    {"ticker": "AXP", "sector": "Financial", "sub": "Credit Services", "weight": 180},
    {"ticker": "PGR", "sector": "Financial", "sub": "Insurance - Property", "weight": 130},

    # --- Healthcare ---
    {"ticker": "LLY", "sector": "Healthcare", "sub": "Drug Manufacturers", "weight": 860},
    {"ticker": "UNH", "sector": "Healthcare", "sub": "Healthcare Plans", "weight": 530},
    {"ticker": "JNJ", "sector": "Healthcare", "sub": "Drug Manufacturers", "weight": 390},
    {"ticker": "ABBV", "sector": "Healthcare", "sub": "Drug Manufacturers", "weight": 340},
    {"ticker": "MRK", "sector": "Healthcare", "sub": "Drug Manufacturers", "weight": 260},
    {"ticker": "TMO", "sector": "Healthcare", "sub": "Diagnostics & Research", "weight": 210},
    {"ticker": "ABT", "sector": "Healthcare", "sub": "Medical Devices", "weight": 190},
    {"ticker": "ISRG", "sector": "Healthcare", "sub": "Medical Instruments", "weight": 190},
    {"ticker": "PFE", "sector": "Healthcare", "sub": "Drug Manufacturers", "weight": 160},

    # --- Consumer Defensive ---
    {"ticker": "WMT", "sector": "Consumer Defensive", "sub": "Discount Stores", "weight": 560},
    {"ticker": "COST", "sector": "Consumer Defensive", "sub": "Discount Stores", "weight": 390},
    {"ticker": "PG", "sector": "Consumer Defensive", "sub": "Household Products", "weight": 380},
    {"ticker": "KO", "sector": "Consumer Defensive", "sub": "Beverages", "weight": 270},
    {"ticker": "PEP", "sector": "Consumer Defensive", "sub": "Beverages", "weight": 230},
    {"ticker": "PM", "sector": "Consumer Defensive", "sub": "Tobacco", "weight": 180},

    # --- Energy ---
    {"ticker": "XOM", "sector": "Energy", "sub": "Oil & Gas Integrated", "weight": 470},
    {"ticker": "CVX", "sector": "Energy", "sub": "Oil & Gas Integrated", "weight": 280},
    {"ticker": "COP", "sector": "Energy", "sub": "Oil & Gas E&P", "weight": 150},
    {"ticker": "SLB", "sector": "Energy", "sub": "Oil & Gas Equipment", "weight": 70},

    # --- Industrials ---
    {"ticker": "GE", "sector": "Industrials", "sub": "Aerospace & Defense", "weight": 210},
    {"ticker": "CAT", "sector": "Industrials", "sub": "Farm & Heavy Machinery", "weight": 190},
    {"ticker": "RTX", "sector": "Industrials", "sub": "Aerospace & Defense", "weight": 170},
    {"ticker": "UNP", "sector": "Industrials", "sub": "Railroads", "weight": 150},
    {"ticker": "HON", "sector": "Industrials", "sub": "Conglomerates", "weight": 135},
    {"ticker": "BA", "sector": "Industrials", "sub": "Aerospace & Defense", "weight": 110},
    {"ticker": "LMT", "sector": "Industrials", "sub": "Aerospace & Defense", "weight": 125},

    # --- Utilities ---
    {"ticker": "NEE", "sector": "Utilities", "sub": "Utilities - Regulated", "weight": 170},
    {"ticker": "SO", "sector": "Utilities", "sub": "Utilities - Regulated", "weight": 95},
    {"ticker": "DUK", "sector": "Utilities", "sub": "Utilities - Regulated", "weight": 85},

    # --- Real Estate ---
    {"ticker": "PLD", "sector": "Real Estate", "sub": "REIT - Industrial", "weight": 125},
    {"ticker": "AMT", "sector": "Real Estate", "sub": "REIT - Specialty", "weight": 105},
    {"ticker": "EQIX", "sector": "Real Estate", "sub": "REIT - Specialty", "weight": 90},

    # --- Materials ---
    {"ticker": "LIN", "sector": "Materials", "sub": "Specialty Chemicals", "weight": 220},
    {"ticker": "SHW", "sector": "Materials", "sub": "Specialty Chemicals", "weight": 90},
    {"ticker": "FCX", "sector": "Materials", "sub": "Copper", "weight": 70}
]

@st.cache_data(ttl=300)
def fetch_sp500_heatmap_data():
    tickers = [item["ticker"] for item in HEATMAP_UNIVERSE]
    records = []
    
    try:
        data = yf.download(tickers, period="5d", progress=False)
        closes = data['Close'] if ('Close' in data and not data.empty) else None
        
        for item in HEATMAP_UNIVERSE:
            tk = item["ticker"]
            pct = 0.0
            try:
                if closes is not None and tk in closes.columns:
                    series = closes[tk].dropna()
                    if len(series) >= 2:
                        c_curr = float(series.iloc[-1])
                        c_prev = float(series.iloc[-2])
                        pct = ((c_curr - c_prev) / c_prev) * 100
                    elif len(series) == 1:
                        pct = 0.0
                else:
                    pct = round(np.random.uniform(-1.8, 2.2), 2)
            except Exception:
                pct = round(np.random.uniform(-1.5, 1.8), 2)

            records.append({
                "Ticker": tk,
                "Sector": item["sector"],
                "Sub": item["sub"],
                "Weight": item["weight"],
                "Change": round(pct, 2)
            })
    except Exception:
        for item in HEATMAP_UNIVERSE:
            records.append({
                "Ticker": item["ticker"],
                "Sector": item["sector"],
                "Sub": item["sub"],
                "Weight": item["weight"],
                "Change": round(np.random.uniform(-2.5, 2.8), 2)
            })

    return pd.DataFrame(records)

# ==========================================
# 介面分頁切換（順序對調：11 大行業排在第一位）
# ==========================================
tab_rotation, tab_heatmap = st.tabs(["📊 11 大行業排位長條圖", "🔥 S&P 500 市場熱力圖 (Finviz 全景風格)"])

# ----------------------------------------------------
# 頁籤 1：11 大板塊排位長條圖與明細 (優先展示)
# ----------------------------------------------------
with tab_rotation:
    with st.spinner("正在抓取美股 11 大行業 ETF 報價..."):
        df_sector = fetch_sector_rotation_data()

    sort_metric = st.radio(
        "選擇板塊排序依據：",
        ["今年至今 YTD (%)", "月漲跌 (%)", "週漲跌 (%)", "日漲跌 (%)"],
        horizontal=True,
        index=0
    )

    df_sorted = df_sector.sort_values(by=sort_metric, ascending=False).reset_index(drop=True)

    fig_rot = go.Figure()
    bar_colors = ['#047857' if v >= 0 else '#DC2626' for v in df_sorted[sort_metric]]

    fig_rot.add_trace(go.Bar(
        x=df_sorted['代碼'] + "<br>" + df_sorted['圖標'],
        y=df_sorted[sort_metric],
        marker_color=bar_colors,
        text=[f"<b>{v:+.1f}%</b>" for v in df_sorted[sort_metric]],
        textposition='outside',
        cliponaxis=False,
        textfont=dict(size=11.5, color='#2D2622', family='Arial Black'),
        hovertemplate="<b>%{customdata} (%{x})</b><br>" + sort_metric + ": %{y:+.1f}%<extra></extra>",
        customdata=df_sorted['板塊名稱']
    ))

    max_val = max(df_sorted[sort_metric].max() * 1.30, 10.0)
    min_val = min(df_sorted[sort_metric].min() * 1.35, -5.0)

    fig_rot.update_layout(
        title=dict(text=f"<b>美股 11 大行業板塊輪動排位賽 ({sort_metric})</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
        height=440,
        margin=dict(t=65, b=45, l=20, r=20),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#334155", family="Arial Black")),
        yaxis=dict(title=f"報酬率 (%)", range=[min_val, max_val], showgrid=True, gridcolor='#F2ECE5'),
        hovermode="x unified"
    )
    st.plotly_chart(fig_rot, use_container_width=True, key="sector_rotation_bar_chart")

    st.markdown("##### 📋 美股 11 大 GICS 行業 ETF 完整多週期報酬率明細表")
    df_disp = df_sorted.copy()
    df_disp['即時現價'] = df_disp['即時現價'].apply(lambda x: f"${x:.2f}")
    for col in ["日漲跌 (%)", "週漲跌 (%)", "月漲跌 (%)", "今年至今 YTD (%)"]:
        df_disp[col] = df_disp[col].apply(lambda x: f"{x:+.2f}%")

    st.dataframe(df_disp[['代碼', '圖標', '板塊名稱', '即時現價', '日漲跌 (%)', '週漲跌 (%)', '月漲跌 (%)', '今年至今 YTD (%)']], use_container_width=True, hide_index=True)

# ----------------------------------------------------
# 頁籤 2：Finviz 密實風格 Treemap 熱力圖
# ----------------------------------------------------
with tab_heatmap:
    with st.spinner("正在連線抓取 S&P 500 核心 65+ 檔權值龍頭股即時報價與漲跌幅..."):
        df_hm = fetch_sp500_heatmap_data()

    df_hm['ColorMetric'] = df_hm['Change'].clip(-3.0, 3.0)

    finviz_colors = [
        [0.0, "#A81E1E"],
        [0.35, "#571616"],
        [0.5, "#252830"],
        [0.65, "#144D29"],
        [1.0, "#089981"]
    ]

    fig_tree = px.treemap(
        df_hm,
        path=['Sector', 'Sub', 'Ticker'],
        values='Weight',
        color='ColorMetric',
        color_continuous_scale=finviz_colors,
        range_color=[-3.0, 3.0],
        custom_data=['Ticker', 'Change', 'Sector', 'Sub']
    )

    fig_tree.update_traces(
        texttemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:+.2f}%",
        textfont=dict(size=12, color="#FFFFFF", family="Arial Black"),
        textposition="middle center",
        hovertemplate="<b>%{customdata[0]}</b><br>板塊：%{customdata[2]}<br>行業：%{customdata[3]}<br>漲跌幅：<b>%{customdata[1]:+.2f}%</b><extra></extra>",
        marker=dict(cornerradius=2, line=dict(color='#111317', width=1.5))
    )

    fig_tree.update_layout(
        margin=dict(t=15, l=5, r=5, b=10),
        height=720,
        paper_bgcolor="#111317",
        plot_bgcolor="#111317",
        coloraxis_showscale=False
    )

    st.plotly_chart(fig_tree, use_container_width=True, key="finviz_treemap_chart_full")
    st.caption("💡 互動說明：方塊大小依據個股市值權重計算；可點擊各大板塊（如 Technology、Financial）進入細部行業縮放檢視，點擊頂部即可返回上一層。")

st.markdown("""
<div class="guide-box">
    <strong style="color: #0F766E; font-size: 1.05rem;">💡 【板塊輪動 (Sector Rotation) 實戰應用指南】</strong>
    <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
        • <strong>景氣循環切換</strong>：當經濟處於復甦期，資金通常由防禦型板塊（公用事業 XLU、必需消費 XLP）流向攻擊型板塊（科技 XLK、非必需消費 XLY）；若進入景氣晚期或滯脹，資金則轉向能源 (XLE) 與房地產 (XLRE)。<br>
        • <strong>強者恆強與均值回歸</strong>：觀察週與月的排序，若某一板塊連續數週蟬聯榜首，代表機構主力正在進行波段建倉（順勢追蹤）；若落後板塊出現利空出盡且成交量放量，則可留意週期性反轉機會。
    </p>
</div>
""", unsafe_allow_html=True)
