from datetime import datetime
import os
import sqlite3
import hashlib
from io import BytesIO
import pandas as pd
import streamlit as st

# Sayfa Ayarları
st.set_page_config(
    page_title="Online Muhasebe Programı", page_icon="💰", layout="wide"
)

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
  
  # Müşteriler Tablosu (Kullanıcıya özel user_id eklendi)
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
  
  # İşlemler Tablosu (Kullanıcıya özel user_id eklendi)
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

# Oturum Durumu (Session State) Kontrolü
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.session_state["email"] = None

# ---------------------------------------------------------
# GİRİŞ / KAYIT EKRANI (Eğer giriş yapılmadıysa)
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
                st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.error("Hatalı e-posta veya şifre!")

# ---------------------------------------------------------
# ANA UYGULAMA (Giriş yapıldıysa)
# ---------------------------------------------------------
else:
    current_user_id = st.session_state["user_id"]
    
    # Üst Bilgi ve Çıkış Yap Butonu
    col_baslik, col_cikis = st.columns([5, 1])
    with col_baslik:
        st.title(f"💰 Online Muhasebe Programı")
        st.caption(f"Aktif Hesap: **{st.session_state['email']}**")
    with col_cikis:
        if st.button("Çıkış Yap"):
            st.session_state["logged_in"] = False
            st.session_state["user_id"] = None
            st.session_state["email"] = None
            st.rerun()

    st.divider()

    # Sekmeler (Tabs)
    tab1, tab2, tab3 = st.tabs(["İŞLEMLER", "MÜŞTERİ / TEDARİKÇİ", "RAPORLAR"])

    # -------------------- İŞLEMLER SEKMESİ --------------------
    with tab1:
      st.subheader("Yeni İşlem Ekle")

      conn, cursor = get_db()
      # Sadece bu kullanıcıya ait müşterileri getir
      cursor.execute("SELECT id, ad FROM musteriler WHERE user_id = ? ORDER BY ad", (current_user_id,))
      musteriler = cursor.fetchall()
      conn.close()

      musteri_dict = {"SEÇİLMEMİŞ": None}
      for m_id, m_ad in musteriler:
        musteri_dict[m_ad.upper()] = m_id

      col1, col2, col3, col4 = st.columns(4)
      with col1:
        islem_tarihi = st.date_input("Tarih", datetime.now())
      with col2:
        islem_tipi = st.selectbox("Tür", ["GELEN", "GİDEN"])
      with col3:
        secilen_musteri = st.selectbox(
            "Müşteri / Tedarikçi", list(musteri_dict.keys()), key="islem_mus_select"
        )
      with col4:
        islem_tutar = st.number_input(
            "Tutar (₺)", min_value=0.0, format="%.2f", step=10.0
        )

      islem_aciklama = st.text_input("Açıklama", key="islem_aciklama_input").upper()

      if st.button("İŞLEMİ EKLE"):
        if not islem_aciklama:
          st.warning("Lütfen açıklama girin!")
        elif islem_tutar <= 0:
          st.warning("Tutar sıfırdan büyük olmalıdır!")
        else:
          conn, cursor = get_db()
          m_id = musteri_dict[secilen_musteri]
          cursor.execute(
              """
                    INSERT INTO islemler (user_id, tarih, tip, aciklama, tutar, musteri_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
              (
                  current_user_id,
                  islem_tarihi.strftime("%Y-%m-%d"),
                  islem_tipi,
                  islem_aciklama,
                  islem_tutar,
                  m_id,
              ),
          )
          conn.commit()
          conn.close()
          st.success("İşlem başarıyla eklendi!")
          st.rerun()

      st.divider()
      st.subheader("Kayıtlı İşlemler Listesi")

      conn, cursor = get_db()
      # Sadece bu kullanıcıya ait işlemleri getir
      cursor.execute("""
            SELECT i.id, i.tarih, i.tip, i.aciklama, i.tutar, COALESCE(m.ad, '-') 
            FROM islemler i 
            LEFT JOIN musteriler m ON i.musteri_id = m.id 
            WHERE i.user_id = ?
            ORDER BY i.tarih DESC, i.id DESC
        """, (current_user_id,))
      islem_verileri = cursor.fetchall()
      conn.close()

      if islem_verileri:
        df_islemler = pd.DataFrame(
            islem_verileri,
            columns=["ID", "Tarih", "Tür", "Açıklama", "Tutar", "Müşteri"],
        )
        st.dataframe(df_islemler, use_container_width=True)
      else:
        st.info("Henüz kayıtlı işlem bulunmuyor.")

    # -------------------- MÜŞTERİ / TEDARİKÇİ SEKMESİ --------------------
    with tab2:
      st.subheader("Müşteri veya Tedarikçi Ekle")

      col1, col2 = st.columns(2)
      with col1:
        mus_ad = st.text_input("Adı / Şirket Adı", key="mus_ad_input").upper()
        mus_tip = st.selectbox("Tip", ["MÜŞTERİ", "TEDARİKÇİ"], key="mus_tip_select")
        mus_tel = st.text_input("Telefon", key="mus_tel_input")
      with col2:
        mus_email = st.text_input("E-Mail", key="mus_email_input").upper()
        mus_adres = st.text_input("Adres", key="mus_adres_input").upper()

      if st.button("MÜŞTERİYİ KAYDET"):
        if not mus_ad:
          st.warning("Ad alanı zorunludur!")
        else:
          try:
            conn, cursor = get_db()
            cursor.execute(
                """
                        INSERT INTO musteriler (user_id, ad, tip, telefon, email, adres)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                (current_user_id, mus_ad, mus_tip, mus_tel, mus_email, mus_adres),
            )
            conn.commit()
            conn.close()
            st.success("Müşteri/Tedarikçi eklendi!")
            st.rerun()
          except sqlite3.IntegrityError:
            st.error("Bu isimde bir müşteri zaten kayıtlı!")

      st.divider()
      st.subheader("Kayıtlı Müşteri ve Tedarikçiler")
      conn, cursor = get_db()
      cursor.execute("SELECT id, ad, tip, telefon, email, adres FROM musteriler WHERE user_id = ? ORDER BY ad", (current_user_id,))
      mus_verileri = cursor.fetchall()
      conn.close()

      if mus_verileri:
        df_mus = pd.DataFrame(
            mus_verileri, columns=["ID", "Ad", "Tip", "Telefon", "E-Mail", "Adres"]
        )
        st.dataframe(df_mus, use_container_width=True)
      else:
        st.info("Kayıtlı müşteri yok.")

    # -------------------- RAPORLAR SEKMESİ --------------------
    with tab3:
      st.subheader("Raporlama ve Filtreleme")

      col1, col2, col3 = st.columns(3)
      with col1:
         rapor_bas = st.date_input("Rapor Başlangıç", datetime.now(), key="rap_bas")
      with col2:
        rapor_bit = st.date_input("Rapor Bitiş", datetime.now(), key="rap_bit")
      with col3:
        rapor_turu = st.selectbox(
            "Rapor Türü",
            ["ÖZET RAPOR", "MÜŞTERİ RAPORLARI", "TEDARİKÇİ RAPORLARI", "DETAYLI RAPOR"],
            key="rap_tur"
        )

      b_str = rapor_bas.strftime("%Y-%m-%d")
      t_str = rapor_bit.strftime("%Y-%m-%d")

      conn, cursor = get_db()

      if rapor_turu == "ÖZET RAPOR":
        cursor.execute(
            """
                SELECT tip, COALESCE(SUM(tutar), 0) FROM islemler 
                WHERE user_id = ? AND tarih BETWEEN ? AND ? GROUP BY tip
            """,
            (current_user_id, b_str, t_str),
        )
        res = cursor.fetchall()
        gelen, giden = 0, 0
        for tip, tutar in res:
          if tip == "GELEN":
            gelen = tutar
          elif tip == "GİDEN":
            giden = tutar

        st.markdown(f"### Dönem: {b_str} - {t_str}")
        st.metric(label="Toplam Gelen", value=f"₺{gelen:,.2f}")
        st.metric(label="Toplam Giden", value=f"₺{giden:,.2f}")
        st.metric(
            label="Net Kar / Zarar",
            value=f"₺{gelen - giden:,.2f}",
            delta=f"₺{gelen - giden:,.2f}",
        )

      elif rapor_turu in ["MÜŞTERİ RAPORLARI", "TEDARİKÇİ RAPORLARI"]:
        tip_filtre = "MÜŞTERİ" if rapor_turu == "MÜŞTERİ RAPORLARI" else "TEDARİKÇİ"
        cursor.execute(
            """
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
            """,
            (b_str, t_str, current_user_id, current_user_id, tip_filtre),
        )
        data = cursor.fetchall()
        if data:
          df_r = pd.DataFrame(data, columns=["Adı / Şirket", "Toplam Tutar", "Bakiye"])
          st.dataframe(df_r, use_container_width=True)
        else:
          st.info("Bu tarih aralığında kayıt bulunamadı.")

      elif rapor_turu == "DETAYLI RAPOR":
        cursor.execute(
            """
                SELECT i.tarih, i.tip, i.aciklama, i.tutar, COALESCE(m.ad, '-')
                FROM islemler i
                LEFT JOIN musteriler m ON i.musteri_id = m.id
                WHERE i.user_id = ? AND i.tarih BETWEEN ? AND ?
                ORDER BY i.tarih DESC
            """,
            (current_user_id, b_str, t_str),
        )
        data = cursor.fetchall()
        if data:
          df_d = pd.DataFrame(
              data, columns=["Tarih", "Tür", "Açıklama", "Tutar", "Müşteri"]
          )
          st.dataframe(df_d, use_container_width=True)
        else:
          st.info("Bu tarih aralığında detay bulunamadı.")

      conn.close()
