import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

# 注意：
# st.set_page_config 建議只在 app.py （主程式）裡呼叫
# 這個分頁就不要再呼叫一次，以免衝突

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


def load_assets():
    if ASSET_FILE.exists():
        df = pd.read_csv(ASSET_FILE)

        # 確保欄位齊全
        for col in ASSET_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # 轉換日期格式
        df["購買日期"] = pd.to_datetime(df["購買日期"]).dt.date

        # 每次開啟自動更新「持有天數」和「每日均攤費用」
        today = date.today()
        df["持有天數"] = (pd.Series(today for _ in df.index) - pd.to_datetime(df["購買日期"]).dt.date).dt.days + 1
        df.loc[df["持有天數"] <= 0, "持有天數"] = 1  # 避免 0 或負數

        df["每日均攤費用"] = (df["金額"] / df["持有天數"]).round(2)

        return df[ASSET_COLUMNS]
    else:
        df = pd.DataFrame(columns=ASSET_COLUMNS)
        df.to_csv(ASSET_FILE, index=False, encoding="utf-8-sig")
        return df


def save_assets(df: pd.DataFrame):
    df.to_csv(ASSET_FILE, index=False, encoding="utf-8-sig")


def main():
    st.title("固定資產折舊計算")

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
        st.success("已新增固定資產資料！")

    st.subheader("固定資產總覽")
    st.dataframe(df_assets, use_container_width=True)

    # （可選）簡單統計：每日均攤總額
    if not df_assets.empty:
        total_daily_cost = df_assets["每日均攤費用"].sum()
        st.markdown(f"**目前所有資產合計每日均攤費用：約 {total_daily_cost:.2f} 元**")


if __name__ == "__main__":
    main()
