import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Sayfa ayarları
st.set_page_config(
    page_title="Excel Veri Dönüştürücü",
    page_icon="📊",
    layout="wide"
)

# Şifre kontrolü
def check_password():
    def password_entered():
        if st.session_state["password"] == "admin123":  # Buraya kendi şifreni yaz
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Giriş Yapın")
        st.text_input("Şifre", type="password", on_change=password_entered, key="password")
        st.info("Sisteme erişim için şifre gerekli")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Giriş Yapın")
        st.text_input("Şifre", type="password", on_change=password_entered, key="password")
        st.error("❌ Yanlış şifre")
        return False
    else:
        return True

# Şifre kontrolü
if not check_password():
    st.stop()

# Ana uygulama
st.title("📊 Excel Veri Dönüştürücü")
st.markdown("### Ürün verilerinizi Idefix formatına dönüştürün")

# Sidebar - Dosya yükleme
with st.sidebar:
    st.header("📂 Dosya Yükleme")
    
    # Sabit dosyalar
    st.subheader("Sabit Dosyalar (Bir kez yükleyin)")
    hedef_dosya = st.file_uploader("ide_data.xlsx (Hedef şablon)", type=['xlsx'], key="hedef")
    markalar_dosyasi = st.file_uploader("marka.xlsx", type=['xlsx'], key="marka")
    kategoriler_dosyasi = st.file_uploader("kategori.xlsx", type=['xlsx'], key="kategori")
    
    st.divider()
    
    # Kaynak dosya
    st.subheader("İşlenecek Dosya")
    kaynak_dosya = st.file_uploader("TR Veri Dosyası (Her seferinde farklı)", type=['xlsx'], key="kaynak")

# Kolon eşleştirme sözlüğü
kolon_eslestirme = {
    'Ürün Adı': 'Ürün Adı',
    'Barkod': 'Barkod',
    'Kategori İsmi': 'Kategori',
    'Marka': 'Marka',
    'Ürün Açıklaması': 'Ürün Açıklaması',
    'Tedarikçi Stok Kodu': 'Satıcı Stok Kodu',
    'KDV Oranı': 'KDV',
    'Desi': 'Desi',
    'Görsel 1': 'Görsel 1',
    'Görsel 2': 'Görsel 2',
    'Görsel 3': 'Görsel 3',
    'Görsel 4': 'Görsel 4',
    'Görsel 5': 'Görsel 5',
    'Görsel 6': 'Görsel 6',
    'Görsel 7': 'Görsel 7',
    'Görsel 8': 'Görsel 8',
    'Ürün Rengi': 'Renk',
    'Boyut/Ebat': 'Boyut/Ebat'
}

