import streamlit as st
import pandas as pd
import utils
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# --- KONFIGURASI WARNA ---
COLOR_PAGI  = '#f1c40f'  # Kuning
COLOR_SIANG = '#e67e22'  # Oranye
COLOR_MALAM = '#2980b9'  # Biru
COLOR_TOTAL = '#4361ee'  # Biru Utama
COLOR_SUHU  = '#ef4444'  # Merah
COLOR_HUJAN = '#10b981'  # Hijau
COLOR_GRID  = '#ecf0f1'  # Abu grid

def show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan, mape_text):
    st.markdown(f"## Visualisasi Tren & Cuaca")
    
    # --- PENJELASAN HALAMAN (DENGAN STYLE KOTAK) ---
    st.markdown("""
    <div style="background-color: #f1f5f9; border-left: 5px solid #009688; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
        <p style="margin:0; color: #334155; font-size: 1rem;">
            <b>Panduan Visualisasi:</b> Halaman ini menyajikan analisis grafis untuk membantu Anda memahami pola penjualan selama <b>30 hari ke depan</b>.
            Anda dapat melihat tren pergerakan omzet per shift, serta hubungan antara kondisi cuaca (suhu dan curah hujan) terhadap total pendapatan apotek.
        </p>
    </div>
    """, unsafe_allow_html=True)
    # -----------------------------------------------
    
    st.info(f"Proyeksi analisis dimulai dari tanggal: **{tanggal_pilihan.strftime('%d-%m-%Y')}**")
    
    st.markdown("---")

    # Generate Data (30 Hari)
    df_viz = utils.generate_30_days_data(model, df_historis, tanggal_pilihan, input_suhu, input_hujan)
    
    # Hitung Total
    total_30_hari = df_viz['Prediksi Total'].sum()
    max_day = df_viz.loc[df_viz['Prediksi Total'].idxmax()]
    
    # --- KPI SUMMARY ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(utils.create_card_html("Total Omzet (30 Hari)", utils.format_rupiah(total_30_hari), "Akumulasi Semua Shift", "border-primary"), unsafe_allow_html=True)
    with c2:
        st.markdown(utils.create_card_html("Hari Tersibuk", f"{max_day['Hari_Nama']}, {max_day['Tanggal'].strftime('%d %b')}", utils.format_rupiah(max_day['Prediksi Total']), "border-success"), unsafe_allow_html=True)

    st.write("")

    # --- GRAFIK 1: TREN PER SHIFT (INTERAKTIF) ---
    st.markdown("### Tren Omzet per Shift")
    st.caption("Grafik di bawah menunjukkan perbandingan performa penjualan antara shift Pagi, Siang, dan Malam.")
    
    fig = go.Figure()

    # Shift Pagi
    fig.add_trace(go.Scatter(
        x=df_viz['Tanggal'], y=df_viz['Prediksi Pagi'],
        mode='lines+markers', name='Pagi',
        line=dict(color=COLOR_PAGI, width=2),
        marker=dict(size=6),
        hovertemplate='Pagi: <b>Rp %{y:,.0f}</b><extra></extra>'
    ))
    
    # Shift Siang
    fig.add_trace(go.Scatter(
        x=df_viz['Tanggal'], y=df_viz['Prediksi Siang'],
        mode='lines+markers', name='Siang',
        line=dict(color=COLOR_SIANG, width=2),
        marker=dict(size=6),
        hovertemplate='Siang: <b>Rp %{y:,.0f}</b><extra></extra>'
    ))
    
    # Shift Malam
    fig.add_trace(go.Scatter(
        x=df_viz['Tanggal'], y=df_viz['Prediksi Malam'],
        mode='lines+markers', name='Malam',
        line=dict(color=COLOR_MALAM, width=2),
        marker=dict(size=6),
        hovertemplate='Malam: <b>Rp %{y:,.0f}</b><extra></extra>'
    ))

    fig.update_layout(
        plot_bgcolor='white',
        height=450,
        hovermode="x unified",
        xaxis=dict(showgrid=False, title='Tanggal'),
        yaxis=dict(title='Omzet (Rp)', gridcolor=COLOR_GRID, tickprefix="Rp "),
        legend=dict(orientation="h", y=1.1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("")
    st.markdown("---")
    
    # --- GRAFIK 2 & 3: KORELASI CUACA (INTERAKTIF DUAL AXIS) ---
    st.markdown("### Analisis Dampak Cuaca")
    st.caption("Melihat korelasi atau hubungan antara perubahan cuaca (Suhu/Hujan) dengan naik-turunnya omzet.")

    col_g1, col_g2 = st.columns(2)
    
    # KORELASI SUHU
    with col_g1:
        st.markdown("#### Total Omzet vs Suhu")
        
        # Dual Axis Chart
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])

        # Axis 1: Omzet
        fig2.add_trace(
            go.Scatter(x=df_viz['Tanggal'], y=df_viz['Prediksi Total'], name="Omzet",
                       line=dict(color=COLOR_TOTAL, width=3)),
            secondary_y=False,
        )

        # Axis 2: Suhu
        fig2.add_trace(
            go.Scatter(x=df_viz['Tanggal'], y=df_viz['Suhu'], name="Suhu (°C)",
                       line=dict(color=COLOR_SUHU, width=2, dash='dot')),
            secondary_y=True,
        )

        fig2.update_layout(
            plot_bgcolor='white',
            height=400,
            hovermode="x unified",
            showlegend=True,
            legend=dict(orientation="h", y=1.1)
        )
        
        fig2.update_yaxes(title_text="Omzet (Rp)", secondary_y=False, showgrid=False)
        fig2.update_yaxes(title_text="Suhu (°C)", secondary_y=True, showgrid=False)

        st.plotly_chart(fig2, use_container_width=True)

    # KORELASI HUJAN
    with col_g2:
        st.markdown("#### Total Omzet vs Hujan")
        
        # Dual Axis Chart
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])

        # Axis 1: Omzet
        fig3.add_trace(
            go.Scatter(x=df_viz['Tanggal'], y=df_viz['Prediksi Total'], name="Omzet",
                       line=dict(color=COLOR_TOTAL, width=3)),
            secondary_y=False,
        )

        # Axis 2: Hujan
        fig3.add_trace(
            go.Scatter(x=df_viz['Tanggal'], y=df_viz['Hujan'], name="Hujan (mm)",
                       line=dict(color=COLOR_HUJAN, width=2, dash='dot')),
            secondary_y=True,
        )

        fig3.update_layout(
            plot_bgcolor='white',
            height=400,
            hovermode="x unified",
            showlegend=True,
            legend=dict(orientation="h", y=1.1)
        )
        
        fig3.update_yaxes(title_text="Omzet (Rp)", secondary_y=False, showgrid=False)
        fig3.update_yaxes(title_text="Hujan (mm)", secondary_y=True, showgrid=False)

        st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    
    # --- FEATURE IMPORTANCE (INTERAKTIF HORIZONTAL BAR) ---
    st.markdown("### Faktor Pengaruh (Feature Importance)")
    st.markdown("""
    Grafik ini menunjukkan **variabel apa yang paling dominan** dalam menentukan hasil prediksi model.
    Semakin panjang batang grafik, semakin besar pengaruh variabel tersebut terhadap naik-turunnya omzet.
    """)
    
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
        
        # Validasi panjang array
        if len(importances) == len(feature_names):
            df_imp = pd.DataFrame({'Fitur': feature_names, 'Penting': importances})
            df_imp = df_imp.sort_values('Penting', ascending=True)
            
            # Plotly Horizontal Bar
            fig4 = go.Figure(go.Bar(
                x=df_imp['Penting'],
                y=df_imp['Fitur'],
                orientation='h',
                marker=dict(color='#4361ee', line=dict(color='#2c3e50', width=0)),
                text=[f"{val:.1%}" for val in df_imp['Penting']],
                textposition='auto'
            ))

            fig4.update_layout(
                plot_bgcolor='white',
                height=600,
                xaxis=dict(showgrid=True, gridcolor=COLOR_GRID, title="Skor Kepentingan"),
                yaxis=dict(showgrid=False),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.error(f"Mismatch Error: Model memiliki {len(importances)} fitur, tetapi daftar nama ada {len(feature_names)}.")
    else:
        st.warning("Model tidak mendukung feature importance.")