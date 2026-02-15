import streamlit as st
import pandas as pd
import datetime
import utils
from streamlit_option_menu import option_menu # Import library menu

# Import Views
from views import dashboard, visualisasi, input_data, dataset, perbandingan, landing_page

# 1. KONFIGURASI HALAMAN (Wajib Paling Atas)
st.set_page_config(
    page_title="Sistem Prediksi Apotek",
    page_icon="🏥",
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
# KONDISI 1: USER BELUM KLIK "MULAI SEKARANG" (LANDING PAGE)
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

    # --- SIDEBAR NAVIGASI MODERN ---
    with st.sidebar:
        try:
            st.image("logo.png", width=200)
        except:
            pass 
            
        st.markdown("### 🏥 Menu Utama")
        
        # --- GANTI SELECTBOX DENGAN OPTION MENU ---
        selected_menu = option_menu(
            menu_title=None,  # Judul menu (None karena sudah ada header diatas)
            options=[
                "Dashboard", 
                "Visualisasi", 
                "Perbandingan", 
                "Lihat Dataset",
                "Input Data"
            ],
            icons=[
                "speedometer2",    # Ikon Dashboard
                "graph-up-arrow",  # Ikon Visualisasi
                "scales",          # Ikon Perbandingan
                "table",           # Ikon Dataset
                "cloud-upload"     # Ikon Input
            ],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#ffffff"},
                "icon": {"color": "#009688", "font-size": "18px"}, 
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#f1f5f9",
                    "color": "#334155"
                },
                "nav-link-selected": {
                    "background-color": "#009688", # Warna Hijau Vmedis
                    "color": "white",
                    "font-weight": "600"
                },
            }
        )
        
        st.markdown("---")
        
        # Inisialisasi variabel input default
        tanggal_pilihan = datetime.date.today()
        input_suhu = 27.0
        input_hujan = 5.0
        
        # --- INPUT PARAMETER (Kecuali di halaman Input/Dataset) ---
        # Kita sesuaikan kondisi ini dengan nama menu baru
        if selected_menu not in ["Input Data", "Lihat Dataset"]:
            st.subheader("⚙️ Parameter")
            default_date = datetime.date.today()
            tanggal_pilihan = st.date_input("Tanggal Target", default_date)

            # Auto-Fetch Cuaca
            def_suhu, def_hujan = 27.0, 5.0
            if df_historis is not None:
                ts_pilih = pd.to_datetime(tanggal_pilihan)
                row_now = df_historis[df_historis['Tanggal'] == ts_pilih]
                if not row_now.empty:
                    if 'Suhu' in row_now.columns: def_suhu = float(row_now['Suhu'].values[0])
                    if 'Curah Hujan' in row_now.columns: def_hujan = float(row_now['Curah Hujan'].values[0])

            st.caption("Kondisi Cuaca (Estimasi)")
            input_suhu = st.slider("Suhu (°C)", 20.0, 40.0, def_suhu, step=0.1)
            input_hujan = st.number_input("Curah Hujan (mm)", 0.0, 150.0, def_hujan, step=0.1)
        
        st.markdown("---")
        
        # Tombol Kembali
        if st.button("🏠 Kembali ke Depan", use_container_width=True):
            st.session_state['landing_page_selesai'] = False
            st.rerun()

    # --- ROUTING KONTEN (SESUAIKAN DENGAN NAMA MENU BARU) ---
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