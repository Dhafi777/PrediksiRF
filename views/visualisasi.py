import streamlit as st
import pandas as pd
import numpy as np
import utils
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# --- KONFIGURASI WARNA ---
COLOR_PAGI  = '#f1c40f'
COLOR_SIANG = '#e67e22'
COLOR_MALAM = '#2980b9'
COLOR_TOTAL = '#009688'
COLOR_SUHU  = '#ef4444'
COLOR_HUJAN = '#10b981'
COLOR_GRID  = '#ecf0f1'

def get_indo_month(month_int):
    months = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
              7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
    return months.get(month_int, '')

def get_monthly_smart_insight(df_historis, target_date, col_target, col_feature, feature_name, current_val):
    """
    Analisis Cerdas: Membandingkan data bulan terpilih dengan sejarah bulan yang sama di tahun lalu.
    """
    bulan_target = target_date.month
    nama_bulan = get_indo_month(bulan_target)
    
    # 1. FILTER: Ambil hanya data di bulan yang sama dari sejarah (Misal: Semua data Januari)
    df_bulan = df_historis[df_historis['Tanggal'].dt.month == bulan_target].copy()
    
    # Fallback jika data bulan ini terlalu sedikit (< 10 hari), pakai semua data
    dataset_used = "Bulan " + nama_bulan
    if len(df_bulan) < 10:
        df_bulan = df_historis.copy()
        dataset_used = "Keseluruhan Data"

    # 2. HITUNG KORELASI (Hubungan Sebab-Akibat)
    if df_bulan[col_feature].std() == 0 or df_bulan[col_target].std() == 0:
        corr = 0 # Data konstan tidak punya korelasi
    else:
        corr = df_bulan[col_target].corr(df_bulan[col_feature])
    
    # 3. BANDINGKAN NILAI: Saat ini vs Rata-rata Historis
    avg_hist = df_bulan[col_feature].mean()
    diff = current_val - avg_hist
    
    status_nilai = "Normal"
    if diff > (avg_hist * 0.05): status_nilai = "Lebih Tinggi"
    elif diff < -(avg_hist * 0.05): status_nilai = "Lebih Rendah"
    
    # 4. RANGKAI KALIMAT ANALISIS
    penjelasan = f"Analisis Musiman ({dataset_used}):<br>"
    
    # Bagian 2: Konteks Prediksi Saat Ini

    penjelasan += f"Prediksi {feature_name} rata-rata periode ini adalah {current_val:.1f}, yang tergolong {status_nilai} dibanding rata-rata historis bulan {nama_bulan} ({avg_hist:.1f})."
    
    return penjelasan, corr

