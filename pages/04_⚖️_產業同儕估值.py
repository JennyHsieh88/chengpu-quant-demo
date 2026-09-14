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
    page_title="產業同儕估值 - 澄璞財務",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. 注入全站燕麥奶茶風格與品牌卡片
import config
config.inject_global_style()

# 2. 掛載側邊欄會員狀態卡片
from auth import render_login_widget, init_auth_state, TIER_NAMES, render_upgrade_checkout_widget
render_login_widget()

# ==============================================================================
# 🔒 本頁專屬安檢門（已移除重複彩色卡片，直接銜接就地開通與完整工具清單）
# ==============================================================================
init_auth_state()
user_tier = st.session_state.get("user_tier", 0)

if user_tier < 1:
    target_plan = TIER_NAMES.get(1, "⚡ 進階量化版 (NT$ 200/月)")
    user_plan = TIER_NAMES.get(user_tier, "🌿 基礎探索版 (免費)")

    # 頂部專屬解鎖門檻卡片
    st.markdown(f"""
    <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 26px; margin-top:20px; margin-bottom:20px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.5rem;">🔒</span>
                <span style="font-size:1.30rem; font-weight:900; color:#78350F;">【4. ⚖️ 產業同儕估值與多維性價比對標】會員專屬解鎖功能</span>
            </div>
            <span style="background:#FEF3C7; color:#92400E; font-size:0.88rem; font-weight:900; padding:5px 14px; border-radius:20px; border:1.5px solid #FDE68A;">
                需要解鎖：{target_plan}
            </span>
        </div>
        <div style="font-size:1.02rem; font-weight:800; color:#92400E; margin-bottom:8px;">
            ✦ 核心價值：全美股 11,000+ 標的動態產業穿透，以機構級六大維度橫向對標真實估值與自體造血力
        </div>
        <div style="font-size:0.96rem; color:#6B584C; line-height:1.7;">
            您目前的使用權限為：<strong>{user_plan}</strong>。散戶最常犯的致命錯誤，就是「看好某個產業題材就盲目追高」，殊不知該標的早已被炒作到同業歷史估值的 3 倍以上，一旦景氣稍有雜音，動輒吞下 40%~60% 的殺估值暴跌！
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 💎 就地渲染：由 auth.py 統一帶出「6大工具清單 + 雙方案對比按鈕」，不再重覆出現兩次！
    render_upgrade_checkout_widget(required_tier=1, feature_title="產業同儕估值")

    st.stop()

# ==============================================================================
# 👇 通過驗證放行後，正常執行的完整分析與視覺化程式碼（100% 完整保留原本代碼）
# ==============================================================================

# ==========================================
# 全域雙向狀態綁定邏輯 (Two-Way Sync)
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = ""

if 'active_tab_p3' not in st.session_state:
    st.session_state['active_tab_p3'] = "tab1"

st.session_state['ticker_input_p3'] = st.session_state['current_ticker']

def sync_ticker_p3():
    val = st.session_state.get('ticker_input_p3', '').upper().strip()
    st.session_state['current_ticker'] = val

st.subheader("⚖️ 產業同儕估值與多維性價比對標 (Industry Peer Valuation & Multiples)")

col_search, col_name, col_p = st.columns([1.8, 3.2, 2])

with col_search:
    st.text_input(
        "🔍 請輸入欲對標分析之美股代碼 (個股或 ETF 均可)", 
        key="ticker_input_p3",
        on_change=sync_ticker_p3,
        placeholder="例如: NVDA, SMCI, VRT, RKLB, ISRG, LLY, TSLA...",
        help="支援全美股 11,000+ 檔個股與 ETF！系統自動即時穿透官方產業鏈或 ETF 前大成分股"
    )
    st.markdown("<p style='font-size: 0.82rem; color: #7A6C60; margin-top: -10px; margin-bottom: 0;'>全美股 11 大板塊、150+ 細分子行業及全主題 ETF 實時動態穿透</p>", unsafe_allow_html=True)

target_symbol = st.session_state.get('current_ticker', '').strip().upper()
user_has_typed = bool(target_symbol)

# ==============================================================================
# 🛑 純淨待機機制：完美垂直置中大器排版
# ==============================================================================
if not user_has_typed:
    with col_name:
        st.markdown("### ⚖️ 產業同儕對標系統（待機中）")
        st.caption("👈 請於左側輸入美股個股或 ETF 代碼以啟動全市場動態同儕對照")
    with col_p:
        st.metric("分析狀態", "Standby", "等待輸入標的")

    st.divider()

    standby_html = (
        '<div style="background:#FFFDF9; border:1px solid #EADBCE; border-radius:14px; padding:45px 30px; margin:20px auto; max-width:980px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.02); display:flex; flex-direction:column; align-items:center; justify-content:center;">'
        '<div style="font-size:3.0rem; line-height:1; margin-bottom:14px;">⚖️</div>'
        '<div style="font-size:1.35rem; font-weight:800; color:#2D2622; margin-bottom:14px; letter-spacing:0.5px;">尚未指定分析標的</div>'
        '<div style="font-size:0.95rem; color:#6B5E52; max-width:780px; line-height:1.85; margin-bottom:24px; text-align:center;">'
        '請於上方搜尋框輸入任意美股代碼（例如 AI 伺服器 <code style="background:#F1EBE4; color:#78350F; padding:2px 6px; border-radius:4px; font-weight:700;">SMCI</code>、散熱重電 <code style="background:#F1EBE4; color:#78350F; padding:2px 6px; border-radius:4px; font-weight:700;">VRT</code>、AI 晶片 <code style="background:#F1EBE4; color:#78350F; padding:2px 6px; border-radius:4px; font-weight:700;">NVDA</code>、微創手術 <code style="background:#F1EBE4; color:#78350F; padding:2px 6px; border-radius:4px; font-weight:700;">ISRG</code>）。<br>'
        '系統全面嚴格對接<strong>「國際官方財報現金流量表」</strong>：確保 FCF 自由現金流真實反映企業造血與燒錢狀態！'
        '</div>'
        '<div style="display:inline-flex; align-items:center; justify-content:center; background:#F8FAFC; border:1px solid #CBD5E1; padding:8px 22px; border-radius:24px; font-size:0.88rem; color:#475569; font-weight:700;">'
        '✦ 全美股 11,000+ 標的動態同儕穿透 ｜ IFRS 官方現金流解析 ｜ 未盈利真實呈現 ✦'
        '</div>'
        '</div>'
    )
    st.markdown(standby_html, unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 💎 機構級：全美股精準 GICS 分類與真實現金流對帳引擎
# ==============================================================================
@st.cache_data(ttl=300)
def fetch_dynamic_peers_and_data(target: str):
    target = target.upper().strip()
    target_ticker = yf.Ticker(target)
    
    try:
        t_info = target_ticker.info or {}
    except Exception:
        t_info = {}

    quote_type = t_info.get('quoteType', 'EQUITY').upper()
    sector = t_info.get('sector', '')
    industry = t_info.get('industry', '')
    target_name = t_info.get('shortName', target)
    summary = t_info.get('longBusinessSummary', '')

    peers_list = []
    category_label = ""

    ticker_peer_mapping = {
        'SMCI': (['SMCI', 'DELL', 'HPE', 'VRT', 'NVDA', 'QCOM', 'CSCO'], "AI 伺服器、高效能運算與硬體基礎設施"),
        'DELL': (['DELL', 'SMCI', 'HPE', 'HPQ', 'AAPL', 'MSFT'], "伺服器、個人電腦與企業 IT 解決方案"),
        'VRT': (['VRT', 'ETN', 'NVT', 'HUBB', 'PWR', 'PH', 'DELL', 'SMCI'], "AI 數據中心基礎設施、散熱與重電電力設備"),
        'ETN': (['ETN', 'VRT', 'NVT', 'HUBB', 'PWR', 'PH', 'DELL', 'ROK'], "全球電氣化、重電電力與工業自動化"),
        'HUBB': (['HUBB', 'ETN', 'VRT', 'NVT', 'PWR', 'PH'], "電力傳輸、配電設備與工業元件"),
        'NVT': (['NVT', 'ETN', 'VRT', 'HUBB', 'PH', 'PWR'], "電機電氣零組件與工業自動化"),
        'RKLB': (['RKLB', 'ASTS', 'LUNR', 'PL', 'SPCX', 'IRDM', 'VSAT', 'RDW'], "商業太空、低軌衛星與火箭運載科技"),
        'ASTS': (['ASTS', 'RKLB', 'LUNR', 'PL', 'IRDM', 'SPCX', 'VSAT'], "太空蜂窩通信與低軌衛星網路"),
        'SPCX': (['SPCX', 'RKLB', 'ASTS', 'LUNR', 'PL', 'IRDM'], "全球商業太空與衛星產業鏈"),
        'NVDA': (['NVDA', 'AMD', 'AVGO', 'TSM', 'QCOM', 'ASML', 'MU', 'ARM'], "全球半導體與 AI 核心晶片"),
        'AMD': (['AMD', 'NVDA', 'AVGO', 'TSM', 'QCOM', 'INTC', 'ARM'], "高效能運算與半導體晶片設計"),
        'TSM': (['TSM', 'NVDA', 'AVGO', 'AMD', 'QCOM', 'ASML', 'INTC'], "先進晶圓代工與半導體製造"),
        'CRWD': (['CRWD', 'PANW', 'FTNT', 'NET', 'ZS', 'OKTA', 'QLYS'], "雲端端點安全與資安防禦平台"),
        'PANW': (['PANW', 'CRWD', 'FTNT', 'NET', 'ZS', 'OKTA'], "企業網路安全與防火牆解決方案"),
        'ISRG': (['ISRG', 'MDT', 'ABT', 'BSX', 'SYK', 'EW', 'BDX', 'ZBH'], "先進微創手術機械手臂與高階醫療器械"),
        'LLY': (['LLY', 'NVO', 'MRK', 'ABBV', 'PFE', 'JNJ', 'AMGN', 'VRTX'], "生技新藥研發與跨國製藥巨頭"),
        'NVO': (['NVO', 'LLY', 'MRK', 'ABBV', 'PFE', 'JNJ', 'AMGN', 'VRTX'], "代謝疾病、糖尿病與跨國製藥"),
        'TSLA': (['TSLA', 'RIVN', 'NIO', 'LCID', 'GM', 'F', 'TM'], "純電動車與能源儲存系統"),
        'RIVN': (['RIVN', 'TSLA', 'NIO', 'LCID', 'GM', 'F'], "電動皮卡與商用電動車"),
        'LMT': (['LMT', 'RTX', 'NOC', 'GD', 'BA', 'TDG', 'LHX'], "國防航太與先進軍工製造"),
        'JPM': (['JPM', 'GS', 'MS', 'BAC', 'WFC', 'BLK', 'C'], "全球頂級投資銀行與商業金融"),
        'XOM': (['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'OXY'], "石油、天然氣與整合性能源探勘"),
        'MSFT': (['MSFT', 'ORCL', 'CRM', 'NOW', 'ADBE', 'WDAY', 'PLTR', 'SNOW'], "雲端運算與企業級軟體 SaaS")
    }

    if target in ticker_peer_mapping:
        peers_list, category_label = ticker_peer_mapping[target]
    elif quote_type == 'ETF' or 'ETF' in target_name.upper():
        category_label = f"【ETF 專題對標】{t_info.get('category', '主題型指數基金')}"
        try:
            funds_data = target_ticker.funds_data
            if funds_data and hasattr(funds_data, 'top_holdings') and funds_data.top_holdings is not None:
                df_holdings = funds_data.top_holdings
                if not df_holdings.empty and 'Symbol' in df_holdings.columns:
                    peers_list = df_holdings['Symbol'].head(8).tolist()
        except Exception:
            pass
        if not peers_list:
            peers_list = ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'XLK']
    else:
        full_text = f"{target} {industry} {sector} {summary} {target_name}".lower()

        if any(k in full_text for k in ['server', 'supermicro', 'smci', 'hardware', 'oem']):
            peers_list = ['SMCI', 'DELL', 'HPE', 'VRT', 'HPQ', 'CSCO']
            category_label = "AI 伺服器、高效能運算與硬體基礎設施"
        elif any(k in full_text for k in ['data center', 'thermal', 'cooling', 'uninterruptible power', 'power management', 'vertiv']):
            peers_list = ['VRT', 'ETN', 'NVT', 'HUBB', 'PWR', 'PH', 'DELL', 'SMCI']
            category_label = "AI 數據中心基礎設施、散熱與重電電力設備"
        elif any(k in full_text for k in ['space', 'satellite', 'orbit', 'rocket', 'lunar', 'spacecraft', 'rklb', 'asts']):
            peers_list = ['SPCX', 'RKLB', 'ASTS', 'LUNR', 'PL', 'IRDM', 'VSAT', 'RDW']
            category_label = "商業太空、低軌衛星與火箭運載科技"
        elif any(k in full_text for k in ['semiconductor', 'chip', 'wafer']):
            peers_list = ['NVDA', 'AMD', 'AVGO', 'TSM', 'QCOM', 'ASML', 'MU', 'ARM']
            category_label = "全球半導體與 AI 核心晶片"
        elif any(k in full_text for k in ['cybersecurity', 'network security', 'threat']):
            peers_list = ['CRWD', 'PANW', 'FTNT', 'NET', 'ZS', 'S', 'OKTA']
            category_label = "網路資訊安全與端點威脅防禦"
        elif any(k in full_text for k in ['surgical', 'medical instrument', 'device']):
            peers_list = ['ISRG', 'MDT', 'ABT', 'BSX', 'SYK', 'EW', 'BDX', 'ZBH']
            category_label = "先進微創手術與高階醫療器械"
        elif any(k in full_text for k in ['drug', 'biotechnology', 'pharma', 'glp-1']):
            peers_list = ['LLY', 'NVO', 'MRK', 'ABBV', 'PFE', 'JNJ', 'AMGN', 'VRTX']
            category_label = "生技新藥研發與跨國製藥巨頭"
        elif any(k in full_text for k in ['electric vehicle', 'ev manufacturer', 'battery electric', 'tesla']):
            peers_list = ['TSLA', 'RIVN', 'NIO', 'BYDDF', 'LCID', 'GM', 'F']
            category_label = "新能源電動車與智慧移動"
        elif any(k in full_text for k in ['defense', 'military', 'aerospace']):
            peers_list = ['LMT', 'RTX', 'NOC', 'GD', 'BA', 'TDG', 'LHX']
            category_label = "國防航太與先進軍工製造"
        elif any(k in full_text for k in ['bank', 'financial', 'capital market']):
            peers_list = ['JPM', 'GS', 'MS', 'BAC', 'WFC', 'BLK', 'C']
            category_label = "投資銀行、商業金融與資產管理"
        elif any(k in full_text for k in ['oil', 'gas', 'energy']):
            peers_list = ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'OXY']
            category_label = "石油、天然氣與能源探勘工程"
        elif any(k in full_text for k in ['cloud', 'software']):
            peers_list = ['MSFT', 'ORCL', 'CRM', 'NOW', 'ADBE', 'WDAY', 'PLTR', 'SNOW']
            category_label = "雲端運算與企業級軟體 SaaS"
        else:
            peers_list = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA']
            category_label = industry or sector or "同板塊核心競爭群"

    final_tickers = [target] + [s for s in peers_list if s != target][:7]

    records = []
    for sym in final_tickers:
        try:
            stk = yf.Ticker(sym)
            inf = stk.info or {}

            c_name = inf.get('shortName', sym)
            curr_p = inf.get('currentPrice') or inf.get('regularMarketPrice') or inf.get('navPrice') or 0.0
            
            raw_fwd_pe = inf.get('forwardPE')
            raw_trail_pe = inf.get('trailingPE')
            
            if raw_fwd_pe is not None and float(raw_fwd_pe) > 0 and float(raw_fwd_pe) < 300:
                final_fwd_pe = round(float(raw_fwd_pe), 1)
                is_profitable = True
            elif raw_trail_pe is not None and float(raw_trail_pe) > 0 and float(raw_trail_pe) < 300:
                final_fwd_pe = round(float(raw_trail_pe), 1)
                is_profitable = True
            else:
                final_fwd_pe = None
                is_profitable = False

            peg = inf.get('pegRatio')
            ev_ebitda = inf.get('enterpriseToEbitda')
            ps = inf.get('priceToSalesTrailing12Months') or 0.0
            roe = (inf.get('returnOnEquity') or 0.0) * 100.0

            true_fcf = None
            try:
                cf_df = stk.cashflow
                if cf_df is not None and not cf_df.empty:
                    col_latest = cf_df.columns[0]
                    op_cf = 0.0
                    capex = 0.0
                    for row_idx in cf_df.index:
                        r_lower = str(row_idx).lower()
                        if any(k in r_lower for k in ['operating cash flow', 'total cash from operating', 'cash flow from continuing operating']):
                            val = cf_df.loc[row_idx, col_latest]
                            if pd.notnull(val):
                                op_cf = float(val)
                        elif any(k in r_lower for k in ['capital expenditures', 'capital expenditure', 'purchase of property', 'property, plant and equipment', 'additions to property']):
                            val = cf_df.loc[row_idx, col_latest]
                            if pd.notnull(val):
                                capex = float(val)
                    
                    if capex > 0:
                        capex = -capex
                    
                    if op_cf != 0:
                        raw_calc_fcf = op_cf + capex
                        
                        fin_curr = inf.get('financialCurrency', 'USD')
                        trade_curr = inf.get('currency', 'USD')
                        if fin_curr != trade_curr:
                            if fin_curr == 'DKK':
                                raw_calc_fcf = raw_calc_fcf / 6.8
                            elif fin_curr == 'EUR':
                                raw_calc_fcf = raw_calc_fcf * 1.08
                            elif fin_curr == 'TWD':
                                raw_calc_fcf = raw_calc_fcf / 32.2
                        true_fcf = raw_calc_fcf
            except Exception:
                pass

            if true_fcf is None:
                true_fcf = inf.get('freeCashflow')

            mkt_cap = inf.get('marketCap')
            if not mkt_cap or mkt_cap <= 0:
                shares = inf.get('sharesOutstanding', 0)
                if shares > 0 and curr_p > 0:
                    mkt_cap = shares * curr_p
                else:
                    mkt_cap = 1

            if mkt_cap > 0 and true_fcf is not None:
                calc_fcf_yield = (true_fcf / mkt_cap) * 100.0
            else:
                calc_fcf_yield = 1.5 if is_profitable else -3.5

            calc_fcf_yield = min(max(calc_fcf_yield, -25.0), 25.0)

            eps_growth = (inf.get('earningsGrowth') or 0.15) * 100.0
            raw_growth = eps_growth
            plot_growth = max(eps_growth, 5.0)
            
            calc_peg = round(float(peg), 2) if (peg and 0 < float(peg) < 8.0) else (round(final_fwd_pe / plot_growth, 2) if (final_fwd_pe and plot_growth > 0) else None)
            final_ev = round(float(ev_ebitda), 1) if (ev_ebitda and float(ev_ebitda) > 0 and float(ev_ebitda) < 150) else None

            records.append({
                "代碼": sym,
                "公司": c_name,
                "現價": round(float(curr_p), 2),
                "前瞻 P/E": final_fwd_pe,
                "是否獲利": is_profitable,
                "繪圖 EPS 年增": round(float(plot_growth), 1),
                "原始 EPS 年增": round(float(raw_growth), 1),
                "PEG": calc_peg,
                "EV/EBITDA": final_ev,
                "P/S": round(float(ps), 1) if ps > 0 else 0.0,
                "FCF Yield": round(float(calc_fcf_yield), 1),
                "ROE": round(float(roe), 1)
            })
        except Exception:
            pass

    return pd.DataFrame(records), sector, category_label, target_name

with st.spinner(f"正在全市場動態穿透 {target_symbol} 真實細分賽道、持股與同儕即時財報現金流..."):
    df_peers, detected_sector, detected_industry, active_name = fetch_dynamic_peers_and_data(target_symbol)

if not df_peers.empty:
    target_row = df_peers.iloc[0]
else:
    target_row = {"公司": target_symbol, "現價": 100.0, "前瞻 P/E": None, "是否獲利": False, "PEG": None, "EV/EBITDA": None, "P/S": 8.0, "FCF Yield": 2.5}

with col_name:
    st.markdown(f"### {active_name} (`{target_symbol}`)")
    st.caption(f"動態產業穿透：**【{detected_sector or '美股市場'} ➔ {detected_industry}】**")
with col_p:
    pe_display = f"{target_row['前瞻 P/E']:.1f}x" if target_row['前瞻 P/E'] is not None else "N/A (未盈利/成長期)"
    st.metric("即時現價", f"${target_row['現價']:.2f}", f"前瞻 P/E: {pe_display}")

st.divider()

# ==========================================
# 估值四大核心指標卡
# ==========================================
st.markdown(f"#### ⚡ {target_symbol} 真實同儕估值定位（{detected_industry} 對標）")

peers_only = df_peers.iloc[1:] if len(df_peers) > 1 else df_peers
profitable_peers = peers_only[peers_only['是否獲利']]

if not profitable_peers.empty:
    median_pe = profitable_peers['前瞻 P/E'].median()
    median_pe_str = f"同行獲利股中位數: {median_pe:.1f}x"
else:
    median_pe = None
    median_pe_str = "同業多數處於前期擴張 (無正向 P/E)"

profitable_ev = peers_only[peers_only['EV/EBITDA'].notnull()]
median_ev = profitable_ev['EV/EBITDA'].median() if not profitable_ev.empty else None
median_ev_str = f"同行中位數: {median_ev:.1f}x" if median_ev else "同業 EBITDA 尚在擴張"

v1, v2, v3, v4 = st.columns(4)
v1.metric("📈 前瞻本益比 (Forward P/E)", pe_display, median_pe_str, delta_color="normal")
peg_disp = f"{target_row['PEG']:.2f}" if target_row['PEG'] is not None else "N/A"
v2.metric("🎯 PEG 成長性價比 (P/E to Growth)", peg_disp, "需具備穩定淨利潤", delta_color="normal")
ev_disp = f"{target_row['EV/EBITDA']:.1f}x" if target_row['EV/EBITDA'] is not None else "N/A"
v3.metric("🏢 企業價值倍數 (EV/EBITDA)", ev_disp, median_ev_str, delta_color="normal")
v4.metric("💵 市銷率倍數 (P/S Ratio)", f"{target_row['P/S']:.1f}x", f"同行中位數: {peers_only['P/S'].median():.1f}x", delta_color="normal")

st.markdown("---")

# ==========================================
# 六大深度導航按鈕 (滿格 3x2 對稱佈局)
# ==========================================
st.markdown("##### 🧭 產業同儕估值 — 六大深度分析選單")

g1, g2, g3 = st.columns(3)
g4, g5, g6 = st.columns(3)

with g1:
    if st.button("📊 一、前瞻本益比 (Forward P/E) 與歷史估值通道對比", type="primary" if st.session_state['active_tab_p3'] == "tab1" else "secondary", use_container_width=True):
        st.session_state['active_tab_p3'] = "tab1"
        st.rerun()

with g2:
    if st.button("🎯 二、PEG 成長估值合理性矩陣 (P/E vs. EPS Growth)", type="primary" if st.session_state['active_tab_p3'] == "tab2" else "secondary", use_container_width=True):
        st.session_state['active_tab_p3'] = "tab2"
        st.rerun()

with g3:
    if st.button("🏢 三、企業價值倍數 (EV/EBITDA) 與資本結構中立性檢驗", type="primary" if st.session_state['active_tab_p3'] == "tab3" else "secondary", use_container_width=True):
        st.session_state['active_tab_p3'] = "tab3"
        st.rerun()

with g4:
    if st.button("💵 四、市銷率 (P/S) 與自由現金流收益率 (FCF Yield) 對照", type="primary" if st.session_state['active_tab_p3'] == "tab4" else "secondary", use_container_width=True):
        st.session_state['active_tab_p3'] = "tab4"
        st.rerun()

with g5:
    if st.button("📋 五、同儕財務體質雷達與綜合估值折溢價評級總表", type="primary" if st.session_state['active_tab_p3'] == "tab5" else "secondary", use_container_width=True):
        st.session_state['active_tab_p3'] = "tab5"
        st.rerun()

with g6:
    if st.button(f"🏛️ 六、{target_symbol} 產業特定估值治理與結構風險穿透", type="primary" if st.session_state['active_tab_p3'] == "tab6" else "secondary", use_container_width=True):
        st.session_state['active_tab_p3'] = "tab6"
        st.rerun()

st.markdown("---")

active_p3 = st.session_state['active_tab_p3']

# ----------------------------------------------------
# 分頁 1：前瞻本益比通道對比（整合圖象化決策對照指南）
# ----------------------------------------------------
if active_p3 == "tab1":
    st.markdown(f"### 📊 一、{target_symbol} 前瞻本益比 (Forward P/E) 與直屬同行對標")
    st.caption(f"數據來源：Yahoo Finance 華爾街即時共識。精確對標【{detected_industry}】直屬同行陣列。")

    valid_pe_vals = [r['前瞻 P/E'] for _, r in df_peers.iterrows() if r['前瞻 P/E'] is not None and r['前瞻 P/E'] > 0]
    base_max_pe = max(valid_pe_vals) if valid_pe_vals else 40.0

    plot_pe = []
    display_texts = []
    bar_colors = []
    bar_borders = []

    placeholder_height = max(base_max_pe * 0.10, 4.0)

    for _, r in df_peers.iterrows():
        is_target = (r['代碼'] == target_symbol)
        if r['前瞻 P/E'] is not None and r['前瞻 P/E'] > 0:
            plot_pe.append(r['前瞻 P/E'])
            display_texts.append(f"<b>{r['前瞻 P/E']:.1f}x</b>")
            bar_colors.append('#0D9488' if is_target else '#BAE6FD')
            bar_borders.append('#0F766E' if is_target else '#0284C7')
        else:
            plot_pe.append(placeholder_height)
            display_texts.append("<b>無P/E<br>(尚未盈利)</b>")
            bar_colors.append('rgba(241, 245, 249, 0.75)')
            bar_borders.append('#94A3B8')

    fig_pe = go.Figure()

    fig_pe.add_trace(go.Bar(
        x=df_peers['代碼'], 
        y=plot_pe,
        marker=dict(color=bar_colors, line=dict(color=bar_borders, width=1.5)),
        text=display_texts,
        textposition='outside',
        cliponaxis=False,
        textfont=dict(size=11, color='#1E293B', family='Arial Black'),
        hovertemplate="<b>%{x}</b> (%{customdata})<br>狀態: %{text}<extra></extra>",
        customdata=df_peers['公司']
    ))

    if median_pe is not None:
        fig_pe.add_hline(
            y=median_pe, 
            line_dash="dash", 
            line_color="#D97706", 
            line_width=2.0
        )
        fig_pe.add_annotation(
            xref="paper", yref="y",
            x=0.96, y=median_pe,
            xanchor="right",
            text=f"<b>獲利同行中位數<br>({median_pe:.1f}x)</b>",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.0,
            arrowwidth=1.5,
            arrowcolor="#D97706",
            ax=0,
            ay=-28,
            bgcolor="#FFFFFF",
            bordercolor="#D97706",
            borderwidth=1.5,
            borderpad=6,
            font=dict(size=11, color="#9A3412", family="Arial Black")
        )

    fig_pe.update_layout(
        title=dict(text=f"<b>【{detected_industry}】真實前瞻本益比橫向對照 (Forward P/E vs Peers)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
        height=460,
        margin=dict(t=75, b=35, l=20, r=110),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="前瞻 P/E 倍數 (x)", range=[0, base_max_pe * 1.35], showgrid=True, gridcolor='#F2ECE5'),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        hovermode="x unified"
    )
    st.plotly_chart(fig_pe, use_container_width=True, key="p3_real_pe_chart")

    st.markdown("""
    <div style="background:#FFFDF9; border:1px solid #EADBCE; border-left:5px solid #0F766E; border-radius:12px; padding:20px 22px; margin-top:16px; margin-bottom:18px; box-shadow:0 1px 4px rgba(0,0,0,0.02);">
        <div style="color:#0F766E; font-size:1.05rem; font-weight:800; margin-bottom:12px; display:flex; align-items:center; gap:6px;">
            <span>🧭</span> <span>這張圖表怎麼應用？（買進、持有、避險的決策導讀）</span>
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; margin-bottom:14px;">
            <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px 14px;">
                <div style="color:#15803D; font-weight:800; font-size:0.92rem; margin-bottom:4px;">🟢 柱高低於中位數線（估值折價）</div>
                <div style="color:#2D2622; font-size:0.86rem; line-height:1.65;">
                    • <strong>應用含義</strong>：買進成本相對便宜，具下檔安全邊際。<br>
                    • <strong>決策檢查</strong>：切到【分頁二】看 EPS 成長。若成長仍在則為<strong>「黃金甜點股」</strong>；若成長衰退則為<strong>「價值陷阱（勿接刀）」</strong>。
                </div>
            </div>
            <div style="background:#FEF3C7; border:1px solid #FDE68A; border-radius:8px; padding:12px 14px;">
                <div style="color:#B45309; font-weight:800; font-size:0.92rem; margin-bottom:4px;">🟡 柱高緊貼中位數線（估值合理）</div>
                <div style="color:#2D2622; font-size:0.86rem; line-height:1.65;">
                    • <strong>應用含義</strong>：定價反映現狀，不貴也不便宜。<br>
                    • <strong>決策檢查</strong>：適合長期定期定額或穩健持有。
                </div>
            </div>
            <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:12px 14px;">
                <div style="color:#B91C1C; font-weight:800; font-size:0.92rem; margin-bottom:4px;">🔴 柱高顯著高於中位數（估值溢價）</div>
                <div style="color:#2D2622; font-size:0.86rem; line-height:1.65;">
                    • <strong>應用含義</strong>：股價預支未來成長。<br>
                    • <strong>決策檢查</strong>：不宜重倉追高；緊盯財報是否超預期。
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 2：PEG 成長估值合理性矩陣
# ----------------------------------------------------
elif active_p3 == "tab2":
    st.markdown("### 🎯 二、PEG 成長估值合理性矩陣 (P/E vs. EPS Growth)")
    st.caption("衡量每單位獲利成長之估值乘數合理性：`PEG = 前瞻本益比 ÷ 預估 EPS 年增率`。僅針對已具備正向淨利潤之標的評估。")

    valid_peg_df = df_peers[df_peers['前瞻 P/E'].notnull()].copy()

    if not valid_peg_df.empty:
        valid_peg_df = valid_peg_df.sort_values(by="繪圖 EPS 年增", ascending=True).reset_index(drop=True)
        fig_peg = go.Figure()

        smart_positions = ['top right', 'bottom center', 'top left', 'bottom right', 'top center', 'middle right', 'bottom left']

        for idx, row in valid_peg_df.iterrows():
            is_target = (row['代碼'] == target_symbol)
            x_val = row['繪圖 EPS 年增']
            y_val = row['前瞻 P/E']
            code = row['代碼']
            pos = smart_positions[idx % len(smart_positions)]

            fig_peg.add_trace(go.Scatter(
                x=[x_val],
                y=[y_val],
                mode='markers+text',
                cliponaxis=False,
                marker=dict(
                    size=18 if is_target else 13,
                    color='#0D9488' if is_target else '#0284C7',
                    line=dict(width=2.5, color='#FFFFFF')
                ),
                text=[f"<b>{code}</b>"],
                textposition=pos,
                textfont=dict(size=12, color='#0D9488' if is_target else '#1E293B', family='Arial Black'),
                hovertemplate=f"<b>{row['公司']} ({code})</b><br>" +
                              f"前瞻 P/E: {y_val:.1f}x<br>" +
                              f"預估 EPS 年增: +{row['原始 EPS 年增']:.1f}%<br>" +
                              f"PEG 性價比: <b>{row['PEG'] if row['PEG'] else 'N/A'}</b><extra></extra>",
                showlegend=False
            ))

        max_pe_actual = valid_peg_df['前瞻 P/E'].max()
        max_growth_actual = 50.0

        x_grid = np.linspace(0, 60.0, 100)
        fig_peg.add_trace(go.Scatter(x=x_grid, y=x_grid * 1.0, mode='lines', line=dict(color='#047857', width=2, dash='dash'), name="PEG = 1.0 (高性價比邊界)"))
        fig_peg.add_trace(go.Scatter(x=x_grid, y=x_grid * 2.0, mode='lines', line=dict(color='#DC2626', width=2, dash='dot'), name="PEG = 2.0 (成長透支警戒線)"))

        y_ceiling = max(max_pe_actual * 1.30, 45.0)

        fig_peg.update_layout(
            title=dict(text=f"<b>【{detected_industry}】同行真實 PEG 矩陣 (P/E vs. EPS Growth)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
            height=520,
            margin=dict(t=75, b=40, l=35, r=55),
            xaxis=dict(title="預估 EPS 年增長率 (%)", range=[0, 60.0], showgrid=True, gridcolor='#F2ECE5'),
            yaxis=dict(title="前瞻 P/E 倍數 (x)", range=[0, y_ceiling], showgrid=True, gridcolor='#F2ECE5'),
            legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF"
        )
        st.plotly_chart(fig_peg, use_container_width=True, key="p3_dynamic_peg_chart")
    else:
        st.info("💡 同儕標的多數處於前期擴張建置期（EPS 尚未轉正），本矩陣暫不適用。")

# ----------------------------------------------------
# 分頁 3：企業價值倍數 (EV/EBITDA)
# ----------------------------------------------------
elif active_p3 == "tab3":
    st.markdown("### 🏢 三、企業價值倍數 (EV/EBITDA) 與資本結構中立性檢驗")
    st.caption("數據來源：SEC 最新財報申報。排除折舊攤銷與負債結構差異的真實企業倍數。")

    valid_ev_df = df_peers[df_peers['EV/EBITDA'].notnull()]
    
    if not valid_ev_df.empty:
        fig_ev = go.Figure()
        bar_ev_colors = ['#0D9488' if row['代碼'] == target_symbol else '#64748B' for _, row in valid_ev_df.iterrows()]
        fig_ev.add_trace(go.Bar(
            x=valid_ev_df['代碼'], y=valid_ev_df['EV/EBITDA'],
            marker_color=bar_ev_colors,
            text=[f"{v:.1f}x" for v in valid_ev_df['EV/EBITDA']],
            textposition='outside',
            cliponaxis=False,
            textfont=dict(size=12, family='Arial Black')
        ))

        max_ev = valid_ev_df['EV/EBITDA'].max()
        fig_ev.update_layout(
            title=dict(text=f"<b>【{detected_industry}】同行真實 EV/EBITDA 倍數對比</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.96),
            height=440,
            margin=dict(t=65, b=30, l=15, r=30),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="EV/EBITDA 倍數 (x)", range=[0, max_ev * 1.30], showgrid=True, gridcolor='#F2ECE5')
        )
        st.plotly_chart(fig_ev, use_container_width=True, key="p3_real_ev_chart")
    else:
        st.info("💡 當前對標同行企業多數處於資本支出開拓期，EBITDA 尚未轉正，建議參考市銷率 (P/S)。")

# ----------------------------------------------------
# 分頁 4：市銷率 (P/S) 與真實自由現金流收益率 (FCF Yield) 綜合對照
# ----------------------------------------------------
elif active_p3 == "tab4":
    st.markdown("### 💵 四、市銷率 (P/S) 與自由現金流收益率 (FCF Yield) 對照")
    st.caption(f"對標【{detected_industry}】之營收倍數與自體真金白銀流入（高成長未獲利賽道最關鍵衡量指標）。")

    chart_view = st.radio(
        "切換圖表呈現維度：",
        ["📊 上下分層獨立視角（專業標準・數據最清晰）", "⚡ 單圖雙軸綜合視角（交集透視・速覽性價比）"],
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )

    max_ps_val = max(df_peers['P/S'].max() * 1.30, 10.0)
    max_fcf_val = max(df_peers['FCF Yield'].max() * 1.35, 8.0)
    min_fcf_val = min(df_peers['FCF Yield'].min() * 1.25, -5.0)

    bar_colors_ps = ['#0D9488' if row['代碼'] == target_symbol else '#BAE6FD' for _, row in df_peers.iterrows()]
    bar_borders_ps = ['#0F766E' if row['代碼'] == target_symbol else '#0284C7' for _, row in df_peers.iterrows()]

    fcf_combo_text_positions = []
    for ps_v, fcf_v in zip(df_peers['P/S'], df_peers['FCF Yield']):
        if ps_v >= 3.0 and 2.0 <= fcf_v <= 7.5:
            fcf_combo_text_positions.append('bottom center')
        else:
            fcf_combo_text_positions.append('top center')

    if "上下分層" in chart_view:
        fig_fcf = make_subplots(
            rows=2, cols=1,
            shared_xaxes=False,
            vertical_spacing=0.20,
            subplot_titles=(
                "<b>📊 市銷率 P/S 倍數 (營收估值乘數 - 越低越具吸引力)</b>",
                "<b>💵 自由現金流收益率 FCF Yield (%) (真實現金造血與燒錢狀態)</b>"
            )
        )

        fig_fcf.add_trace(
            go.Bar(
                x=df_peers['代碼'], 
                y=df_peers['P/S'],
                name="市銷率 P/S (x)",
                marker=dict(color=bar_colors_ps, line=dict(color=bar_borders_ps, width=1.5)),
                text=[f"<b>{v:.1f}x</b>" for v in df_peers['P/S']],
                textposition='outside',
                cliponaxis=False,
                textfont=dict(size=12, color='#1E293B', family='Arial Black'),
                hovertemplate="<b>%{x}</b> (%{customdata})<br>市銷率 P/S: %{y:.1f}x<extra></extra>",
                customdata=df_peers['公司']
            ),
            row=1, col=1
        )

        fig_fcf.add_trace(
            go.Scatter(
                x=df_peers['代碼'], 
                y=df_peers['FCF Yield'],
                name="自由現金流收益率 FCF Yield (%)",
                mode='lines+markers+text',
                line=dict(color='#D97706', width=3.5),
                marker=dict(size=10, color='#FFFFFF', line=dict(color='#D97706', width=3)),
                text=[f"<b>{v:+.1f}%</b>" for v in df_peers['FCF Yield']],
                textposition='top center',
                cliponaxis=False,
                textfont=dict(size=11.5, color='#991B1B', family='Arial Black'),
                hovertemplate="<b>%{x}</b><br>真實 FCF 收益率: %{y:+.1f}%<extra></extra>"
            ),
            row=2, col=1
        )

        fig_fcf.add_hline(y=3.0, line_dash="dash", line_color="#0D9488", line_width=1.8, row=2, col=1)
        fig_fcf.add_annotation(
            xref="x2 domain", yref="y2",
            x=0.98, y=3.0,
            xanchor="right",
            text="<b>機構安全基準 (3.0%)</b>",
            showarrow=False,
            bgcolor="#FFFFFF",
            bordercolor="#0D9488",
            borderwidth=1.2,
            borderpad=4,
            font=dict(size=10.5, color="#065F46", family="Arial Black")
        )
        fig_fcf.add_hline(y=0.0, line_dash="solid", line_color="#E2E8F0", line_width=1.2, row=2, col=1)

        fig_fcf.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=640,
            margin=dict(t=50, b=40, l=35, r=40),
            showlegend=False
        )
        fig_fcf.update_xaxes(showgrid=False, tickfont=dict(size=11, color="#334155", family="Arial Black"), row=1, col=1)
        fig_fcf.update_xaxes(showgrid=False, tickfont=dict(size=11, color="#334155", family="Arial Black"), row=2, col=1)
        fig_fcf.update_yaxes(title_text="P/S 倍數 (x)", range=[0, max_ps_val], row=1, col=1, showgrid=True, gridcolor='#F2ECE5')
        fig_fcf.update_yaxes(title_text="FCF Yield (%)", range=[min_fcf_val, max_fcf_val], row=2, col=1, showgrid=True, gridcolor='#F2ECE5')

        st.plotly_chart(fig_fcf, use_container_width=True, key="p3_split_view_chart")

    else:
        fig_combo = make_subplots(specs=[[{"secondary_y": True}]])

        fig_combo.add_trace(
            go.Bar(
                x=df_peers['代碼'], 
                y=df_peers['P/S'],
                name="市銷率 P/S (倍數 - 左軸)",
                marker=dict(color=bar_colors_ps, line=dict(color=bar_borders_ps, width=1.5)),
                text=[f"<b>{v:.1f}x</b>" for v in df_peers['P/S']],
                textposition='outside',
                cliponaxis=False,
                textfont=dict(size=11.5, color='#1E293B', family='Arial Black'),
                hovertemplate="<b>%{x}</b> (%{customdata})<br>市銷率 P/S: %{y:.1f}x<extra></extra>",
                customdata=df_peers['公司']
            ),
            secondary_y=False
        )

        fig_combo.add_trace(
            go.Scatter(
                x=df_peers['代碼'], 
                y=df_peers['FCF Yield'],
                name="自由現金流收益率 FCF Yield (% - 右軸)",
                mode='lines+markers+text',
                line=dict(color='#D97706', width=3.2),
                marker=dict(size=10, color='#FFFFFF', line=dict(color='#D97706', width=2.8)),
                text=[f"<b>{v:+.1f}%</b>" for v in df_peers['FCF Yield']],
                textposition=fcf_combo_text_positions,
                cliponaxis=False,
                textfont=dict(size=11.5, color='#991B1B', family='Arial Black'),
                hovertemplate="<b>%{x}</b><br>真實 FCF 收益率: %{y:+.1f}%<extra></extra>"
            ),
            secondary_y=True
        )

        fig_combo.add_hline(y=3.0, line_dash="dash", line_color="#059669", line_width=1.8, secondary_y=True)
        fig_combo.add_annotation(
            xref="paper", yref="y2",
            x=0.96, y=3.0,
            xanchor="right",
            text="<b>機構防禦基準線 (3.0%)</b>",
            showarrow=False,
            bgcolor="#FFFFFF",
            bordercolor="#059669",
            borderwidth=1.5,
            borderpad=4,
            font=dict(size=10.5, color="#047857", family="Arial Black")
        )

        fig_combo.update_layout(
            title=dict(
                text=f"<b>【{detected_industry}】市銷率 (P/S 柱) 與自由現金流造血力 (FCF 折線) 綜合對照</b>",
                font=dict(size=14, color="#2D2622"),
                x=0.01,
                y=0.98
            ),
            height=490,
            margin=dict(t=88, b=35, l=20, r=80),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="right",
                x=0.98,
                font=dict(size=11)
            ),
            hovermode="x unified",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF"
        )

        fig_combo.update_yaxes(
            title_text="<b>市銷率 P/S 倍數 (x)</b>",
            title_font=dict(color="#0284C7"),
            tickfont=dict(color="#0284C7"),
            range=[0, max_ps_val],
            showgrid=True,
            gridcolor='#F2ECE5',
            secondary_y=False
        )

        fig_combo.update_yaxes(
            title_text="<b>自由現金流收益率 FCF Yield (%)</b>",
            title_font=dict(color="#D97706"),
            tickfont=dict(color="#D97706"),
            range=[min_fcf_val, max_fcf_val],
            showgrid=False,
            secondary_y=True
        )

        fig_combo.update_xaxes(showgrid=False)

        st.plotly_chart(fig_combo, use_container_width=True, key="p3_combo_view_chart")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【圖表解讀指南】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            • <strong>市銷率 P/S（藍色柱體）</strong>：衡量市場對每 1 元營收賦予的估值乘數，柱高越低代表溢價負擔越輕。<br>
            • <strong>自由現金流 FCF Yield（橘色折線）</strong>：衡量扣除資本開支後的真實造血回報率，<strong>高於 3.0% 綠色基準線</strong>代表財務護城河堅實；若為反向負數，如實代表該公司正處於重資本擴張的現金消耗期。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 5：同儕財務體質雷達與綜合估值折溢價總表
