import streamlit as st
import pandas as pd
import random
from time import sleep

# ========================
# 🔧 Konfigurasi awal
# ========================
st.set_page_config(page_title="Belajar Kosakata Jepang", page_icon="🇯🇵", layout="centered")

# ========================
# 🎨 Gaya CSS biar menarik
# ========================
st.markdown("""
<style>
    body { background: linear-gradient(135deg, #f0f7ff 0%, #c2e9fb 100%); }
    .word-card {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.2s ease-in-out;
    }
    .word-card:hover { transform: scale(1.03); }
    .kanji { font-size: 70px; font-weight: bold; color: #1a73e8; }
    .kana { font-size: 30px; color: #333; }
    .romaji { font-size: 22px; color: #555; margin-bottom: 10px; }
    .meaning { font-size: 20px; margin-top: 15px; }
    .category { font-size: 16px; color: gray; }
    .stButton button {
        border-radius: 10px;
        font-size: 20px;
        padding: 10px 20px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# 📘 Load Dataset
# ========================
DATA_FILE = "Book4.csv"

try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    st.error(f"File `{DATA_FILE}` tidak ditemukan. Pastikan file CSV-nya ada di folder yang sama.")
    st.stop()

# Bersihkan kolom kosong
df = df.fillna("")

# ========================
# 🔁 State untuk progress
# ========================
if "index" not in st.session_state:
    st.session_state.index = 0
if "hafal" not in st.session_state:
    st.session_state.hafal = []

# ========================
# 🔀 Fungsi ambil kata
# ========================
def next_word():
    total = len(df)
    if len(st.session_state.hafal) == total:
        st.success("🎉 Semua kata sudah kamu pelajari! Hebat banget!")
        return None

    # Pilih random dari kata yang belum dihafal
    remaining = df[~df.index.isin(st.session_state.hafal)]
    row = remaining.sample(1).iloc[0]
    st.session_state.index = row.name
    return row

# ========================
# 🚀 Tampilkan kartu kata
# ========================
word = df.iloc[st.session_state.index]

st.markdown(f"""
<div class="word-card">
    <div class="category">📚 {word['kategori'].title()}</div>
    <div class="kanji">{word['kanji']}</div>
    <div class="kana">{word['hiragana']}　{word['katakana']}</div>
    <div class="romaji">({word['romaji']})</div>
    <div class="meaning">🇮🇩 {word['indo']}<br>🇬🇧 {word['eng']}</div>
</div>
""", unsafe_allow_html=True)

# ========================
# 🔘 Tombol interaktif
# ========================
col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Saya Hafal!"):
        st.session_state.hafal.append(st.session_state.index)
        word = next_word()
        if word is not None:
            sleep(0.5)
            st.rerun()

with col2:
    if st.button("⏭️ Belum Hafal / Lanjut"):
        word = next_word()
        if word is not None:
            sleep(0.5)
            st.rerun()

# ========================
# 📊 Statistik belajar
# ========================
st.progress(len(st.session_state.hafal) / len(df))
st.caption(f"Hafalan: {len(st.session_state.hafal)} dari {len(df)} kosakata")

# ========================
# 🎵 Motivasi tambahan
# ========================
motivasi = [
    "💪 Semangat! Sedikit lagi kamu jago bahasa Jepang!",
    "🌸 Ganbatte! Setiap hari tambah pintar!",
    "🚀 Hebat! Terus lanjut, jangan menyerah!",
    "🔥 Mantap! Kamu sudah selangkah lebih dekat ke fasih!",
]
st.info(random.choice(motivasi))
