import streamlit as st
import re
import phonenumbers
from difflib import SequenceMatcher
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# 1. كلمة السر الخاصة بداخلية الإشراف
ADMIN_PASSWORD = "bellona2026"

# 2. إعدادات الاتصال بـ Supabase
SUPABASE_URL = "https://igskxyazuomofeqvkwcy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlnc2t4eWF6dW9tb2ZlcXZrd2N5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYxNTkyNTksImV4cCI6MjEwMTczNTI1OX0.HadeqymBYWETFaauKYFNtlD-ahg3GfoOGoH0XKu_mWg"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# 3. إعدادات الصفحة وجماليات الساكورا (Sakura Aesthetic)
st.set_page_config(page_title="بوابة استقبال BELLONA", page_icon="🌸", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0f0a12; color: #f3e8ee; font-family: 'Cairo', sans-serif; }
    .main-card { background: rgba(30, 20, 32, 0.75); border: 1px solid #ffb3c6; border-radius: 20px; padding: 30px; box-shadow: 0 0 25px rgba(255, 179, 198, 0.15); text-align: center; margin-bottom: 20px; }
    h1 { color: #ffb3c6 !important; font-weight: 800 !important; }
    .sub-title { color: #ff7aa2; font-weight: 600; font-size: 15px; margin-bottom: 15px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; background: linear-gradient(135deg, #ff7aa2, #ffb3c6); color: #1a0814; border: none; padding: 12px; transition: 0.3s; }
    .stButton>button:hover { box-shadow: 0 0 15px rgba(255, 122, 162, 0.6); color: #000; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 4. دوال التعامل مع قاعدة البيانات
def load_data_from_supabase():
    try:
        response = supabase.table("members").select("*").execute()
        records = response.data if response.data else []
        nicknames = [str(r.get("nickname", "")).strip() for r in records if r.get("nickname")]
        default_nicks = ["آرثر", "لامينو", "Arthur", "Lamino"]
        for dn in default_nicks:
            if dn not in nicknames: nicknames.append(dn)
        return {"registered_nicknames": nicknames, "members": records}
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return {"registered_nicknames": ["آرثر", "لامينو"], "members": []}

def add_member_to_supabase(new_entry):
    supabase.table("members").insert(new_entry).execute()

def delete_member_from_supabase(phone_to_del):
    supabase.table("members").delete().eq("phone", str(phone_to_del)).execute()

db_data = load_data_from_supabase()

# 5. دوال التحقق
def normalize_arabic(text):
    text = re.sub(r'[\u064B-\u0652\u0654-\u0655ـ]', '', str(text).strip().lower())
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    return text

def is_nickname_taken(new_nick, existing_nicks):
    norm_new = normalize_arabic(new_nick)
    for existing in existing_nicks:
        if norm_new == normalize_arabic(existing):
            return True, f"اللقب محجوز ({existing})"
    return False, "اللقب متاح"

def is_valid_phone(phone_str):
    try: return phonenumbers.is_valid_number(phonenumbers.parse(phone_str, None))
    except: return False

# 6. الواجهة
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False

if st.session_state.admin_logged_in:
    st.markdown("<h1>👑 لوحة إشراف استقبال BELLONA 👑</h1>", unsafe_allow_html=True)
    if st.button("🚪 خروج"): st.session_state.admin_logged_in = False; st.rerun()
    if db_data["members"]:
        selected = st.selectbox("اختر العضو:", [f"{m['nickname']} - ({m['phone']})" for m in db_data["members"]])
        m = next(x for x in db_data["members"] if f"{x['nickname']} - ({x['phone']})" == selected)
        st.write(f"📱 الرقم: {m['phone']} | 🤝 الدعوة: {m.get('referrer', 'مباشر')}")
        if st.button(f"🗑️ حذف {m['nickname']}"): delete_member_from_supabase(m['phone']); st.rerun()
    else: st.info("لا يوجد أعضاء.")
else:
    st.markdown("<div class='main-card'><h1>🌸 بوابة استقبال BELLONA 🌸</h1></div>", unsafe_allow_html=True)
    phone = st.text_input("رقم الهاتف (مع المفتاح الدولي)")
    nick = st.text_input("اللقب المختار")
    referrer = st.text_input("صاحب الدعوة")
    receiver = st.text_input("مسؤول الاستقبال")
    
    if st.button("تأكيد وتسجيل"):
        if is_valid_phone(phone) and not is_nickname_taken(nick, db_data["registered_nicknames"])[0]:
            add_member_to_supabase({"phone": phone, "nickname": nick, "referrer": referrer, "received_by": receiver, "date": str(datetime.now())})
            st.success("تم التسجيل!")
        else: st.error("بيانات غير صالحة أو مكررة.")

    with st.expander("🌸"):
        if st.text_input("رمز المشرف", type="password") == ADMIN_PASSWORD: st.session_state.admin_logged_in = True; st.rerun()
    
