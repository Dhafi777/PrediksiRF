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
    history_lookup = {}
    if df_historis is not None:
        temp_df = df_historis.set_index('Tanggal')
        cols_needed = [c for c in temp_df.columns if c in ['Suhu', 'Curah Hujan', 'Omzet Pagi', 'Omzet Siang', 'Omzet Malam', 'Total Omzet']]
        history_lookup = temp_df[cols_needed].to_dict('index')

    prediction_buffer = {} 

    # Loop hari
    for i in range(days):
        tgt = pd.to_datetime(start_date) + pd.Timedelta(days=i)
        
        # 1. Fitur Waktu
        h, b, mk, wd = tgt.day, tgt.month, tgt.isocalendar()[1], tgt.weekday()
        is_wk = 1 if wd >= 5 else 0
        
        # 2. Fitur Event (Sosio-kultural)
        is_akhir_tahun = 1 if (b == 12 and h >= 20) else 0
        
        tgt_str = tgt.strftime('%Y-%m-%d')
        is_ramadhan = 1 if (('2024-03-11' <= tgt_str <= '2024-04-09') or 
                            ('2025-03-01' <= tgt_str <= '2025-03-30') or 
                            ('2026-02-18' <= tgt_str <= '2026-03-19')) else 0
                            
        is_lebaran = 1 if (('2024-04-10' <= tgt_str <= '2024-04-11') or 
                           ('2025-03-31' <= tgt_str <= '2025-04-01') or 
                           ('2026-03-20' <= tgt_str <= '2026-03-21')) else 0

        # 3. Fitur Cuaca & Lag Cuaca
        curr_s = get_val_fast(history_lookup, tgt, 'Suhu', base_suhu)
        curr_h = get_val_fast(history_lookup, tgt, 'Curah Hujan', base_hujan)
        
        h_t3 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=3), 'Curah Hujan', base_hujan)
        h_t7 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=7), 'Curah Hujan', base_hujan)
        h_t14 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=14), 'Curah Hujan', base_hujan)
        
        s_t3 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=3), 'Suhu', base_suhu)
        s_t7 = get_val_fast(history_lookup, tgt - pd.Timedelta(days=7), 'Suhu', base_suhu)

        # 4. Lag Omzet
        shifts = ['Omzet Pagi', 'Omzet Siang', 'Omzet Malam']
        lags = [7, 30]
        lag_values = {}
        
        for shift in shifts:
            for l in lags:
                lag_date = tgt - pd.Timedelta(days=l)
                if lag_date in prediction_buffer:
                    val = prediction_buffer[lag_date][shift]
                else:
                    val = get_val_fast(history_lookup, lag_date, shift, 5000000) 
                lag_values[f'{shift}_t-{l}'] = val

        # 5. Susun Input (Sesuai 20 Fitur Model Baru)
        row_data = {
            'Hari': h, 'Bulan': b, 'Minggu ke': mk, 'Weekend': is_wk,
            'is_ramadhan': is_ramadhan, 'is_lebaran': is_lebaran, 'is_akhir_tahun': is_akhir_tahun,
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
            'is_ramadhan', 'is_lebaran', 'is_akhir_tahun', 
            'Suhu', 'Curah Hujan',
            'Hujan_t-3', 'Hujan_t-7', 'Hujan_t-14', 'Suhu_t-3', 'Suhu_t-7',
            'Omzet Pagi_t-7', 'Omzet Pagi_t-30',
            'Omzet Siang_t-7', 'Omzet Siang_t-30',
            'Omzet Malam_t-7', 'Omzet Malam_t-30'
        ]
        
        row_df = pd.DataFrame([row_data])[cols]
        
        # 6. Prediksi
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

def generate_30_days_data(model, df_historis, start_date, base_suhu, base_hujan):
    return generate_forecast_data(model, df_historis, start_date, base_suhu, base_hujan, days=30)

def hitung_mape_otomatis(model, df):
    return "Tersedia"

