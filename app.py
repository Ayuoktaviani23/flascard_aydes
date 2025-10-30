# app.py
import streamlit as st
import pandas as pd
import random
import io
import re
from textwrap import dedent
from difflib import SequenceMatcher

# ---------- Config ----------
st.set_page_config(page_title="Flashcard Jepang Inggris — Flashcard & Quiz", layout="wide")
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

def normalize_japanese_kana(s: str) -> str:
    if s is None: return ""
    s = str(s).replace("　","")
    s = re.sub(r"[^\u3040-\u30ff\w\s\-']", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "", s).strip()
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
    for key, val in [("idx_list", []), ("pos",0), ("score",0), ("attempts",0),
                     ("favorites", set()), ("ui_style","Sederhana"),
                     ("last_filter", None), ("sim_sum",0.0), ("sim_count",0), ("history", []),
                     ("mcq_choices_dict", {})]:
        if key not in st.session_state:
            st.session_state[key] = val

# ---------- Load dataset ----------
try:
    df = load_data(DATA_PATH)
except Exception as e:
    st.error(str(e))
    st.stop()

ensure_session()

# --- Memorization status ---
if "memorized" not in st.session_state:
    st.session_state["memorized"] = {}  # key=index, value="sudah"/"belum"

# ---------- Sidebar ----------
with st.sidebar:
    st.title("Kontrol — Flashcard Jepang")
    all_cats = sorted({c for cats in df["kategori_list"] for c in cats})
    cat_options = ["Semua"] + all_cats
    selected = st.multiselect("Pilih kategori (multi):", options=cat_options, default=["Semua"])
    mode = st.radio("Mode Belajar:", ("Flashcard", "Quiz (MCQ)", "Ketik Jawaban"))
    direction = st.radio("Mode tampilan:", ("Hiragana → Indo", "Romaji → Indo", "Indo → Hiragana"))
    show_romaji = st.checkbox("Tampilkan Romaji", value=True)
    order_random = st.checkbox("Acak urutan saat mulai", value=True)
    st.markdown("---")
    mcq_choices = st.slider("Pilihan pada MCQ", 2, 6, 4)
    st.markdown("---")
    fuzz_threshold = st.slider("Ambang terima (similarity %) ≥", 50, 100, 80)
    typing_flex = st.checkbox("Flexible check (ignore case/punct)", value=True)
    st.markdown("---")
    ui_style = st.radio("Gaya UI:", ("Sederhana (cepat)", "Keren (flip card)"))
    st.session_state["ui_style"] = "Sederhana" if ui_style.startswith("Sederhana") else "Keren"
    st.markdown("---")
    q = st.text_input("Cari (hiragana / katakana / romaji / indo / eng):")
    focus_unmemorized = st.checkbox("Fokuskan hanya kata belum hafal", value=False)
    st.markdown("---")
    st.caption("Favorit dan hafalan disimpan sementara di session browser. Export tersedia.")

# ---------- Rebuild filtered index ----------
current_filter = (tuple(selected), q, order_random, mode, direction, mcq_choices, typing_flex, fuzz_threshold, focus_unmemorized)
if st.session_state["last_filter"] != current_filter:
    idx_list, filtered_df = build_index(df, selected, q, random_order=order_random)
    if focus_unmemorized:
        unmem = [i for i in idx_list if st.session_state["memorized"].get(i, "belum") == "belum"]
        idx_list = unmem
    st.session_state["idx_list"] = idx_list
    st.session_state["pos"] = 0
    st.session_state["last_filter"] = current_filter
else:
    idx_list = st.session_state["idx_list"]
    try:
        filtered_df
    except NameError:
        _, filtered_df = build_index(df, selected, q, random_order=order_random)

total = len(idx_list)
if total == 0:
    st.warning("Tidak ada kata untuk filter / pencarian.")
    st.stop()

# ---------- Header ----------
st.title("🈂️ Flashcard Bahasa Jepang — Flashcard, MCQ & Typing")
col1, col2, col3 = st.columns([2,4,2])
with col1:
    st.markdown(f"**Total:** {total}")
    st.markdown(f"**Kategori aktif:** {', '.join(selected) if selected else 'Semua'}")
    attempts = st.session_state["attempts"]
    score = st.session_state["score"]
    avg_sim = (st.session_state["sim_sum"]/st.session_state["sim_count"]*100) if st.session_state["sim_count"]>0 else 0.0
    acc_pct = (score/attempts*100) if attempts>0 else 0.0
    st.markdown(f"**Skor:** {score}/{attempts} • Akurasi: {acc_pct:.1f}% • Avg similarity: {avg_sim:.1f}%")
with col2:
    pos = st.slider("Posisi kartu:", 1, max(1,total), value=st.session_state["pos"]+1)-1
    st.session_state["pos"] = pos
