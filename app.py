import streamlit as st
import json
import os
import re
import phonenumbers
from difflib import SequenceMatcher
import pandas as pd
from datetime import datetime

# 1. كلمة السر الخاصة بداخلية الإشراف
ADMIN_PASSWORD = "bellona2026"

# 2. إعدادات الصفحة المتقدمة وجماليات الساكورا (Sakura Aesthetic)
st.set_page_config(
    page_title="بوابة استقبال BELLONA",
    page_icon="🌸",
    layout="centered"
)

st.markdown("""
<style>
    /* الخلفية العامة */
    .stApp {
        background-color: #0f0a12;
        color: #f3e8ee;
        font-family: 'Cairo', sans-serif;
    }
    
    /* بطاقة المحتوى الرئيسية */
    .main-card {
        background: rgba(30, 20, 32, 0.75);
        border: 1px solid #ffb3c6;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 0 25px rgba(255, 179, 198, 0.15);
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* العناوين */
    h1 {
        color: #ffb3c6 !important;
        font-weight: 800 !important;
    }
    .sub-title {
        color: #ff7aa2;
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 15px;
    }
    
    /* تخصيص الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: bold;
        background: linear-gradient(135deg, #ff7aa2, #ffb3c6);
        color: #1a0814;
        border: none;
        padding: 12px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(255, 122, 162, 0.6);
        color: #000;
    }
    
    /* إخفاء عناصر ستريمليت الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. إدارة ملف البيانات Local JSON
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "registered_nicknames": ["آرثر", "لامينو", "Arthur", "Lamino"],
            "members": []
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db_data = load_data()

# 4. خوارزميات تنظيف النصوص والتحقق الذكي من الألقاب (Fuzzy Normalization)
def normalize_arabic(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r'ـ+', '', text)
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def is_nickname_taken(new_nick, existing_nicks, threshold=0.80):
    norm_new = normalize_arabic(new_nick)
    if not norm_new:
        return True, "اللقب غير صالح"
    
    for existing in existing_nicks:
        norm_exist = normalize_arabic(existing)
        
        if norm_new == norm_exist:
            return True, f"اللقب مطابق أو محجوز سابقاً ({existing})"
        
        ratio = SequenceMatcher(None, norm_new, norm_exist).ratio()
        if ratio >= threshold:
            return True, f"اللقب مشابه جداً للقب مسجل سابقاً ({existing})"
            
    return False, "اللقب متاح للانضمام"

# 5. فحص صحة رقم الهاتف
def is_valid_phone(phone_str):
    try:
        parsed = phonenumbers.parse(phone_str, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

# 6. الواجهة الرئيسية
st.markdown("""
<div class="main-card">
    <h1>🌸 بوابة استقبال BELLONA 🌸</h1>
    <div class="sub-title">أهلاً بك في مجتمع BELLONA الرسمي</div>
    <p style="font-size: 13px; color: #d8c2ce;">يرجى إكمال الاستمارة أدناه لتأكيد هويتك وتوليد رابط الانضمام</p>
</div>
""", unsafe_allow_html=True)

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if not st.session_state.submitted:
    with st.container():
        phone_input = st.text_input("رقم الهاتف (مع رمز الدولة)", placeholder="+9647700000000")
        nick_input = st.text_input("اللقب المختار", placeholder="اكتب لقبك هنا...")
        referrer_input = st.text_input("من طرف منو أتيت؟ (الاستقبال)", placeholder="اسم العضو أو الجهة الداعية")

        phone_valid = is_valid_phone(phone_input)
        nick_taken, nick_msg = is_nickname_taken(nick_input, db_data["registered_nicknames"]) if nick_input else (True, "")
        referrer_valid = len(referrer_input.strip()) > 0

        if phone_input:
            if phone_valid:
                st.caption("✅ رقم الهاتف صحيح ومفعل")
            else:
                st.caption("❌ يرجى كتابة رقم هاتف حقيقي مع المفتاح الدولي")

        if nick_input:
            if not nick_taken:
                st.caption("✅ " + nick_msg)
            else:
                st.caption("❌ " + nick_msg)

        form_ready = phone_valid and (not nick_taken) and referrer_valid

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("تأكيد البيانات وتوليد رابط الدخول", disabled=not form_ready):
            # استخراج الأرقام فقط بدون + أو رموز لضمان المنشن النظيف
            clean_digits_only = re.sub(r'\D', '', phone_input.strip())
            
            new_entry = {
                "phone": clean_digits_only,
                "nickname": nick_input.strip(),
                "referrer": referrer_input.strip(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            db_data["members"].append(new_entry)
            db_data["registered_nicknames"].append(nick_input.strip())
            save_data(db_data)
            
            st.session_state.submitted = True
            st.rerun()

else:
    st.success("🎉 تم التحقق من بياناتك وتسجيل لقبك بنجاح!")
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <p style="color: #ffb3c6; font-size: 16px;">اضغط على الزر أدناه للانضمام للمجموعة مباشرة:</p>
        <a href="https://chat.whatsapp.com/YOUR_GROUP_LINK_HERE" target="_blank" style="
            display: inline-block;
            padding: 14px 28px;
            background: #25d366;
            color: white;
            text-decoration: none;
            font-weight: bold;
            border-radius: 12px;
            box-shadow: 0 0 15px rgba(37, 211, 102, 0.4);
        ">📱 دخول جروب BELLONA الآن</a>
    </div>
    """, unsafe_allow_html=True)

