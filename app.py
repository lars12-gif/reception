import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials

st.title("🧪 اختبار الاتصال بقاعدة البيانات")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    # 1. قراءة وتنظيف المفتاح
    with open("bellona-504904-2c178e02693d.json", "r", encoding="utf-8") as f:
        info = json.load(f)
    
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")

    # 2. إنشاء الاعتمادات والاتصال
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    # 3. فتح الشيت وجلب البيانات
    sh = client.open("BELLONA_DB")
    worksheets = [ws.title for ws in sh.worksheets()]

    st.success("✅ تم الاتصال بنجاح!")
    st.write("📋 الأوراق الموجودة داخل الملف:")
    st.write(worksheets)

except Exception as e:
    st.error(f"❌ فشل الاتصال: {e}")
    
