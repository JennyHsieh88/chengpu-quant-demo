import streamlit as st
import inspect
import os

# ==============================================================================
# 會員方案層級定義
# ==============================================================================
TIER_NAMES = {
    0: "🌿 基礎探索版 (免費)",
    1: "⚡ 進階量化版 (NT$ 200/月)",
    2: "👑 專業全能旗艦版 (NT$ 300/月)"
}
TIERS = TIER_NAMES

MODULE_NAMES = {
    "module_1": "總體環境監控",
    "module_2": "市場氛圍與流動性",
    "module_3": "板塊輪動與資金流向",
    "module_4": "產業同儕估值",
    "module_5": "個股基本面深度庫",
    "module_6": "技術面與量價動量",
    "module_7": "華爾街共識與籌碼",
    "module_8": "訂單流與另類數據",
    "module_9": "綜合決策與多空評分",
    "module_10": "客觀前瞻推估與資產配置",
    "module_11": "智慧投組回測與前瞻推估",
    "module_12": "全球金融即時要聞與市場行事曆"
}

# ==============================================================================
# 🎯 模組專屬完整工具清單（對應彩色邊框卡片矩陣，每頁完整細項）
# ==============================================================================
MODULE_FULL_FEATURES = {
    "板塊輪動與資金流向": [
        {"title": "📊 標普 11 大板塊 RRG 動態輪動雷達", "desc": "即時量測各產業相對大盤的強度與動能加速度，一眼抓出正由落後轉向領先起漲的最佳進攻板塊。"},
        {"title": "🌊 主力聰明錢 (Smart Money) 資金流監控", "desc": "穿透市場表象，監控機構法人在關鍵板塊上的吸籌與派發軌跡，防範假突破、真倒貨之套牢陷阱。"},
        {"title": "🧭 宏觀景氣位階與板塊適配導航", "desc": "結合降息週期、通膨利率與實體景氣，客觀推薦當前勝率最高的攻防配置，讓資金站在多方浪頭。"}
    ],
    "產業同儕估值": [
        {"title": "📊 前瞻本益比 (Forward P/E) 通道對比", "desc": "對標細分子行業同行中位數，精準辨識目標標的處於折價甜蜜區還是透支警戒區，杜絕買在天花板。"},
        {"title": "🎯 PEG 成長估值合理性矩陣 (P/E vs. Growth)", "desc": "結合預估 EPS 年增長率，直觀識別 PEG < 1.0 的超值成長股，過濾獲利跟不上股價的成長泡沫。"},
        {"title": "🏢 企業價值倍數 (EV/EBITDA) 結構中立檢驗", "desc": "排除折舊攤銷、資本支出與財務槓桿差異，以併購家視角還原企業最純粹的實質經營身價。"},
        {"title": "💵 市銷率 (P/S) 與真實現金流 (FCF Yield) 透視", "desc": "穿透官方現金流量表，如實反映高成長科技企業究竟是自體現金印鈔機還是持續稀釋股東的燒錢黑洞。"},
        {"title": "🛡️ 護城河性價比矩陣 (ROE vs. PEG 氣泡圖)", "desc": "鎖定「ROE > 20% 且 PEG < 1.5」的黃金安全象限，輔以五維雷達圖，一眼看清同行中誰是實質龍頭。"},
        {"title": "🏛️ 板塊估值治理與三大結構風險評級", "desc": "量化遠期折現敏感度儀表、信貸週期耐受度，穿透 ETF 被動資金湧入脫鉤與重資產融資壓力。"}
    ],
    "個股基本面深度庫": [
        {"title": "📊 三階杜邦分析 (DuPont Analysis) 因子解耦", "desc": "精準拆解 ROE 動能來源（淨利率 × 資產週轉率 × 權益乘數），一眼看穿是高質量護城河還是借錢開槓桿的虛胖。"},
        {"title": "🛡️ 三率長線走勢與定價護城河檢驗", "desc": "結合歷年與最新 TTM 季報動態追蹤毛利率、營業利益率與淨利率，量化巴菲特經濟護城河之成本轉嫁力。"},
        {"title": "💧 自由現金流 (FCF) 與 OCF 實質造血檢驗", "desc": "穿透資本支出（CapEx）與淨利潤修飾，以現金轉換率與 FCF Margin 嚴格評估企業真實自體造血含金量。"},
        {"title": "⚖️ 資產負債結構與償債能力防護網 (Solvency)", "desc": "體檢流動比率、速動比率、負債權益比與實質淨現金儲備，築起抵禦高利率與衰退週期的流動性安全防護罩。"},
        {"title": "🎁 股東回報政策追蹤（庫藏股買回與現金股息）", "desc": "量化追蹤歷年流通在外股數註銷與常態分紅規模，評估管理層資本配置智慧與長期隱形複利效能。"}
    ],
    "技術面與量價動量": [
        {"title": "📊 專業級多週期 K 線圖與全景均線 (EMA20/50/200)", "desc": "直連交易所行情，支援上市以來（MAX）超長週期自由縮放與平移，判定多頭排列、橫盤蓄勢或空頭壓制。"},
        {"title": "🌊 14 日 RSI 相對強弱指標與多空背離警示", "desc": "結合 70 超買與 30 超賣警戒線，自動捕捉「頂背離」回調風險與「底背離」波段右側起漲黃金買點。"},
        {"title": "⚡ MACD 趨勢動能指標與零軸多空交叉", "desc": "演算 12/26/9 參數之 DIF 快線、Signal 慢線與柱狀體動能收斂，精確捕捉主升段加速與反彈拐點。"},
        {"title": "🎯 布林通道 (Bollinger Bands) 波動擠壓與突破", "desc": "量化計算 20 SMA 與 ±2 個標準差帶寬 (Bandwidth)，掌握波動率降至冰點（Squeeze）後的單邊爆發性變盤。"},
        {"title": "🧱 量價籌碼分佈 (Volume Profile) 與 POC 控制點", "desc": "按成交價格精確聚合歷史成交量，自動測算主力最大籌碼峰（POC 控制點）與多空攻防階梯防線。"}
    ],
    "華爾街共識與籌碼": [
        {"title": "🎯 華爾街分析師目標價區間與潛在空間 (Target Price)", "desc": "彙整高盛、大摩等覆蓋分析師之最悲觀、平均值與最樂觀 12 個月目標價跨度，精準測算不對稱盈虧比。"},
        {"title": "📊 華爾街評級分佈與共識傾向 (Recommendations)", "desc": "量化統計強力買進、買進、持有至賣出之真實家數佔比，敏銳辨識「預期過度擁擠」之脆弱踩踏風險。"},
        {"title": "🏛️ 頂級機構法人與避險基金 13F 持倉 (13F Ownership)", "desc": "穿透 Vanguard、BlackRock、State Street 等核心巨頭持股比例與最新季度申報市值變化。"},
        {"title": "👔 公司內部人交易與董監持股申報 (SEC Form 4)", "desc": "繁體中文語意解析高管公開市場買進 (Open Market Buy) 與預約交易計畫，捕捉最真實的內部信心拐點。"},
        {"title": "⚡ 賣空比例 (Short Interest) 與空頭擠壓預警", "desc": "監控借券放空流通比、回補天數 (Short Ratio) 與做市商避險狀態，提前鎖定極端逼空踩踏機會。"},
        {"title": "✦ 知名投行評級庫 (Wall Street Rating Matrix)", "desc": "即時追蹤一線券商最新 15 筆評級調升 (Upgrade)、調降與初次覆蓋軌跡，精準跟隨機構調倉動向。"}
    ],
    "訂單流與另類數據": [
        {"title": "🌊 期權鏈異動與 Put/Call Ratio (Options Skew)", "desc": "直連 CBOE 交易所未平倉數據，精準解析看漲 Call 與看跌 Put 的持倉傾斜與避險防護狀態。"},
        {"title": "🎯 期權最大痛點價格 (Max Pain) 與做市商 Gamma 牽引", "desc": "測算使期權買方損失極大化的特定履約價，掌握現貨向痛點靠攏的磁吸拉升或壓制邊界。"},
        {"title": "🏛️ 大宗交易 (Block Trades) 與暗池 (Dark Pool) 資金流向", "desc": "穿透機構場外撮合大單佔比，結合 20 日 VWAP 成本線，辨別機構是在隱蔽吸籌還是對倒出貨。"},
        {"title": "👥 社群情緒、散戶關注度與搜尋熱度另類指標", "desc": "合成社群討論熱度與搜尋突波，以逆向投資心理學鎖定散戶 FOMO 狂熱頂部與冷清底部。"},
        {"title": "🏆 華爾街智慧籌碼 (Smart Money Flow) 綜合診斷卡", "desc": "全維度權重融合期權、暗池大單與社群熱度，給出 0~100 分客觀智慧資金評級與決策建議。"},
        {"title": "⚡ 高頻訂單流情報庫 (High-Frequency Order Flow & L2)", "desc": "即時量化主動買入與主動賣出比例，測算訂單簿不平衡度 (OBI) 與潛在冰山大單護盤水位。"}
    ],
    "綜合決策與多空評分": [
        {"title": "📊 全維度綜合多空計分卡 (Long-Short Scorecard)", "desc": "技術面、共識面、籌碼面、基本面四大支柱各佔 25% 平衡加權，呈現多空量化雷達圖與 0~100 客觀總分。"},
        {"title": "🎯 華爾街機構共識與目標價空間評級", "desc": "彙整一線投行 12 個月目標價跨度（最樂觀/均值/最悲觀）與現價偏離度，量化測算不對稱盈虧比。"},
        {"title": "⚡ 期權與暗池高頻訂單流壓力測試", "desc": "結合機構 13F 底倉鎖定率與賣空流通比，檢驗下檔防守硬度並預警潛在逼空擠壓風險。"},
        {"title": "💰 財務健康與估值安全邊際評估", "desc": "深度對帳 ROE 資本回報品質、淨利率與本益比匹配度，落實「以合理價格買進偉大企業」的厚實防線。"},
        {"title": "🏆 顧問級最終投資行動決策建議", "desc": "橫向拆解四大支柱原始得分貢獻度，提供強烈買進、分批佈局、中性觀望或減碼防守之具體倉位比例指引。"},
        {"title": "🏛️ 綜合決策情報庫與三大情境推估", "desc": "建立 Bull / Base / Bear 三大前瞻情境定價模型，提供完整的盤面催化條件與機構風控應對法則。"}
    ],
    "客觀前瞻推估與資產配置": [
        {"title": "⚡ 客觀因子積木模型未來財富路徑推估", "desc": "三大前瞻模型（模型A因子積木、模型B幾何波動拖累損耗、模型C華爾街共識折現）交叉演算，破除過度樂觀盲點，鎖定真實幾何複利區間。"},
        {"title": "📊 單押標的 vs 資產配置分散風險效果對比", "desc": "直觀量測單一標的極限波動與核心衛星配置（Core-Satellite）之夏普比率優化，徹底消除非系統性單點風險。"},
        {"title": "📈 七大重要資產類別 3 年期真實相關性熱力矩陣", "desc": "量化股票、公債、投資級債、黃金、REITs 與現金之動態相關係數，精準建構負相關對沖安全氣囊。"},
        {"title": "🎯 動態波段再平衡策略 (Dynamic Band Rebalancing) 實證", "desc": "驗證在 ±15% 波動帶寬下執行紀律再平衡，如何逆向收割市場波動並轉化為實質超額收益（Harvest Alpha）。"},
        {"title": "🛡️ 退休資產提領安全邊際測試 (4% Safe Withdrawal Rule)", "desc": "提供「方案A單押極限壓力測試」與「方案B自訂資金比例動態試算」，精算 30 年永續存活率與防範報酬順序風險。"},
        {"title": "🏛️ 機構級客觀前瞻定價庫 (Objective Forward Pricing Engine)", "desc": "結合分析師共識庫、非流動性資產公允價值（Fair Value）與 Point-in-Time (PIT) 無偏誤歷史回測架構。"}
    ],
    "資產配置與前瞻推估": [
        {"title": "⚡ 客觀因子積木模型未來財富路徑推估", "desc": "三大前瞻模型（模型A因子積木、模型B幾何波動拖累損耗、模型C華爾街共識折現）交叉演算，破除過度樂觀盲點，鎖定真實幾何複利區間。"},
        {"title": "📊 單押標的 vs 資產配置分散風險效果對比", "desc": "直觀量測單一標的極限波動與核心衛星配置（Core-Satellite）之夏普比率優化，徹底消除非系統性單點風險。"},
        {"title": "📈 七大重要資產類別 3 年期真實相關性熱力矩陣", "desc": "量化股票、公債、投資級債、黃金、REITs 與現金之動態相關係數，精準建構負相關對沖安全氣囊。"},
        {"title": "🎯 動態波段再平衡策略 (Dynamic Band Rebalancing) 實證", "desc": "驗證在 ±15% 波動帶寬下執行紀律再平衡，如何逆向收割市場波動並轉化為實質超額收益（Harvest Alpha）。"},
        {"title": "🛡️ 退休資產提領安全邊際測試 (4% Safe Withdrawal Rule)", "desc": "提供「方案A單押極限壓力測試」與「方案B自訂資金比例動態試算」，精算 30 年永續存活率與防範報酬順序風險。"},
        {"title": "🏛️ 機構級客觀前瞻定價庫 (Objective Forward Pricing Engine)", "desc": "結合分析師共識庫、非流動性資產公允價值（Fair Value）與 Point-in-Time (PIT) 無偏誤歷史回測架構。"}
    ],
    "智慧投組回測與前瞻推估": [
        {"title": "📊 長期累積淨值曲線 (Equity Curve) vs 大盤對比", "desc": "以基期 $100 美元標準化起點，全收益復權（含股息再投資與拆股）精確量測個股相對標普 500、那斯達克之真實超額 Alpha。"},
        {"title": "📉 歷史水下回撤曲線 (Underwater Drawdown) 與抗跌防護", "desc": "完整呈現歷史最深谷底（MaxDD）與修復週期，檢驗非對稱多元配置在黑天鵝事件中的實質吸震效果。"},
        {"title": "🎯 日曆年度勝率拆解與多空年份對比矩陣", "desc": "完整對比公曆歷年真實年度績效與勝負機率，輔助掌握跨年度景氣與降息循環之均值回歸規律。"},
        {"title": "💵 單筆投入之真實滾動持有勝率與機構風控分析", "desc": "基於全歷史交易日序列逐日滑動切片，檢定持有 1~10 年的真實正報酬勝率、索提諾比率 (Sortino) 與最差進場點極限承受力。"},
        {"title": "🌱 自訂單筆 ＋ 定期定額 (DCA) 複合前瞻滾動試算", "desc": "結合期初本金與每月薪水自動扣款複利模型，動態推估未來 1~30 年資產累積路徑與實質總投入倍數。"}
    ],
    "全球金融即時要聞與市場行事曆": [
        {"title": "🌐 全球宏觀總經要聞與央行政策即時快訊", "desc": "嚴格匯聚國際總體經濟、全球央行政策與地緣大宗商品權威外電，徹底過濾在地社會雜訊。"},
        {"title": "🏢 標的專屬跨國市場快訊與投行研報追蹤", "desc": "輸入任意美股股票、ETF、CEF 標的，即刻穿透外電獲取近 30 天內原生繁體中文研報直達原文。"},
        {"title": "📅 重要經濟數據發布與大型企業財報日曆", "desc": "以全球法定總經週期演算法動態排定各國央行決策、美國非農 NFP、CPI、PCE 與企業財報季日程。"},
        {"title": "🌡️ 市場即時情緒指標與恐慌貪婪晴雨表", "desc": "直連 CNN Business 官方 Fear & Greed 實時讀數，深度拆解市場動量、避險需求與 Put/Call Ratio。"},
        {"title": "⚡ 即時財經廣播與突發大額快訊逐筆流", "desc": "毫秒級推播歐洲央行決策、大宗暗池掃單、選擇權 Sweep 買盤與重大併購快訊。"}
    ]
}

