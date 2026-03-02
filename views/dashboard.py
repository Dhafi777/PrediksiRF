import streamlit as st
import pandas as pd
import utils 
import calendar
import plotly.graph_objects as go
import plotly.express as px
import io 
import streamlit.components.v1 as components 

# --- KONFIGURASI WARNA ---
COLOR_PAGI = '#f1c40f'   
COLOR_SIANG = '#e67e22'  
COLOR_MALAM = '#2980b9'  
COLOR_TOTAL = '#009688'  
COLOR_GRID  = '#ecf0f1'  

COLOR_NAIK = '#10b981'   # Hijau
COLOR_TURUN = '#ef4444'  # Merah

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Laporan_Prediksi')
        worksheet = writer.sheets['Laporan_Prediksi']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
    processed_data = output.getvalue()
    return processed_data

# --- FUNGSI REKOMENDASI STOK OBAT ---
def get_stock_recommendation(target_month, input_hujan):
    if input_hujan > 10 or target_month in [11, 12, 1, 2]:
        return "Rekomendasi Persediaan: Penanganan Influenza", "Kondisi meteorologi menunjukkan tingkat curah hujan yang tinggi. Disarankan untuk memprioritaskan persediaan <b>Obat Flu, Antipiretik (Pereda Demam), dan Suplemen Vitamin C</b> pada area strategis etalase.", "#0ea5e9"
    elif target_month in [3, 4]:
        return "Rekomendasi Persediaan: Periode Ramadhan", "Memasuki periode bulan puasa/Ramadhan. Analisis historis menunjukkan probabilitas peningkatan permintaan untuk <b>Antasida (Obat Lambung), Pereda Panas Dalam, dan Suplemen Sahur</b>.", "#10b981"
    elif target_month in [7, 8]:
        return "Rekomendasi Persediaan: Aktivitas Sosial", "Periode ini secara historis berkaitan dengan frekuensi tinggi aktivitas sosial kemasyarakatan. Disarankan mengoptimalkan ketersediaan <b>Suplemen Multivitamin Dewasa dan Produk Perawatan Diri</b>.", "#f43f5e"
    elif target_month in [5, 6]:
        return "Rekomendasi Persediaan: Tahun Ajaran Baru", "Memasuki periode pergantian tahun ajaran sekolah. Proyeksi peningkatan permintaan terpusat pada kategori <b>Multivitamin Anak dan Perlengkapan Pertolongan Pertama (P3K)</b>.", "#8b5cf6"
    else:
        return "Rekomendasi Persediaan: Operasional Standar", "Periode observasi berada pada parameter standar. Disarankan untuk menjaga stabilitas level pengadaan <b>Obat Resep Penyakit Kronis dan Suplemen Kesehatan Harian</b>.", "#64748b"

# ==============================================================================
# FUNGSI 1: ANALISIS HARIAN
# ==============================================================================
def get_daily_smart_insight(row, input_hujan, df_historis):
    pred_total = row['Prediksi Total']
    target_date = row['Tanggal']
    
    if df_historis is not None and not df_historis.empty:
        if not pd.api.types.is_datetime64_any_dtype(df_historis['Tanggal']): 
            df_historis['Tanggal'] = pd.to_datetime(df_historis['Tanggal'])
            
    if df_historis is not None and 'Total Omzet' in df_historis.columns:
        q33 = df_historis['Total Omzet'].quantile(0.33)
        q66 = df_historis['Total Omzet'].quantile(0.66)
        avg_omzet = df_historis['Total Omzet'].mean()
    else:
        q33, q66, avg_omzet = 3000000, 6000000, 4500000 
        
    kategori = "RENDAH" if pred_total <= q33 else ("SEDANG" if pred_total <= q66 else "TINGGI")
    warna_kategori = "#ef4444" if kategori == "RENDAH" else ("#f59e0b" if kategori == "SEDANG" else "#10b981")
    status_tren = "NAIK" if pred_total > avg_omzet else "TURUN"
    
    is_weekend = target_date.weekday() >= 5
    minggu_ke = (target_date.day - 1) // 7 + 1
    
    cards_data = []
    
    if minggu_ke == 1 or minggu_ke == 5: 
        cards_data.append((f"Efek Awal Bulan (Minggu ke-{minggu_ke})", "Fase ini bertepatan dengan siklus penerimaan pendapatan reguler masyarakat. Algoritma mendeteksi potensi peningkatan rasio daya beli secara signifikan.", "#3b82f6"))
    else: 
        cards_data.append((f"Siklus Pertengahan Bulan (Minggu ke-{minggu_ke})", "Berada pada siklus pertengahan fluktuasi pendapatan bulanan. Karakteristik transaksi umumnya didominasi oleh pemenuhan resep medis rutin.", "#64748b"))

    rekom_title, rekom_desc, rekom_color = get_stock_recommendation(target_date.month, input_hujan)
    cards_data.append((rekom_title, rekom_desc, rekom_color))

    if input_hujan > 20: 
        cards_data.append((f"Faktor Meteorologi: Curah Hujan Tinggi ({input_hujan}mm)", "Tingkat curah hujan yang signifikan dapat membatasi mobilitas fisik pasien. Evaluasi menunjukkan pergeseran pada obat-obatan keluhan musim penghujan.", "#0ea5e9"))
    elif input_hujan <= 5: 
        cards_data.append((f"Faktor Meteorologi: Curah Hujan Rendah ({input_hujan}mm)", "Kondisi cuaca terdeteksi kondusif bagi optimalisasi mobilitas masyarakat, yang berkorelasi positif dengan probabilitas tingkat kunjungan fisik ke apotek.", "#eab308"))

    if df_historis is not None and not df_historis.empty:
        tgl_30_hari_lalu = target_date - pd.Timedelta(days=30)
        df_30d = df_historis[(df_historis['Tanggal'] >= tgl_30_hari_lalu) & (df_historis['Tanggal'] < target_date)]
        if len(df_30d) >= 14:
            avg_30d = df_30d['Total Omzet'].mean()
            avg_7d = df_30d.tail(7)['Total Omzet'].mean()
            if avg_7d > avg_30d * 1.05: 
                cards_data.append(("Tren Historis Berjalan (Positif)", "Data historis dalam 7 hari terakhir menunjukkan indikator pergerakan volume penjualan yang konsisten berada di atas parameter rata-rata bulanan.", "#10b981"))
            elif avg_7d < avg_30d * 0.95: 
                cards_data.append(("Tren Historis Berjalan (Negatif)", "Terdapat indikasi kontraksi tren penjualan berdasarkan analisis komparatif performa 7 hari terakhir terhadap nilai rata-rata bulanan.", "#ef4444"))

    cards_html = ""
    for title, desc, color in cards_data: 
        cards_html += f"""<div style="flex: 1 1 calc(33.333% - 15px); min-width: 220px; background: white; border: 1px solid #e2e8f0; border-top: 4px solid {color}; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);"><h5 style="margin: 0 0 8px 0; color: #1e293b; font-size: 0.95rem;">{title}</h5><p style="margin: 0; font-size: 0.85rem; color: #64748b; line-height: 1.5;">{desc}</p></div>"""
    
    return f"""<div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 6px solid {warna_kategori}; padding: 20px; border-radius: 8px; margin-top: 15px;"><h4 style="margin-top: 0; margin-bottom: 15px; color: #1e293b; display: flex; align-items: center; font-family: sans-serif;">Hasil Analisis Algoritma Prediksi</h4><div style="background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin-bottom: 20px; font-family: sans-serif;"><span style="font-size: 1.05rem; color: #334155;">Pada tanggal <b>{target_date.strftime('%d %B %Y')}</b>, indikator penjualan diproyeksikan <b>{status_tren}</b> dengan klasifikasi tingkat pendapatan:</span><span style="background-color: {warna_kategori}20; color: {warna_kategori}; font-weight: 800; padding: 6px 14px; border-radius: 20px; margin-left: 8px; font-size: 1rem; border: 1px solid {warna_kategori}50; display: inline-block; margin-top: 5px;">{kategori}</span></div><p style="font-size: 0.95rem; color: #475569; margin-bottom: 12px; font-weight: 600; font-family: sans-serif;">Faktor Determinasi Parameter dan Rekomendasi:</p><div style="display: flex; gap: 15px; flex-wrap: wrap; font-family: sans-serif;">{cards_html}</div></div>"""

