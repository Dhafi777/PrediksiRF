import streamlit as st

def show():
    # --- HERO SECTION (JUDUL BESAR) ---
    st.markdown("""
    <div style="text-align: center; padding-top: 50px; padding-bottom: 20px;">
        <h1 style="color: #4361ee; font-size: 3rem;">🏥 Sistem Forecasting Apotek</h1>
        <p style="font-size: 1.5rem; color: #64748b; margin-top: -10px;">
            Solusi Cerdas Prediksi Omzet & Perencanaan Stok Obat
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- GAMBAR ILUSTRASI (OPSIONAL) ---
    # Jika Anda punya gambar banner, bisa taruh di sini. Jika tidak, hapus saja.
    # st.image("assets/banner.png", use_column_width=True)

    st.markdown("---")

    # --- PANDUAN PENGGUNAAN (3 LANGKAH) ---
    st.markdown("<h3 style='text-align: center;'>🚀 Bagaimana Cara Kerjanya?</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 10px; border: 1px solid #cbd5e1; height: 100%; text-align: center;">
            <div style="font-size: 3rem;">📂</div>
            <h3>1. Input Data</h3>
            <p style="color: #475569;">Unggah file Excel penjualan harian Anda untuk memperbarui data historis sistem.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 10px; border: 1px solid #cbd5e1; height: 100%; text-align: center;">
            <div style="font-size: 3rem;">⚙️</div>
            <h3>2. Pilih Periode</h3>
            <p style="color: #475569;">Tentukan apakah Anda ingin melihat prediksi Harian, Mingguan, Bulanan, atau Tahunan.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 10px; border: 1px solid #cbd5e1; height: 100%; text-align: center;">
            <div style="font-size: 3rem;">📊</div>
            <h3>3. Analisis</h3>
            <p style="color: #475569;">Dapatkan hasil forecasting akurat untuk Pagi, Siang, dan Malam guna strategi stok.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.markdown("---")
    
    # --- TOMBOL MULAI (ACTION BUTTON) ---
    # Kita buat tombol besar di tengah
    _, col_btn, _ = st.columns([1, 2, 1])
    
    with col_btn:
        st.write("")
        # Callback ini akan mengubah status session menjadi 'True'
        if st.button("🚀 MULAI SEKARANG", type="primary", use_container_width=True):
            st.session_state['landing_page_selesai'] = True
            st.rerun() # Refresh halaman untuk masuk ke sistem utama