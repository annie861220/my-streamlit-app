import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date

st.set_page_config(page_title="記帳小程式", layout="wide")

# ====== 檔案設定 ======
DATA_FILE = Path("transactions.csv")

# Excel 表頭對應
COLUMNS = [
    "月份", "日期", "星期",
    "類別", "小類", "項目",
    "支付方式", "收入", "支出",
    "支出比例", "實際支出", "備註"
]

# 類別 / 小類 / 支付方式 選項
CATEGORY_OPTIONS = [
    "飲食", "衣著", "日常", "交通",
    "教育", "娛樂", "醫療", "理財", "其他"
]

SUBCATEGORY_OPTIONS = [
    "早餐", "午餐", "晚餐", "零食飲料", "食材原料",
    "服飾鞋包",
    "水費", "電費", "房租", "電話費",
    "日用消耗", "居家百貨", "美妝保養", "電子數位",
    "加油", "保養維修", "停車費", "過路費",
    "公共交通", "叫車",
    "學雜費", "文具用品",
    "旅遊", "聚會娛樂", "運動健身", "人情世故",
    "醫藥費", "藥品",
    "保險", "股票", "稅務",
    "其他",
]

PAYMENT_OPTIONS = [
    "現金", "魔法小卡", "大哥"
]

WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]


# ====== 資料讀寫 ======
def load_data() -> pd.DataFrame:
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        # 確保所有欄位都有
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df["日期"] = pd.to_datetime(df["日期"])
    else:
        df = pd.DataFrame(columns=COLUMNS)
    return df


def save_data(df: pd.DataFrame):
    df_to_save = df.copy()
    df_to_save["日期"] = df_to_save["日期"].dt.strftime("%Y-%m-%d")
    df_to_save.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


df = load_data()

st.title("📒 Excel 邏輯版本記帳小程式")

st.markdown(
    """
表頭結構與你的 Excel 一致：  
**月份、日期、星期、類別、小類、項目、支付方式、收入、支出、支出比例、實際支出、備註**  

- 月份、星期會依日期自動帶入  
- 收入／支出只輸入一個金額，程式會自動放到對應欄位  
- 目前「支出比例」在畫面統計中計算，不需要手動輸入  
"""
)

# ====== 側邊欄：新增紀錄 ======
st.sidebar.header("新增一筆紀錄")

with st.sidebar.form("add_transaction", clear_on_submit=True):
    today = date.today()
    tx_date = st.date_input("日期", today)

    # 類別 / 小類 / 支付方式
    category = st.selectbox("類別", CATEGORY_OPTIONS)
    subcategory = st.selectbox("小類", SUBCATEGORY_OPTIONS)

    item_name = st.text_input("項目")
    pay_method = st.selectbox("支付方式", PAYMENT_OPTIONS)

    income_or_expense = st.radio("這筆是？", ["支出", "收入"], horizontal=True)
    amount = st.number_input("金額", min_value=0.0, step=1.0)

    note = st.text_area("備註（選填）", height=60)

    submitted = st.form_submit_button("💾 新增紀錄")

    if submitted:
        if amount <= 0:
            st.sidebar.error("金額必須 > 0")
        elif item_name.strip() == "":
            st.sidebar.error("請填寫項目")
        else:
            # 自動帶入「月份」與「星期」
            dt = datetime.combine(tx_date, datetime.min.time())
            month_str = dt.strftime("%Y-%m")          # 例：2025-01
            weekday_str = "星期" + WEEKDAY_LABELS[dt.weekday()]

            income = amount if income_or_expense == "收入" else 0.0
            expense = amount if income_or_expense == "支出" else 0.0

            new_row = {
                "月份": month_str,
                "日期": dt,
                "星期": weekday_str,
                "類別": category,
                "小類": subcategory,
                "項目": item_name,
                "支付方式": pay_method,
                "收入": income,
                "支出": expense,
                # 支出比例與實際支出在統計時會重算，這裡先留空或等於支出
                "支出比例": 0.0,
                "實際支出": expense,
                "備註": note,
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.sidebar.success("已新增一筆紀錄 ✅")


# ====== 篩選條件 ======
st.subheader("篩選條件")

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
        "類別篩選",
        options=CATEGORY_OPTIONS,
        default=CATEGORY_OPTIONS,
    )

with col4:
    payment_filter = st.multiselect(
        "支付方式篩選",
        options=PAYMENT_OPTIONS,
        default=PAYMENT_OPTIONS,
    )

if not df.empty:
    mask = (
        (df["日期"].dt.date >= start_date) &
        (df["日期"].dt.date <= end_date) &
        (df["類別"].isin(category_filter)) &
        (df["支付方式"].isin(payment_filter))
    )
    filtered_df = df[mask].copy()
else:
    filtered_df = df.copy()

st.write(f"符合條件的筆數：**{len(filtered_df)}**")

# ====== 明細表格 ======
st.subheader("明細紀錄")

if filtered_df.empty:
    st.info("目前沒有符合條件的紀錄。")
else:
    display_df = filtered_df.copy()
    display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")

    # 重新計算「支出比例」：以目前篩選範圍內的總支出為基準
    total_exp = display_df["實際支出"].sum()
    if total_exp > 0:
        display_df["支出比例"] = display_df["實際支出"] / total_exp

    st.dataframe(
        display_df.sort_values("日期", ascending=False),
        use_container_width=True
    )

# ====== 統計總覽 ======
st.subheader("統計總覽")

if not filtered_df.empty:
    stats_df = filtered_df.copy()
    total_income = stats_df["收入"].sum()
    total_expense = stats_df["實際支出"].sum()
    net = total_income - total_expense

    c1, c2, c3 = st.columns(3)
    c1.metric("總收入", f"{total_income:,.0f}")
    c2.metric("總支出", f"{total_expense:,.0f}")
    c3.metric("結餘（收入 - 支出）", f"{net:,.0f}")

    # 依「類別」統計支出與收入
    st.markdown("### 依類別統計")
    by_cat = (
        stats_df.groupby("類別")[["收入", "實際支出"]]
        .sum()
        .rename(columns={"實際支出": "支出"})
        .sort_values("支出", ascending=False)
    )
    st.dataframe(by_cat, use_container_width=True)

    # 依「月份」統計
    st.markdown("### 依月份統計")
    by_month = (
        stats_df.groupby("月份")[["收入", "實際支出"]]
        .sum()
        .rename(columns={"實際支出": "支出"})
        .sort_values("月份", ascending=True)
    )
    st.dataframe(by_month, use_container_width=True)
else:
    st.info("尚無資料可以統計。")


