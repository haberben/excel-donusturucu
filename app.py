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
        if st.session_state["password"] == "idepim65":  # Buraya kendi şifreni yaz
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
                
                # VARYANT GRUP ID - Model Kodu aktarımı
                varyant_sutun_isimleri = [
                    'Varyant Grup ID', 'Varyant Grup Id', 'Varyant Grup id',
                    'VARYANT GRUP ID', 'varyant grup id'
                ]
                
                hedef_varyant_sutun = None
                for sutun in varyant_sutun_isimleri:
                    if sutun in df_hedef.columns:
                        hedef_varyant_sutun = sutun
                        break
                
                if 'Model Kodu' in df_kaynak.columns and hedef_varyant_sutun:
                    df_hedef[hedef_varyant_sutun] = df_kaynak['Model Kodu']
                    st.success(f"✅ Model Kodu → {hedef_varyant_sutun}")
                
                # Boyut/Ebat sütunu ekleme (Renk sütunundan sonra)
                current_pos = df_hedef.columns.get_loc('Renk') if 'Renk' in df_hedef.columns else len(df_hedef.columns)
                
                if 'Boyut/Ebat' in df_kaynak.columns:
                    if 'Boyut/Ebat' not in df_hedef.columns:
                        current_pos += 1
                        df_hedef.insert(current_pos, 'Boyut/Ebat', df_kaynak['Boyut/Ebat'])
                        st.success("✅ Boyut/Ebat sütunu eklendi")
                    else:
                        df_hedef['Boyut/Ebat'] = df_kaynak['Boyut/Ebat']
                
                # Cep Telefonu Modeli sütunu ekleme
                if 'Cep Telefonu Modeli' in df_kaynak.columns:
                    current_pos += 1
                    df_hedef.insert(current_pos, 'Cep Telefonu Modeli', df_kaynak['Cep Telefonu Modeli'])
                    st.success("✅ Cep Telefonu Modeli sütunu eklendi")
                
                # Uyumlu Marka sütunu ekleme
                if 'Uyumlu Marka' in df_kaynak.columns:
                    current_pos += 1
                    df_hedef.insert(current_pos, 'Uyumlu Marka', df_kaynak['Uyumlu Marka'])
                    st.success("✅ Uyumlu Marka sütunu eklendi")
                
                # Ayakkabı Numarası sütunu ekleme
                if 'Ayakkabı Numarası' in df_kaynak.columns:
                    current_pos += 1
                    df_hedef.insert(current_pos, 'Ayakkabı Numarası', df_kaynak['Ayakkabı Numarası'])
                    st.success("✅ Ayakkabı Numarası sütunu eklendi")
                
                # Beden sütunu ekleme
                if 'Beden' in df_kaynak.columns:
                    current_pos += 1
                    df_hedef.insert(current_pos, 'Beden', df_kaynak['Beden'])
                    st.success("✅ Beden sütunu eklendi")
                
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
                
                # Marka ID eşleştirmesi
                if 'Marka' in df_hedef.columns:
                    df_hedef['Marka'] = df_hedef['Marka'].map(marka_map).fillna(df_hedef['Marka'])
                
                # Kategori ID eşleştirmesi - DÜZELTME
                if 'Kategori' in df_hedef.columns and 'Kategori İsmi' in df_kaynak.columns:
                    # Önce ID eşleştirmesini dene
                    kategori_idleri = df_hedef['Kategori'].map(kategori_map)
                    
                    # Eşleşmeyenler için orijinal kategori adını koru
                    for i in range(len(df_hedef)):
                        if pd.isna(kategori_idleri.iloc[i]):
                            # Eşleşme bulunamadı, orijinal kategori adını koru
                            df_hedef.at[i, 'Kategori'] = df_kaynak.at[i, 'Kategori İsmi']
                        else:
                            # Eşleşme bulundu, ID'yi kullan
                            df_hedef.at[i, 'Kategori'] = kategori_idleri.iloc[i]
                
                # Kategori Adı sütunu ekleme (Kategori sütunundan önce)
                if 'Kategori' in df_hedef.columns and 'Kategori İsmi' in df_kaynak.columns:
                    kategori_id_to_name = dict(zip(df_kategoriler['Kategori ID'], df_kategoriler['Kategori Adı']))
                    kategori_pos = df_hedef.columns.get_loc('Kategori')
                    
                    kategori_adlari = []
                    for i in range(len(df_hedef)):
                        kategori_degeri = df_hedef.at[i, 'Kategori']
                        
                        # Eğer sayısal ID ise, kategori adını bul
                        if str(kategori_degeri).isdigit() and int(kategori_degeri) in kategori_id_to_name:
                            kategori_adlari.append(kategori_id_to_name[int(kategori_degeri)])
                        else:
                            # ID değilse, değerin kendisi kategori adı
                            kategori_adlari.append(str(kategori_degeri))
                    
                    df_hedef.insert(kategori_pos, 'Kategori Adı', kategori_adlari)
                    st.success("✅ Kategori Adı sütunu eklendi")
                
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
                st.metric("Kaynak Sayfa", kaynak_sayfa)
            
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
""")
