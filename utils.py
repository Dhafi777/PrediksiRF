import pandas as pd
import joblib
import streamlit as st
import numpy as np

# --- HELPER FUNCTIONS UI ---
def format_rupiah(nilai):
    return f"Rp {nilai:,.0f}".replace(',', '.')

def create_card_html(title, value, sub_text="", color_class="border-primary"):
    html = f"""
    <div class="kpi-card {color_class}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub_text}</div>
    </div>
    """
    return html

# --- LOAD RESOURCES ---
@st.cache_resource
def load_resources():
    try:
        model = joblib.load('model_skripsi_multishift.pkl')
    except FileNotFoundError:
        return None, None

    try:
        # Prioritas baca file yang baru diupload
        df_db = pd.read_excel('TRAIN_80_ANGKA.xlsx')
    except:
        try:
            df_db = pd.read_csv('train_datas (1).csv') 
        except:
            df_db = None
            
    if df_db is not None:
        df_db.columns = [c.strip() for c in df_db.columns]
        if 'Tanggal' in df_db.columns:
            df_db['Tanggal'] = pd.to_datetime(df_db['Tanggal'])
            df_db = df_db.sort_values('Tanggal')
        
    return model, df_db

# --- HELPER AMBIL DATA CEPAT (OPTIMIZED) ---
# Kita tidak lagi filter dataframe berulang kali, tapi pakai dictionary lookup
def get_val_fast(history_lookup, date_key, col, default):
    if date_key in history_lookup:
        val = history_lookup[date_key].get(col)
        return float(val) if val is not None and pd.notnull(val) else default
    return default

# --- LOGIKA PREDIKSI FLEKSIBEL (OPTIMIZED LOOP) ---
def generate_forecast_data(model, df_historis, start_date, base_suhu, base_hujan, days=30):
    results = []
    list_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    list_bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
    
    # 1. PERSIAPAN DATA CEPAT (PRE-COMPUTE)
    # Ubah DataFrame ke Dictionary agar pencarian jadi O(1) alias instan
    history_lookup = {}
    if df_historis is not None:
        # Kita set index tanggal agar bisa dicari berdasarkan tanggal
        temp_df = df_historis.set_index('Tanggal')
        # Ambil kolom yang relevan saja agar ringan
        cols_needed = [c for c in temp_df.columns if c in ['Suhu', 'Curah Hujan', 'Omzet Pagi', 'Omzet Siang', 'Omzet Malam', 'Total Omzet']]
        # Convert ke dictionary: {Timestamp('2024-01-01'): {'Suhu': 27, ...}, ...}
        history_lookup = temp_df[cols_needed].to_dict('index')

    prediction_buffer = {} 

    # Loop hari
    for i in range(days):
        tgt = pd.to_datetime(start_date) + pd.Timedelta(days=i)
        
        # 1. Fitur Waktu
        h, b, mk, wd = tgt.day, tgt.month, tgt.isocalendar()[1], tgt.weekday()
        is_wk = 1 if wd >= 5 else 0
        
        # 2. FITUR CUACA (Cek Lookup Dulu)
        # Ambil dari lookup dictionary (cepat)
        curr_s = get_val_fast(history_lookup, tgt, 'Suhu', base_suhu)
        curr_h = get_val_fast(history_lookup, tgt, 'Curah Hujan', base_hujan)
        
        # 3. LAG CUACA (Ambil dari lookup dictionary)
        h_t3 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=3), 'Curah Hujan', base_hujan)
        h_t7 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=7), 'Curah Hujan', base_hujan)
        h_t14 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=14), 'Curah Hujan', base_hujan)
        
        s_t3 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=3), 'Suhu', base_suhu)
        s_t7 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=7), 'Suhu', base_suhu)

        # 4. LAG OMZET (PAGI, SIANG, MALAM)
        shifts = ['Omzet Pagi', 'Omzet Siang', 'Omzet Malam']
        lags = [7, 30]
        lag_values = {}
        
        for shift in shifts:
            for l in lags:
                lag_date = tgt - pd.Timedelta(days=l)
                
                # Cek buffer prediksi (masa depan) -> O(1)
                if lag_date in prediction_buffer:
                    val = prediction_buffer[lag_date][shift]
                else:
                    # Ambil dari history lookup -> O(1)
                    val = get_val_fast(history_lookup, lag_date, shift, 5000000) 
                
                lag_values[f'{shift}_t-{l}'] = val

        # 5. Susun Input
        row_data = {
            'Hari': h, 'Bulan': b, 'Minggu ke': mk, 'Weekend': is_wk,
            'Suhu': curr_s, 'Curah Hujan': curr_h,
            'Hujan_t-3': h_t3, 'Hujan_t-7': h_t7, 'Hujan_t-14': h_t14,
            'Suhu_t-3': s_t3, 'Suhu_t-7': s_t7,
            'Omzet Pagi_t-7': lag_values['Omzet Pagi_t-7'], 
            'Omzet Pagi_t-30': lag_values['Omzet Pagi_t-30'],
            'Omzet Siang_t-7': lag_values['Omzet Siang_t-7'], 
            'Omzet Siang_t-30': lag_values['Omzet Siang_t-30'],
            'Omzet Malam_t-7': lag_values['Omzet Malam_t-7'], 
            'Omzet Malam_t-30': lag_values['Omzet Malam_t-30']
        }
        
        cols = [
            'Hari', 'Bulan', 'Minggu ke', 'Weekend',
            'Suhu', 'Curah Hujan',
            'Hujan_t-3', 'Hujan_t-7', 'Hujan_t-14', 'Suhu_t-3', 'Suhu_t-7',
            'Omzet Pagi_t-7', 'Omzet Pagi_t-30',
            'Omzet Siang_t-7', 'Omzet Siang_t-30',
            'Omzet Malam_t-7', 'Omzet Malam_t-30'
        ]
        
        row_df = pd.DataFrame([row_data])[cols]
        
        # 6. PREDIKSI
        pred = model.predict(row_df)[0]
        
        p_pagi, p_siang, p_malam = pred[0], pred[1], pred[2]
        p_total = p_pagi + p_siang + p_malam
        
        prediction_buffer[tgt] = {'Omzet Pagi': p_pagi, 'Omzet Siang': p_siang, 'Omzet Malam': p_malam}
        
        results.append({
            'Tanggal': tgt, 
            'Hari_Nama': list_hari[wd],
            'Bulan': b,
            'Bulan_Nama': list_bulan[b-1], 
            'Tahun': tgt.year,
            'Prediksi Pagi': p_pagi,
            'Prediksi Siang': p_siang,
            'Prediksi Malam': p_malam,
            'Prediksi Total': p_total,
            'Suhu': curr_s,
            'Hujan': curr_h
        })
        
    return pd.DataFrame(results)

# Wrapper agar kode lama tidak error
def generate_30_days_data(model, df_historis, start_date, base_suhu, base_hujan):
    return generate_forecast_data(model, df_historis, start_date, base_suhu, base_hujan, days=30)

def hitung_mape_otomatis(model, df):
    return "Tersedia"