import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date

st.set_page_config(page_title="家芬自己來", layout="wide")

# ====== 檔案設定 ======
DATA_FILE = Path("transactions.csv")

# 多了一個隱藏用的 ID 欄位
COLUMNS = [
    "ID",           # 只用來識別紀錄
    "日期", "星期",
    "類別", "小類", "項目",
    "支付方式", "幣別",
    "收入", "支出",
    "支出比例", "實際支出",
    "備註"
]

CATEGORY_OPTIONS = [
    "飲食", "衣著", "日常", "交通",
    "教育", "娛樂", "醫療", "理財",
    "收入",  # 新增
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
    "理財": ["保險", "股票", "稅務"],
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
        # 確保所有欄位都有
        for col in COLUMNS:
            if col not in df.columns:
                # ID 用整數，其它用空字串
                df[col] = 0 if col == "ID" else ""
        df["日期"] = pd.to_datetime(df["日期"])

        # 舊檔案若沒有 ID，就自動補一個
        if (df["ID"] == 0).all():
            df["ID"] = range(1, len(df) + 1)
            save_data(df)
    else:
        df = pd.DataFrame(columns=COLUMNS)
    return df


def save_data(df: pd.DataFrame):
    df_to_save = df.copy()
    if not df_to_save.empty:
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

# ====== 側邊欄：新增紀錄 + 清空全部 ======
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

amount_str = st.sidebar.text_input("金額（{}）".format(currency))

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

        # 產生新的 ID（目前最大 + 1）
        if df.empty:
            new_id = 1
        else:
            new_id = int(df["ID"].max()) + 1

        new_row = {
            "ID": new_id,
            "日期": dt,
            "星期": weekday_str,
            "類別": category,
            "小類": subcategory,
            "項目": item_name,
            "支付方式": pay_method,
            "幣別": currency,
            "收入": income,
            "支出": expense,
            "支出比例": int(pay_ratio),  # 存整數 %
            "實際支出": actual_expense,
            "備註": note,
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.sidebar.success("已新增一筆紀錄 ✅")
        st.experimental_rerun()

# 危險區：刪除全部紀錄
with st.sidebar.expander("⚠️ 危險區（刪除全部紀錄）"):
    clear_all = st.button("🗑 刪除全部紀錄（不可復原）")
    if clear_all:
        df = pd.DataFrame(columns=COLUMNS)
        save_data(df)
        st.sidebar.success("已刪除全部紀錄")
        st.experimental_rerun()


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
    if category_filter:
        mask &= df["類別"].isin(category_filter)
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

    # 顯示時隱藏 ID，比較乾淨
    show_df = display_df.drop(columns=["ID"])
    st.dataframe(
        show_df.sort_values("日期", ascending=False),
        use_container_width=True
    )

# ====== 修改 / 刪除單筆紀錄 ======
st.subheader("修改 / 刪除紀錄")

if not filtered_df.empty:
    # 用 ID 當選擇 key
    id_list = filtered_df["ID"].tolist()
    id_labels = [
        f"ID {row['ID']}｜{row['日期'].strftime('%Y-%m-%d')}｜{row['類別']}-{row['小類']}｜{row['項目']}"
        for _, row in filtered_df.iterrows()
    ]
    selected = st.selectbox("選擇要修改 / 刪除的紀錄：", options=list(zip(id_list, id_labels)), format_func=lambda x: x[1])
    selected_id = selected[0]

    # 找到這筆資料
    record = df[df["ID"] == selected_id].iloc[0]

    st.markdown("#### 修改這筆紀錄")

    with st.form("edit_record"):
        # 預設值用原本紀錄
        edit_date = st.date_input("日期（修改）", record["日期"].date())
        edit_category = st.selectbox("類別（修改）", CATEGORY_OPTIONS, index=CATEGORY_OPTIONS.index(record["類別"]))
        edit_sub_options = SUBCATEGORY_MAP.get(edit_category, ["其他"])
        # 若原本的小類不在新類別裡，就預設第一個
        try:
            sub_index = edit_sub_options.index(record["小類"])
        except ValueError:
            sub_index = 0
        edit_subcategory = st.selectbox("小類（修改）", edit_sub_options, index=sub_index)

        edit_item = st.text_input("項目（修改）", record["項目"])
        edit_pay = st.selectbox("支付方式（修改）", PAYMENT_OPTIONS, index=PAYMENT_OPTIONS.index(record["支付方式"]))
        edit_currency = st.selectbox("幣別（修改）", CURRENCY_OPTIONS, index=CURRENCY_OPTIONS.index(record["幣別"]) if record["幣別"] in CURRENCY_OPTIONS else 0)

        # 判斷原本是收入還是支出
        original_type = "收入" if record["收入"] > 0 else "支出"
        edit_type = st.radio("這筆是？（修改）", ["支出", "收入"], index=0 if original_type == "支出" else 1, horizontal=True)

        edit_amount_str = st.text_input("金額（修改）", value=str(record["收入"] or record["支出"]))
        edit_ratio = st.number_input("支付比例（修改，%）", min_value=0, max_value=100, value=int(record["支出比例"]), step=5)

        edit_note = st.text_area("備註（修改）", value=record["備註"], height=60)

        save_edit = st.form_submit_button("💾 儲存修改")

    col_del1, col_del2 = st.columns(2)
    with col_del1:
        delete_btn = st.button("🗑 刪除這筆紀錄")

    if save_edit:
        try:
            edit_amount = float(edit_amount_str)
        except ValueError:
            st.error("修改後金額請輸入數字")
            edit_amount = -1

        if edit_amount <= 0:
            st.error("修改後金額必須 > 0")
        else:
            new_dt = datetime.combine(edit_date, datetime.min.time())
            weekday_str = WEEKDAY_LABELS[new_dt.weekday()]
            new_income = edit_amount if edit_type == "收入" else 0.0
            new_expense = edit_amount if edit_type == "支出" else 0.0
            if edit_type == "支出":
                new_actual = new_expense * (edit_ratio / 100.0)
            else:
                new_actual = 0.0

            # 寫回 df
            df.loc[df["ID"] == selected_id, :] = {
                "ID": selected_id,
                "日期": new_dt,
                "星期": weekday_str,
                "類別": edit_category,
                "小類": edit_subcategory,
                "項目": edit_item,
                "支付方式": edit_pay,
                "幣別": edit_currency,
                "收入": new_income,
                "支出": new_expense,
                "支出比例": int(edit_ratio),
                "實際支出": new_actual,
                "備註": edit_note,
            }
            save_data(df)
            st.success("已更新這筆紀錄 ✅")
            st.experimental_rerun()

    if delete_btn:
        df = df[df["ID"] != selected_id].copy()
        save_data(df)
        st.success("已刪除這筆紀錄 🗑")
        st.experimental_rerun()
else:
    st.info("目前沒有可以修改 / 刪除的紀錄。")

# ====== 統計總覽 ======
st.subheader("統計總覽")

if not df.empty:
    all_stats = df.copy()
    all_income = all_stats["收入"].sum()
    all_expense = all_stats["實際支出"].sum()

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

    st.markdown("### 依月份統計（全部資料）")
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
