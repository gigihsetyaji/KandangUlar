import streamlit as st

st.set_page_config(page_title="KandangUlar", page_icon="🐍")
st.title("🐍 KandangUlar")
st.write("Dashboard demonstrasi integrasi Python.")
st.info("Dashboard ini hanya menampilkan data contoh. Hubungkan identitas pengguna sebelum menambahkan data privat.")
st.bar_chart({"Django": [3, 5, 8], "FastAPI": [4, 7, 10], "Flask": [2, 3, 4]})
st.caption("Angka ilustrasi, bukan metrik produksi.")
