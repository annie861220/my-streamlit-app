import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date

st.set_page_config(page_title="家芬自己來", layout="wide")

# ====== 檔案設定 ======
DATA_FILE = Path("transactions.csv")

# Excel 表頭對應（已拿掉「月份」）
COLUMNS = [
    "日期", "星期",
    "類別", "小類", "項目",
    "支付方式", "收入", "支出",
    "支出比例", "實際支出", "備註"
]

# 類別 / 小類 / 支付方式 選項
CATEGORY_OPTIONS = [
    "飲食", "衣著", "日常", "交通",
    "教育", "娛樂", "醫療", "理財", "其他"
]

# 類別 → 小類對應表（連動選單）
SUBCATEGORY_MAP = {
    "飲食": ["早餐", "午餐", "晚餐", "零食飲料", "食材原料"],
    "衣著": ["服飾鞋包"],
    "日常": ["水費", "電費", "房租", "電話費",
           "日用消耗", "居家百貨", "美妝保養", "電子數位",
           "保險", "股票", "稅務"],
    "交通": ["加油", "保養維修", "停車費", "過路費", "公共交通", "叫車"],
    "教育": ["學雜費", "文具用品"],
    "娛樂": ["旅遊", "聚會娛樂", "運動健身", "人情世故"],
    "醫療": ["醫藥費", "藥品"],
    "理財": ["保險", "股票", "稅務"],
    "其他": ["其他"],
}

PAYMENT_OPTIONS = [
    "現金", "魔法小卡", "大哥"
]

# 只存「一、二、三、四、五、六、日」
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

st.title("📒 嘎昏 a 記帳小本本")

st.markdown(
    """
這是說明：  
**保持可愛。**  

- 每月 5 號發薪水  
- 要存錢  
- 不要死掉
"""
)

# ====== 側邊欄：新增紀錄 ======
st.sidebar.header("花了什麼")

with st.sidebar.form("add_transaction", clear_on_submit=True):
    today = date.today()
    tx_date = st.date_input("日期", today)

    # 類別
    category = st.selectbox("類別", CATEGORY_OPTIONS)

    # 類別 → 小類連動
    sub_options = SUBCATEGORY_MAP.get(category, ["其他"])
    subcategory = st.selectbox("小類", sub_options)

    item_name = st.text_input("項目")
    pay_method = st.selectbox("支付方式", PAYMENT_OPTIONS)

    income_or_expense = st.radio("這筆是？", ["支出", "收入"], horizontal=True)

    # 支付比例（你實際負擔多少 %，預設 100）
    pay_ratio = st.number_input(
        "支付比例（%）",
        min_value=0.0,
        max_value=100.0,
        value=100.0,
        step=5.0,
    )

    # 金額用文字輸入，避免預設 0.00，並加上幣別說明
    amount_str = st.text_input("金額（TWD）")

    note = st.text_area("備註（選填）", height=60)

    submitted = st.form_submit_button("💾 Add")

    if submitted:
        # 轉換金額
        try:
            amount = float(amount_str)
        except ValueError:
            st.sidebar.error("金額請輸入數字")
            amount = -1  # 讓下面的判斷擋下去

        if amount <= 0:
            st.sidebar.error("金額必須 > 0")
        elif item_name.strip() == "":
            st.sidebar.error("請填寫完整")
        else:
            # 只保留「日期」與「星期」（不存月份）
            dt = datetime.combine(tx_date, datetime.min.time())
            weekday_str = WEEKDAY_LABELS[dt.weekday()]  # 例如：一、二、三...

            # 收入 / 支出欄位
            income = amount if income_or_expense == "收入" else 0.0
            expense = amount if income_or_expense == "支出" else 0.0

            # 實際支出 = 金額 × 支付比例（收入就不算實際支出）
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
                "收入": income,
                "支出": expense,
                "支出比例": pay_ratio / 100.0,  # 0~1，表格再看要不要改成 %
                "實際支出": actual_expense,
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

    # 如果有選類別才加條件，沒選視為「全部」
    if category_filter:
        mask &= df["類別"].isin(category_filter)

    # 如果有選支付方式才加條件
    if payment_filter:
        mask &= df["支付方式"].isin(payment_filter)

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

    # 重新計算「支出比例」：以目前篩選範圍內的總「實際支出」為基準
    total_exp = display_df["實際支出"].sum()
    if total_exp > 0:
        display_df["支出比例"] = display_df["實際支出"] / total_exp

    st.dataframe(
        display_df.sort_values("日期", ascending=False),
        use_container_width=True
    )

# ====== 統計總覽 ======
st.subheader("統計總覽")

if not df.empty:
    # 全部紀錄統計（不受篩選影響）
    all_stats = df.copy()
    all_income = all_stats["收入"].sum()
    all_expense = all_stats["實際支出"].sum()

    # 當月統計（以今天的年月為準）
    today = date.today()
    this_month_mask = (
        (all_stats["日期"].dt.year == today.year) &
        (all_stats["日期"].dt.month == today.month)
    )
    this_month_df = all_stats[this_month_mask]

    this_month_income = this_month_df["收入"].sum()
    this_month_expense = this_month_df["實際支出"].sum()
    this_month_net = this_month_income - this_month_expense

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("全部紀錄收入", f"{all_income:,.0f}")
    c2.metric("全部紀錄支出", f"{all_expense:,.0f}")
    c3.metric("當月收入", f"{this_month_income:,.0f}")
    c4.metric("當月支出", f"{this_month_expense:,.0f}")
    c5.metric("當月結餘", f"{this_month_net:,.0f}")

    # 依「類別」統計（使用目前篩選結果）
    st.markdown("### 依類別統計（依篩選結果）")
    if not filtered_df.empty:
        stats_df = filtered_df.copy()
        by_cat = (
            stats_df.groupby("類別")[["收入", "實際支出"]]
            .sum()
            .rename(columns={"實際支出": "支出"})
            .sort_values("支出", ascending=False)
        )
        st.dataframe(by_cat, use_container_width=True)
    else:
        st.info("目前篩選結果沒有資料可供類別統計。")

    # 依「月份」統計（用全部資料，但不存月份欄位，只臨時計算）
    st.markdown("### 依月份統計（全部資料）")
    if not df.empty:
        month_stats = df.copy()
        month_stats["月份"] = month_stats["日期"].dt.strftime("%Y-%m")
        by_month = (
            month_stats.groupby("月份")[["收入", "實際支出"]]
            .sum()
            .rename(columns={"實際支出": "支出"})
            .sort_values("月份", ascending=True)
        )
        st.dataframe(by_month, use_container_width=True)
else:
    st.info("尚無資料可以統計。")
