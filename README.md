# Dashboard Analisis E-Commerce ✨

Proyek analisis data menggunakan **E-Commerce Public Dataset** (Olist), yaitu data pesanan sebuah
marketplace di Brasil. Analisis dibatasi pada pesanan berstatus `delivered` dengan tanggal pembelian
**Januari 2017 - Agustus 2018**. Seluruh nilai uang dalam Brazilian Real (BRL).

## Pertanyaan Bisnis

1. Bagaimana tren revenue bulanan pada Januari 2017 - Agustus 2018, dan kategori produk apa saja
   yang menyumbang revenue tertinggi dan terendah?
2. Seberapa besar keterlambatan pengiriman menurunkan rata-rata review score pelanggan pada
   Januari 2017 - Agustus 2018, dan di state mana pesanan paling sering terlambat?

Analisis lanjutan: **RFM Analysis** beserta segmentasi pelanggan, dan **binning** untuk
mengelompokkan tingkat keterlambatan pengiriman.

## Isi Dashboard

| Tab | Isi |
|---|---|
| Revenue & Kategori | Tren revenue bulanan serta 5 kategori dengan revenue tertinggi dan terendah |
| Pengiriman & Review | Pengaruh keterlambatan terhadap review score, dan 10 state dengan order terlambat terbanyak |
| Analisis RFM | Pelanggan terbaik per parameter RFM dan segmentasi pelanggan |

Tersedia filter **rentang waktu** pada sidebar. Seluruh angka, grafik, dan teks insight ikut
menyesuaikan rentang waktu yang dipilih.

## Struktur Berkas

```
submission
├── dashboard
│   ├── dashboard.py
│   ├── logo.png
│   └── main_data.csv
├── data
│   ├── customers_dataset.csv
│   ├── orders_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── products_dataset.csv
│   └── product_category_name_translation.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment - Anaconda

```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```
mkdir Data_Analysis_E-Commerce
cd Data_Analysis_E-Commerce
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run steamlit app

```
streamlit run dashboard/dashboard.py
```

## Menjalankan Notebook

Jalankan `notebook.ipynb` dari folder utama proyek (folder yang sama dengan berkas README ini),
karena notebook membaca dataset dari folder `data/`. Sel terakhir pada notebook akan menghasilkan
kembali berkas `dashboard/main_data.csv` yang dipakai oleh dashboard.

```
jupyter-notebook .
```
