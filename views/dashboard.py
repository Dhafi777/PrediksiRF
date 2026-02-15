import streamlit as st
import pandas as pd
import utils 
import matplotlib.pyplot as plt

def show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan):
    st.markdown(f"## 🔮 Dashboard Prediksi")
    st.write(f"Start Prediksi: **{tanggal_pilihan.strftime('%d-%m-%Y')}**")
    
    # --- PILIH TIPE PREDIKSI ---
    mode_prediksi = st.selectbox("Pilih Tampilan:", ["📅 Harian (Detail 30 Hari)", "🗓️ Bulanan (Rekap 12 Bulan)"])
    
    st.markdown("---")

    if st.button("Jalankan Prediksi 🚀", type="primary"):
        
        with st.spinner("Sedang melakukan forecasting..."):
            # Tentukan durasi prediksi
            if "Harian" in mode_prediksi:
                days_to_predict = 30
            else:
                days_to_predict = 365 # Setahun penuh untuk dapat data bulanan
            
            # Generate Data (Cepat karena sudah dioptimasi)
            df_forecast = utils.generate_forecast_data(model, df_historis, tanggal_pilihan, input_suhu, input_hujan, days=days_to_predict)
            
        # --- TAMPILAN 1: REKAP BULANAN (GRAFIK BATANG) ---
        if "Bulanan" in mode_prediksi:
            # Buat kolom 'Periode' untuk sorting (YYYY-MM)
            df_forecast['Periode'] = df_forecast['Tahun'].astype(str) + "-" + df_forecast['Bulan'].astype(str).str.zfill(2)
            
            # AGREGASI: Jumlahkan omzet berdasarkan Bulan & Tahun
            df_monthly = df_forecast.groupby(['Periode', 'Tahun', 'Bulan_Nama'], sort=False)[
                ['Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']
            ].sum().reset_index()
            
            # --- KPI TAHUNAN ---
            total_setahun = df_monthly['Prediksi Total'].sum()
            avg_bulanan = df_monthly['Prediksi Total'].mean()
            max_bulan = df_monthly.loc[df_monthly['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Total Omzet (12 Bulan)", utils.format_rupiah(total_setahun), "Proyeksi Tahunan", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rata-rata Bulanan", utils.format_rupiah(avg_bulanan), "Mean", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Bulan Terbaik", f"{max_bulan['Bulan_Nama']} {max_bulan['Tahun']}", utils.format_rupiah(max_bulan['Prediksi Total']), "border-warning"), unsafe_allow_html=True)
            
            st.write("")
            
            # --- GRAFIK BATANG BULANAN ---
            st.markdown("### 📊 Proyeksi Omzet per Bulan")
            st.write("Grafik ini menunjukkan total omzet akumulasi untuk setiap bulan ke depan.")
            
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Label X-Axis
            labels = df_monthly['Bulan_Nama'] + " " + df_monthly['Tahun'].astype(str)
            
            # Plot Bar Chart
            bars = ax.bar(labels, df_monthly['Prediksi Total'], color='#4361ee', width=0.6)
            
            ax.set_ylabel('Total Omzet (Rp)', fontweight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Format Y Axis
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x)).replace(',', '.')))
            
            plt.xticks(rotation=45, ha='right')
            
            # Label Angka di Atas Bar
            for bar in bars:
                height = bar.get_height()
                label_text = f'{height/1000000:.1f} Jt' 
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        label_text,
                        ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333')
            
            st.pyplot(fig)
            
            # Tabel Detail
            st.markdown("### 📋 Rincian Angka per Bulan")
            df_show = df_monthly[['Bulan_Nama', 'Tahun', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].copy()
            for c in ['Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']:
                df_show[c] = df_show[c].apply(lambda x: utils.format_rupiah(x))
            st.dataframe(df_show, use_container_width=True)

        # --- TAMPILAN 2: DETAIL HARIAN (GRAFIK GARIS/AREA) ---
        else:
            # Ambil data hari pertama
            res = df_forecast.iloc[0]
            pred_total = res['Prediksi Total']
            
            # KPI Harian
            st.markdown("### 🎯 Prediksi Harian")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(utils.create_card_html("Total Hari Ini", utils.format_rupiah(pred_total), "Estimasi", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Pagi", utils.format_rupiah(res['Prediksi Pagi']), "Shift 1", "border-warning"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Siang", utils.format_rupiah(res['Prediksi Siang']), "Shift 2", "border-warning"), unsafe_allow_html=True)
            with c4: st.markdown(utils.create_card_html("Malam", utils.format_rupiah(res['Prediksi Malam']), "Shift 3", "border-primary"), unsafe_allow_html=True)

            st.write("")
            
            # Grafik Tren Harian
            st.markdown("### 📈 Tren Harian (30 Hari ke Depan)")
            fig, ax = plt.subplots(figsize=(12, 5))
            
            ax.plot(df_forecast['Tanggal'], df_forecast['Prediksi Total'], marker='o', markersize=4, color='#4361ee', label='Total Omzet')
            
            ax.stackplot(df_forecast['Tanggal'], 
                         df_forecast['Prediksi Pagi'], 
                         df_forecast['Prediksi Siang'], 
                         df_forecast['Prediksi Malam'], 
                         labels=['Pagi', 'Siang', 'Malam'],
                         colors=['#fde047', '#fb923c', '#1e3a8a'], alpha=0.2)
            
            ax.set_ylabel('Omzet (Rupiah)')
            ax.legend(loc='upper left')
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x)).replace(',', '.')))
            
            ax.set_xticks(df_forecast['Tanggal'][::2])
            ax.set_xticklabels([d.strftime('%d/%m') for d in df_forecast['Tanggal'][::2]], rotation=45)
                
            st.pyplot(fig)
            
            # Tabel Detail Harian
            st.markdown("### 📋 Tabel Rincian Harian")
            df_table = df_forecast[['Tanggal', 'Hari_Nama', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].copy()
            df_table['Tanggal'] = df_table['Tanggal'].dt.strftime('%d-%m-%Y')
            for c in ['Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']:
                df_table[c] = df_table[c].apply(lambda x: utils.format_rupiah(x))
                
            st.dataframe(df_table, use_container_width=True)

    else:
        st.info("Silakan pilih tipe tampilan dan tekan tombol **Jalankan Prediksi**.")