# İşlem butonu ve sonuçlar
if st.button("🚀 Verileri Dönüştür", type="primary", use_container_width=True):
    if not all([hedef_dosya, markalar_dosyasi, kategoriler_dosyasi, kaynak_dosya]):
        st.error("❌ Lütfen tüm dosyaları yükleyin!")
    else:
        try:
            with st.spinner("⏳ İşlem yapılıyor..."):
                
                # Dosyaları okuma
                df_hedef = pd.read_excel(hedef_dosya, sheet_name=0)
                df_markalar = pd.read_excel(markalar_dosyasi)
                df_kategoriler = pd.read_excel(kategoriler_dosyasi)
                
                # Kaynak dosyadaki sayfaları kontrol et
                xl_file = pd.ExcelFile(kaynak_dosya)
                kaynak_sayfa = None
                
                # Uygun sayfa adını bul
                for sheet in xl_file.sheet_names:
                    if 'ürün' in sheet.lower() or 'urun' in sheet.lower():
                        kaynak_sayfa = sheet
                        break
                
                if not kaynak_sayfa:
                    kaynak_sayfa = xl_file.sheet_names[0]
                
                df_kaynak = pd.read_excel(kaynak_dosya, sheet_name=kaynak_sayfa)
                
                # Debug: Sütun isimlerini göster
                st.info(f"Kaynak dosya sütunları: {list(df_kaynak.columns)}")
                st.info(f"Hedef dosya sütunları: {list(df_hedef.columns)}")
                
                # Akıllı marka eşleştirme sözlüğü
                marka_map = {}
                for index, row in df_markalar.iterrows():
                    marka_adi = str(row['Marka Adı']).strip()
                    marka_id = row['Marka ID']
                    # Orijinal hali
                    marka_map[marka_adi] = marka_id
                    # Küçük harf hali
                    marka_map[marka_adi.lower()] = marka_id
                    # Büyük harf hali
                    marka_map[marka_adi.upper()] = marka_id
                    # İlk harf büyük hali
                    marka_map[marka_adi.capitalize()] = marka_id

                # Akıllı kategori eşleştirme sözlüğü
                kategori_map = {}
                for index, row in df_kategoriler.iterrows():
                    kategori_adi = str(row['Kategori Adı']).strip()
                    kategori_id = row['Kategori ID']
                    # Orijinal hali
                    kategori_map[kategori_adi] = kategori_id
                    # Küçük harf hali
                    kategori_map[kategori_adi.lower()] = kategori_id
                    # Büyük harf hali
                    kategori_map[kategori_adi.upper()] = kategori_id
                    # İlk harf büyük hali
                    kategori_map[kategori_adi.capitalize()] = kategori_id
                    
                # Özel kategori eşleştirmeleri
                kategori_map["Dizüstü Bilgisayar"] = kategori_map.get("Dizüstü Bilgisayar & Laptop")
                kategori_map["dizüstü bilgisayar"] = kategori_map.get("Dizüstü Bilgisayar & Laptop")
                
                # Kolon eşleştirmelerine göre veri aktar
                for kaynak_kolon, hedef_kolon in kolon_eslestirme.items():
                    if kaynak_kolon in df_kaynak.columns and hedef_kolon in df_hedef.columns:
                        df_hedef[hedef_kolon] = df_kaynak[kaynak_kolon]
                        st.success(f"✅ {kaynak_kolon} → {hedef_kolon}")
                
                # VARYANT GRUP ID - Model Kodu aktarımı (KESIN ÇÖZÜM)
                model_kodu_aktarildi = False
                
                # Tüm olası Varyant Grup ID sütun isimlerini dene
                varyant_sutun_isimleri = [
                    'Varyant Grup ID', 'Varyant Grup Id', 'Varyant Grup id',
                    'VARYANT GRUP ID', 'varyant grup id', 'Varyant Grup ID'
                ]
                
                hedef_varyant_sutun = None
                for sutun in varyant_sutun_isimleri:
                    if sutun in df_hedef.columns:
                        hedef_varyant_sutun = sutun
                        break
                
                # Model Kodu sütunu bul
                model_sutun = None
                if 'Model Kodu' in df_kaynak.columns:
                    model_sutun = 'Model Kodu'
                
                # Aktarım yap
                if model_sutun and hedef_varyant_sutun:
                    df_hedef[hedef_varyant_sutun] = df_kaynak[model_sutun]
                    st.success(f"✅ Model Kodu → {hedef_varyant_sutun} BAŞARILI!")
                    model_kodu_aktarildi = True
                else:
                    st.error(f"HATA: Model Sutun: {model_sutun}, Varyant Sutun: {hedef_varyant_sutun}")
                
                # Boyut/Ebat sütunu özel işleme
                if 'Boyut/Ebat' in df_kaynak.columns:
                    if 'Boyut/Ebat' not in df_hedef.columns and 'Renk' in df_hedef.columns:
                        renk_pos = df_hedef.columns.get_loc('Renk')
                        df_hedef.insert(renk_pos + 1, 'Boyut/Ebat', df_kaynak['Boyut/Ebat'])
                    elif 'Boyut/Ebat' in df_hedef.columns:
                        df_hedef['Boyut/Ebat'] = df_kaynak['Boyut/Ebat']
                
                # Marka adını ürün adına ekle
                if 'Marka' in df_hedef.columns and 'Ürün Adı' in df_hedef.columns:
                    df_hedef['Ürün Adı'] = df_hedef.apply(
                        lambda row: f"{str(row['Marka']).capitalize()} {row['Ürün Adı']}" 
                        if pd.notna(row['Marka']) else row['Ürün Adı'], axis=1
                    )
                
                # Açıklama düzenleme ve site ismi temizleme
                if 'Ürün Açıklaması' in df_hedef.columns:
                    df_hedef['Ürün Açıklaması'] = df_hedef['Ürün Açıklaması'].astype(str)
                    
                    # Site isimlerini temizle
                    site_isimleri = ['trendyol', 'hepsiburada', 'n11', 'gittigidiyor', 'amazon', 'sahibinden', 'pazarama', 'ciceksepeti']
                    for site in site_isimleri:
                        df_hedef['Ürün Açıklaması'] = df_hedef['Ürün Açıklaması'].str.replace(site, '', regex=False, case=False)
                    
                    # Diğer temizlemeler
                    df_hedef['Ürün Açıklaması'] = df_hedef['Ürün Açıklaması'].str.replace(';', '<br>', regex=False)
                    df_hedef['Ürün Açıklaması'] = df_hedef['Ürün Açıklaması'].str.replace('*', '<br>*', regex=False)
                
                # Boş açıklamaları ürün adı ile doldur
                if 'Ürün Açıklaması' in df_hedef.columns and 'Ürün Adı' in df_hedef.columns:
                    df_hedef['Ürün Açıklaması'] = df_hedef.apply(
                        lambda row: row['Ürün Adı'] if pd.isna(row['Ürün Açıklaması']) 
                        or str(row['Ürün Açıklaması']).lower().strip() in ['nan', ''] 
                        else row['Ürün Açıklaması'], axis=1
                    )
                
                # Satıcı stok kodu boşsa barkod ile doldur
                if 'Satıcı Stok Kodu' in df_hedef.columns and 'Barkod' in df_hedef.columns:
                    df_hedef['Satıcı Stok Kodu'] = df_hedef['Satıcı Stok Kodu'].fillna(df_hedef['Barkod'])
                
                # Marka ve kategori ID eşleştirmeleri
                if 'Marka' in df_hedef.columns:
                    df_hedef['Marka'] = df_hedef['Marka'].map(marka_map).fillna(df_hedef['Marka'])
                if 'Kategori' in df_hedef.columns:
                    df_hedef['Kategori'] = df_hedef['Kategori'].map(kategori_map).fillna(df_hedef['Kategori'])
                
                # Kategori Adı sütunu - ORİJİNAL KATEGORİ ADI İLE
                if 'Kategori' in df_hedef.columns and 'Kategori İsmi' in df_kaynak.columns:
                    kategori_id_to_name = dict(zip(df_kategoriler['Kategori ID'], df_kategoriler['Kategori Adı']))
                    kategori_pos = df_hedef.columns.get_loc('Kategori')
                    
                    # ID bulunanlar için kategori adı, bulunamayanlar için orijinal kategori ismi
                    kategori_adlari = []
                    for i, kategori_id in enumerate(df_hedef['Kategori']):
                        if kategori_id in kategori_id_to_name:
                            kategori_adlari.append(kategori_id_to_name[kategori_id])
                        else:
                            # Orijinal kategori adını kullan
                            orijinal_ad = df_kaynak['Kategori İsmi'].iloc[i] if i < len(df_kaynak['Kategori İsmi']) else 'Bilinmiyor'
                            kategori_adlari.append(orijinal_ad)
                    
                    df_hedef.insert(kategori_pos, 'Kategori Adı', kategori_adlari)
                
                # Sabit kolonlar
                df_hedef['Stok Adedi'] = 0
                df_hedef['Idefix Satış Fiyatı'] = 0
                df_hedef['Piyasa Satış Fiyatı'] = 0
                
            st.success("✅ İşlem başarıyla tamamlandı!")
            
            # Sonuç dosyasını indirme
            buffer = BytesIO()
            df_hedef.to_excel(buffer, index=False, engine='xlsxwriter')
            buffer.seek(0)
            
            kaynak_dosya_adi = os.path.splitext(kaynak_dosya.name)[0]
            
            st.download_button(
                label="📥 Sonuç Dosyasını İndir",
                data=buffer,
                file_name=f"{kaynak_dosya_adi}_idefix_sonuc.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
            # Özet bilgileri
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("İşlenen Satır", len(df_hedef))
            with col2:
                st.metric("Toplam Kolon", len(df_hedef.columns))
            with col3:
                st.metric("Model Kodu Aktarım", "✅" if model_kodu_aktarildi else "❌")
            
            # Önizleme
            with st.expander("📋 Sonuç Önizlemesi (İlk 5 satır)"):
                st.dataframe(df_hedef.head(), use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Hata oluştu: {str(e)}")
            st.info("💡 Dosya formatlarını ve sayfa isimlerini kontrol edin")

# Alt bilgi
st.divider()
st.markdown("""
### 📝 Kullanım Talimatları:
1. **Sabit dosyalar**: ide_data.xlsx, marka.xlsx, kategori.xlsx dosyalarını bir kez yükleyin
2. **TR Veri Dosyası**: Her işlem için farklı kaynak dosyanızı yükleyin
3. **Dönüştür**: Butona tıklayarak işlemi başlatın
4. **İndir**: Sonuç dosyasını bilgisayarınıza indirin

**🔐 Şifre**: Güvenlik için değiştirmeyi unutmayın!
"