# ==============================================================================
# FUNGSI EXPLAINABLE AI (SHAP)
# ==============================================================================
def extract_single_day_features(df_historis, target_date, input_suhu, input_hujan):
    target_date = pd.to_datetime(target_date)
    hari, bulan, minggu_ke = target_date.day, target_date.month, target_date.isocalendar().week
    weekend = 1 if target_date.weekday() >= 5 else 0
    
    is_akhir_tahun = 1 if (bulan == 12 and hari >= 20) else 0
    tgt_str = target_date.strftime('%Y-%m-%d')
    is_ramadhan = 1 if (('2024-03-11' <= tgt_str <= '2024-04-09') or 
                        ('2025-03-01' <= tgt_str <= '2025-03-30') or 
                        ('2026-02-18' <= tgt_str <= '2026-03-19')) else 0
    is_lebaran = 1 if (('2024-04-10' <= tgt_str <= '2024-04-11') or 
                       ('2025-03-31' <= tgt_str <= '2025-04-01') or 
                       ('2026-03-20' <= tgt_str <= '2026-03-21')) else 0

    try:
        t_3, t_7, t_14, t_30 = target_date - pd.Timedelta(days=3), target_date - pd.Timedelta(days=7), target_date - pd.Timedelta(days=14), target_date - pd.Timedelta(days=30)
        df_hist = df_historis.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_hist.index):
            df_hist['Tanggal'] = pd.to_datetime(df_hist['Tanggal'])
            df_hist = df_hist.set_index('Tanggal')
            
        hujan_t3 = df_hist.loc[t_3, 'Curah Hujan'] if t_3 in df_hist.index else 0
        hujan_t7 = df_hist.loc[t_7, 'Curah Hujan'] if t_7 in df_hist.index else 0
        hujan_t14 = df_hist.loc[t_14, 'Curah Hujan'] if t_14 in df_hist.index else 0
        suhu_t3 = df_hist.loc[t_3, 'Suhu'] if t_3 in df_hist.index else 27.0
        suhu_t7 = df_hist.loc[t_7, 'Suhu'] if t_7 in df_hist.index else 27.0
        
        omzet_pagi_t7 = df_hist.loc[t_7, 'Omzet Pagi'] if t_7 in df_hist.index else 5000000
        omzet_pagi_t30 = df_hist.loc[t_30, 'Omzet Pagi'] if t_30 in df_hist.index else 5000000
        omzet_siang_t7 = df_hist.loc[t_7, 'Omzet Siang'] if t_7 in df_hist.index else 5000000
        omzet_siang_t30 = df_hist.loc[t_30, 'Omzet Siang'] if t_30 in df_hist.index else 5000000
        omzet_malam_t7 = df_hist.loc[t_7, 'Omzet Malam'] if t_7 in df_hist.index else 5000000
        omzet_malam_t30 = df_hist.loc[t_30, 'Omzet Malam'] if t_30 in df_hist.index else 5000000
    except Exception:
        hujan_t3, hujan_t7, hujan_t14, suhu_t3, suhu_t7 = 0, 0, 0, 27.0, 27.0
        omzet_pagi_t7, omzet_pagi_t30, omzet_siang_t7, omzet_siang_t30, omzet_malam_t7, omzet_malam_t30 = [5000000]*6

    feature_names = ['Hari', 'Bulan', 'Minggu ke', 'Weekend', 'is_ramadhan', 'is_lebaran', 'is_akhir_tahun', 'Suhu', 'Curah Hujan', 'Hujan_t-3', 'Hujan_t-7', 'Hujan_t-14', 'Suhu_t-3', 'Suhu_t-7', 'Omzet Pagi_t-7', 'Omzet Pagi_t-30', 'Omzet Siang_t-7', 'Omzet Siang_t-30', 'Omzet Malam_t-7', 'Omzet Malam_t-30']
    feature_values = [hari, bulan, minggu_ke, weekend, is_ramadhan, is_lebaran, is_akhir_tahun, input_suhu, input_hujan, hujan_t3, hujan_t7, hujan_t14, suhu_t3, suhu_t7, omzet_pagi_t7, omzet_pagi_t30, omzet_siang_t7, omzet_siang_t30, omzet_malam_t7, omzet_malam_t30]
    return pd.DataFrame([feature_values], columns=feature_names), feature_names

def generate_shap_waterfall(model, feature_row, feature_names):
    import shap
    import matplotlib.pyplot as plt
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(feature_row)
    
    # Adaptasi Matrix SHAP (Menangani Total Omzet dari 3 Output)
    if isinstance(shap_values, list):
        shap_val_total = shap_values[0][0] + shap_values[1][0] + shap_values[2][0]
        base_val_total = explainer.expected_value[0] + explainer.expected_value[1] + explainer.expected_value[2]
    else:
        shap_val_total = shap_values[0, :, 0] + shap_values[0, :, 1] + shap_values[0, :, 2]
        base_val_total = explainer.expected_value[0] + explainer.expected_value[1] + explainer.expected_value[2]

    shap_exp = shap.Explanation(
        values=shap_val_total,
        base_values=base_val_total,
        data=feature_row.iloc[0].values,
        feature_names=feature_names
    )

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    shap.waterfall_plot(shap_exp, show=False) 
    plt.title("Dekomposisi Parameter Prediksi (SHAP Waterfall Plot)", fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig