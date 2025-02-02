import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import json
import requests
import folium
from folium.plugins import FastMarkerCluster
from streamlit_folium import st_folium

sns.set_theme(style="dark")

combined_df = pd.read_csv("./data/combined_df.csv")
geolocation_df = pd.read_csv("./data/geolocation_dataset.csv")
combined_df["order_approved_at"] = pd.to_datetime(combined_df["order_approved_at"])
min_date = combined_df["order_approved_at"].min().date()
max_date = combined_df["order_approved_at"].max().date()

with st.sidebar:
    start_date, end_date = st.date_input(
        label="Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],
    )

main_df = combined_df[
    (combined_df["order_approved_at"] >= str(start_date))
    & (combined_df["order_approved_at"] <= str(end_date))
]

st.title("Proyek Analisis Data: E-Commerce Public Dataset by Olist")
st.markdown(
    """
**Pertanyaan Bisnis:** \n
1. Bagaimana pengaruh harga produk dengan volume penjualan produk
2. Wilayah mana yang melakukan pembelian terbanyak
"""
)
st.subheader("Deskripsi Data")
st.write(combined_df.describe())
st.subheader("Dataframe")
st.dataframe(combined_df.head())


st.subheader("1. Pengaruh Harga Produk dengan Volume Penjualan Produk")

bins = [0, 50, 100, 200, 500, 1000, 5000, 10000, 50000]
labels = [
    "0-50",
    "50-100",
    "100-200",
    "200-500",
    "500-1000",
    "1000-5000",
    "5000-10000",
    "10000+",
]
main_df.loc[:, "price_bin"] = pd.cut(
    main_df["price"], bins=bins, labels=labels, right=False
)
corr_main_df = (
    main_df.groupby("price_bin", observed=False)
    .agg({"product_id": "nunique", "order_item_id": "count", "price": "mean"})
    .reset_index()
)

plt.figure(figsize=(12, 6))
sns.barplot(x="price_bin", y="order_item_id", data=corr_main_df, palette="Blues_r")
plt.title("Volume Penjualan Berdasarkan Rentang Harga (BRL)", fontsize=14)
plt.xlabel("Rentang Harga (BRL)", fontsize=12)
plt.ylabel("Jumlah Produk Terjual", fontsize=12)
plt.xticks(rotation=45)
st.pyplot(plt.gcf())

plt.figure(figsize=(6, 4))
corr_matrix = corr_main_df[["order_item_id", "price"]].corr()
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
plt.title("Heatmap Korelasi antara Harga barang dan jumlah terjualnya barang")
st.pyplot(plt.gcf())

st.markdown(
    """**Pengaruh Harga produk dengan volume pembelian produk**  
terlihat bahwa terdapat hubungan negatif moderat antara harga produk dan volume penjualan produk. Korelasi antara harga dan volume penjualan adalah -0.58, yang menunjukkan bahwa peningkatan harga cenderung mengurangi volume penjualan produk 
"""
)

st.subheader("2. Wilayah mana yang melakukan pembelian terbanyak")

r = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/mesorregioes")
content = [c["UF"] for c in json.loads(r.text)]
br_info = pd.DataFrame(content)
br_info["nome_regiao"] = br_info["regiao"].apply(lambda x: x["nome"])
br_info.drop("regiao", axis=1, inplace=True)
br_info.drop_duplicates(inplace=True)

geo_group = geolocation_df.groupby(
    by="geolocation_zip_code_prefix", as_index=False
).min()

map_df = main_df.merge(br_info, how="left", left_on="customer_state", right_on="sigla")

map_df = map_df.merge(
    geo_group,
    how="left",
    left_on="customer_zip_code_prefix",
    right_on="geolocation_zip_code_prefix",
)

valid_latitude_range = (-33.75, 5.3)
valid_longitude_range = (-73.98, -34.79)

map_df = map_df[
    (map_df["geolocation_lat"] >= valid_latitude_range[0])
    & (map_df["geolocation_lat"] <= valid_latitude_range[1])
    & (map_df["geolocation_lng"] >= valid_longitude_range[0])
    & (map_df["geolocation_lng"] <= valid_longitude_range[1])
]

map_df.drop_duplicates(inplace=True)
lats = list(map_df["geolocation_lat"].dropna().values)
longs = list(map_df["geolocation_lng"].dropna().values)
locations = list(zip(lats, longs))
map1 = folium.Map(location=[-15, -50], zoom_start=4.0)
FastMarkerCluster(data=locations).add_to(map1)

st_folium(map1)

st.markdown(
    """**Kota dengan pembelian terbanyak**  
Produk dengan distribusi tertinggi terletak di wilayah Tenggara dan Selatan Brasil, yang merupakan daerah dengan kepadatan penduduk terbesar. Misalnya, wilayah Tenggara, khususnya São Paulo, memiliki populasi sekitar 12 juta penduduk.
"""
)

st.title("Kesimpulan")
st.markdown(
    """
1. harga yang lebih rendah berhubungan dengan volume penjualan yang lebih tinggi, sementara harga yang lebih tinggi mengarah pada volume penjualan yang lebih rendah. Ini mencerminkan pola umum dalam e-commerce, di mana produk dengan harga lebih rendah cenderung lebih terjangkau dan lebih diminati oleh konsumen, sedangkan produk dengan harga tinggi mungkin lebih terbatas dalam permintaan karena faktor harga yang lebih tinggi. Namun, meskipun harga berperan penting dalam menentukan volume penjualan, faktor-faktor lain seperti kualitas produk, kategori produk, serta strategi pemasaran juga turut memengaruhi hasil ini.
2. São Paulo muncul sebagai kota dengan jumlah pembelian terbanyak, yang mengindikasikan bahwa kota ini memiliki jumlah pelanggan yang besar dan aktivitas belanja yang lebih tinggi dibandingkan dengan kota-kota lainnya. Hal ini bisa dipengaruhi oleh faktor seperti populasi yang besar, ekonomi yang kuat, dan akses lebih mudah ke berbagai produk dan layanan.
"""
)
