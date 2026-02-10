import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Cabinet Patrimonial & Fiscal", page_icon="🏛️", layout="wide")

# --- 2. GESTION DES DOSSIERS (SESSION) ---
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}
if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

def get_dossier_names():
    return list(st.session_state.dossiers.keys())

# --- 3. BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    # Logo et Titre
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/1995/1995515.png", width=50)
    with col2:
        st.markdown("<h3 style='margin:0; color:#D4AF37;'>CABINET IA</h3><p style='font-size:12px; color:grey;'>Gestion Privée</p>", unsafe_allow_html=True)
    
    st.divider()

    # Navigation Dossiers
    st.caption("🗂️ DOSSIERS CLIENTS")
    
    # Bouton Nouveau
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    # Liste des dossiers
    all_dossiers = get_dossier_names()
    # Sécurité si liste vide
    if not all_dossiers:
        st.session_state.dossiers = {"Dossier 1": []}
        all_
