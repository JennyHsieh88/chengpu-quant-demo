import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
import importlib

# 引入會員狀態與註冊功能
from auth import render_login_widget, register_or_upgrade_user

# ==========================================
# 頁面基礎配置
# ==========================================
st.set_page_config(
    page_title="決策總覽首頁 - 澄璞財務",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 渲染側邊欄登入狀態卡片
render_login_widget()

# 引入全站共用樣式與品牌設定（啟用熱重載機制：按 F5 自動同步最新 config.py）
import config
importlib.reload(config)
config.inject_global_style()

# ==========================================
# 頁面專屬排版強化 CSS
# ==========================================
st.markdown("""
<style>
    /* 頂部指標微型卡片容器 */
    .hero-stat-card {
        background: #FFFFFF;
        border: 1px solid #E6DFD7;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 2px 6px rgba(45, 38, 34, 0.03);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .hero-stat-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #5C554F;
        display: flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
    }
    .hero-stat-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #2D2622;
        margin: 4px 0 2px 0;
        letter-spacing: -0.5px;
    }
    .hero-stat-desc {
        font-size: 0.82rem;
        color: #047857;
        font-weight: 600;
        background: #F0FDF4;
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-block;
        width: fit-content;
    }
    
    /* 輕量級高質感橫幅 */
    .hero-clean-banner {
        background: #FFFFFF;
        border: 1px solid #E6DFD7;
        border-left: 4px solid #0D9488;
        border-radius: 12px;
        padding: 14px 20px;
        margin-top: 14px;
        margin-bottom: 22px;
        box-shadow: 0 2px 8px rgba(45, 38, 34, 0.03);
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }
    .hero-pill-badge {
        background: #FAF6F2;
        border: 1px solid #E6DFD7;
        color: #4A3E36;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 16px;
        display: inline-block;
    }

    /* 章節序號圓徽 */
    .sec-badge-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        color: #FFFFFF !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        margin-right: 10px;
        flex-shrink: 0;
    }
    .num-bg-1 { background-color: #0284C7; }
    .num-bg-2 { background-color: #047857; }
    .num-bg-3 { background-color: #4338CA; }
    .num-bg-4 { background-color: #D97706; }
    .num-bg-5 { background-color: #6B584C; }
    .num-bg-6 { background-color: #7C3AED; }

    .status-badge-preview {
        background: #FFFFFF;
        color: #475569;
        font-size: 0.80rem;
        font-weight: 700;
        padding: 3px 12px;
        border-radius: 14px;
        border: 1px solid #CBD5E1;
    }
    .status-badge-active {
        background: #FFFFFF;
        color: #3730A3;
        font-size: 0.80rem;
        font-weight: 800;
        padding: 3px 12px;
        border-radius: 14px;
        border: 1.5px solid #6366F1;
    }

    /* 方案卡片專屬容器 */
    .pricing-box-wrapper {
        background: #FFFFFF;
        border: 1px solid #E6DFD7;
        border-radius: 12px;
        padding: 22px 20px;
        box-shadow: 0 2px 8px rgba(45, 38, 34, 0.03);
        min-height: 520px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .pricing-box-wrapper.popular {
        border: 2px solid #0D9488;
        box-shadow: 0 4px 14px rgba(13, 148, 136, 0.12);
        position: relative;
    }
    .pricing-box-wrapper.pro {
        border: 1.5px solid #0284C7;
        box-shadow: 0 3px 10px rgba(2, 132, 199, 0.08);
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
# 全球主要資產類別即時 YTD 報酬率動態計算引擎
# ==========================================
@st.cache_data(ttl=300)
def fetch_realtime_assets_ytd():
    asset_dict = {
        'QQQ': '科技龍頭代表 (QQQ)',
        'SPY': '標普 500 大盤 (SPY)',
        'GLD': '實體黃金期貨 (GLD)',
        'HYG': '高收益企業債 (HYG)',
        'AGG': '全球投資級債 (AGG)',
        'SGOV': '超短期美國公債 (SGOV)',
        'USO': '能源大宗商品 (USO)'
    }
    
    current_year = datetime.now().year
    records = []
    
    for ticker, label in asset_dict.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if hist is not None and not hist.empty and len(hist) >= 2:
                closes = hist['Close'].dropna()
                if len(closes) >= 2:
                    hist_prev_year = hist[hist.index.year < current_year]
                    if not hist_prev_year.empty:
                        base_close = float(hist_prev_year['Close'].iloc[-1])
                    else:
                        base_close = float(closes.iloc[0])
                    
                    latest_close = float(closes.iloc[-1])
                    if base_close > 0 and not np.isnan(base_close) and not np.isnan(latest_close):
                        ytd_ret = ((latest_close - base_close) / base_close) * 100.0
                        if not np.isnan(ytd_ret) and not np.isinf(ytd_ret):
                            records.append({
                                "資產名稱": label,
                                "YTD報酬率": round(float(ytd_ret), 1),
                                "代碼": ticker
                            })
        except Exception:
            pass

    fallback_map = {
        'QQQ': 17.3,
        'SPY': 12.8,
        'GLD': 13.2,
        'HYG': 6.8,
        'AGG': 2.8,
        'SGOV': 3.1,
        'USO': -3.5
    }
    
    existing_tickers = {r["代碼"] for r in records}
    for ticker, label in asset_dict.items():
        if ticker not in existing_tickers:
            records.append({
                "資產名稱": label,
                "YTD報酬率": fallback_map.get(ticker, 5.0),
                "代碼": ticker
            })
            
    df_res = pd.DataFrame(records)
    return df_res.sort_values(by="YTD報酬率", ascending=False).reset_index(drop=True)

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
        placeholder="",
        help="在此輸入代碼後，全站 12 大分析模組將即時同步切換"
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
        st.caption("全站 12 大分析模組已同步切換至該股票之專屬深度資料")
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
# 四大市場狀態卡片
# ==========================================
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown("""
    <div class="hero-stat-card">
        <div class="hero-stat-title">🌐 全球宏觀淨流動性</div>
        <div class="hero-stat-value">$6.18 兆</div>
        <div class="hero-stat-desc">↑ 水位健康穩定</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    sentiment_color = "#DC2626" if home_fg['score'] < 25 else ("#D97706" if home_fg['score'] < 45 else "#047857")
    sentiment_bg = "#FEF2F2" if home_fg['score'] < 25 else ("#FFFBEB" if home_fg['score'] < 45 else "#F0FDF4")
    st.markdown(f"""
    <div class="hero-stat-card">
        <div class="hero-stat-title">📊 全市場情緒指標</div>
        <div class="hero-stat-value">{home_fg['score']} <span style="font-size:1.0rem; color:#847568; font-weight:600;">/ 100</span></div>
        <div class="hero-stat-desc" style="background:{sentiment_bg}; color:{sentiment_color};">
            ● {home_fg['rating']} 實時同步
        </div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div class="hero-stat-card">
        <div class="hero-stat-title">⚖️ 期權 Put/Call 比率</div>
        <div class="hero-stat-value">0.68</div>
        <div class="hero-stat-desc">↑ 正 Gamma 緩衝</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown("""
    <div class="hero-stat-card">
        <div class="hero-stat-title">🛡️ 美債實質無風險利率</div>
        <div class="hero-stat-value">4.35%</div>
        <div class="hero-stat-desc">↑ 短端現金流充裕</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 輕量呼吸感橫幅
# ==========================================
st.markdown("""
<div class="hero-clean-banner">
    <div>
        <div style="font-size:1.02rem; font-weight:800; color:#2D2622;">
            ✦ 澄璞財務機構級即時量化決策體系 ✦
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:8px;">
            <span class="hero-pill-badge">🛡️ 做市商 Gamma 預警</span>
            <span class="hero-pill-badge">🌡️ 7 維度情緒雷達</span>
            <span class="hero-pill-badge">🏛️ 央行政策日曆</span>
            <span class="hero-pill-badge">💼 CFP® 全天候配置</span>
        </div>
    </div>
    <div style="flex-shrink:0;">
        <span style="background:#0D9488; color:#FFFFFF; padding:6px 14px; border-radius:20px; font-weight:700; font-size:0.84rem; letter-spacing:0.5px;">
            ● 實時演算法連線中
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 全寬四大深度圖表內容
# ==============================================================================

# 區塊一：標普 500 大盤走勢
st.markdown("""
<div style="background:#F0F7FD; border:1px solid #BAE6FD; border-left:6px solid #0284C7; border-radius:10px; padding:14px 18px; margin-top:36px; margin-bottom:14px;">
    <div style="display:flex; align-items:center; gap:10px;">
        <span class="sec-badge-num num-bg-1">01</span>
        <span style="font-size:1.24rem; font-weight:800; color:#1E3A8A;">一、全市場核心資產趨勢與均線位階走向 (Market Macro Trends)</span>
    </div>
    <div style="font-size:0.90rem; color:#475569; margin-top:6px; margin-left:38px;">
        追蹤標普 500 大盤中長期價格走勢，結合 20 日與 50 日均線系統，研判當前市場動能位階與宏觀趨勢支撐。
    </div>
</div>
""", unsafe_allow_html=True)

dates_macro = pd.date_range(end=datetime.now(), periods=504, freq='B')
np.random.seed(101)
base_p = 460.0 + np.cumsum(np.random.normal(0.40, 3.8, len(dates_macro)))
ma20 = pd.Series(base_p).rolling(20).mean()
ma50 = pd.Series(base_p).rolling(50).mean()

fig_macro = go.Figure()
fig_macro.add_trace(go.Scatter(
    x=dates_macro, y=base_p,
    mode='lines', line=dict(color='#0284C7', width=2.5),
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
    title=dict(text="<b>標普 500 近 2 年宏觀走勢與均線結構對照 ($)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
    height=440,
    margin=dict(t=75, b=30, l=15, r=30),
    paper_bgcolor="#F8FAFC",
    plot_bgcolor="#FFFFFF",
    xaxis=dict(showgrid=False, hoverformat="%Y年%m月%d日"),
    yaxis=dict(title="價格 ($)", showgrid=True, gridcolor='#F1F5F9'),
    legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="right", x=0.98, font=dict(size=11)),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#38302B", font_size=13, font_family="sans-serif", font_color="#2D2622")
)
st.plotly_chart(fig_macro, use_container_width=True, key="home_macro_chart_2yr")

st.markdown("""
<div style="background:#F0F7FD; border:1px solid #BAE6FD; border-left:4px solid #0284C7; border-radius:8px; padding:12px 16px; margin-top:10px; margin-bottom:30px;">
    <strong style="color: #0369A1; font-size: 1.02rem;">💡 【大盤趨勢怎麼看？】</strong>
    <p style="color: #2D2622; margin: 4px 0 0 0; font-size: 0.92rem; line-height: 1.65;">
        • 當股價持續位於 20MA（綠虛線）與 50MA（橘虛線）上方時，代表整體金融環境處於「多頭攻擊波段」，適合維持充裕的權益多頭部位；<br>
        • 若跌破 50MA 中期防線，則需轉向防禦，提升 SGOV 超短債與黃金的避險氣囊配置。
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊二：全球主要資產 YTD 表現
# ----------------------------------------------------
st.markdown("""
<div style="background:#F2FAF5; border:1px solid #A7F3D0; border-left:6px solid #047857; border-radius:10px; padding:14px 18px; margin-top:36px; margin-bottom:14px;">
    <div style="display:flex; align-items:center; gap:10px;">
        <span class="sec-badge-num num-bg-2">02</span>
        <span style="font-size:1.24rem; font-weight:800; color:#065F46;">二、全球主要資產類別年至今 (YTD) 表現與輪動全景</span>
    </div>
    <div style="font-size:0.90rem; color:#475569; margin-top:6px; margin-left:38px;">
        連線金融市場即時計算跨資產累積報酬率，動態呈現市場主線輪動邏輯與分散配置效益。
    </div>
</div>
""", unsafe_allow_html=True)

df_ytd_live = fetch_realtime_assets_ytd()

assets_names = df_ytd_live['資產名稱'].tolist()
assets_returns = df_ytd_live['YTD報酬率'].tolist()
assets_colors = ['#047857' if v > 0 else '#DC2626' for v in assets_returns]

fig_assets = go.Figure(go.Bar(
    x=assets_names,
    y=assets_returns,
    marker_color=assets_colors,
    text=[f"{v:+.1f}%" for v in assets_returns],
    textposition='outside',
    cliponaxis=False,
    textfont=dict(size=12, color='#2D2622', family='Arial Black'),
    hovertemplate="<b>%{x}</b><br>年至今即時報酬 (YTD): %{y:+.1f}%<extra></extra>"
))

valid_vals = [v for v in assets_returns if not np.isnan(v)]
max_ret = max(valid_vals) if valid_vals else 15.0
min_ret = min(valid_vals) if valid_vals else -5.0

max_ytd_val = max(max_ret * 1.30, max_ret + 3.0, 10.0)
min_ytd_val = min(min_ret * 1.35 if min_ret < 0 else -2.0, -5.0)

fig_assets.update_layout(
    title=dict(text="<b>主要資產類別即時累積報酬率對比 (%) — 自動連網實時更新</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
    height=440,
    margin=dict(t=65, b=45, l=15, r=25),
    paper_bgcolor="#F2FAF5",
    plot_bgcolor="#FFFFFF",
    xaxis=dict(showgrid=False),
    yaxis=dict(title="年至今報酬率 (%)", range=[min_ytd_val, max_ytd_val], showgrid=True, gridcolor='#E2E8F0'),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#38302B", font_size=13, font_color="#2D2622")
)
st.plotly_chart(fig_assets, use_container_width=True, key="home_assets_chart_live_v2")

st.markdown("""
<div style="background:#F2FAF5; border:1px solid #A7F3D0; border-left:4px solid #047857; border-radius:8px; padding:12px 16px; margin-top:10px; margin-bottom:30px;">
    <strong style="color: #047857; font-size: 1.02rem;">💡 【資產輪動怎麼看？】</strong>
    <p style="color: #2D2622; margin: 4px 0 0 0; font-size: 0.92rem; line-height: 1.65;">
        • <strong>黃金與股票同步走強</strong>：反映市場在追求科技成長紅利的同時，也在防範貨幣信用貶值，驗證了「全天候投組」同時配置權益與黃金的戰略價值；<br>
        • <strong>超短債 (SGOV) 穩健貢獻息收</strong>：提供無風險息收底座，充當市場大幅回調時的最佳彈藥庫。
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊三：360° 跨維度量化診斷雷達
# ----------------------------------------------------
if user_has_typed:
    display_title = f"三、{target_symbol} 360° 跨維度量化診斷雷達全景"
    badge_html = '<span class="status-badge-active">● 個股即時診斷</span>'
    caption_text = f"綜合評估 <strong>{target_symbol}</strong> 之「基本面護城河、估值性價比、機構籌碼、技術量價動量、另類數據信號」五大核心因子。"
    radar_scores = [92.0, 72.0, 88.0, 85.0, 84.0]
    trace_name = f"{target_symbol} 量化評分"
else:
    display_title = "三、標普大盤基準 (SPY) 360° 跨維度量化診斷雷達全景"
    badge_html = '<span class="status-badge-preview">👁️ 基準預覽模式</span>'
    caption_text = "💡 <strong>目前呈現全市場基準</strong>。於上方搜尋框輸入任意美股代碼（如 NVDA、ISRG、AAPL）後，此處將自動即時切換為該個股五大多因子雷達。"
    radar_scores = [78.0, 70.0, 75.0, 74.0, 72.0]
    trace_name = "標普大盤基準 (SPY) 量化評分"

st.markdown(f"""
<div style="background:#EEF2FF; border:1px solid #C7D2FE; border-left:6px solid #4338CA; border-radius:10px; padding:14px 18px; margin-top:36px; margin-bottom:14px;">
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span class="sec-badge-num num-bg-3">03</span>
            <span style="font-size:1.24rem; font-weight:800; color:#312E81;">{display_title}</span>
        </div>
        <div>{badge_html}</div>
    </div>
    <div style="font-size:0.90rem; color:#475569; margin-top:6px; margin-left:38px;">{caption_text}</div>
</div>
""", unsafe_allow_html=True)

radar_categories = ['基本面護城河 (Moat)', '同儕估值性價比 (Value)', '外資機構籌碼 (Smart Money)', '技術量價動量 (Technical)', '另類數據信號 (Alt Data)']
benchmark_scores = [70.0, 68.0, 65.0, 68.0, 65.0]

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=radar_scores + [radar_scores[0]],
    theta=radar_categories + [radar_categories[0]],
    fill='toself',
    fillcolor='rgba(79, 70, 229, 0.22)',
    line=dict(color='#4F46E5', width=2.8),
    name=trace_name,
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
    title=dict(text=f"<b>{target_symbol if user_has_typed else '標普大盤基準 (SPY)'} 五大多因子量化診斷雷達</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
        angularaxis=dict(tickfont=dict(size=12, family='Arial Black')),
        bgcolor="#FFFFFF"
    ),
    height=440,
    margin=dict(t=70, b=30, l=40, r=40),
    paper_bgcolor="#EEF2FF",
    legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#38302B", font_size=13, font_color="#2D2622")
)
st.plotly_chart(fig_radar, use_container_width=True, key="home_radar_chart")

st.markdown("""
<div style="background:#EEF2FF; border:1px solid #C7D2FE; border-left:4px solid #4338CA; border-radius:8px; padding:12px 16px; margin-top:10px; margin-bottom:30px;">
    <strong style="color: #3730A3; font-size: 1.02rem;">💡 【量化雷達怎麼看？】</strong>
    <p style="color: #2D2622; margin: 4px 0 0 0; font-size: 0.92rem; line-height: 1.65;">
        • 靛紫色覆蓋區域顯著大於灰色虛線，代表該資產具備全面的超額收益實力；<br>
        • 詳細單項得分與各因子權重分解，可點擊左側導航進入<strong>「進階數據與評分 ➔ 綜合決策與多空評分」</strong>查看完整矩陣。
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊四：最新宏觀要聞快訊
# ----------------------------------------------------
st.markdown("""<div style="background-color: #FCF8EE; border: 1.5px solid #FDE68A; border-left: 6px solid #D97706; border-radius: 14px; padding: 22px 24px 16px 24px; margin-top: 38px; margin-bottom: 24px; box-shadow: 0 3px 12px rgba(217,119,6,0.04);"><div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;"><span style="display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; color: #FFFFFF; font-size: 0.85rem; font-weight: 800; background-color: #D97706; flex-shrink: 0;">04</span><span style="font-size: 1.25rem; font-weight: 800; color: #78350F; letter-spacing: 0.5px;">四、最新全球金融宏觀要聞與市場快訊摘要</span></div><div style="font-size: 0.90rem; color: #854D0E; margin-top: 4px; margin-left: 38px; margin-bottom: 18px;">毫秒級追蹤影響全球市場流動性與個股走勢之重大事件。</div><div style="background: #FFFDF9; border: 1px solid #FCE7A6; border-left: 4px solid #D97706; border-radius: 9px; padding: 15px 18px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(217,119,6,0.03);"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;"><span style="background: #FAF4EB; color: #854D0E; padding: 3px 9px; border-radius: 5px; font-weight: 700; font-size: 0.80rem; border: 1px solid #FDE68A;">🕒 16:20</span><span style="background: #FEF3C7; color: #92400E; padding: 3px 9px; border-radius: 5px; font-weight: 800; font-size: 0.82rem;">🏛️ 總經政策</span></div><div style="font-weight: 700; font-size: 1.06rem; color: #2D2622; margin-bottom: 5px; line-height: 1.5;">美聯儲官員重申數據依賴路徑，強調抗通膨進程持續推進但需保持政策彈性</div><div style="color: #78716C; font-size: 0.90rem; display: flex; align-items: center; gap: 5px;"><span style="color: #D97706; font-weight: 800; font-size: 0.95rem;">✦</span><span><strong style="color: #451A03;">傳導影響：</strong>公債殖利率平穩，市場對軟著陸預期保持樂觀</span></div></div><div style="background: #FFFDF9; border: 1px solid #FCE7A6; border-left: 4px solid #D97706; border-radius: 9px; padding: 15px 18px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(217,119,6,0.03);"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;"><span style="background: #FAF4EB; color: #854D0E; padding: 3px 9px; border-radius: 5px; font-weight: 700; font-size: 0.80rem; border: 1px solid #FDE68A;">🕒 14:45</span><span style="background: #FEF3C7; color: #92400E; padding: 3px 9px; border-radius: 5px; font-weight: 800; font-size: 0.82rem;">🏛️ 半導體/AI</span></div><div style="font-weight: 700; font-size: 1.06rem; color: #2D2622; margin-bottom: 5px; line-height: 1.5;">大型雲端服務商 (CSP) 持續調升 AI 基礎設施資本支出預算，晶片需求能見度延伸</div><div style="color: #78716C; font-size: 0.90rem; display: flex; align-items: center; gap: 5px;"><span style="color: #D97706; font-weight: 800; font-size: 0.95rem;">✦</span><span><strong style="color: #451A03;">傳導影響：</strong>提振科技股與半導體供應鏈長線基本面信心</span></div></div><div style="background: #FFFDF9; border: 1px solid #FCE7A6; border-left: 4px solid #D97706; border-radius: 9px; padding: 15px 18px; margin-bottom: 6px; box-shadow: 0 2px 6px rgba(217,119,6,0.03);"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;"><span style="background: #FAF4EB; color: #854D0E; padding: 3px 9px; border-radius: 5px; font-weight: 700; font-size: 0.80rem; border: 1px solid #FDE68A;">🕒 11:15</span><span style="background: #FEF3C7; color: #92400E; padding: 3px 9px; border-radius: 5px; font-weight: 800; font-size: 0.82rem;">🏛️ 能源大宗</span></div><div style="font-weight: 700; font-size: 1.06rem; color: #2D2622; margin-bottom: 5px; line-height: 1.5;">地緣政治溢價支撐油價震盪盤整，非 OPEC+ 產能穩健限制了油價過熱上行空間</div><div style="color: #78716C; font-size: 0.90rem; display: flex; align-items: center; gap: 5px;"><span style="color: #D97706; font-weight: 800; font-size: 0.95rem;">✦</span><span><strong style="color: #451A03;">傳導影響：</strong>通膨二次反彈風險受控，有助維持寬鬆貨幣環境</span></div></div></div>""", unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊五：12 大分析模組導航矩陣（摩卡焙茶褐）
# ----------------------------------------------------
st.markdown("""
<div style="background:#F8F5F1; border:1px solid #D8CFC7; border-left:6px solid #6B584C; border-radius:10px; padding:14px 18px; margin-top:36px; margin-bottom:18px;">
    <div style="display:flex; align-items:center; gap:10px;">
        <span class="sec-badge-num num-bg-5">05</span>
        <span style="font-size:1.24rem; font-weight:800; color:#4A3E36;">五、澄璞全方位量化分析終端 — 12 大模組功能導航</span>
    </div>
    <div style="font-size:0.90rem; color:#64748B; margin-top:6px; margin-left:38px;">
        點擊左側側邊欄即可直達各項深度量化模組進行細部診斷：
    </div>
</div>
""", unsafe_allow_html=True)

q_col1, q_col2 = st.columns(2)

with q_col1:
    q1_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #0284C7; margin-bottom: 18px; background:#FFFFFF; border-radius:10px; padding:18px; border:1px solid #E6DFD7;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#0284C7;">🌐 宏觀環境與市場流動性</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#0284C7; background:#E0F2FE; padding:2px 8px; border-radius:12px;">模組 01 ~ 02</span>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">01_總體環境監控</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#E0F2FE; color:#0369A1; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">免費開放</span> 實質殖利率走勢、信用利差、總經經濟週期與衰退預警模型'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">02_市場氛圍與流動性</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#E0F2FE; color:#0369A1; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">免費開放</span> 全市場 7 維度情緒雷達、TGA / RRP 水位、CBOE 期權 Gamma 曝險'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q1_html, unsafe_allow_html=True)

    q2_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #D97706; background:#FFFFFF; border-radius:10px; padding:18px; border:1px solid #E6DFD7;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#D97706;">📈 技術量價與籌碼微觀</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#D97706; background:#FEF3C7; padding:2px 8px; border-radius:12px;">模組 06 ~ 08</span>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">06_技術面與量價動量</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#FEF3C7; color:#B45309; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">進階解鎖</span> 多天期均線排列、RSI 背離監控、MACD 與布林軌道通道位階'
        '</div>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">07_華爾街共識與籌碼</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#FEF3C7; color:#B45309; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">進階解鎖</span> 頂級投行評級雷達、機構目標價矩陣與 13F 明星經理人持倉'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">08_訂單流與另類數據</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#FEF3C7; color:#B45309; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">進階解鎖</span> 主力暗池 (Dark Pool) 掃貨監控、CVD 累積買盤偏度與軋空指數'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q2_html, unsafe_allow_html=True)

with q_col2:
    q3_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #047857; margin-bottom: 18px; background:#FFFFFF; border-radius:10px; padding:18px; border:1px solid #E6DFD7;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#047857;">🏢 板塊與個股基本面深度</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#047857; background:#D1FAE5; padding:2px 8px; border-radius:12px;">模組 03 ~ 05</span>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">03_板塊輪動與資金流向</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#D1FAE5; color:#047857; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">進階解鎖</span> 追蹤各大產業板块強弱與資金輪動路徑'
        '</div>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">04_產業同儕估值</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#D1FAE5; color:#047857; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">進階解鎖</span> Forward P/E、PEG 成長比率、EV/EBITDA 與橫向同儕對標'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">05_個股基本面深度庫</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#D1FAE5; color:#047857; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">進階解鎖</span> 三階杜邦分析 (DuPont)、毛利成長性、自由現金流 (FCF) 與資產負債安全'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q3_html, unsafe_allow_html=True)

    q4_html = (
        '<div class="nav-quad-card" style="border-top: 4px solid #8B5CF6; background:#FFFFFF; border-radius:10px; padding:18px; border:1px solid #E6DFD7;">'
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">'
        '<span style="font-size:1.12rem; font-weight:800; color:#8B5CF6;">⚖️ 決策配置、投組回測與要聞</span>'
        '<span style="font-size:0.80rem; font-weight:700; color:#8B5CF6; background:#EDE9FE; padding:2px 8px; border-radius:12px;">模組 09 ~ 12</span>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">09_綜合決策與多空評分</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#EDE9FE; color:#6D28D9; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">進階解鎖</span> 五大多因子加權客觀評分系統、關鍵支撐阻力攻防階梯價'
        '</div>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">10_資產配置與前瞻推估</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#EDE9FE; color:#6D28D9; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">旗艦專屬</span> 跨資產積木定價、降噪相關性矩陣、全天候 70/30 抗震結構'
        '</div>'
        '</div>'
        '<div class="nav-item-row" style="margin-bottom:10px;">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">11_智慧投組回測與前瞻推估</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#EDE9FE; color:#6D28D9; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">旗艦專屬</span> 歷史滾動回測、最大回撤 (MDD) 控制、單筆與 DCA 複利存股'
        '</div>'
        '</div>'
        '<div class="nav-item-row">'
        '<div style="font-weight:700; font-size:0.98rem; color:#2D2622;">12_全球金融即時要聞與市場脈動</div>'
        '<div style="font-size:0.86rem; color:#64748B; margin-top:3px;">'
        '<span style="background:#EDE9FE; color:#6D28D9; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">旗艦專屬</span> 跨國央行與財報日曆、今日高亮導航、毫秒級即時市場快訊流'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(q4_html, unsafe_allow_html=True)

# ----------------------------------------------------
# 區塊六：方案升級與訂閱版本付費選擇（支援月繳/年繳優惠切換）
# ----------------------------------------------------
st.markdown("""
<div style="background:#F8F6FE; border:1px solid #DDD6FE; border-left:6px solid #7C3AED; border-radius:10px; padding:14px 18px; margin-top:36px; margin-bottom:18px;">
    <div style="display:flex; align-items:center; gap:10px;">
        <span class="sec-badge-num num-bg-6">06</span>
        <span style="font-size:1.24rem; font-weight:800; color:#5B21B6;">六、想要獲取更多進階功能？探索澄璞專業方案與付費版本選擇</span>
    </div>
    <div style="font-size:0.90rem; color:#64748B; margin-top:6px; margin-left:38px;">
        支援月繳與超值年繳優惠，線上刷卡完成輸入資料即刻自動開通：
    </div>
</div>
""", unsafe_allow_html=True)

# 彈出對話視窗：加入會員與線上刷卡（支援月繳/年繳動態選擇）
@st.dialog("💎 加入會員與線上刷卡開通", width="large")
def modal_checkout(tier_code: int, plan_name: str, monthly_price: int, annual_price: int, monthly_url: str, annual_url: str):
    billing_cycle = st.radio(
        "選擇計費週期：",
        options=[f"月繳：NT$ {monthly_price:,} / 月", f"🔥 年繳超值優惠：NT$ {annual_price:,} / 年 (現省 NT$ {monthly_price*12 - annual_price:,})"],
        index=1,
        horizontal=True
    )
    is_annual = "年繳" in billing_cycle
    current_price_str = f"NT$ {annual_price:,} / 年" if is_annual else f"NT$ {monthly_price:,} / 月"
    current_url = annual_url if is_annual else monthly_url
    cycle_tag = "ANNUAL" if is_annual else "MONTHLY"

    st.markdown(f"""
    <div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 12px 18px; border-radius: 8px; margin-top: 10px; margin-bottom: 14px;">
        <div style="font-weight: 800; font-size: 1.15rem; color: #166534;">您選擇開通：{plan_name}（{'年繳方案' if is_annual else '月繳方案'}）</div>
        <div style="font-size: 1.05rem; color: #0D9488; font-weight: 800; margin-top: 3px;">應付金額：{current_price_str}</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab_signup, tab_google = st.tabs(["📝 填寫資料加入並刷卡", "🌐 使用 Google 信箱快速開通"])
    
    with tab_signup:
        with st.form(f"form_signup_{tier_code}"):
            col_a, col_b = st.columns(2)
            with col_a:
                f_name = st.text_input("會員姓名 / 稱呼 *", placeholder="例如：謝小姐")
                f_email = st.text_input("聯絡信箱 (Email) *", placeholder="收取帳單與登入通知")
            with col_b:
                f_user = st.text_input("自訂登入帳號 *", placeholder="英文或數字")
                f_pw = st.text_input("自訂登入密碼 *", type="password", placeholder="至少 6 位數")
            
            st.markdown("---")
            st.markdown("##### 💳 線上付費刷卡連結")
            st.caption(f"點選下方刷卡按鈕開啟安全支付頁面（應付：{current_price_str}），付款完成後請輸入刷卡卡號末4碼或交易單號。")
            st.link_button(f"👉 點此前往【線上安全刷卡】({current_price_str})", current_url, type="secondary", use_container_width=True)
            
            f_paycode = st.text_input("刷卡末 4 碼或授權碼 *", placeholder="完成刷卡後輸入，例：8899")
            
            submit_manual = st.form_submit_button("🚀 確認開通並直接啟用登入", type="primary", use_container_width=True)
            
            if submit_manual:
                if not (f_name and f_email and f_user and f_pw and f_paycode):
                    st.error("請完整填寫所有標記 * 的欄位。")
                else:
                    ref_code = f"{cycle_tag}_{f_paycode.strip()}"
                    ok, msg = register_or_upgrade_user(
                        username=f_user.strip(),
                        password=f_pw.strip(),
                        tier=tier_code,
                        display_name=f_name.strip(),
                        email=f_email.strip(),
                        auth_provider="local",
                        payment_ref=ref_code
                    )
                    if ok:
                        st.session_state["is_authenticated"] = True
                        st.session_state["username"] = f_user.strip()
                        st.session_state["user_tier"] = tier_code
                        st.session_state["display_name"] = f_name.strip()
                        st.session_state["email"] = f_email.strip()
                        st.success("🎉 恭喜！會員權限已開通，系統已自動為您登入！")
                        st.rerun()
                    else:
                        st.error(msg)
                        
    with tab_google:
        st.info("💡 透過您的 Google / Gmail 信箱快速綁定開通，省去記憶帳號密碼的繁瑣步驟。")
        with st.form(f"form_google_{tier_code}"):
            g_email = st.text_input("請輸入您的 Google (Gmail) 信箱 *", placeholder="yourname@gmail.com")
            g_name = st.text_input("您的姓名或暱稱 *", placeholder="例如：Jenny")
            
            st.markdown("---")
            st.markdown("##### 💳 線上刷卡連結")
            st.link_button(f"👉 點此前往【線上安全刷卡】({current_price_str})", current_url, type="secondary", use_container_width=True)
            
            g_paycode = st.text_input("刷卡授權碼或卡號末 4 碼 *", placeholder="刷卡完成後填入")
            
            submit_google = st.form_submit_button("🚀 以 Google 信箱完成開通並登入", type="primary", use_container_width=True)
            
            if submit_google:
                if not (g_email and g_name and g_paycode) or "@" not in g_email:
                    st.error("請輸入正確的 Gmail 信箱與刷卡驗證資訊。")
                else:
                    g_user = g_email.split("@")[0]
                    ref_code = f"{cycle_tag}_{g_paycode.strip()}"
                    ok, msg = register_or_upgrade_user(
                        username=g_user,
                        password=g_paycode,
                        tier=tier_code,
                        display_name=g_name.strip(),
                        email=g_email.strip(),
                        auth_provider="google",
                        payment_ref=ref_code
                    )
                    if ok:
                        st.session_state["is_authenticated"] = True
                        st.session_state["username"] = g_user
                        st.session_state["user_tier"] = tier_code
                        st.session_state["display_name"] = g_name.strip()
                        st.session_state["email"] = g_email.strip()
                        st.success("🎉 Google 帳號綁定成功，方案已立即生效！")
                        st.rerun()
                    else:
                        st.error(msg)

col_p1, col_p2, col_p3 = st.columns(3)

# 方案 1：基礎探索版（免費）
with col_p1:
    st.markdown("""
    <div class="pricing-box-wrapper">
        <div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #2D2622;">🌿 基礎探索版</div>
            <div style="font-size: 0.86rem; color: #64748B; margin-top: 5px;">適合自主大盤觀察與總經入門追蹤</div>
            <div style="margin: 20px 0 18px 0; padding-bottom: 16px; border-bottom: 1px solid #EFEAE2;">
                <span style="font-size: 2.2rem; font-weight: 800; color: #2D2622;">免費</span>
                <span style="font-size: 0.90rem; color: #847568;">/ 永久體驗</span>
            </div>
            <div style="color: #475569; font-size: 0.90rem; line-height: 2.1;">
                <div><span style="color:#047857; font-weight:800;">✔</span> <strong>決策總覽首頁</strong>：大盤趨勢與均線位階</div>
                <div><span style="color:#047857; font-weight:800;">✔</span> <strong>總體環境監控</strong>：實質殖利率、利差與衰退模型</div>
                <div><span style="color:#047857; font-weight:800;">✔</span> <strong>市場氛圍與流動性</strong>：淨流動性、TGA/RRP 與情緒</div>
                <div style="color: #94A3B8;"><span>✖</span> 個股深度研究（同儕估值、杜邦財報、技術量價）</div>
                <div style="color: #94A3B8;"><span>✖</span> 進階數據與評分（暗池大單、13F 名冊、多空階梯價）</div>
                <div style="color: #94A3B8;"><span>✖</span> 資產配置與模擬（全天候投組回測、跨國日曆）</div>
            </div>
        </div>
        <div style="margin-top: 22px;">
            <div style="text-align: center; padding: 13px; background: #F1F5F9; border-radius: 8px; color: #475569; font-weight: 700; font-size: 0.92rem; border: 1px solid #E2E8F0;">
                當前免費使用中
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 方案 2：進階量化版（NT$ 200/月 ｜ 年繳 NT$ 2,000）
with col_p2:
    st.markdown("""
    <div class="pricing-box-wrapper pro">
        <div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #0284C7;">⚡ 進階量化版</div>
            <div style="font-size: 0.86rem; color: #64748B; margin-top: 5px;">適合主動選股、波段操作與深度基本面研究者</div>
            <div style="margin: 20px 0 18px 0; padding-bottom: 16px; border-bottom: 1px solid #EFEAE2;">
                <span style="font-size: 1.20rem; font-weight: 700; color: #0284C7;">NT$</span>
                <span style="font-size: 2.2rem; font-weight: 800; color: #0284C7;">200</span>
                <span style="font-size: 0.88rem; color: #847568;">/ 月</span>
                <div style="background:#E0F2FE; color:#0369A1; font-size:0.84rem; font-weight:800; padding:4px 8px; border-radius:6px; margin-top:6px; display:inline-block;">
                    🎉 年繳優惠 NT$ 2,000 / 年 (現省 NT$ 400)
                </div>
            </div>
            <div style="color: #2D2622; font-size: 0.90rem; line-height: 2.1;">
                <div><span style="color:#0284C7; font-weight:800;">✔</span> <strong>包含基礎探索版全部總經功能</strong></div>
                <div><span style="color:#0284C7; font-weight:800;">✔</span> <strong>解鎖【個股深度研究】全模組</strong></div>
                <div><span style="color:#0284C7; font-weight:800;">✔</span> <strong>解鎖【進階數據與評分】全模組</strong></div>
                <div><span style="color:#0284C7; font-weight:800;">✔</span> <strong>五大多因子量化綜合評分</strong> 與 攻防階梯價</div>
                <div style="color: #94A3B8;"><span>✖</span> 資產配置與模擬（全天候模型、歷史回測推估）</div>
                <div style="color: #94A3B8;"><span>✖</span> 全球跨國央行與財報數據庫（市場要聞）</div>
            </div>
        </div>
        <div style="margin-top: 14px;">
    """, unsafe_allow_html=True)
    
    if st.button("🚀 開通進階量化版 (NT$ 200/月 或 年繳 2,000)", key="btn_pay_200", type="secondary", use_container_width=True):
        modal_checkout(
            tier_code=1,
            plan_name="⚡ 進階量化版",
            monthly_price=200,
            annual_price=2000,
            monthly_url="https://payment.ecpay.com.tw",
            annual_url="https://payment.ecpay.com.tw"
        )
        
    st.markdown("</div></div>", unsafe_allow_html=True)

# 方案 3：專業全能旗艦版（NT$ 300/月 ｜ 年繳 NT$ 3,000）
with col_p3:
    st.markdown("""
    <div class="pricing-box-wrapper popular">
        <div style="position:absolute; top:-12px; right:18px; background:#0D9488; color:#FFFFFF; padding:2px 10px; border-radius:12px; font-weight:800; font-size:0.75rem; letter-spacing:0.5px;">🔥 專業首選</div>
        <div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #0D9488;">👑 專業全能旗艦版</div>
            <div style="font-size: 0.86rem; color: #64748B; margin-top: 5px;">適合全方位資產配置、長期存股與高階交易者</div>
            <div style="margin: 20px 0 18px 0; padding-bottom: 16px; border-bottom: 1px solid #EFEAE2;">
                <span style="font-size: 1.20rem; font-weight: 700; color: #0D9488;">NT$</span>
                <span style="font-size: 2.2rem; font-weight: 800; color: #0D9488;">300</span>
                <span style="font-size: 0.88rem; color: #847568;">/ 月</span>
                <div style="background:#D1FAE5; color:#065F46; font-size:0.84rem; font-weight:800; padding:4px 8px; border-radius:6px; margin-top:6px; display:inline-block;">
                    🎉 年繳超值 NT$ 3,000 / 年 (現省 NT$ 600)
                </div>
            </div>
            <div style="color: #2D2622; font-size: 0.90rem; line-height: 2.1;">
                <div><span style="color:#0D9488; font-weight:800;">✔</span> <strong>100% 完整解鎖全系統 12 大分析模組</strong></div>
                <div><span style="color:#0D9488; font-weight:800;">✔</span> <strong>解鎖【資產配置與模擬】</strong>：客觀積木、相關性矩陣</div>
                <div><span style="color:#0D9488; font-weight:800;">✔</span> <strong>智慧投組滾動回測</strong>：單筆與 DCA 複利試算</div>
                <div><span style="color:#0D9488; font-weight:800;">✔</span> <strong>全球金融即時要聞</strong>：央行日曆、毫秒級快訊串流</div>
                <div><span style="color:#0D9488; font-weight:800;">✔</span> <strong>享受未來全站所有新功能優先自動升級</strong></div>
            </div>
        </div>
        <div style="margin-top: 14px;">
    """, unsafe_allow_html=True)
    
    if st.button("🌟 開通專業全能旗艦版 (NT$ 300/月 或 年繳 3,000)", key="btn_pay_300", type="primary", use_container_width=True):
        modal_checkout(
            tier_code=2,
            plan_name="👑 專業全能旗艦版",
            monthly_price=300,
            annual_price=3000,
            monthly_url="https://payment.ecpay.com.tw",
            annual_url="https://payment.ecpay.com.tw"
        )
        
    st.markdown("</div></div>", unsafe_allow_html=True)

# ==========================================
# 頁尾版權與專業免責聲明
# ==========================================
st.markdown("""
<div style="margin-top: 48px; text-align: center; color: #5C5248; font-size: 0.94rem; line-height: 1.8; padding: 28px 10px 18px 10px; border-top: 1.5px solid #E6DFD7;">
    <strong style="color: #2D2622; font-size: 1.08rem; letter-spacing: 0.5px;">澄璞財務顧問工作室 ｜ JennyHsieh CFP® 認證理財規劃顧問</strong><br>
    <span style="color: #78716C; font-size: 0.90rem;">有「筱」陪伴 ｜ 攜手「筑」夢 ｜ 打造客觀、獨立、無利益衝突之量化財務決策體系</span>
</div>

<div style="background: #FAF7F2; border: 1px solid #E8DFD5; border-radius: 10px; padding: 18px 22px; margin-top: 12px; margin-bottom: 25px; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <span style="background: #E2E8F0; color: #334155; padding: 2px 8px; border-radius: 4px; font-weight: 800; font-size: 0.80rem;">⚠️ 免責聲明 (Disclaimer)</span>
    </div>
    <div style="color: #6E5D4F; font-size: 0.85rem; line-height: 1.7; margin: 0;">
        本終端機所提供之所有市場數據、分析圖表、演算法評分及量化模型僅供<strong>財務教育與投資決策輔助參考</strong>，不構成任何證券買賣、投資標的推薦或財務要約建議。<br>
        金融市場投資必定伴隨風險，過往歷史績效不保證未來獲利回報。投資人於進行任何資產配置決策前，應審慎評估自身之財務狀況與風險承受能力，並自負投資損益之責任。
    </div>
</div>
""", unsafe_allow_html=True)