# ==============================================================================
# FUNGSI 2: ANALISIS MINGGUAN
# ==============================================================================
def get_weekly_smart_insight(df_forecast, df_historis):
    pred_total = df_forecast['Prediksi Total'].sum()
    tgl_awal = df_forecast['Tanggal'].iloc[0].strftime('%d %b')
    tgl_akhir = df_forecast['Tanggal'].iloc[-1].strftime('%d %b %Y')
    target_month = df_forecast['Tanggal'].iloc[0].month
    avg_hujan = df_forecast['Hujan'].mean()
    
    if df_historis is not None and 'Total Omzet' in df_historis.columns:
        avg_omzet = df_historis['Total Omzet'].mean() * 7
        q33 = df_historis['Total Omzet'].quantile(0.33) * 7
        q66 = df_historis['Total Omzet'].quantile(0.66) * 7
    else:
        q33, q66, avg_omzet = 3000000*7, 6000000*7, 4500000*7 
        
    kategori = "RENDAH" if pred_total <= q33 else ("SEDANG" if pred_total <= q66 else "TINGGI")
    warna_kategori = "#ef4444" if kategori == "RENDAH" else ("#f59e0b" if kategori == "SEDANG" else "#10b981")
    status_tren = "MENINGKAT" if pred_total > avg_omzet else "MENURUN"
    
    cards_data = []
    
    rekom_title, rekom_desc, rekom_color = get_stock_recommendation(target_month, avg_hujan)
    cards_data.append((rekom_title, rekom_desc, rekom_color))

    payday_days = df_forecast[(df_forecast['Tanggal'].dt.day >= 25) | (df_forecast['Tanggal'].dt.day <= 5)]
    if len(payday_days) >= 4: 
        cards_data.append(("Fase Puncak Daya Beli", "Distribusi hari dalam periode observasi ini selaras dengan siklus agregat penerimaan pendapatan reguler. Diproyeksikan terjadi peningkatan aktivitas transaksi.", "#3b82f6"))
    else: 
        cards_data.append(("Siklus Operasional Normal", "Sebagian besar rentang observasi memetakan fluktuasi pertengahan bulan. Indikator transaksi diasumsikan berjalan pada rasio standar bulanan.", "#64748b"))

    best_day = df_forecast.loc[df_forecast['Prediksi Total'].idxmax()]
    cards_data.append(("Proyeksi Titik Puncak Mingguan", f"Estimasi volume kunjungan tertinggi teridentifikasi pada hari {best_day['Hari_Nama']}. Disarankan untuk mengevaluasi alokasi personel kefarmasian pada shift operasional terkait.", "#f59e0b"))

    cards_html = ""
    for title, desc, color in cards_data: 
        cards_html += f"""<div style="flex: 1 1 calc(33.333% - 15px); min-width: 220px; background: white; border: 1px solid #e2e8f0; border-top: 4px solid {color}; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);"><h5 style="margin: 0 0 8px 0; color: #1e293b; font-size: 0.95rem;">{title}</h5><p style="margin: 0; font-size: 0.85rem; color: #64748b; line-height: 1.5;">{desc}</p></div>"""
    
    return f"""<div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 6px solid {warna_kategori}; padding: 20px; border-radius: 8px; margin-top: 15px;"><h4 style="margin-top: 0; margin-bottom: 15px; color: #1e293b; display: flex; align-items: center; font-family: sans-serif;">Hasil Analisis Algoritma Prediksi (Mingguan)</h4><div style="background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin-bottom: 20px; font-family: sans-serif;"><span style="font-size: 1.05rem; color: #334155;">Pada periode observasi <b>{tgl_awal} - {tgl_akhir}</b>, tren indikator pendapatan diproyeksikan <b>{status_tren}</b> dengan parameter performa:</span><span style="background-color: {warna_kategori}20; color: {warna_kategori}; font-weight: 800; padding: 6px 14px; border-radius: 20px; margin-left: 8px; font-size: 1rem; border: 1px solid {warna_kategori}50; display: inline-block; margin-top: 5px;">{kategori}</span></div><p style="font-size: 0.95rem; color: #475569; margin-bottom: 12px; font-weight: 600; font-family: sans-serif;">Faktor Determinasi Parameter dan Rekomendasi:</p><div style="display: flex; gap: 15px; flex-wrap: wrap; font-family: sans-serif;">{cards_html}</div></div>"""

