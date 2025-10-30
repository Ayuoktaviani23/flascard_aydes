import streamlit as st
import pandas as pd
import random
from time import sleep

# ========================
# 🔧 Konfigurasi Awal
# ========================
st.set_page_config(page_title="Belajar Kosakata Jepang", page_icon="🇯🇵", layout="centered")

# ========================
# 🎨 CSS Biar Menarik
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

df = df.fillna("")

# ========================
# 🔁 State untuk Progress
# ========================
if "index" not in st.session_state:
    st.session_state.index = 0
if "hafal" not in st.session_state:
    st.session_state.hafal = []

# ========================
# ⚙️ Pengaturan Tampilan
# ========================
st.sidebar.header("⚙️ Pengaturan Tampilan")
show_romaji = st.sidebar.checkbox("Tampilkan Romaji", value=True)
show_meaning = st.sidebar.checkbox("Tampilkan Arti (🇮🇩 & 🇬🇧)", value=True)
st.sidebar.divider()
st.sidebar.caption("Tips: Sembunyikan arti & romaji untuk latihan hafalan!")

# ========================
# 🔀 Fungsi Ambil Kata
# ========================
def next_word():
    total = len(df)
    if len(st.session_state.hafal) == total:
        st.success("🎉 Semua kata sudah kamu pelajari! Keren banget!")
        return None

    remaining = df[~df.index.isin(st.session_state.hafal)]
    row = remaining.sample(1).iloc[0]
    st.session_state.index = row.name
    return row

# ========================
# 🚀 Tampilkan Kartu Kata
# ========================
word = df.iloc[st.session_state.index]

st.markdown(f"""
<div class="word-card">
    <div class="category">📚 {word['kategori'].title()}</div>
    <div class="kanji">{word['kanji']}</div>
    <div class="kana">{word['hiragana']}　{word['katakana']}</div>
</div>
""", unsafe_allow_html=True)

# Romaji
if show_romaji:
    st.markdown(f"<div class='romaji'>({word['romaji']})</div>", unsafe_allow_html=True)

# Arti
if show_meaning:
    st.markdown(f"<div class='meaning'>🇮🇩 {word['indo']}<br>🇬🇧 {word['eng']}</div>", unsafe_allow_html=True)

# ========================
# 🔘 Tombol Interaktif
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
# 📊 Statistik Belajar
# ========================
progress = len(st.session_state.hafal) / len(df)
st.progress(progress)
st.caption(f"Hafalan: {len(st.session_state.hafal)} dari {len(df)} kosakata")

# ========================
# 🌸 Motivasi Acak
# ========================
motivasi = [
    "💪 Semangat! Sedikit lagi kamu jago bahasa Jepang!",
    "🌸 Ganbatte! Setiap hari tambah pintar!",
    "🚀 Hebat! Terus lanjut, jangan menyerah!",
    "🔥 Mantap! Kamu sudah selangkah lebih dekat ke fasih!",
    "🍀 Belajar dengan senyum bikin hafalan makin kuat!",
]
st.info(random.choice(motivasi))
