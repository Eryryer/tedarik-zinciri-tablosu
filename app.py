import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os # Veritabanı dosyası kontrolü için lazım

# Sayfa ayarlari
st.set_page_config(page_title="Tedarik Zinciri Dashboard", layout="wide")

DB_NAME = 'tedarik_db.sqlite'

# Şehir koordinatlarıi
KOORDINATLAR = {
    'İstanbul': (41.0082, 28.9784), 'İzmir': (38.4192, 27.1287),
    'Kocaeli': (40.7656, 29.9406), 'Mersin': (36.8000, 34.6333),
    'Rotterdam': (51.9244, 4.4777), 'Hamburg': (53.5511, 9.9937),
    'Barselona': (41.3851, 2.1734), 'Marsilya': (43.2965, 5.3698)
}

# VERİTABANI VE TABLO HAZIRLAMA 


# 1. Veritabanı var mı kontrol et 
if not os.path.exists(DB_NAME):
    # Veritabanına bağlan dosya olustur.
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabloyu oluştur
    c.execute('''
        CREATE TABLE IF NOT EXISTS kargolar (
            Siparis_ID TEXT PRIMARY KEY, Urun TEXT, Cikis_Noktasi TEXT,
            Varis_Noktasi TEXT, Miktar INTEGER, Durum TEXT, Teslimat_Suresi_Gun INTEGER
        )
    ''')
    
    # Örnek verileri ekle 
    c.execute("INSERT INTO kargolar VALUES ('TRK001', 'Polimer', 'İstanbul', 'Rotterdam', 500, 'Teslim Edildi', 5)")
    c.execute("INSERT INTO kargolar VALUES ('TRK002', 'Plastik Hammadde', 'İzmir', 'Hamburg', 300, 'Gecikmede', 8)")
    c.execute("INSERT INTO kargolar VALUES ('TRK003', 'Kimyasal Çözücü', 'Kocaeli', 'Barselona', 150, 'Yolda', 4)")
    c.execute("INSERT INTO kargolar VALUES ('TRK004', 'Polimer', 'Mersin', 'Marsilya', 600, 'Teslim Edildi', 6)")
    
    conn.commit()
    conn.close()

# 2. Verileri getir
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute("SELECT * FROM kargolar")
veriler = c.fetchall()
# tablo
df = pd.DataFrame(veriler, columns=['Siparis_ID', 'Urun', 'Cikis_Noktasi', 'Varis_Noktasi', 'Miktar', 'Durum', 'Teslimat_Suresi_Gun'])
conn.close()

# ==========================================
# SOL MENÜ  - Filtreleme 
# ==========================================
st.sidebar.header("🔍 Filtreleme")

# Benzersiz durum listesini oluşturmak için döngü 
durum_listesi_ham = df["Durum"].tolist()
unique_durumlar = []
for durum in durum_listesi_ham:
    if durum not in unique_durumlar:
        unique_durumlar.append(durum)

secilen_durumlar = st.sidebar.multiselect(
    "Kargo Durumu:",
    options=unique_durumlar,
    default=unique_durumlar
)

# Filtreleme
# Original DataFrame'i alıp, yeni bir DataFrame'e ekle
filtrelenmis_veriler_listesi = []
for index, row in df.iterrows():
    if row['Durum'] in secilen_durumlar:
        filtrelenmis_veriler_listesi.append(row)
# Eğer hiç filtre seçilmezse hata vermemesi için kontrol et
if filtrelenmis_veriler_listesi:
    df_filtrelenmis = pd.DataFrame(filtrelenmis_veriler_listesi)
else:
    # Boş bir DataFrame oluştur
    df_filtrelenmis = pd.DataFrame(columns=df.columns)

# ==========================================
# SOL MENÜ  - Veri Yönetimi 
# ==========================================
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Veri Yönetimi")

# Şehir listesini oluştur
bilinen_sehirler = []
for sehir in KOORDINATLAR.keys():
    bilinen_sehirler.append(sehir)

