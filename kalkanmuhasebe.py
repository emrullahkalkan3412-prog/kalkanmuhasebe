from datetime import datetime
import os
import sqlite3
import hashlib
import pandas as pd
import streamlit as st

# Sayfa Ayarları
st.set_page_config(
    page_title="Online Muhasebe Programı", page_icon="💰", layout="wide"
)

# Kendi Yönetici E-Posta Adresini buraya yazmalısın:
ADMIN_EMAIL = "admin@kalkanmuhasebe.com"  # Kendi mail adresinle değiştirebilirsin

# Şifreleri güvenli saklamak için hashleme fonksiyonu
def hash_sifre(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

# Veritabanı ve Tabloları Başlatma
def init_db():
    conn = sqlite3.connect("muhasebe.db")
    cursor = conn.cursor()
    
    # Kullanıcılar Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            sifre TEXT
        )
    """)
    
    # Müşteriler Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ad TEXT,
            tip TEXT,
            telefon TEXT,
            email TEXT,
            adres TEXT,
            FOREIGN KEY(user_id) REFERENCES kullanicilar(id)
        )
    """)
    
    # İşlemler Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS islemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tarih TEXT,
            tip TEXT,
            aciklama TEXT,
            tutar REAL,
            musteri_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES kullanicilar(id),
            FOREIGN KEY(musteri_id) REFERENCES musteriler(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect("muhasebe.db")
    return conn, conn.cursor()

# Oturum Durumu Kontrolü
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.session_state["email"] = None

# ---------------------------------------------------------
# GİRİŞ / KAYIT EKRANI
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.title("🔐 Online Muhasebe Programı - Giriş")
    
    secim = st.selectbox("İşlem Seçin", ["Giriş Yap", "Kayıt Ol"])
    
    if secim == "Kayıt Ol":
        st.subheader("Yeni Hesap Oluştur")
        yeni_email = st.text_input("E-Posta Adresi").strip().lower()
        yeni_sifre = st.text_input("Şifre", type="password")
        yeni_sifre_tekrar = st.text_input("Şifre (Tekrar)", type="password")
        
        if st.button("KAYIT OL"):
            if not yeni_email or not yeni_sifre:
                st.warning("Lütfen tüm alanları doldurun!")
            elif yeni_sifre != yeni_sifre_tekrar:
                st.error("Şifreler birbiriyle eşleşmiyor!")
            else:
                try:
                    conn, cursor = get_db()
                    cursor.execute(
                        "INSERT INTO kullanicilar (email, sifre) VALUES (?, ?)",
                        (yeni_email, hash_sifre(yeni_sifre))
                    )
                    conn.commit()
                    conn.close()
                    st.success("Kayıt başarılı! Şimdi 'Giriş Yap' sekmesinden giriş yapabilirsiniz.")
                except sqlite3.IntegrityError:
                    st.error("Bu e-posta adresi zaten kayıtlı!")
                    
    else: # Giriş Yap
        st.subheader("Hesabınıza Giriş Yapın")
        giris_email = st.text_input("E-Posta Adresi").strip().lower()
        giris_sifre = st.text_input("Şifre", type="password")
        
        if st.button("GİRİŞ YAP"):
            conn, cursor = get_db()
            cursor.execute(
                "SELECT id, email, sifre FROM kullanicilar WHERE email = ?",
                (giris_email,)
            )
            user = cursor.fetchone()
            conn.close()
            
            if user and user[2] == hash_sifre(giris_sifre):
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user[0]
                st.session_state["email"] = user[1]
                st.success("Giriş başarılı!")
                st.rerun()
            else:
                st.error("Hatalı e-posta veya şifre!")

# ---------------------------------------------------------
# ANA UYGULAMA (Giriş yapıldıysa)
# ---------------------------------------------------------
else:
    current_user_id = st.session_state["user_id"]
    current_email = st.session_state["email"]
    is_admin = (current_email == ADMIN_EMAIL.lower())
    
    # Üst Bilgi ve Çıkış Yap Butonu
    col_baslik, col_cikis = st.columns([5, 1])
    with col_baslik:
        st.title("💰 MUHASEBE PROGRAMI V2.3")
        if is_admin:
            st.caption(f"Aktif Hesap: **{current_email}** (👑 **YÖNETİCİ**) ")
        else:
            st.caption(f"Aktif Hesap: **{current_email}**")
    with col_cikis:
        if st.button("Çıkış Yap"):
            st.session_state["logged_in"] = False
            st.session_state["user_id"] = None
            st.session_state["email"] = None
            st.rerun()

    st.divider()

    # Sekmeleri dinamik oluştur (Eğer adminse Yönetici Paneli sekmesini de ekle)
    if is_admin:
        tabs = st.tabs(["İŞLEMLER", "MÜŞTERİ/TEDARİKÇİ", "RAPORLAR", "👑 YÖNETİCİ PANELİ"])
    else:
        tabs = st.tabs(["İŞLEMLER", "MÜŞTERİ/TEDARİKÇİ", "RAPORLAR"])

    # -------------------- İŞLEMLER SEKMESİ --------------------
    with tabs[0]:
        st.subheader("➕ Yeni İşlem Ekle")

        conn, cursor = get_db()
        cursor.execute("SELECT id, ad FROM musteriler WHERE user_id = ? ORDER BY ad", (current_user_id,))
        musteriler = cursor.fetchall()
        conn.close()

        musteri_dict = {"SEÇİLMEMİŞ": None}
        for m_id, m_ad in musteriler:
            musteri_dict[(m_ad or "").upper()] = m_id

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            islem_tarihi = st.date_input("TARİH", datetime.now(), key="islem_tarih_input")
        with col2:
            islem_tipi = st.selectbox("TÜR", ["GELEN", "GİDEN"], key="islem_tip_select")
        with col3:
            secilen_musteri = st.selectbox("MÜŞTERİ/TEDARİKÇİ", list(musteri_dict.keys()), key="islem_mus_select")
        with col4:
            islem_tutar = st.number_input("TUTAR (₺)", min_value=0.0, format="%.2f", step=10.0, key="islem_tutar_input")

        islem_aciklama = st.text_input("AÇIKLAMA", key="islem_aciklama_input").upper()

        if st.button("İŞLEMİ EKLE"):
            if not islem_aciklama:
                st.warning("AÇIKLAMA ALANINI DOLDURUN!")
            elif islem_tutar <= 0:
                st.warning("TUTAR SIFIRDAN BÜYÜK OLMALIDIR!")
            else:
                conn, cursor = get_db()
                m_id = musteri_dict[secilen_musteri]
                cursor.execute("""
                    INSERT INTO islemler (user_id, tarih, tip, aciklama, tutar, musteri_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    current_user_id,
                    islem_tarihi.strftime("%Y-%m-%d"),
                    islem_tipi,
                    islem_aciklama,
                    islem_tutar,
                    m_id
                ))
                conn.commit()
                conn.close()
                st.success("İŞLEM EKLENDİ!")
                st.rerun()

        st.divider()
        st.subheader("📋 İşlemler Listesi")

        conn, cursor = get_db()
        cursor.execute("""
            SELECT i.id, i.tarih, i.tip, i.aciklama, i.tutar, COALESCE(UPPER(m.ad), '-') 
            FROM islemler i 
            LEFT JOIN musteriler m ON i.musteri_id = m.id 
            WHERE i.user_id = ?
            ORDER BY i.tarih ASC, i.id ASC
        """, (current_user_id,))
        islem_verileri = cursor.fetchall()
        conn.close()

        if islem_verileri:
            islem_listesi_tablo = []
            bakiye_takip = 0
            
            conn, cursor = get_db()
            cursor.execute("SELECT COALESCE(SUM(CASE WHEN tip='GELEN' THEN tutar ELSE -tutar END), 0) FROM islemler WHERE user_id = ?", (current_user_id,))
            son_bakiye = cursor.fetchone()[0]
            conn.close()
            
            st.info(f"SON BAKİYE: ₺{son_bakiye:,.2f}")

            for row in islem_verileri:
                i_id, i_tarih, i_tip, i_aciklama, i_tutar, i_musteri = row
                if i_tip == "GELEN":
                    bakiye_takip += i_tutar
                else:
                    bakiye_takip -= i_tutar
                
                islem_listesi_tablo.append({
                    "ID": i_id,
                    "TARİH": i_tarih,
                    "TÜR": i_tip,
                    "AÇIKLAMA": i_aciklama,
                    "TUTAR": f"₺{i_tutar:,.2f}",
                    "MÜŞTERİ": i_musteri,
                    "BAKİYE": f"₺{bakiye_takip:,.2f}"
                })

            df_islemler = pd.DataFrame(islem_listesi_tablo)
            st.dataframe(df_islemler, use_container_width=True)

            st.markdown("---")
            sil_id = st.number_input("Silinecek İşlem ID:", min_value=1, step=1, key="islem_sil_id")
            if st.button("İŞLEMİ SİL"):
                conn, cursor = get_db()
                cursor.execute("DELETE FROM islemler WHERE id = ? AND user_id = ?", (sil_id, current_user_id))
                if cursor.rowcount > 0:
                    conn.commit()
                    st.success("İşlem başarıyla silindi!")
                    conn.close()
                    st.rerun()
                else:
                    st.error("Bu ID'ye ait işlem bulunamadı.")
                    conn.close()
        else:
            st.info("Henüz kayıtlı işlem bulunmuyor.")

    # -------------------- MÜŞTERİ/TEDARİKÇİ SEKMESİ --------------------
    with tabs[1]:
        st.subheader("👤 Müşteri / Tedarikçi Ekle")

        col1, col2 = st.columns(2)
        with col1:
            mus_ad = st.text_input("ADI / ŞİRKETİ", key="mus_ad_input").upper()
            mus_tip = st.selectbox("TİP", ["MÜŞTERİ", "TEDARİKÇİ"], key="mus_tip_combo")
            mus_telefon = st.text_input("TELEFON", key="mus_tel_input")
        with col2:
            mus_email = st.text_input("EMAIL", key="mus_email_input").upper()
            mus_adres = st.text_input("ADRES", key="mus_adres_input").upper()

        if st.button("MÜŞTERİ EKLE"):
            if not mus_ad:
                st.warning("AD ALANI ZORUNLUDUR!")
            else:
                try:
                    conn, cursor = get_db()
                    cursor.execute("""
                        INSERT INTO musteriler (user_id, ad, tip, telefon, email, adres)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (current_user_id, mus_ad, mus_tip, mus_telefon, mus_email, mus_adres))
                    conn.commit()
                    conn.close()
                    st.success("MÜŞTERİ EKLENDİ!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("BU İSİM ZATEN KAYITLI!")

        st.divider()
        st.subheader("👥 Kayıtlı Müşteri ve Tedarikçiler")

        conn, cursor = get_db()
        cursor.execute("SELECT id, ad, tip, telefon, email, adres FROM musteriler WHERE user_id = ? ORDER BY ad", (current_user_id,))
        musteriler = cursor.fetchall()
        conn.close()

        if musteriler:
            df_musteriler = pd.DataFrame(musteriler, columns=["ID", "AD", "TİP", "TELEFON", "EMAIL", "ADRES"])
            st.dataframe(df_musteriler, use_container_width=True)

            st.markdown("---")
            sil_mus_id = st.number_input("Silinecek Müşteri ID:", min_value=1, step=1, key="mus_sil_id")
            if st.button("MÜŞTERİ SİL"):
                conn, cursor = get_db()
                cursor.execute("DELETE FROM musteriler WHERE id = ? AND user_id = ?", (sil_mus_id, current_user_id))
                if cursor.rowcount > 0:
                    conn.commit()
                    st.success("Müşteri silindi!")
                    conn.close()
                    st.rerun()
                else:
                    st.error("Bu ID'ye ait müşteri bulunamadı.")
                    conn.close()
        else:
            st.info("Kayıtlı müşteri veya tedarikçi bulunmuyor.")

    # -------------------- RAPORLAR SEKMESİ --------------------
    with tabs[2]:
        st.subheader("📊 Raporlar ve Dışa Aktarım")

        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            rapor_bas = st.date_input("BAŞLANGIÇ", datetime.now(), key="rap_bas_tarih")
        with r_col2:
            rapor_bit = st.date_input("BİTİŞ", datetime.now(), key="rap_bit_tarih")
        with r_col3:
            rapor_turu = st.selectbox(
                "RAPOR TÜRÜ",
                ["ÖZET RAPOR", "MÜŞTERİ RAPORLARI", "TEDARİKÇİ RAPORLARI", "DETAYLI RAPOR"],
                key="rap_tur_combo"
            )

        b_str = rapor_bas.strftime("%Y-%m-%d")
        t_str = rapor_bit.strftime("%Y-%m-%d")

        conn, cursor = get_db()

        if rapor_turu == "ÖZET RAPOR":
            cursor.execute("""
                SELECT tip, COALESCE(SUM(tutar), 0) 
                FROM islemler 
                WHERE user_id = ? AND tarih BETWEEN ? AND ? 
                GROUP BY tip
            """, (current_user_id, b_str, t_str))
            sonuclar = cursor.fetchall()
            
            gelen, giden = 0, 0
            for tip, tutar in sonuclar:
                if tip == "GELEN":
                    gelen = tutar
                elif tip == "GİDEN":
                    giden = tutar

            st.markdown(f"### DÖNEM: {b_str} - {t_str}")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric(label="TOPLAM GELEN", value=f"₺{gelen:,.2f}")
            with mc2:
                st.metric(label="TOPLAM GİDEN", value=f"₺{giden:,.2f}")
            with mc3:
                st.metric(label="NET KAR/ZARAR", value=f"₺{gelen - giden:,.2f}", delta=f"₺{gelen - giden:,.2f}")

        elif rapor_turu in ["MÜŞTERİ RAPORLARI", "TEDARİKÇİ RAPORLARI"]:
            tip_f = "MÜŞTERİ" if rapor_turu == "MÜŞTERİ RAPORLARI" else "TEDARİKÇİ"
            cursor.execute("""
                SELECT m.ad, 
                       COALESCE(SUM(i.tutar), 0),
                       COALESCE(SUM(CASE WHEN i.tip = 'GELEN' THEN i.tutar ELSE 0 END), 0) - 
                       COALESCE(SUM(CASE WHEN i.tip = 'GİDEN' THEN i.tutar ELSE 0 END), 0)
                FROM musteriler m
                JOIN islemler i ON m.id = i.musteri_id AND i.tarih BETWEEN ? AND ? AND i.user_id = ?
                WHERE m.user_id = ? AND m.tip = ?
                GROUP BY m.id
                HAVING COALESCE(SUM(i.tutar), 0) > 0
                ORDER BY m.ad
            """, (b_str, t_str, current_user_id, current_user_id, tip_f))
            data = cursor.fetchall()

            if data:
                df_rap = pd.DataFrame(data, columns=["ADI / ŞİRKET", "TOPLAM TUTAR", "BAKİYE"])
                st.dataframe(df_rap, use_container_width=True)
            else:
                st.info("Bu tarih aralığında kayıt bulunamadı.")

        elif rapor_turu == "DETAYLI RAPOR":
            cursor.execute("""
                SELECT i.tarih, i.tip, i.aciklama, i.tutar, COALESCE(m.ad, '-')
                FROM islemler i
                LEFT JOIN musteriler m ON i.musteri_id = m.id
                WHERE i.user_id = ? AND i.tarih BETWEEN ? AND ?
                ORDER BY i.tarih DESC, i.id DESC
            """, (current_user_id, b_str, t_str))
            data = cursor.fetchall()

            if data:
                df_detay = pd.DataFrame(data, columns=["TARİH", "TÜR", "AÇIKLAMA", "TUTAR", "MÜŞTERİ"])
                st.dataframe(df_detay, use_container_width=True)
            else:
                st.info("Bu tarih aralığında detay bulunamadı.")

        conn.close()

    # -------------------- YÖNETİCİ PANELİ SEKMESİ (Sadece Admin Görebilir) --------------------
    if is_admin:
        with tabs[3]:
            st.subheader("👑 Sistem Yönetici Paneli")
            st.info("Bu paneli yalnızca sistem yöneticisi (sen) görüntüleyebilir.")

            conn, cursor = get_db()
            # Toplam kullanıcı sayısı
            cursor.execute("SELECT COUNT(*) FROM kullanicilar")
            toplam_kullanici = cursor.fetchone()[0]

            # Toplam işlem sayısı
            cursor.execute("SELECT COUNT(*) FROM islemler")
            toplam_islem = cursor.fetchone()[0]
            conn.close()

            sc1, sc2 = st.columns(2)
            with sc1:
                st.metric(label="Toplam Kayıtlı Kullanıcı", value=toplam_kullanici)
            with sc2:
                st.metric(label="Sistemdeki Toplam İşlem", value=toplam_islem)

            st.divider()
            st.subheader("📋 Kayıtlı Tüm Kullanıcılar Listesi")

            conn, cursor = get_db()
            cursor.execute("SELECT id, email FROM kullanicilar ORDER BY id ASC")
            tum_kullanicilar = cursor.fetchall()
            conn.close()

            if tum_kullanicilar:
                df_kull = pd.DataFrame(tum_kullanicilar, columns=["Kullanıcı ID", "E-Posta Adresi"])
                st.dataframe(df_kull, use_container_width=True)

                st.markdown("---")
                st.write("⚠️ **Kullanıcı Yönetimi / Silme**")
                silinecek_kull_id = st.number_input("Silmek istediğiniz Kullanıcı ID:", min_value=1, step=1, key="admin_sil_kull_id")
                
                if st.button("KULLANICIYI VE TÜM VERİLERİNİ SİL"):
                    if silinecek_kull_id == current_user_id:
                        st.error("Kendi yönetici hesabınızı bu alandan silemezsiniz!")
                    else:
                        conn, cursor = get_db()
                        # Önce kullanıcının verilerini, müşterilerini ve hesabını silelim
                        cursor.execute("DELETE FROM islemler WHERE user_id = ?", (silinecek_kull_id,))
                        cursor.execute("DELETE FROM musteriler WHERE user_id = ?", (silinecek_kull_id,))
                        cursor.execute("DELETE FROM kullanicilar WHERE id = ?", (silinecek_kull_id,))
                        
                        if cursor.rowcount > 0:
                            conn.commit()
                            conn.close()
                            st.success(f"{silinecek_kull_id} ID'li kullanıcı ve tüm verileri tamamen silindi!")
                            st.rerun()
                        else:
                            conn.close()
                            st.error("Bu ID'ye ait kullanıcı bulunamadı.")
            else:
                st.info("Sistemde henüz kayıtlı kullanıcı yok.")