def show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan, mape_text):
    st.markdown(f"## Visualisasi Tren & Analisis Faktor")
    
    # PENJELASAN (Bahasa Akademis)
    st.markdown("""
    <div style="background-color: #f8f9fa; border-left: 5px solid #009688; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
        <p style="margin:0; color: #333; font-size: 0.95rem;">
            <b>Panduan Analisis:</b> Halaman ini menyajikan proyeksi penjualan 30 hari ke depan. 
            Sistem menggunakan metode <b>Analisis Musiman (Seasonality Analysis)</b> untuk melihat pola hubungan cuaca dan omzet spesifik pada bulan yang dipilih.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write(f"Proyeksi dimulai dari tanggal: **{tanggal_pilihan.strftime('%d-%m-%Y')}**")
    st.markdown("---")

    # Generate Data Prediksi
    df_viz = utils.generate_30_days_data(model, df_historis, tanggal_pilihan, input_suhu, input_hujan)
    
    # Hitung KPI
    total_30_hari = df_viz['Prediksi Total'].sum()
    max_day = df_viz.loc[df_viz['Prediksi Total'].idxmax()]
    avg_suhu_prediksi = df_viz['Suhu'].mean()
    avg_hujan_prediksi = df_viz['Hujan'].mean()
    
    # --- KPI SUMMARY ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(utils.create_card_html("Estimasi Total (30 Hari)", utils.format_rupiah(total_30_hari), "Akumulasi Pendapatan", "border-primary"), unsafe_allow_html=True)
    with c2:
        st.markdown(utils.create_card_html("Prediksi Puncak", f"{max_day['Hari_Nama']}, {max_day['Tanggal'].strftime('%d %b')}", utils.format_rupiah(max_day['Prediksi Total']), "border-success"), unsafe_allow_html=True)

    st.write("")

    # --- GRAFIK 1: TREN SHIFT ---
    st.subheader("1. Tren Pergerakan Omzet per Shift")
    st.caption("Visualisasi pola fluktuasi penjualan harian berdasarkan pembagian waktu operasional (Shift Pagi, Siang, Malam).")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_viz['Tanggal'], y=df_viz['Prediksi Pagi'], mode='lines+markers', name='Pagi', line=dict(color=COLOR_PAGI, width=2)))
    fig.add_trace(go.Scatter(x=df_viz['Tanggal'], y=df_viz['Prediksi Siang'], mode='lines+markers', name='Siang', line=dict(color=COLOR_SIANG, width=2)))
    fig.add_trace(go.Scatter(x=df_viz['Tanggal'], y=df_viz['Prediksi Malam'], mode='lines+markers', name='Malam', line=dict(color=COLOR_MALAM, width=2)))

    fig.update_layout(plot_bgcolor='white', height=450, hovermode="x unified", xaxis=dict(showgrid=False), yaxis=dict(title='Omzet (Rp)', gridcolor=COLOR_GRID, tickprefix="Rp "), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # --- GRAFIK 2 & 3: ANALISIS KORELASI MUSIMAN ---
    st.subheader(f"2. Analisis Dampak Klimatologi (Spesifik Bulan {get_indo_month(tanggal_pilihan.month)})")
    st.caption("Analisis ini membandingkan data prediksi saat ini dengan pola historis pada bulan yang sama di tahun-tahun sebelumnya.")

    col_g1, col_g2 = st.columns(2)
    
    # === SUHU ===
    with col_g1:
        st.markdown("#### 🌡️ Omzet vs Suhu")
        
        # Grafik Dual Axis
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_viz['Tanggal'], y=df_viz['Prediksi Total'], name="Omzet", line=dict(color=COLOR_TOTAL, width=3)), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_viz['Tanggal'], y=df_viz['Suhu'], name="Suhu (°C)", line=dict(color=COLOR_SUHU, width=2, dash='dot')), secondary_y=True)
        fig2.update_layout(plot_bgcolor='white', height=350, hovermode="x unified", legend=dict(orientation="h", y=1.1))
        fig2.update_yaxes(title_text="Omzet (Rp)", secondary_y=False, showgrid=False)
        fig2.update_yaxes(title_text="Suhu (°C)", secondary_y=True, showgrid=False)
        st.plotly_chart(fig2, use_container_width=True)
        
        # SMART INSIGHT (Monthly)
        insight_suhu, corr_suhu = get_monthly_smart_insight(df_historis, tanggal_pilihan, 'Total Omzet', 'Suhu', 'Temperatur Suhu', avg_suhu_prediksi)
        
        st.markdown(f"""
        <div style="background-color: #fff3cd; border: 1px solid #ffeeba; padding: 12px; border-radius: 5px; color: #856404; font-size: 0.9rem;">
            {insight_suhu}
        </div>
        """, unsafe_allow_html=True)

    # === HUJAN ===
    with col_g2:
        st.markdown("#### 🌧️ Omzet vs Curah Hujan")
        
        # Grafik Dual Axis
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Scatter(x=df_viz['Tanggal'], y=df_viz['Prediksi Total'], name="Omzet", line=dict(color=COLOR_TOTAL, width=3)), secondary_y=False)
        fig3.add_trace(go.Scatter(x=df_viz['Tanggal'], y=df_viz['Hujan'], name="Hujan (mm)", line=dict(color=COLOR_HUJAN, width=2, dash='dot')), secondary_y=True)
        fig3.update_layout(plot_bgcolor='white', height=350, hovermode="x unified", legend=dict(orientation="h", y=1.1))
        fig3.update_yaxes(title_text="Omzet (Rp)", secondary_y=False, showgrid=False)
        fig3.update_yaxes(title_text="Hujan (mm)", secondary_y=True, showgrid=False)
        st.plotly_chart(fig3, use_container_width=True)
        
        # SMART INSIGHT (Monthly)
        insight_hujan, corr_hujan = get_monthly_smart_insight(df_historis, tanggal_pilihan, 'Total Omzet', 'Curah Hujan', 'Curah Hujan', avg_hujan_prediksi)
        
        st.markdown(f"""
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 12px; border-radius: 5px; color: #155724; font-size: 0.9rem;">
            {insight_hujan}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- FEATURE IMPORTANCE ---
    st.subheader("3. Kontribusi Variabel (Feature Importance)")
    st.markdown("Grafik ini menunjukkan bobot kontribusi setiap variabel terhadap hasil prediksi model.")
    
    feature_names = [
        'Hari', 'Bulan', 'Minggu ke', 'Weekend',
        'Suhu', 'Curah Hujan',
        'Hujan_t-3', 'Hujan_t-7', 'Hujan_t-14', 'Suhu_t-3', 'Suhu_t-7',
        'Omzet Pagi_t-7', 'Omzet Pagi_t-30',
        'Omzet Siang_t-7', 'Omzet Siang_t-30',
        'Omzet Malam_t-7', 'Omzet Malam_t-30'
    ]
    
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        if len(importances) == len(feature_names):
            df_imp = pd.DataFrame({'Fitur': feature_names, 'Penting': importances}).sort_values('Penting', ascending=True)
            fig4 = go.Figure(go.Bar(
                x=df_imp['Penting'], y=df_imp['Fitur'], orientation='h',
                marker=dict(color='#4361ee'), text=[f"{val:.1%}" for val in df_imp['Penting']], textposition='auto'
            ))
            fig4.update_layout(plot_bgcolor='white', height=600, xaxis=dict(title="Bobot Kepentingan"), yaxis=dict(showgrid=False))
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.error("Mismatch fitur model.")
    else:
        st.warning("Feature importance tidak tersedia.")