# 1. YENİ KAYIT EKLEME
with st.sidebar.expander("➕ Yeni Kayıt Ekle"):
    # İnputları al
    yeni_id = st.text_input("Sipariş ID (Örn: TRK007)")
    yeni_urun = st.text_input("Ürün Adı")
    yeni_cikis = st.selectbox("Çıkış Noktası", bilinen_sehirler)
    yeni_varis = st.selectbox("Varış Noktası", bilinen_sehirler)
    yeni_miktar = st.number_input("Miktar", min_value=1, step=1)
    yeni_durum = st.selectbox("Durum", ["Yolda", "Teslim Edildi", "Gecikmede", "İptal"])
    yeni_sure = st.number_input("Teslimat Süresi (Gün)", min_value=0, step=1)
    
    # buton 
    if st.sidebar.button("Veriyi Veritabanına Kaydet"):
        if yeni_id == "" or yeni_urun == "":
            st.error("ID ve Ürün boş olamaz!")
        # ID kontrolü 
        id_var_mi = False
        for m_id in df["Siparis_ID"].tolist():
            if yeni_id == m_id:
                id_var_mi = True
                break
        
        if id_var_mi:
            st.error("Bu ID mevcut!")
        else:
            # Bağlantı olustur
            conn_ekle = sqlite3.connect(DB_NAME)
            c_ekle = conn_ekle.cursor()
            c_ekle.execute("INSERT INTO kargolar VALUES (?,?,?,?,?,?,?)", 
                          (yeni_id, yeni_urun, yeni_cikis, yeni_varis, yeni_miktar, yeni_durum, yeni_sure))
            conn_ekle.commit()
            conn_ekle.close()
            st.success("Veri eklendi!")
            st.rerun()

# 2. KAYIT GÜNCELLEME
with st.sidebar.expander("🔄 Durum Güncelle"):
    # Mevcut ID'leri olustur
    mevcut_idler = df["Siparis_ID"].tolist()
    guncellenecek_id = st.selectbox("Güncellenecek Sipariş ID", mevcut_idler if mevcut_idler else [])
    yeni_durum_guncel = st.selectbox("Yeni Durumu Seçin", ["Yolda", "Teslim Edildi", "Gecikmede", "İptal"])
    
    if st.sidebar.button("Durumu Güncelle"):
        if guncellenecek_id:
            # Bağlantı olustur
            conn_guncel = sqlite3.connect(DB_NAME)
            c_guncel = conn_guncel.cursor()
            c_guncel.execute("UPDATE kargolar SET Durum=? WHERE Siparis_ID=?", (yeni_durum_guncel, guncellenecek_id))
            conn_guncel.commit()
            conn_guncel.close()
            st.success("Güncellendi!")
            st.rerun()

# 3. KAYIT SİLME
with st.sidebar.expander("❌ Kayıt Sil"):
    silinecek_id = st.selectbox("Silinecek Sipariş ID", df["Siparis_ID"].tolist() if not df.empty else [])
    
    if st.sidebar.button("Siparişi Sil"):
        if silinecek_id:
            # Baglantı olustur
            conn_sil = sqlite3.connect(DB_NAME)
            c_sil = conn_sil.cursor()
            c_sil.execute("DELETE FROM kargolar WHERE Siparis_ID=?", (silinecek_id,))
            conn_sil.commit()
            conn_sil.close()
            st.success("Silindi!")
            st.rerun()

# ANA SAYFA GÖRÜNÜMÜ

st.title("🌍 Küresel Tedarik Zinciri Veri Analizi")

# --- Geciken Sipariş Kontrolü  ---
geciken_sayisi_manuel = 0
for durum_kontol in df_filtrelenmis["Durum"].tolist():
    if durum_kontol == 'Gecikmede':
        geciken_sayisi_manuel += 1

if geciken_sayisi_manuel > 0:
    st.warning(f"⚠️ DİKKAT: Şu anda sistemde **{geciken_sayisi_manuel} adet** gecikmede sipariş var!")
else:
    st.success("✅ Gecikmede olan sipariş yok.")

# --- Metrikler  ---
st.markdown("### 📊 Genel Özet")
col1, col2, col3 = st.columns(3)

# Toplam Sipariş
col1.metric("Toplam Sipariş", len(df_filtrelenmis))