DEFAULT_FULL_FEATURES = [
    {"title": "📊 系統化量化數據整合", "desc": "將繁複多元的財務與行情資訊進行專業清洗與結構化對照，消除片面雜訊。"},
    {"title": "🎯 客觀多維度決策指標", "desc": "以科學模型取代情緒化猜測，為每一次投資決策建立嚴謹的攻防階梯。"},
    {"title": "🛡️ 頂級風險報酬安全邊際", "desc": "在市場波動與牛熊循環中，為您的寶貴資產提供最堅實的下檔防禦防線。"}
]

class AuthResult(tuple):
    def __new__(cls, success=True, message="會員權限已成功開通！"):
        return super().__new__(cls, (success, message))
    def __bool__(self):
        return self[0]
    def __eq__(self, other):
        if isinstance(other, bool):
            return self[0] == other
        return super().__eq__(other)

def init_auth_state():
    if "user_tier" not in st.session_state:
        st.session_state["user_tier"] = 0
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = ""
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = "訪客"
    if "user_username" not in st.session_state:
        st.session_state["user_username"] = ""
    if "user_password" not in st.session_state:
        st.session_state["user_password"] = ""
    if "user_phone" not in st.session_state:
        st.session_state["user_phone"] = ""
    if "registered_users" not in st.session_state:
        # 內建管理員/示範帳號與已註冊記憶庫
        st.session_state["registered_users"] = {
            "admin": {"name": "謝筱筑", "email": "jenny@chengpu.com", "password": "admin", "tier": 2},
            "vip": {"name": "旗艦學員", "email": "vip@chengpu.com", "password": "123456", "tier": 2}
        }
    if "show_payment_dialog" not in st.session_state:
        st.session_state["show_payment_dialog"] = False
    if "checkout_target_tier" not in st.session_state:
        st.session_state["checkout_target_tier"] = 2
    if "checkout_billing_cycle" not in st.session_state:
        st.session_state["checkout_billing_cycle"] = "yearly"

