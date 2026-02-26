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

# --- FUNGSI ANALISIS CERDAS (DENGAN LAG FEATURES & SEASONALITY) ---
def get_daily_smart_insight(row, input_hujan, df_historis):
    pred_total = row['Prediksi Total']
    target_date = row['Tanggal']
    
    # Pastikan data historis ada dan tanggal format datetime
    if df_historis is not None and not df_historis.empty:
        if not pd.api.types.is_datetime64_any_dtype(df_historis['Tanggal']):
            df_historis['Tanggal'] = pd.to_datetime(df_historis['Tanggal'])
            
    if df_historis is not None and 'Total Omzet' in df_historis.columns:
        q33 = df_historis['Total Omzet'].quantile(0.33)
        q66 = df_historis['Total Omzet'].quantile(0.66)
        avg_omzet = df_historis['Total Omzet'].mean()
    else:
        q33, q66, avg_omzet = 3000000, 6000000, 4500000 
        
    kategori = ""
    warna_kategori = ""
    if pred_total <= q33:
        kategori = "RENDAH"
        warna_kategori = "#ef4444" 
    elif pred_total <= q66:
        kategori = "SEDANG"
        warna_kategori = "#f59e0b" 
    else:
        kategori = "TINGGI"
        warna_kategori = "#10b981" 
        
    status_tren = "NAIK 📈" if pred_total > avg_omzet else "TURUN 📉"
    
    # Variabel bawaan
    is_weekend = target_date.weekday() >= 5
    minggu_ke = (target_date.day - 1) // 7 + 1
    
    # LIST KARTU DINAMIS
    cards_data = []
    
    # [1] Faktor Gajian
    if minggu_ke == 1 or minggu_ke == 5:
        cards_data.append(("💰", f"Siklus Gajian (Mg ke-{minggu_ke})", "Fase awal/akhir bulan. Algoritma mendeteksi daya beli masyarakat yang lebih tinggi.", "#3b82f6"))
    else:
        cards_data.append(("📅", f"Tengah Bulan (Mg ke-{minggu_ke})", "Fase pertengahan. Transaksi didominasi obat rutin atau kebutuhan mendesak.", "#64748b"))

    # [2] Faktor Weekend
    if is_weekend:
        cards_data.append(("🏖️", "Akhir Pekan (Ya)", "Jatuh pada hari libur. Model melihat tren kunjungan naik karena waktu luang pasien.", "#8b5cf6"))
    else:
        cards_data.append(("🏢", "Hari Kerja (Tidak)", "Jatuh pada hari aktif. Pembelian umumnya dipicu mobilitas sela-sela jam kerja.", "#0ea5e9"))

    # [3] Cuaca Hari Ini
    if input_hujan > 20:
        cards_data.append(("🌧️", f"Hujan Lebat ({input_hujan}mm)", "Meskipun mobilitas fisik terhambat, terekam potensi naiknya permintaan obat flu/demam.", "#0ea5e9"))
    elif input_hujan > 5:
        cards_data.append(("🌦️", f"Hujan Sedang ({input_hujan}mm)", "Cuaca dalam batas toleransi wajar, bukan menjadi penghalang utama kunjungan.", "#f59e0b"))
    else:
        cards_data.append(("☀️", f"Cerah ({input_hujan}mm)", "Kondisi cuaca amat cerah. Sangat mendukung tingkat kunjungan maksimal ke apotek.", "#eab308"))

    # --- PENAMBAHAN FAKTOR LAG & HISTORIS ---
    if df_historis is not None and not df_historis.empty:
        
        # [4] Faktor Lag Omzet (30 Hari Terakhir)
        tgl_30_hari_lalu = target_date - pd.Timedelta(days=30)
        df_30d = df_historis[(df_historis['Tanggal'] >= tgl_30_hari_lalu) & (df_historis['Tanggal'] < target_date)]
        
        if len(df_30d) >= 14: # Syarat data cukup
            avg_30d = df_30d['Total Omzet'].mean()
            avg_7d = df_30d.tail(7)['Total Omzet'].mean() # Rata-rata seminggu terakhir
            
            if avg_7d > avg_30d * 1.05:
                cards_data.append(("📈", "Tren 30 Hari (Meningkat)", "Membawa momentum NAIK. 7 hari terakhir menunjukkan pergerakan penjualan yang lebih tinggi dari rata-rata bulanannya.", "#10b981"))
            elif avg_7d < avg_30d * 0.95:
                cards_data.append(("📉", "Tren 30 Hari (Menurun)", "Membawa momentum TURUN. Sebulan terakhir penjualan sedang melemah atau melambat.", "#ef4444"))

        # [5] Faktor Lag Cuaca (Hujan Lebat 3 Hari Lalu)
        tgl_3_hari_lalu = target_date - pd.Timedelta(days=3)
        df_3d = df_historis[df_historis['Tanggal'].dt.date == tgl_3_hari_lalu.date()]
        if not df_3d.empty and 'Curah Hujan' in df_3d.columns:
            hujan_3d_lalu = df_3d['Curah Hujan'].values[0]
            if hujan_3d_lalu > 20: # Jika 3 hari lalu hujan lebat
                cards_data.append(("☔", "Lag Cuaca (-3 Hari)", f"Tiga hari lalu sempat terjadi hujan lebat ({hujan_3d_lalu}mm). Secara historis, pasien cenderung menunda berobat dan baru datang ke apotek hari ini.", "#3b82f6"))

        # [6] Faktor Historis Bulan Tahunan
        target_month = target_date.month
        nama_bulan = target_date.strftime('%B')
        df_month = df_historis[(df_historis['Tanggal'].dt.month == target_month) & (df_historis['Tanggal'].dt.year < target_date.year)]
        
        if not df_month.empty:
            avg_month_omzet = df_month['Total Omzet'].mean()
            if avg_month_omzet > avg_omzet * 1.05:
                cards_data.append(("📆", f"Siklus {nama_bulan} (Tinggi)", f"Pola tahunan menunjukkan bahwa bulan {nama_bulan} adalah momen di mana omzet secara historis selalu lebih tinggi dari bulan lainnya.", "#10b981"))
            elif avg_month_omzet < avg_omzet * 0.95:
                cards_data.append(("📆", f"Siklus {nama_bulan} (Rendah)", f"Berdasarkan pola tahun lalu, bulan {nama_bulan} secara historis memang cenderung memiliki tingkat penjualan yang lesu/rendah.", "#ef4444"))

    # Render Cards jadi HTML (Dirapatkan agar tidak error di Streamlit)
    cards_html = ""
    for icon, title, desc, color in cards_data:
        cards_html += f"""<div style="flex: 1 1 calc(33.333% - 15px); min-width: 220px; background: white; border: 1px solid #e2e8f0; border-top: 4px solid {color}; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);"><div style="font-size: 28px; margin-bottom: 10px;">{icon}</div><h5 style="margin: 0 0 8px 0; color: #1e293b; font-size: 0.95rem;">{title}</h5><p style="margin: 0; font-size: 0.85rem; color: #64748b; line-height: 1.5;">{desc}</p></div>"""

    html_insight = f"""<div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 6px solid {warna_kategori}; padding: 20px; border-radius: 8px; margin-top: 15px;"><h4 style="margin-top: 0; margin-bottom: 15px; color: #1e293b; display: flex; align-items: center; font-family: sans-serif;"><span style="font-size: 1.4rem; margin-right: 8px;">🤖</span> Analisis Prediksi AI (Berdasarkan Fitur & Lag Dataset)</h4><div style="background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin-bottom: 20px; font-family: sans-serif;"><span style="font-size: 1.05rem; color: #334155;">Pada <b>{target_date.strftime('%d %B %Y')}</b>, tren omzet diprediksi <b>{status_tren}</b> dengan klasifikasi tingkat pendapatan:</span><span style="background-color: {warna_kategori}20; color: {warna_kategori}; font-weight: 800; padding: 6px 14px; border-radius: 20px; margin-left: 8px; font-size: 1rem; border: 1px solid {warna_kategori}50; display: inline-block; margin-top: 5px;">{kategori}</span></div><p style="font-size: 0.95rem; color: #475569; margin-bottom: 12px; font-weight: 600; font-family: sans-serif;">Faktor Penentu Algoritma & Rekam Jejak Historis:</p><div style="display: flex; gap: 15px; flex-wrap: wrap; font-family: sans-serif;">{cards_html}</div></div>"""
    return html_insight