# Toplam Miktar 
toplam_miktar_manuel = 0
for miktar_kontol in df_filtrelenmis["Miktar"].tolist():
    toplam_miktar_manuel += miktar_kontol
col2.metric("Toplam Miktar", toplam_miktar_manuel)

# Ortalama Süre 
toplam_sure_manuel = 0
if not df_filtrelenmis.empty:
    for sure_kontol in df_filtrelenmis["Teslimat_Suresi_Gun"].tolist():
        toplam_sure_manuel += sure_kontol
    ortalama_sure_manuel = toplam_sure_manuel / len(df_filtrelenmis)
else:
    ortalama_sure_manuel = 0
col3.metric("Ortalama Süre", f"{ortalama_sure_manuel:.1f} Gün")

st.markdown("---")

# --- Harita  ---
st.subheader("🗺️ Küresel Lojistik Haritası")
if not df_filtrelenmis.empty:
    harita_verisi_manuel = []
    #  döngü
    for index, row in df_filtrelenmis.iterrows():
        cikis = row['Cikis_Noktasi']
        varis = row['Varis_Noktasi']
        if cikis in KOORDINATLAR and varis in KOORDINATLAR:
            # Çıkış
            harita_verisi_manuel.append({
                'Sipariş': row['Siparis_ID'], 'Şehir': cikis,
                'Enlem': KOORDINATLAR[cikis][0], 'Boylam': KOORDINATLAR[cikis][1], 'Durum': row['Durum']
            })
            # Varış
            harita_verisi_manuel.append({
                'Sipariş': row['Siparis_ID'], 'Şehir': varis,
                'Enlem': KOORDINATLAR[varis][0], 'Boylam': KOORDINATLAR[varis][1], 'Durum': row['Durum']
            })
    
    if harita_verisi_manuel:
        df_harita_manuel = pd.DataFrame(harita_verisi_manuel)
        fig_harita = px.line_geo(df_harita_manuel, lat="Enlem", lon="Boylam", line_group="Sipariş", color="Durum", projection="natural earth")
        fig_harita.add_trace(px.scatter_geo(df_harita_manuel, lat="Enlem", lon="Boylam", hover_name="Şehir").data[0])
        st.plotly_chart(fig_harita, use_container_width=True)
st.markdown("---")

# --- Grafikler  ---
col_grafik1, col_grafik2 = st.columns(2)
with col_grafik1:
    st.subheader("Kargo Durumları")
    # Pasta grafiği 
    if not df_filtrelenmis.empty:
        fig_durum = px.pie(df_filtrelenmis, names="Durum", hole=0) # hole=0'la donut grafigi olmadı
        st.plotly_chart(fig_durum, use_container_width=True)

with col_grafik2:
    st.subheader("Ürün Miktarları")
    # Sütun grafigi
    if not df_filtrelenmis.empty:
        fig_miktar = px.bar(df_filtrelenmis, x="Urun", y="Miktar") # color="Urun" sildik
        st.plotly_chart(fig_miktar, use_container_width=True)

st.markdown("---")


def tablo_renklendir_acemi(row):
    
    # Gecikmedeyse  : Arka plan açık kırmızı/pembe, yazi rengi siyah ve kalin
    if row['Durum'] == 'Gecikmede':
        return ['background-color: #ffcdd2; color: #000000; font-weight: bold;'] * 7
        
    # Teslim edildiyse: Arka plan açık pastel yeşil, YAZI RENGİ SİYAH ve KALIN
    elif row['Durum'] == 'Teslim Edildi':
        return ['background-color: #c8e6c9; color: #000000; font-weight: bold;'] * 7
        
    # Diğer durumlarda  dokunma
    else:
        return [''] * 7

# --- Detaylı Veri Tablosu ---
st.subheader("📦 Detaylı Veri Tablosu")
if not df_filtrelenmis.empty:
    # Pandas style özelliği
    renkli_tablo_acemi = df_filtrelenmis.style.apply(tablo_renklendir_acemi, axis=1)
    st.dataframe(renkli_tablo_acemi, use_container_width=True)
