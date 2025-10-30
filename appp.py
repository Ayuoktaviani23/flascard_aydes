# app.py
import streamlit as st
import pandas as pd
import random
import io
import re
from textwrap import dedent
from difflib import SequenceMatcher
import time

# ---------- Config ----------
st.set_page_config(page_title="Flashcard Jepang Inggris — Fun Mode 🎌", layout="wide")
st.markdown("Jika ada eror atau request tambah kosakata bisa hubungi nomor WA di bawah")
DATA_PATH = "Book4.csv"
WA_NUMBER = "6285780648970"

# ---------- Utility helpers ----------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    required = {"kategori","kanji","hiragana","katakana","romaji","indo","eng","tipe","catatan"}
    for col in required:
        if col not in df.columns:
            df[col] = ""
    df = df.fillna("")
    df["kategori_list"] = df["kategori"].astype(str).apply(lambda s: [x.strip() for x in s.split(",") if x.strip()])
    return df

def normalize_text(s: str) -> str:
    if s is None: return ""
    s = str(s)
    s = s.replace("。", ".").replace("、", ",").replace("！", "!").replace("？", "?")
    s = re.sub(r"[^\w\s\u3040-\u30ff\-']", " ", s, flags=re.UNICODE)
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def build_index(df: pd.DataFrame, selected_cats, query, random_order):
    if selected_cats and "Semua" not in selected_cats:
        mask = df["kategori_list"].apply(lambda lst: any(c in selected_cats for c in lst))
        filt = df[mask]
    else:
        filt = df
    if query:
        q = query.strip().lower()
        filt = filt[filt.apply(lambda r: 
                               q in str(r["hiragana"]).lower() 
                            or q in str(r["katakana"]).lower()
                            or q in str(r["romaji"]).lower() 
                            or q in str(r["indo"]).lower()
                            or q in str(r["eng"]).lower(), axis=1)]
    idx = list(filt.index)
    if random_order:
        random.shuffle(idx)
    return idx, filt

def ensure_session():
    defaults = {
        "idx_list": [], "pos": 0, "score": 0, "attempts": 0,
        "favorites": set(), "ui_style": "Keren",
        "last_filter": None, "memorized": {}, 
        "motivation": 0, "level": 1
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# ---------- Load dataset ----------
try:
    df = load_data(DATA_PATH)
except Exception as e:
    st.error(str(e))
    st.stop()

ensure_session()

# ---------- Sidebar ----------
with st.sidebar:
    st.title("⚙️ Kontrol — Flashcard Jepang")
    all_cats = sorted({c for cats in df["kategori_list"] for c in cats})
    selected = st.multiselect("Pilih kategori:", ["Semua"] + all_cats, default=["Semua"])
    order_random = st.checkbox("Acak urutan", value=True)
    show_romaji = st.checkbox("Tampilkan Romaji", value=True)
    focus_unmemorized = st.checkbox("Fokus hanya belum hafal", value=False)
    st.markdown("---")
    ui_mode = st.radio("Mode:", ["Belajar Santai ☕", "Quiz (MCQ)"])
    st.markdown("---")
    st.caption(f"💬 Kritik & saran: [wa.me/{WA_NUMBER}](https://wa.me/{WA_NUMBER})")

# ---------- Data filtering ----------
idx_list, filtered_df = build_index(df, selected, "", random_order=order_random)
if focus_unmemorized:
    idx_list = [i for i in idx_list if st.session_state["memorized"].get(i, "belum") == "belum"]
total = len(idx_list)
if total == 0:
    st.warning("Tidak ada data untuk kategori ini.")
    st.stop()

# ---------- Header ----------
st.markdown(f"<h1 style='text-align:center;'>🎴 Belajar Kosakata Jepang — Anti Ngantuk!</h1>", unsafe_allow_html=True)
st.caption(f"Total {total} kosakata | Level: {st.session_state['level']} | Poin: {st.session_state['score']}")

# ---------- Card ----------
current_idx = idx_list[st.session_state["pos"]]
row = df.loc[current_idx]
kanji = row["kanji"]
hiragana = row["hiragana"]
romaji = row["romaji"]
indo = row["indo"]
eng = row["eng"]

colors = ["#FFF4E6", "#E0F7FA", "#F3E5F5", "#E8F5E9", "#FFF9C4"]
bg = random.choice(colors)

st.markdown(
    f"""
    <div style='background:{bg};padding:35px;border-radius:16px;text-align:center;
    box-shadow:0 4px 12px rgba(0,0,0,0.1);'>
    <h2 style='font-size:48px'>{kanji if kanji else hiragana}</h2>
    <p style='font-size:20px;color:#666;'>({romaji})</p>
    <h3 style='color:#00796B;'>👉 {indo}</h3>
    <p style='color:#999;'>{eng}</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- Buttons ----------
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Sudah Hafal!"):
        st.session_state["memorized"][current_idx] = "sudah"
        st.session_state["score"] += 10
        st.session_state["level"] = 1 + st.session_state["score"] // 50
        st.balloons()
        st.success(random.choice([
            "Kamu luar biasa 💪", 
            "Teruskan semangatnya! 🔥", 
            "Mantap! Kosakatamu makin kuat!", 
            "Hebat! Nihongo jouzu desu 🌸"
        ]))
        time.sleep(1)
        st.session_state["pos"] = (st.session_state["pos"] + 1) % total
        st.rerun()
with col2:
    if st.button("❌ Belum Hafal"):
        st.session_state["memorized"][current_idx] = "belum"
        st.info("Gak apa, lanjut ke kata lain dulu 😎")
        time.sleep(1)
        st.session_state["pos"] = (st.session_state["pos"] + 1) % total
        st.rerun()

# ---------- Motivasi tiap 5 kata ----------
st.session_state["motivation"] += 1
if st.session_state["motivation"] % 5 == 0:
    st.success(random.choice([
        "🌸 Nihongo wa tanoshii desu! (Bahasa Jepang itu menyenangkan!)",
        "🚀 Kamu makin cepat belajar hari ini!",
        "🔥 Luar biasa! Jangan berhenti di sini!",
        "💫 Hafalanmu makin tajam! Terus lanjut!"
    ]))

# ---------- Progress bar ----------
progress = len([v for v in st.session_state["memorized"].values() if v == "sudah"])
st.progress(progress / max(1, total))
st.caption(f"Progress hafalan: {progress}/{total} ({progress/total*100:.1f}%)")

# ---------- Download progress ----------
mem_df = pd.DataFrame([
    {"index": k, "kata": df.loc[k, "hiragana"], "arti": df.loc[k, "indo"], "status": v}
    for k, v in st.session_state["memorized"].items()
])
if not mem_df.empty:
    buf = io.StringIO()
    mem_df.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("📘 Download Progress Hafalan", buf.getvalue().encode("utf-8-sig"), "progress.csv")

# ---------- Footer ----------
st.markdown("<hr>", unsafe_allow_html=True)
st.info(f"Hubungi admin via WhatsApp: [wa.me/{WA_NUMBER}](https://wa.me/{WA_NUMBER})")
