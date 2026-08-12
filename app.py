import streamlit as st
import json
import os
import re
import phonenumbers
from difflib import SequenceMatcher
from datetime import datetime
from supabase import create_client, Client

# 1. كلمة السر الخاصة بداخلية الإشراف
ADMIN_PASSWORD = "bellona2026"

# 2. إعدادات الاتصال بـ Supabase
SUPABASE_URL = "https://igskxyazuomofeqvkwcy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlnc2t4eWF6dW9tb2ZlcXZrd2N5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYxNTkyNTksImV4cCI6MjEwMTczNTI1OX0.HadeqymBYWETFaauKYFNtlD-ahg3GfoOGoH0XKu_mWg"

@st.cache_resource
def init_supabase() -> Client:
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

supabase = init_supabase()

# 3. إعدادات الصفحة وجماليات الساكورا مع إخفاء الشريط العلوي والعلامة المائية تماماً
st.set_page_config(
    page_title="بوابة استقبال BELLONA",
    page_icon="🌸",
    layout="centered"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0f0a12;
        color: #f3e8ee;
        font-family: 'Cairo', sans-serif;
    }
    .main-card {
        background: rgba(30, 20, 32, 0.75);
        border: 1px solid #ffb3c6;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 0 25px rgba(255, 179, 198, 0.15);
        text-align: center;
        margin-bottom: 20px;
    }
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
    
    /* --- تحديث شامل وقوي جداً لإخفاء جميع عناصر Streamlit Cloud --- */
    [data-testid="stHeader"], 
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="manage-app-button"],
    #MainMenu, 
    header,
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* إخفاء الأيقونة العائمة الخاصة بالبروفايل (Viewer Badge) بأكثر من طريقة لضمان اختفائها */
    div[class^="viewerBadge_container"],
    div[class*="viewerBadge_container"],
    .viewerBadge_container__1QSob,
    a[class^="viewerBadge_link"],
    a[href*="streamlit.io/cloud"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        z-index: -9999 !important;
    }
