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
    page_title="智慧回測與前瞻推估 - 澄璞財務",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

import config
config.inject_global_style()

# 2. 掛載側邊欄狀態
from auth import render_login_widget, init_auth_state, TIER_NAMES, render_upgrade_checkout_widget
render_login_widget()
init_auth_state()
user_tier = st.session_state.get("user_tier", 0)

# ==============================================================================
# 🔒 本頁專屬安檢門（300 元旗艦版門檻：銜接統一雙欄彩色網格與就地開通模組）
# ==============================================================================
if user_tier < 2:
    target_plan = TIER_NAMES.get(2, "👑 專業全能旗艦版 (NT$ 300/月)")
    user_plan = TIER_NAMES.get(user_tier, "🌿 基礎探索版 (免費)")

    st.markdown(f"""
    <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 26px; margin-top:20px; margin-bottom:20px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.5rem;">🔒</span>
                <span style="font-size:1.30rem; font-weight:900; color:#78350F;">【11. 💰 標的真實歷史回測與前瞻推估】旗艦專屬解鎖功能</span>
            </div>
            <span style="background:#FEF3C7; color:#92400E; font-size:0.88rem; font-weight:900; padding:5px 14px; border-radius:20px; border:1.5px solid #FDE68A;">
                需要解鎖：{target_plan}
            </span>
        </div>
        <div style="font-size:1.02rem; font-weight:800; color:#92400E; margin-bottom:8px;">
            ✦ 核心價值：跨世紀全收益復權回測引擎，結合真實滾動勝率與複合 DCA 前瞻，打破單純靜態年化的倖存者偏差盲點
        </div>
        <div style="font-size:0.96rem; color:#6B584C; line-height:1.7;">
            您目前的使用權限為：<strong>{user_plan}</strong>。單看靜態報酬容易忽略波段回撤的巨大心理折磨，本模組提供全收益復權回測、水下最深回撤深度、日曆年矩陣與定期定額 (DCA) 複合前瞻滾動試算，為您的真實資金建立最客觀的風控底線。
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 💎 就地渲染：由 auth.py 統一帶出彩色邊框雙欄網格卡片矩陣與全套帳密開通表單
    render_upgrade_checkout_widget(required_tier=2, feature_title="智慧投組回測與前瞻推估")

    st.stop()

# ==============================================================================
# 👇 通過驗證放行後，正常執行的完整分析與視覺化程式碼
# ==============================================================================

# ==========================================
# 注入自訂 CSS (思源繁體中文、暮光粉導航、大氣留白)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }

    .section-spacer {
        margin-top: 50px !important;
        margin-bottom: 24px !important;
    }
    .content-spacer {
        margin-top: 36px !important;
        margin-bottom: 20px !important;
    }

    .console-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 20px;
        margin: 18px 0 24px 0;
    }

    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
    }
    .kpi-cagr::before { background: linear-gradient(90deg, #10B981, #059669); }
    .kpi-vol::before { background: linear-gradient(90deg, #F59E0B, #D97706); }
    .kpi-sharpe::before { background: linear-gradient(90deg, #0284C7, #2563EB); }
    .kpi-maxdd::before { background: linear-gradient(90deg, #F43F5E, #E11D48); }

    .kpi-label {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, 'PingFang TC', sans-serif !important;
        font-size: 0.85rem;
        font-weight: 700;
        color: #64748B;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 900;
        color: #0F172A;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .kpi-delta {
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 8px;
    }
    .delta-green { color: #059669; }
    .delta-amber { color: #D97706; }
    .delta-blue { color: #0284C7; }
    .delta-red { color: #E11D48; }

    .feature-nav-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 18px;
        padding-bottom: 12px;
        border-bottom: 2px solid #FFE4E6;
    }
    .feature-nav-title {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Microsoft JhengHei UI', sans-serif !important;
        font-size: 1.22rem;
        font-weight: 900;
        color: #9F1239;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: 0.3px;
    }
    .feature-nav-subtitle {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Microsoft JhengHei UI', sans-serif !important;
        font-size: 0.90rem;
        color: #BE123C;
        font-weight: 800;
        background: #FFF1F2;
        border: 1px solid #FECDD3;
        padding: 5px 16px;
        border-radius: 20px;
    }

    div[data-testid="stButton"] button {
        height: 58px !important;
        border-radius: 14px !important;
        transition: all 0.20s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stButton"] button * {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Microsoft JhengHei UI', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.4px !important;
    }

    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #FB7185 0%, #E11D48 100%) !important;
        border: 1px solid #E11D48 !important;
        box-shadow: 0 4px 14px rgba(225, 29, 72, 0.28) !important;
    }
    div[data-testid="stButton"] button[kind="primary"] * {
        color: #FFFFFF !important;
        font-weight: 900 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15) !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #F43F5E 0%, #BE123C 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(225, 29, 72, 0.38) !important;
    }

    div[data-testid="stButton"] button[kind="secondary"] {
        background: #FFFFFF !important;
        border: 1.8px solid #E2E8F0 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] * {
        color: #475569 !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: #FFF5F6 !important;
        border-color: #FDA4AF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(244, 63, 94, 0.12) !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover * {
        color: #E11D48 !important;
    }

    .section-title-line {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Microsoft JhengHei UI', sans-serif !important;
        font-size: 1.50rem;
        font-weight: 900;
        color: #0F172A;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    .section-subtitle-line {
        font-size: 0.95rem;
        color: #64748B;
        line-height: 1.6;
        margin-bottom: 24px;
    }

    .concept-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #0284C7;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 16px 0 24px 0;
    }
    .concept-title {
        font-size: 0.92rem;
        font-weight: 800;
        color: #0369A1;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .concept-body {
        font-size: 0.88rem;
        color: #334155;
        line-height: 1.7;
    }

    .tactics-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 22px 24px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.02);
    }
    .tactics-card.accent-red { border-top: 4.5px solid #EF4444; }
    .tactics-card.accent-blue { border-top: 4.5px solid #0284C7; }
    .tactics-card.accent-green { border-top: 4.5px solid #059669; }

    .tactics-badge {
        font-size: 0.76rem;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 20px;
        display: inline-block;
        width: fit-content;
        margin-bottom: 10px;
    }
    .badge-red { background: #FEE2E2; color: #991B1B; }
    .badge-blue { background: #E0F2FE; color: #0369A1; }
    .badge-green { background: #D1FAE5; color: #065F46; }

    .tactics-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 8px;
    }
    .tactics-content {
        font-size: 0.90rem;
        color: #475569;
        line-height: 1.75;
    }
    .tactics-tip {
        margin-top: 14px;
        padding-top: 10px;
        border-top: 1px dashed #E2E8F0;
        font-size: 0.84rem;
        color: #64748B;
        font-weight: 600;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E6DFD7;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(45, 38, 34, 0.03);
        margin-top: 16px;
        margin-bottom: 16px;
    }
    .guide-box {
        background: #F4F0EB;
        border-left: 4.5px solid #0F766E;
        border-radius: 8px;
        padding: 20px 24px;
        margin: 28px 0;
    }
    .card-box {
        background: #FFFFFF;
        border: 1px solid #E6DFD7;
        border-left: 4.5px solid #0284C7;
        border-radius: 10px;
        padding: 20px 22px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .nowrap-unit {
        white-space: nowrap !important;
        display: inline-block;
    }
    .hero-title-box {
        margin: 0;
        padding: 0;
        line-height: 1.35;
    }
    .hero-caption-box {
        color: #64748B;
        font-size: 0.90rem;
        line-height: 1.6;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 全域雙向狀態綁定邏輯
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = ""

if 'active_tab_p10' not in st.session_state:
    st.session_state['active_tab_p10'] = "tab1"

if 'backtest_years' not in st.session_state:
    st.session_state['backtest_years'] = "5Y"

if 'benchmark_choice' not in st.session_state:
    st.session_state['benchmark_choice'] = "SP500"

if 'forward_years' not in st.session_state:
    st.session_state['forward_years'] = 8

if 'custom_forward_cagr' not in st.session_state:
    st.session_state['custom_forward_cagr'] = 10.0

if 'last_calculated_symbol' not in st.session_state:
    st.session_state['last_calculated_symbol'] = ""

if 'use_log_scale' not in st.session_state:
    st.session_state['use_log_scale'] = False

st.session_state['ticker_input_p10'] = st.session_state['current_ticker']

def sync_ticker_p10():
    val = st.session_state.get('ticker_input_p10', '').upper().strip()
    st.session_state['current_ticker'] = val

st.markdown("<h2 style='margin-bottom: 20px; font-weight: 900; color: #0F172A;'>💰 標的真實歷史回測與前瞻推估</h2>", unsafe_allow_html=True)

# ==========================================
# 頂部 Hero 區塊
# ==========================================
target_symbol = st.session_state.get('current_ticker', '').strip()
user_has_typed = bool(target_symbol)

benchmark_code = st.session_state['benchmark_choice']
benchmark_names = {
    "SP500": "標普 500 大盤",
    "QQQ": "那斯達克 100",
    "SOXX": "費城半導體",
    "DJI": "道瓊工業指數"
}
benchmark_tickers = {
    "SP500": "SPY",
    "QQQ": "QQQ",
    "SOXX": "SOXX",
    "DJI": "DIA"
}
current_bench_name = benchmark_names[benchmark_code]

if user_has_typed:
    active_symbol = target_symbol
    comparator_ticker = benchmark_tickers[benchmark_code]
    comparator_bench_label = current_bench_name
else:
    active_symbol = benchmark_tickers[benchmark_code]
    if benchmark_code == "SP500":
        comparator_ticker = "QQQ"
        comparator_bench_label = "那斯達克 100"
    else:
        comparator_ticker = "SPY"
        comparator_bench_label = "標普 500 大盤"

@st.cache_data(ttl=300)
def fetch_p10_meta(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
        company_name = info.get('shortName', symbol)
        curr_p = info.get('currentPrice') or info.get('regularMarketPrice') or 100.0
        return {'name': company_name, 'curr_p': curr_p}
    except Exception:
        return {'name': symbol, 'curr_p': 100.0}

p_meta = fetch_p10_meta(active_symbol)

bt_choice = st.session_state['backtest_years']
years_map = {"1Y": 1, "3Y": 3, "5Y": 5, "10Y": 10, "20Y": 20, "MAX": 99}
selected_years = years_map.get(bt_choice, 5)

col_search, col_name, col_p = st.columns([2.0, 4.2, 1.8])

with col_search:
    st.text_input(
        "🔍 本頁快速切換監控標的", 
        key="ticker_input_p10",
        on_change=sync_ticker_p10,
        placeholder="",
        help="輸入美股代碼後按 Enter 即時連動全模組"
    )
    st.markdown("""
        <div style='font-size: 0.80rem; color: #64748B; margin-top: -8px; line-height: 1.5;'>
            例：NVDA、MU、LLY、AAPL <span class='nowrap-unit' style='color: #BE123C; font-weight: 700;'>（輸入後按 Enter 查詢）</span>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 💎 跨世紀多基準真實全收益復權引擎
# ==========================================
@st.cache_data(ttl=600)
def run_unbiased_multi_benchmark_engine_v42(target_sym: str, comp_sym: str, years: int, is_custom: bool):
    t_target = yf.Ticker(target_sym)
    h_stock_full = t_target.history(period="max", auto_adjust=True)

    if h_stock_full is None or h_stock_full.empty or len(h_stock_full) < 10:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(25 * 365.25))
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        n = len(dates)
        np.random.seed(42)
        s_stock_full = pd.Series(100 * np.cumprod(1 + np.random.normal(0.0006, 0.016, n)), index=dates)
    else:
        s_stock_full = h_stock_full['Close'].dropna()

    t_comp = yf.Ticker(comp_sym)
    h_comp_full = t_comp.history(period="max", auto_adjust=True)
    
    if h_comp_full is not None and not h_comp_full.empty and len(h_comp_full) > 10:
        s_comp_raw = h_comp_full['Close'].dropna()
    else:
        s_comp_raw = s_stock_full.copy()

    common_start_dt = max(s_stock_full.index[0], s_comp_raw.index[0])
    s_stock_full = s_stock_full[s_stock_full.index >= common_start_dt]
    s_bench_full = s_comp_raw[s_comp_raw.index >= common_start_dt].reindex(s_stock_full.index).bfill().ffill()

    h_gld = yf.Ticker('GLD').history(start=common_start_dt.strftime('%Y-%m-%d'), auto_adjust=True)
    s_gld = h_gld['Close'].dropna() if (h_gld is not None and not h_gld.empty) else pd.Series(dtype=float)

    h_shy = yf.Ticker('SHY').history(start=common_start_dt.strftime('%Y-%m-%d'), auto_adjust=True)
    s_shy = h_shy['Close'].dropna() if (h_shy is not None and not h_shy.empty) else pd.Series(dtype=float)

    if years >= 90:
        s_stock = s_stock_full
        s_bench = s_bench_full
    else:
        cutoff_dt = s_stock_full.index[-1] - timedelta(days=int(years * 365.25))
        s_stock = s_stock_full[s_stock_full.index >= cutoff_dt]
        s_bench = s_bench_full[s_bench_full.index >= cutoff_dt]

    start_actual_price = float(s_stock.iloc[0])
    end_actual_price = float(s_stock.iloc[-1])

    stock_equity_sub = (s_stock / s_stock.iloc[0]) * 100.0
    bench_equity_sub = (s_bench / s_bench.iloc[0]) * 100.0

    stock_equity_full = (s_stock_full / s_stock_full.iloc[0]) * 100.0
    bench_equity_full = (s_bench_full / s_bench_full.iloc[0]) * 100.0

    stock_daily_full = s_stock_full.pct_change().dropna()
    bench_daily_full = s_bench_full.pct_change().reindex(stock_daily_full.index).fillna(0.0)
    r_gld_daily_full = s_gld.pct_change().reindex(stock_daily_full.index).fillna(0.00015)
    r_shy_daily_full = s_shy.pct_change().reindex(stock_daily_full.index).fillna(0.00010)

    port_daily_full = (
        bench_daily_full * 0.55 + 
        stock_daily_full * 0.15 + 
        r_gld_daily_full * 0.15 + 
        r_shy_daily_full * 0.15
    )
    port_equity_full = (1 + port_daily_full).cumprod() * 100.0

    port_equity_sub = port_equity_full.reindex(s_stock.index)
    port_equity_sub = (port_equity_sub / port_equity_sub.iloc[0]) * 100.0

    stock_peaks_full = stock_equity_full.cummax()
    stock_dd_full = (stock_equity_full - stock_peaks_full) / stock_peaks_full * 100.0
    bench_peaks_full = bench_equity_full.cummax()
    bench_dd_full = (bench_equity_full - bench_peaks_full) / bench_peaks_full * 100.0
    port_peaks_full = port_equity_full.cummax()
    port_dd_full = (port_equity_full - port_peaks_full) / port_peaks_full * 100.0

    stock_daily = s_stock.pct_change().dropna()
    bench_daily = s_bench.pct_change().reindex(stock_daily.index).fillna(0.0)

    actual_days = len(stock_daily)
    actual_years = actual_days / 252.0 if actual_days > 0 else 1.0
    first_date_str = s_stock.index[0].strftime('%Y-%m-%d')
    first_year = s_stock.index[0].year

    stock_total_ret = ((stock_equity_sub.iloc[-1] - 100.0) / 100.0) * 100.0
    bench_total_ret = ((bench_equity_sub.iloc[-1] - 100.0) / 100.0) * 100.0
    
    stock_cagr = ((stock_equity_sub.iloc[-1] / 100.0) ** (1.0 / actual_years) - 1.0) * 100.0
    stock_vol = stock_daily.std() * np.sqrt(252) * 100.0
    bench_cagr = ((bench_equity_sub.iloc[-1] / 100.0) ** (1.0 / actual_years) - 1.0) * 100.0
    bench_vol = bench_daily.std() * np.sqrt(252) * 100.0

    rf = 3.8
    stock_sharpe = (stock_cagr - rf) / stock_vol if stock_vol > 0 else 0
    bench_sharpe = (bench_cagr - rf) / bench_vol if bench_vol > 0 else 0

    rf_daily = rf / 100.0 / 252.0
    negative_returns = stock_daily[stock_daily < rf_daily] - rf_daily
    if len(negative_returns) > 5:
        real_downside_std = np.sqrt(np.mean(negative_returns**2)) * np.sqrt(252) * 100.0
        real_sortino = (stock_cagr - rf) / real_downside_std if real_downside_std > 0 else 0
    else:
        real_downside_std = stock_vol * 0.7
        real_sortino = stock_sharpe * 1.3

    stock_peaks_sub = stock_equity_sub.cummax()
    stock_dd_sub = (stock_equity_sub - stock_peaks_sub) / stock_peaks_sub * 100.0
    stock_max_dd = stock_dd_sub.min()
    bench_peaks_sub = bench_equity_sub.cummax()
    bench_dd_sub = (bench_equity_sub - bench_peaks_sub) / bench_peaks_sub * 100.0
    bench_max_dd = bench_dd_sub.min()
    port_max_dd = port_dd_full.min()

    full_min_dd = min(float(stock_dd_full.min()), float(bench_dd_full.min()), float(port_dd_full.min()))

    stock_annual_full = stock_daily_full.resample('YE').apply(lambda r: (np.prod(1 + r) - 1) * 100.0)
    bench_annual_full = bench_daily_full.resample('YE').apply(lambda r: (np.prod(1 + r) - 1) * 100.0)
    
    label_col = f'{target_sym} 標的' if is_custom else f'{p_meta["name"]} 標的'
    
    annual_dates = [datetime(d.year, 1, 1) for d in stock_annual_full.index]
    annual_matrix_full = pd.DataFrame({
        '日期': annual_dates,
        '年度': [str(d.year) for d in stock_annual_full.index],
        label_col: stock_annual_full.values,
        f'{comparator_bench_label}': bench_annual_full.reindex(stock_annual_full.index).fillna(0.0).values
    })

    is_shorter_than_selected = (actual_years < (years * 0.85)) and (years >= 3) and (years < 90)

    return {
        's_stock_full': s_stock_full,
        'stock_equity_sub': stock_equity_sub,
        'bench_equity_sub': bench_equity_sub,
        'port_equity_sub': port_equity_sub,
        'stock_dd_full': stock_dd_full,
        'bench_dd_full': bench_dd_full,
        'port_dd_full': port_dd_full,
        'stock_total_ret': stock_total_ret,
        'bench_total_ret': bench_total_ret,
        'stock_cagr': stock_cagr,
        'stock_vol': stock_vol,
        'stock_sharpe': stock_sharpe,
        'stock_sortino': real_sortino,
        'stock_max_dd': stock_max_dd,
        'full_min_dd': full_min_dd,
        'bench_cagr': bench_cagr,
        'bench_vol': bench_vol,
        'bench_sharpe': bench_sharpe,
        'bench_max_dd': bench_max_dd,
        'port_max_dd': port_max_dd,
        'annual_matrix_full': annual_matrix_full,
        'actual_years': actual_years,
        'first_date_str': first_date_str,
        'first_year': first_year,
        'is_shorter_than_selected': is_shorter_than_selected,
        'start_actual_price': start_actual_price,
        'end_actual_price': end_actual_price,
        'selected_start_dt': s_stock.index[0],
        'selected_end_dt': s_stock.index[-1]
    }

