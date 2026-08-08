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

# 2. إعدادات الصفحة وجماليات الساكورا (Sakura Aesthetic)
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
    
    /* بطاقات المحتوى */
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

# 3. إدارة ملف البيانات Local JSON المحصنة
DATA_FILE = "data.json"

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    default_data = {
        "registered_nicknames": ["آرثر", "لامينو", "Arthur", "Lamino"],
        "members": []
    }
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        save_data(default_data)
        return default_data
        
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        save_data(default_data)
        return default_data

db_data = load_data()

# 4. خوارزميات التنظيف والتحقق الذكي
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

def is_valid_phone(phone_str):
    try:
        parsed = phonenumbers.parse(phone_str, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

def is_phone_registered(phone_str, members_list):
    clean_digits = re.sub(r'\D', '', phone_str)
    if not clean_digits:
        return False
    existing_phones = [m.get("phone", "") for m in members_list]
    return clean_digits in existing_phones

# 5. إدارة حالة تسجيل الدخول للإشراف
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# =========================================================
#                    صفحة الإشراف الكاملة
# =========================================================
if st.session_state.admin_logged_in:
    st.markdown("""
    <div class="main-card">
        <h1>👑 لوحة إشراف استقبال BELLONA 👑</h1>
        <p style="font-size: 13px; color: #d8c2ce;">إدارة الألقاب المسجلة وسجل الأعضاء ورسائل الترحيب</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 الخروج من لوحة الإشراف"):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.write("---")
    
    # 1. قسم حجز الألقاب يدويًا
    st.markdown("### 📌 حجز لقب جديد يدويًا")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        new_admin_nick = st.text_input("أدخل اللقب المراد حجزه:", label_visibility="collapsed", placeholder="اكتب اللقب هنا...")
    with col_b:
        if st.button("حجز اللقب"):
            if new_admin_nick and new_admin_nick.strip() not in db_data["registered_nicknames"]:
                db_data["registered_nicknames"].append(new_admin_nick.strip())
                save_data(db_data)
                st.success(f"تم حجز اللقب: {new_admin_nick}")
                st.rerun()

    st.write("---")
    
    # 2. قسم سجل الأعضاء وإدارتهم
    st.markdown("### 📋 سجل الأعضاء ورسائل الترحيب")
    
    if db_data["members"]:
        reversed_members = list(reversed(db_data["members"]))
        member_options = [f"{m['nickname']} - ({m['phone']})" for m in reversed_members]
        
        selected_option = st.selectbox("اختر العضو لعرض تفاصيله أو حذفه:", options=member_options)
        
        selected_index = member_options.index(selected_option)
        selected_member = reversed_members[selected_index]
        
        # بطاقة تفاصيل العضو المختار مع زر الحذف
        st.markdown(f"""
        <div style="background: rgba(255, 179, 198, 0.08); border: 1px solid #ffb3c6; border-radius: 12px; padding: 18px; margin-top: 15px;">
            <p style="margin: 4px 0;">👑 <b>اللقب:</b> {selected_member['nickname']}</p>
            <p style="margin: 4px 0;">📱 <b>الرقم:</b> {selected_member['phone']}</p>
            <p style="margin: 4px 0;">🤝 <b>من طرف:</b> {selected_member['referrer']}</p>
            <p style="margin: 4px 0; font-size: 12px; color: #ff7aa2;">📅 <b>تاريخ التسجيل:</b> {selected_member['date']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # زر حذف العضو المحدد
        if st.button(f"🗑️ حذف العضو ({selected_member['nickname']})"):
            # 1. إزالة العضو من قائمة الأعضاء
            db_data["members"] = [m for m in db_data["members"] if m["phone"] != selected_member["phone"]]
            
            # 2. إزالة اللقب من قائمة الألقاب المحجوزة
            if selected_member["nickname"] in db_data["registered_nicknames"]:
                db_data["registered_nicknames"].remove(selected_member["nickname"])
                
            save_data(db_data)
            st.success(f"تم حذف العضو ({selected_member['nickname']}) وتحرير لقبه ورقمه بنجاح!")
            st.rerun()
            
        st.markdown("<br><b>📝 رسالة الترحيب المجهزة للواتساب (انسخها بضغطة زر):</b>", unsafe_allow_html=True)
        
        clean_tag = selected_member['phone']
        welcome_text = (
            f"🌸 ✨ أهـلاً وسهـلاً بـالعـضـو الـجـديـد ✨ 🌸\n\n"
            f"👑 اللقب: {selected_member['nickname']}\n"
            f"📱 الرقم: @{clean_tag}\n"
            f"🏰 مرحباً بك في عالم BELLONA 🌟\n\n"
            f"نورت الجروب يا بطل! يسعدنا انضمامك لعائلتنا الرهيبة، ونتمنى لك أوقاتاً ممتعة ومميزة معنا 🔥🤍\n\n"
            f"📜 ملاحظة مهمة جداً: لا تنسى مراجعة قوانين الجروب المثبتة والتأكد من الاطلاع عليها للحفاظ على ترتيب وتفاعل المجموعة وتجنب أي مخالفة.\n\n"
            f"نتمنى لك إقامة خرافية معنا! 🚀✨"
        )
        
        st.code(welcome_text, language="text")
    else:
        st.info("لا يوجد أعضاء مسجلون حتى الآن.")
        
    st.write("---")
    st.markdown("**الألقاب المحجوزة حالياً بالنظام:**")
    st.write(", ".join(db_data["registered_nicknames"]))

# =========================================================
#                    صفحة استقبال الأعضاء (العامة)
# =========================================================
else:
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
            phone_registered = is_phone_registered(phone_input, db_data["members"]) if phone_input else False
            nick_taken, nick_msg = is_nickname_taken(nick_input, db_data["registered_nicknames"]) if nick_input else (True, "")
            referrer_valid = len(referrer_input.strip()) > 0

            # تنبيهات فحص الرقم
            if phone_input:
                if not phone_valid:
                    st.caption("❌ يرجى كتابة رقم هاتف حقيقي مع المفتاح الدولي")
                elif phone_registered:
                    st.caption("❌ هذا الرقم مسجل سابقاً بالمجموعة! لا يمكن تكراره")
                else:
                    st.caption("✅ رقم الهاتف صحيح وغير مسجل سابقاً")

            # تنبيهات فحص اللقب
            if nick_input:
                if not nick_taken:
                    st.caption("✅ " + nick_msg)
                else:
                    st.caption("❌ " + nick_msg)

            form_ready = phone_valid and (not phone_registered) and (not nick_taken) and referrer_valid

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("تأكيد البيانات وتوليد رابط الدخول", disabled=not form_ready):
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

    # 6. الزر المخفي في أسفل الصفحة
    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.expander("🌸", expanded=False):
            admin_pass = st.text_input("رمز مرور المشرفين", type="password")
            if admin_pass == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
