import streamlit as st
import pandas as pd
import utils

def show(df):
    st.markdown("##  Data Historis Penjualan")
    st.write("Berikut adalah basis data yang saat ini tersimpan dalam sistem dan digunakan untuk proses prediksi.")
    st.markdown("---")
    
    if df is not None:
        # --- RINGKASAN DATA ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(utils.create_card_html("Total Transaksi", f"{len(df)} Baris", "Volume Data", "border-primary"), unsafe_allow_html=True)
        with col2:
            try:
                tgl_awal = df['Tanggal'].min().strftime('%d-%m-%Y')
                st.markdown(utils.create_card_html("Periode Awal", tgl_awal, "Start Date", "border-success"), unsafe_allow_html=True)
            except:
                st.write("-")
        with col3:
            try:
                tgl_akhir = df['Tanggal'].max().strftime('%d-%m-%Y')
                st.markdown(utils.create_card_html("Periode Akhir", tgl_akhir, "End Date", "border-warning"), unsafe_allow_html=True)
            except:
                st.write("-")
        
        # --- TABEL UTAMA ---
        st.markdown("###  Tabel Detail")
        
        sort_order = st.radio("Urutkan Data:", ["Terbaru ke Terlama", "Terlama ke Terbaru"], horizontal=True)
        
        if sort_order == "Terbaru ke Terlama":
            df_display = df.sort_values(by='Tanggal', ascending=False)
        else:
            df_display = df.sort_values(by='Tanggal', ascending=True)

        st.dataframe(df_display, use_container_width=True, height=600)
        
    else:
        st.warning("Data tidak ditemukan dalam sistem. Silakan unggah data melalui menu Input Data Histori.")