# ==============================================================================

def show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan):
    st.markdown(f"## Dashboard Prediksi")
    
    st.markdown("""
    <div style="background-color: #f1f5f9; border-left: 5px solid #009688; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
        <p style="margin:0; color: #334155; font-size: 1rem;">
            <b>Panduan Dashboard:</b> Halaman ini menyajikan ringkasan prediksi omzet. 
            Visualisasi menggunakan skema warna dinamis (Hijau = Di atas rata-rata, Merah = Di bawah rata-rata) untuk memudahkan identifikasi tren kenaikan atau penurunan pendapatan (Seasonality).
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write(f"Tanggal Input: **{tanggal_pilihan.strftime('%d-%m-%Y')}**")
    
    if 'hasil_prediksi' not in st.session_state:
        st.session_state['hasil_prediksi'] = None
    
    mode_prediksi = st.selectbox("Pilih Periode Analisis:", 
                                 ["Per Hari (Detail Shift)", 
                                  "Per Minggu (Senin - Minggu)",
                                  "Per Bulan (Tanggal 1 - Akhir Bulan)", 
                                  "Per Tahun (Januari - Desember)"])
    
    st.markdown("---")

    if st.button("Proses Prediksi", type="primary"):
        with st.spinner("Sedang memproses data..."):
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
        
        st.success("Prediksi Selesai. Silakan unduh laporan di bawah ini.")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        excel_data = to_excel(df_forecast)
        file_name_xl = f"Laporan_Prediksi_{df_forecast['Tanggal'].iloc[0].strftime('%d%b%Y')}.xlsx"
        
        with col_dl1: st.download_button(label="Unduh Excel (.xlsx)", data=excel_data, file_name=file_name_xl, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        csv_data = df_forecast.to_csv(index=False).encode('utf-8')
        file_name_csv = f"Data_Mentah_{df_forecast['Tanggal'].iloc[0].strftime('%d%b%Y')}.csv"
        
        with col_dl2: st.download_button(label="Unduh CSV", data=csv_data, file_name=file_name_csv, mime="text/csv", use_container_width=True)
        with col_dl3:
            if st.button("Cetak PDF (Grafik)", use_container_width=True): components.html("<script>window.print()</script>", height=0, width=0)
        
        st.markdown("---")
        
        # =========================================================
        # TAMPILAN 1: PER HARI (DENGAN ANALISIS CERDAS UI CARDS)
        # =========================================================
        if "Per Hari" in mode_current:
            row = df_forecast.iloc[0]
            st.markdown(f"### Analisis Per Hari: {row['Tanggal'].strftime('%A, %d %B %Y')}")
            
            # PANGGIL FUNGSI ANALISIS CERDAS CARD (YANG SUDAH ADA LAG-NYA)
            insight_html = get_daily_smart_insight(row, input_hujan, df_historis)
            st.markdown(insight_html, unsafe_allow_html=True)
            st.write("")
            st.write("")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(utils.create_card_html("Total Omzet", utils.format_rupiah(row['Prediksi Total']), "Estimasi Hari Ini", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Shift Pagi", utils.format_rupiah(row['Prediksi Pagi']), "08:00 - 14:00", "border-warning"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Shift Siang", utils.format_rupiah(row['Prediksi Siang']), "14:00 - 19:00", "border-warning"), unsafe_allow_html=True)
            with c4: st.markdown(utils.create_card_html("Shift Malam", utils.format_rupiah(row['Prediksi Malam']), "19:00 - Tutup", "border-primary"), unsafe_allow_html=True)
            
            st.write("")
            st.markdown("### Distribusi Omzet per Shift")
            
            shifts = ['Pagi', 'Siang', 'Malam']
            values = [row['Prediksi Pagi'], row['Prediksi Siang'], row['Prediksi Malam']]
            colors = [COLOR_PAGI, COLOR_SIANG, COLOR_MALAM]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=shifts, y=values, marker_color=colors, text=[utils.format_rupiah(v) for v in values], textposition='auto', hovertemplate='Shift %{x}: <b>Rp %{y:,.0f}</b><extra></extra>'))
            fig.add_trace(go.Scatter(x=shifts, y=values, mode='lines+markers', line=dict(color='gray', width=2, dash='dot'), hoverinfo='skip'))
            fig.update_layout(plot_bgcolor='white', height=400, yaxis=dict(title='Rupiah (Rp)', gridcolor=COLOR_GRID), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # =========================================================
        # TAMPILAN 2: PER MINGGU
        # =========================================================
        elif "Per Minggu" in mode_current:
            tgl_awal = df_forecast['Tanggal'].iloc[0].strftime('%d %b')
            tgl_akhir = df_forecast['Tanggal'].iloc[-1].strftime('%d %b %Y')
            st.markdown(f"### Analisis Per Minggu: {tgl_awal} - {tgl_akhir}")
            
            total_minggu = df_forecast['Prediksi Total'].sum()
            avg_minggu = df_forecast['Prediksi Total'].mean()
            max_hari = df_forecast.loc[df_forecast['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Total Mingguan", utils.format_rupiah(total_minggu), "Senin - Minggu", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rata-rata Harian", utils.format_rupiah(avg_minggu), "Mean", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Penjualan Tertinggi", f"{max_hari['Hari_Nama']}", utils.format_rupiah(max_hari['Prediksi Total']), "border-warning"), unsafe_allow_html=True)

            st.write("")
            st.markdown("### Tren Omzet Harian (Senin - Minggu)")
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_forecast['Hari_Nama'], y=df_forecast['Prediksi Pagi'], name='Pagi', marker_color=COLOR_PAGI))
            fig.add_trace(go.Bar(x=df_forecast['Hari_Nama'], y=df_forecast['Prediksi Siang'], name='Siang', marker_color=COLOR_SIANG))
            fig.add_trace(go.Bar(x=df_forecast['Hari_Nama'], y=df_forecast['Prediksi Malam'], name='Malam', marker_color=COLOR_MALAM))
            fig.add_trace(go.Scatter(x=df_forecast['Hari_Nama'], y=df_forecast['Prediksi Total'], mode='lines+markers', name='TOTAL', line=dict(color=COLOR_TOTAL, width=3, dash='dot')))

            fig.update_layout(barmode='group', hovermode="x unified", plot_bgcolor='white', height=450, xaxis=dict(showgrid=False), yaxis=dict(gridcolor=COLOR_GRID, tickprefix="Rp "), legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Lihat Rincian Mingguan"):
                st.dataframe(df_forecast[['Hari_Nama', 'Tanggal', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"}), use_container_width=True)

        # =========================================================
        # TAMPILAN 3: PER BULAN (SEASONALITY MERAH/HIJAU)
        # =========================================================
        elif "Per Bulan" in mode_current:
            bulan_nama = df_forecast['Bulan_Nama'].iloc[0]
            tahun = df_forecast['Tahun'].iloc[0]
            st.markdown(f"### Analisis Seasonality Per Bulan: {bulan_nama} {tahun}")
            
            total_sebulan = df_forecast['Prediksi Total'].sum()
            avg_harian = df_forecast['Prediksi Total'].mean()
            max_hari = df_forecast.loc[df_forecast['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Total Bulanan", utils.format_rupiah(total_sebulan), f"Bulan {bulan_nama}", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rata-rata Harian", utils.format_rupiah(avg_harian), "Batas Threshold", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Penjualan Tertinggi", f"{max_hari['Hari_Nama']}, {max_hari['Tanggal'].day}", utils.format_rupiah(max_hari['Prediksi Total']), "border-warning"), unsafe_allow_html=True)

            st.write("")
            st.markdown(f"### Peta Kekuatan Omzet (Tren Naik/Turun)")
            
            colors_monthly = [COLOR_NAIK if val >= avg_harian else COLOR_TURUN for val in df_forecast['Prediksi Total']]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_forecast['Tanggal'], y=df_forecast['Prediksi Total'], 
                name='Omzet', marker_color=colors_monthly, 
                hovertemplate='Tanggal: %{x|%d %b %Y}<br>Total: <b>Rp %{y:,.0f}</b><extra></extra>'
            ))
            
            fig.add_hline(
                y=avg_harian, line_dash="dash", line_color="#475569", 
                annotation_text=f"Rata-rata (Rp {avg_harian:,.0f})", 
                annotation_position="top left", annotation_font=dict(color="#475569", size=11)
            )
            
            max_omzet = df_forecast['Prediksi Total'].max()
            fig.update_layout(plot_bgcolor='white', height=500, xaxis=dict(showgrid=False, tickformat="%d %b", title="Tanggal"), yaxis=dict(gridcolor=COLOR_GRID, tickprefix="Rp ", title="Total Omzet (Rp)", range=[0, max_omzet * 1.1]), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption("Keterangan: Batang 🟢 **Hijau** menunjukkan omzet di atas rata-rata bulanan. Batang 🔴 **Merah** menunjukkan omzet di bawah rata-rata bulanan.")
            
            with st.expander("Lihat Rincian Harian"):
                st.dataframe(df_forecast[['Tanggal', 'Hari_Nama', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"}), use_container_width=True)

        # =========================================================
        # TAMPILAN 4: PER TAHUN (SEASONALITY BAR & HEATMAP)
        # =========================================================
        else: 
            tahun = df_forecast['Tahun'].iloc[0]
            st.markdown(f"### Analisis Seasonality Per Tahun: {tahun}")
            
            df_forecast['Periode'] = df_forecast['Tahun'].astype(str) + "-" + df_forecast['Bulan'].astype(str).str.zfill(2)
            df_monthly = df_forecast.groupby(['Periode', 'Tahun', 'Bulan_Nama'], sort=False)[['Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].sum().reset_index()
            
            total_setahun = df_monthly['Prediksi Total'].sum()
            avg_bulanan = df_monthly['Prediksi Total'].mean()
            max_bulan = df_monthly.loc[df_monthly['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Total Tahunan", utils.format_rupiah(total_setahun), f"Jan - Des {tahun}", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rata-rata Bulanan", utils.format_rupiah(avg_bulanan), "Batas Threshold", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Bulan Terbaik", f"{max_bulan['Bulan_Nama']}", utils.format_rupiah(max_bulan['Prediksi Total']), "border-warning"), unsafe_allow_html=True)
            
            st.write("")
            st.markdown(f"### 1. Peta Kekuatan Omzet Bulanan (Tren Naik/Turun)")
            
            colors_yearly = [COLOR_NAIK if val >= avg_bulanan else COLOR_TURUN for val in df_monthly['Prediksi Total']]
            
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=df_monthly['Bulan_Nama'], y=df_monthly['Prediksi Total'], 
                name='Omzet', marker_color=colors_yearly, 
                text=[f"{v/1000000:.1f} Jt" for v in df_monthly['Prediksi Total']], 
                textposition='auto', hovertemplate='%{x}: <b>Rp %{y:,.0f}</b><extra></extra>'
            ))
            
            fig1.add_hline(
                y=avg_bulanan, line_dash="dash", line_color="#475569", 
                annotation_text=f"Rata-rata (Rp {avg_bulanan:,.0f})", 
                annotation_position="top left", annotation_font=dict(color="#475569", size=11)
            )
            
            fig1.update_layout(plot_bgcolor='white', height=400, xaxis=dict(showgrid=False), yaxis=dict(gridcolor=COLOR_GRID, title="Total Omzet (Rp)"), showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
            st.caption("Keterangan: Batang 🟢 **Hijau** menunjukkan performa bulan tersebut di atas rata-rata tahunan. Batang 🔴 **Merah** menunjukkan di bawah rata-rata tahunan.")
            
            st.markdown("---")
            st.markdown(f"### 2. Heatmap Intensitas Keramaian per Shift")
            st.caption("Grafik matriks ini mendeteksi titik puncak keramaian (hotspot). Warna yang semakin gelap/pekat menunjukkan tingginya omzet pada shift dan bulan tertentu.")

            z_data = [df_monthly['Prediksi Pagi'].tolist(), df_monthly['Prediksi Siang'].tolist(), df_monthly['Prediksi Malam'].tolist()]
            y_labels = ['Shift Pagi', 'Shift Siang', 'Shift Malam']
            x_labels = df_monthly['Bulan_Nama'].tolist()

            fig_heat = go.Figure(data=go.Heatmap(
                z=z_data, x=x_labels, y=y_labels, colorscale='YlOrRd', 
                hovertemplate='Bulan: %{x}<br>Waktu: %{y}<br>Omzet: <b>Rp %{z:,.0f}</b><extra></extra>',
                text=[[f"Rp {val/1000000:.1f} Jt" for val in row] for row in z_data], 
                texttemplate="%{text}", showscale=True
            ))

            fig_heat.update_layout(height=350, xaxis=dict(tickangle=-45), margin=dict(t=30, b=50, l=50, r=50))
            st.plotly_chart(fig_heat, use_container_width=True)
            
            with st.expander("Lihat Rincian Bulanan"):
                st.dataframe(df_monthly[['Bulan_Nama', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"}), use_container_width=True)

    else:
        st.info("Silakan pilih periode analisis dan tekan tombol **Proses Prediksi**.")