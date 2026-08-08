import streamlit as st
import json
import os
import re
import phonenumbers
from difflib import SequenceMatcher
import pandas as pd
from datetime import datetime

# 1. إعدادات الصفحة وجماليات الساكورا (Sakura Aesthetic)
st.set_page_config(
    page_title="بوابة الاستقبال والانضمام",
    page_icon="🌸",
    layout="centered"
)

# تصميم CSS مخصص بثيم الساكورا والوضع الداكن
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
    
    /* إخفاء القوائم الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 2. إدارة ملف البيانات Local JSON
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

# 3. خوارزميات تنظيف النصوص والتحقق الذكي من الألقاب (Fuzzy Normalization)
def normalize_arabic(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r'ـ+', '', text)  # إزالة التطويل
    text = re.sub(r'[\u064B-\u0652]', '', text)  # إزالة التشكيل
    text = re.sub(r'[أإآ]', 'ا', text)  # توحيد الألف
    text = re.sub(r'ى', 'ي', text)  # توحيد الألف المقصورة
    text = re.sub(r'ة', 'ه', text)  # توحيد التاء المربوطة
    text = re.sub(r'[^\w\s]', '', text)  # إزالة الرموز والنقاط
    text = re.sub(r'\s+', ' ', text)  # توحيد المسافات
    return text

def is_nickname_taken(new_nick, existing_nicks, threshold=0.80):
    norm_new = normalize_arabic(new_nick)
    if not norm_new:
        return True, "اللقب غير صالح"
    
    for existing in existing_nicks:
        norm_exist = normalize_arabic(existing)
        
        # تطابق تام بعد التنظيف
        if norm_new == norm_exist:
            return True, f"اللقب مطاطب أو محجوز سابقاً ({existing})"
        
        # نسبة التشابه
        ratio = SequenceMatcher(None, norm_new, norm_exist).ratio()
        if ratio >= threshold:
            return True, f"اللقب مشابه جداً للقب مسجل سابقاً ({existing})"
            
    return False, "اللقب متاح للانضمام"

# 4. فحص صحة رقم الهاتف
def is_valid_phone(phone_str):
    try:
        parsed = phonenumbers.parse(phone_str, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

# 5. الواجهة الرئيسية
st.markdown("""
<div class="main-card">
    <h1>🌸 بوابة الاستقبال والانضمام 🌸</h1>
    <div class="sub-title">الإشراف من قبل آرثر والمساعد لامينو</div>
    <p style="font-size: 13px; color: #d8c2ce;">يرجى إكمال الاستمارة أدناه لتأكيد هويتك والانضمام للجروب الرسمي</p>
</div>
""", unsafe_allow_html=True)

# تهيئة Session State لتتبع نجاح التسجيل
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if not st.session_state.submitted:
    with st.container():
        phone_input = st.text_input("رقم الهاتف (مع رمز الدولة)", placeholder="+9647700000000")
        nick_input = st.text_input("اللقب المختار", placeholder="اكتب لقبك هنا...")
        referrer_input = st.text_input("من طرف منو أتيت؟ (الاستقبال)", placeholder="اسم العضو أو الجهة الداعية")

        # التحقق اللحظي من المدخلات
        phone_valid = is_valid_phone(phone_input)
        nick_taken, nick_msg = is_nickname_taken(nick_input, db_data["registered_nicknames"]) if nick_input else (True, "")
        referrer_valid = len(referrer_input.strip()) > 0

        # مؤشرات حالة المدخلات
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

        # شروط تفعيل الزر
        form_ready = phone_valid and (not nick_taken) and referrer_valid

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("تأكيد البيانات وتوليد رابط الدخول", disabled=not form_ready):
            # حفظ العضو الجديد
            new_entry = {
                "phone": phone_input.strip(),
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
    # واجهة النجاح ورابط الواتساب
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
        ">📱 دخول جروب الواتساب الآن</a>
    </div>
    """, unsafe_allow_html=True)

# 6. الزر المخفي ولوحة الإشراف (Admin Panel)
st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # زهرة الساكورا هي الزر المخفي
    with st.expander("🌸", expanded=False):
        admin_pass = st.text_input("رمز مرور المشرفين", type="password")
        if admin_pass == "1234":  # يمكنك تغيير كلمة السر هنا
            st.subheader("لوحة إشراف الاستقبال")
            
            # قسم إضافة الألقاب المحجوزة يدويًا
            st.write("---")
            st.markdown("**حجز لقب جديد يدويًا**")
            new_admin_nick = st.text_input("أدخل اللقب المراد حجزه:")
            if st.button("إضافة للقائمة"):
                if new_admin_nick and new_admin_nick not in db_data["registered_nicknames"]:
                    db_data["registered_nicknames"].append(new_admin_nick.strip())
                    save_data(db_data)
                    st.success(f"تم حجز اللقب: {new_admin_nick}")
                    st.rerun()

            # عرض قائمة الأعضاء والبيانات
            st.write("---")
            st.markdown("**سجل الأعضاء المسجلين**")
            if db_data["members"]:
                df = pd.DataFrame(db_data["members"])
                df.columns = ["رقم الهاتف", "اللقب", "من طرف", "تاريخ التسجيل"]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("لا يوجد أعضاء مسجلون حتى الآن.")
                
            st.write("---")
            st.markdown("**الألقاب المحجوزة حالياً:**")
            st.write(", ".join(db_data["registered_nicknames"]))
  
