import streamlit as st
import pandas as pd
import datetime
import utils
from views import dashboard, visualisasi, input_data, dataset, perbandingan

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Sistem Prediksi Apotek (Multi-Shift)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. LOAD CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 3. LOAD MODEL & DATA
model, df_historis = utils.load_resources()

if model is None:
    st.error("Error: File model 'model_skripsi_multishift.pkl' tidak ditemukan!")
    st.stop()

# 4. SIDEBAR GLOBAL
st.sidebar.markdown("<br>", unsafe_allow_html=True) 
st.sidebar.markdown("<h3 style='color:#6c5ce7; margin-top:-5px;'>Sistem Prediksi Multi-Shift</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---") 

# Menu Navigasi
menu_halaman = st.sidebar.selectbox(
    "Pilih Halaman:",
    ["Dashboard Prediksi", "Visualisasi Data", "Perbandingan Aktual vs Prediksi", "Lihat Dataset", "Input Data Histori"]
)
st.sidebar.markdown("---") 

# Sidebar Kontrol (Kecuali halaman input)
if menu_halaman != "Input Data Histori":
    st.sidebar.subheader("Pengaturan Tanggal")
    default_date = datetime.date.today()
    tanggal_pilihan = st.sidebar.date_input("Tanggal Target", default_date)

    # Auto-Fetch Cuaca Logic
    def_suhu, def_hujan = 27.0, 5.0
    
    # Ambil nilai cuaca dari histori jika ada (untuk default value)
    if df_historis is not None:
        ts_pilih = pd.to_datetime(tanggal_pilihan)
        row_now = df_historis[df_historis['Tanggal'] == ts_pilih]
        if not row_now.empty:
            if 'Suhu' in row_now.columns: def_suhu = float(row_now['Suhu'].values[0])
            if 'Curah Hujan' in row_now.columns: def_hujan = float(row_now['Curah Hujan'].values[0])

    st.sidebar.caption("Parameter Cuaca")
    input_suhu = st.sidebar.slider("Suhu (°C)", 20.0, 40.0, def_suhu, step=0.1)
    input_hujan = st.sidebar.number_input("Curah Hujan (mm)", 0.0, 150.0, def_hujan, step=0.1)
    
    st.sidebar.info("ℹ️ Nilai Omzet Pagi/Siang/Malam yang lalu (t-7 & t-30) akan diambil otomatis dari database.")

# 5. ROUTING HALAMAN
if menu_halaman == "Dashboard Prediksi":
    # Sekarang dashboard hanya butuh parameter dasar, sisanya dia urus sendiri pakai utils
    dashboard.show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan)

elif menu_halaman == "Visualisasi Data":
    visualisasi.show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan, "N/A")

elif menu_halaman == "Perbandingan Aktual vs Prediksi":
    perbandingan.show(model, df_historis)    

elif menu_halaman == "Lihat Dataset":
    dataset.show(df_historis)

elif menu_halaman == "Input Data Histori":
    input_data.show()