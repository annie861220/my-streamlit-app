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

# ====== 預先算「本月」與「長期」統計 ======
today = date.today()
if not df.empty:
    this_month_mask = (
        (df["日期"].dt.year == today.year) &
        (df["日期"].dt.month == today.month)
    )
    this_month_df = df[this_month_mask].copy()
else:
    this_month_df = df.copy()

# 本月統計（固定，不看篩選）
if not this_month_df.empty:
    month_income = this_month_df["收入"].sum()
    month_expense = this_month_df["實際支出"].sum()
    month_net = month_income - month_expense
else:
    month_income = month_expense = month_net = 0.0

# 長期統計（全部資料）
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

# ====== 本月統計總覽（固定本月，不跟篩選跑） ======
st.subheader("本月統計總覽")

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        f"""
        <div class="kpi-card kpi-income">
            <div class="kpi-label">本月收入</div>
            <div class="kpi-value">{month_income:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"""
        <div class="kpi-card kpi-expense">
            <div class="kpi-label">本月支出（實際）</div>
            <div class="kpi-value">{month_expense:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"""
        <div class="kpi-card kpi-net">
            <div class="kpi-label">本月結餘（收入 - 支出）</div>
            <div class="kpi-value">{month_net:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ====== 明細紀錄 ======
st.subheader("明細紀錄")

if filtered_df.empty:
    st.info("目前沒有符合條件的紀錄。")
else:
    edit_df = filtered_df.sort_values("日期", ascending=False).copy()

    # 不要顯示 ID（如果 csv 裡還有舊欄位）
    if "ID" in edit_df.columns:
        edit_df = edit_df.drop(columns=["ID"])

    # 顯示用字串日期
    edit_df["日期"] = edit_df["日期"].dt.strftime("%Y-%m-%d")

    if "刪除" not in edit_df.columns:
        edit_df["刪除"] = False

    st.markdown(
        '<p class="hint-text">直接在下列表格中修改欄位內容，或勾選「刪除」，最後按下方按鈕儲存。</p>',
        unsafe_allow_html=True,
    )

    column_order = [
        "日期", "星期", "類別", "小類", "項目",
        "支付方式", "幣別",
        "收入", "支出", "支出比例", "實際支出",
        "備註", "刪除",
    ]
    column_order = [c for c in column_order if c in edit_df.columns]

    edited_df = st.data_editor(
        edit_df,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        column_order=column_order,
        key="editor",
    )

    if st.button("💾 儲存修改 / 刪除"):
        new_df = df.copy()

        # edited_df 的 index = 原本 df 的 index
        for idx, row in edited_df.iterrows():
            # 刪除優先
            if "刪除" in row and row["刪除"]:
                if idx in new_df.index:
                    new_df = new_df.drop(index=idx)
                continue

            # 修改資料
            try:
                new_date = datetime.strptime(str(row["日期"]), "%Y-%m-%d")
            except ValueError:
                st.error(f"第 {idx} 列日期格式錯誤，請用 YYYY-MM-DD")
                continue

            try:
                new_income = float(row["收入"]) if str(row["收入"]).strip() != "" else 0.0
                new_expense = float(row["支出"]) if str(row["支出"]).strip() != "" else 0.0
                new_ratio = int(row["支出比例"]) if str(row["支出比例"]).strip() != "" else 0
            except ValueError:
                st.error(f"第 {idx} 列的金額或比例欄位有非數字，請修正。")
                continue

            if new_expense > 0:
                new_actual = new_expense * (new_ratio / 100.0)
            else:
                new_actual = 0.0

            if idx in new_df.index:
                new_df.loc[idx, "日期"] = new_date
                new_df.loc[idx, "星期"] = row["星期"]
                new_df.loc[idx, "類別"] = row["類別"]
                new_df.loc[idx, "小類"] = row["小類"]
                new_df.loc[idx, "項目"] = row["項目"]
                new_df.loc[idx, "支付方式"] = row["支付方式"]
                new_df.loc[idx, "幣別"] = row["幣別"]
                new_df.loc[idx, "收入"] = new_income
                new_df.loc[idx, "支出"] = new_expense
                new_df.loc[idx, "支出比例"] = new_ratio
                new_df.loc[idx, "實際支出"] = new_actual
                new_df.loc[idx, "備註"] = row["備註"]

        df = new_df
        save_data(df)
        st.success("已套用修改 / 刪除 ✅")

st.divider()

# ====== 長期統計（全部資料） ======
st.subheader("長期統計（全部資料）")

if not df.empty:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="kpi-card kpi-income">
                <div class="kpi-label">全部紀錄收入</div>
                <div class="kpi-value">{all_income:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi-card kpi-expense">
                <div class="kpi-label">全部紀錄支出</div>
                <div class="kpi-value">{all_expense:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-card kpi-net">
                <div class="kpi-label">全部紀錄結餘</div>
                <div class="kpi-value">{all_net:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ====== 依月份統計（卡片式） ======
    st.subheader("依月份統計（卡片式）")

    month_stats = df.copy()
    month_stats["月份"] = month_stats["日期"].dt.strftime("%Y-%m")
    by_month = (
        month_stats.groupby("月份")[["收入", "實際支出"]]
        .sum()
        .rename(columns={"實際支出": "支出"})
        .sort_values("月份", ascending=True)
    )

    if by_month.empty:
        st.info("尚無資料可以進行月份統計。")
    else:
        for ym, row in by_month.iterrows():
            income = row["收入"]
            expense = row["支出"]
            net = income - expense

            st.markdown(
                f"""
                <div class="month-card">
                    <div class="month-title">{ym}</div>

                    <div class="month-line">
                        <div class="month-line-label">收入</div>
                        <div class="month-line-income">{income:,.0f}</div>
                    </div>

                    <div class="month-line">
                        <div class="month-line-label">支出</div>
                        <div class="month-line-expense">{expense:,.0f}</div>
                    </div>

                    <div class="month-line">
                        <div class="month-line-label">結餘</div>
                        <div class="month-line-net">{net:,.0f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("尚無資料可以統計。")
