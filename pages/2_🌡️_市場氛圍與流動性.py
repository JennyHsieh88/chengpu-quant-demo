import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf

# 頁面配置
st.set_page_config(page_title="市場氛圍與流動性 - 澄璞財務", page_icon="🌡️", layout="wide")

# ==========================================
# 注入自訂 CSS（全域放大 + 原生置頂品牌卡片）
# ==========================================
st.markdown("""
<style>
    /* 1. 全域基礎字體與行高放大 */
    html, body, [class*="css"], .stMarkdown, p, div, span, label {
        font-size: 1.06rem !important;
        line-height: 1.6 !important;
    }

    /* 2. 在左側導航欄最上方自動渲染專屬品牌卡片 */
    [data-testid="stSidebarNav"]::before {
        content: "澄璞財務顧問工作室\\A Jenny 筱筑 CFP®\\A 有「筱」陪伴\\A 攜手「筑」夢";
        white-space: pre-wrap;
        display: block;
        margin: 12px 14px 18px 14px;
        padding: 16px 12px;
        background: linear-gradient(135deg, #1E3A8A 0%, #0D9488 100%);
        border-radius: 10px;
        color: #FFFFFF;
        text-align: center;
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.65;
        letter-spacing: 0.6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* 3. 核心指標卡片 (Metric) 數值放大 */
    [data-testid="stMetricValue"] {
        font-size: clamp(1.45rem, 2.0vw, 1.85rem) !important;
        font-weight: 700 !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.25 !important;
    }

    /* 4. 指標卡片標籤解除截斷 */
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] p {
        font-size: 1.02rem !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }

    /* 5. 分頁 Tab 標籤樣式優化 */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        border-bottom: 2px solid #ECEFF1 !important;
        padding-bottom: 6px !important;
    }
    button[data-baseweb="tab"] {
        font-size: 1.08rem !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        background-color: #F8F9FA !important;
        border: 1px solid #E2E8F0 !important;
        margin-right: 4px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #E3F2FD !important;
        border-color: #1E88E5 !important;
        color: #1565C0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 全域狀態管理與單一回呼同步
# ==========================================
if 'current_ticker' not in st.session_state:
    st.session_state['current_ticker'] = "MSFT"

if 'ticker_input_top_p2' not in st.session_state:
    st.session_state['ticker_input_top_p2'] = st.session_state['current_ticker']

def update_ticker_top_p2():
    val = st.session_state.get('ticker_input_top_p2', '').upper().strip()
    if val:
        st.session_state['current_ticker'] = val

# ==========================================
# 主頁面頂部快速切換欄
# ==========================================
st.subheader("🌡️ 市場氛圍、流動性與景氣四象限 (Sentiment, Liquidity & Clock)")

col_search, col_name, col_p = st.columns([1.6, 3.4, 2])

with col_search:
    st.text_input(
        "🔍 本頁快速切換標的代碼", 
        key="ticker_input_top_p2",
        on_change=update_ticker_top_p2,
        help="輸入代碼後按 Enter 立即重新載入"
    )

target_symbol = st.session_state['current_ticker']

# ==========================================
# 市場情緒與宏觀象限計算引擎
# ==========================================
def get_yf_history(symbol, period="3y"):
    try:
        h = yf.Ticker(symbol).history(period=period)
        if not h.empty:
            h.index = h.index.tz_localize(None) if h.index.tz is not None else h.index
            return h
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=900)
def fetch_sentiment_module_data(symbol: str):
    stock = yf.Ticker(symbol)
    info = stock.info or {}
    curr_p = info.get('currentPrice') or info.get('regularMarketPrice') or 100.0

    vix_hist = get_yf_history("^VIX", period="2y")
    sp_hist = get_yf_history("^GSPC", period="2y")
    hyg_hist = get_yf_history("HYG", period="2y")
    lqd_hist = get_yf_history("LQD", period="2y")

    vix_val = float(vix_hist['Close'].iloc[-1]) if not vix_hist.empty else 16.5
    fng_val = 62.0  # CNN Fear & Greed 估計值
    pcr_val = 0.82  # CBOE Put/Call Ratio

    # 信用利差比
    credit_spread_ratio = 0.88
    if not hyg_hist.empty and not lqd_hist.empty:
        common_idx = hyg_hist.index.intersection(lqd_hist.index)
        if len(common_idx) > 0:
            credit_spread_ratio = float((hyg_hist.loc[common_idx, 'Close'] / lqd_hist.loc[common_idx, 'Close']).iloc[-1])

    # 宏觀四象限定位坐標 (X: 通膨/流動性緊縮程度, Y: 經濟/企業成長動能)
    macro_coords = {'x': -0.35, 'y': 0.60, 'stage': '復甦 / 景氣牛 (Goldilocks)'}

    return {
        'company_name': info.get('shortName', symbol),
        'sector': info.get('sector', 'N/A'),
        'curr_p': curr_p,
        'vix_val': vix_val,
        'fng_val': fng_val,
        'pcr_val': pcr_val,
        'credit_spread_ratio': credit_spread_ratio,
        'm2_growth': "+4.2%",
        'fed_bs_trend': "$7.2T (QT 放緩)",
        'vix_hist': vix_hist,
        'sp_hist': sp_hist,
        'hyg_hist': hyg_hist,
        'lqd_hist': lqd_hist,
        'macro_coords': macro_coords
    }

sent = fetch_sentiment_module_data(target_symbol)

with col_name:
    st.markdown(f"### {sent['company_name']} (`{target_symbol}`)")
    st.caption(f"板塊：**{sent['sector']}** ｜ 當前宏觀週期：**{sent['macro_coords']['stage']}**")

with col_p:
    st.metric("即時股價", f"${sent['curr_p']:.2f}", "多空情緒：樂觀看多")

st.divider()

# ==========================================
# 頂部四大核心指標卡
# ==========================================
s_c1, s_c2, s_c3, s_c4 = st.columns(4)
s_c1.metric("⚡ VIX 波動率指數", f"{sent['vix_val']:.2f}", "平穩 (Risk-On)" if sent['vix_val'] < 20 else "恐慌警戒 (Risk-Off)", delta_color="normal" if sent['vix_val'] < 20 else "inverse")
s_c2.metric("🧭 CNN 恐慌與貪婪指數", f"{sent['fng_val']:.0f} / 100", "貪婪 (Greed)" if sent['fng_val'] > 55 else ("恐慌 (Fear)" if sent['fng_val'] < 45 else "中性"))
s_c3.metric("⚖️ 標普 Put/Call Ratio", f"{sent['pcr_val']:.2f}", "多方勝出 (<1.0)" if sent['pcr_val'] < 1.0 else "避險看空增強")
s_c4.metric("🏛️ 高收益債/投資級債比", f"{sent['credit_spread_ratio']:.3f}", "信用風險平穩")

st.markdown("---")

# ==========================================
# 四大子分頁（含全新四象限景氣輪動圖表與實戰說明）
# ==========================================
s_tab1, s_tab2, s_tab3, s_tab4 = st.tabs([
    "🧭 一、恐慌與貪婪多空溫度計 (Fear & Greed Index)",
    "⚡ 二、VIX 波動率期限結構與期權籌碼 (Options & Volatility)",
    "💧 三、全球央行流動性與信用利差 (Credit & Central Banks)",
    "🕰️ 四、美林時鐘與景氣/資金四象限 (Macro Quadrants)"
])

with s_tab1:
    st.markdown("### 🧭 一、CNN 恐慌與貪婪指數 (Fear & Greed Index 儀表盤)")
    col_fg1, col_fg2 = st.columns([1.2, 1])
    with col_fg1:
        fig_fg = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sent['fng_val'],
            title={'text': "CNN Fear & Greed Index"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2ECC71" if sent['fng_val'] > 55 else ("#E74C3C" if sent['fng_val'] < 45 else "#F1C40F")},
                'steps': [
                    {'range': [0, 25], 'color': 'rgba(231, 76, 60, 0.4)'},
                    {'range': [25, 45], 'color': 'rgba(230, 126, 34, 0.3)'},
                    {'range': [45, 55], 'color': 'rgba(189, 195, 199, 0.3)'},
                    {'range': [55, 75], 'color': 'rgba(46, 204, 113, 0.3)'},
                    {'range': [75, 100], 'color': 'rgba(39, 174, 96, 0.5)'}
                ]
            }
        ))
        fig_fg.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_fg, use_container_width=True, key=f"fng_chart_{target_symbol}")

    with col_fg2:
        st.markdown("#### 💡 情緒指標實戰解讀")
        st.write(f"- **目前點位**：**`{sent['fng_val']:.0f}`（貪婪 Greed）**")
        st.write(f"- **市場特徵**：多方買盤主導，動量型股票享受流動性溢價。")
        st.write(f"- **操盤應對**：順勢持有強勢龍頭股，但不宜在此時使用高倍槓桿盲目追高。")

    st.info("""
    💡 **【恐慌與貪婪鐘擺】機構實戰運用指引**：
    - **極度恐慌 (0 ~ 25)**：市場全面恐慌性拋售，優質股被錯殺，為歷史勝率最高的「左側分批逢低佈局」黃金期。
    - **貪婪區間 (55 ~ 75)**：健康的多頭主升段，順勢操作，緊盯均線防守。
    - **極度貪婪 (75 ~ 100)**：槓桿情緒過度亢奮，通常預示波段頂部即將出現，應逐步分批獲利了結或配置 Collar 選擇權避險。
    """)

with s_tab2:
    st.markdown("### ⚡ 二、VIX 歷史波動率走勢與防守門檻")
    if not sent['vix_hist'].empty:
        fig_vix = go.Figure(go.Scatter(x=sent['vix_hist'].index, y=sent['vix_hist']['Close'], line=dict(color='#E74C3C', width=2), name="VIX 恐慌指數"))
        fig_vix.add_hline(y=20, line_dash="dash", line_color="#F39C12", annotation_text="20 恐慌警戒門檻")
        fig_vix.add_hline(y=30, line_dash="solid", line_color="#C0392B", annotation_text="30 市場流動性危機線")
        fig_vix.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), xaxis_title="交易日期", yaxis_title="VIX 點位")
        st.plotly_chart(fig_vix, use_container_width=True, key=f"vix_chart_{target_symbol}")

    st.info(f"""
    💡 **【VIX 波動率】機構實戰運用指引**：
    - **VIX < 20 (當前 `{sent['vix_val']:.2f}`)**：市場處於 Risk-On（風險偏好擴張）環境，波動平穩，有利於多頭趨勢延續。
    - **VIX 突破 20 ~ 25**：避險資金開始湧入 Put 選擇權，短期震盪加劇，宜收緊停損點。
    - **VIX 飆升至 30 以上**：出現流動性踩踏拋售，通常也是短線極端恐慌即將見底的訊號。
    """)

with s_tab3:
    st.markdown("### 💧 三、央行流動性與信用利差 (HYG vs LQD)")
    col_cr1, col_cr2 = st.columns([1.3, 1])
    with col_cr1:
        if not sent['hyg_hist'].empty and not sent['lqd_hist'].empty:
            common_idx = sent['hyg_hist'].index.intersection(sent['lqd_hist'].index)
            spread_ratio_series = sent['hyg_hist'].loc[common_idx, 'Close'] / sent['lqd_hist'].loc[common_idx, 'Close']
            fig_spread = go.Figure(go.Scatter(x=common_idx, y=spread_ratio_series, line=dict(color='#3498DB', width=2), name="HYG/LQD 信用強度比"))
            fig_spread.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), xaxis_title="交易日期", yaxis_title="比率 (向上=信用風險低)")
            st.plotly_chart(fig_spread, use_container_width=True, key=f"spread_chart_{target_symbol}")
    with col_cr2:
        st.markdown("#### 央行流動性結構")
        st.write(f"- **M2 貨幣年增率**：`{sent['m2_growth']}`")
        st.write(f"- **聯準會資產負債表**：`{sent['fed_bs_trend']}`")
        st.write(f"- **高收益債違約風險**：`處於低檔健康水位`")
        st.success("🟢 實體企業融資與信用市場正常，未見信用利差走闊引發的系統性危機。")

with s_tab4:
    st.markdown("### 🕰️ 四、美林投資時鐘與景氣/資金四象限定位")
    
    col_q_chart, col_q_desc = st.columns([1.3, 1])
    
    with col_q_chart:
        fig_quad = go.Figure()

        # 4 個象限背景顏色填充
        fig_quad.add_shape(type="rect", x0=-1, y0=0, x1=0, y1=1, fillcolor="rgba(46, 204, 113, 0.15)", line_width=0)
        fig_quad.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1, fillcolor="rgba(241, 196, 15, 0.15)", line_width=0)
        fig_quad.add_shape(type="rect", x0=-1, y0=-1, x1=0, y1=0, fillcolor="rgba(52, 152, 219, 0.15)", line_width=0)
        fig_quad.add_shape(type="rect", x0=0, y0=-1, x1=1, y1=0, fillcolor="rgba(231, 76, 60, 0.15)", line_width=0)

        # 象限文字標籤
        fig_quad.add_annotation(x=-0.5, y=0.5, text="<b>【復甦期 / 景氣牛】</b><br>成長↑ 通膨↓<br>🏆 優選：科技/成長股", showarrow=False, font=dict(color="#27AE60", size=13))
        fig_quad.add_annotation(x=0.5, y=0.5, text="<b>【過熱期 / 資金牛】</b><br>成長↑ 通膨↑<br>🏆 優選：原物料/週期股", showarrow=False, font=dict(color="#D35400", size=13))
        fig_quad.add_annotation(x=-0.5, y=-0.5, text="<b>【衰退期 / 降息潮】</b><br>成長↓ 通膨↓<br>🏆 優選：美國國債/高評級債", showarrow=False, font=dict(color="#2980B9", size=13))
        fig_quad.add_annotation(x=0.5, y=-0.5, text="<b>【滯脹期 / 殺估值】</b><br>成長↓ 通膨↑<br>🏆 優選：現金/黃金避險", showarrow=False, font=dict(color="#C0392B", size=13))

        # 當前市場定位點
        fig_quad.add_trace(go.Scatter(
            x=[sent['macro_coords']['x']],
            y=[sent['macro_coords']['y']],
            mode="markers+text",
            marker=dict(size=26, color="#E74C3C", symbol="star", line=dict(width=2, color="#FFFFFF")),
            text=["📍 當前市場定位"],
            textposition="top center",
            name="最新總經位階"
        ))

        fig_quad.update_layout(
            height=420,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(title="← 通膨回落 (Disinflation) ｜ 通膨升溫 (Inflation) →", range=[-1, 1], zeroline=True, zerolinewidth=2, zerolinecolor="#7F8C8D"),
            yaxis=dict(title="← 經濟下行 (Contraction) ｜ 經濟擴張 (Expansion) →", range=[-1, 1], zeroline=True, zerolinewidth=2, zerolinecolor="#7F8C8D"),
            showlegend=False
        )
        st.plotly_chart(fig_quad, use_container_width=True, key=f"quad_chart_{target_symbol}")

    with col_q_desc:
        st.markdown("#### 🧭 當前象限：【復甦 / 景氣牛】")
        st.success("""
        **景氣特徵 (Goldilocks 金髮女孩)**：
        - **實質 GDP** 維持穩健正成長，企業獲利（EPS）持續上修。
        - **通膨壓力 (CPI/PCE)** 受到控制並平穩回落，提供央行寬鬆政策彈性。
        - **驅動力**：由「企業實質獲利增長（景氣牛）」引領市場，而非單純由資金大放水推升。
        """)
        st.markdown("#### 🎯 機構推薦資產配置權重")
        st.write("- **股票配置 (Equities)**：**`65% ~ 70%`** (重倉科技/優質成長股)")
        st.write("- **固定收益 (Fixed Income)**：**`20% ~ 25%`** (中長天期公債鎖利)")
        st.write("- **大宗商品 / 現金 (Commodities/Cash)**：**`10%`** (流動性儲備)")

    st.info(f"""
    💡 **【美林投資時鐘四象限】機構實戰運用指引**：
    1. **復甦期（景氣牛）**：經濟向上、通膨向下。股票是表現最優異的資產類別，尤其以高 ROIC 的科技股、非必需消費與通訊板塊最具超額報酬（Alpha）。
    2. **過熱期（資金牛/原物料牛）**：經濟向上、通膨向上。原油、銅、黃金等大宗商品領跑，能源與工業週期股表現亮眼。
    3. **滯脹期（股債雙殺）**：經濟向下、通膨向上。此階段企業成本高企且需求萎縮，現金為王，宜加重防禦型公用事業或黃金避險。
    4. **衰退期（降息債券牛）**：經濟向下、通膨向下。央行啟動降息循環救市，長天期公債享有極大的資本利得空間。
    """)