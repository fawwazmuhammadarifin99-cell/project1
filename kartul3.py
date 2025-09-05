# tambahan riset

import streamlit as st
import os
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


st.markdown(
    "<h1 style='text-align: center;'>Prototype Pemanfaatan Kecerdasan Buatan (AI) sebagai Alat Bantu Diagnosis Masalah Kesehatan Siswa Siswi SMP Labschool Jakarta</h1>", 
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align: center;'>Silakan jawab pertanyaan berikut untuk menganalisis masalah kesehatan anda.</p>", 
    unsafe_allow_html=True
)
st.divider()

# Inisialisasi
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "qa_pairs" not in st.session_state:
    st.session_state.qa_pairs = []
if "step" not in st.session_state:
    st.session_state.step = "bio"
if "bio_data" not in st.session_state:
    st.session_state.bio_data = {}
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "max_questions" not in st.session_state:
    st.session_state.max_questions = 10

bio_fields = [
    ("Nama lengkap Anda?", "nama"),
    ("Berapa usia Anda?", "usia"),
    ("Anda saat ini duduk di kelas berapa?", "kelas"),
    ("Apa jenis kelamin Anda? (L/P)", "jenis_kelamin")
]
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("OPENAI_API_KEY belum disetel")
    st.stop()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def generate_next_question(qa_pairs):
    messages = [
        {"role": "system", "content": (
                    "Kamu adalah Dokter Spesialis, "
                    "profil: dokter lulusan Fakultas Kedokteran UI, S2 Johns Hopkins University. "
                    "Peranmu: lakukan anamnesis MEDIS TERSTRUKTUR, berbasis bukti, fokus penyakit umum tropis. "
                    "Setiap pertanyaan lanjutan wajib berdasarkan analisis jawaban terakhir + ringkasan riset internet terlampir sehingga pertanyaan lanjutan yang lebih dalam dan relevan"
                    "Jangan bilang 'pergi ke dokter'; kamu yang memandu. "
                    "Jika ada tanda gawat darurat (sesak berat, nyeri dada hebat, kejang, penurunan kesadaran, bibir/kuku membiru, perdarahan hebat), "
                    "boleh klarifikasi keberadaannya dengan pertanyaan spesifik. "
                    "KELUARAN untuk fungsi pertanyaan: hanya SATU kalimat tanya yang paling diagnostik."
        )},
        {"role": "user", "content": "Berikut riwayat percakapan:\n" + "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs])}
    ]
    response = client.chat.completions.create(
        model="gpt-4o", 
        #model="gpt-5",
        messages=messages
    )
    return response.choices[0].message.content.strip()

def fetch_research_summary():
    try:
        sources = [
            "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1517920/full",
            "https://bmcpsychology.biomedcentral.com/articles/10.1186/s40359-025-02602-6",
            "https://link.springer.com/article/10.1007/s10212-023-00731-3",
            "https://www.verywellmind.com/top-school-stress-relievers-for-students-3145179",
            "https://arxiv.org/abs/2505.15974",
            "https://www.who.int/health-topics/dengue-and-severe-dengue",
            "https://www.cdc.gov/dengue/index.html",
            "https://www.cdc.gov/malaria/index.html",
            "https://www.idai.or.id/",
            "https://www.kemkes.go.id/"
        ]
        summary = ""
        for url in sources:
            resp = requests.get(url, timeout=10)
            if resp.ok:
                text_snippet = resp.text[:1500]  # Ambil cuplikan awal sebagai ringkasan kasar
                summary += f"Sumber: {url}\nCuplikan: {text_snippet}\n\n"
        return summary
    except:
        return "Tidak dapat mengambil ringkasan riset saat ini."


def analyze_stress(bio, qa_pairs, research_summary):
    messages = [
        #{"role": "system", "content": "Kamu adalah psikolog akademik yang menganalisis tingkat stres siswa berdasarkan jawaban mereka dan riset terbaru."},
        {"role": "system", "content": (
#                    "Kamu adalah AI Dokter Remaja untuk siswa-siswi SMP Labschool Jakarta, "
#                   "profil: dokter kesehatan remaja lulusan Fakultas Kedokteran UI, S2 Johns Hopkins University. "
                    "Kamu adalah Dokter Spesialis lulusan Fakultas Kedokteran UI, S2 Johns Hopkins University yang menganalisis dan diagnosis penyakit berdasarkan jawaban mereka dan riset terbaru "
                    "Peranmu: lakukan anamnesis MEDIS TERSTRUKTUR, berbasis bukti, fokus penyakit umum tropis. "
#                    "Setiap pertanyaan lanjutan wajib berdasarkan analisis jawaban terakhir + ringkasan riset internet terlampir sehingga pertanyaan lanjutan yang lebih dalam dan relevan"
#                    "Jangan bilang 'pergi ke dokter'; kamu yang memandu. "
#                    "Jika ada tanda gawat darurat (sesak berat, nyeri dada hebat, kejang, penurunan kesadaran, bibir/kuku membiru, perdarahan hebat), "
#                    "boleh klarifikasi keberadaannya dengan pertanyaan spesifik. "
#                    "KELUARAN untuk fungsi pertanyaan: hanya SATU kalimat tanya yang paling diagnostik."
        )},
        {"role": "user", "content": (
            f"Berikut biodata siswa:\n"
            f"Nama: {bio['nama']}\nUsia: {bio['usia']}\nKelas: {bio['kelas']}\nJenis Kelamin: {bio['jenis_kelamin']}\n\n"
            f"Dan berikut percakapan:\n" + "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs]) +
            f"\n\nBerikut ringkasan riset kesehatan terkini:\n{research_summary}\n"
            "\n\nTolong berikan analisis gejala masalah kesehatan siswa ini , saran , diagnosis berbasis bukti ilmiah dan hasil riset dan praktisi Dan jangan lupa obatnya juga apa serta dosisnya."
        )}
    ]
    response = client.chat.completions.create(
        model="gpt-4o", 
        #model="gpt-5",
        messages=messages
    )
    return response.choices[0].message.content.strip()

# Input pengguna
user_input = st.chat_input("Jawaban Anda...")
if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_log.append({"role": "user", "content": user_input})

    if st.session_state.step == "bio":
        current_index = len(st.session_state.bio_data)
        label = bio_fields[current_index][1]
        st.session_state.bio_data[label] = user_input
        if len(st.session_state.bio_data) == len(bio_fields):
            st.session_state.step = "chat"

    elif st.session_state.step == "chat":
        last_q = st.session_state.chat_log[-2]["content"]
        st.session_state.qa_pairs.append((last_q, user_input))
        st.session_state.question_count += 1

        if st.session_state.question_count >= st.session_state.max_questions:
            with st.spinner("Mengambil referensi riset..."):
                research_summary = fetch_research_summary()
            with st.spinner("Menganalisis jawaban Anda berdasarkan riset..."):
                result = analyze_stress(st.session_state.bio_data, st.session_state.qa_pairs, research_summary)
                st.chat_message("assistant").markdown("*Hasil analisis masalah kesehatan Anda:*")
                st.chat_message("assistant").markdown(result)
                st.session_state.chat_log.append({"role": "assistant", "content": result})
                st.session_state.step = "done"
        else:
            with st.spinner("Mempersiapkan pertanyaan selanjutnya..."):
                next_q = generate_next_question(st.session_state.qa_pairs)
                st.chat_message("assistant").markdown(next_q)
                st.session_state.chat_log.append({"role": "assistant", "content": next_q})

# Pertanyaan pertama
if st.session_state.step == "bio":
    q = bio_fields[len(st.session_state.bio_data)][0]
    st.chat_message("assistant").markdown(q)
    st.session_state.chat_log.append({"role": "assistant", "content": q})

elif st.session_state.step == "chat" and st.session_state.question_count == 0:
    q = "Bisa diceritakan dengan lengkap, anda saat ini mengalami masalah kesehatan apa?"
    st.chat_message("assistant").markdown(q)
    st.session_state.chat_log.append({"role": "assistant", "content": q})

st.info("Disclaimer: Ini bukan diagnosis resmi. Jika Anda merasa sakit tidak tertahankan, hubungi unit gawat darurat secepatnya ")