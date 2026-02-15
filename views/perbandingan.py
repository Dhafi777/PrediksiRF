import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
import utils  # Import helper format_rupiah & create_card

def show(model, df_historis):
    st.markdown("##  Komparasi Data Aktual banding Prediksi")
    st.write("Halaman ini menyajikan evaluasi kinerja model prediksi dengan membandingkan data penjualan aktual terhadap hasil estimasi model Random Forest.")
    st.markdown("---")

    # Cek ketersediaan dan validitas data historis
    if df_historis is not None and len(df_historis) > 30:
        
        # Validasi kolom wajib untuk model multi-shift
        required_cols = ['Omzet Pagi', 'Omzet Siang', 'Omzet Malam', 'Total Omzet']
        missing = [c for c in required_cols if c not in df_historis.columns]
        
        if missing:
            st.error(f" Struktur data tidak kompatibel. Atribut berikut tidak ditemukan: {', '.join(missing)}")
            st.info("Mohon pastikan berkas data yang diunggah memuat informasi omzet per shift (Pagi, Siang, Malam).")
            return

        # --- 1. PREPARASI DATA ---
        df = df_historis.copy()
        
        # Ekstraksi Fitur Waktu
        df['Hari'] = df['Tanggal'].dt.day
        df['Bulan'] = df['Tanggal'].dt.month
        df['Minggu ke'] = df['Tanggal'].dt.isocalendar().week
        df['Weekend'] = (df['Tanggal'].dt.weekday >= 5).astype(int)
        
        # --- KONSTRUKSI FITUR LAG (Sesuai Konfigurasi Pelatihan Model) ---
        
        # 1. Lag Variabel Cuaca
        df['Hujan_t-3'] = df['Curah Hujan'].shift(3)
        df['Hujan_t-7'] = df['Curah Hujan'].shift(7)
        df['Hujan_t-14'] = df['Curah Hujan'].shift(14)
        df['Suhu_t-3'] = df['Suhu'].shift(3)
        df['Suhu_t-7'] = df['Suhu'].shift(7)

        # 2. Lag Variabel Omzet Per Shift
        shifts = ['Omzet Pagi', 'Omzet Siang', 'Omzet Malam']
        for col in shifts:
            df[f'{col}_t-7'] = df[col].shift(7)
            df[f'{col}_t-30'] = df[col].shift(30)

        # Eliminasi data dengan nilai null akibat proses shifting
        df_ready = df.dropna().reset_index(drop=True)

        # Definisi Fitur Input (Urutan harus konsisten dengan model latih)
        features = [
            'Hari', 'Bulan', 'Minggu ke', 'Weekend',
            'Suhu', 'Curah Hujan',
            'Hujan_t-3', 'Hujan_t-7', 'Hujan_t-14', 'Suhu_t-3', 'Suhu_t-7',
            'Omzet Pagi_t-7', 'Omzet Pagi_t-30',
            'Omzet Siang_t-7', 'Omzet Siang_t-30',
            'Omzet Malam_t-7', 'Omzet Malam_t-30'
        ]
        
        if len(df_ready) > 0:
            # Eksekusi Prediksi
            X = df_ready[features]
            
            try:
                # Prediksi Multi-Output [Pagi, Siang, Malam]
                y_pred_raw = model.predict(X)
                
                # Agregasi Prediksi Total
                df_ready['Prediksi'] = y_pred_raw.sum(axis=1)
                
                # Kalkulasi Deviasi (Residu)
                df_ready['Selisih'] = df_ready['Total Omzet'] - df_ready['Prediksi']
                
            except Exception as e:
                st.error(f"Terjadi kesalahan komputasi prediksi: {e}")
                return
            
            # Atribut Filter
            df_ready['Tahun'] = df_ready['Tanggal'].dt.year
            df_ready['Bulan_Angka'] = df_ready['Tanggal'].dt.month

            # --- 2. PANEL FILTER DATA ---
            with st.container():
                c1, c2, c3 = st.columns([2, 2, 1])
                
                list_tahun = sorted(df_ready['Tahun'].unique(), reverse=True)
                list_bulan_map = {
                    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
                    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
                }

                with c1:
                    pilih_tahun = st.selectbox("Pilih Tahun Evaluasi", list_tahun)
                
                with c2:
                    bulan_tersedia = sorted(df_ready[df_ready['Tahun'] == pilih_tahun]['Bulan_Angka'].unique())
                    opsi_bulan = {k: v for k, v in list_bulan_map.items() if k in bulan_tersedia}
                    if opsi_bulan:
                        pilih_bulan_nama = st.selectbox("Pilih Bulan Evaluasi", list(opsi_bulan.values()))
                        pilih_bulan = [k for k, v in list_bulan_map.items() if v == pilih_bulan_nama][0]
                    else:
                        st.warning("Data tidak tersedia untuk periode tahun terpilih.")
                        return

                with c3:
                    st.write("") 
                    st.write("") 
                    tombol = st.button("Tampilkan Analisis ", type="primary", use_container_width=True)

            if tombol:
                df_view = df_ready[(df_ready['Tahun'] == pilih_tahun) & (df_ready['Bulan_Angka'] == pilih_bulan)]

                if not df_view.empty:
                    # --- 3. KALKULASI METRIK EVALUASI ---
                    total_aktual = df_view['Total Omzet'].sum()
                    total_prediksi = df_view['Prediksi'].sum()
                    total_selisih = total_aktual - total_prediksi 
                    
                    # Metrik Statistik
                    mse = mean_squared_error(df_view['Total Omzet'], df_view['Prediksi'])
                    rmse = np.sqrt(mse)
                    mape = mean_absolute_percentage_error(df_view['Total Omzet'], df_view['Prediksi'])
                    r2 = r2_score(df_view['Total Omzet'], df_view['Prediksi'])
                    akurasi_persen = 100 * (1 - mape)

                    # --- 4. VISUALISASI KPI ---
                    st.markdown("###  Ringkasan Performa Bulanan")
                    
                    k1, k2, k3 = st.columns(3)
                    with k1:
                        st.markdown(utils.create_card_html("Total Pendapatan Riil", utils.format_rupiah(total_aktual), "Data Aktual", "border-primary"), unsafe_allow_html=True)
                    with k2:
                        st.markdown(utils.create_card_html("Total Estimasi Model", utils.format_rupiah(total_prediksi), "Hasil Prediksi", "border-primary"), unsafe_allow_html=True)
                    with k3:
                        persen_selisih = abs(total_selisih / total_aktual)
                        if persen_selisih < 0.05: 
                            color_selisih = "border-success"
                            ket = " Akurasi Tinggi"
                        elif persen_selisih < 0.15: 
                            color_selisih = "border-warning"
                            ket = " Akurasi Sedang"
                        else: 
                            color_selisih = "border-danger"
                            ket = " Deviasi Signifikan"
                        
                        st.markdown(utils.create_card_html("Deviasi Total", utils.format_rupiah(abs(total_selisih)), ket, color_selisih), unsafe_allow_html=True)

                    st.write("")

                    s1, s2, s3, s4 = st.columns(4)
                    if mape < 0.1: color_mape = "border-success" 
                    elif mape < 0.2: color_mape = "border-primary"
                    elif mape < 0.5: color_mape = "border-warning"
                    else: color_mape = "border-danger"

                    with s1: st.markdown(utils.create_card_html("Tingkat Akurasi", f"{akurasi_persen:.2f}%", "1 - MAPE", color_mape), unsafe_allow_html=True)
                    with s2: st.markdown(utils.create_card_html("MAPE", f"{mape:.2%}", "Mean Abs. % Error", color_mape), unsafe_allow_html=True)
                    with s3: st.markdown(utils.create_card_html("RMSE", f"{rmse:,.0f}", "Root Mean Sq. Error (Rp)", "border-primary"), unsafe_allow_html=True)
                    with s4: st.markdown(utils.create_card_html("Koefisien Determinasi (R²)", f"{r2:.4f}", "Goodness of Fit", "border-primary"), unsafe_allow_html=True)

                    st.markdown("---")
                    
                    # --- [NEW] BAGIAN EDUKASI METRIK (BAHASA BAKU) ---
                    with st.expander(" Interpretasi Metrik Evaluasi Model (Klik untuk detail)"):
                        st.markdown("""
                        **Penjelasan Indikator Kinerja Model:**
                        
                        1.  **Tingkat Akurasi (1 - MAPE):** * Merepresentasikan persentase ketepatan model dalam mengestimasi nilai target secara keseluruhan.
                            * Nilai yang mendekati **100%** mengindikasikan kinerja model yang sangat baik.
                        
                        2.  **MAPE (Mean Absolute Percentage Error):**
                            * Rata-rata persentase kesalahan absolut antara nilai prediksi dan nilai aktual.
                            * Semakin kecil nilai MAPE, semakin tinggi akurasi model. Contoh: MAPE **5%** berarti rata-rata deviasi prediksi adalah 5% dari nilai sebenarnya.
                        
                        3.  **RMSE (Root Mean Squared Error):**
                            * Akar kuadrat dari rata-rata kesalahan kuadrat. Metrik ini mengukur besarnya tingkat kesalahan prediksi dalam satuan nilai asli (Rupiah).
                            * RMSE memberikan bobot lebih pada kesalahan yang besar (outliers).
                        
                        4.  **Koefisien Determinasi (R² Score):**
                            * Indikator statistik yang mengukur proporsi variabilitas dalam data dependen yang dapat dijelaskan oleh model regresi.
                            * Nilai **1.0** menunjukkan model sempurna memprediksi data, sedangkan nilai **0.0** menunjukkan model tidak lebih baik dari sekadar memprediksi nilai rata-rata.
                        """)
                    
                    st.write("")

                    # --- 5. TABEL DETAIL (WARNA PADA NOMINAL SELISIH) ---
                    st.markdown("###  Rincian Data Harian")
                    
                    tabel_show = df_view[['Tanggal', 'Total Omzet', 'Prediksi', 'Selisih']].copy()
                    tabel_show['Tanggal'] = tabel_show['Tanggal'].dt.strftime('%d-%m-%Y')
                    
                    # Render Tabel HTML
                    html_table = '<table class="styled-table" style="width:100%">'
                    html_table += '<thead><tr><th>Tanggal</th><th>Aktual (Rp)</th><th>Prediksi (Rp)</th><th>Selisih (Rp)</th></tr></thead>'
                    html_table += '<tbody>'
                    
                    for index, row in tabel_show.iterrows():
                        selisih = row['Selisih']
                        aktual = row['Total Omzet']
                        
                        val_aktual = utils.format_rupiah(aktual)
                        val_pred = utils.format_rupiah(row['Prediksi'])
                        val_selisih_num = utils.format_rupiah(abs(selisih)) 
                        
                        # LOGIKA WARNA TEKS
                        err_rate = abs(selisih) / aktual if aktual != 0 else 1
                        
                        if err_rate < 0.2: 
                            color_style = "color: #166534; font-weight: bold;" # Hijau
                        else:
                            color_style = "color: #991b1b; font-weight: bold;" # Merah
                            
                        tanda = "+" if selisih >= 0 else "-"
                        
                        html_table += f"<tr><td>{row['Tanggal']}</td><td>{val_aktual}</td><td>{val_pred}</td><td style='{color_style}'>{tanda} {val_selisih_num}</td></tr>"
                    
                    # Footer Total
                    html_table += f'<tr style="background-color:#e0e7ff; font-weight:bold;"><td>TOTAL PERIODE INI</td><td>{utils.format_rupiah(total_aktual)}</td><td>{utils.format_rupiah(total_prediksi)}</td><td>{utils.format_rupiah(abs(total_selisih))}</td></tr>'
                    html_table += '</tbody></table>'
                    
                    st.markdown(html_table, unsafe_allow_html=True)

                else:
                    st.warning("Data tidak ditemukan untuk periode bulan yang dipilih.")
        else:
            st.error("Volume data historis tidak memadai untuk melakukan analisis komparatif (kurang dari 30 entri data).")
    else:
        st.warning("Silakan unggah data historis yang valid terlebih dahulu untuk memulai analisis.")