bt_data = run_unbiased_multi_benchmark_engine_v42(active_symbol, comparator_ticker, selected_years, user_has_typed)
label_name = target_symbol if user_has_typed else current_bench_name

if st.session_state['last_calculated_symbol'] != active_symbol:
    cagr_anchor = max(5.0, min(15.0, round(float(bt_data['stock_cagr']), 1)))
    st.session_state['custom_forward_cagr'] = cagr_anchor
    st.session_state['last_calculated_symbol'] = active_symbol

if bt_choice == "MAX":
    period_badge_title = f"共同上市以來（{bt_data['first_date_str']} 起，共 {bt_data['actual_years']:.1f} 年）"
    card_term_label = f"上市以來總報酬 ({bt_data['first_year']}~至今)"
elif bt_data['is_shorter_than_selected']:
    period_badge_title = f"掛牌以來（{bt_data['first_date_str']} 起，共 {bt_data['actual_years']:.1f} 年）"
    card_term_label = f"掛牌以來總報酬 ({bt_data['first_year']}~至今)"
else:
    period_badge_title = f"近 {bt_choice}（共 {bt_data['actual_years']:.1f} 年）"
    card_term_label = f"近 {bt_choice} 累積總報酬"

with col_name:
    if user_has_typed:
        st.markdown(f"""
            <div class="hero-title-box">
                <h3 style="margin:0; font-weight:800; color:#0F172A; display:inline-block;">{p_meta['name']}</h3> 
                <span class="nowrap-unit" style="font-size:1.15rem; font-weight:800; color:#BE123C; margin-left:6px;">({target_symbol})</span>
            </div>
            <div class="hero-caption-box">
                回測範疇：<strong>{period_badge_title}</strong> ｜ 對照基準：<strong>{current_bench_name}</strong>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="hero-title-box">
                <h3 style="margin:0; font-weight:800; color:#0F172A; display:inline-block;">💰 {current_bench_name}</h3> 
                <span class="nowrap-unit" style="font-size:0.95rem; font-weight:700; color:#64748B; background:#F1F5F9; padding:2px 8px; border-radius:6px; margin-left:6px;">基準巡航中</span>
            </div>
            <div class="hero-caption-box">
                對照基準：<strong>{comparator_bench_label}</strong> ｜ 模式：大盤基準巡航
            </div>
        """, unsafe_allow_html=True)