# ==============================================================================
# FUNGSI 3: ANALISIS BULANAN
# ==============================================================================
def get_monthly_smart_insight(df_forecast, df_historis):
    pred_total = df_forecast['Prediksi Total'].sum()
    bulan_nama = df_forecast['Bulan_Nama'].iloc[0]
    tahun = df_forecast['Tahun'].iloc[0]
    days_in_month = len(df_forecast)
    target_month = df_forecast['Tanggal'].iloc[0].month
    avg_hujan = df_forecast['Hujan'].mean()
    
    if df_historis is not None and 'Total Omzet' in df_historis.columns:
        avg_omzet = df_historis['Total Omzet'].mean() * days_in_month
        q33 = df_historis['Total Omzet'].quantile(0.33) * days_in_month
        q66 = df_historis['Total Omzet'].quantile(0.66) * days_in_month
    else:
        q33, q66, avg_omzet = 3000000*days_in_month, 6000000*days_in_month, 4500000*days_in_month
        
    kategori = "RENDAH" if pred_total <= q33 else ("SEDANG" if pred_total <= q66 else "TINGGI")
    warna_kategori = "#ef4444" if kategori == "RENDAH" else ("#f59e0b" if kategori == "SEDANG" else "#10b981")
    status_tren = "Naik" if pred_total > avg_omzet else "Turun"
    
    cards_data = []
    
    rekom_title, rekom_desc, rekom_color = get_stock_recommendation(target_month, avg_hujan)
    cards_data.append((rekom_title, rekom_desc, rekom_color))

    weekend_omzet = df_forecast[df_forecast['Hari_Nama'].isin(['Sabtu', 'Minggu'])]['Prediksi Total'].sum()
    pct_weekend = (weekend_omzet / pred_total) * 100 if pred_total > 0 else 0
    if pct_weekend > 35: 
        cards_data.append(("Distribusi Transaksi Akhir Pekan", f"Analisis proporsi mengindikasikan kontribusi hari akhir pekan memegang peranan signifikan ({pct_weekend:.1f}%). Formulasi strategi pemasaran khusus akhir pekan direkomendasikan.", "#8b5cf6"))
    else: 
        cards_data.append(("Distribusi Transaksi Hari Kerja", f"Aktivitas operasional apotek didominasi oleh perputaran transaksi pada hari kerja aktif, menyumbang {100-pct_weekend:.1f}% terhadap total estimasi bulan ini.", "#0ea5e9"))

    if df_historis is not None and not df_historis.empty:
        df_hist_month = df_historis[df_historis['Tanggal'].dt.month == target_month]
        if not df_hist_month.empty:
            avg_hist_month = df_hist_month['Total Omzet'].mean() * days_in_month
            if pred_total > avg_hist_month: 
                cards_data.append((f"Analisis Pola Musiman Historis (Positif)", f"Proyeksi akumulasi pendapatan menunjukkan nilai margin yang lebih superior dibandingkan nilai rata-rata historis khusus periode bulan {bulan_nama}.", "#10b981"))
            else: 
                cards_data.append((f"Analisis Pola Musiman Historis (Negatif)", f"Berdasarkan evaluasi fluktuasi masa lalu, terdeteksi indikasi pelambatan tingkat sirkulasi obat untuk periode bulan {bulan_nama} pada tahun prediksi.", "#ef4444"))

    cards_html = ""
    for title, desc, color in cards_data: 
        cards_html += f"""<div style="flex: 1 1 calc(33.333% - 15px); min-width: 220px; background: white; border: 1px solid #e2e8f0; border-top: 4px solid {color}; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);"><h5 style="margin: 0 0 8px 0; color: #1e293b; font-size: 0.95rem;">{title}</h5><p style="margin: 0; font-size: 0.85rem; color: #64748b; line-height: 1.5;">{desc}</p></div>"""
    
    return f"""<div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 6px solid {warna_kategori}; padding: 20px; border-radius: 8px; margin-top: 15px;"><h4 style="margin-top: 0; margin-bottom: 15px; color: #1e293b; display: flex; align-items: center; font-family: sans-serif;">Hasil Analisis Algoritma Prediksi (Bulanan)</h4><div style="background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin-bottom: 20px; font-family: sans-serif;"><span style="font-size: 1.05rem; color: #334155;">Pada periode bulanan <b>{bulan_nama} {tahun}</b>, tren pertumbuhan diproyeksikan <b>{status_tren}</b> dengan hasil komparasi kuartil bernilai:</span><span style="background-color: {warna_kategori}20; color: {warna_kategori}; font-weight: 800; padding: 6px 14px; border-radius: 20px; margin-left: 8px; font-size: 1rem; border: 1px solid {warna_kategori}50; display: inline-block; margin-top: 5px;">{kategori}</span></div><p style="font-size: 0.95rem; color: #475569; margin-bottom: 12px; font-weight: 600; font-family: sans-serif;">Faktor Determinasi Parameter dan Rekomendasi Manajerial:</p><div style="display: flex; gap: 15px; flex-wrap: wrap; font-family: sans-serif;">{cards_html}</div></div>"""

