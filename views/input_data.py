import streamlit as st
import pandas as pd
import os
import time

def normalize_column_names(df):
    """
    Fungsi pintar untuk memperbaiki nama kolom secara otomatis.
    Mengubah 'suhu', 'Suhu (C)', 'temp' -> menjadi 'Suhu'
    Mengubah 'hujan', 'curah hujan', 'CH' -> menjadi 'Curah Hujan'
    """
    new_cols = []
    for col in df.columns:
        c_lower = str(col).lower().strip()
        
        # Logika Deteksi Cerdas
        if 'tanggal' in c_lower or 'date' in c_lower:
            new_cols.append('Tanggal')
        elif 'suhu' in c_lower or 'temp' in c_lower:
            new_cols.append('Suhu')
        elif 'hujan' in c_lower or 'rain' in c_lower or 'curah' in c_lower:
            new_cols.append('Curah Hujan')
        elif 'pagi' in c_lower:
            new_cols.append('Omzet Pagi')
        elif 'siang' in c_lower:
            new_cols.append('Omzet Siang')
        elif 'malam' in c_lower:
            new_cols.append('Omzet Malam')
        elif 'total' in c_lower and 'omzet' in c_lower:
            new_cols.append('Total Omzet')
        else:
            new_cols.append(col) # Biarkan apa adanya jika tidak dikenali
            
    df.columns = new_cols
    return df

def show():
    st.markdown("## 📥 Input Data Histori (Smart Detect)")
    st.write("Unggah file Excel untuk memperbarui basis data prediksi sistem.")
    
    # Kotak Informasi
    st.info("""
    **Tips:** Sistem sekarang otomatis mendeteksi kolom meskipun nama kolom Anda sedikit berbeda (misal: "suhu" kecil atau "Hujan (mm)").
    """)

    # Komponen File Uploader
    uploaded_file = st.file_uploader("Drag & Drop File Excel Anda Di Sini", type=['xlsx', 'xls', 'csv'])

    if uploaded_file is not None:
        try:
            # Baca File (Excel atau CSV)
            if uploaded_file.name.endswith('.csv'):
                df_new = pd.read_csv(uploaded_file)
            else:
                df_new = pd.read_excel(uploaded_file)
            
            # --- DEBUGGING: LIHAT APA YANG DIBACA ---
            st.write("Nama Kolom Asli dari File:", list(df_new.columns))
            
            # 1. NORMALISASI NAMA KOLOM (AUTO-FIX)
            df_new = normalize_column_names(df_new)
            
            st.write("Nama Kolom Setelah Diperbaiki:", list(df_new.columns))

            # 2. VALIDASI KOLOM WAJIB
            required_columns = [
                'Tanggal', 'Suhu', 'Curah Hujan',
                'Omzet Pagi', 'Omzet Siang', 'Omzet Malam'
            ]
            
            # Cek yang hilang
            missing_cols = [col for col in required_columns if col not in df_new.columns]

            if not missing_cols:
                # Pastikan Tanggal formatnya benar
                df_new['Tanggal'] = pd.to_datetime(df_new['Tanggal'])
                
                # Preview Data
                st.markdown("### ✅ Data Valid & Siap Disimpan")
                st.dataframe(df_new.head(), use_container_width=True)

                if st.button("Simpan Data", type="primary"):
                    # Simpan ke file standar sistem
                    save_path = 'TRAIN_80_ANGKA.xlsx'
                    df_new.to_excel(save_path, index=False)
                    
                    st.cache_resource.clear()
                    st.success("Berhasil! Data tersimpan.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error(f"❌ Masih ada kolom yang hilang: {', '.join(missing_cols)}")
                st.warning("Coba ubah nama header di Excel Anda agar lebih jelas (Contoh: 'Suhu', 'Hujan', 'Omzet Pagi').")
                
        except Exception as e:
            st.error(f"Error: {e}")