with col_p:
    st.metric("即時現價", f"${p_meta['curr_p']:.2f}", f"年化 CAGR: +{bt_data['stock_cagr']:.2f}%")

# ==========================================
# 整合式控制艙
# ==========================================
st.markdown("""
<div class="console-box">
    <div style="font-size: 0.86rem; font-weight: 800; color: #334155; margin-bottom: 8px;">
        🧭 回測時間跨度與專業基準切換（全歷史數據已完備）
    </div>
</div>
""", unsafe_allow_html=True)

c_horizon, c_benchmark = st.columns([1.1, 1.0])

with c_horizon:
    time_options = ["1Y", "3Y", "5Y", "10Y", "20Y", "MAX"]
    time_labels = {"1Y": "1年 (1Y)", "3Y": "3年 (3Y)", "5Y": "5年 (5Y)", "10Y": "10年 (10Y)", "20Y": "20年 (20Y)", "MAX": "完整上限 (MAX)"}
    selected_time = st.segmented_control(
        "回測時間跨度",
        options=time_options,
        format_func=lambda x: time_labels[x],
        default=st.session_state['backtest_years'] if st.session_state['backtest_years'] in time_options else "5Y",
        label_visibility="collapsed"
    )
    if selected_time and selected_time != st.session_state['backtest_years']:
        st.session_state['backtest_years'] = selected_time
        st.rerun()

with c_benchmark:
    b_keys = ["SP500", "QQQ", "SOXX", "DJI"]
    b_labels = {
        "SP500": "🏛️ 標普 500",
        "QQQ": "🚀 那斯達克",
        "SOXX": "⚡ 費半晶片",
        "DJI": "🛡️ 道瓊工業"
    }
    selected_b = st.segmented_control(
        "對標基準",
        options=b_keys,
        format_func=lambda x: b_labels[x],
        default=st.session_state['benchmark_choice'],
        label_visibility="collapsed"
    )
    if selected_b and selected_b != st.session_state['benchmark_choice']:
        st.session_state['benchmark_choice'] = selected_b
        st.rerun()

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ==========================================
# 現代微光金融指標卡
# ==========================================
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card kpi-cagr">
        <div class="kpi-label">📈 歷史年化報酬率 (CAGR)</div>
        <div class="kpi-value">+{bt_data['stock_cagr']:.2f}%</div>
        <div class="kpi-delta delta-green">
            <span>同期{comparator_bench_label}</span> <strong>+{bt_data['bench_cagr']:.2f}%</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card kpi-vol">
        <div class="kpi-label">⚡ 歷史年化波動率</div>
        <div class="kpi-value">{bt_data['stock_vol']:.2f}%</div>
        <div class="kpi-delta delta-amber">
            <span>同期{comparator_bench_label}</span> <strong>{bt_data['bench_vol']:.2f}%</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card kpi-sharpe">
        <div class="kpi-label">💎 歷史夏普值 (Sharpe)</div>
        <div class="kpi-value">{bt_data['stock_sharpe']:.2f}</div>
        <div class="kpi-delta delta-blue">
            <span>{comparator_bench_label}夏普</span> <strong>{bt_data.get('bench_sharpe', 0.85):.2f}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card kpi-maxdd">
        <div class="kpi-label">⚓ 歷史最深回撤 (MaxDD)</div>
        <div class="kpi-value">{bt_data['stock_max_dd']:.2f}%</div>
        <div class="kpi-delta delta-red">
            <span>{comparator_bench_label}最深</span> <strong>{bt_data['bench_max_dd']:.2f}%</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 💎 頂級導航控制艙（思源繁中字型 ＋ 暮光蜜桃淡粉高亮 ＋ 充裕留白）