</style>
""", unsafe_allow_html=True)

# 4. جلب البيانات من Supabase (تعديل الجدول إلى work_members ليتزامن تماماً مع الوورك)
def load_data():
    default_data = {
        "registered_nicknames": ["آرثر", "لامينو", "Arthur", "Lamino"],
        "members": []
    }
    if supabase is None:
        return default_data, False
    try:
        response = supabase.table("work_members").select("*").execute()
        records = response.data if response.data else []
        nicknames = [str(r.get("nickname", "")).strip() for r in records if r.get("nickname")]
        for dn in default_data["registered_nicknames"]:
            if dn not in nicknames:
                nicknames.append(dn)
        return {"registered_nicknames": nicknames, "members": records}, True
    except Exception:
        return default_data, False

db_data, is_online = load_data()

# مؤشر حالة الاتصال أعلى الصفحة (Online / Offline)
if is_online:
    st.markdown("<div style='text-align: left; color: #25d366; font-size: 13px; font-weight: bold; padding: 5px;'>🟢 متصل بقاعدة البيانات (Online)</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align: left; color: #ff4d4d; font-size: 13px; font-weight: bold; padding: 5px;'>🔴 غير متصل - يعمل بشكل محلي (Offline)</div>", unsafe_allow_html=True)

# 5. خوارزميات التنظيف والتحقق
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
    existing_phones = [str(m.get("phone", "")) for m in members_list]
    return clean_digits in existing_phones

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
            if new_admin_nick and new_admin_nick.strip():
                if new_admin_nick.strip() not in db_data["registered_nicknames"]:
                    db_data["registered_nicknames"].append(new_admin_nick.strip())
                    st.success(f"تم حجز اللقب بنجاح: {new_admin_nick}")
                    st.rerun()

    st.write("---")
    
    # 2. قسم سجل الأعضاء وإدارتهم (الحذف المتبادل من table work_members)
    st.markdown("### 📋 سجل الأعضاء وإدارة الحذف المتبادل")
    
    if db_data["members"]:
        reversed_members = list(reversed(db_data["members"]))
        member_options = [f"{m.get('nickname', 'بدون لقب')} - ({m.get('phone', 'بدون رقم')})" for m in reversed_members]
        
        selected_option = st.selectbox("اختر العضو لعرض تفاصيله أو حذفه:", options=member_options)
        selected_index = member_options.index(selected_option)
        selected_member = reversed_members[selected_index]
        
        st.markdown(f"""
        <div style="background: rgba(255, 179, 198, 0.08); border: 1px solid #ffb3c6; border-radius: 12px; padding: 18px; margin-top: 15px;">
            <p style="margin: 4px 0;">👑 <b>اللقب:</b> {selected_member.get('nickname', '')}</p>
            <p style="margin: 4px 0;">📱 <b>الرقم:</b> {selected_member.get('phone', '')}</p>
            <p style="margin: 4px 0;">🤝 <b>صاحب الدعوة:</b> {selected_member.get('referrer', 'مباشر')}</p>
            <p style="margin: 4px 0;">🤝 <b>مسؤول الاستقبال:</b> {selected_member.get('received_by', 'غير محدد')}</p>
            <p style="margin: 4px 0; font-size: 12px; color: #ff7aa2;">📅 <b>تاريخ التسجيل:</b> {selected_member.get('date', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(f"🗑️ حذف العضو ({selected_member.get('nickname', '')})"):
            if supabase:
                try:
                    supabase.table("work_members").delete().eq("phone", str(selected_member.get('phone', ''))).execute()
                except Exception as e:
                    st.error(f"خطأ أثناء الحذف من القاعدة: {e}")
            st.success(f"تم حذف العضو ({selected_member.get('nickname', '')}) بنجاح من النظامين!")
            st.rerun()
            
        st.markdown("<br><b>📝 رسالة الترحيب المجهزة للواتساب:</b>", unsafe_allow_html=True)
        clean_tag = selected_member.get('phone', '')
        welcome_text = (
            f"🌸 ✨ أهـلاً وسهـلاً بـالعـضـو الـجـديـد ✨ 🌸\n\n"
            f"👑 اللقب: {selected_member.get('nickname', '')}\n"
            f"📱 الرقم: @{clean_tag}\n"
            f"🏰 مرحباً بك في عالم BELLONA 🌟\n\n"
            f"نورت الجروب يا بطل! يسعدنا انضمامك لعائلتنا الرهيبة 🔥🤍"
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
            referrer_input = st.text_input("صاحب الدعوة (المستضيف)", placeholder="اسم العضو صاحب الدعوة")
            receiver_input = st.text_input("تم الاستقبال من طرف (مسؤول الاستقبال)", placeholder="اسم مسؤول الاستقبال")

            phone_valid = is_valid_phone(phone_input)
            phone_registered = is_phone_registered(phone_input, db_data["members"]) if phone_input else False
            nick_taken, nick_msg = is_nickname_taken(nick_input, db_data["registered_nicknames"]) if nick_input else (True, "")
            referrer_valid = len(referrer_input.strip()) > 0

            if phone_input:
                if not phone_valid:
                    st.caption("❌ يرجى كتابة رقم هاتف حقيقي مع المفتاح الدولي")
                elif phone_registered:
                    st.caption("❌ هذا الرقم مسجل سابقاً بالمجموعة!")
                else:
                    st.caption("✅ رقم الهاتف صحيح وغير مسجل سابقاً")

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
                    "nickname": nick_input.strip(),
                    "phone": clean_digits_only,
                    "referrer": referrer_input.strip(),
                    "received_by": receiver_input.strip() if receiver_input.strip() else "غير محدد",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if supabase:
                    try:
                        supabase.table("work_members").insert(new_entry).execute()
                    except Exception as e:
                        st.error(f"خطأ في الحفظ بقاعدة البيانات: {e}")
                
                st.session_state.submitted = True
                st.rerun()

    else:
        st.success("🎉 تم التحقق من بياناتك وتسجيل لقبك بنجاح!")
        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <a href="https://chat.whatsapp.com/EQ2EuFZkd93Ie6YuygTe00?s=cl&p=a&ilr=0" target="_blank" style="
                display: inline-block; padding: 14px 28px; background: #25d366; color: white;
                text-decoration: none; font-weight: bold; border-radius: 12px;
            ">📱 دخول جروب BELLONA الآن</a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.expander("🌸", expanded=False):
            admin_pass = st.text_input("رمز مرور المشرفين", type="password")
            if admin_pass == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
