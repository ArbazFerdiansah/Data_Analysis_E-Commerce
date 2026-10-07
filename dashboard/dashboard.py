# Impor library yang digunakan
import os                              # Menentukan lokasi berkas data
import pandas as pd                    # Manipulasi data
import matplotlib.pyplot as plt        # Membuat grafik
import seaborn as sns                  # Membuat grafik
import streamlit as st                 # Membuat aplikasi web

import warnings
warnings.filterwarnings("ignore")

# Konfigurasi halaman streamlit (harus menjadi perintah streamlit pertama)
st.set_page_config(page_title="Analisis E-Commerce", layout="wide")

# Urutan kelompok keterlambatan, dipakai agar grafik terbaca dari yang paling cepat
DELAY_ORDER = ["Tepat waktu", "Telat 1-3 hari", "Telat 4-7 hari", "Telat 8-14 hari", "Telat >14 hari"]

# Helper function yang dibutuhkan untuk menyiapkan berbagai dataframe

@st.cache_data
def load_data():
    # Berkas dibaca dari folder yang sama dengan dashboard.py, bukan dari folder tempat perintah dijalankan
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_data.csv")
    df = pd.read_csv(path)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df.sort_values(by="order_purchase_timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["delay_group"] = pd.Categorical(df["delay_group"], categories=DELAY_ORDER, ordered=True)

    return df

def create_order_df(df):
    # satu baris = satu order (main_data.csv berisi data per item, jadi order bisa muncul lebih dari sekali)
    order_df = df.drop_duplicates(subset="order_id")
    return order_df

def create_monthly_revenue_df(df):
    df = df.copy()
    df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    monthly_revenue_df = df.groupby(by="order_month").agg({
        "order_id": "nunique",
        "revenue": "sum"
    })
    monthly_revenue_df = monthly_revenue_df.reset_index()
    monthly_revenue_df.rename(columns={
        "order_id": "order_count"
    }, inplace=True)

    return monthly_revenue_df

def create_category_df(df):
    category_df = df.groupby("product_category_name_english").revenue.sum().sort_values(ascending=False).reset_index()
    return category_df

def create_delay_df(df):
    delay_df = create_order_df(df).groupby(by="delay_group").review_score.mean().reset_index()
    return delay_df

def create_state_late_df(df):
    state_late_df = create_order_df(df).groupby(by="customer_state").agg({
        "order_id": "nunique",
        "is_late": "mean",
        "review_score": "mean"
    }).sort_values(by="is_late", ascending=False)
    state_late_df["is_late"] = state_late_df["is_late"] * 100
    state_late_df = state_late_df.reset_index()

    return state_late_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max",  # mengambil tanggal order terakhir
        "order_id": "nunique",
        "revenue": "sum"
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]

    # menghitung kapan terakhir pelanggan melakukan transaksi (hari)
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    # ID dipersingkat agar label pada grafik mudah dibaca
    rfm_df["short_id"] = rfm_df["customer_unique_id"].str[:6]

    return rfm_df

