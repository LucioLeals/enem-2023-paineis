import streamlit as st

st.set_page_config(page_title="ENEM 2023: estatística", layout="wide")
st.navigation([
    st.Page("paginas/painel1.py", title="Painel 1: população", url_path="populacao"),
    st.Page("paginas/painel2.py", title="Painel 2: amostra", url_path="amostra"),
    st.Page("paginas/painel3.py", title="Painel 3: inferência", url_path="inferencia"),
]).run()