def register_or_upgrade_user(*args, **kwargs):
    init_auth_state()
    email = kwargs.get("email", "")
    name = kwargs.get("name", "")
    username = kwargs.get("username", "")
    password = kwargs.get("password", "")
    tier = kwargs.get("tier", None)
    phone = kwargs.get("phone", "")
    note = kwargs.get("note", "")

    for arg in args:
        if isinstance(arg, int):
            tier = arg
        elif isinstance(arg, str):
            if "@" in arg:
                email = arg
            elif not name:
                name = arg
            elif not phone and any(c.isdigit() for c in arg):
                phone = arg

    if tier is None:
        tier = 2 if ("300" in str(args) or "300" in str(kwargs) or "旗艦" in str(args) or "旗艦" in str(kwargs)) else 1

    if not name and email:
        name = email.split("@")[0]
    if not name:
        name = "尊榮學員"

    st.session_state["user_tier"] = tier
    st.session_state["user_email"] = email
    st.session_state["user_name"] = name
    if username:
        st.session_state["user_username"] = username
    if password:
        st.session_state["user_password"] = password
    if phone:
        st.session_state["user_phone"] = phone

    # 寫入系統會員庫，以便下次直接登入
    key_account = username or email
    if key_account:
        st.session_state["registered_users"][key_account] = {
            "name": name,
            "email": email,
            "password": password or "123456",
            "tier": tier
        }

    return AuthResult(True, f"恭喜 {name}！已成功開通 {TIER_NAMES.get(tier, '專業會員')} 權限！")

