import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

# 不要在這裡 set_page_config，主頁 app.py 已經有設定就好

# ====== 檔案設定 ======
ASSET_FILE = Path("assets.csv")

ASSET_COLUMNS = [
    "分類",
    "小類",
    "產品名稱",
    "品牌/型號",
    "購買日期",
    "金額",
    "持有天數",
    "每日均攤費用",
    "當前狀態(服役中/已除役)",
    "地點",
    "備註",
]


def load_assets() -> pd.DataFrame:
    if ASSET_FILE.exists():
        df = pd.read_csv(ASSET_FILE)

        # 確保欄位都有（之後如果你加欄位，不會因為舊資料爆炸）
        for col in ASSET_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # 數值欄位轉數字
        df["金額"] = pd.to_numeric(df["金額"], errors="coerce").fillna(0)

        # 日期欄位轉成 datetime
        df["購買日期"] = pd.to_datetime(df["購買日期"], errors="coerce")

        # 自動更新「持有天數」與「每日均攤費用」
        today = pd.to_datetime(date.today())
        valid_mask = df["購買日期"].notna()
        df.loc[valid_mask, "持有天數"] = (today - df.loc[valid_mask, "購買日期"]).dt.days + 1
        df.loc[~valid_mask, "持有天數"] = 1  # 如果沒填日期，先當 1 天避免除以 0
        df.loc[df["持有天數"] <= 0, "持有天數"] = 1

        df["每日均攤費用"] = (df["金額"] / df["持有天數"]).round(2)

        # 顯示時，購買日期改成 date（不帶時間）
        df["購買日期"] = df["購買日期"].dt.date

        return df[ASSET_COLUMNS]
    else:
        df = pd.DataFrame(columns=ASSET_COLUMNS)
        df.to_csv(ASSET_FILE, index=False, encoding="utf-8-sig")
        return df


def save_assets(df: pd.DataFrame):
    df_to_save = df.copy()
    # 存檔前，把日期轉成字串，不然有時候會有格式問題
    if not df_to_save.empty:
        df_to_save["購買日期"] = pd.to_datetime(df_to_save["購買日期"]).dt.strftime("%Y-%m-%d")
    df_to_save.to_csv(ASSET_FILE, index=False, encoding="utf-8-sig")


def main():
    st.title("🧱 固定資產折舊計算")

    # 讀取現有資料 & 自動更新 天數 / 均攤費用
    df_assets = load_assets()

    st.subheader("新增 / 登記固定資產")

    with st.form("asset_form"):
        col1, col2 = st.columns(2)

        with col1:
            category = st.text_input("分類", placeholder="例如：3C、家電、家具、衣物…")
            subcategory = st.text_input("小類", placeholder="例如：手機、電腦、外套…")
            name = st.text_input("產品名稱", placeholder="例如：iPhone 16、羽絨外套…")
            brand_model = st.text_input("品牌/型號", placeholder="例如：Apple / 256GB")
            location = st.text_input("地點", placeholder="例如：家裡房間、公司…")

        with col2:
            purchase_date = st.date_input("購買日期", value=date.today())
            amount = st.number_input("金額", min_value=0.0, step=100.0)
            status = st.selectbox("當前狀態", ["服役中", "已除役"])
            note = st.text_input("備註", placeholder="例如：團購價、二手購入、含配件…")

        submitted = st.form_submit_button("新增資產")

    if submitted:
        today = date.today()
        holding_days = (today - purchase_date).days + 1
        if holding_days <= 0:
            holding_days = 1

        daily_cost = round(amount / holding_days, 2) if holding_days > 0 else 0

        new_row = {
            "分類": category,
            "小類": subcategory,
            "產品名稱": name,
            "品牌/型號": brand_model,
            "購買日期": purchase_date,
            "金額": amount,
            "持有天數": holding_days,
            "每日均攤費用": daily_cost,
            "當前狀態(服役中/已除役)": status,
            "地點": location,
            "備註": note,
        }

        df_assets = pd.concat([df_assets, pd.DataFrame([new_row])], ignore_index=True)
        save_assets(df_assets)
        st.success("已新增固定資產資料 ✅")

    st.subheader("固定資產總覽")

    if df_assets.empty:
        st.info("目前尚未登記任何固定資產。")
    else:
        st.dataframe(df_assets, use_container_width=True)

        # 簡單統計：所有資產每日均攤總額
        total_daily_cost = df_assets["每日均攤費用"].sum()
        st.markdown(f"**目前所有資產合計每日均攤費用：約 {total_daily_cost:,.2f} 元**")


if __name__ == "__main__":
    main()
