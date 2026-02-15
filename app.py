import streamlit as st
import pandas as pd
import datetime
import utils
from streamlit_option_menu import option_menu 

# Import Views
from views import dashboard, visualisasi, input_data, dataset, perbandingan, landing_page

# 1. KONFIGURASI HALAMAN (Wajib Paling Atas)
st.set_page_config(
    page_title="Sistem Prediksi Apotek",
    page_icon="logo.png", # Pastikan file logo.png ada di folder root
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# 2. LOAD CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass 

# 3. INITIALISASI SESSION STATE
if 'landing_page_selesai' not in st.session_state:
    st.session_state['landing_page_selesai'] = False

# =========================================================
# KONDISI 1: USER BELUM KLIK "MULAI" (LANDING PAGE)
# =========================================================
if not st.session_state['landing_page_selesai']:
    landing_page.show()

# =========================================================
# KONDISI 2: USER SUDAH KLIK "MULAI" (MASUK SISTEM UTAMA)
# =========================================================
else:
    # --- LOAD RESOURCES ---
    model, df_historis = utils.load_resources()

    if model is None:
        st.error("Error: File model 'model_skripsi_multishift.pkl' tidak ditemukan!")
        st.stop()

    # --- SIDEBAR NAVIGASI ---

    
    with st.sidebar:

        st.markdown("<h3 style='text-align: left; color: #333;'>Menu Utama</h3>", unsafe_allow_html=True)
        # Menampilkan Logo (Layout 3 kolom agar logo di tengah)
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            try:
                st.image("logo.png", width=100) 
            except:
                pass
            
        
        
        selected_menu = option_menu(
            menu_title=None, 
            options=[
                "Dashboard", 
                "Visualisasi", 
                "Perbandingan", 
                "Lihat Dataset",
                "Input Data"
            ],
            icons=[
                "speedometer2",    
                "graph-up-arrow",  
                "graph-up-arrow",          
                "table",           
                "cloud-upload"     
            ],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#ffffff"},
                "icon": {"color": "#009688", "font-size": "16px"}, 
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#f1f5f9",
                    "color": "#334155"
                },
                "nav-link-selected": {
                    "background-color": "#009688", 
                    "color": "white",
                    "font-weight": "600"
                },
            }
        )
        
        st.markdown("---")
        
        # Inisialisasi variabel default
        tanggal_pilihan = datetime.date.today()
        input_suhu = 27.0
        input_hujan = 5.0
        
        # --- INPUT PARAMETER (Hanya di menu tertentu) ---
        if selected_menu not in ["Input Data", "Lihat Dataset"]:
            st.subheader("Parameter Input")
            
            # Input Tanggal
            default_date = datetime.date.today()
            tanggal_pilihan = st.date_input("Pilih Tanggal Target", default_date)

            # --- LOGIKA OTOMATIS CUACA ---
            data_tersedia = False
            real_suhu = 0.0
            real_hujan = 0.0
            
            # Cek database
            if df_historis is not None:
                ts_pilih = pd.to_datetime(tanggal_pilihan)
                
                # Normalisasi tipe data tanggal agar sinkron
                if not pd.api.types.is_datetime64_any_dtype(df_historis['Tanggal']):
                     df_historis['Tanggal'] = pd.to_datetime(df_historis['Tanggal'])
                
                # Filter data
                row_now = df_historis[df_historis['Tanggal'] == ts_pilih]
                
                if not row_now.empty:
                    data_tersedia = True
                    if 'Suhu' in row_now.columns: real_suhu = float(row_now['Suhu'].values[0])
                    if 'Curah Hujan' in row_now.columns: real_hujan = float(row_now['Curah Hujan'].values[0])
            
            # --- TAMPILAN KONDISIONAL (FORMAL) ---
            if data_tersedia:
                # Kondisi A: Data Ada -> Tampilkan Input Read-Only (Rapi & Formal)
                st.info("Data klimatologi tersedia di database.")
                
                # Menggunakan text_input disabled agar ukurannya wajar
                col_suhu, col_hujan = st.columns(2)
                with col_suhu:
                    st.text_input("Suhu (°C)", value=f"{real_suhu}", disabled=True)
                with col_hujan:
                    st.text_input("Curah Hujan (mm)", value=f"{real_hujan}", disabled=True)
                
                # Set nilai variabel
                input_suhu = real_suhu
                input_hujan = real_hujan
                
            else:
                # Kondisi B: Data Tidak Ada -> Input Manual (Pakai Number Input Semua)
                st.warning("Data klimatologi belum tersedia.")
                st.caption("Silakan masukkan estimasi secara manual.")
                
                # GANTI SLIDER JADI NUMBER INPUT
                input_suhu = st.number_input("Estimasi Suhu (°C)", min_value=20.0, max_value=40.0, value=27.0, step=0.1)
                input_hujan = st.number_input("Estimasi Curah Hujan (mm)", min_value=0.0, max_value=150.0, value=5.0, step=0.1)
        
        st.markdown("---")
        
        # Tombol Kembali (Bahasa Baku)
        if st.button("Kembali ke Beranda", use_container_width=True):
            st.session_state['landing_page_selesai'] = False
            st.rerun()

    # --- ROUTING KONTEN ---
    if selected_menu == "Dashboard":
        dashboard.show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan)

    elif selected_menu == "Visualisasi":
        visualisasi.show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan, "N/A")

    elif selected_menu == "Perbandingan":
        perbandingan.show(model, df_historis)    

    elif selected_menu == "Lihat Dataset":
        dataset.show(df_historis)

    elif selected_menu == "Input Data":
        input_data.show()