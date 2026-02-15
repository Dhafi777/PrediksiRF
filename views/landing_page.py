import streamlit as st

def show():
    # --- 1. ANIMASI BACKGROUND (CSS & HTML INJECTION) ---
    st.markdown("""
        <style>
        /* Mengubah background default Streamlit menjadi transparan agar animasi terlihat */
        .stApp {
            background-color: transparent !important;
        }

        /* Container untuk Background Animasi */
        .landing-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(-45deg, #009688, #34e89e, #0f3443, #34e89e);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            z-index: -1; /* Pastikan di belakang konten */
        }

        /* Keyframes untuk pergerakan warna background (Efek Gelombang) */
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Area Partikel Melayang (Efek Modern) */
        .circles {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            margin: 0;
            padding: 0;
        }

        .circles li {
            position: absolute;
            display: block;
            list-style: none;
            width: 20px;
            height: 20px;
            background: rgba(255, 255, 255, 0.2); /* Transparan putih */
            animation: animate 25s linear infinite;
            bottom: -150px; /* Mulai dari bawah layar */
            border-radius: 50%; /* Bentuk Bulat (Bubble/Molekul) */
        }

        /* Pengaturan acak untuk setiap partikel */
        .circles li:nth-child(1) { left: 25%; width: 80px; height: 80px; animation-delay: 0s; }
        .circles li:nth-child(2) { left: 10%; width: 20px; height: 20px; animation-delay: 2s; animation-duration: 12s; }
        .circles li:nth-child(3) { left: 70%; width: 20px; height: 20px; animation-delay: 4s; }
        .circles li:nth-child(4) { left: 40%; width: 60px; height: 60px; animation-delay: 0s; animation-duration: 18s; }
        .circles li:nth-child(5) { left: 65%; width: 20px; height: 20px; animation-delay: 0s; }
        .circles li:nth-child(6) { left: 75%; width: 110px; height: 110px; animation-delay: 3s; }
        .circles li:nth-child(7) { left: 35%; width: 150px; height: 150px; animation-delay: 7s; }
        .circles li:nth-child(8) { left: 50%; width: 25px; height: 25px; animation-delay: 15s; animation-duration: 45s; }
        .circles li:nth-child(9) { left: 20%; width: 15px; height: 15px; animation-delay: 2s; animation-duration: 35s; }
        .circles li:nth-child(10){ left: 85%; width: 150px; height: 150px; animation-delay: 0s; animation-duration: 11s; }

        @keyframes animate {
            0% { transform: translateY(0) rotate(0deg); opacity: 1; border-radius: 50%; }
            100% { transform: translateY(-1000px) rotate(720deg); opacity: 0; border-radius: 50%; }
        }
        
        /* Typography Colors */
        h1, h2, h3, p, li {
            color: white !important;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
        }
        
        /* Guide Card Style */
        .guide-card {
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
            color: #334155 !important; 
        }
        .guide-card h3, .guide-card p {
            color: #334155 !important;
            text-shadow: none !important;
        }

        /* Disclaimer Box Style */
        .info-box {
            background-color: rgba(0, 0, 0, 0.4);
            border-left: 5px solid #f39c12;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }
        </style>

        <div class="landing-bg">
            <ul class="circles">
                <li></li><li></li><li></li><li></li><li></li>
                <li></li><li></li><li></li><li></li><li></li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # --- 2. LOGO DI TENGAH ---
    col_kiri, col_tengah, col_kanan = st.columns([3, 2, 3])
    with col_tengah:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.warning("Logo belum diupload")

    # --- 3. HERO SECTION (JUDUL) ---
    st.markdown("""
    <div style="text-align: center; padding-top: 10px; padding-bottom: 20px;">
        <h1 style="font-size: 3.5rem; font-weight: 700;">Sistem Prediksi Omzet <br>Apotek Mitra Medical</h1>
        <p style="font-size: 1.5rem; margin-top: -10px; opacity: 0.9;">
            Solusi Cerdas Pendukung Perencanaan Apotek 
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("") 

    # --- 4. PANDUAN PENGGUNAAN ---
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'> Bagaimana Cara Kerjanya?</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="guide-card" style="padding: 20px; border-radius: 15px; height: 100%; text-align: center;">
            <div style="font-size: 3rem;">📂</div>
            <h3>1. Input Data</h3>
            <p>Unggah file Excel penjualan harian Anda untuk memperbarui data historis sistem.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="guide-card" style="padding: 20px; border-radius: 15px; height: 100%; text-align: center;">
            <div style="font-size: 3rem;">⚙️</div>
            <h3>2. Pilih Periode</h3>
            <p>Tentukan apakah Anda ingin melihat prediksi Harian, Mingguan, Bulanan, atau Tahunan.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="guide-card" style="padding: 20px; border-radius: 15px; height: 100%; text-align: center;">
            <div style="font-size: 3rem;">📊</div>
            <h3>3. Analisis</h3>
            <p>Dapatkan hasil prediksi omzet apotek untuk membantu pengambilan keputusan strategi.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # --- 5. DISCLAIMER (CENTERED) ---
    # Kita buat layout kolom agar disclaimer ada di tengah (tidak terlalu lebar)
    _, col_disc_center, _ = st.columns([1, 4, 1])
    
    with col_disc_center:
        st.markdown("""
        <div class="info-box">
            <h4 style="margin-top:0; color:white !important;"> Disclaimer</h4>
            <ul style="font-size: 0.9rem; padding-left: 20px; color: white;">
                <li>Sistem ini menggunakan metode <b>Random Forest</b> berdasarkan pola data historis penjualan sebelumnya.</li>
                <li>Hasil prediksi adalah <b>estimasi probabilitas</b>, bukan kepastian mutlak. Akurasi dapat dipengaruhi oleh anomali data atau faktor eksternal.</li>
                <li>Keputusan akhir bisnis tetap membutuhkan validasi profesional dari Apoteker/Manajemen.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.write("")
    
    # --- 6. TOMBOL MULAI ---
    _, col_btn, _ = st.columns([1, 2, 1])
    
    with col_btn:
        if st.button(" MULAI SEKARANG", type="primary", use_container_width=True):
            st.session_state['landing_page_selesai'] = True
            st.rerun()