with col3:
    if st.button("Acak ulang"):
        st.session_state["idx_list"], _ = build_index(df, selected, q, random_order=True)
        st.session_state["pos"] = 0
        st.rerun()
    if st.button("Reset skor"):
        for key in ["score","attempts","sim_sum","sim_count","history","mcq_choices_dict"]:
            st.session_state[key] = 0 if key in ["score","attempts"] else ([] if key!="mcq_choices_dict" else {})
        st.rerun()

# ---------- Current card ----------
current_idx = idx_list[st.session_state["pos"]]
card = df.loc[current_idx]

if direction == "Hiragana → Indo":
    front = card["hiragana"] if card["hiragana"] else (card["katakana"] or card["romaji"])
    back = card["indo"]
elif direction == "Romaji → Indo":
    front = card["romaji"]
    back = card["indo"]
else:  # Indo → Hiragana
    front = card["indo"]
    back = card["hiragana"] if card["hiragana"] else card["katakana"]

# ---------- UI ----------
def simple_card_display(front_text, back_text):
    if card["kanji"]:
        st.markdown(f"## 🈶 Kanji: {card['kanji']}")
    st.markdown(f"### {front_text}")
    if show_romaji and direction != "Romaji → Indo":
        st.caption(f"Romaji: {card['romaji']}")
    if st.button("Tampilkan jawaban"):
        st.success(f"Jawaban: **{back_text}** 🎉")

def fancy_css():
    return dedent("""
    <style>
    .card-wrap { perspective: 1000px; margin-bottom: 10px; }
    .card { width:100%; max-width:800px; height:240px; border-radius:12px; box-shadow:0 6px 18px rgba(0,0,0,0.12);
            display:flex; align-items:center; justify-content:center; flex-direction:column; padding:24px; }
    .card-front { background: linear-gradient(120deg,#fef3c7,#fde68a); }
    .card-back { background: linear-gradient(120deg,#bfdbfe,#93c5fd); }
    .big { font-size:36px; font-weight:700; }
    .small { font-size:14px; opacity:0.9; margin-top:8px; }
    </style>
    """)

def fancy_card_display(front_text, back_text):
    st.markdown(fancy_css(), unsafe_allow_html=True)
    kanji_html = f"<div class='small'>Kanji: {card['kanji']}</div>" if card["kanji"] else ""
    if st.session_state.get("flipped_card", False):
        st.markdown(f'<div class="card card-back"><div class="big">{back_text}</div><div class="small">{"Romaji: "+card["romaji"] if show_romaji else ""}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="card card-front">{kanji_html}<div class="big">{front_text}</div><div class="small">{"Romaji: "+card["romaji"] if show_romaji else ""}</div></div>', unsafe_allow_html=True)
    b1,b2,b3 = st.columns([1,1,1])
    with b1:
        if st.button("Flip"): st.session_state["flipped_card"] = not st.session_state.get("flipped_card", False); st.rerun()
    with b2:
        if st.button("Prev") and st.session_state["pos"]>0: st.session_state["pos"]-=1; st.session_state["flipped_card"]=False; st.rerun()
    with b3:
        if st.button("Next") and st.session_state["pos"]<total-1: st.session_state["pos"]+=1; st.session_state["flipped_card"]=False; st.rerun()

col_main, col_side = st.columns([3,1])
with col_main:
    if st.session_state["ui_style"]=="Sederhana": simple_card_display(front, back)
    else: fancy_card_display(front, back)

# --- Tombol hafalan ---
st.markdown("---")
col_h1, col_h2 = st.columns(2)
current_status = st.session_state["memorized"].get(current_idx, "belum")

with col_h1:
    if st.button("✅ Sudah hafal"):
        st.session_state["memorized"][current_idx] = "sudah"
        st.success("Ditandai sebagai sudah hafal!")
with col_h2:
    if st.button("❌ Belum hafal"):
        st.session_state["memorized"][current_idx] = "belum"
        st.info("Ditandai sebagai belum hafal.")

st.caption(f"Status hafalan untuk kata ini: **{current_status.upper()}**")

