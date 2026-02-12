import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
import utils  # Import helper format_rupiah & create_card

def show(model, df_historis):
    st.markdown("## 📊 Perbandingan Aktual vs Prediksi (Multi-Shift)")
    st.write("Analisis performa model dengan membandingkan data riil dan hasil prediksi.")
    st.markdown("---")

    # Cek apakah data historis cukup dan memiliki kolom yang dibutuhkan
    if df_historis is not None and len(df_historis) > 30:
        
        # Validasi kolom wajib untuk model baru
        required_cols = ['Omzet Pagi', 'Omzet Siang', 'Omzet Malam', 'Total Omzet']
        missing = [c for c in required_cols if c not in df_historis.columns]
        
        if missing:
            st.error(f"❌ Data historis tidak kompatibel dengan model baru. Kolom hilang: {', '.join(missing)}")
            st.info("Pastikan Anda sudah mengunggah file Excel baru dengan kolom per shift (Pagi, Siang, Malam).")
            return

        # --- 1. DATA PREPARATION (SESUAIKAN DENGAN MODEL BARU) ---
        df = df_historis.copy()
        
        # Ekstrak Fitur Waktu
        df['Hari'] = df['Tanggal'].dt.day
        df['Bulan'] = df['Tanggal'].dt.month
        df['Minggu ke'] = df['Tanggal'].dt.isocalendar().week
        df['Weekend'] = (df['Tanggal'].dt.weekday >= 5).astype(int)
        
        # --- FITUR LAG (PENTING: HARUS SAMA DENGAN TRAINING) ---
        
        # 1. Lag Cuaca
        df['Hujan_t-3'] = df['Curah Hujan'].shift(3)
        df['Hujan_t-7'] = df['Curah Hujan'].shift(7)
        df['Hujan_t-14'] = df['Curah Hujan'].shift(14)
        df['Suhu_t-3'] = df['Suhu'].shift(3)
        df['Suhu_t-7'] = df['Suhu'].shift(7)

        # 2. Lag Omzet Per Shift
        shifts = ['Omzet Pagi', 'Omzet Siang', 'Omzet Malam']
        for col in shifts:
            df[f'{col}_t-7'] = df[col].shift(7)
            df[f'{col}_t-30'] = df[col].shift(30)

        # Hapus data kosong akibat shifting (30 hari pertama akan hilang)
        df_ready = df.dropna().reset_index(drop=True)

        # Daftar Fitur (Urutan HARUS SAMA PERSIS dengan Training)
        features = [
            'Hari', 'Bulan', 'Minggu ke', 'Weekend',
            'Suhu', 'Curah Hujan',
            'Hujan_t-3', 'Hujan_t-7', 'Hujan_t-14', 'Suhu_t-3', 'Suhu_t-7',
            'Omzet Pagi_t-7', 'Omzet Pagi_t-30',
            'Omzet Siang_t-7', 'Omzet Siang_t-30',
            'Omzet Malam_t-7', 'Omzet Malam_t-30'
        ]
        
        if len(df_ready) > 0:
            # Lakukan Prediksi
            X = df_ready[features]
            
            try:
                # Model memprediksi 3 kolom [Pagi, Siang, Malam]
                y_pred_raw = model.predict(X)
                
                # Kita jumlahkan ke samping untuk dapat Total Prediksi
                # y_pred_raw adalah numpy array (n_samples, 3)
                df_ready['Prediksi'] = y_pred_raw.sum(axis=1)
                
                # Hitung Selisih dengan Total Omzet Aktual
                df_ready['Selisih'] = df_ready['Total Omzet'] - df_ready['Prediksi']
                
            except Exception as e:
                st.error(f"Terjadi kesalahan saat prediksi: {e}")
                return
            
            # Kolom filter untuk UI
            df_ready['Tahun'] = df_ready['Tanggal'].dt.year
            df_ready['Bulan_Angka'] = df_ready['Tanggal'].dt.month

            # --- 2. FILTER SECTION ---
            with st.container():
                c1, c2, c3 = st.columns([2, 2, 1])
                
                list_tahun = sorted(df_ready['Tahun'].unique(), reverse=True)
                list_bulan_map = {
                    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
                    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
                }

                with c1:
                    pilih_tahun = st.selectbox("Pilih Tahun", list_tahun)
                
                with c2:
                    bulan_tersedia = sorted(df_ready[df_ready['Tahun'] == pilih_tahun]['Bulan_Angka'].unique())
                    opsi_bulan = {k: v for k, v in list_bulan_map.items() if k in bulan_tersedia}
                    if opsi_bulan:
                        pilih_bulan_nama = st.selectbox("Pilih Bulan", list(opsi_bulan.values()))
                        pilih_bulan = [k for k, v in list_bulan_map.items() if v == pilih_bulan_nama][0]
                    else:
                        st.warning("Data belum tersedia untuk tahun ini.")
                        return

                with c3:
                    st.write("") 
                    st.write("") 
                    tombol = st.button("Tampilkan 🔍", type="primary", use_container_width=True)

            if tombol:
                df_view = df_ready[(df_ready['Tahun'] == pilih_tahun) & (df_ready['Bulan_Angka'] == pilih_bulan)]

                if not df_view.empty:
                    # --- 3. KALKULASI METRIK ---
                    total_aktual = df_view['Total Omzet'].sum()
                    total_prediksi = df_view['Prediksi'].sum()
                    total_selisih = total_aktual - total_prediksi 
                    
                    # Metrik Statistik
                    mse = mean_squared_error(df_view['Total Omzet'], df_view['Prediksi'])
                    rmse = np.sqrt(mse)
                    mape = mean_absolute_percentage_error(df_view['Total Omzet'], df_view['Prediksi'])
                    r2 = r2_score(df_view['Total Omzet'], df_view['Prediksi'])
                    akurasi_persen = 100 * (1 - mape)

                    # --- 4. TAMPILAN KPI ---
                    st.markdown("### 📈 Ringkasan Performa Bulanan")
                    
                    k1, k2, k3 = st.columns(3)
                    with k1:
                        st.markdown(utils.create_card_html("Total Aktual", utils.format_rupiah(total_aktual), "Pendapatan Riil", "border-primary"), unsafe_allow_html=True)
                    with k2:
                        st.markdown(utils.create_card_html("Total Prediksi", utils.format_rupiah(total_prediksi), "Hasil Model", "border-primary"), unsafe_allow_html=True)
                    with k3:
                        persen_selisih = abs(total_selisih / total_aktual)
                        if persen_selisih < 0.05: 
                            color_selisih = "border-success"
                            ket = "✅ Sangat Akurat"
                        elif persen_selisih < 0.15: 
                            color_selisih = "border-warning"
                            ket = "⚠️ Cukup Akurat"
                        else: 
                            color_selisih = "border-danger"
                            ket = "❌ Melenceng Jauh"
                        
                        st.markdown(utils.create_card_html("Selisih Total", utils.format_rupiah(abs(total_selisih)), ket, color_selisih), unsafe_allow_html=True)

                    st.write("")

                    s1, s2, s3, s4 = st.columns(4)
                    if mape < 0.1: color_mape = "border-success" 
                    elif mape < 0.2: color_mape = "border-primary"
                    elif mape < 0.5: color_mape = "border-warning"
                    else: color_mape = "border-danger"

                    with s1: st.markdown(utils.create_card_html("Akurasi (1-MAPE)", f"{akurasi_persen:.2f}%", "Tingkat Ketepatan", color_mape), unsafe_allow_html=True)
                    with s2: st.markdown(utils.create_card_html("MAPE", f"{mape:.2%}", "Persentase Error", color_mape), unsafe_allow_html=True)
                    with s3: st.markdown(utils.create_card_html("RMSE", f"{rmse:,.0f}", "Rata-rata Deviasi (Rp)", "border-primary"), unsafe_allow_html=True)
                    with s4: st.markdown(utils.create_card_html("R² Score", f"{r2:.4f}", "Kecocokan Pola", "border-primary"), unsafe_allow_html=True)

                    st.markdown("---")

                    # --- 5. TABEL DETAIL (WARNA PADA NOMINAL SELISIH) ---
                    st.markdown("### 📋 Detail Harian")
                    
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
                    html_table += f'<tr style="background-color:#e0e7ff; font-weight:bold;"><td>TOTAL BULAN INI</td><td>{utils.format_rupiah(total_aktual)}</td><td>{utils.format_rupiah(total_prediksi)}</td><td>{utils.format_rupiah(abs(total_selisih))}</td></tr>'
                    html_table += '</tbody></table>'
                    
                    st.markdown(html_table, unsafe_allow_html=True)

                else:
                    st.warning("Data tidak ditemukan untuk periode yang dipilih.")
        else:
            st.error("Data historis tidak mencukupi untuk melakukan analisis perbandingan (kurang dari 30 hari).")
    else:
        st.warning("Silakan unggah data historis yang valid terlebih dahulu.")