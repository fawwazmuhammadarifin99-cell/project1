# app.py (versi Streamlit Secrets / TOML)
import re
import requests
import streamlit as st
from openai import OpenAI

# =========================
# Setup & Config
# =========================
st.set_page_config(page_title="AI Dokter Remaja", page_icon="🩺", layout="centered")

st.markdown(
    "<h1 style='text-align: center;'>Prototype Pemanfaatan Kecerdasan Buatan (AI) sebagai Alat Bantu Diagnosis Masalah Kesehatan Siswa Siswi SMP Labschool Jakarta</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center;'>Silakan jawab pertanyaan berikut untuk menganalisis masalah kesehatan anda.</p>",
    unsafe_allow_html=True
)
st.divider()

# =========================
# Session State
# =========================
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "qa_pairs" not in st.session_state:
    st.session_state.qa_pairs = []
if "step" not in st.session_state:
    st.session_state.step = "bio"  # 'bio' -> 'chat' -> 'done'
if "bio_data" not in st.session_state:
    st.session_state.bio_data = {}
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "max_questions" not in st.session_state:
    st.session_state.max_questions = 10
if "final_analysis" not in st.session_state:
    st.session_state.final_analysis = None
if "first_question_sent" not in st.session_state:
    st.session_state.first_question_sent = False

# =========================
# Keys & Clients (via st.secrets)
# =========================
try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("OPENAI_API_KEY belum disetel di .streamlit/secrets.toml")
    st.stop()

OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")
openai_client = OpenAI(api_key=API_KEY)

# SendGrid (Email)
SENDGRID_API_KEY = st.secrets.get("SENDGRID_API_KEY", "").strip()
EMAIL_FROM       = st.secrets.get("FROM_EMAIL", "").strip() or st.secrets.get("EMAIL_FROM", "").strip()

