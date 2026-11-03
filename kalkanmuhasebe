from datetime import datetime
import os
import sqlite3
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import streamlit as st

# Sayfa Ayarları
st.set_page_config(
    page_title="Online Muhasebe Programı", page_icon="💰", layout="wide"
)


# Veritabanı Başlatma
def init_db():
  conn = sqlite3.connect("muhasebe.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY,
            ad TEXT UNIQUE,
            tip TEXT,
            telefon TEXT,
            email TEXT,
            adres TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS islemler (
            id INTEGER PRIMARY KEY,
            tarih TEXT,
            tip TEXT,
            aciklama TEXT,
            tutar REAL,
            musteri_id INTEGER,
            FOREIGN KEY(musteri_id) REFERENCES musteriler(id)
        )
    """)
  conn.commit()
  conn.close()


init_db()


def get_db():
  conn = sqlite3.connect("muhasebe.db")
  return conn, conn.cursor()


st.title("💰 Online Muhasebe Programı V1.0")

# Sekmeler (Tabs)
tab1, tab2, tab3 = st.tabs(["İŞLEMLER", "MÜŞTERİ / TEDARİKÇİ", "RAPORLAR"])

# -------------------- İŞLEMLER SEKMESİ --------------------
with tab1:
  st.subheader("Yeni İşlem Ekle")

  conn, cursor = get_db()
  cursor.execute("SELECT id, ad FROM musteriler ORDER BY ad")
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
        "Müşteri / Tedarikçi", list(musteri_dict.keys())
    )
  with col4:
    islem_tutar = st.number_input(
        "Tutar (₺)", min_value=0.0, format="%.2f", step=10.0
    )

  islem_aciklama = st.text_input("Açıklama").upper()

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
                INSERT INTO islemler (tarih, tip, aciklama, tutar, musteri_id)
                VALUES (?, ?, ?, ?, ?)
            """,
          (
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
  cursor.execute("""
        SELECT i.id, i.tarih, i.tip, i.aciklama, i.tutar, COALESCE(m.ad, '-') 
        FROM islemler i 
        LEFT JOIN musteriler m ON i.musteri_id = m.id 
        ORDER BY i.tarih DESC, i.id DESC
    """)
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
    mus_ad = st.text_input("Adı / Şirket Adı").upper()
    mus_tip = st.selectbox("Tip", ["MÜŞTERİ", "TEDARİKÇİ"])
    mus_tel = st.text_input("Telefon")
  with col2:
    mus_email = st.text_input("E-Mail").upper()
    mus_adres = st.text_input("Adres").upper()

  if st.button("MÜŞTERİYİ KAYDET"):
    if not mus_ad:
      st.warning("Ad alanı zorunludur!")
    else:
      try:
        conn, cursor = get_db()
        cursor.execute(
            """
                    INSERT INTO musteriler (ad, tip, telefon, email, adres)
                    VALUES (?, ?, ?, ?, ?)
                """,
            (mus_ad, mus_tip, mus_tel, mus_email, mus_adres),
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
  cursor.execute("SELECT id, ad, tip, telefon, email, adres FROM musteriler ORDER BY ad")
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
     rapor_bas = st.date_input("Rapor Başlangıç", datetime.now())
  with col2:
    rapor_bit = st.date_input("Rapor Bitiş", datetime.now())
  with col3:
    rapor_turu = st.selectbox(
        "Rapor Türü",
        ["ÖZET RAPOR", "MÜŞTERİ RAPORLARI", "TEDARİKÇİ RAPORLARI", "DETAYLI RAPOR"],
    )

  b_str = rapor_bas.strftime("%Y-%m-%d")
  t_str = rapor_bit.strftime("%Y-%m-%d")

  conn, cursor = get_db()

  if rapor_turu == "ÖZET RAPOR":
    cursor.execute(
        """
            SELECT tip, COALESCE(SUM(tutar), 0) FROM islemler 
            WHERE tarih BETWEEN ? AND ? GROUP BY tip
        """,
        (b_str, t_str),
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
            JOIN islemler i ON m.id = i.musteri_id AND i.tarih BETWEEN ? AND ?
            WHERE m.tip = ?
            GROUP BY m.id
            HAVING COALESCE(SUM(i.tutar), 0) > 0
            ORDER BY m.ad
        """,
        (b_str, t_str, tip_filtre),
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
            WHERE i.tarih BETWEEN ? AND ?
            ORDER BY i.tarih DESC
        """,
        (b_str, t_str),
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
