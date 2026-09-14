import streamlit as st
import streamlit.components.v1 as components
import os
import base64

def inject_global_style():
    # 1. 搜尋專案根目錄的 Q 版圖片並轉成 Base64
    img_b64 = ""
    candidate_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "我Q版.jpg"),
        os.path.join(os.getcwd(), "我Q版.jpg"),
        "我Q版.jpg"
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
                if img_b64:
                    break
            except Exception:
                pass

    # 2. 全站背景色與側邊欄樣式
    st.markdown("""
    <style>
        .stApp {
            background-color: #FAF8F5 !important;
            color: #2D2622 !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #F4EFEA !important;
            border-right: 1px solid #E6DFD7 !important;
        }

        /* 解除導航高度限制 */
        div[data-testid="stSidebarNav"],
        div[data-testid="stSidebarNav"] > div,
        div[data-testid="stSidebarNav"] ul {
            max-height: none !important;
            height: auto !important;
            overflow: visible !important;
        }

        div[data-testid="stSidebarNav"] li {
            margin-bottom: 2px !important;
        }
        div[data-testid="stSidebarNav"] a {
            padding: 6px 12px !important;
            border-radius: 8px !important;
        }
        div[data-testid="stSidebarNav"] a span {
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            color: #4A3E36 !important;
        }

        div[data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: #FFFFFF !important;
            border: 1.5px solid #D6CBC1 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.04) !important;
        }
        div[data-testid="stSidebarNav"] a[aria-current="page"] span {
            color: #1E293B !important;
            font-weight: 800 !important;
        }

        div[data-testid="stMetric"] label div p,
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] div,
        div[data-testid="stMetric"] div[data-testid="stMetricDelta"] div {
            white-space: normal !important;
            text-overflow: clip !important;
            word-break: break-word !important;
            overflow: visible !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 3. 頭像標籤 HTML
    if img_b64:
        avatar_html = f'<img src="data:image/jpeg;base64,{img_b64}" style="width:84px; height:84px; border-radius:50%; object-fit:cover; border:2.5px solid #0F766E; box-shadow:0 3px 10px rgba(15,118,110,0.25);">'
    else:
        avatar_html = '<div style="width:84px; height:84px; border-radius:50%; background:#0F766E; color:#FFF; display:flex; align-items:center; justify-content:center; font-size:1.8rem; font-weight:800; margin:0 auto; border:2.5px solid #0F766E;">JH</div>'

    # 4. 強制每次刷新名片卡、自動展開選單並正確排序分類
    components.html(f"""
    <script>
    function forceUpdateBrand() {{
        const doc = window.parent.document;
        const sidebarNav = doc.querySelector('div[data-testid="stSidebarNav"]');
        if (!sidebarNav) return;

        // 💥 自動點擊「View more」按鈕展開隱藏分頁
        const viewMoreBtn = sidebarNav.querySelector('button');
        if (viewMoreBtn && (viewMoreBtn.innerText.includes('more') || viewMoreBtn.innerText.includes('更多'))) {{
            viewMoreBtn.click();
        }}

        // 💥 強制移除舊名片盒與舊分類標題，避免重複累積錯亂
        const oldCards = doc.querySelectorAll('#chengpu-brand-header-card');
        oldCards.forEach(el => el.remove());

        const oldHeaders = doc.querySelectorAll('.custom-sidebar-cat-header');
        oldHeaders.forEach(el => el.remove());

        const brandCard = doc.createElement('div');
        brandCard.id = 'chengpu-brand-header-card';
        brandCard.innerHTML = `
            <div style="
                background: linear-gradient(145deg, #FFFDFB 0%, #F5EDE4 100%);
                border: 1.5px solid #E2D7CC;
                border-radius: 14px;
                padding: 16px 14px 14px 14px;
                margin: 10px 12px 22px 12px;
                box-shadow: 0 4px 14px rgba(60, 45, 30, 0.06);
                text-align: center;
                font-family: -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Microsoft JhengHei', sans-serif;
            ">
                <!-- 專屬 Q 版頭像 -->
                <div style="display:flex; justify-content:center; margin-bottom: 8px;">
                    {avatar_html}
                </div>

                <!-- 工作室名稱 -->
                <div style="font-size: 0.98rem; font-weight: 900; color: #2D241E; letter-spacing: 0.8px; margin-bottom: 4px;">
                    澄璞財務顧問工作室
                </div>

                <!-- 顧問姓名與認證標籤 -->
                <div style="display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 8px;">
                    <span style="font-size: 0.88rem; font-weight: 800; color: #5C4A3E;">JennyHsieh</span>
                    <span style="background:#0F766E; color:#FFFFFF; font-size:0.68rem; font-weight:800; padding:1px 6px; border-radius:4px; letter-spacing:0.5px;">CFP®</span>
                </div>

                <!-- Slogan 標語卡 -->
                <div style="
                    background: #FFFFFF;
                    border: 1px dashed #D6CBC1;
                    border-radius: 8px;
                    padding: 6px 10px;
                    margin-top: 4px;
                ">
                    <div style="font-size: 0.86rem; font-weight: 700; color: #4A3E36; line-height: 1.5;">
                        有「<span style="color:#0F766E; font-size:0.96rem; font-weight:900;">筱</span>」陪伴
                    </div>
                    <div style="font-size: 0.86rem; font-weight: 700; color: #4A3E36; line-height: 1.5;">
                        攜手「<span style="color:#7C3AED; font-size:0.98rem; font-weight:900; text-shadow:0 0 1px #7C3AED;">筑</span>」夢
                    </div>
                </div>
            </div>
        `;
        sidebarNav.insertBefore(brandCard, sidebarNav.firstChild);

        // 插入 12 大模組完整分類標籤（修正 03 頁歸類至總體與市場氛圍）
        const navUl = sidebarNav.querySelector('ul');
        if (!navUl) return;

        const mapping = [
            {{ text: "決策總覽首頁", title: "▌ 決策總覽" }},
            {{ text: "總體環境監控", title: "▌ 總體與市場氛圍" }},
            {{ text: "市場氛圍與流動性", title: "" }},
            {{ text: "板塊輪動與資金流向", title: "" }},
            {{ text: "產業同儕估值", title: "▌ 個股深度研究" }},
            {{ text: "個股基本面深度庫", title: "" }},
            {{ text: "技術面與量價動量", title: "" }},
            {{ text: "華爾街共識與籌碼", title: "" }},
            {{ text: "訂單流與另類數據", title: "▌ 進階數據與評分" }},
            {{ text: "綜合決策與多空評分", title: "" }},
            {{ text: "資產配置與前瞻推估", title: "▌ 資產配置與模擬" }},
            {{ text: "智慧投組回測與前瞻推估", title: "" }},
            {{ text: "全球金融即時要聞與市場脈動", title: "▌ 市場要聞" }}
        ];

        const listItems = navUl.querySelectorAll('li');
        listItems.forEach(li => {{
            const anchor = li.querySelector('a');
            if (!anchor) return;
            const content = anchor.innerText;

            mapping.forEach(m => {{
                if (content.includes(m.text) && m.title !== "") {{
                    const prevElem = li.previousElementSibling;
                    if (!prevElem || !prevElem.classList.contains('custom-sidebar-cat-header')) {{
                        const headerDiv = doc.createElement('div');
                        headerDiv.className = 'custom-sidebar-cat-header';
                        headerDiv.innerText = m.title;
                        headerDiv.style.cssText = `
                            display: block;
                            background: linear-gradient(180deg, #EFE8DF 0%, #E8DFD3 100%);
                            border: 1px solid #D8CEC2;
                            border-radius: 8px;
                            padding: 8px 14px;
                            font-size: 0.90rem;
                            font-weight: 800;
                            color: #2D241E;
                            letter-spacing: 0.5px;
                            margin-top: 14px;
                            margin-bottom: 6px;
                            box-shadow: 0 1px 3px rgba(60, 45, 30, 0.05);
                            font-family: sans-serif;
                        `;
                        navUl.insertBefore(headerDiv, li);
                    }}
                }}
            }});
        }});
    }}

    setTimeout(forceUpdateBrand, 150);
    setTimeout(forceUpdateBrand, 500);
    setTimeout(forceUpdateBrand, 1200);
    </script>
    """, height=0, width=0)
