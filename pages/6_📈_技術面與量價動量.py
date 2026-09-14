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
    page_title="技術面與量價動量 - 澄璞財務",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. 引入全站共用樣式與品牌設定
import config
config.inject_global_style()

# 2. 掛載側邊欄狀態
from auth import render_login_widget, init_auth_state, TIER_NAMES, render_upgrade_checkout_widget
render_login_widget()
init_auth_state()
user_tier = st.session_state.get("user_tier", 0)

# ==============================================================================
# 🔒 本頁專屬安檢門（300 元旗艦版門檻：內嵌技術面五大深度量化價值說明・就地開通升級）
# ==============================================================================
if user_tier < 2:
    target_plan = TIER_NAMES.get(2, "👑 專業全能旗艦版 (NT$ 300/月)")
    user_plan = TIER_NAMES.get(user_tier, "🌿 基礎探索版 (免費)")

    st.markdown(f"""
    <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 26px; margin-top:20px; margin-bottom:20px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.5rem;">🔒</span>
                <span style="font-size:1.30rem; font-weight:900; color:#78350F;">【6. 📈 技術面與量價動量動態監控】旗艦專屬解鎖功能</span>
            </div>
            <span style="background:#FEF3C7; color:#92400E; font-size:0.88rem; font-weight:900; padding:5px 14px; border-radius:20px; border:1.5px solid #FDE68A;">
                需要解鎖：{target_plan}
            </span>
        </div>
        <div style="font-size:1.02rem; font-weight:800; color:#92400E; margin-bottom:8px;">
            ✦ 核心價值：掌握大額主力進出足跡與看盤級動態動量，以多天期均線與籌碼分佈建立高勝率交易攻防點
        </div>
        <div style="font-size:0.96rem; color:#6B584C; line-height:1.7;">
            您目前的使用權限為：<strong>{user_plan}</strong>。單純依靠零碎消息或單一指標容易遭遇「假突破」與鈍化震盪！解鎖旗艦版，以全週期量價微觀結構與籌碼密集峰，為每一筆波段操作建立最清晰的攻防防線。
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 💎 就地渲染：由 auth.py 統一帶出與第4頁、第5頁完全一致的高質感「彩色邊框雙欄網格卡片 + 雙方案對比按鈕」！
    render_upgrade_checkout_widget(required_tier=2, feature_title="技術面與量價動量")

    st.stop()

# ==============================================================================
# 👇 通過驗證放行後，正常執行的完整分析與視覺化程式碼（100% 完整保留原本代碼）
# ==============================================================================

# ==========================================
# 全域雙向狀態綁定邏輯
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = ""

if 'active_tab_p5' not in st.session_state:
    st.session_state['active_tab_p5'] = "tab1"

if 'kline_period_select' not in st.session_state:
    st.session_state['kline_period_select'] = "1年 (1Y)"

st.session_state['ticker_input_p5'] = st.session_state['current_ticker']

def sync_ticker_p5():
    val = st.session_state.get('ticker_input_p5', '').upper().strip()
    st.session_state['current_ticker'] = val

st.subheader("📈 技術面與量價動量動態監控 (Technical Analysis & Price Action Momentum)")

col_search, col_name, col_p, col_refresh = st.columns([1.8, 2.5, 1.7, 1.0])

with col_search:
    st.text_input(
        "🔍 請輸入欲檢驗技術面之美股代碼", 
        key="ticker_input_p5",
        on_change=sync_ticker_p5,
        placeholder="例如: AAPL, NVDA, LLY, MSFT...",
        help="輸入代碼後按 Enter，即時載入上市以來真實看盤級技術分析"
    )

target_symbol = st.session_state.get('current_ticker', '').strip()
user_has_typed = bool(target_symbol)

# ==========================================
# 🛑 純淨待機機制
# ==========================================
if not user_has_typed:
    with col_name:
        st.markdown("### 📈 技術面與量價動量系統（待機中）")
        st.caption("👈 請於左側輸入股票代碼以啟動專業級看盤圖表")
    with col_p:
        st.metric("分析狀態", "Standby", "等待輸入標的")

    st.divider()

    st.markdown("""
    <div class="standby-card">
        <div style="font-size: 2.8rem; margin-bottom: 12px;">📈</div>
        <div style="font-size: 1.35rem; font-weight: 800; color: #2D2622;">尚未指定技術分析標的</div>
        <div style="font-size: 0.98rem; color: #7A6C60; max-width: 650px; margin: 8px auto 20px auto; line-height: 1.7;">
            請於上方搜尋框輸入任意美股代碼（例如蘋果 <code>AAPL</code>、輝達 <code>NVDA</code>、微軟 <code>MSFT</code>、禮來 <code>LLY</code>）。<br>
            系統載入<strong>上市以來全部歷史行情（MAX）</strong>，附帶<strong>專業級時間軸滑塊導航器</strong>，可自由放大任意歷史區間（如 2010~2012）並任意向左、向右拖曳巡航。
        </div>
        <div style="display: inline-block; background: #F1F5F9; padding: 8px 18px; border-radius: 20px; font-size: 0.88rem; color: #475569; font-weight: 600;">
            ✦ 附帶歷史全景時間軸導航滑桿 ｜ 自由框選放大與平移 ✦
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# 💎 高效能超長週期資料引擎（最佳化快取與多重索引清洗）
# ==========================================
@st.cache_data(ttl=86400)
def fetch_technical_master_data(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="max")
        if df.empty:
            df = yf.download(symbol, period="max", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        info = stock.info or {}
        c_name = info.get('shortName', symbol)
    except Exception:
        df = pd.DataFrame()
        c_name = symbol

    if df.empty or len(df) < 20:
        return None, c_name, 0.0, 0.0

    df = df.dropna()
    if hasattr(df.index, 'tz_localize'):
        try:
            df.index = df.index.tz_localize(None)
        except TypeError:
            df.index = df.index.tz_convert(None)

    close = df['Close']

    df['EMA20'] = close.ewm(span=20, adjust=False).mean()
    df['SMA50'] = close.rolling(window=50).mean()
    df['SMA200'] = close.rolling(window=200).mean()

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    exp12 = close.ewm(span=12, adjust=False).mean()
    exp26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']

    df['BB_Mid'] = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Mid'] - (bb_std * 2)
    df['BB_Bandwidth'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid']) * 100

    latest_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) >= 2 else latest_close
    chg_pct = ((latest_close - prev_close) / prev_close) * 100 if prev_close != 0 else 0.0

    return df, c_name, latest_close, chg_pct

with col_refresh:
    if st.button("🔄 即刻刷新", help="手動清除快取，重新載入最新市場價格數據"):
        st.cache_data.clear()
        st.rerun()

with st.spinner(f"正在連線交易所載入 {target_symbol} 上市以來完整歷史數據..."):
    tech_df, company_title, curr_p, day_chg = fetch_technical_master_data(target_symbol)

if tech_df is None:
    st.error(f"⚠️ 無法取得美股代碼 `{target_symbol}` 的真實行情，請確認代碼是否輸入正確。")
    st.stop()

curr_rsi = float(tech_df['RSI'].dropna().iloc[-1]) if not tech_df['RSI'].dropna().empty else 50.0
curr_hist = float(tech_df['MACD_Hist'].dropna().iloc[-1]) if not tech_df['MACD_Hist'].dropna().empty else 0.0
curr_macd = float(tech_df['MACD'].dropna().iloc[-1]) if not tech_df['MACD'].dropna().empty else 0.0
curr_sma50 = float(tech_df['SMA50'].dropna().iloc[-1]) if not tech_df['SMA50'].dropna().empty else curr_p
curr_sma200 = float(tech_df['SMA200'].dropna().iloc[-1]) if not tech_df['SMA200'].dropna().empty else curr_sma50
bandwidth = float(tech_df['BB_Bandwidth'].dropna().iloc[-1]) if not tech_df['BB_Bandwidth'].dropna().empty else 10.0

trend_status = "多頭排列 (站上 50/200MA)" if curr_p > curr_sma50 and curr_p > curr_sma200 else ("震盪整理" if curr_p > curr_sma50 else "偏空格局 (跌破均線)")

with col_name:
    st.markdown(f"### {company_title} (`{target_symbol}`)")
    st.caption(f"即時趨勢判定：**【{trend_status}】 ｜ 站上 50MA: {curr_p > curr_sma50} ｜ 站上 200MA: {curr_p > curr_sma200}**")
with col_p:
    st.metric("即時現價", f"${curr_p:.2f}", f"{day_chg:+.2f}%")

st.divider()

# ==========================================
# 💎 合規與資料來源透明度狀態卡 (Transparency Header)
# ==========================================
st.markdown("""
<div style="background:#FAF8F5; border:1px solid #EADBCE; border-radius:10px; padding:12px 18px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
    <div style="font-size:0.86rem; color:#475569; display:flex; gap:14px; align-items:center; flex-wrap:wrap;">
        <span>🟢 <strong>歷史行情與 OHLCV</strong>：交易所即時與歷史還原行情直連</span>
        <span>🟡 <strong>技術指標運算</strong>：標準開源量化指標公式計算 (EMA/SMA/RSI/MACD/BB)</span>
        <span>⚪ <strong>籌碼分佈 (Volume Profile)</strong>：歷史價格區間成交量聚合模型</span>
    </div>
    <div style="font-size:0.82rem; color:#8C7E72; font-weight:600;">
        資料源：Yahoo Finance / 澄璞技術量化引擎
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 技術面四大核心指標卡
# ==========================================
st.markdown(f"#### ⚡ {target_symbol} 四大核心量價動能體格 (實時交易數據核算)")

t1, t2, t3, t4 = st.columns(4)
rsi_label = "超買鈍化 (>70)" if curr_rsi > 70 else ("超賣築底 (<30)" if curr_rsi < 30 else "常態強弱區間")
t1.metric("📊 14日 RSI 相對強弱", f"{curr_rsi:.1f}", rsi_label, delta_color="normal")

macd_status = "多方柱狀擴張" if curr_hist > 0 else "空方動能收斂"
t2.metric("🌊 MACD 柱狀動量 (Hist)", f"{curr_hist:+.2f}", f"DIF: {curr_macd:.2f} ｜ {macd_status}", delta_color="normal")

dist_50ma = ((curr_p - curr_sma50) / curr_sma50) * 100 if curr_sma50 > 0 else 0.0
t3.metric("📈 50日均線乖離率 (SMA 50)", f"{dist_50ma:+.1f}%", f"50MA 現值: ${curr_sma50:.2f}", delta_color="normal")

t4.metric("🎯 布林通道帶寬 (Bandwidth)", f"{bandwidth:.1f}%", "數值收窄代表變盤醞釀中" if bandwidth < 10 else "通道開口放大趨勢中", delta_color="normal")

st.markdown("---")

# ==========================================
# 五大深度導航按鈕
# ==========================================
st.markdown("##### 🧭 技術面與量價動量 — 五大深度分析選單")

g1, g2, g3 = st.columns(3)
g4, g5, g6 = st.columns(3)

with g1:
    if st.button("📊 一、專業級多週期 K 線圖與均線系統 (EMA20 / SMA50 / SMA200)", type="primary" if st.session_state['active_tab_p5'] == "tab1" else "secondary", use_container_width=True):
        st.session_state['active_tab_p5'] = "tab1"
        st.rerun()

with g2:
    if st.button("🌊 二、RSI 相對強弱指標與多空背離警示 (14-day RSI)", type="primary" if st.session_state['active_tab_p5'] == "tab2" else "secondary", use_container_width=True):
        st.session_state['active_tab_p5'] = "tab2"
        st.rerun()

with g3:
    if st.button("⚡ 三、MACD 趨勢動能指標與黃金/死亡交叉檢驗", type="primary" if st.session_state['active_tab_p5'] == "tab3" else "secondary", use_container_width=True):
        st.session_state['active_tab_p5'] = "tab3"
        st.rerun()

with g4:
    if st.button("🎯 四、布林通道 (Bollinger Bands) 波動擠壓與突破檢驗", type="primary" if st.session_state['active_tab_p5'] == "tab4" else "secondary", use_container_width=True):
        st.session_state['active_tab_p5'] = "tab4"
        st.rerun()

with g5:
    if st.button("🧱 五、量價關係與籌碼分佈支撐壓力位檢驗 (Volume Profile)", type="primary" if st.session_state['active_tab_p5'] == "tab5" else "secondary", use_container_width=True):
        st.session_state['active_tab_p5'] = "tab5"
        st.rerun()

with g6:
    st.markdown(f"<div style='height: 52px; background: #FFFFFF; border: 1px solid #D6CBC1; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #847568; font-weight: 700; font-size: 0.95rem;'>✦ 上市以來全歷史數據 ✦</div>", unsafe_allow_html=True)

st.markdown("---")

active_p5 = st.session_state['active_tab_p5']

# ==========================================
# 頂部超長週期切換工具列
# ==========================================
col_period_bar, col_empty = st.columns([4.2, 0.8])
with col_period_bar:
    selected_period = st.radio(
        "⏱️ 選擇技術分析週期",
        ["1個月 (1M)", "3個月 (3M)", "6個月 (6M)", "1年 (1Y)", "5年 (5Y)", "10年 (10Y)", "全部歷史 (MAX)"],
        horizontal=True,
        index=3,
        key="kline_period_select"
    )

now_dt = tech_df.index[-1]
is_max_mode = ("全部歷史" in selected_period)

if "1個月" in selected_period:
    df_view = tech_df.loc[now_dt - timedelta(days=30):]
elif "3個月" in selected_period:
    df_view = tech_df.loc[now_dt - timedelta(days=90):]
elif "6個月" in selected_period:
    df_view = tech_df.loc[now_dt - timedelta(days=180):]
elif "1年" in selected_period:
    df_view = tech_df.loc[now_dt - timedelta(days=365):]
elif "5年" in selected_period:
    df_view = tech_df.loc[now_dt - timedelta(days=365 * 5):]
elif "10年" in selected_period:
    df_view = tech_df.loc[now_dt - timedelta(days=365 * 10):]
else:
    df_view = tech_df

if df_view.empty:
    df_view = tech_df.iloc[-60:]

x_min_bound = df_view.index.min()
x_max_bound = df_view.index.max()

if is_max_mode and len(df_view) > 750:
    initial_x_range = [now_dt - timedelta(days=365 * 3), x_max_bound]
else:
    initial_x_range = [x_min_bound, x_max_bound]

v_low = df_view['Low'].min()
v_high = df_view['High'].max()
v_pad = (v_high - v_low) * 0.04
y_min = v_low - v_pad
y_max = v_high + v_pad

# ----------------------------------------------------
# 分頁 1：專業級多週期 K 線圖與均線系統
# ----------------------------------------------------
if active_p5 == "tab1":
    st.markdown(f"### 📊 一、{target_symbol} 專業級多週期 K 線圖與均線系統")
    st.caption(f"當前視角：**【{selected_period}】** ｜ 數據區間：{x_min_bound.strftime('%Y-%m-%d')} ~ {x_max_bound.strftime('%Y-%m-%d')}。支援滑鼠滾輪縮放與底層全景滑塊自由平移。")

    fig_k = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.75, 0.25]
    )

    fig_k.add_trace(go.Candlestick(
        x=df_view.index,
        open=df_view['Open'], high=df_view['High'],
        low=df_view['Low'], close=df_view['Close'],
        name="日 K 線",
        increasing_line_color='#047857', decreasing_line_color='#DC2626'
    ), row=1, col=1)

    fig_k.add_trace(go.Scatter(x=df_view.index, y=df_view['EMA20'], mode='lines', line=dict(color='#D97706', width=1.5), name="20 EMA"), row=1, col=1)
    fig_k.add_trace(go.Scatter(x=df_view.index, y=df_view['SMA50'], mode='lines', line=dict(color='#0284C7', width=2), name="50 SMA"), row=1, col=1)
    fig_k.add_trace(go.Scatter(x=df_view.index, y=df_view['SMA200'], mode='lines', line=dict(color='#4F433B', width=2, dash='dash'), name="200 SMA"), row=1, col=1)

    vol_colors = ['#047857' if c >= o else '#DC2626' for c, o in zip(df_view['Close'], df_view['Open'])]
    fig_k.add_trace(go.Bar(x=df_view.index, y=df_view['Volume'], marker_color=vol_colors, name="成交量"), row=2, col=1)

    fig_k.update_layout(
        height=650,
        margin=dict(t=35, b=25, l=15, r=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=12)),
        xaxis_rangeslider_visible=False,
        dragmode="pan",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF"
    )
    fig_k.update_xaxes(
        range=initial_x_range,
        rangeslider=dict(visible=is_max_mode, thickness=0.06),
        row=2, col=1, 
        showgrid=False
    )
    fig_k.update_xaxes(range=initial_x_range, row=1, col=1, showgrid=False)

    fig_k.update_yaxes(
        title_text="價格 ($)", 
        range=[y_min, y_max], 
        row=1, col=1, 
        showgrid=True, 
        gridcolor='#F2ECE5'
    )
    fig_k.update_yaxes(
        title_text="成交量", 
        row=2, col=1, 
        showgrid=True, 
        gridcolor='#F2ECE5'
    )
    st.plotly_chart(fig_k, use_container_width=True, config={'scrollZoom': True}, key="p5_candle_perfect_view")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【均線系統判讀與實戰運用指南】</strong>
        <p style="color: #2D2622; margin: 6px 0 10px 0; font-size: 0.92rem; line-height: 1.65;">
            均線系統（MA / EMA）是衡量市場中期成本與趨勢方向的最基礎工具。實戰操作中，應結合均線排列與回踩支撐進行動態倉位調整：
        </p>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.89rem; text-align:left;">
                <thead>
                    <tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">
                        <th style="padding:10px 12px; font-weight:800; width:22%;">均線排列型態</th>
                        <th style="padding:10px 12px; font-weight:800; width:30%;">市場多空實質涵義</th>
                        <th style="padding:10px 12px; font-weight:800; width:48%;">實戰操作與進出場指引</th>
                    </tr>
                </thead>
                <tbody style="color:#2D2622;">
                    <tr style="border-bottom:1px solid #EFEAE2; background:#F0FDF4;">
                        <td style="padding:10px 12px; font-weight:700; color:#047857;">🟢 多頭黃金排列<br>(Price > EMA20 > SMA50 > SMA200)</td>
                        <td style="padding:10px 12px; line-height:1.65;">短中長期持股成本全數獲利，市場買盤強勁，回調均線均吸引主動資金承接。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>順勢買進與續抱</strong>：回踩 50 SMA 或 20 EMA 支撐不破時為高勝率加碼點；嚴設跌破 200 SMA 長期防線。</td>
                    </tr>
                    <tr style="border-bottom:1px solid #EFEAE2; background:#FFFBEB;">
                        <td style="padding:10px 12px; font-weight:700; color:#B45309;">🟡 均線糾結收斂<br>(橫盤震盪整理)</td>
                        <td style="padding:10px 12px; line-height:1.65;">多空力道均衡，均線相互靠攏，通常為大型突破行情前的蓄勢或籌碼換手期。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>箱體突破策略</strong>：切忌過度追價，靜待放量長紅突破上緣或帶量長黑跌破下緣再順勢跟進。</td>
                    </tr>
                    <tr style="background:#FEF2F2;">
                        <td style="padding:10px 12px; font-weight:700; color:#DC2626;">🔴 空頭長天期壓制<br>(Price < SMA50 < SMA200)</td>
                        <td style="padding:10px 12px; line-height:1.65;">長期持股者全面套牢，反彈遭遇沉重解套賣壓，市場趨勢明顯偏空。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>防守規避或反彈減碼</strong>：未見 200 SMA 築底翻揚前，嚴禁盲目左側抄底；反彈觸及 50 SMA 應視為減倉機會。</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div style="font-size:0.82rem; color:#854D0E; margin-top:10px; line-height:1.6;">
            ⚠️ <strong>技術分析限制警示</strong>：所有均線指標均為「歷史價格之滯後平均反映」，當面臨總經震撼或突發利空時，均線支撐可能瞬間失效，實盤必須搭配停損機制。
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 2：RSI 相對強弱指標
# ----------------------------------------------------
elif active_p5 == "tab2":
    st.markdown(f"### 🌊 二、{target_symbol} 14 日 RSI 相對強弱指標與多空背離警示")
    st.caption(f"當前視角：**【{selected_period}】** ｜ 數據區間：{x_min_bound.strftime('%Y-%m-%d')} ~ {x_max_bound.strftime('%Y-%m-%d')}。可透過底部時間軸滑桿任意框選特定年份（如 2010~2012）並自由拖曳平移。")

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df_view.index, 
        y=df_view['RSI'], 
        mode='lines', 
        line=dict(color='#0284C7', width=2.2), 
        name="14-day RSI"
    ))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="#DC2626", annotation_text="70 超買警戒線", annotation_position="top right")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="#047857", annotation_text="30 超賣築底線", annotation_position="bottom right")
    fig_rsi.add_hline(y=50, line_dash="dot", line_color="#94A3B8")

    fig_rsi.update_layout(
        height=540,
        margin=dict(t=35, b=25, l=15, r=20),
        xaxis=dict(
            range=initial_x_range,
            rangeslider=dict(
                visible=True,
                thickness=0.10,
                bgcolor="#F8FAFC",
                bordercolor="#CBD5E1"
            ),
            showgrid=False
        ),
        yaxis=dict(title_text="RSI 數值", range=[0, 100], showgrid=True, gridcolor='#F2ECE5'),
        dragmode="pan",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF"
    )
    st.plotly_chart(fig_rsi, use_container_width=True, config={'scrollZoom': True}, key="p5_rsi_perfect_view")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【RSI 動能實戰】相對強弱指標與背離訊號操作矩陣</strong>
        <p style="color: #2D2622; margin: 6px 0 10px 0; font-size: 0.92rem; line-height: 1.65;">
            RSI（Relative Strength Index）衡量多空雙方力量強弱的極端程度。在不同數值區間與背離型態下，其代表的實戰涵義截然不同：
        </p>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.89rem; text-align:left;">
                <thead>
                    <tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">
                        <th style="padding:10px 12px; font-weight:800; width:22%;">RSI 訊號狀態</th>
                        <th style="padding:10px 12px; font-weight:800; width:30%;">市場多空實質涵義</th>
                        <th style="padding:10px 12px; font-weight:800; width:48%;">實戰操作與進出場指引</th>
                    </tr>
                </thead>
                <tbody style="color:#2D2622;">
                    <tr style="border-bottom:1px solid #EFEAE2; background:#FEF2F2;">
                        <td style="padding:10px 12px; font-weight:700; color:#DC2626;">🔴 超買鈍化區<br>(RSI > 70 且持續高檔)</td>
                        <td style="padding:10px 12px; line-height:1.65;">多頭強勢上攻，買方動能極端強烈；但在牛市中常見「超買後繼續超買」的鈍化現象。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>分批停利或沿均線續抱</strong>：切忌單憑 RSI > 70 盲目放空；若出現「頂背離（股價創新高但 RSI 未創新高）」，則為強烈短線回調預警。</td>
                    </tr>
                    <tr style="border-bottom:1px solid #EFEAE2; background:#FFFBEB;">
                        <td style="padding:10px 12px; font-weight:700; color:#B45309;">🟡 多空拉鋸中軸<br>(RSI 40 ~ 60 區間)</td>
                        <td style="padding:10px 12px; line-height:1.65;">多空力道均衡，無明顯單邊過熱或過冷，盤面隨機波動居多。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>觀望或搭配均線佈局</strong>：不適宜作為獨立進場依據，應回歸基本面或趨勢線操作。</td>
                    </tr>
                    <tr style="background:#F0FDF4;">
                        <td style="padding:10px 12px; font-weight:700; color:#047857;">🟢 超賣築底區<br>(RSI < 30 且出現底背離)</td>
                        <td style="padding:10px 12px; line-height:1.65;">市場短線恐慌殺盤或過度悲觀，籌碼鬆動釋放，醞釀均值回歸契機。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>左側分批低吸</strong>：若伴隨「底背離（股價創新低但 RSI 未創新低）」，為勝率極高的波段右側起漲前兆。</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div style="font-size:0.82rem; color:#854D0E; margin-top:10px; line-height:1.6;">
            ⚠️ <strong>歷史導航提示</strong>：可隨時利用下方滑桿平移至 2008 或 2020 年熊市底部，觀察極端恐慌下 RSI 跌破 20 的築底特徵。
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 3：MACD 趨勢動能指標
# ----------------------------------------------------
elif active_p5 == "tab3":
    st.markdown(f"### ⚡ 三、{target_symbol} MACD 趨勢動能指標與黃金/死亡交叉檢驗")
    st.caption(f"當前視角：**【{selected_period}】** ｜ 真實 12/26/9 參數計算。底部具備時間軸滑桿，可拖曳平移巡航。")

    fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.55, 0.45])
    fig_macd.add_trace(go.Scatter(x=df_view.index, y=df_view['Close'], mode='lines', line=dict(color='#2D2622', width=2), name="收盤價 ($)"), row=1, col=1)
    fig_macd.add_trace(go.Scatter(x=df_view.index, y=df_view['MACD'], mode='lines', line=dict(color='#0284C7', width=2), name="DIF 快線"), row=2, col=1)
    fig_macd.add_trace(go.Scatter(x=df_view.index, y=df_view['Signal'], mode='lines', line=dict(color='#D97706', width=2, dash='dot'), name="Signal 慢線"), row=2, col=1)
    
    hist_colors = ['#047857' if v >= 0 else '#DC2626' for v in df_view['MACD_Hist']]
    fig_macd.add_trace(go.Bar(x=df_view.index, y=df_view['MACD_Hist'], marker_color=hist_colors, name="MACD 柱狀體"), row=2, col=1)

    fig_macd.update_layout(
        height=560,
        margin=dict(t=35, b=25, l=15, r=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=12)),
        dragmode="pan",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF"
    )
    
    fig_macd.update_xaxes(
        range=initial_x_range,
        rangeslider=dict(visible=is_max_mode, thickness=0.06),
        row=2, col=1, 
        showgrid=False
    )
    fig_macd.update_xaxes(range=initial_x_range, row=1, col=1, showgrid=False)

    fig_macd.update_yaxes(title_text="價格 ($)", range=[y_min, y_max], row=1, col=1, showgrid=True, gridcolor='#F2ECE5')
    fig_macd.update_yaxes(title_text="MACD", row=2, col=1, showgrid=True, gridcolor='#F2ECE5')
    st.plotly_chart(fig_macd, use_container_width=True, config={'scrollZoom': True}, key="p5_macd_perfect_view")

    st.markdown("""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【MACD 動能實戰】黃金/死亡交叉與柱狀體反轉操作矩陣</strong>
        <p style="color: #2D2622; margin: 6px 0 10px 0; font-size: 0.92rem; line-height: 1.65;">
            MACD（Moving Average Convergence Divergence）是捕捉中長線趨勢反轉與動能放大的利器。實戰應用時應區分零軸上下方的交叉意義：
        </p>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.89rem; text-align:left;">
                <thead>
                    <tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">
                        <th style="padding:10px 12px; font-weight:800; width:22%;">MACD 型態訊號</th>
                        <th style="padding:10px 12px; font-weight:800; width:30%;">市場動能實質涵義</th>
                        <th style="padding:10px 12px; font-weight:800; width:48%;">實戰操作與進出場指引</th>
                    </tr>
                </thead>
                <tbody style="color:#2D2622;">
                    <tr style="border-bottom:1px solid #EFEAE2; background:#F0FDF4;">
                        <td style="padding:10px 12px; font-weight:700; color:#047857;">🟢 零軸上方黃金交叉<br>(DIF 上穿 Signal 於 0 軸上)</td>
                        <td style="padding:10px 12px; line-height:1.65;">多頭主升段延續中，短期動能重新加速超越中期均值，為強勢上攻訊號。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>順勢加碼買進</strong>：波段多單可積極擴大部位，跟隨動能向上推升。</td>
                    </tr>
                    <tr style="border-bottom:1px solid #EFEAE2; background:#FFFBEB;">
                        <td style="padding:10px 12px; font-weight:700; color:#B45309;">🟡 零軸下方黃金交叉<br>(DIF 上穿 Signal 於 0 軸下)</td>
                        <td style="padding:10px 12px; line-height:1.65;">空頭趨勢中的跌勢趨緩或技術性反彈，主趨勢尚未完全翻多。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>短線搶反彈</strong>：僅適合作為快進快出的左側短多操作，嚴設短線止損。</td>
                    </tr>
                    <tr style="background:#FEF2F2;">
                        <td style="padding:10px 12px; font-weight:700; color:#DC2626;">🔴 零軸下方死亡交叉<br>(DIF 下穿 Signal 於 0 軸下)</td>
                        <td style="padding:10px 12px; line-height:1.65;">空方主導跌勢擴大，中長線賣壓沈重，向下破位風險急遽升高。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>嚴格防守與出場</strong>：反彈無力時應果斷停損，切勿抱股苦撐。</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 4：布林通道 (Bollinger Bands)
# ----------------------------------------------------
elif active_p5 == "tab4":
    st.markdown(f"### 🎯 四、{target_symbol} 布林通道 (Bollinger Bands) 波動擠壓與突破檢驗")
    st.caption(f"當前視角：**【{selected_period}】** ｜ 真實 20 SMA 與 ±2 個標準差統計通道。")

    bb_low = min(df_view['BB_Lower'].min(), df_view['Low'].min())
    bb_high = max(df_view['BB_Upper'].max(), df_view['High'].max())
    bb_pad = (bb_high - bb_low) * 0.04

    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(x=df_view.index, y=df_view['BB_Upper'], mode='lines', line=dict(color='rgba(148, 163, 184, 0.4)'), name="布林上軌 (+2σ)"))
    fig_bb.add_trace(go.Scatter(x=df_view.index, y=df_view['BB_Lower'], mode='lines', line=dict(color='rgba(148, 163, 184, 0.4)'), fill='tonexty', fillcolor='rgba(224, 242, 254, 0.35)', name="布林通道區間"))
    fig_bb.add_trace(go.Scatter(x=df_view.index, y=df_view['BB_Mid'], mode='lines', line=dict(color='#0284C7', width=1.8), name="布林中軌 (20 SMA)"))
    fig_bb.add_trace(go.Scatter(x=df_view.index, y=df_view['Close'], mode='lines', line=dict(color='#2D2622', width=2.5), name="真實收盤價 ($)"))

    fig_bb.update_layout(
        height=540,
        margin=dict(t=35, b=25, l=15, r=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=12)),
        dragmode="pan",
        xaxis=dict(
            range=initial_x_range,
            rangeslider=dict(visible=is_max_mode, thickness=0.08),
            showgrid=False
        ),
        yaxis=dict(title_text="價格 ($)", range=[bb_low - bb_pad, bb_high + bb_pad], showgrid=True, gridcolor='#F2ECE5'),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF"
    )
    st.plotly_chart(fig_bb, use_container_width=True, config={'scrollZoom': True}, key="p5_bb_perfect_view")

    st.markdown(f"""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【布林波動實戰】頻寬擠壓 (Squeeze) 與突破操作矩陣</strong>
        <p style="color: #2D2622; margin: 6px 0 10px 0; font-size: 0.92rem; line-height: 1.65;">
            布林通道（Bollinger Bands）結合了移動平均線與標準差，帶寬（Bandwidth）收窄代表市場波動率降至冰點，往往是暴風雨前的寧靜：
        </p>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.89rem; text-align:left;">
                <thead>
                    <tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">
                        <th style="padding:10px 12px; font-weight:800; width:22%;">布林型態情境</th>
                        <th style="padding:10px 12px; font-weight:800; width:30%;">市場波動實質涵義</th>
                        <th style="padding:10px 12px; font-weight:800; width:48%;">實戰操作與進出場指引</th>
                    </tr>
                </thead>
                <tbody style="color:#2D2622;">
                    <tr style="border-bottom:1px solid #EFEAE2; background:#F0FDF4;">
                        <td style="padding:10px 12px; font-weight:700; color:#047857;">🟢 通道帶寬極度收窄<br>(Bandwidth < 8% / Squeeze)</td>
                        <td style="padding:10px 12px; line-height:1.65;">多空雙方在狹幅區間激烈鬥法，蓄勢待發，即將迎來方向性的大幅變盤。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>潛伏佈局等待突破</strong>：切忌提前猜方向；等待帶量長紅突破上軌或帶量長黑跌破下軌時順勢跟進。</td>
                    </tr>
                    <tr style="border-bottom:1px solid #EFEAE2; background:#FFFBEB;">
                        <td style="padding:10px 12px; font-weight:700; color:#B45309;">🟡 中軌支撐/壓力防守<br>(價格貼近 BB_Mid)</td>
                        <td style="padding:10px 12px; line-height:1.65;">20日均線扮演多空分水嶺，強勢多頭回踩中軌不破即彈升。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>回踩中軌低吸</strong>：多頭趨勢中以中軌作為移動防守止損點。</td>
                    </tr>
                    <tr style="background:#FEF2F2;">
                        <td style="padding:10px 12px; font-weight:700; color:#DC2626;">🔴 觸及上下軌反轉<br>(Price touches Upper/Lower Band)</td>
                        <td style="padding:10px 12px; line-height:1.65;">價格偏離均值過遠，在沒有走軌（Walking the Bands）前容易發生均值回歸。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>短線獲利了結</strong>：觸及上軌且量能萎縮時可考慮部分落袋為安。</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div style="font-size:0.82rem; color:#854D0E; margin-top:10px; line-height:1.6;">
            当前布林通道帶寬數值為 <strong>{bandwidth:.1f}%</strong>。
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 分頁 5：量價關係與籌碼分佈 (Volume Profile)
# ----------------------------------------------------
elif active_p5 == "tab5":
    st.markdown(f"### 🧱 五、{target_symbol} 量價關係與籌碼分佈支撐壓力位檢驗 (Volume Profile)")
    st.caption(f"當前視角：**【{selected_period}】** ｜ 按成交價格聚合真實成交量，左右 100% 水平對齊連動。")

    p_min = df_view['Low'].min()
    p_max = df_view['High'].max()
    num_bins = 24
    bins = np.linspace(p_min, p_max, num_bins + 1)
    
    bin_volumes = np.zeros(num_bins)
    for _, row in df_view.iterrows():
        mid_p = (row['High'] + row['Low']) / 2.0
        idx = int(np.clip(np.digitize(mid_p, bins) - 1, 0, num_bins - 1))
        bin_volumes[idx] += row['Volume']

    bin_centers = [(bins[i] + bins[i+1]) / 2.0 for i in range(num_bins)]
    max_vol_idx = np.argmax(bin_volumes)
    poc_price = bin_centers[max_vol_idx]

    fig_vp = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.02, column_widths=[0.75, 0.25])
    fig_vp.add_trace(go.Scatter(x=df_view.index, y=df_view['Close'], mode='lines', line=dict(color='#2D2622', width=2), name="價格走勢"), row=1, col=1)
    fig_vp.add_hline(y=poc_price, line_dash="dash", line_color="#D97706", annotation_text=f"主力最大籌碼峰 (${poc_price:.2f})")

    vp_colors = ['#D97706' if i == max_vol_idx else '#0284C7' for i in range(num_bins)]
    fig_vp.add_trace(go.Bar(
        x=bin_volumes, y=bin_centers,
        orientation='h',
        marker_color=vp_colors,
        name="各價位堆積量能"
    ), row=1, col=2)

    fig_vp.update_layout(
        height=520,
        margin=dict(t=35, b=25, l=15, r=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=12)),
        dragmode="pan",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF"
    )
    fig_vp.update_xaxes(range=initial_x_range, row=1, col=1, showgrid=False)
    fig_vp.update_xaxes(title_text="累積成交量", row=1, col=2, showgrid=False)

    fig_vp.update_yaxes(
        title_text="價格區間 ($)", 
        range=[y_min, y_max], 
        row=1, col=1, 
        showgrid=True, gridcolor='#F2ECE5'
    )
    fig_vp.update_yaxes(
        range=[y_min, y_max], 
        row=1, col=2, 
        showgrid=True, gridcolor='#F2ECE5'
    )
    st.plotly_chart(fig_vp, use_container_width=True, config={'scrollZoom': True}, key="p5_vp_perfect_view")

    st.markdown(f"""
    <div class="guide-box">
        <strong style="color: #0F766E; font-size: 1.05rem;">💡 【籌碼分佈實戰】POC 控制點與支撐壓力位操作矩陣</strong>
        <p style="color: #2D2622; margin: 6px 0 10px 0; font-size: 0.92rem; line-height: 1.65;">
            籌碼分佈（Volume Profile）顯示了在特定價格區間內累積的成交量多寡。實戰應用中，主力控制點（POC）扮演著最強大的磁吸與防守角色：
        </p>
        <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:0.89rem; text-align:left;">
                <thead>
                    <tr style="background:#FAF6F2; border-bottom:2px solid #D8CFC7; color:#4A3E36;">
                        <th style="padding:10px 12px; font-weight:800; width:22%;">現價與 POC 相對位置</th>
                        <th style="padding:10px 12px; font-weight:800; width:30%;">籌碼供需實質涵義</th>
                        <th style="padding:10px 12px; font-weight:800; width:48%;">實戰操作與進出場指引</th>
                    </tr>
                </thead>
                <tbody style="color:#2D2622;">
                    <tr style="border-bottom:1px solid #EFEAE2; background:#F0FDF4;">
                        <td style="padding:10px 12px; font-weight:700; color:#047857;">🟢 價格穩居 POC 上方<br>(Price > POC: ${poc_price:.2f})</td>
                        <td style="padding:10px 12px; line-height:1.65;">大部分持倉者處於獲利狀態，POC 成為下方最強大的支撐防線。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>回踩 POC 支撐承接</strong>：股價若回撤至 POC 附近縮量止跌，為極佳的順勢低吸點。</td>
                    </tr>
                    <tr style="border-bottom:1px solid #EFEAE2; background:#FFFBEB;">
                        <td style="padding:10px 12px; font-weight:700; color:#B45309;">🟡 價格橫盤穿梭 POC 區間<br>(Price near POC)</td>
                        <td style="padding:10px 12px; line-height:1.65;">多空雙方在最大籌碼堆積帶激烈換手，屬於成本共識區。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>區間來回操作</strong>：等待帶量脫離此密集區再做單邊跟隨。</td>
                    </tr>
                    <tr style="background:#FEF2F2;">
                        <td style="padding:10px 12px; font-weight:700; color:#DC2626;">🔴 價格跌破 POC 下方<br>(Price < POC: ${poc_price:.2f})</td>
                        <td style="padding:10px 12px; line-height:1.65;">多數籌碼陷入套牢，原先的支撐帶瞬間轉化為強大解套賣壓帶。</td>
                        <td style="padding:10px 12px; line-height:1.65;"><strong>反彈至 POC 附近減碼</strong>：若反彈無法重新站穩 POC，應視為弱勢反彈，防範進一步下殺。</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 💎 全域合規與免責宣告聲明 (Compliance & Regulatory Disclaimer)
# ==========================================
st.markdown("""
<div style="background:#FAF8F5; border:1px solid #E6DFD7; border-radius:8px; padding:14px 18px; margin-top:28px;">
    <div style="font-size:0.82rem; color:#786C60; line-height:1.6;">
        <strong>免責聲明與使用規範 (Regulatory Disclosure)：</strong><br>
        本系統所載之歷史行情、OHLCV 數據均源自公開市場交易所資料庫；各項技術指標（EMA、SMA、RSI、MACD、Bollinger Bands、Volume Profile）係透過標準開源量化公式進行數學運算產生。分析數據與圖表僅供機構級投研與技術分析輔助參考，不構成任何有價證券之買賣要約或投資保證。投資人應獨立審慎評估市場價格波動與技術面失效之風險。
    </div>
</div>
""", unsafe_allow_html=True)
