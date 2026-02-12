import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import utils

def show(model, df_historis, tanggal_pilihan, input_suhu, input_hujan, mape_text):
    st.markdown(f"## 📊 Visualisasi Tren & Cuaca")
    st.write(f"Proyeksi 30 hari ke depan mulai: **{tanggal_pilihan.strftime('%d-%m-%Y')}**")
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

    # --- GRAFIK 1: TREN PER SHIFT (Pagi vs Siang vs Malam) ---
    st.markdown("### 📈 Tren Omzet per Shift")
    fig, ax = plt.subplots(figsize=(12, 5))
    
    ax.plot(df_viz['Tanggal'], df_viz['Prediksi Pagi'], marker='.', label='Pagi', color='#eab308', linewidth=2)
    ax.plot(df_viz['Tanggal'], df_viz['Prediksi Siang'], marker='.', label='Siang', color='#ea580c', linewidth=2)
    ax.plot(df_viz['Tanggal'], df_viz['Prediksi Malam'], marker='.', label='Malam', color='#1d4ed8', linewidth=2)
    
    ax.set_ylabel('Omzet (Rupiah)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Format Rupiah di Axis Y
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x)).replace(',', '.')))
    
    st.pyplot(fig)
    
    st.write("")
    
    # --- GRAFIK 2 & 3: KORELASI CUACA (DIKEMBALIKAN) ---
    # Kita bandingkan 'Prediksi Total' vs Suhu/Hujan
    
    col_g1, col_g2 = st.columns(2)
    
    # KORELASI SUHU
    with col_g1:
        st.markdown("#### 🌡️ Total Omzet vs Suhu")
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        
        # Garis 1: Total Omzet
        line1 = ax2.plot(df_viz['Tanggal'], df_viz['Prediksi Total'], color='#4361ee', label='Total Omzet')
        ax2.set_ylabel("Omzet", color='#4361ee', fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#4361ee')
        ax2.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x)).replace(',', '.')))
        
        # Garis 2: Suhu (Sumbu Kanan)
        ax2_twin = ax2.twinx()
        line2 = ax2_twin.plot(df_viz['Tanggal'], df_viz['Suhu'], color='#ef4444', linestyle='--', label='Suhu')
        ax2_twin.set_ylabel("Suhu (°C)", color='#ef4444', fontweight='bold')
        ax2_twin.tick_params(axis='y', labelcolor='#ef4444')
        
        # Legend
        lns = line1 + line2
        labs = [l.get_label() for l in lns]
        ax2.legend(lns, labs, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)
        ax2.grid(True, linestyle='--', alpha=0.3)
        ax2.set_xticks([]) 
        st.pyplot(fig2)

    # KORELASI HUJAN
    with col_g2:
        st.markdown("#### 🌧️ Total Omzet vs Hujan")
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        
        # Garis 1: Total Omzet
        line3 = ax3.plot(df_viz['Tanggal'], df_viz['Prediksi Total'], color='#4361ee', label='Total Omzet')
        ax3.set_ylabel("Omzet", color='#4361ee', fontweight='bold')
        ax3.tick_params(axis='y', labelcolor='#4361ee')
        ax3.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x)).replace(',', '.')))
        
        # Garis 2: Hujan (Sumbu Kanan)
        ax3_twin = ax3.twinx()
        line4 = ax3_twin.plot(df_viz['Tanggal'], df_viz['Hujan'], color='#10b981', linestyle='--', label='Hujan')
        ax3_twin.set_ylabel("Hujan (mm)", color='#10b981', fontweight='bold')
        ax3_twin.tick_params(axis='y', labelcolor='#10b981')
        
        # Legend
        lns2 = line3 + line4
        labs2 = [l.get_label() for l in lns2]
        ax3.legend(lns2, labs2, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)
        ax3.grid(True, linestyle='--', alpha=0.3)
        ax3.set_xticks([]) 
        st.pyplot(fig3)
    
    st.markdown("---")
    
    # --- FEATURE IMPORTANCE ---
    st.markdown("### 🧠 Faktor Pengaruh (Feature Importance)")
    st.write("Variabel mana yang paling mempengaruhi prediksi (Rata-rata pengaruh ke semua shift).")
    
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
            
            fig4, ax4 = plt.subplots(figsize=(10, 8))
            
            # Warna Bar
            bars = ax4.barh(df_imp['Fitur'], df_imp['Penting'], color='#4361ee', alpha=0.8)
            
            # Label Angka
            for bar in bars:
                width = bar.get_width()
                ax4.text(width + 0.001, bar.get_y() + bar.get_height()/2, 
                         f'{width:.1%}', 
                         ha='left', va='center', fontsize=9, color='#1e293b')

            ax4.set_xlabel('Score Kepentingan')
            ax4.set_xlim(0, max(importances)*1.2)
            
            ax4.spines['top'].set_visible(False)
            ax4.spines['right'].set_visible(False)
            ax4.grid(axis='x', linestyle='--', alpha=0.3)
            
            st.pyplot(fig4)
        else:
            st.error(f"Mismatch Error: Model memiliki {len(importances)} fitur, tetapi daftar nama ada {len(feature_names)}.")
    else:
        st.warning("Model tidak mendukung feature importance.")