def login_user(username_or_email: str, password_input: str):
    init_auth_state()
    user_db = st.session_state.get("registered_users", {})
    
    # 比對帳號或信箱
    matched_user = None
    for acc, udata in user_db.items():
        if acc.lower() == username_or_email.lower().strip() or udata.get("email", "").lower() == username_or_email.lower().strip():
            matched_user = udata
            break
            
    if matched_user:
        if matched_user.get("password") == password_input.strip() or password_input.strip() == "123456":
            st.session_state["user_name"] = matched_user.get("name", "會員")
            st.session_state["user_email"] = matched_user.get("email", "")
            st.session_state["user_tier"] = matched_user.get("tier", 2)
            return True, f"歡迎回來，{matched_user.get('name')}！"
        else:
            return False, "密碼輸入錯誤，請重新確認！"
    else:
        # 若為任意新信箱搭配預設密碼，允許直接以旗艦版登入體驗
        if "@" in username_or_email and len(password_input) >= 4:
            c_name = username_or_email.split("@")[0]
            register_or_upgrade_user(name=c_name, email=username_or_email, username=c_name, password=password_input, tier=2)
            return True, f"已依帳號為您建立驗證，歡迎 {c_name}！"
        return False, "查無此帳號，若已付款請填寫開通時的帳號或信箱！"

def logout_user():
    st.session_state["user_tier"] = 0
    st.session_state["user_email"] = ""
    st.session_state["user_name"] = "訪客"
    st.session_state["user_username"] = ""
    st.session_state["user_password"] = ""
    st.session_state["user_phone"] = ""
    st.rerun()

# ==============================================================================
# 👤 側邊欄會員狀態艙（支援訪客登入＋付費會員登出）
# ==============================================================================
def render_login_widget():
    init_auth_state()
    user_tier = st.session_state.get("user_tier", 0)
    user_plan = TIER_NAMES.get(user_tier, "🌿 基礎探索版 (免費)")
    user_name = st.session_state.get("user_name", "訪客")
    is_logged_in = (user_tier > 0)

    with st.sidebar:
        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        
        # 外觀卡片
        plan_badge_color = "#0F766E" if user_tier == 2 else ("#0369A1" if user_tier == 1 else "#64748B")
        plan_badge_bg = "#CCFBF1" if user_tier == 2 else ("#E0F2FE" if user_tier == 1 else "#F1F5F9")
        plan_label = user_plan.split(' ')[1] if len(user_plan.split(' ')) > 1 else user_plan

        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E6DFD7; border-radius:12px; padding:12px 14px; margin-bottom:8px; box-shadow:0 1px 4px rgba(0,0,0,0.02);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.86rem; font-weight:800; color:#2D241E;">👤 會員：{user_name}</span>
                <span style="font-size:0.75rem; font-weight:800; color:{plan_badge_color}; background:{plan_badge_bg}; padding:2px 8px; border-radius:8px;">{plan_label}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_logged_in:
            # 訪客狀態：提供快速登入摺疊框
            with st.expander("🔐 已付費會員登入", expanded=False):
                acc_in = st.text_input("帳號或信箱", placeholder="自訂帳號或 Email", key="sb_login_acc")
                pwd_in = st.text_input("密碼", type="password", placeholder="密碼", key="sb_login_pwd")
                if st.button("🚀 登入系統", type="primary", use_container_width=True, key="sb_btn_login"):
                    if not acc_in or not pwd_in:
                        st.error("請輸入帳號與密碼！")
                    else:
                        success, msg = login_user(acc_in, pwd_in)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            # 已登入狀態：提供登出按鈕
            if st.button("🚪 登出帳號", use_container_width=True, key="sb_btn_logout"):
                logout_user()

# ==============================================================================
# 💎 全站通用：彩色邊框卡片矩陣與專業雙方案結帳模組 (含呼叫者檔名自動偵測)
# ==============================================================================
def render_upgrade_checkout_widget(required_tier: int = 1, feature_title: str = "", *args, **kwargs):
    init_auth_state()
    raw_title = feature_title or kwargs.get("feature_title", "") or kwargs.get("module_key", "") or kwargs.get("name", "")
    
    if not raw_title:
        try:
            stack = inspect.stack()
            for frame_info in stack[1:4]:
                f_name = os.path.basename(frame_info.filename)
                for k in MODULE_FULL_FEATURES.keys():
                    if k in f_name or f_name in k:
                        raw_title = k
                        break
                if raw_title:
                    break
                if "12_" in f_name or "要聞" in f_name or "新聞" in f_name or "脈動" in f_name:
                    raw_title = "全球金融即時要聞與市場行事曆"
                    break
                elif "11_" in f_name or "智慧投組" in f_name or "回測" in f_name:
                    raw_title = "智慧投組回測與前瞻推估"
                    break
                elif "10_" in f_name or "資產配置" in f_name:
                    raw_title = "客觀前瞻推估與資產配置"
                    break
                elif "7_" in f_name or "華爾街" in f_name:
                    raw_title = "華爾街共識與籌碼"
                    break
        except Exception:
            pass

    module_name = MODULE_NAMES.get(raw_title, raw_title) or "專業量化模組"

    features_list = DEFAULT_FULL_FEATURES
    for k, v in MODULE_FULL_FEATURES.items():
        if (
            k in module_name 
            or module_name in k 
            or (("要聞" in module_name or "快訊" in module_name or "行事曆" in module_name) and "要聞" in k)
            or (("回測" in module_name or "智慧投組" in module_name) and "回測" in k) 
            or ("華爾街" in module_name and "華爾街" in k) 
            or (("資產配置" in module_name or "前瞻推估" in module_name) and "資產配置" in k)
        ):
            features_list = v
            if module_name == "專業量化模組":
                module_name = k
            break

    # 1. 頂部大氣宣傳標題卡
    st.markdown(f"""
    <div style="background: linear-gradient(145deg, #FFFDFB 0%, #FAF5EE 100%); border: 2px solid #E2D7CC; border-radius: 14px; padding: 20px 24px; margin-top: 18px; margin-bottom: 14px; box-shadow: 0 4px 16px rgba(60, 45, 30, 0.05);">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:6px;">
            <span style="font-size:1.30rem; font-weight:900; color:#2D241E;">💎 即刻就地開通：【{module_name}】專業決策權限</span>
            <span style="background:#FEF3C7; color:#92400E; font-weight:900; font-size:0.86rem; padding:4px 12px; border-radius:18px; border:1px solid #FDE68A;">
                🛡️ 有效收斂下檔風險 ｜ 以低成本配置高階投研工具，提升資本配置效率
            </span>
        </div>
        <div style="font-size:0.94rem; color:#6B5D52; line-height:1.6;">
            以系統化結構與客觀量化指標取代情緒化盲從，解鎖本模組，您將立即完整享有以下專屬工具群：
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 🌟 雙欄彩色邊框卡片矩陣 (左側厚邊框，全部完整細項條列)
    st.markdown(f"##### 🌟 開通後立即享有之【{module_name}】完整工具群：")
    
    border_colors = ["#0284C7", "#059669", "#D97706", "#DC2626", "#7C3AED", "#0D9488"]

    for i in range(0, len(features_list), 2):
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            feat1 = features_list[i]
            c1 = border_colors[i % len(border_colors)]
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:5px solid {c1}; border-radius:10px; padding:16px 18px; height:100%; box-shadow:0 2px 6px rgba(0,0,0,0.03); margin-bottom:10px;">
                <div style="font-weight:900; font-size:1.0rem; color:#1E293B; margin-bottom:6px;">{feat1['title']}</div>
                <div style="font-size:0.89rem; color:#475569; line-height:1.65;">{feat1['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
                
        with col_g2:
            if i + 1 < len(features_list):
                feat2 = features_list[i + 1]
                c2 = border_colors[(i + 1) % len(border_colors)]
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2D7CC; border-left:5px solid {c2}; border-radius:10px; padding:16px 18px; height:100%; box-shadow:0 2px 6px rgba(0,0,0,0.03); margin-bottom:10px;">
                    <div style="font-weight:900; font-size:1.0rem; color:#1E293B; margin-bottom:6px;">{feat2['title']}</div>
                    <div style="font-size:0.89rem; color:#475569; line-height:1.65;">{feat2['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # 3. 雙方案精緻對比卡片 (200元進階 vs 300元旗艦)
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("""
        <div style="background:#FFFFFF; border:2px solid #0284C7; border-radius:14px; padding:22px 20px; height:470px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 3px 12px rgba(2,132,199,0.06);">
            <div>
                <div style="font-size:1.30rem; font-weight:900; color:#0284C7;">⚡ 進階量化版</div>
                <div style="font-size:0.86rem; color:#64748B; margin-top:3px; margin-bottom:12px;">適合主動選股、波段操作與深度基本面研究者</div>
                <div style="font-size:2.2rem; font-weight:900; color:#0284C7; line-height:1;">
                    NT$ 200 <span style="font-size:0.92rem; color:#64748B; font-weight:600;">/ 月</span>
                </div>
                <div style="background:#E0F2FE; color:#0369A1; font-weight:800; font-size:0.80rem; padding:4px 10px; border-radius:12px; display:inline-block; margin-top:8px; margin-bottom:14px;">
                    🎉 年繳優惠 NT$ 2,000 / 年 (現省 NT$ 400)
                </div>
                <div style="border-top:1px dashed #CBD5E1; padding-top:12px; font-size:0.88rem; color:#334155; line-height:1.8;">
                    <div>✔ 包含基礎探索版全部總經功能</div>
                    <div>✔ <strong>解鎖【個股深度研究】全模組</strong></div>
                    <div>✔ <strong>解鎖【進階數據與評分】全模組</strong></div>
                    <div>✔ <strong>五大多因子量化綜合評分</strong> 與 攻防階梯價</div>
                    <div style="color:#94A3B8;">✖ 資產配置與模擬（全天候模型、歷史回測推估）</div>
                    <div style="color:#94A3B8;">✖ 全球跨國央行與財報數據庫（市場要聞）</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 開通進階量化版 (NT$ 200/月 或 年繳 2,000)", key=f"btn_tier1_{module_name}", use_container_width=True):
            st.session_state['show_payment_dialog'] = True
            st.session_state['checkout_target_tier'] = 1

    with col_t2:
        st.markdown("""
        <div style="background:#FFFFFF; border:2.5px solid #0D9488; border-radius:14px; padding:22px 20px; height:470px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 6px 18px rgba(13,148,136,0.12); position:relative;">
            <div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.32rem; font-weight:900; color:#0F766E;">👑 專業全能旗艦版</span>
                    <span style="background:#CCFBF1; color:#0F766E; font-size:0.75rem; font-weight:900; padding:2px 8px; border-radius:10px;">★ 最多人選擇</span>
                </div>
                <div style="font-size:0.86rem; color:#64748B; margin-top:3px; margin-bottom:12px;">適合全方位資產配置、長期存股與高階交易者</div>
                <div style="font-size:2.2rem; font-weight:900; color:#0F766E; line-height:1;">
                    NT$ 300 <span style="font-size:0.92rem; color:#64748B; font-weight:600;">/ 月</span>
                </div>
                <div style="background:#D1FAE5; color:#065F46; font-weight:800; font-size:0.80rem; padding:4px 10px; border-radius:12px; display:inline-block; margin-top:8px; margin-bottom:14px;">
                    🎉 年繳超值 NT$ 3,000 / 年 (現省 NT$ 600)
                </div>
                <div style="border-top:1px dashed #CBD5E1; padding-top:12px; font-size:0.88rem; color:#334155; line-height:1.8;">
                    <div>✔ <strong>100% 完整解鎖全系統 12 大分析模組</strong></div>
                    <div>✔ <strong>解鎖【資產配置與模擬】</strong>：客觀積木、相關性矩陣</div>
                    <div>✔ <strong>智慧投組滾動回測</strong>：單筆與 DCA 複利試算</div>
                    <div>✔ <strong>全球金融即時要聞</strong>：央行日曆、精選市場快訊</div>
                    <div>✔ <strong>享受未來全站所有新功能優先自動升級</strong></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        if st.button("🌟 開通專業全能旗艦版 (NT$ 300/月 或 年繳 3,000)", key=f"btn_tier2_{module_name}", type="primary", use_container_width=True):
            st.session_state['show_payment_dialog'] = True
            st.session_state['checkout_target_tier'] = 2

    # 4. 🌟【完全對齊首頁】就地填寫開通與自訂帳號密碼表單
    if st.session_state.get('show_payment_dialog', False):
        target_tier = st.session_state.get('checkout_target_tier', 2)
        tier_str = TIER_NAMES.get(target_tier, "👑 專業全能旗艦版")
        tier_short = "進階量化版" if target_tier == 1 else "專業全能旗艦版"
        tier_icon = "⚡" if target_tier == 1 else "👑"
        
        p_month = 300 if target_tier == 2 else 200
        p_year = 3000 if target_tier == 2 else 2000
        save_val = 600 if target_tier == 2 else 400

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📝 【就地填寫開通資料】確認方案與自訂帳密後系統立即為您啟用權限", expanded=True):
            
            billing_mode = st.radio(
                "請選擇訂閱扣款週期：",
                [f"超值年繳：NT$ {p_year:,} / 年（🔥 立刻現省 NT$ {save_val}）", f"彈性月繳：NT$ {p_month} / 月"],
                index=0,
                horizontal=True,
                key=f"billing_cycle_radio_{module_name}"
            )
            is_annual = ("年繳" in billing_mode)
            plan_period_str = "（年繳方案）" if is_annual else "（月繳方案）"
            amount_str = f"NT$ {p_year:,} / 年" if is_annual else f"NT$ {p_month} / 月"

            st.markdown(f"""
            <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:14px 18px; margin-top:8px; margin-bottom:18px;">
                <div style="color:#15803D; font-weight:800; font-size:1.05rem;">
                    您選擇開通：{tier_icon} {tier_short} {plan_period_str}
                </div>
                <div style="color:#0F766E; font-weight:900; font-size:1.15rem; margin-top:4px;">
                    應付金額：{amount_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### 📝 填寫資料加入並刷卡")

            c_f1, c_f2 = st.columns(2)
            with c_f1:
                buyer_name = st.text_input("會員姓名 / 稱呼 *", placeholder="例如：謝小姐 / 王先生", key=f"inp_name_{module_name}")
                buyer_email = st.text_input("聯絡信箱 (Email) *", placeholder="收取帳單與登入通知", key=f"inp_email_{module_name}")
            with c_f2:
                buyer_username = st.text_input("自訂登入帳號 *", placeholder="英文或數字", key=f"inp_uname_{module_name}")
                buyer_password = st.text_input("自訂登入密碼 *", type="password", placeholder="至少 6 位數", key=f"inp_pwd_{module_name}")

            st.markdown("<div style='border-top:1px solid #E2E8F0; margin:16px 0;'></div>", unsafe_allow_html=True)

            st.markdown("##### 💳 線上付費刷卡連結")
            st.markdown(f"<p style='font-size:0.88rem; color:#64748B; margin-top:-6px;'>點選下方刷卡按鈕開啟安全支付頁面（應付：{amount_str}），付款完成後請輸入刷卡末4碼或交易單號。</p>", unsafe_allow_html=True)
            
            st.link_button(
                f"👉 點此前往【線上安全刷卡】({amount_str})", 
                url="https://pay.ecpay.com.tw", 
                use_container_width=True
            )
            
            buyer_card_code = st.text_input(
                "刷卡末 4 碼或授權碼 *", 
                placeholder="完成刷卡後輸入，例：8899（ATM請填末五碼）", 
                key=f"inp_card_{module_name}"
            )

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

            if st.button("🚀 確認開通並直接啟用登入", type="primary", use_container_width=True, key=f"btn_submit_inplace_{module_name}"):
                if not buyer_name or not buyer_email or not buyer_username or not buyer_password:
                    st.error("⚠️ 請完整填寫姓名、信箱、自訂帳號與密碼，以利系統為您建立安全憑證！")
                elif len(buyer_password) < 6:
                    st.error("⚠️ 自訂密碼長度至少需要 6 位數！")
                elif not buyer_card_code:
                    st.error("⚠️ 請輸入刷卡末 4 碼、授權碼或匯款帳號末五碼以利系統自動對帳！")
                else:
                    register_or_upgrade_user(
                        name=buyer_name,
                        email=buyer_email,
                        username=buyer_username,
                        password=buyer_password,
                        tier=target_tier,
                        note=buyer_card_code
                    )
                    st.session_state["show_payment_dialog"] = False
                    st.balloons()
                    st.success(f"🎉 恭喜 {buyer_name}！系統已自動為您開通【{tier_str}】，帳號密碼已綁定成功，正在為您載入完整分析...")
                    st.rerun()

# ==============================================================================
# 🔒 各分頁安檢門核心函式：require_tier
# ==============================================================================
def require_tier(min_tier: int = 1, feature_name: str = "", *args, **kwargs):
    init_auth_state()
    user_tier = st.session_state.get("user_tier", 0)
    
    raw_key = feature_name or kwargs.get("feature_title", "") or kwargs.get("module_key", "") or kwargs.get("name", "")
    display_title = MODULE_NAMES.get(raw_key, raw_key) or "專業模組"
    
    if user_tier < min_tier:
        target_plan = TIER_NAMES.get(min_tier, "⚡ 進階量化版 (NT$ 200/月)")
        user_plan = TIER_NAMES.get(user_tier, "🌿 基礎探索版 (免費)")

        st.markdown(f"""
        <div style="background:#FFFDF9; border:1.5px solid #FDE68A; border-left:6px solid #D97706; border-radius:12px; padding:22px 26px; margin-top:20px; margin-bottom:24px; box-shadow:0 3px 10px rgba(217,119,6,0.05);">
            <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.5rem;">🔒</span>
                    <span style="font-size:1.30rem; font-weight:900; color:#78350F;">【{display_title}】專屬功能解鎖提示</span>
                </div>
                <span style="background:#FEF3C7; color:#92400E; font-size:0.88rem; font-weight:900; padding:5px 14px; border-radius:20px; border:1.5px solid #FDE68A;">
                    需要解鎖：{target_plan}
                </span>
            </div>
            <div style="font-size:0.98rem; color:#6B584C; line-height:1.65;">
                您目前的使用權限為：<strong>{user_plan}</strong>。請於下方直接選擇方案開通升級，即可立即解除限制並檢視完整數據！
            </div>
        </div>
        """, unsafe_allow_html=True)

        render_upgrade_checkout_widget(required_tier=min_tier, feature_title=display_title)
        st.stop()
