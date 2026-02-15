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

# --- FUNGSI HELPER EXPORT ---
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

def show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan):
    st.markdown(f"## Dashboard Prediksi")
    st.write(f"Tanggal Input: **{tanggal_pilihan.strftime('%d-%m-%Y')}**")
    
    if 'hasil_prediksi' not in st.session_state:
        st.session_state['hasil_prediksi'] = None
    
    # --- PILIHAN PERIODE ---
    mode_prediksi = st.selectbox("Pilih Periode Analisis:", 
                                 ["Per Hari (Detail Shift)", 
                                  "Per Minggu (Senin - Minggu)",
                                  "Per Bulan (Tanggal 1 - Akhir Bulan)", 
                                  "Per Tahun (Januari - Desember)"])
    
    st.markdown("---")

    if st.button("Proses Prediksi", type="primary"):
        with st.spinner("Sedang memproses data..."):
            
            # --- LOGIKA PENENTUAN START DATE & DURASI ---
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
        
        # 1. DOWNLOAD EXCEL
        excel_data = to_excel(df_forecast)
        file_name_xl = f"Laporan_Prediksi_{df_forecast['Tanggal'].iloc[0].strftime('%d%b%Y')}.xlsx"
        
        with col_dl1:
            st.download_button(
                label="Unduh Excel (.xlsx)",
                data=excel_data,
                file_name=file_name_xl,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            
        st.markdown("---")
        
        # --- BAGIAN GRAFIK ---
        if "Per Hari" in mode_current:
            row = df_forecast.iloc[0]
            st.markdown(f"### Analisis Per Hari: {row['Tanggal'].strftime('%A, %d %B %Y')}")
            
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
            fig.add_trace(go.Bar(
                x=shifts, y=values, marker_color=colors,
                text=[utils.format_rupiah(v) for v in values], textposition='auto',
                hovertemplate='Shift %{x}: <b>Rp %{y:,.0f}</b><extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=shifts, y=values, mode='lines+markers', line=dict(color='gray', width=2, dash='dot'), hoverinfo='skip'
            ))
            fig.update_layout(plot_bgcolor='white', height=400, yaxis=dict(title='Rupiah (Rp)', gridcolor=COLOR_GRID), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

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
            
            # --- MENGGUNAKAN GROUPED BAR CHART ---
            fig = go.Figure()
            
            # 1. Batang Pagi
            fig.add_trace(go.Bar(
                x=df_forecast['Hari_Nama'], 
                y=df_forecast['Prediksi Pagi'], 
                name='Pagi', 
                marker_color=COLOR_PAGI,
                hovertemplate='Pagi: <b>Rp %{y:,.0f}</b><extra></extra>'
            ))
            
            # 2. Batang Siang
            fig.add_trace(go.Bar(
                x=df_forecast['Hari_Nama'], 
                y=df_forecast['Prediksi Siang'], 
                name='Siang', 
                marker_color=COLOR_SIANG,
                hovertemplate='Siang: <b>Rp %{y:,.0f}</b><extra></extra>'
            ))
            
            # 3. Batang Malam
            fig.add_trace(go.Bar(
                x=df_forecast['Hari_Nama'], 
                y=df_forecast['Prediksi Malam'], 
                name='Malam', 
                marker_color=COLOR_MALAM,
                hovertemplate='Malam: <b>Rp %{y:,.0f}</b><extra></extra>'
            ))
            
            # 4. Garis Total (Overlay)
            fig.add_trace(go.Scatter(
                x=df_forecast['Hari_Nama'], 
                y=df_forecast['Prediksi Total'], 
                mode='lines+markers', 
                name='TOTAL', 
                line=dict(color=COLOR_TOTAL, width=3, dash='dot'),
                hovertemplate='Total: <b>Rp %{y:,.0f}</b><extra></extra>'
            ))

            fig.update_layout(
                barmode='group', # Grouped Bar agar berdampingan
                hovermode="x unified", 
                plot_bgcolor='white', 
                height=450, 
                xaxis=dict(showgrid=False), 
                yaxis=dict(gridcolor=COLOR_GRID, tickprefix="Rp "), 
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Lihat Rincian Mingguan"):
                st.dataframe(df_forecast[['Hari_Nama', 'Tanggal', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({
                    'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 
                    'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"
                }), use_container_width=True)

        elif "Per Bulan" in mode_current:
            bulan_nama = df_forecast['Bulan_Nama'].iloc[0]
            tahun = df_forecast['Tahun'].iloc[0]
            st.markdown(f"### Analisis Per Bulan: {bulan_nama} {tahun}")
            
            total_sebulan = df_forecast['Prediksi Total'].sum()
            avg_harian = df_forecast['Prediksi Total'].mean()
            max_hari = df_forecast.loc[df_forecast['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Total Bulanan", utils.format_rupiah(total_sebulan), f"Bulan {bulan_nama}", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rata-rata Harian", utils.format_rupiah(avg_harian), "Mean", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Penjualan Tertinggi", f"{max_hari['Hari_Nama']}, {max_hari['Tanggal'].day}", utils.format_rupiah(max_hari['Prediksi Total']), "border-warning"), unsafe_allow_html=True)

            st.write("")
            st.markdown(f"### Tren Omzet Harian ({bulan_nama})")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_forecast['Tanggal'], y=df_forecast['Prediksi Pagi'], name='Pagi', stackgroup='one', line=dict(width=0), marker=dict(color=COLOR_PAGI)))
            fig.add_trace(go.Scatter(x=df_forecast['Tanggal'], y=df_forecast['Prediksi Siang'], name='Siang', stackgroup='one', line=dict(width=0), marker=dict(color=COLOR_SIANG)))
            fig.add_trace(go.Scatter(x=df_forecast['Tanggal'], y=df_forecast['Prediksi Malam'], name='Malam', stackgroup='one', line=dict(width=0), marker=dict(color=COLOR_MALAM)))
            fig.add_trace(go.Scatter(x=df_forecast['Tanggal'], y=df_forecast['Prediksi Total'], mode='lines', name='Total Harian', line=dict(color=COLOR_TOTAL, width=3)))

            fig.update_layout(hovermode="x unified", plot_bgcolor='white', height=500, xaxis=dict(showgrid=False, rangeslider=dict(visible=True), type="date"), yaxis=dict(gridcolor=COLOR_GRID, tickprefix="Rp "), legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Lihat Rincian Harian"):
                st.dataframe(df_forecast[['Tanggal', 'Hari_Nama', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({
                    'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 
                    'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"
                }), use_container_width=True)

        else: 
            tahun = df_forecast['Tahun'].iloc[0]
            st.markdown(f"### Analisis Per Tahun: {tahun}")
            
            df_forecast['Periode'] = df_forecast['Tahun'].astype(str) + "-" + df_forecast['Bulan'].astype(str).str.zfill(2)
            df_monthly = df_forecast.groupby(['Periode', 'Tahun', 'Bulan_Nama'], sort=False)[['Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].sum().reset_index()
            
            total_setahun = df_monthly['Prediksi Total'].sum()
            avg_bulanan = df_monthly['Prediksi Total'].mean()
            max_bulan = df_monthly.loc[df_monthly['Prediksi Total'].idxmax()]
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(utils.create_card_html("Total Tahunan", utils.format_rupiah(total_setahun), f"Jan - Des {tahun}", "border-success"), unsafe_allow_html=True)
            with c2: st.markdown(utils.create_card_html("Rata-rata Bulanan", utils.format_rupiah(avg_bulanan), "Mean", "border-primary"), unsafe_allow_html=True)
            with c3: st.markdown(utils.create_card_html("Bulan Terbaik", f"{max_bulan['Bulan_Nama']}", utils.format_rupiah(max_bulan['Prediksi Total']), "border-warning"), unsafe_allow_html=True)
            
            st.write("")
            st.markdown(f"### Akumulasi Omzet per Bulan ({tahun})")
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_monthly['Bulan_Nama'], y=df_monthly['Prediksi Total'], name='Total Omzet', marker_color=COLOR_TOTAL, text=[f"{v/1000000:.1f} Jt" for v in df_monthly['Prediksi Total']], textposition='auto', hovertemplate='%{x}: <b>Rp %{y:,.0f}</b><extra></extra>'))
            
            fig.update_layout(plot_bgcolor='white', height=450, xaxis=dict(showgrid=False), yaxis=dict(gridcolor=COLOR_GRID, title="Total Omzet (Rp)"))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Lihat Rincian Bulanan"):
                st.dataframe(df_monthly[['Bulan_Nama', 'Prediksi Pagi', 'Prediksi Siang', 'Prediksi Malam', 'Prediksi Total']].style.format({
                    'Prediksi Pagi': "Rp {:,.0f}", 'Prediksi Siang': "Rp {:,.0f}", 
                    'Prediksi Malam': "Rp {:,.0f}", 'Prediksi Total': "Rp {:,.0f}"
                }), use_container_width=True)

    else:
        st.info("Silakan pilih periode analisis dan tekan tombol **Proses Prediksi**.")