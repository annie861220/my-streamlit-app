import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date

st.set_page_config(page_title="家芬a整合平台", layout="wide")

# ====== 全域樣式（CSS） ======
st.markdown(
    """
    <style>
    /* 整體背景 & 版面寬度 */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* 主標題下面留點空間 */
    h1 {
        margin-bottom: 0.2rem;
    }

    /* 說明文字區塊 */
    .intro-box {
        padding: 0.8rem 1rem;
        border-radius: 0.8rem;
        background: #fff7f0;
        border: 1px solid #ffd6aa;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }

    /* KPI 卡片 */
    .kpi-card {
        padding: 0.9rem 1rem;
        border-radius: 0.8rem;
        background: #ffffff;
        border: 1px solid #e5e5e5;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #777777;
        margin-bottom: 0.2rem;
    }
    .kpi-value {
        font-size: 1.4rem;
        font-weight: 700;
    }
    .kpi-income .kpi-value {
        color: #2e7d32;
    }
    .kpi-expense .kpi-value {
        color: #c62828;
    }
    .kpi-net .kpi-value {
        color: #1565c0;
    }

    /* 明細提示文字 */
    .hint-text {
        font-size: 0.85rem;
        color: #666666;
        margin-bottom: 0.4rem;
    }

    /* Sidebar 標題微調 */
    section[data-testid="stSidebar"] h2 {
        margin-top: 0.5rem;
    }

    /* 月份卡片統一風格 */
    .month-card {
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        border-radius: 0.8rem;
        background: #ffffff;
        border: 1px solid #e5e5e5;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .month-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.6rem;
    }
    .month-line {
        display: flex;
        justify-content: space-between;
        padding: 0.25rem 0;
    }
    .month-line-label {
        font-size: 0.85rem;
        color: #666666;
    }
    .month-line-income {
        font-size: 1rem;
        font-weight: 700;
        color: #2e7d32;
    }
    .month-line-expense {
        font-size: 1rem;
        font-weight: 700;
        color: #c62828;
    }
    .month-line-net {
        font-size: 1rem;
        font-weight: 700;
        color: #1565c0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ====== 檔案設定 ======
DATA_FILE = Path("transactions.csv")

COLUMNS = [
    "日期", "星期",
    "類別", "小類", "項目",
    "支付方式", "幣別",
    "收入", "支出",
    "支出比例", "實際支出",
    "備註",
]

CATEGORY_OPTIONS = [
    "飲食", "衣著", "日常", "交通",
    "教育", "娛樂", "醫療",
    "收入",
    "其他",
]

SUBCATEGORY_MAP = {
    "飲食": ["早餐", "午餐", "晚餐", "零食飲料", "食材原料"],
    "衣著": ["服飾鞋包"],
    "日常": [
        "水費", "電費", "房租", "電話費",
        "日用消耗", "居家百貨", "美妝保養", "電子數位",
        "保險", "股票", "稅務",
    ],
    "交通": ["加油", "保養維修", "停車費", "過路費", "公共交通", "叫車"],
    "教育": ["學雜費", "文具用品"],
    "娛樂": ["旅遊", "聚會娛樂", "運動健身", "人情世故"],
    "醫療": ["醫藥費", "藥品"],
    "收入": ["薪資", "獎金"],
    "其他": ["其他"],
}

PAYMENT_OPTIONS = ["現金", "魔法小卡", "大哥"]
CURRENCY_OPTIONS = ["TWD", "USD", "JPY", "EUR", "其他"]
WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]


# ====== 資料讀寫 ======
def load_data() -> pd.DataFrame:
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        if not df.empty:
            df["日期"] = pd.to_datetime(df["日期"])
    else:
        df = pd.DataFrame(columns=COLUMNS)
    return df


def save_data(df: pd.DataFrame):
    df_to_save = df.copy()
    if not df_to_save.empty:
        df_to_save["日期"] = df_to_save["日期"].dt.strftime("%Y-%m-%d")
    df_to_save.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


df = load_data()

# ====== 側邊欄：匯入舊 Excel（一次性使用） ======
st.sidebar.markdown("---")
st.sidebar.subheader("📥 匯入舊 Excel（一次性）")

upload_file = st.sidebar.file_uploader("選擇舊的記帳 Excel 檔", type=["xlsx", "xls"])

if upload_file is not None:
    try:
        old_df = pd.read_excel(upload_file)

        # 舊檔可能有「月份」欄，先丟掉
        if "月份" in old_df.columns:
            old_df = old_df.drop(columns=["月份"])

        # 確保所有需要的欄位都有
        for col in COLUMNS:
            if col not in old_df.columns:
                if col == "幣別":
                    old_df[col] = "TWD"
                elif col in ["收入", "支出", "支出比例", "實際支出"]:
                    old_df[col] = 0
                else:
                    old_df[col] = ""

        old_df = old_df[COLUMNS]
        old_df["日期"] = pd.to_datetime(old_df["日期"])

        st.sidebar.success(f"預覽舊資料共 {len(old_df)} 筆，可匯入。")

        if st.sidebar.button("↪ 把舊資料匯入現在檔案"):
            df = pd.concat([df, old_df], ignore_index=True)
            save_data(df)
            st.sidebar.success("舊資料已匯入 ✅，重新整理頁面即可看到。")
    except Exception as e:
        st.sidebar.error(f"匯入失敗：{e}")

# ====== 預先算「本月」與「長期」統計（用匯入後的 df） ======
today = date.today()
if not df.empty:
    this_month_mask = (
        (df["日期"].dt.year == today.year) &
        (df["日期"].dt.month == today.month)
    )
    this_month_df = df[this_month_mask].copy()
else:
    this_month_df = df.copy()

if not this_month_df.empty:
    month_income = this_month_df["收入"].sum()
    month_expense = this_month_df["實際支出"].sum()
    month_net = month_income - month_expense
else:
    month_income = month_expense = month_net = 0.0

if not df.empty:
    all_income = df["收入"].sum()
    all_expense = df["實際支出"].sum()
    all_net = all_income - all_expense
else:
    all_income = all_expense = all_net = 0.0

# ====== 標題 & 說明 ======
st.title("📒 嘎昏 a 記帳小程式")

st.markdown(
    """
    <div class="intro-box">
    <b>保持可愛。</b><br><br>
    ‧ 每月 5 號發薪水<br>
    ‧ 乖乖記帳，知道錢跑去哪<br>
    ‧ 不要死掉，要快樂花錢
    </div>
    """,
    unsafe_allow_html=True,
)

# ====== 側邊欄：新增紀錄 ======
st.sidebar.header("花了什麼")

today = date.today()
tx_date = st.sidebar.date_input("日期", today)

category = st.sidebar.selectbox("類別", CATEGORY_OPTIONS)
sub_options = SUBCATEGORY_MAP.get(category, ["其他"])
subcategory = st.sidebar.selectbox("小類", sub_options)

item_name = st.sidebar.text_input("項目")
pay_method = st.sidebar.selectbox("支付方式", PAYMENT_OPTIONS)
currency = st.sidebar.selectbox("幣別", CURRENCY_OPTIONS, index=0)  # 預設 TWD

income_or_expense = st.sidebar.radio("這筆是？", ["支出", "收入"], horizontal=True)

pay_ratio = st.sidebar.number_input(
    "支付比例（%）",
    min_value=0,
    max_value=100,
    value=100,
    step=5,
)

amount_str = st.sidebar.text_input(f"金額（{currency}）")
note = st.sidebar.text_area("備註（選填）", height=60)

submitted = st.sidebar.button("💾 Add")

if submitted:
    try:
        amount = float(amount_str)
    except ValueError:
        st.sidebar.error("金額請輸入數字")
        amount = -1

    if amount <= 0:
        st.sidebar.error("金額必須 > 0")
    elif item_name.strip() == "":
        st.sidebar.error("請填寫完整")
    else:
        dt = datetime.combine(tx_date, datetime.min.time())
        weekday_str = WEEKDAY_LABELS[dt.weekday()]

        income = amount if income_or_expense == "收入" else 0.0
        expense = amount if income_or_expense == "支出" else 0.0

        if income_or_expense == "支出":
            actual_expense = expense * (pay_ratio / 100.0)
        else:
            actual_expense = 0.0

        new_row = {
            "日期": dt,
            "星期": weekday_str,
            "類別": category,
            "小類": subcategory,
            "項目": item_name,
            "支付方式": pay_method,
            "幣別": currency,
            "收入": income,
            "支出": expense,
            "支出比例": int(pay_ratio),
            "實際支出": actual_expense,
            "備註": note,
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.sidebar.success("已新增一筆紀錄 ✅")

# ====== 篩選條件 ======
st.subheader("篩選條件")

with st.container():
    col1, col2, col3, col4 = st.columns(4)

    if not df.empty:
        min_date = df["日期"].min().date()
        max_date = df["日期"].max().date()
    else:
        min_date = max_date = date.today()

    with col1:
        start_date = st.date_input("起始日期", min_date)

    with col2:
        end_date = st.date_input("結束日期", max_date)

    with col3:
        category_filter = st.multiselect(
            "類別篩選（空白 = 全部）",
            options=CATEGORY_OPTIONS,
            default=[],
        )

    with col4:
        payment_filter = st.multiselect(
            "支付方式篩選（空白 = 全部）",
            options=PAYMENT_OPTIONS,
            default=[],
        )

if not df.empty:
    mask = (
        (df["日期"].dt.date >= start_date) &
        (df["日期"].dt.date <= end_date)
    )
    if category_filter:
        mask &= df["類別"].isin(category_filter)
    if payment_filter:
        mask &= df["支付方式"].isin(payment_filter)

    filtered_df = df[mask].copy()
else:
    filtered_df = df.copy()

st.write(f"符合條件的筆數：**{len(filtered_df)}**")

# ====== 本月統計總覽（固定本月） ======
st.subheader("本月統計總覽")

k1,