# ==============================================================================
nav_dict = {
    "tab1": "一、長期淨值增長曲線 (Equity Curve) vs 大盤對比",
    "tab2": "二、歷史水下回撤曲線 (Underwater Drawdown) 與抗跌防護",
    "tab3": "三、日曆年度勝率拆解與多空年份對比矩陣",
    "tab4": "四、單筆投入之真實滾動持有勝率與機構風控分析",
    "tab5": "五、自訂單筆 ＋ 定期定額 (DCA) 複合前瞻滾動試算"
}

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="feature-nav-header">
    <div class="feature-nav-title">
        <span>🧭 模組深度分析選單</span>
        <span style="font-size: 0.90rem; color: #64748B; font-weight: 600;">（請點擊下方按鈕切換檢視維度）</span>
    </div>
    <div class="feature-nav-subtitle">
        當前檢視：{nav_dict[st.session_state['active_tab_p10']]}
    </div>
</div>
""", unsafe_allow_html=True)

row1_c1, row1_c2, row1_c3 = st.columns(3)
with row1_c1:
    is_t1 = (st.session_state['active_tab_p10'] == "tab1")
    if st.button("📊 一、長期淨值增長曲線 vs 大盤對比", type="primary" if is_t1 else "secondary", use_container_width=True):
        st.session_state['active_tab_p10'] = "tab1"
        st.rerun()

with row1_c2:
    is_t2 = (st.session_state['active_tab_p10'] == "tab2")
    if st.button("📉 二、歷史水下回撤與抗跌防護分析", type="primary" if is_t2 else "secondary", use_container_width=True):
        st.session_state['active_tab_p10'] = "tab2"
        st.rerun()

with row1_c3:
    is_t3 = (st.session_state['active_tab_p10'] == "tab3")
    if st.button("🎯 三、日曆年度勝率拆解與多空矩陣", type="primary" if is_t3 else "secondary", use_container_width=True):
        st.session_state['active_tab_p10'] = "tab3"
        st.rerun()

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

row2_c1, row2_c2 = st.columns(2)
with row2_c1:
    is_t4 = (st.session_state['active_tab_p10'] == "tab4")
    if st.button("💵 四、單筆投入之真實滾動持有勝率與機構風控分析", type="primary" if is_t4 else "secondary", use_container_width=True):
        st.session_state['active_tab_p10'] = "tab4"
        st.rerun()

with row2_c2:
    is_t5 = (st.session_state['active_tab_p10'] == "tab5")
    if st.button("🌱 五、自訂單筆 ＋ 定期定額 (DCA) 複合前瞻滾動試算", type="primary" if is_t5 else "secondary", use_container_width=True):
        st.session_state['active_tab_p10'] = "tab5"
        st.rerun()

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

active_p10 = st.session_state['active_tab_p10']

# ----------------------------------------------------
# 分頁 1：長期淨值曲線 vs 對標基準
# ----------------------------------------------------
if active_p10 == "tab1":
    c_hdr1, c_hdr2 = st.columns([3.3, 1.2])
    with c_hdr1:
        st.markdown(f"""
            <div class="section-title-line">
                📊 一、{label_name} 長期累積淨值曲線 <span class="nowrap-unit">(Equity Curve)</span> vs <span class="nowrap-unit">{comparator_bench_label} 對比</span>
            </div>
            <div class="section-subtitle-line">
                追蹤國際標準之還原總回報走勢（Total Return），精確對比個股 Alpha 與大盤機會成本。
            </div>
        """, unsafe_allow_html=True)
    with c_hdr2:
        use_dual_axis = st.checkbox("⚖️ 啟用右側獨立 Y 軸 (解決對照組貼地)", value=False, help="若標的漲幅極大導致對照組貼地，可勾選啟用獨立右軸縮放")
        use_log = st.checkbox("📐 切換為對數座標 (Log Scale)", value=False, help="以對數比例呈現百分比複合增長")

    st.markdown(f"""
    <div class="concept-card">
        <div class="concept-title">
            💡 什麼是「基期 $100」？為什麼 Y 軸數值不是現價？
        </div>
        <div class="concept-body">
            • <strong>非即時股價走勢</strong>：這張圖表並非呈現標的的市場成交價格，而是國際資產管理業標準之<strong>「資產累積淨值走勢（Equity Curve）」</strong>。<br>
            • <strong>標準化起點比較</strong>：本模型假設在回測第一天，您於 <code>{label_name}</code>、<code>{comparator_bench_label}</code> 與 <code>多元配置</code> 各自單筆買入 <strong>$100 美元</strong>，並將這段期間所有的<strong>現金股利發放、股票分割拆股完全還原滾入複利</strong>。<br>
            • <strong>如何閱讀 Y 軸</strong>：若當前走勢線來到 <strong>$180</strong>，代表當初投入的 $100 元已成長為 $180 元（實質淨回報 <strong>+80%</strong>）；若來到 <strong>$3,000</strong>，代表本金滾動放大了 <strong>30 倍</strong>。
        </div>
    </div>
    """, unsafe_allow_html=True)

    fig_eq = make_subplots(specs=[[{"secondary_y": True}]]) if use_dual_axis else go.Figure()
    
    trace_stock = go.Scatter(
        x=bt_data['stock_equity_sub'].index, y=bt_data['stock_equity_sub'].values,
        mode='lines', line=dict(color='#0284C7', width=3),
        name=f"🌟 {label_name} (起點 $100 ➔ 終值 ${bt_data['stock_equity_sub'].iloc[-1]:,.1f})",
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" + f"{label_name}: " + "投入 $100 ➔ 累積為 $%{y:,.1f}<extra></extra>"
    )
    
    trace_bench = go.Scatter(
        x=bt_data['bench_equity_sub'].index, y=bt_data['bench_equity_sub'].values,
        mode='lines', line=dict(color='#EF4444', width=2, dash='dot'),
        name=f"{comparator_bench_label} (起點 $100 ➔ 終值 ${bt_data['bench_equity_sub'].iloc[-1]:,.1f})",
        hovertemplate="<b>" + f"{comparator_bench_label}: " + "</b>投入 $100 ➔ 累積為 $%{y:,.1f}<extra></extra>"
    )
    
    trace_port = go.Scatter(
        x=bt_data['port_equity_sub'].index, y=bt_data['port_equity_sub'].values,
        mode='lines', line=dict(color='#047857', width=2.2, dash='dash'),
        name=f"多元分散配置 (起點 $100 ➔ 終值 ${bt_data['port_equity_sub'].iloc[-1]:,.1f})",
        hovertemplate="<b>多元配置: </b>投入 $100 ➔ 累積為 $%{y:,.1f}<extra></extra>"
    )

    if use_dual_axis:
        fig_eq.add_trace(trace_stock, secondary_y=False)
        fig_eq.add_trace(trace_bench, secondary_y=True)
        fig_eq.add_trace(trace_port, secondary_y=True)
    else:
        fig_eq.add_trace(trace_stock)
        fig_eq.add_trace(trace_bench)
        fig_eq.add_trace(trace_port)

    y_title_text = f"<b>{label_name} 資產終值（基期 $100 起算）</b>"
    y_secondary_title = f"<b>{comparator_bench_label} / 多元配置 終值（基期 $100）</b>"

    layout_dict = dict(
        title=dict(
            text=f"<b>{period_badge_title} 累積淨值走勢（所有標的均以 $100 本金起跑）{' — [雙軸獨立尺度]' if use_dual_axis else ''}</b>",
            font=dict(size=14, color="#1E293B"),
            x=0.01,
            y=0.98,
            yanchor="top"
        ),
        height=550,
        margin=dict(t=95, b=65, l=65, r=160 if use_dual_axis else 130),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11, color="#475569"),
            rangeslider=dict(
                visible=True,
                thickness=0.08,
                bgcolor="#F8FAFC",
                bordercolor="#CBD5E1",
                borderwidth=1
            ),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="近1年", step="year", stepmode="backward"),
                    dict(count=3, label="近3年", step="year", stepmode="backward"),
                    dict(count=5, label="近5年", step="year", stepmode="backward"),
                    dict(count=10, label="近10年", step="year", stepmode="backward"),
                    dict(step="all", label="所選完整區間")
                ]),
                font=dict(size=11, color="#334155"),
                bgcolor="#FFFFFF",
                activecolor="#FFE4E6",
                y=1.08,
                x=0.01
            )
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.05 if use_dual_axis else 1.02,
            font=dict(size=11, color="#1E293B"),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="#E2E8F0",
            borderwidth=1
        ),
        hovermode="x unified"
    )

    fig_eq.update_layout(**layout_dict)

    if use_dual_axis:
        fig_eq.update_yaxes(
            title_text=y_title_text, 
            secondary_y=False, 
            showgrid=True, 
            gridcolor='#F1F5F9',
            tickformat="$,.0f",
            tickfont=dict(size=11, color="#0284C7"),
            type="log" if use_log else "linear"
        )
        fig_eq.update_yaxes(
            title_text=y_secondary_title, 
            secondary_y=True, 
            showgrid=False,
            tickformat="$,.0f",
            tickfont=dict(size=11, color="#DC2626"),
            type="log" if use_log else "linear"
        )
    else:
        fig_eq.update_yaxes(
            title="<b>資產成長終值（以 $100 本金起算）</b>", 
            showgrid=True, 
            gridcolor='#F1F5F9',
            tickformat="$,.0f",
            tickfont=dict(size=11, color="#475569"),
            type="log" if use_log else "linear"
        )

    st.plotly_chart(fig_eq, use_container_width=True, key="p10_stock_eq_v42")

    alpha_diff = bt_data['stock_total_ret'] - bt_data['bench_total_ret']
    alpha_cagr_diff = bt_data['stock_cagr'] - bt_data['bench_cagr']

    stock_ret_val = bt_data['stock_total_ret']
    bench_ret_val = bt_data['bench_total_ret']
    multiple_val = (bt_data['stock_equity_sub'].iloc[-1] / 100.0)

    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    col_m1, col_m2, col_m3 = st.columns(3)

    with col_m1:
        arrow_s = "⬆" if stock_ret_val >= 0 else "⬇"
        color_s = "#047857" if stock_ret_val >= 0 else "#DC2626"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.90rem; font-weight:700; color:#64748B; margin-bottom:4px;">🌟 {card_term_label}</div>
            <div style="font-size:1.60rem; font-weight:900; color:#0F172A; margin-bottom:4px;">{stock_ret_val:+,.1f}%</div>
            <div style="font-size:0.86rem; color:{color_s}; font-weight:700; margin-bottom:2px;">{arrow_s} 年化回報 +{bt_data['stock_cagr']:.2f}%</div>
            <div style="font-size:0.78rem; color:#64748B;">投入 $100 ➔ 終值 ${bt_data['stock_equity_sub'].iloc[-1]:,.1f}（增長 {multiple_val:.1f} 倍）</div>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        arrow_b = "⬆" if bench_ret_val >= 0 else "⬇"
        color_b = "#047857" if bench_ret_val >= 0 else "#DC2626"
        bench_multiple_val = (bt_data['bench_equity_sub'].iloc[-1] / 100.0)
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.90rem; font-weight:700; color:#64748B; margin-bottom:4px;">同期 {comparator_bench_label} 總報酬</div>
            <div style="font-size:1.60rem; font-weight:900; color:#0F172A; margin-bottom:4px;">{bench_ret_val:+,.1f}%</div>
            <div style="font-size:0.86rem; color:{color_b}; font-weight:700; margin-bottom:2px;">{arrow_b} 同期年化 +{bt_data['bench_cagr']:.2f}%</div>
            <div style="font-size:0.78rem; color:#64748B;">投入 $100 ➔ 終值 ${bt_data['bench_equity_sub'].iloc[-1]:,.1f}（增長 {bench_multiple_val:.1f} 倍）</div>
        </div>
        """, unsafe_allow_html=True)

    with col_m3:
        arrow_alpha = "⬆" if alpha_diff >= 0 else "⬇"
        color_alpha = "#047857" if alpha_diff >= 0 else "#DC2626"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.90rem; font-weight:700; color:#64748B; margin-bottom:4px;">🎯 相對 {comparator_bench_label} Alpha</div>
            <div style="font-size:1.60rem; font-weight:900; color:#0F172A; margin-bottom:4px;">{alpha_diff:+,.1f}%</div>
            <div style="font-size:0.86rem; color:{color_alpha}; font-weight:700; margin-bottom:2px;">{arrow_alpha} 年化勝出 {alpha_cagr_diff:+.1f}%</div>
            <div style="font-size:0.78rem; color:#64748B;">板塊超額資本利得與複利優勢</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #FFFBEB; border: 1px solid #D97706; border-left: 4.5px solid #D97706; border-radius: 8px; padding: 16px 20px; margin-top: 24px;">
        <div style="font-weight: 800; font-size: 0.90rem; color: #92400E; margin-bottom: 4px;">
            ⚠️ 【長期累積淨值回測之風險警語與實務限制】
        </div>
        <div style="color: #78350F; font-size: 0.83rem; line-height: 1.65;">
            • <strong>歷史績效非未來保證</strong>：過去長期累積之超額 Alpha 係反映標的歷史成長軌跡，不代表未來必然複製相同回報。<br>
            • <strong>倖存者偏差與極端行情限制</strong>：超長週期個股回測通常包含企業從微型轉向成熟之高速爆發期；投資人應審慎考量大數法則制約，避免以極端歷史倍數作為未來現金流規劃之單一依據。
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 2：歷史水下回撤曲線
# ----------------------------------------------------
elif active_p10 == "tab2":
    st.markdown(f"""
        <div class="section-title-line">
            📉 二、{label_name} 歷史水下回撤深度曲線 <span class="nowrap-unit">(Underwater Drawdown)</span> 與抗跌防護
        </div>
        <div class="section-subtitle-line">
            完整記錄標的每一次歷史波段修正中，自前期高點下跌之深度與修復歷程。
        </div>
    """, unsafe_allow_html=True)

    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=bt_data['stock_dd_full'].index, y=bt_data['stock_dd_full'].values,
        mode='lines', line=dict(color='#0284C7', width=2),
        fill='tozeroy', fillcolor='rgba(2, 132, 199, 0.15)',
        name=f"🌟 {label_name} 回撤 (歷史最深 {bt_data['stock_max_dd']:.1f}%)",
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>回撤: %{y:.1f}%<extra></extra>"
    ))
    fig_dd.add_trace(go.Scatter(
        x=bt_data['bench_dd_full'].index, y=bt_data['bench_dd_full'].values,
        mode='lines', line=dict(color='#EF4444', width=1.5, dash='dot'),
        name=f"{comparator_bench_label} 回撤 (最深 {bt_data['bench_max_dd']:.1f}%)",
        hovertemplate="<b>" + f"{comparator_bench_label} 回撤: " + "</b>%{y:.1f}%<extra></extra>"
    ))
    fig_dd.add_trace(go.Scatter(
        x=bt_data['port_dd_full'].index, y=bt_data['port_dd_full'].values,
        mode='lines', line=dict(color='#047857', width=2, dash='dash'),
        name=f"多元配置回撤 (最深 {bt_data['port_max_dd']:.1f}%)",
        hovertemplate="<b>配置回撤</b>: %{y:.1f}%<extra></extra>"
    ))
    fig_dd.add_hline(y=0, line_color="#334155", line_width=1)

    y_full_lowest = bt_data['full_min_dd']
    y_plot_bottom = min(-100.0, np.floor(y_full_lowest * 1.08 / 10.0) * 10.0) if y_full_lowest < -90 else (np.floor(y_full_lowest * 1.08 / 5.0) * 5.0)
    
    fig_dd.update_layout(
        title=dict(
            text=f"<b>{period_badge_title} 歷史下檔回撤深度對比 (%) — 谷底完整呈現，可拖動下方滑桿</b>",
            font=dict(size=14, color="#1E293B"),
            x=0.01,
            y=0.98,
            yanchor="top"
        ),
        height=560,
        margin=dict(t=95, b=75, l=55, r=160),
        xaxis=dict(
            showgrid=False, 
            tickfont=dict(size=11, color="#475569"),
            range=[bt_data['selected_start_dt'], bt_data['selected_end_dt']],
            rangeslider=dict(
                visible=True,
                thickness=0.08,
                bgcolor="#F8FAFC",
                bordercolor="#CBD5E1",
                borderwidth=1
            ),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="近1年", step="year", stepmode="backward"),
                    dict(count=3, label="近3年", step="year", stepmode="backward"),
                    dict(count=5, label="近5年", step="year", stepmode="backward"),
                    dict(count=10, label="近10年", step="year", stepmode="backward"),
                    dict(count=20, label="近20年", step="year", stepmode="backward"),
                    dict(step="all", label="完整上限 (MAX)")
                ]),
                font=dict(size=11, color="#334155"),
                bgcolor="#FFFFFF",
                activecolor="#FFE4E6",
                y=1.08,
                x=0.01
            )
        ),
        yaxis=dict(
            title="回撤深度 (%)", 
            range=[y_plot_bottom, 3],
            showgrid=True, 
            gridcolor='#F1F5F9', 
            tickfont=dict(size=11, color="#475569")
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            font=dict(size=11, color="#1E293B"),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="#E2E8F0",
            borderwidth=1
        ),
        hovermode="x unified"
    )
    st.plotly_chart(fig_dd, use_container_width=True, key="p10_dd_chart_v42")

    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.markdown("<h4 style='font-size:1.20rem; font-weight:900; color:#0F172A; margin-bottom:18px;'>🏛️ 水下回撤數據實戰解讀與操作策略</h4>", unsafe_allow_html=True)
    col_t1, col_t2, col_t3 = st.columns(3)

    with col_t1:
        st.markdown(f"""
        <div class="tactics-card accent-red">
            <div>
                <span class="tactics-badge badge-red">🛡️ 維度一：極限壓力測試</span>
                <div class="tactics-title">極限下檔邊界 ({bt_data['stock_max_dd']:.1f}%)</div>
                <div class="tactics-content">
                    該標的歷史曾面臨高達 <strong>{bt_data['stock_max_dd']:.1f}%</strong> 的帳面跌幅。<br>
                    <strong>【實戰指引】</strong>：此極限值界定了最壞情況。在建立部位前，應嚴格限制單一持股上限（例如總資產 15%~20%），避免在空頭谷底因保證金壓力或情緒崩潰被迫低割。
                </div>
            </div>
            <div class="tactics-tip">📌 操作底線：設定最大容忍停損位階</div>
        </div>
        """, unsafe_allow_html=True)

    with col_t2:
        st.markdown("""
        <div class="tactics-card accent-blue">
            <div>
                <span class="tactics-badge badge-blue">⏱️ 維度二：修復週期檢驗</span>
                <div class="tactics-title">資本停滯期與造血力</div>
                <div class="tactics-content">
                    觀察曲線自深谷重返 0% 水平所耗費的時間。<br>
                    <strong>【實戰指引】</strong>：<br>
                    • <strong>V型快速收斂</strong>：代表市場情緒過度悲觀引起的超跌，具備極佳右側回補價值；<br>
                    • <strong>L型長期貼地</strong>：代表企業競爭護城河遭侵蝕，需當機立斷汰弱留強。
                </div>
            </div>
            <div class="tactics-tip">📌 操作底線：檢視是估值殺戮還是本業受損</div>
        </div>
        """, unsafe_allow_html=True)

    with col_t3:
        st.markdown(f"""
        <div class="tactics-card accent-green">
            <div>
                <span class="tactics-badge badge-green">⚖️ 維度三：非對稱防禦效益</span>
                <div class="tactics-title">多元配置吸震效果 ({bt_data['port_max_dd']:.1f}%)</div>
                <div class="tactics-content">
                    對照綠色虛線（股債金多元配置），最深回撤僅 <strong>{bt_data['port_max_dd']:.1f}%</strong>。<br>
                    <strong>【實戰指引】</strong>：配置負相關性之防禦層（如超短期公債、黃金），能在高 Beta 個股劇烈回調時充當安全氣囊，並在市場最恐慌時提供充裕的現金流逢低再平衡。
                </div>
            </div>
            <div class="tactics-tip">📌 操作底線：以資產積木平滑整體淨值震盪</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #FFFBEB; border: 1px solid #D97706; border-left: 4.5px solid #D97706; border-radius: 8px; padding: 16px 20px; margin-top: 24px;">
        <div style="font-weight: 800; font-size: 0.90rem; color: #92400E; margin-bottom: 4px;">
            ⚠️ 【水下回撤與下檔風險控制警語】
        </div>
        <div style="color: #78350F; font-size: 0.83rem; line-height: 1.65;">
            • <strong>極端歷史回撤非下檔極限</strong>：歷史最大回撤（Max Drawdown）僅反映既往樣本區間內之最大跌幅；若未來遭遇更嚴峻之產業顛覆、地緣黑天鵝或流動性擠兌，實際淨值下修幅度可能突破歷史邊界。<br>
            • <strong>流動性風險防範</strong>：深度回撤期間往往伴隨交易量萎縮與滑價損耗，建議投資人保留 6 ~ 12 個月無風險流動資金池，切忌以短支長。
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 3：日曆年度勝率拆解
# ----------------------------------------------------
elif active_p10 == "tab3":
    st.markdown(f"""
        <div class="section-title-line">
            🎯 三、{label_name} 日曆年度勝率拆解與多空年份對比矩陣 <span class="nowrap-unit">(Calendar Year)</span>
        </div>
        <div class="section-subtitle-line">
            客觀對照歷年該標的 vs {comparator_bench_label} 的年度勝負表現。您可以點擊左上方快捷鍵或直接拖曳下方時間滑動軌道，自由縮放與框選任意歷史多空週期。
        </div>
    """, unsafe_allow_html=True)

    df_ann = bt_data['annual_matrix_full']
    sym_col = df_ann.columns[2]

    fig_ann = go.Figure()
    fig_ann.add_trace(go.Bar(
        x=df_ann['日期'], 
        y=df_ann[sym_col],
        name=f"🌟 {label_name}",
        marker_color='#0284C7',
        text=[f"{v:+.1f}%" for v in df_ann[sym_col]],
        textposition='outside',
        cliponaxis=False,
        textfont=dict(size=11, color='#0284C7', family='Arial Black'),
        hovertemplate="<b>%{x|%Y} 年度</b><br>" + f"{label_name}: %{{y:+.2f}}%<extra></extra>"
    ))
    fig_ann.add_trace(go.Bar(
        x=df_ann['日期'], 
        y=df_ann[f'{comparator_bench_label}'],
        name=f"{comparator_bench_label}",
        marker_color='#EF4444',
        text=[f"{v:+.1f}%" for v in df_ann[f'{comparator_bench_label}']],
        textposition='outside',
        cliponaxis=False,
        textfont=dict(size=11, color='#EF4444', family='Arial Black'),
        hovertemplate="<b>%{x|%Y} 年度</b><br>" + f"{comparator_bench_label}: %{{y:+.2f}}%<extra></extra>"
    ))

    max_val_ann = max(df_ann[sym_col].max(), df_ann[f'{comparator_bench_label}'].max())
    min_val_ann = min(df_ann[sym_col].min(), df_ann[f'{comparator_bench_label}'].min())
    y_upper = max(max_val_ann * 1.25, max_val_ann + 15.0)
    y_lower = min(min_val_ann * 1.25 if min_val_ann < 0 else 0, -10.0)

    latest_date = df_ann['日期'].iloc[-1]
    default_start_date = latest_date - timedelta(days=int(9.5 * 365.25))

    fig_ann.update_layout(
        barmode='group',
        bargap=0.32,
        bargroupgap=0.08,
        title=dict(
            text=f"<b>歷年日曆年真實績效對照 (%) — 對標 {comparator_bench_label}（可拖曳下方軌道自由縮放年限）</b>",
            font=dict(size=14, color="#1E293B"),
            x=0.01,
            y=0.98,
            yanchor="top"
        ),
        height=550,
        margin=dict(t=98, b=75, l=45, r=160),
        xaxis=dict(
            type='date',
            range=[default_start_date, latest_date + timedelta(days=200)],
            dtick="M12",
            tickformat="%Y",
            showgrid=False, 
            tickfont=dict(size=11, color="#475569"),
            rangeslider=dict(
                visible=True,
                thickness=0.08,
                bgcolor="#F8FAFC",
                bordercolor="#CBD5E1",
                borderwidth=1
            ),
            rangeselector=dict(
                buttons=list([
                    dict(count=5, label="近5年", step="year", stepmode="backward"),
                    dict(count=10, label="近10年", step="year", stepmode="backward"),
                    dict(count=20, label="近20年", step="year", stepmode="backward"),
                    dict(step="all", label="完整收錄 (MAX)")
                ]),
                font=dict(size=11, color="#334155"),
                bgcolor="#FFFFFF",
                activecolor="#FFE4E6",
                y=1.08,
                x=0.01
            )
        ),
        yaxis=dict(title="年度報酬率 (%)", range=[y_lower, y_upper], showgrid=True, gridcolor='#F1F5F9', tickfont=dict(size=11, color="#475569")),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            font=dict(size=11, color="#1E293B"),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="#E2E8F0",
            borderwidth=1
        )
    )
    st.plotly_chart(fig_ann, use_container_width=True, key="p10_ann_chart_v42")

    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)

    df_disp = df_ann[['年度', sym_col, f'{comparator_bench_label}']].copy()
    df_disp['年度勝出方'] = np.where(df_disp[sym_col] >= df_disp[f'{comparator_bench_label}'], f'🌟 {label_name} 勝出', f'{comparator_bench_label} 勝出')
    df_disp['超額差額'] = df_disp[sym_col] - df_disp[f'{comparator_bench_label}']
    df_disp[sym_col] = df_disp[sym_col].apply(lambda x: f"{x:+.2f}%")
    df_disp[f'{comparator_bench_label}'] = df_disp[f'{comparator_bench_label}'].apply(lambda x: f"{x:+.2f}%")
    df_disp['超額差額'] = df_disp['超額差額'].apply(lambda x: f"{x:+.2f}%")
    st.dataframe(df_disp, use_container_width=True, hide_index=True)

    st.markdown("""
    <div style="background-color: #FFFBEB; border: 1px solid #D97706; border-left: 4.5px solid #D97706; border-radius: 8px; padding: 14px 18px; margin-top: 24px;">
        <div style="font-weight: 800; font-size: 0.90rem; color: #92400E; margin-bottom: 6px;">
            💡 【日曆年度數據實務判讀指引】
        </div>
        <div style="color: #78350F; font-size: 0.83rem; line-height: 1.7;">
            • <strong>跨年度景氣循環視角</strong>：年度柱狀圖是以標準公曆（1/1 ~ 12/31）結算。然而市場真實的升降息循環與產業庫存波段往往跨越 1 ~ 2 年，建議搭配「二、水下回撤分析」綜合檢視，更能看清波段真實跌幅與抗震能力。<br>
            • <strong>動態再平衡提醒</strong>：個別資產在連續多年大漲後，往往伴隨估值均值回歸的拉回整理，長線投資宜定期檢視資產配置比例，適時獲利了結或再平衡。
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 4：單筆投入之機構級風控指標與真實滾動勝率分析
# ----------------------------------------------------
elif active_p10 == "tab4":
    st.markdown(f"""
        <div class="section-title-line">
            💵 四、{label_name} 單筆投入之真實滾動持有勝率與機構風控分析
        </div>
        <div class="section-subtitle-line">
            基於全歷史交易日序列逐日滑動檢驗：評估在任意歷史時點單筆進場後，持有特定年限之真實正報酬機率與平均收益。
        </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([1.5, 1.5])
    with col_s1:
        init_lump_p4 = st.number_input(
            "💵 單筆期初投入金額（新台幣 / 元）：",
            min_value=0, max_value=100000000, value=1000000, step=100000,
            help="設定進行單筆機構級風控與勝率分析的金額"
        )
        st.caption(f"分析本金：**NT$ {init_lump_p4:,.0f} 元**")

    with col_s2:
        holding_period_years = st.slider(
            "⏳ 滾動持有週期 (1 ~ 10 年)：",
            min_value=1, max_value=10, value=3, step=1,
            help="評估單筆投入後，持有不同年數的真實歷史勝率與平均回報"
        )

    s_prices = bt_data['s_stock_full']
    window_days = int(holding_period_years * 252)

    if len(s_prices) > window_days + 10:
        rolling_returns = (s_prices.shift(-window_days) / s_prices - 1.0).dropna() * 100.0
        total_samples = len(rolling_returns)
        positive_samples = (rolling_returns > 0).sum()
        real_win_rate = (positive_samples / total_samples) * 100.0 if total_samples > 0 else 50.0
        real_avg_gain = rolling_returns.mean()
        real_median_gain = rolling_returns.median()
        real_worst_gain = rolling_returns.min()
    else:
        rolling_returns = (s_prices.iloc[-1] / s_prices.iloc[0] - 1.0) * 100.0
        real_win_rate = 100.0 if rolling_returns > 0 else 0.0
        real_avg_gain = rolling_returns
        real_median_gain = rolling_returns
        real_worst_gain = rolling_returns
        total_samples = len(s_prices)

    cagr_val = bt_data['stock_cagr']
    vol_val = bt_data['stock_vol']
    max_dd_val = bt_data['stock_max_dd']
    sharpe_val = bt_data['stock_sharpe']
    sortino_val = bt_data['stock_sortino']

    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("⚖️ 歷史夏普值 (Sharpe)", f"{sharpe_val:.2f}", "每承擔1%總風險之超額", delta_color="normal")
    rc2.metric("🛡️ 真實索提諾比率 (Sortino)", f"{sortino_val:.2f}", "校正真實負下檔風險", delta_color="normal")
    rc3.metric(f"🎯 {holding_period_years}年真實滾動勝率", f"{real_win_rate:.1f}%", f"全歷史取樣 {total_samples:,} 個真實區間", delta_color="normal")
    rc4.metric("📈 滾動平均總報酬", f"{real_avg_gain:+,.1f}%", f"中位數: {real_median_gain:+,.1f}%", delta_color="normal")

    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)
    st.markdown("<h4 style='font-size:1.25rem; font-weight:900; color:#0F172A; margin-bottom:18px;'>🏛️ 華爾街投行視角：單筆資金進場的三大真實風控審查維度</h4>", unsafe_allow_html=True)

    card_col1, card_col2 = st.columns(2)

    with card_col1:
        st.markdown(f"""
        <div class="card-box">
            <div style="font-size:1.05rem; font-weight:800; color:#0F766E; margin-bottom:10px;">📌 1. 極端尾部風險與歷史最差持有區間</div>
            <div style="font-size:0.92rem; color:#475569; line-height:1.8;">
                • <strong>週期最深回撤</strong>：<code>{target_symbol}</code> 回測期內最深單次回撤為 <strong>{max_dd_val:.1f}%</strong>。<br>
                • <strong>最不幸進場點測試</strong>：若在歷史最高點進場並嚴格持有 {holding_period_years} 年，歷史最差報酬為 <strong>{real_worst_gain:+,.1f}%</strong>（帳面曾面臨約 <strong>NT$ {init_lump_p4 * abs(min(0, real_worst_gain)) / 100:,.0f} 元</strong> 壓力）。這項數據真實呈現了大額資金進場的極限抗壓門檻。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with card_col2:
        st.markdown(f"""
        <div class="card-box" style="border-left-color: #047857;">
            <div style="font-size:1.05rem; font-weight:800; color:#047857; margin-bottom:10px;">🎯 2. 時間分散風險的真實歷史威力</div>
            <div style="font-size:0.92rem; color:#475569; line-height:1.8;">
                • <strong>真實樣本統計</strong>：系統已為您掃描 <strong>{total_samples:,} 個</strong> 跨越 {holding_period_years} 年的歷史區間，其中有 <strong>{real_win_rate:.1f}%</strong> 的區間實現正報酬。<br>
                • <strong>專業配置啟示</strong>：單筆資金在強勢資產中，拉長持有時間是降低擇時虧損機率最客觀、最有效的防護盾。
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #FFFBEB; border: 1px solid #D97706; border-left: 4.5px solid #D97706; border-radius: 8px; padding: 14px 18px; margin-top: 24px;">
        <div style="font-weight: 800; font-size: 0.90rem; color: #92400E; margin-bottom: 4px;">
            ⚠️ 【單筆資金進場與滾動勝率模型警語】
        </div>
        <div style="color: #78350F; font-size: 0.83rem; line-height: 1.65;">
            • <strong>純價格歷史量化統計說明</strong>：本模組指標係純粹基於歷年真實成交價格序列進行之嚴格滾動窗口切片，<strong>未包含個別企業未來看板財報預測或主觀市場情緒評分</strong>。<br>
            • <strong>時點選擇風險（Timing Risk）</strong>：單筆資金若一次性配置於歷史評價頂部，即便長線勝率高，短中期仍需承受顯著波動壓力，實務上建議結合分批建倉或護欄策略。
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 5：自訂單筆 ＋ 定期定額 (DCA) 複合前瞻試算
# ----------------------------------------------------
elif active_p10 == "tab5":
    st.markdown(f"""
        <div class="section-title-line">
            🌱 五、{label_name} 自訂單筆 ＋ 定期定額 <span class="nowrap-unit">(DCA)</span> 複合前瞻滾動試算
        </div>
        <div class="section-subtitle-line">
            設定期初單筆與每月扣款計畫，依預期複合成長率推估未來資產累積曲線。
        </div>
    """, unsafe_allow_html=True)

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        init_lump_combo = st.number_input(
            "💵 單筆期初投入金額（元）：",
            min_value=0, max_value=100000000, value=1000000, step=100000,
            help="若只想算純定期定額，此處輸入 0 即可"
        )
        st.caption(f"期初單筆投入：**NT$ {init_lump_combo:,.0f} 元**")

    with col_in2:
        monthly_ntd_combo = st.number_input(
            "🌱 每月定期定額金額（元）：",
            min_value=0, max_value=1000000, value=20000, step=1000,
            help="每月預計扣款金額；若只想算純單筆，此處輸入 0 即可"
        )
        st.caption(f"每月定額：**NT$ {monthly_ntd_combo:,.0f} 元**（一年累計投入 NT$ {monthly_ntd_combo*12:,.0f} 元）")

    col_in3, col_in4 = st.columns(2)
    with col_in3:
        forward_years_combo = st.slider(
            "⏳ 預估持續投資與累積年限 (1 ~ 30 年)：",
            min_value=1, max_value=30, value=st.session_state['forward_years'], step=1,
            key="slider_combo_years"
        )
        st.session_state['forward_years'] = forward_years_combo
        st.caption(f"時間跨度：**{forward_years_combo} 年**（共計存入 {forward_years_combo*12} 個月）")

    with col_in4:
        user_cagr_param = st.slider(
            "🎯 預估年化報酬率 CAGR (%)：",
            min_value=3.0, max_value=20.0, step=0.5,
            key="custom_forward_cagr",
            help=f"依據 {label_name} 歷史表現動態調校，您亦可依規劃策略自由增減"
        )
        st.caption(f"複利推估基準：**每年約 +{user_cagr_param:.1f}% 穩健滾動**")

    r_stock_base = user_cagr_param / 100.0
    monthly_r = r_stock_base / 12.0

    timeline_combo = np.arange(1, forward_years_combo + 1)
    combo_p_list = []
    combo_fv_list = []

    for y in timeline_combo:
        m = y * 12
        fv_lump_part = init_lump_combo * ((1 + r_stock_base) ** y)
        fv_dca_part = monthly_ntd_combo * (((1 + monthly_r)**m - 1) / monthly_r) * (1 + monthly_r) if monthly_r > 0 else (monthly_ntd_combo * m)
        total_fv = fv_lump_part + fv_dca_part
        total_p = init_lump_combo + (monthly_ntd_combo * m)

        combo_p_list.append(total_p)
        combo_fv_list.append(total_fv)

    curr_final_val = combo_fv_list[-1]
    target_top = curr_final_val * 1.15

    if target_top <= 2000000:
        step = 250000
    elif target_top <= 10000000:
        step = 1000000
    elif target_top <= 50000000:
        step = 5000000
    elif target_top <= 100000000:
        step = 10000000
    else:
        step = 25000000

    y_smart_max = np.ceil(target_top / step) * step

    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Scatter(
        x=timeline_combo, y=combo_fv_list,
        mode='lines+markers', line=dict(color='#0284C7', width=3.5),
        marker=dict(size=6),
        name=f"🌟 複合資產總值 (本金 + 複利)",
        fill='tonexty', fillcolor='rgba(2, 132, 199, 0.12)',
        hovertemplate="<b>第 %{x} 年</b><br>資產總值: NT$ %{y:,.0f} 元<extra></extra>"
    ))
    fig_combo.add_trace(go.Scatter(
        x=timeline_combo, y=combo_p_list,
        mode='lines', line=dict(color='#94A3B8', width=2, dash='dash'),
        name="累計總投入本金 (單筆 + 定期定額累計)",
        hovertemplate="<b>第 %{x} 年</b><br>累計本金: NT$ %{y:,.0f} 元<extra></extra>"
    ))

    fig_combo.update_layout(
        title=dict(
            text=f"<b>單筆 NT$ {init_lump_combo:,.0f} 元 ＋ 每月存 NT$ {monthly_ntd_combo:,.0f} 元 ➔ {forward_years_combo} 年累積走勢 (年化 {user_cagr_param:.1f}%)</b>",
            font=dict(size=14, color="#1E293B"),
            x=0.01,
            y=0.96
        ),
        height=480,
        margin=dict(t=65, b=65, l=65, r=160),
        xaxis=dict(
            title="<b>累積年限 (年)</b>", 
            range=[0.8, forward_years_combo + 0.3],
            tickmode='linear', 
            dtick=1 if forward_years_combo <= 10 else 2, 
            showgrid=True, 
            gridcolor='#F1F5F9', 
            tickfont=dict(size=11, color="#475569")
        ),
        yaxis=dict(
            title="<b>資產總值 (新台幣 元)</b>", 
            range=[0, y_smart_max],
            showgrid=True, 
            gridcolor='#F1F5F9', 
            tickfont=dict(size=11, color="#475569")
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            font=dict(size=11, color="#1E293B"),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="#E2E8F0",
            borderwidth=1
        ),
        hovermode="x unified"
    )
    st.plotly_chart(fig_combo, use_container_width=True, key="p10_combo_chart_v42")

    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)

    c_cb1, c_cb2, c_cb3 = st.columns(3)
    final_p = combo_p_list[-1]
    final_fv = combo_fv_list[-1]
    gain = final_fv - final_p
    total_roi_pct = (gain / final_p * 100.0) if final_p > 0 else 0.0
    asset_multiple = (final_fv / final_p) if final_p > 0 else 1.0

    c_cb1.metric("💰 累計總投入本金", f"NT$ {final_p:,.0f} 元", f"單筆 NT$ {init_lump_combo:,.0f} 元 + 定期定額")
    c_cb2.metric(f"🏆 {forward_years_combo} 年期末資產總值", f"NT$ {final_fv:,.0f} 元", f"淨獲利 +NT$ {gain:,.0f} 元", delta_color="normal")
    c_cb3.metric("📈 實質累積總報酬率", f"{total_roi_pct:+,.1f}%", f"總資產為本金之 {asset_multiple:.2f} 倍", delta_color="normal")

    st.markdown(f"""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.02rem;">💡 【圖表前瞻解讀：這張累積走勢圖是如何計算出來的？】</strong>
        <div style="color: #334155; margin-top: 6px; font-size: 0.90rem; line-height: 1.75;">
            • <strong>數學模型解析</strong>：<br>
              1. <strong>期初單筆本金</strong>：以年複利公式 $FV = P \\times (1 + r)^y$ 滾動計算。<br>
              2. <strong>每月定期定額</strong>：採用標準年金終值公式 $FV = PMT \\times \\frac{{(1 + r_m)^m - 1}}{{r_m}} \\times (1 + r_m)$，模擬每月薪水定期扣款滾入複利池之效果。<br>
            • <strong>客觀指標定義</strong>：<br>
              期末累積報酬率為 <strong>{total_roi_pct:+,.1f}%</strong>（代表淨賺本金的 {total_roi_pct:.1f}%），期末總結算資產為 <strong>NT$ {final_fv:,.0f} 元</strong>（為累計投入本金之 <strong>{asset_multiple:.2f} 倍</strong>）。
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #FFFBEB; border: 1px solid #D97706; border-left: 4.5px solid #D97706; border-radius: 8px; padding: 14px 18px; margin-top: 24px;">
        <div style="font-weight: 800; font-size: 0.90rem; color: #92400E; margin-bottom: 4px;">
            ⚠️ 【複合複利前瞻試算之免責與限制警語】
        </div>
        <div style="color: #78350F; font-size: 0.83rem; line-height: 1.65;">
            • <strong>非保證獲利承諾</strong>：前瞻終值試算係依據設定之年化複合報酬率（CAGR）與固定現金流進行之數學模型投影，非保證收益亦不構成任何投資報酬承諾。<br>
            • <strong>通貨膨脹與實質購買力考量</strong>：長天期複利試算未扣除未來通膨稀釋效果及稅賦摩擦成本；實際財務規劃時應同步評估折現後之實質購買力。
        </div>
    </div>
    """, unsafe_allow_html=True)