# ==============================================================================
# FUNGSI 4: ANALISIS TAHUNAN
# ==============================================================================
def get_yearly_smart_insight(df_monthly, tahun, df_historis):
    pred_total = df_monthly['Prediksi Total'].sum()
    
    if df_historis is not None and 'Total Omzet' in df_historis.columns:
        avg_omzet = df_historis['Total Omzet'].mean() * 365
        q33 = df_historis['Total Omzet'].quantile(0.33) * 365
        q66 = df_historis['Total Omzet'].quantile(0.66) * 365
    else:
        q33, q66, avg_omzet = 3000000*365, 6000000*365, 4500000*365
        
    kategori = "RENDAH" if pred_total <= q33 else ("SEDANG" if pred_total <= q66 else "TINGGI")
    warna_kategori = "#ef4444" if kategori == "RENDAH" else ("#f59e0b" if kategori == "SEDANG" else "#10b981")
    status_tren = "NAIK" if pred_total > avg_omzet else "TURUN"
    
    cards_data = []
    
    best_month = df_monthly.loc[df_monthly['Prediksi Total'].idxmax()]
    worst_month = df_monthly.loc[df_monthly['Prediksi Total'].idxmin()]
    
    cards_data.append(("Proyeksi Periode Fluktuasi Optimal", f"Periode <b>{best_month['Bulan_Nama']}</b> diestimasi sebagai fase pencapaian rasio penjualan puncak. Optimalisasi infrastruktur pasokan farmasi sangat dianjurkan.", "#10b981"))
    cards_data.append(("Proyeksi Periode Fluktuasi Sub-optimal", f"Periode <b>{worst_month['Bulan_Nama']}</b> teridentifikasi sebagai titik transisi dengan tren kinerja terendah. Disarankan untuk memitigasi menggunakan diversifikasi metode promosi.", "#ef4444"))
    
    pagi = df_monthly['Prediksi Pagi'].sum()
    siang = df_monthly['Prediksi Siang'].sum()
    malam = df_monthly['Prediksi Malam'].sum()
    best_shift = "Malam" if malam > pagi and malam > siang else ("Siang" if siang > pagi else "Pagi")
    cards_data.append(("Analisis Distribusi Waktu (Shift)", f"Secara komparatif tahunan, <b>Shift {best_shift}</b> memiliki rasio beban penanganan pasien tertinggi. Evaluasi pengaturan SDM pada klaster waktu tersebut dibutuhkan.", "#3b82f6"))

    cards_html = ""
    for title, desc, color in cards_data: 
        cards_html += f"""<div style="flex: 1 1 calc(33.333% - 15px); min-width: 220px; background: white; border: 1px solid #e2e8f0; border-top: 4px solid {color}; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);"><h5 style="margin: 0 0 8px 0; color: #1e293b; font-size: 0.95rem;">{title}</h5><p style="margin: 0; font-size: 0.85rem; color: #64748b; line-height: 1.5;">{desc}</p></div>"""
    
    return f"""<div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 6px solid {warna_kategori}; padding: 20px; border-radius: 8px; margin-top: 15px;"><h4 style="margin-top: 0; margin-bottom: 15px; color: #1e293b; display: flex; align-items: center; font-family: sans-serif;">Hasil Analisis Algoritma Prediksi (Tahunan)</h4><div style="background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin-bottom: 20px; font-family: sans-serif;"><span style="font-size: 1.05rem; color: #334155;">Sepanjang periode pengamatan tahun <b>{tahun}</b>, hasil agregasi estimasi mengindikasikan laju pertumbuhan yang <b>{status_tren}</b> dengan klasifikasi performa:</span><span style="background-color: {warna_kategori}20; color: {warna_kategori}; font-weight: 800; padding: 6px 14px; border-radius: 20px; margin-left: 8px; font-size: 1rem; border: 1px solid {warna_kategori}50; display: inline-block; margin-top: 5px;">{kategori}</span></div><p style="font-size: 0.95rem; color: #475569; margin-bottom: 12px; font-weight: 600; font-family: sans-serif;">Sintesis Evaluasi Makro dan Langkah Operasional:</p><div style="display: flex; gap: 15px; flex-wrap: wrap; font-family: sans-serif;">{cards_html}</div></div>"""

# ==============================================================================