# Twilio (SMS) – opsional
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN  = st.secrets.get("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_FROM        = st.secrets.get("TWILIO_FROM", "").strip()

# =========================
# Utils & Parsers
# =========================
def _clean_md(s: str) -> str:
    s = re.sub(r'\*\*(.*?)\*\*', r'\1', s)  # **bold**
    s = re.sub(r'\*(.*?)\*', r'\1', s)      # *italic*
    s = re.sub(r'^#+\s*', '', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*[-•]\s*', '- ', s, flags=re.MULTILINE)
    return s.strip()

def extract_selected_sections(full_text: str) -> str:
    """
    Ambil hanya:
      1) Kemungkinan diagnosis
      2) Rencana tindak lanjut & saran
      3) Edukasi pencegahan
    Toleran variasi heading.
    """
    text = full_text.strip()
    patterns = {
        "diagnosis": r"(?:^|\n)\s*(?:\*\*)?\s*(?:kemungkinan\s*diagnosis|diagnosis(?:\s*diferensial)?)\s*(?:\*\*)?\s*[:\-]?\s*\n(.*?)(?=\n\s*(?:\*\*)?\s*(?:rencana|saran|edukasi|pencegahan|kesimpulan|catatan)\b|$)",
        "plan":      r"(?:^|\n)\s*(?:\*\*)?\s*(?:rencana\s*tindak\s*lanjut(?:\s*&\s*saran)?|rencana\s*tatalaksana|saran)\s*(?:\*\*)?\s*[:\-]?\s*\n(.*?)(?=\n\s*(?:\*\*)?\s*(?:edukasi|pencegahan|kemungkinan|diagnosis|kesimpulan|catatan)\b|$)",
        "edu":       r"(?:^|\n)\s*(?:\*\*)?\s*(?:edukasi\s*pencegahan|pencegahan)\s*(?:\*\*)?\s*[:\-]?\s*\n(.*?)(?=\n\s*(?:\*\*)?\s*(?:rencana|saran|kemungkinan|diagnosis|kesimpulan|catatan)\b|$)"
    }
    out_parts = []
    for title, pat in [("Kemungkinan Diagnosis", patterns["diagnosis"]),
                       ("Rencana Tindak Lanjut & Saran", patterns["plan"]),
                       ("Edukasi Pencegahan", patterns["edu"])]:
        m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
        if m and m.group(1).strip():
            content = _clean_md(m.group(1))
            out_parts.append(f"{title}:\n{content.strip()}")

    if not out_parts:
        fallback = _clean_md(text)
        return (fallback[:6000] + "…") if len(fallback) > 6000 else fallback

    final = "\n\n".join(out_parts).strip()
    return (final[:8000] + "…") if len(final) > 8000 else final

def normalize_msisdn(num: str) -> str:
    """Ubah 08xxxx menjadi +628xxxx; jaga jika sudah +..; hilangkan spasi/dash."""
    if not num:
        return ""
    s = re.sub(r"[^\d+]", "", num.strip())
    if s.startswith("+"):
        return s
    if s.startswith("0"):
        return "+62" + s[1:]
    if s.startswith("62"):
        return "+" + s
    if s.isdigit():
        return "+62" + s
    return s

def is_valid_email(addr: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", addr or ""))

def send_email_via_sendgrid(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY belum di-set di secrets.")
    if not EMAIL_FROM:
        raise RuntimeError("FROM_EMAIL/EMAIL_FROM belum di-set di secrets.")
    if not to_email:
        raise RuntimeError("Alamat email tujuan kosong.")
    # import di dalam fungsi agar fleksibel saat paket belum terinstal
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=to_email,
        subject=subject,
        html_content=html_body,
        plain_text_content=text_body,
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)

def send_sms_via_twilio(text_body: str, to_number: str) -> str:
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM):
        raise RuntimeError("Kredensial Twilio belum lengkap (TWILIO_ACCOUNT_SID/AUTH_TOKEN/TWILIO_FROM).")
    if not to_number:
        raise RuntimeError("Nomor tujuan SMS kosong.")
    from twilio.rest import Client as TwilioClient
    t_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    msg = t_client.messages.create(from_=TWILIO_FROM, to=to_number, body=text_body)
    return msg.sid

# =========================
# Model Helpers
# =========================
def generate_next_question(qa_pairs):
    messages = [
        {"role": "system", "content": (
            "Kamu adalah Dokter Spesialis, lulusan FK UI & S2 Johns Hopkins. "
            "Lakukan anamnesis MEDIS TERSTRUKTUR, berbasis bukti, fokus penyakit umum tropis. "
            "Pertanyaan lanjutan wajib berdasar jawaban terakhir dan relevansi klinis. "
            "Boleh cek red flag (sesak berat, nyeri dada hebat, kejang, penurunan kesadaran, bibir/kuku membiru, perdarahan hebat) dengan pertanyaan spesifik. "
            "KELUARAN: hanya SATU kalimat tanya paling diagnostik."
        )},
        {"role": "user", "content": "Berikut riwayat percakapan:\n" + "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs])}
    ]
    # gunakan model dari secrets
    resp = openai_client.chat.completions.create(model=OPENAI_MODEL, messages=messages)
    return resp.choices[0].message.content.strip()

def fetch_research_summary():
    try:
        sources = [
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
                text_snippet = resp.text[:1500]
                summary += f"Sumber: {url}\nCuplikan: {text_snippet}\n\n"
        return summary if summary else "Tidak ada ringkasan yang dapat diambil saat ini."
    except Exception:
        return "Tidak dapat mengambil ringkasan riset saat ini."

def analyze_health(bio, qa_pairs, research_summary):
    messages = [
        {"role": "system", "content": (
            "Kamu adalah Dokter Spesialis lulusan FK UI dan S2 Johns Hopkins. "
            "Lakukan analisis berbasis bukti dan buat diagnosis diferensial dari anamnesis. "
            "Susun output dengan heading tebal: "
            "(1) Ringkasan Gejala, (2) Kemungkinan Diagnosis (dengan alasan), "
            "(3) Rencana Tindak Lanjut & Saran (spesifik), (4) Edukasi Pencegahan. "
            "Hindari kepastian absolut; tandai red flag bila ada."
        )},
        {"role": "user", "content": (
            f"Biodata:\n"
            f"Nama: {bio.get('nama','-')}\n"
            f"Usia: {bio.get('usia','-')}\n"
            f"Kelas: {bio.get('kelas','-')}\n"
            f"Jenis Kelamin: {bio.get('jenis_kelamin','-')}\n\n"
            f"Percakapan Q/A:\n" + "\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs]) +
            f"\n\nRingkasan riset (opsional):\n{research_summary}\n"
            "\nBerikan analisis sesuai format."
        )}
    ]
    resp = openai_client.chat.completions.create(model=OPENAI_MODEL, messages=messages)
    return resp.choices[0].message.content.strip()

# =========================
# UI Biodata (form hilang setelah Lanjut)
# =========================
if st.session_state.step == "bio":
    placeholder = st.empty()

    with placeholder.container():
        st.markdown("**Isi biodata singkat:**")
        with st.form("bio_form", clear_on_submit=False):
            nama = st.text_input("Nama (opsional, boleh kosong untuk privasi)",
                                 value=st.session_state.bio_data.get("nama", ""))
            try:
                usia_default = int(st.session_state.bio_data.get("usia", 13))
            except Exception:
                usia_default = 13
            usia = st.number_input("Usia (tahun)", min_value=7, max_value=20, step=1, value=usia_default)

            kelas_current = str(st.session_state.bio_data.get("kelas", "7"))
            kelas = st.selectbox("Kelas", options=["7", "8", "9"],
                                 index=["7", "8", "9"].index(kelas_current) if kelas_current in ["7","8","9"] else 0)

            jk = st.selectbox("Jenis Kelamin", options=["L", "P"],
                              index=0 if st.session_state.bio_data.get("jenis_kelamin","L")=="L" else 1)

            email = st.text_input("Email (untuk menerima hasil lengkap via email)",
                                  placeholder="nama@sekolah.sch.id",
                                  value=st.session_state.bio_data.get("email",""))

            nohp = st.text_input("Nomor HP (untuk menerima SMS notifikasi)",
                                 placeholder="+62812xxxxxxx",
                                 value=st.session_state.bio_data.get("nohp",""))

            submit = st.form_submit_button("Lanjut")

    if submit:
        norm = normalize_msisdn(nohp) if nohp else ""
        st.session_state.bio_data.update({
            "nama": nama.strip(),
            "usia": str(usia),
            "kelas": str(kelas),
            "jenis_kelamin": jk,
            "email": email.strip(),
            "nohp": norm or nohp
        })

        if email and not is_valid_email(email):
            st.warning("Format email kurang tepat. Anda tetap bisa lanjut, tetapi pengiriman email mungkin gagal.")

        st.session_state.step = "chat"
        if not st.session_state.first_question_sent:
            q = "Bisa diceritakan dengan lengkap, Anda saat ini mengalami keluhan kesehatan apa?"
            st.session_state.chat_log.append({"role": "assistant", "content": q})
            st.session_state.first_question_sent = True

        placeholder.empty()
        st.rerun()

# =========================
# Tampilkan riwayat chat yang sudah ada (jika ada)
# =========================
for msg in st.session_state.chat_log:
    role = "assistant" if msg["role"] == "assistant" else "user"
    st.chat_message(role).markdown(msg["content"])

# =========================
# Chat Flow
# =========================
user_input = st.chat_input("Jawaban Anda...") if st.session_state.step in ("chat", "done") else None
if user_input and st.session_state.step == "chat":
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_log.append({"role": "user", "content": user_input})

    # Pertanyaan asisten terakhir sebelum jawaban user
    last_q = next((m["content"] for m in reversed(st.session_state.chat_log[:-1]) if m["role"] == "assistant"),
                  "(pertanyaan awal)")
    st.session_state.qa_pairs.append((last_q, user_input))
    st.session_state.question_count += 1

    if st.session_state.question_count >= st.session_state.max_questions:
        with st.spinner("Mengambil referensi riset..."):
            research_summary = fetch_research_summary()
        with st.spinner("Menganalisis jawaban Anda berdasarkan riset..."):
            result = analyze_health(st.session_state.bio_data, st.session_state.qa_pairs, research_summary)

        st.session_state.final_analysis = result
        st.chat_message("assistant").markdown("*Hasil analisis masalah kesehatan Anda:*")
        st.chat_message("assistant").markdown(result)
        st.session_state.chat_log.append({"role": "assistant", "content": result})
        st.session_state.step = "done"

        # ====== Siapkan konten email (3 bagian) ======
        nama = st.session_state.bio_data.get('nama', 'Siswa')
        selected = extract_selected_sections(result)
        subject = f"Hasil AI Dokter Remaja — {nama}"
        text_body = (
            f"Halo {nama},\n\n"
            "Berikut hasil analisis AI Dokter Remaja:\n\n"
            f"{selected}\n\n"
            "Disclaimer: Ini bukan diagnosis resmi. Jika Anda mengalami tanda bahaya atau nyeri berat, segera cari pertolongan medis darurat."
        )
        html_body = (
            f"<p>Halo <b>{nama}</b>,</p>"
            f"<p>Berikut hasil analisis <b>AI Dokter Remaja</b>:</p>"
            f"<pre style='white-space:pre-wrap;font-family:inherit'>{selected}</pre>"
            "<p><i>Disclaimer: Ini bukan diagnosis resmi. Jika Anda mengalami tanda bahaya atau nyeri berat, segera cari pertolongan medis darurat.</i></p>"
        )

        # ====== Kirim Email via SendGrid (penerima = email dari form) ======
        to_email = (st.session_state.bio_data.get("email") or "").strip()
        if to_email:
            try:
                send_email_via_sendgrid(to_email, subject, html_body, text_body)
                st.success(f"Email terkirim ke {to_email}")
            except Exception as e:
                st.warning(f"Email tidak terkirim: {e}")
        else:
            st.info("Email tidak diisi, jadi hasil lengkap tidak dikirim via email.")

        # ====== Kirim SMS notifikasi singkat (opsional) ======
        to_num = normalize_msisdn(st.session_state.bio_data.get("nohp", ""))
        if to_num:
            if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM:
                sms_text = (
                    f"Halo {nama}, hasil AI Dokter Remaja sudah dikirim ke email Anda. "
                    f"Silakan cek inbox/SPAM dengan subjek: '{subject}'."
                )
                try:
                    sid = send_sms_via_twilio(sms_text, to_num)
                    st.success(f"SMS notifikasi terkirim ke {to_num}. SID: {sid}")
                except Exception as e:
                    st.warning(f"SMS tidak terkirim: {e}")
            else:
                st.info("Kredensial Twilio belum lengkap, SMS tidak dikirim.")
        else:
            st.info("Nomor HP tidak diisi, jadi tidak ada SMS notifikasi yang dikirim.")
    else:
        with st.spinner("Mempersiapkan pertanyaan selanjutnya..."):
            next_q = generate_next_question(st.session_state.qa_pairs)
        st.chat_message("assistant").markdown(next_q)
        st.session_state.chat_log.append({"role": "assistant", "content": next_q})

# =========================
# Disclaimer
# =========================
st.info("Disclaimer: Ini bukan diagnosis resmi. Jika Anda mengalami tanda bahaya atau nyeri berat, segera cari pertolongan medis darurat.")
