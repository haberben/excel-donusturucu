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
    'Model Kodu': 'Varyant Grup ID',
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
    'Ürün Rengi': 'Renk'
}
# İşlem butonu ve sonuçlar
if st.button("🚀 Verileri Dönüştür", type="primary", use_container_width=True):
    if not all([hedef_dosya, markalar_dosyasi, kategoriler_dosyasi, kaynak_dosya]):
        st.error("❌ Lütfen tüm dosyaları yükleyin!")
    else:
        try:
            with st.spinner("⏳ İşlem yapılıyor..."):
                
                # Dosyaları okuma
                df_hedef = pd.read_excel(hedef_dosya, sheet_name='Sheet1')
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
                
                # Marka ve kategori eşleştirme sözlükleri
                marka_map = dict(zip(df_markalar['Marka Adı'], df_markalar['Marka ID']))
                kategori_map = dict(zip(df_kategoriler['Kategori Adı'], df_kategoriler['Kategori ID']))
                
                # Kolon eşleştirmelerine göre veri aktar
                for kaynak_kolon, hedef_kolon in kolon_eslestirme.items():
                    if kaynak_kolon in df_kaynak.columns and hedef_kolon in df_hedef.columns:
                        df_hedef[hedef_kolon] = df_kaynak[kaynak_kolon]
                
                # Marka adını ürün adına ekle
                if 'Marka' in df_hedef.columns and 'Ürün Adı' in df_hedef.columns:
                    df_hedef['Ürün Adı'] = df_hedef.apply(
                        lambda row: f"{str(row['Marka']).capitalize()} {row['Ürün Adı']}" 
                        if pd.notna(row['Marka']) else row['Ürün Adı'], axis=1
                    )
                  # Açıklama düzenleme
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