# 7. الزر المخفي ولوحة الإشراف (Admin Panel)
st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    with st.expander("🌸", expanded=False):
        admin_pass = st.text_input("رمز مرور المشرفين", type="password")
        if admin_pass == ADMIN_PASSWORD:
            st.subheader("لوحة إشراف الاستقبال")
            
            # حجز ألقاب يدويًا
            st.write("---")
            st.markdown("**حجز لقب جديد يدويًا**")
            new_admin_nick = st.text_input("أدخل اللقب المراد حجزه:")
            if st.button("إضافة للقائمة"):
                if new_admin_nick and new_admin_nick not in db_data["registered_nicknames"]:
                    db_data["registered_nicknames"].append(new_admin_nick.strip())
                    save_data(db_data)
                    st.success(f"تم حجز اللقب: {new_admin_nick}")
                    st.rerun()

            # سجل الأعضاء ورسائل الترحيب للواتساب
            st.write("---")
            st.markdown("**سجل الأعضاء ورسائل الترحيب**")
            
            if db_data["members"]:
                for idx, member in enumerate(reversed(db_data["members"])):
                    with st.container():
                        st.markdown(f"👤 **اللقب:** `{member['nickname']}` | 📱 **الرقم:** `{member['phone']}`")
                        st.caption(f"🤝 من طرف: {member['referrer']} | 📅 {member['date']}")
                        
                        # توليد نص المنشن بدون أي أقواس أو رموز إضافية لضمان عمل منشن الواتساب تلقائياً
                        clean_tag = member['phone']
                        
                        welcome_text = (
                            f"🌸 ✨ أهـلاً وسهـلاً بـالعـضـو الـجـديـد ✨ 🌸\n\n"
                            f"👑 اللقب: {member['nickname']}\n"
                            f"📱 الرقم: @{clean_tag}\n"
                            f"🏰 مرحباً بك في عالم BELLONA 🌟\n\n"
                            f"نورت الجروب يا بطل! يسعدنا انضمامك لعائلتنا الرهيبة، ونتمنى لك أوقاتاً ممتعة ومميزة معنا 🔥🤍\n\n"
                            f"📜 ملاحظة مهمة جداً: لا تنسى مراجعة قوانين الجروب المثبتة والتأكد من الاطلاع عليها للحفاظ على ترتيب وتفاعل المجموعة وتجنب أي مخالفة.\n\n"
                            f"نتمنى لك إقامة خرافية معنا! 🚀✨"
                        )
                        
                        # كود مخصص يتيح النسخ بضغطة زر واحدة
                        st.code(welcome_text, language="text")
                        st.write("---")
            else:
                st.info("لا يوجد أعضاء مسجلون حتى الآن.")
                
            st.markdown("**الألقاب المحجوزة حالياً:**")
            st.write(", ".join(db_data["registered_nicknames"]))
                