def show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan):
    st.markdown(f"## Dashboard Hasil Prediksi")
    
    st.markdown("""
    <div style="background-color: #f1f5f9; border-left: 5px solid #009688; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
        <p style="margin:0; color: #334155; font-size: 1rem;">
            <b>Panduan Dashboard:</b> Halaman ini menyajikan sintesis proyeksi tingkat pendapatan berdasarkan simulasi algoritma regresi. Model visualisasi mengadopsi indikator warna untuk memfasilitasi proses penarikan kesimpulan strategis terhadap pola fluktuasi (seasonality) maupun distribusi operasional per periode spesifik.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write(f"Parameter Penentuan Waktu (Tanggal): **{tanggal_pilihan.strftime('%d-%m-%Y')}**")
    
    if 'hasil_prediksi' not in st.session_state:
        st.session_state['hasil_prediksi'] = None
    
    mode_prediksi = st.selectbox("Pilih Rentang Analisis Temporal:", 
                                 ["Per Hari (Detail Shift)", 
                                  "Per Minggu (Senin - Minggu)",
                                  "Per Bulan (Tanggal 1 - Akhir Bulan)", 
                                  "Per Tahun (Januari - Desember)"])
    
    st.markdown("---")

    if st.button("Proses Prediksi", type="primary"):
        with st.spinner("Sistem sedang mengkalkulasi dan memproses data algoritma..."):
            if "Per Hari" in mode_prediksi:
                start_date_run = pd.to_datetime(tanggal_pilihan)
                days_to_predict = 1
            elif "Per Minggu" in mode_prediksi:
                tgl_pilih = pd.to_datetime(tanggal_pilihan)
                start_date_run = tgl_pilih - pd.Timedelta(days=tgl_pilih.weekday())
                days_to_predict = 7
            elif "Per Bulan" in mode_prediksi:
                start_date_run = pd.to_datetime(tanggal_pilihan).replace(day=1)
                days_in_month = calendar.monthrange(start_date_run.year, start_date_run.month)[1]
                days_to_predict = days_in_month
            else: 
                start_date_run = pd.to_datetime(tanggal_pilihan).replace(month=1, day=1)
                days_to_predict = 366 if calendar.isleap(start_date_run.year) else 365

            df_forecast = utils.generate_forecast_data(model, df_historis, start_date_run, input_suhu, input_hujan, days=days_to_predict)
            
            st.session_state['hasil_prediksi'] = df_forecast
            st.session_state['mode_terakhir'] = mode_prediksi

    if st.session_state['hasil_prediksi'] is not None:
        df_forecast = st.session_state['hasil_prediksi']
        mode_current = st.session_state.get('mode_terakhir', mode_prediksi)
        
        st.success("Tugas Eksekusi Algoritma Selesai. Hasil pelaporan dapat diunduh pada tautan di bawah ini.")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        excel_data = to_excel(df_forecast)
        file_name_xl = f"Laporan_Prediksi_{df_forecast['Tanggal'].iloc[0].strftime('%d%b%Y')}.xlsx"
        
        with col_dl1:
            if st.button("Cetak Halaman (Termasuk Visualisasi)", use_container_width=True): 
                components.html("<script>window.print()</script>", height=0, width=0)
        
        st.markdown("---")
        
        # =========================================================
        # TAMPILAN 1: PER HARI
        # =========================================================
        if "Per Hari" in mode_current:
            row = df_forecast.iloc[0]
            st.markdown(f"### Observasi Visual Harian: {row['Tanggal'].strftime('%A, %d %B %Y')}")
            
            insight_html = get_daily_smart_insight(row, input_hujan, df_historis)
            st.markdown(insight_html, unsafe_allow_html=True)
            st.write("")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(utils.create_card_html("Akumulasi Total Pendapatan", utils.format_rupiah(row['Prediksi Total']), "Estimasi Pencapaian Penjualan", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Volume Shift Pagi", utils.format_rupiah(row['Prediksi Pagi']), "Periode Operasional 08:00 - 14:00", "border-warning"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Volume Shift Siang", utils.format_rupiah(row['Prediksi Siang']), "Periode Operasional 14:00 - 19:00", "border-warning"), unsafe_allow_html=True)
            with c4: st.markdown(utils.create_card_html("Volume Shift Malam", utils.format_rupiah(row['Prediksi Malam']), "Periode Operasional 19:00 - Selesai", "border-primary"), unsafe_allow_html=True)
            
            st.write("")
            st.markdown("### Rekapitulasi Proporsi Nilai Transaksi per Shift")
            
            shifts = ['Pagi', 'Siang', 'Malam']
            values = [row['Prediksi Pagi'], row['Prediksi Siang'], row['Prediksi Malam']]
            
            values_jt = [v / 1000000 for v in values]
            colors = [COLOR_PAGI, COLOR_SIANG, COLOR_MALAM]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=shifts, y=values_jt, marker_color=colors, 
                text=[f"Rp {v:.1f} Jt" for v in values_jt], textposition='auto', 
                hovertemplate='Waktu Transaksi (Shift) %{x}: <b>Rp %{y:.1f} Jt</b><extra></extra>'
            ))
            fig.add_trace(go.Scatter(x=shifts, y=values_jt, mode='lines+markers', line=dict(color='gray', width=2, dash='dot'), hoverinfo='skip'))
            fig.update_layout(plot_bgcolor='white', height=400, yaxis=dict(title='Skala Estimasi (Juta Rupiah)', gridcolor=COLOR_GRID), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # =========================================================
        # TAMPILAN 2: PER MINGGU
        # =========================================================
        elif "Per Minggu" in mode_current:
            tgl_awal = df_forecast['Tanggal'].iloc[0].strftime('%d %b')
            tgl_akhir = df_forecast['Tanggal'].iloc[-1].strftime('%d %b %Y')
            st.markdown(f"### Observasi Visual Mingguan: {tgl_awal} - {tgl_akhir}")
            
            insight_html = get_weekly_smart_insight(df_forecast, df_historis)
            st.markdown(insight_html, unsafe_allow_html=True)
            st.write("")
            
            total_minggu = df_forecast['Prediksi Total'].sum()
            avg_minggu = df_forecast['Prediksi Total'].mean()
            max_hari = df_forecast.loc[df_forecast['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Akumulasi Total Mingguan", utils.format_rupiah(total_minggu), "Durasi Komparasi: Senin - Minggu", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rasio Volume Transaksi Harian", utils.format_rupiah(avg_minggu), "Perhitungan Nilai Ekspektasi Historis", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Indikator Performa Optimal", f"{max_hari['Hari_Nama']}", utils.format_rupiah(max_hari['Prediksi Total']), "border-warning"), unsafe_allow_html=True)

            st.write("")
            st.markdown("### Pemetaan Puncak Fluktuasi Pendapatan Harian (Senin - Minggu)")
            
            df_forecast['Pagi_Jt'] = df_forecast['Prediksi Pagi'] / 1000000
            df_forecast['Siang_Jt'] = df_forecast['Prediksi Siang'] / 1000000
            df_forecast['Malam_Jt'] = df_forecast['Prediksi Malam'] / 1000000
            df_forecast['Total_Jt'] = df_forecast['Prediksi Total'] / 1000000

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_forecast['Hari_Nama'], y=df_forecast['Pagi_Jt'], name='Pagi', marker_color=COLOR_PAGI, hovertemplate='%{x} Pagi: <b>Rp %{y:.1f} Jt</b><extra></extra>'))
            fig.add_trace(go.Bar(x=df_forecast['Hari_Nama'], y=df_forecast['Siang_Jt'], name='Siang', marker_color=COLOR_SIANG, hovertemplate='%{x} Siang: <b>Rp %{y:.1f} Jt</b><extra></extra>'))
            fig.add_trace(go.Bar(x=df_forecast['Hari_Nama'], y=df_forecast['Malam_Jt'], name='Malam', marker_color=COLOR_MALAM, hovertemplate='%{x} Malam: <b>Rp %{y:.1f} Jt</b><extra></extra>'))
            fig.add_trace(go.Scatter(x=df_forecast['Hari_Nama'], y=df_forecast['Total_Jt'], mode='lines+markers', name='TOTAL KONTRIBUSI', line=dict(color=COLOR_TOTAL, width=3, dash='dot'), hovertemplate='%{x} Total Keseluruhan: <b>Rp %{y:.1f} Jt</b><extra></extra>'))

            fig.update_layout(barmode='group', hovermode="x unified", plot_bgcolor='white', height=450, xaxis=dict(showgrid=False), yaxis=dict(gridcolor=COLOR_GRID, title="Skala Estimasi (Juta Rupiah)", tickprefix="Rp "), legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Inspeksi Repositori Metrik Prediksi Harian"):
                st.dataframe(df_forecast[['Hari_Nama', 'Tanggal', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"}), use_container_width=True)

        # =========================================================
        # TAMPILAN 3: PER BULAN 
        # =========================================================
        elif "Per Bulan" in mode_current:
            bulan_nama = df_forecast['Bulan_Nama'].iloc[0]
            tahun = df_forecast['Tahun'].iloc[0]
            st.markdown(f"### Observasi Pola Siklus Bulanan: {bulan_nama} {tahun}")
            
            insight_html = get_monthly_smart_insight(df_forecast, df_historis)
            st.markdown(insight_html, unsafe_allow_html=True)
            st.write("")
            
            total_sebulan = df_forecast['Prediksi Total'].sum()
            avg_harian = df_forecast['Prediksi Total'].mean()
            max_hari = df_forecast.loc[df_forecast['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Akumulasi Total Bulanan", utils.format_rupiah(total_sebulan), f"Durasi Observasi: Bulan {bulan_nama}", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rasio Transaksi Ekspektasi", utils.format_rupiah(avg_harian), "Batas Toleransi Threshold Kinerja", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Titik Optimal Kunjungan", f"{max_hari['Hari_Nama']}, {max_hari['Tanggal'].day}", utils.format_rupiah(max_hari['Prediksi Total']), "border-warning"), unsafe_allow_html=True)

            st.write("")
            st.markdown(f"### Distribusi Fluktuasi Pendapatan Harian (Korelasi Kinerja)")
            
            colors_monthly = [COLOR_NAIK if val >= avg_harian else COLOR_TURUN for val in df_forecast['Prediksi Total']]
            
            df_forecast['Total_Jt'] = df_forecast['Prediksi Total'] / 1000000
            avg_harian_jt = avg_harian / 1000000
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_forecast['Tanggal'], y=df_forecast['Total_Jt'], name='Total Prediksi', marker_color=colors_monthly, hovertemplate='Tanggal: %{x|%d %b %Y}<br>Angka Estimasi: <b>Rp %{y:.1f} Jt</b><extra></extra>'))
            fig.add_hline(y=avg_harian_jt, line_dash="dash", line_color="#475569", annotation_text=f"Batas Rata-rata Ekuilibrium (Rp {avg_harian_jt:.1f} Jt)", annotation_position="top left", annotation_font=dict(color="#475569", size=11))
            
            max_omzet_jt = df_forecast['Total_Jt'].max()
            fig.update_layout(plot_bgcolor='white', height=500, xaxis=dict(showgrid=False, tickformat="%d %b", title="Indikator Tanggal"), yaxis=dict(gridcolor=COLOR_GRID, tickprefix="Rp ", title="Skala Pendapatan (Juta Rupiah)", range=[0, max_omzet_jt * 1.1]), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption("Keterangan: Batang diagram berwarna Hijau merepresentasikan margin angka di atas nilai rata-rata ekulibrium yang ditetapkan. Sebaliknya, warna Merah merepresentasikan pencapaian di bawah rata-rata berjalan.")
            
            with st.expander("Inspeksi Repositori Metrik Prediksi Harian"):
                st.dataframe(df_forecast[['Tanggal', 'Hari_Nama', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"}), use_container_width=True)

        # =========================================================
        # TAMPILAN 4: PER TAHUN
        # =========================================================
        else: 
            tahun = df_forecast['Tahun'].iloc[0]
            st.markdown(f"### Observasi Makro dan Pola Musiman (Seasonality): Tahun {tahun}")
            
            df_forecast['Periode'] = df_forecast['Tahun'].astype(str) + "-" + df_forecast['Bulan'].astype(str).str.zfill(2)
            df_monthly = df_forecast.groupby(['Periode', 'Tahun', 'Bulan_Nama', 'Bulan'], sort=False)[['Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].sum().reset_index()
            
            insight_html = get_yearly_smart_insight(df_monthly, tahun, df_historis)
            st.markdown(insight_html, unsafe_allow_html=True)
            st.write("")
            
            total_setahun = df_monthly['Prediksi Total'].sum()
            avg_bulanan = df_monthly['Prediksi Total'].mean()
            max_bulan = df_monthly.loc[df_monthly['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Akumulasi Penerimaan Tahunan", utils.format_rupiah(total_setahun), f"Durasi Rekapitulasi: Jan - Des {tahun}", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rasio Distribusi Pendapatan Bulanan", utils.format_rupiah(avg_bulanan), "Batas Toleransi Threshold Bulanan", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Indikator Performa Puncak (Peak)", f"{max_bulan['Bulan_Nama']}", utils.format_rupiah(max_bulan['Prediksi Total']), "border-warning"), unsafe_allow_html=True)
            
            st.write("")
            st.markdown(f"### 1. Visualisasi Distribusi Kinerja Bulanan (Analisis Tren Historis)")
            
            colors_yearly = [COLOR_NAIK if val >= avg_bulanan else COLOR_TURUN for val in df_monthly['Prediksi Total']]
            
            df_monthly['Total_Jt'] = df_monthly['Prediksi Total'] / 1000000
            avg_bulanan_jt = avg_bulanan / 1000000
            
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=df_monthly['Bulan_Nama'], y=df_monthly['Total_Jt'], 
                name='Total Pendapatan', marker_color=colors_yearly, 
                text=[f"{v:.1f}" for v in df_monthly['Total_Jt']], 
                textposition='auto', hovertemplate='Periode Observasi (%{x}): <b>Rp %{y:.1f} Jt</b><extra></extra>'
            ))
            
            fig1.add_hline(y=avg_bulanan_jt, line_dash="dash", line_color="#475569", annotation_text=f"Rata-rata Transaksi (Rp {avg_bulanan_jt:.1f} Jt)", annotation_position="top left", annotation_font=dict(color="#475569", size=11))
            
            fig1.update_layout(plot_bgcolor='white', height=400, xaxis=dict(showgrid=False), yaxis=dict(gridcolor=COLOR_GRID, title="Skala Pendapatan (Juta Rupiah)"), showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
            st.caption("Keterangan: Grafik berbasis warna secara visual membedakan fluktuasi kinerja bulanan yang diklasifikasikan berdasarkan ambang batas rata-rata keseluruhan (hijau mendeskripsikan kondisi memadai/optimal, merah untuk parameter penurunan atau di bawah ekuilibrium).")
            
            # ------------------------------------------------------------------
            # GRAFIK 2: HEATMAP LINTAS TAHUN
            # ------------------------------------------------------------------
            st.markdown("---")
            st.markdown(f"### 2. Heatmap")
            st.caption(f"Model matriks berikut memfasilitasi proses inspeksi visual terhadap signifikansi pergeseran pola pada variabel bulan yang sama antar beberapa tahun historis. Kategorisasi variabel **MENINGKAT/MENURUN** diterapkan pada output algoritma Prediksi ({tahun}), sedangkan pencatatan historis dipertahankan dengan luaran nilai numerik absolut.")

            bulan_map = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 
                         7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}

            heat_data = []

            # 1. Ambil Data Historis
            if df_historis is not None and not df_historis.empty and 'Total Omzet' in df_historis.columns:
                df_hist_copy = df_historis.copy()
                if not pd.api.types.is_datetime64_any_dtype(df_hist_copy['Tanggal']):
                    df_hist_copy['Tanggal'] = pd.to_datetime(df_hist_copy['Tanggal'])
                
                df_hist_copy['Tahun'] = df_hist_copy['Tanggal'].dt.year.astype(str)
                df_hist_copy['Bulan'] = df_hist_copy['Tanggal'].dt.month
                
                hist_grp = df_hist_copy.groupby(['Tahun', 'Bulan'])['Total Omzet'].sum().reset_index()
                heat_data.append(hist_grp)

            # 2. Ambil Data Prediksi
            df_pred_heat = df_monthly[['Tahun', 'Bulan', 'Prediksi Total']].copy()
            df_pred_heat.rename(columns={'Prediksi Total': 'Total Omzet'}, inplace=True)
            df_pred_heat['Tahun'] = df_pred_heat['Tahun'].astype(str) + " (Prediksi Model AI)"
            heat_data.append(df_pred_heat)

            # 3. Gabungkan Data
            if heat_data:
                df_heat_all = pd.concat(heat_data, ignore_index=True)
                
                # 4. Buat Matrix (Pivot)
                pivot_heat = df_heat_all.pivot(index='Tahun', columns='Bulan', values='Total Omzet').fillna(0)
                
                for m in range(1, 13):
                    if m not in pivot_heat.columns:
                        pivot_heat[m] = 0
                        
                pivot_heat = pivot_heat.sort_index(ascending=True)
                
                y_labels_heat = pivot_heat.index.tolist()
                x_labels_heat = [bulan_map[m] for m in range(1, 13)]
                z_data_heat_raw = pivot_heat[[m for m in range(1, 13)]].values.tolist()

                z_data_heat_jt = [[val / 1000000 for val in row] for row in z_data_heat_raw]

                all_vals_heat_jt = [val for row in z_data_heat_jt for val in row if val > 0]
                avg_month_omzet_jt = sum(all_vals_heat_jt) / len(all_vals_heat_jt) if all_vals_heat_jt else 0

                text_data_heat = []
                for i, row in enumerate(z_data_heat_jt):
                    text_row = []
                    label_tahun = str(y_labels_heat[i])
                    
                    for val in row:
                        if val == 0:
                            text_row.append("-")
                        elif label_tahun == f"{tahun} (Prediksi Model AI)":
                            if val > avg_month_omzet_jt:
                                text_row.append("NAIK")
                            else:
                                text_row.append("TURUN")
                        else:
                            text_row.append(f"{val:.1f}") 
                    text_data_heat.append(text_row)

                fig_heat = go.Figure(data=go.Heatmap(
                    z=z_data_heat_jt, 
                    x=x_labels_heat, 
                    y=y_labels_heat, 
                    colorscale='RdYlGn', 
                    zmid=avg_month_omzet_jt, 
                    hovertemplate='Identifikasi Bulan: %{x}<br>Klasifikasi Tahun: %{y}<br>Angka Evaluasi: <b>Rp %{z:.1f} Jt</b><br>Kategori Info: <b>%{text}</b><extra></extra>',
                    text=text_data_heat, 
                    texttemplate="<b>%{text}</b>",
                    textfont=dict(size=13, color="black"), 
                    colorbar=dict(title="Skala Juta (Rp)"),
                    showscale=True
                ))

                fig_heat.update_layout(
                    height=500, 
                    xaxis=dict(tickangle=-45, type='category', tickfont=dict(size=12)), 
                    yaxis=dict(
                        autorange="reversed", 
                        type='category', 
                        tickmode='array', 
                        tickvals=y_labels_heat,
                        title="Variabel Waktu",
                        tickfont=dict(size=13, weight="bold")
                    ), 
                    margin=dict(t=30, b=50, l=50, r=50)
                )
                st.plotly_chart(fig_heat, use_container_width=True)
                st.caption(f"Keterangan: Metrik nilai numerik pada visualisasi matriks di atas merupakan hasil penyesuaian konversi ke skala nominal rasionalisasi (dalam **Jutaan Rupiah / Jt**) agar menghindari potensi ambiguitas klasifikasi format internasional.")

            # ------------------------------------------------------------------
            # GRAFIK 3: MULTI-LINE CHART
            # ------------------------------------------------------------------
            st.markdown("---")
            st.markdown(f"### 3. Seasonal (Year-over-Year Analysis)")
            st.caption("Visualisasi berbasis grafik garis ini dirancang untuk mensimulasikan korelasi serta signifikansi distribusi dari fluktuasi data kronologis guna mengidentifikasi konsistensi tren indikator operasional secara siklis tahunan.")

            seasonal_data = []

            if df_historis is not None and not df_historis.empty and 'Total Omzet' in df_historis.columns:
                df_hist_copy = df_historis.copy()
                if not pd.api.types.is_datetime64_any_dtype(df_hist_copy['Tanggal']):
                    df_hist_copy['Tanggal'] = pd.to_datetime(df_hist_copy['Tanggal'])
                
                df_hist_copy['Tahun'] = df_hist_copy['Tanggal'].dt.year
                df_hist_copy['Bulan'] = df_hist_copy['Tanggal'].dt.month
                
                hist_monthly = df_hist_copy.groupby(['Tahun', 'Bulan'])['Total Omzet'].sum().reset_index()
                hist_monthly['Bulan_Nama'] = hist_monthly['Bulan'].map(bulan_map)
                hist_monthly['Kategori'] = hist_monthly['Tahun'].astype(str) + " (Sistem Aktual/Historis)"
                hist_monthly.rename(columns={'Total Omzet': 'Total_Omzet'}, inplace=True)
                
                seasonal_data.append(hist_monthly[['Bulan', 'Bulan_Nama', 'Kategori', 'Total_Omzet']])

            df_fc_monthly = df_monthly.copy()
            df_fc_monthly['Kategori'] = str(tahun) + " (Implementasi Algoritma AI)"
            df_fc_monthly['Bulan_Nama'] = df_fc_monthly['Bulan'].map(bulan_map) 
            df_fc_monthly.rename(columns={'Prediksi Total': 'Total_Omzet'}, inplace=True)
            
            seasonal_data.append(df_fc_monthly[['Bulan', 'Bulan_Nama', 'Kategori', 'Total_Omzet']])

            if seasonal_data:
                df_seasonal = pd.concat(seasonal_data, ignore_index=True)
                df_seasonal = df_seasonal.sort_values(by=['Kategori', 'Bulan'])
                
                df_seasonal['Total_Omzet_Jt'] = df_seasonal['Total_Omzet'] / 1000000

                fig_seasonal = px.line(
                    df_seasonal, x="Bulan_Nama", y="Total_Omzet_Jt", color="Kategori",
                    markers=True, custom_data=['Kategori'],
                    color_discrete_sequence=['#94a3b8', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'] 
                )

                fig_seasonal.update_layout(
                    plot_bgcolor='white', height=450,
                    xaxis=dict(showgrid=False, title="Rentang Pengamatan", categoryorder='array', categoryarray=list(bulan_map.values())),
                    yaxis=dict(gridcolor=COLOR_GRID, title="Tingkat Estimasi (Juta Rupiah)", tickprefix="Rp "),
                    legend=dict(title="Pemetaan Waktu", orientation="h", y=1.15),
                    hovermode='x unified'
                )
                
                fig_seasonal.update_traces(
                    line=dict(width=3), marker=dict(size=8),
                    hovertemplate='<b>%{customdata[0]}</b><br>Korelasi Nilai Pengamatan: Rp %{y:.1f} Jt<extra></extra>'
                )

                st.plotly_chart(fig_seasonal, use_container_width=True)
            
            with st.expander("Inspeksi Repositori Metrik Prediksi Agregat"):
                st.dataframe(df_monthly[['Bulan_Nama', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"}), use_container_width=True)

    else:
        st.info("Sistem standby. Harap tentukan spesifikasi waktu serta parameter cuaca yang relevan sebelum melakukan proses eksekusi prediksi.")