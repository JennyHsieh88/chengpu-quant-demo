import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from data_loader import fetch_macro_layer, fetch_stock_full_profile
from analytics import calculate_full_technicals, generate_institutional_score
from config import DEFAULT_TICKER, DEFAULT_PEERS

st.set_page_config(page_title="WallStreet Terminal", layout="wide", initial_sidebar_state="expanded")
st.title("🖥️ Institutional Multi-Layer Terminal (機構全維度決策系統)")

# 側邊欄配置
st.sidebar.header("🎯 核心配置")
ticker = st.sidebar.text_input("個股代碼 (Ticker)", value=DEFAULT_TICKER).upper()
peers_raw = st.sidebar.text_input("同業代碼 (逗號分隔)", value=",".join(DEFAULT_PEERS))
peer_list = [p.strip().upper() for p in peers_raw.split(",") if p.strip()]

# 數據載入
with st.spinner("正在載入全球市場與機構數據..."):
    macro = fetch_macro_layer()
    hist_df, fundamentals, peer_df = fetch_stock_full_profile(ticker, peer_list)
    
    if not hist_df.empty:
        # 去除時區避免繪圖報錯
        hist_df.index = hist_df.index.tz_localize(None) if hist_df.index.tz is not None else hist_df.index
        hist_df = calculate_full_technicals(hist_df)
        
    score_data = generate_institutional_score(macro, hist_df, fundamentals)

# 頂部：多空綜合決策總分卡
total_s = score_data['total']
verdict = "強烈看多 (Bullish)" if total_s >= 75 else "震盪偏多 (Neutral-Bull)" if total_s >= 55 else "中性觀望 (Neutral)" if total_s >= 40 else "風險警戒 (Bearish)"
st.metric("🎯 機構多空量化綜合評分", f"{total_s} / 100 分", delta=verdict)

# 頂部宏觀指標條 (Level 1 & 2)
st.markdown("#### 🌐 層級 1 & 2：總體宏觀 (Macro) 與市場情緒 (Sentiment)")
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("VIX 恐慌指數", f"{macro.get('vix', 0):.2f}", f"{macro.get('vix_change', 0):+.2f}%")
m2.metric("S&P 500", f"{macro.get('sp500', 0):.1f}", f"{macro.get('sp500_change', 0):+.2f}%")
m3.metric("恆生指數 HSI", f"{macro.get('hsi', 0):.1f}", f"{macro.get('hsi_change', 0):+.2f}%")
m4.metric("美元指數 DXY", f"{macro.get('dxy', 0):.2f}")
m5.metric("10Y-2Y 殖利率差", f"{macro.get('yield_spread', 0):.2f}%")
m6.metric("基準利率 / CPI", f"{macro.get('fed_rate', 0):.2f}% / {macro.get('cpi_yoy', 0):.1f}%")

st.divider()

# 4大分析 Tab
tab_tech, tab_fund, tab_peer, tab_street = st.tabs([
    "📈 層級 5：技術面與量價動量",
    "🏢 層級 4：個股基本面與體質",
    "⚖️ 層級 3：產業同儕橫向比較",
    "🎯 層級 6：華爾街共識與機構籌碼"
])

with tab_tech:
    if not hist_df.empty and len(hist_df) > 30:
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
        
        # 主圖：K線 + 均線 + 布林通道
        fig.add_trace(go.Candlestick(x=hist_df.index, open=hist_df['Open'], high=hist_df['High'], low=hist_df['Low'], close=hist_df['Close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['SMA_50'], line=dict(color='orange', width=1), name='50 MA'), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['SMA_200'], line=dict(color='blue', width=1.5), name='200 MA'), row=1, col=1)
        
        if 'BB_Upper' in hist_df.columns:
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['BB_Upper'], line=dict(color='gray', dash='dot'), name='布林上軌'), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['BB_Lower'], line=dict(color='gray', dash='dot'), name='布林下軌'), row=1, col=1)
        
        # 成交量
        if 'Volume' in hist_df.columns:
            fig.add_trace(go.Bar(x=hist_df.index, y=hist_df['Volume'], name='成交量', marker_color='teal'), row=2, col=1)
            
        # MACD
        if 'MACD' in hist_df.columns and 'MACD_Signal' in hist_df.columns:
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD'], line=dict(color='black', width=1), name='MACD'), row=3, col=1)
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD_Signal'], line=dict(color='red', width=1), name='Signal'), row=3, col=1)
        
        fig.update_layout(height=550, xaxis_rangeslider_visible=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        rsi_val = hist_df['RSI'].iloc[-1] if 'RSI' in hist_df.columns else 50
        c1.write(f"**即時 RSI (14):** {rsi_val:.2f} （>70 超買，<30 超賣）")
        sma50_val = hist_df['SMA_50'].iloc[-1] if 'SMA_50' in hist_df.columns else 0
        sma200_val = hist_df['SMA_200'].iloc[-1] if 'SMA_200' in hist_df.columns else 0
        c2.write(f"**均線排列:** {'多頭排列 (50MA > 200MA)' if sma50_val > sma200_val else '空頭/震盪排列'}")
    else:
        st.warning("查無足夠股價數據進行技術分析。")

with tab_fund:
    st.markdown("### 📊 核心財報指標 (Financial Health)")
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("毛利率 (Gross Margin)", f"{fundamentals.get('gross_margin', 0):.2f}%")
    f2.metric("營業利益率", f"{fundamentals.get('operating_margin', 0):.2f}%")
    f3.metric("ROE 股東權益報酬率", f"{fundamentals.get('roe', 0):.2f}%")
    f4.metric("營收年增率 (YoY)", f"{fundamentals.get('revenue_growth', 0):.2f}%")
    
    st.write(f"- **歷史本益比 (Trailing P/E):** {fundamentals.get('pe_trailing', 'N/A')}")
    st.write(f"- **預估本益比 (Forward P/E):** {fundamentals.get('pe_forward', 'N/A')}")
    st.write(f"- **負債/股東權益比 (D/E):** {fundamentals.get('debt_to_equity', 'N/A')}")

with tab_peer:
    st.markdown("### 🏢 同業估值橫向對比 (Relative Valuation)")
    if not peer_df.empty:
        st.dataframe(peer_df, use_container_width=True)
    else:
        st.info("請在側邊欄輸入同業股票代碼以進行比較。")

with tab_street:
    st.markdown("### 🎯 華爾街分析師與籌碼分佈")
    current_p = hist_df['Close'].iloc[-1] if not hist_df.empty else 0
    t_median = fundamentals.get('target_median') or current_p
    upside = ((t_median - current_p) / current_p) * 100 if current_p else 0
    
    s1, s2, s3 = st.columns(3)
    s1.metric("目標價中位數", f"${t_median:.2f}", f"空間: {upside:+.2f}%")
    s2.metric("機構法人持股比例", f"{fundamentals.get('institution_pct', 0):.2f}%")
    s3.metric("放空比率 (Short Ratio)", f"{fundamentals.get('short_ratio', 'N/A')}")
    st.write(f"華爾街綜合評等方向: **{str(fundamentals.get('recommendation', 'N/A')).upper()}**")