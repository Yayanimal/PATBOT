import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="Cabinet Patrimonial & Fiscal",
    page_icon="🏛️",
    layout="wide"
)

# --- 2. GESTION INTELLIGENTE DES DOSSIERS ---
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}

if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

def get_dossier_names():
    return list(st.session_state.dossiers.keys())

# --- 3. BARRE LATÉRALE (LE BUREAU DU CGP) ---
with st.sidebar:
    # A. LE LOGO PRESTIGE (Doré sur fond sombre)
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        # Icône "Colonne Grecque Dorée" (Symbole Patrimoine) - URL fiable
        st.image("https://cdn-icons-png.flaticon.com/512/1995/1995515.png", width=60)
    with col_title:
        st.markdown(
            """
            <div style='margin-top: 10px;'>
                <h3 style='margin:0; color: #D4AF37; font-size: 20px;'>CABINET</h3>
                <p style='margin:0; color: #888; font-size: 12px;'>GESTION PRIVÉE & IA</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    st.markdown("---")

    # B. NAVIGATION & DOSSIERS
    st.caption("📂 NAVIGATION CLIENTS")
    
    # Bouton création
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    # Liste des dossiers
    dossier_list = get_dossier_names()
    
    # Sécurité anti-bug
    if not dossier_list:
        st.session_state.dossiers = {"Dossier 1": []}
        dossier_list = ["Dossier 1"]
        st.session_state.active_dossier = "Dossier 1"
    
    if st.session_state.active_dossier not in dossier_list:
        st.session_state.active_dossier = dossier_list[0]

    # Sélecteur de dossier
    selected_dossier = st.radio(
        "Dossiers ouverts :",
        dossier_list,
        index=dossier_list.index(st.session_state.active_dossier),
        label_visibility="collapsed"
    )
    
    if selected_dossier != st.session_state.active