def create_segment_df(rfm_df):
    # pembagian kuantil butuh minimal 5 pelanggan
    if len(rfm_df) < 5:
        return None

    # memberi skor recency & monetary (1-5), lalu mengelompokkan pelanggan ke dalam 4 segmen
    rfm_df["r_score"] = pd.qcut(rfm_df["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm_df["m_score"] = pd.qcut(rfm_df["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    def assign_segment(row):
        if row["frequency"] >= 2:
            return "Loyal Customers"
        if row["r_score"] >= 3:
            return "Recent Customers"
        if row["m_score"] >= 4:
            return "At Risk Big Spenders"
        return "Lapsed Customers"

    rfm_df["segment"] = rfm_df.apply(assign_segment, axis=1)

    segment_df = rfm_df.groupby(by="segment").agg({
        "customer_unique_id": "nunique",
        "monetary": "sum"
    })
    segment_df.columns = ["jumlah_pelanggan", "total_monetary"]
    segment_df["persen_pelanggan"] = segment_df["jumlah_pelanggan"] / segment_df["jumlah_pelanggan"].sum() * 100
    segment_df["persen_revenue"] = segment_df["total_monetary"] / segment_df["total_monetary"].sum() * 100
    segment_df = segment_df.sort_values(by="jumlah_pelanggan", ascending=False).reset_index()

    return segment_df

# Mendefinisikan fungsi utama yang menjalankan seluruh program di dalamnya
def main():

    # Memuat data yang sudah dibersihkan pada notebook
    all_df = load_data()

    min_date = all_df["order_purchase_timestamp"].min()
    max_date = all_df["order_purchase_timestamp"].max()

    # Membuat sidebar
    with st.sidebar:
        # Menampilkan logo
        st.image("https://raw.githubusercontent.com/ArbazFerdiansah/images/refs/heads/main/e-commerce.png")

        # Menampilkan teks
        st.title("Analisis E-Commerce")
        st.write("Arbaz Ferdiansah")
        st.text(2026)

        st.subheader("Filter")

        # Mengambil start_date & end_date dari date_input
        date_range = st.date_input(
            label='Rentang Waktu', min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )

        st.caption("Data: E-Commerce Public Dataset (Olist), order berstatus delivered "
                   "Jan 2017 - Agu 2018. Nilai uang dalam BRL.")

    # Menunggu sampai pengguna memilih tanggal akhir
    if len(date_range) != 2:
        st.info("Pilih tanggal akhir pada filter untuk menampilkan data.")
        return
    start_date, end_date = date_range

    # Menyaring data sesuai rentang waktu yang dipilih
    main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) &
                     (all_df["order_purchase_timestamp"] <= str(end_date) + " 23:59:59")]

    if main_df.empty:
        st.warning("Tidak ada data pada rentang waktu yang dipilih. Coba perlebar rentang waktunya.")
        return

    # Menyiapkan berbagai dataframe
    order_df = create_order_df(main_df)
    monthly_revenue_df = create_monthly_revenue_df(main_df)
    category_df = create_category_df(main_df)
    delay_df = create_delay_df(main_df)
    state_late_df = create_state_late_df(main_df)
    rfm_df = create_rfm_df(main_df)
    segment_df = create_segment_df(rfm_df)

    # Nilai pembanding dari seluruh data, dipakai sebagai delta pada metric
    all_order_df = create_order_df(all_df)
    base_review = all_order_df.review_score.mean()
    base_late = all_order_df.is_late.mean() * 100
    is_filtered = len(main_df) < len(all_df)   # delta hanya ditampilkan saat data disaring

    # Membuat judul dashboard
    st.title("Dashboard Analisis E-Commerce :sparkles:")
    st.caption(f"Periode {start_date:%d %b %Y} - {end_date:%d %b %Y} | Seluruh state")

    # Membuat tiga tab untuk navigasi
    tab1, tab2, tab3 = st.tabs(["Revenue & Kategori", "Pengiriman & Review", "Analisis RFM"])

    # Tab 1: Pertanyaan 1
    with tab1:
        st.header("Monthly Revenue")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_orders = monthly_revenue_df.order_count.sum()
            st.metric("Total Orders", value=f"{total_orders:,}")

        with col2:
            total_revenue = monthly_revenue_df.revenue.sum()
            st.metric("Total Revenue (BRL)", value=f"{total_revenue:,.0f}")

        with col3:
            # Revenue bulan terakhir beserta perubahannya dibanding bulan sebelumnya
            last_revenue = monthly_revenue_df.revenue.iloc[-1]
            last_month = monthly_revenue_df.order_month.iloc[-1]
            if len(monthly_revenue_df) >= 2:
                prev_revenue = monthly_revenue_df.revenue.iloc[-2]
                growth = (last_revenue - prev_revenue) / prev_revenue * 100
                st.metric(f"Revenue {last_month}", value=f"{last_revenue:,.0f}",
                          delta=f"{growth:.1f}% vs bulan sebelumnya")
            else:
                st.metric(f"Revenue {last_month}", value=f"{last_revenue:,.0f}")

        fig, ax = plt.subplots(figsize=(16, 8))
        ax.plot(
            monthly_revenue_df["order_month"],
            monthly_revenue_df["revenue"],
            marker='o',
            linewidth=2,
            color="#72BCD4"
        )
        ax.set_title("Revenue Bulanan (BRL)", loc="center", fontsize=25)
        ax.tick_params(axis='y', labelsize=20)
        ax.tick_params(axis='x', labelsize=15, rotation=45)
        ax.ticklabel_format(style="plain", axis="y")

        st.pyplot(fig)

        # Insight otomatis mengikuti filter yang sedang aktif
        peak = monthly_revenue_df.loc[monthly_revenue_df.revenue.idxmax()]
        st.info(f"**Insight:** Revenue tertinggi terjadi pada **{peak['order_month']}** "
                f"sebesar **BRL {peak['revenue']:,.0f}** dari {peak['order_count']:,} order.")

        st.header("Best & Worst Category by Revenue")

        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

        colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

        sns.barplot(x="revenue", y="product_category_name_english", data=category_df.head(5), palette=colors, ax=ax[0])
        ax[0].set_ylabel(None)
        ax[0].set_xlabel("Revenue (BRL)", fontsize=30)
        ax[0].set_title("Kategori dengan Revenue Tertinggi", loc="center", fontsize=50)
        ax[0].tick_params(axis='y', labelsize=35)
        ax[0].tick_params(axis='x', labelsize=30)
        ax[0].ticklabel_format(style="plain", axis="x")
        for container in ax[0].containers:
            ax[0].bar_label(container, fmt="%.0f", fontsize=28)
        ax[0].margins(x=0.2)

        sns.barplot(x="revenue", y="product_category_name_english", data=category_df.sort_values(by="revenue", ascending=True).head(5), palette=colors, ax=ax[1])
        ax[1].set_ylabel(None)
        ax[1].set_xlabel("Revenue (BRL)", fontsize=30)
        ax[1].invert_xaxis()
        ax[1].yaxis.set_label_position("right")
        ax[1].yaxis.tick_right()
        ax[1].set_title("Kategori dengan Revenue Terendah", loc="center", fontsize=50)
        ax[1].tick_params(axis='y', labelsize=35)
        ax[1].tick_params(axis='x', labelsize=30)
        for container in ax[1].containers:
            ax[1].bar_label(container, fmt="%.0f", fontsize=28)
        ax[1].margins(x=0.2)

        st.pyplot(fig)

        top5_share = category_df.head(5).revenue.sum() / category_df.revenue.sum() * 100
        st.info(f"**Insight:** Dari **{len(category_df)}** kategori, 5 kategori teratas menyumbang "
                f"**{top5_share:.1f}%** dari seluruh revenue. Kategori terbawah "
                f"(**{category_df.iloc[-1]['product_category_name_english']}**) hanya "
                f"BRL {category_df.iloc[-1]['revenue']:,.0f}.")

    # Tab 2: Pertanyaan 2
    with tab2:
        st.header("Delivery Delay & Review Score")

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_review = order_df.review_score.mean()
            st.metric("Average Review Score", value=f"{avg_review:.2f}",
                      delta=f"{avg_review - base_review:+.2f} vs seluruh data" if is_filtered else None)

        with col2:
            late_pct = order_df.is_late.mean() * 100
            # delta_color="inverse" supaya kenaikan keterlambatan ditandai merah
            st.metric("Late Orders", value=f"{late_pct:.2f}%",
                      delta=f"{late_pct - base_late:+.2f} poin vs seluruh data" if is_filtered else None,
                      delta_color="inverse")

        with col3:
            st.metric("Total Orders", value=f"{order_df.order_id.nunique():,}")

        fig, ax = plt.subplots(figsize=(20, 10))

        colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

        sns.barplot(x="delay_group", y="review_score", data=delay_df, palette=colors, ax=ax)
        ax.set_title("Rata-rata Review Score berdasarkan Keterlambatan", loc="center", fontsize=40)
        ax.set_xlabel("Kelompok keterlambatan dibanding estimasi tiba", fontsize=25)
        ax.set_ylabel("Rata-rata review score", fontsize=25)
        ax.tick_params(axis='x', labelsize=22)
        ax.tick_params(axis='y', labelsize=20)
        for container in ax.containers:
            ax.bar_label(container, fmt="%.2f", fontsize=22)
        ax.margins(y=0.1)

        st.pyplot(fig)

        ontime = delay_df.loc[delay_df.delay_group == "Tepat waktu", "review_score"]
        worst = delay_df.loc[delay_df.review_score.idxmin()]
        if not ontime.empty:
            st.info(f"**Insight:** Review turun dari **{ontime.iloc[0]:.2f}** saat tepat waktu "
                    f"menjadi **{worst['review_score']:.2f}** pada kelompok **{worst['delay_group']}**.")

        st.header("Late Orders by State")

        fig, ax = plt.subplots(figsize=(20, 10))

        colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3",
                  "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

        sns.barplot(x="is_late", y="customer_state", data=state_late_df.head(10), palette=colors, ax=ax)
        ax.set_title("10 State dengan Persentase Order Terlambat Tertinggi", loc="center", fontsize=40)
        ax.set_xlabel("Persentase order terlambat (%)", fontsize=25)
        ax.set_ylabel("State Pelanggan", fontsize=25)
        ax.tick_params(axis='y', labelsize=25)
        ax.tick_params(axis='x', labelsize=20)
        for container in ax.containers:
            ax.bar_label(container, fmt="%.1f%%", fontsize=22)
        ax.margins(x=0.1)

        st.pyplot(fig)

        top_state = state_late_df.iloc[0]
        st.info(f"**Insight:** State dengan keterlambatan tertinggi adalah **{top_state['customer_state']}** "
                f"(**{top_state['is_late']:.1f}%** dari {top_state['order_id']:,} order), "
                f"dibanding rata-rata **{late_pct:.2f}%**. Perhatikan jumlah order tiap state, "
                f"karena state dengan order sedikit membuat persentasenya kurang andal.")

    # Tab 3: Analisis lanjutan
    with tab3:
        st.header("Best Customer Based on RFM Parameters")

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_recency = round(rfm_df.recency.mean(), 1)
            st.metric("Average Recency (days)", value=avg_recency)

        with col2:
            avg_frequency = round(rfm_df.frequency.mean(), 2)
            repeat_pct = (rfm_df.frequency > 1).mean() * 100
            st.metric("Average Frequency", value=avg_frequency,
                      delta=f"{repeat_pct:.1f}% pelanggan belanja ulang", delta_color="off")

        with col3:
            avg_monetary = rfm_df.monetary.mean()
            st.metric("Average Monetary (BRL)", value=f"{avg_monetary:,.1f}")

        fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))

        colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]

        sns.barplot(y="recency", x="short_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
        ax[0].set_ylabel(None)
        ax[0].set_xlabel("customer_unique_id (6 karakter pertama)", fontsize=30)
        ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
        ax[0].tick_params(axis='y', labelsize=30)
        ax[0].tick_params(axis='x', labelsize=30, rotation=45)
        for container in ax[0].containers:
            ax[0].bar_label(container, fmt="%.0f", fontsize=28)
        ax[0].margins(y=0.2)

        sns.barplot(y="frequency", x="short_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
        ax[1].set_ylabel(None)
        ax[1].set_xlabel("customer_unique_id (6 karakter pertama)", fontsize=30)
        ax[1].set_title("By Frequency", loc="center", fontsize=50)
        ax[1].tick_params(axis='y', labelsize=30)
        ax[1].tick_params(axis='x', labelsize=30, rotation=45)
        for container in ax[1].containers:
            ax[1].bar_label(container, fmt="%.0f", fontsize=28)
        ax[1].margins(y=0.2)

        sns.barplot(y="monetary", x="short_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
        ax[2].set_ylabel(None)
        ax[2].set_xlabel("customer_unique_id (6 karakter pertama)", fontsize=30)
        ax[2].set_title("By Monetary (BRL)", loc="center", fontsize=50)
        ax[2].tick_params(axis='y', labelsize=30)
        ax[2].tick_params(axis='x', labelsize=30, rotation=45)
        for container in ax[2].containers:
            ax[2].bar_label(container, fmt="%.0f", fontsize=28)
        ax[2].margins(y=0.2)

        st.pyplot(fig)

        st.info(f"**Insight:** Dari **{len(rfm_df):,}** pelanggan, hanya **{repeat_pct:.1f}%** "
                f"yang berbelanja lebih dari sekali. Pelanggan dengan belanja terbesar mencapai "
                f"**BRL {rfm_df.monetary.max():,.0f}**. Recency bernilai 0 berarti pelanggan "
                f"berbelanja tepat pada hari terakhir data.")

        st.header("Customer Segmentation Based on RFM")

        if segment_df is None:
            st.warning("Jumlah pelanggan terlalu sedikit untuk membuat segmentasi RFM.")
        else:
            fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(30, 10))

            sns.barplot(x="persen_pelanggan", y="segment", data=segment_df, color="#72BCD4", ax=ax[0])
            ax[0].set_ylabel(None)
            ax[0].set_xlabel("% dari seluruh pelanggan", fontsize=25)
            ax[0].set_title("Persentase Pelanggan per Segmen", loc="center", fontsize=40)
            ax[0].tick_params(axis='y', labelsize=25)
            ax[0].tick_params(axis='x', labelsize=20)
            for container in ax[0].containers:
                ax[0].bar_label(container, fmt="%.1f%%", fontsize=22)
            ax[0].margins(x=0.35)

            sns.barplot(x="persen_revenue", y="segment", data=segment_df, color="#72BCD4", ax=ax[1])
            ax[1].set_ylabel(None)
            ax[1].set_xlabel("% dari total revenue", fontsize=25)
            ax[1].set_title("Persentase Revenue per Segmen", loc="center", fontsize=40)
            ax[1].tick_params(axis='y', labelsize=25)
            ax[1].tick_params(axis='x', labelsize=20)
            for container in ax[1].containers:
                ax[1].bar_label(container, fmt="%.1f%%", fontsize=22)
            ax[1].margins(x=0.35)

            st.pyplot(fig)

            # Segmen dengan selisih kontribusi revenue terbesar dibanding jumlah pelanggannya
            segment_df["selisih"] = segment_df["persen_revenue"] - segment_df["persen_pelanggan"]
            best = segment_df.loc[segment_df["selisih"].idxmax()]
            st.info(f"**Insight:** Segmen **{best['segment']}** hanya **{best['persen_pelanggan']:.1f}%** "
                    f"dari pelanggan tetapi menyumbang **{best['persen_revenue']:.1f}%** revenue, "
                    f"sehingga paling layak diprioritaskan.")

    # Menampilkan teks dalam ukuran kecil
    st.caption('Copyright (c) Arbaz Ferdiansah 2026')

# Memastikan fungsi main() dijalankan jika skrip dieksekusi
if __name__ == "__main__":
    main()