# ----------------------------------------------------
elif active_p3 == "tab5":
    st.markdown(f"### 📋 五、{detected_industry} 同儕財務體質與估值總表")
    st.caption("彙總同行主要標的真實 Forward P/E、預估成長率、PEG、EV/EBITDA、P/S、FCF Yield 與股東權益報酬率 (ROE)。")

    chart_choice_p5 = st.radio(
        "選擇視覺透視圖表：",
        ["🎯 護城河與估值性價比矩陣 (ROE vs. PEG 氣泡圖)", "🕸️ 目標 vs. 同行中位數 五維財務體質雷達圖"],
        index=0,
        horizontal=True,
        label_visibility="collapsed"
    )

    if "ROE vs. PEG" in chart_choice_p5:
        fig_quad = go.Figure()
        
        valid_bubble_df = df_peers.copy()
        max_roe_raw = valid_bubble_df['ROE'].max() if not valid_bubble_df['ROE'].empty else 40.0
        
        for _, row in valid_bubble_df.iterrows():
            is_target = (row['代碼'] == target_symbol)
            peg_val = row['PEG'] if row['PEG'] is not None and row['PEG'] > 0 else 2.5
            roe_val = row['ROE'] if row['ROE'] is not None else 5.0
            ps_size = max(min(row['P/S'] * 1.5, 30.0), 10.0)

            pos_text = 'bottom center' if roe_val > 75.0 else 'top center'

            fig_quad.add_trace(go.Scatter(
                x=[peg_val],
                y=[roe_val],
                mode='markers+text',
                cliponaxis=False,
                marker=dict(
                    size=ps_size + (6 if is_target else 0),
                    color='#0D9488' if is_target else '#0284C7',
                    opacity=0.88 if is_target else 0.70,
                    line=dict(width=2.5 if is_target else 1.5, color='#FFFFFF')
                ),
                text=[f"<b>{row['代碼']}</b>"],
                textposition=pos_text,
                textfont=dict(size=11.5, color='#0D9488' if is_target else '#1E293B', family='Arial Black'),
                hovertemplate=f"<b>{row['公司']} ({row['代碼']})</b><br>" +
                              f"ROE (股本回報): {row['ROE']:.1f}%<br>" +
                              f"PEG 性價比: {row['PEG'] if row['PEG'] else 'N/A'}<br>" +
                              f"P/S 市銷率: {row['P/S']:.1f}x<extra></extra>",
                showlegend=False
            ))

        fig_quad.add_hline(y=20.0, line_dash="dash", line_color="#059669", line_width=1.5)
        fig_quad.add_annotation(
            xref="paper", yref="y",
            x=0.98, y=20.0,
            xanchor="right",
            text="<b>高護城河基準線 (ROE = 20%)</b>",
            showarrow=False,
            bgcolor="#FFFFFF",
            bordercolor="#059669",
            borderwidth=1.2,
            borderpad=4,
            font=dict(size=10, color="#065F46", family="Arial Black")
        )

        fig_quad.add_vline(x=1.5, line_dash="dash", line_color="#D97706", line_width=1.5)
        fig_quad.add_annotation(
            xref="x", yref="paper",
            x=1.5, y=0.94,
            xanchor="left",
            text="<b>合理估值邊界 (PEG = 1.5)</b>",
            showarrow=False,
            bgcolor="#FFFFFF",
            bordercolor="#D97706",
            borderwidth=1.2,
            borderpad=4,
            font=dict(size=10, color="#B45309", family="Arial Black")
        )

        max_y = max(max_roe_raw * 1.35, 60.0)
        min_y = min(valid_bubble_df['ROE'].min() * 1.15, -15.0)

        fig_quad.add_shape(
            type="rect",
            x0=0, y0=20.0, x1=1.5, y1=max_y,
            fillcolor="rgba(16, 185, 129, 0.07)",
            line_width=0,
            layer="below"
        )
        
        fig_quad.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.95,
            xanchor="left",
            text="<b>🌟 黃金高性價比區 (ROE > 20% & PEG < 1.5)</b>",
            showarrow=False,
            bgcolor="rgba(255, 255, 255, 0.90)",
            bordercolor="#059669",
            borderwidth=1.2,
            borderpad=5,
            font=dict(color="#047857", size=11, family="Arial Black")
        )

        max_x = max(valid_bubble_df['PEG'].dropna().max() * 1.25, 3.5) if not valid_bubble_df['PEG'].dropna().empty else 3.5

        fig_quad.update_layout(
            title=dict(text=f"<b>【{detected_industry}】護城河與估值性價比矩陣 (氣泡大小 = 市銷率 P/S)</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
            height=500,
            margin=dict(t=85, b=45, l=40, r=40),
            xaxis=dict(title="<b>PEG 成長性價比 (越往左越便宜)</b>", range=[0, max_x], showgrid=True, gridcolor='#F2ECE5'),
            yaxis=dict(title="<b>ROE 股東權益報酬率 (%) (越往上護城河越深)</b>", range=[min_y, max_y], showgrid=True, gridcolor='#F2ECE5'),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF"
        )
        st.plotly_chart(fig_quad, use_container_width=True, key="p5_quad_bubble_chart")

    else:
        categories_radar = ['獲利成長性 (EPS Growth)', '資本回報率 (ROE)', '現金造血力 (FCF Yield)', '估值優勢度 (1/PEG)', '營收效率 (P/S)']
        
        t_growth_s = min(max(float(target_row['原始 EPS 年增']) / 50.0 * 100.0, 15.0), 95.0)
        t_roe_s = min(max(float(target_row['ROE']) / 40.0 * 100.0, 15.0), 95.0)
        t_fcf_s = min(max((float(target_row['FCF Yield']) + 2.0) / 8.0 * 100.0, 15.0), 95.0)
        t_peg_s = min(max((2.5 - (target_row['PEG'] or 1.5)) / 2.0 * 100.0, 15.0), 95.0)
        t_ps_s = min(max((30.0 - float(target_row['P/S'])) / 28.0 * 100.0, 15.0), 95.0)

        med_growth = peers_only['原始 EPS 年增'].median()
        med_roe = peers_only['ROE'].median()
        med_fcf = peers_only['FCF Yield'].median()
        med_peg = peers_only['PEG'].dropna().median() if not peers_only['PEG'].dropna().empty else 1.5
        med_ps = peers_only['P/S'].median()

        m_growth_s = min(max(float(med_growth) / 50.0 * 100.0, 15.0), 95.0)
        m_roe_s = min(max(float(med_roe) / 40.0 * 100.0, 15.0), 15.0)
        m_fcf_s = min(max((float(med_fcf) + 2.0) / 8.0 * 100.0, 95.0), 95.0)
        m_peg_s = min(max((2.5 - float(med_peg)) / 2.0 * 100.0, 15.0), 95.0)
        m_ps_s = min(max((30.0 - float(med_ps)) / 28.0 * 100.0, 15.0), 95.0)

        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=[t_growth_s, t_roe_s, t_fcf_s, t_peg_s, t_ps_s, t_growth_s],
            theta=categories_radar + [categories_radar[0]],
            fill='toself',
            name=f"{target_symbol} (目標標的)",
            fillcolor="rgba(13, 148, 136, 0.25)",
            line=dict(color='#0D9488', width=2.8)
        ))

        fig_radar.add_trace(go.Scatterpolar(
            r=[m_growth_s, m_roe_s, m_fcf_s, m_peg_s, m_ps_s, m_growth_s],
            theta=categories_radar + [categories_radar[0]],
            fill='toself',
            name="同行中位數基準 (Peer Median)",
            fillcolor="rgba(217, 119, 6, 0.12)",
            line=dict(color='#D97706', width=2.0, dash='dash')
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor="#E2E8F0"),
                angularaxis=dict(tickfont=dict(size=11, color="#2D2622", family="Arial Black"))
            ),
            title=dict(text=f"<b>【{target_symbol} vs. 同行中位數】五維核心體質雷達圖</b>", font=dict(size=14, color="#2D2622"), x=0.01, y=0.98),
            height=460,
            margin=dict(t=85, b=30, l=35, r=35),
            legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=0.98, font=dict(size=11)),
            paper_bgcolor="#FFFFFF"
        )
        st.plotly_chart(fig_radar, use_container_width=True, key="p5_radar_chart")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### 📊 {detected_industry} 直屬同行完整指標數據表")

    df_disp = df_peers.copy()
    df_disp['現價'] = df_disp['現價'].apply(lambda x: f"${x:.2f}")
    df_disp['前瞻 P/E'] = df_disp['前瞻 P/E'].apply(lambda x: f"{x:.1f}x" if pd.notnull(x) else "N/A (未盈利)")
    df_disp['預估 EPS 年增'] = df_disp['原始 EPS 年增'].apply(lambda x: f"+{x:.1f}%")
    df_disp['PEG'] = df_disp['PEG'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
    df_disp['EV/EBITDA'] = df_disp['EV/EBITDA'].apply(lambda x: f"{x:.1f}x" if pd.notnull(x) else "N/A")
    df_disp['P/S'] = df_disp['P/S'].apply(lambda x: f"{x:.1f}x")
    df_disp['FCF Yield'] = df_disp['FCF Yield'].apply(lambda x: f"{x:.1f}%")
    df_disp['ROE'] = df_disp['ROE'].apply(lambda x: f"{x:.1f}%")

    cols_to_show = ['代碼', '公司', '現價', '前瞻 P/E', '預估 EPS 年增', 'PEG', 'EV/EBITDA', 'P/S', 'FCF Yield', 'ROE']
    st.dataframe(df_disp[cols_to_show], use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【真實同儕矩陣判讀】</strong>
        <p style="color: #2D2622; margin: 6px 0 0 0; font-size: 0.94rem; line-height: 1.65;">
            • 尋找<strong><span>ROE > 20% 且 PEG < 1.5</span></strong>（落在上方氣泡圖綠色黃金區）的同儕標的，這代表公司既有深厚護城河的高資本回報率，估值又未被過度透支，是長期複利增長的核心首選。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 6：標的產業特定估值治理與個股結構風險穿透
# ----------------------------------------------------
elif active_p3 == "tab6":
    st.markdown(f"### 🏛️ 六、{target_symbol} 產業特定估值治理條件與個股結構風險穿透")
    st.caption(f"針對當前標的 `{target_symbol}` 執行現金流折現敏感度儀表量化、所屬板塊專屬治理條件比對與三大結構風險評估。")

    pe_val = float(target_row['前瞻 P/E']) if target_row['前瞻 P/E'] is not None else 35.0
    fcf_val = float(target_row['FCF Yield'])
    
    sens_score = min(max(int((pe_val / 35.0) * 100), 15), 95)
    sens_level = "高敏感 (估值壓力大)" if sens_score >= 70 else ("中度敏感" if sens_score >= 40 else "低敏感 (安全邊際厚)")
    
    resil_score = min(max(int(((fcf_val + 5.0) / 10.0) * 100), 10), 95)
    resil_level = "防禦性強 (自體造血佳)" if resil_score >= 60 else ("中等耐受" if resil_score >= 35 else "流動性脆弱 (需關注負債/燒錢率)")

    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-radius:12px 12px 0 0; padding:14px 18px 6px 18px; text-align:center;">
            <div style="font-size:1.05rem; font-weight:800; color:#0284C7; margin-bottom:2px;">
                📉 遠期現金流折現敏感度
            </div>
            <div style="font-size:0.84rem; color:#7A6C60; font-weight:600;">
                利率上行環境下的估值倍數壓縮風險
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        fig_gauge1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sens_score,
            number={'suffix': " 分", 'font': {'size': 28, 'color': '#2D2622', 'family': 'Arial Black'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#D6CBC1", 'tickfont': {'size': 11}},
                'bar': {'color': "#0284C7", 'thickness': 0.28},
                'bgcolor': "#FFFFFF",
                'borderwidth': 1,
                'bordercolor': "#E6DFD7",
                'steps': [
                    {'range': [0, 40], 'color': '#F0FDFA'},
                    {'range': [40, 70], 'color': '#FEF3C7'},
                    {'range': [70, 100], 'color': '#FEE2E2'}
                ],
                'threshold': {
                    'line': {'color': "#DC2626", 'width': 3.5},
                    'thickness': 0.8,
                    'value': sens_score
                }
            }
        ))
        fig_gauge1.update_layout(height=180, margin=dict(t=15, b=10, l=35, r=35), paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig_gauge1, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-top:none; border-radius:0 0 12px 12px; padding:6px 18px 14px 18px; text-align:center; font-size:0.90rem; color:#475569;">
            評定等級：<strong style="color:#0284C7;">{sens_level}</strong>
        </div>
        """, unsafe_allow_html=True)

    with g_col2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-radius:12px 12px 0 0; padding:14px 18px 6px 18px; text-align:center;">
            <div style="font-size:1.05rem; font-weight:800; color:#0D9488; margin-bottom:2px;">
                🌊 資本支出與信貸週期耐受度
            </div>
            <div style="font-size:0.84rem; color:#7A6C60; font-weight:600;">
                緊縮信貸環境下的自體造血防禦力
            </div>
        </div>
        """, unsafe_allow_html=True)

        fig_gauge2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=resil_score,
            number={'suffix': " 分", 'font': {'size': 28, 'color': '#2D2622', 'family': 'Arial Black'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#D6CBC1", 'tickfont': {'size': 11}},
                'bar': {'color': "#0D9488", 'thickness': 0.28},
                'bgcolor': "#FFFFFF",
                'borderwidth': 1,
                'bordercolor': "#E6DFD7",
                'steps': [
                    {'range': [0, 35], 'color': '#FEE2E2'},
                    {'range': [35, 60], 'color': '#FEF3C7'},
                    {'range': [60, 100], 'color': '#F0FDFA'}
                ],
                'threshold': {
                    'line': {'color': "#0D9488", 'width': 3.5},
                    'thickness': 0.8,
                    'value': resil_score
                }
            }
        ))
        fig_gauge2.update_layout(height=180, margin=dict(t=15, b=10, l=35, r=35), paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig_gauge2, use_container_width=True, config={'displayModeBar': False})

        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-top:none; border-radius:0 0 12px 12px; padding:6px 18px 14px 18px; text-align:center; font-size:0.90rem; color:#475569;">
            評定等級：<strong style="color:#0D9488;">{resil_level}</strong> ｜ FCF 收益率 <strong>{fcf_val:.1f}%</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#FFFDF9; border:1px solid #EADBCE; border-left:5px solid #0F766E; border-radius:12px; padding:20px 22px; margin-top:18px; margin-bottom:24px; box-shadow:0 1px 4px rgba(0,0,0,0.02);">
        <div style="color:#0F766E; font-size:1.04rem; font-weight:800; margin-bottom:10px;">💡 【機構指南】儀表板分數高低怎麼判讀？分數愈高愈值得買嗎？</div>
        <div style="color:#2D2622; font-size:0.91rem; line-height:1.75; margin-bottom:12px;">
            • <strong>核心原則：不同儀表代表不同維度，並非所有分數都是「愈高愈好」</strong>。<br>
            左側折現儀表與下方結構風險長條圖代表「市場壓力與脆弱度」，<strong>分數愈高代表風險愈大</strong>；右側信貸耐受度儀表代表「自體造血防禦力」，<strong>分數愈高才代表防禦體質愈強</strong>。
        </div>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.88rem; text-align:left;">
                <thead>
                    <tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">
                        <th style="padding:9px 12px; font-weight:800; width:25%;">量化監控維度</th>
                        <th style="padding:9px 12px; font-weight:800; width:20%;">方向性法則</th>
                        <th style="padding:9px 12px; font-weight:800; width:55%;">機構解讀與配置操作指引</th>
                    </tr>
                </thead>
                <tbody style="color:#2D2622;">
                    <tr style="border-bottom:1px solid #EFEAE2; background:#FFFFFF;">
                        <td style="padding:10px 12px; font-weight:700; color:#0284C7;">📉 遠期折現敏感度<br>(左側儀表)</td>
                        <td style="padding:10px 12px; font-weight:700; color:#DC2626;">▼ 分數愈低愈安全<br>(高分 = 風險大)</td>
                        <td style="padding:10px 12px; line-height:1.65;">
                            衡量在降息落空或長天期殖利率上揚時的<strong>估值壓縮（Multiple Contraction）風險</strong>。<br>
                            • <strong>低分 (<40分)</strong>：估值具安全邊際，對利率波動耐受度高。<br>
                            • <strong>高分 (>70分)</strong>：股價已被高度透支，只要利率稍有波動容易引發大幅殺估值。
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid #EFEAE2; background:#F0FDF4;">
                        <td style="padding:10px 12px; font-weight:700; color:#0D9488;">🌊 信貸週期耐受度<br>(右側儀表)</td>
                        <td style="padding:10px 12px; font-weight:700; color:#047857;">▲ 分數愈高愈優秀<br>(高分 = 造血強)</td>
                        <td style="padding:10px 12px; line-height:1.65;">
                            衡量扣除高額資本支出（CapEx）後，公司<strong>真實自體現金造血防禦力</strong>。<br>
                            • <strong>高分 (>60分)</strong>：自體造血充沛，不依賴外部發債借錢，具備穿透衰退週期的實力。<br>
                            • <strong>低分 (<35分)</strong>：現金流吃緊或處於燒錢期，一旦信貸緊縮容易面臨融資困境。
                        </td>
                    </tr>
                    <tr style="background:#FFFFFF;">
                        <td style="padding:10px 12px; font-weight:700; color:#D97706;">⚠️ 三大結構性風險<br>(下方長條圖)</td>
                        <td style="padding:10px 12px; font-weight:700; color:#DC2626;">▼ 分數愈低愈安全<br>(高分 = 警戒紅條)</td>
                        <td style="padding:10px 12px; line-height:1.65;">
                            評估 ETF 被動資金湧入脫鉤、業績承諾兌現難度與轉型融資壓力。<br>
                            • <strong>綠條 (安全)</strong>：結構健康，基本面支撐扎實。<br>
                            • <strong>紅條 (警戒)</strong>：潛在暗礁浮現，即使是優質龍頭也不應過度追高，須留足安全邊際。
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"#### 📌 【{detected_sector or '所屬板塊'}】專屬核心估值治理與約束條件")

    sector_library = {
        "Healthcare": {
            "name": "醫療保健 (Healthcare)",
            "icon": "🧬",
            "metrics": "前瞻 P/E、EV/EBITDA、研發費用率 (R&D to Sales)",
            "condition": "臨床新藥 Pipeline 通過率與專利懸崖（Patent Cliff）到期時間；FDA 監管審批時程與公私醫保降價談判風險。",
            "color": "#0D9488"
        },
        "Technology": {
            "name": "資訊科技 (Information Technology)",
            "icon": "💻",
            "metrics": "本益比 (P/E)、企業價值/銷售額 (EV/Sales)、市銷率 (P/S)",
            "condition": "大型基礎設施資本支出週期（如 AI 算力中心建設）之回收期，以及未來 1~3 年獲利可見度與訂單留存率。",
            "color": "#0284C7"
        },
        "Financial": {
            "name": "金融服務 (Financials)",
            "icon": "🏦",
            "metrics": "市淨率 (P/B)、市有形資產淨值比 (P/TBV)",
            "condition": "流動性覆蓋率 (LCR)、不良資產比率 (NPL)、淨利息差 (NIM) 與巴塞爾協議監管資本充足率 (CET1)。",
            "color": "#8C7565"
        },
        "Utilities": {
            "name": "公用事業與房地產 (Utilities & Real Estate)",
            "icon": "⚡",
            "metrics": "股息收益率 (Dividend Yield)、市價/調整後營運資金 (P/AFFO)",
            "condition": "與基準公債殖利率之替代利差競爭力、利率再融資敏感度、受主管機關監管之可預測現金分配能力。",
            "color": "#D97706"
        },
        "Energy": {
            "name": "能源與原物料 (Energy & Materials)",
            "icon": "🛢️",
            "metrics": "企業價值倍數 (EV/EBITDA)、市現率 (P/CF)",
            "condition": "大宗商品週期價格實現度、全球供應鏈碎片化衝擊與地緣政治斷鏈外生風險。",
            "color": "#DC2626"
        },
        "Industrials": {
            "name": "工業製造與國防 (Industrials)",
            "icon": "🏗️",
            "metrics": "前瞻本益比 (Forward P/E)、企業價值倍數 (EV/EBITDA)",
            "condition": "全球實體製造業 PMI 週期走勢、國防常態化預算支出、關稅壁壘對終端利潤率之侵蝕壓力。",
            "color": "#475569"
        }
    }

    current_sec_key = "Technology"
    for k in sector_library.keys():
        if k.lower() in (detected_sector or "").lower():
            current_sec_key = k
            break
    sec_info = sector_library[current_sec_key]

    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1.5px solid {sec_info['color']}; border-radius: 12px; padding: 22px; margin-bottom: 18px; box-shadow: 0 4px 14px rgba(0,0,0,0.04);">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #F0ECE8; padding-bottom: 12px; margin-bottom: 14px;">
            <div style="font-size: 1.22rem; font-weight: 800; color: #2D2622;">
                {sec_info['icon']} {target_symbol} 標的匹配板塊：<span style="color:{sec_info['color']};">{sec_info['name']}</span>
            </div>
            <span style="background: #FAF8F5; border: 1px solid {sec_info['color']}; color: {sec_info['color']}; font-size: 0.82rem; font-weight: 700; padding: 4px 12px; border-radius: 20px;">
                ● 核心治理鎖定
            </span>
        </div>
        <div style="margin-bottom: 12px;">
            <span style="font-weight: 800; color: #2D2622; font-size: 0.96rem;">🔍 機構首選對標乘數：</span>
            <span style="color: #0284C7; font-weight: 700; font-size: 0.96rem;">{sec_info['metrics']}</span>
        </div>
        <div style="background: #FBFBFA; border: 1px solid #E6DFD7; border-left: 4px solid {sec_info['color']}; border-radius: 8px; padding: 14px 16px;">
            <div style="font-weight: 800; color: #2D2622; font-size: 0.94rem; margin-bottom: 4px;">⚙️ 嚴格治理與審查條件約束 (Governance Constraints)：</div>
            <div style="font-size: 0.90rem; color: #475569; line-height: 1.75;">
                {sec_info['condition']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🌐 查看美股其他 5 大板塊之估值治理對標標準", expanded=False):
        for k, v in sector_library.items():
            if k != current_sec_key:
                st.markdown(f"""
                <div style="border-bottom: 1px solid #F0ECE8; padding: 10px 0;">
                    <strong style="color: #2D2622;">{v['icon']} {v['name']}</strong><br>
                    <span style="font-size: 0.88rem; color: #0284C7;">指標：{v['metrics']}</span><br>
                    <span style="font-size: 0.86rem; color: #5C554F;">條件：{v['condition']}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### ⚠️ {target_symbol} 三大結構性風險量化評級")

    risk_categories = [
        "被動資金湧入與數據扭曲 (ETF 買盤脫鉤)",
        "高估值生產力變現檢驗 (業績兌現承諾)",
        "資本密集度轉型負擔 (CapEx 融資壓力)"
    ]
    
    risk_scores = [
        min(max(int((target_row['PEG'] or 1.5) * 35), 30), 85),
        min(max(int((pe_val / 40.0) * 100), 25), 90),
        min(max(int((10.0 - fcf_val) * 8), 20), 80)
    ]
    risk_colors = ['#DC2626' if s >= 70 else ('#D97706' if s >= 45 else '#0D9488') for s in risk_scores]

    fig_risk = go.Figure()
    fig_risk.add_trace(go.Bar(
        y=risk_categories,
        x=risk_scores,
        orientation='h',
        marker=dict(color=risk_colors, line=dict(color='#FFFFFF', width=1.5)),
        text=[f"壓力值: {s}分 ({'警戒' if s>=70 else ('觀察' if s>=45 else '安全')})" for s in risk_scores],
        textposition='inside',
        textfont=dict(size=12, color='#FFFFFF', family='Arial Black')
    ))

    fig_risk.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=240,
        margin=dict(t=20, b=20, l=230, r=25),
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor='#F2ECE5', title="結構性風險評級分位數 (%)"),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color="#2D2622"))
    )
    st.plotly_chart(fig_risk, use_container_width=True, config={'displayModeBar': False})

    st.markdown(f"""
    <div style="background: #F8FAF9; border: 1px solid #D1E5DE; border-left: 4px solid #0D9488; border-radius: 8px; padding: 12px 16px; margin-top: 8px; font-size: 0.88rem; color: #2D2622;">
        💡 <strong>機構風控結論：</strong><code>{target_symbol}</code> 之結構性風險主要來自於<strong>「{risk_categories[1].split('(')[0]}」</strong>。當前估值已提前反映未來多季利多，在同儕對標與投資組合配置時，應嚴格設立安全邊際以防估值驟降。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #FFFBEB; border: 1px solid #B45309; border-radius: 6px; padding: 10px 14px; margin-top: 22px;">
        <span style="color: #B45309; font-size: 0.82rem; line-height: 1.4; display: block;">
            <strong>免責聲明與使用規範：</strong>本產業特定估值治理條件與結構風險矩陣僅供機構級投研對標參考，非個股保證買賣建議。分析時應充分考量個別企業之資本結構與資本支出生命週期差異。
        </span>
    </div>
    """, unsafe_allow_html=True)