# ---------- MODE: Typing jawaban ----------
if mode=="Ketik Jawaban":
    st.markdown("---")
    st.header("⌨️ Mode Ketik Jawaban")
    form_key = f"typing_form_{current_idx}"
    with st.form(key=form_key, clear_on_submit=True):
        user_input = st.text_input("Jawabanmu:", key=f"input_{current_idx}")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["attempts"] += 1
            expected = back
            if typing_flex:
                e_norm = normalize_text(expected) if direction!="Indo → Hiragana" else normalize_japanese_kana(expected)
                u_norm = normalize_text(user_input) if direction!="Indo → Hiragana" else normalize_japanese_kana(user_input)
            else:
                e_norm = expected.strip()
                u_norm = user_input.strip()
            sim_pct = similarity(e_norm,u_norm)*100
            st.session_state["sim_sum"] += sim_pct/100
            st.session_state["sim_count"] +=1
            is_correct = sim_pct>=fuzz_threshold
            st.session_state["history"].insert(0,(card["kanji"], card["hiragana"], card["katakana"], card["romaji"], card["indo"], card["eng"], card["tipe"], card["catatan"], user_input, expected, sim_pct, is_correct))
            if is_correct:
                st.session_state["score"] +=1
                st.success(f"Benar! ✅ similarity: {sim_pct:.0f}% 🎉")
                st.balloons()
            else:
                st.error(f"Salah ❌ — jawaban benar: {expected} 😢")
                st.snow()
            if st.session_state["pos"]<total-1: st.session_state["pos"]+=1
            st.rerun()

# ---------- MODE: Quiz MCQ ----------
if mode=="Quiz (MCQ)":
    st.markdown("---")
    st.header("📝 Quiz Pilihan Ganda")
    
    current_card = df.loc[idx_list[st.session_state["pos"]]]
    if direction=="Hiragana → Indo":
        soal_text = current_card["hiragana"]
        jawaban_benar = current_card["indo"]
    elif direction=="Romaji → Indo":
        soal_text = current_card["romaji"]
        jawaban_benar = current_card["indo"]
    else:
        soal_text = current_card["indo"]
        jawaban_benar = current_card["hiragana"] if current_card["hiragana"] else current_card["katakana"]

    mcq_dict = st.session_state["mcq_choices_dict"]
    if current_idx not in mcq_dict:
        choices = [jawaban_benar]
        other_cards = df.drop(idx_list[st.session_state["pos"]])
        while len(choices) < mcq_choices and not other_cards.empty:
            rand_card = other_cards.sample(1).iloc[0]
            other_answer = (rand_card["indo"] if direction!="Indo → Hiragana" 
                            else (rand_card["hiragana"] or rand_card["katakana"]))
            if other_answer not in choices:
                choices.append(other_answer)
        random.shuffle(choices)
        mcq_dict[current_idx] = choices
    else:
        choices = mcq_dict[current_idx]

    st.markdown(f"**Soal:** {soal_text}")
    answer = st.radio("Pilih jawabanmu:", options=choices, key=f"mcq_{current_idx}")
    if st.button("Submit jawaban", key=f"submit_mcq_{current_idx}"):
        st.session_state["attempts"] += 1
        is_correct = answer == jawaban_benar
        if is_correct:
            st.session_state["score"] += 1
            st.success(f"Benar! 🎉 Jawaban: {jawaban_benar}")
            st.balloons()
        else:
            st.error(f"Salah ❌ Jawaban benar: {jawaban_benar} 😢")
            st.snow()
        st.session_state["history"].insert(0,(card["kanji"], card["hiragana"], card["katakana"], card["romaji"], card["indo"], card["eng"], card["tipe"], card["catatan"], answer, jawaban_benar, 100 if is_correct else 0, is_correct))
        if st.session_state["pos"] < total-1:
            st.session_state["pos"] += 1
        st.rerun()

# ---------- History ----------
st.markdown("---")
st.subheader("Riwayat percobaan (terbaru)")
hist = st.session_state["history"]
if hist:
    hist_df = pd.DataFrame([{
        "kanji":h, "hiragana":hi, "katakana":k, "romaji":r, "indo":i, "eng":e, "tipe":t, "catatan":c, 
        "jawaban_user":u, "jawaban_benar":jb, "similarity_%":f"{s:.0f}", "benar":"Ya" if bc else "Tidak"
    } for h,hi,k,r,i,e,t,c,u,jb,s,bc in hist])
    st.dataframe(hist_df)
else:
    st.caption("Belum ada percobaan.")

# ---------- Footer ----------
st.markdown("---")
dl_col, hint_col = st.columns([1,3])
with dl_col:
    buf = io.StringIO()
    filtered_df.to_csv(buf,index=False,encoding="utf-8-sig")
    st.download_button("Download dataset (filtered)",data=buf.getvalue().encode("utf-8-sig"),file_name="kosakata_filtered.csv")

    # Download progress hafalan
    mem_df = pd.DataFrame([{"index":k, "kanji":df.loc[k,"kanji"], "indo":df.loc[k,"indo"], "status":v}
                           for k,v in st.session_state["memorized"].items()])
    if not mem_df.empty:
        st.download_button("📘 Download progress hafalan", mem_df.to_csv(index=False).encode("utf-8-sig"), "progress_hafalan.csv")
    else:
        st.caption("Belum ada progress hafalan.")

with hint_col:
    st.info(f"💬 Hubungi via WhatsApp untuk masukan / data baru: [wa.me/{WA_NUMBER}](https://wa.me/{WA_NUMBER})")
