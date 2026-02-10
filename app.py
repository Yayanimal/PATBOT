import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Cabinet Patrimoine", page_icon="🏛️", layout="wide")

# --- 2. VÉRIFICATION DE LA CLÉ API (IMMÉDIATE) ---
# On vérifie la clé tout de suite pour éviter l'écran blanc
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ ERREUR CRITIQUE : La clé API est introuvable dans les Secrets.")
    st.info("Allez dans Settings > Secrets et ajoutez GOOGLE_API_KEY.")
    st.stop()

# Configuration de l'IA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error(f"Erreur de connexion Google : {e}")
    st.stop()

# --- 3. GESTION DES DOSSIERS ---
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}
if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

def get_dossier_names():
    return list(st.session_state.dossiers.keys())

# --- 4. LA BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    # --- LOGO TYPOGRAPHIQUE DORÉ (Indestructible) ---
    st.markdown(
        """
        <div style="text-align: left; margin-bottom: 20px;">
            <div style="font-size: 40px;">🏛️</div>
            <h1 style="color: #D4AF37; font-size: 25px; margin: 0;">CABINET IA</h1>
            <p style="color: #888; font-size: 14px; margin: 0;">Gestion Privée & Fiscalité</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # --- NAVIGATION ---
    st.caption("🗂️ DOSSIERS CLIENTS")
    
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    dossiers_dispos = get_dossier_names()
    
    # Sécurité anti-crash
    if st.session_state.active_dossier not in dossiers_dispos:
        st.session_state.active_dossier = dossiers_dispos[0]

    # Sélecteur de dossier
    choix = st.radio(
        "Sélectionnez un dossier :", 
        dossiers_dispos, 
        index=dossiers_dispos.index(st.session_state.active_dossier),
        label_visibility="collapsed"
    )
    
    if choix != st.session_state.active_dossier:
        st.session_state.active_dossier = choix
        st.rerun()

    # --- OPTIONS ---
    with st.expander("⚙️ Options du dossier"):
        new_name = st.text_input("Renommer :", value=st.session_state.active_dossier)
        if st.button("Valider Nom"):
            if new_name and new_name != st.session_state.active_dossier:
                data = st.session_state.dossiers.pop(st.session_state.active_dossier)
                st.session_state.dossiers[new_name] = data
                st.session_state.active_dossier = new_name
                st.rerun()
        
        st.write("")
        if st.button("🗑️ Supprimer", type="primary"):
            if len(dossiers_dispos) > 1:
                del st.session_state.dossiers[st.session_state.active_dossier]
                st.session_state.active_dossier = list(st.session_state.dossiers.keys())[0]
                st.rerun()
            else:
                st.error("Impossible de supprimer le dernier dossier.")

    st.markdown("---")
    
    # --- PARAMÈTRES ---
    st.caption("⚖️ PARAMÈTRES EXPERTS")
    profil = st.selectbox("Profil", ["Mode Général (Recherche)", "Particulier", "Chef d'entreprise", "SCI", "Non-résident"])
    annee = st.selectbox("Année Fiscale", ["2026", "2025", "2024"])

# --- 5. L'INTELLIGENCE (Le Prompt) ---
contexte_profil = "Recherche généraliste, donne des définitions et seuils." if "Général" in profil else f"Le client est : {profil}. Adapte la stratégie."

system_instruction = f"""
RÔLE : Expert Senior en Gestion de Patrimoine et Fiscalité.
CONTEXTE : Année {annee}. {contexte_profil}
RÈGLES :
1. Sources : Code Général des Impôts (CGI) et BOFiP uniquement.
2. Format : Structure claire, liste à puces, calculs détaillés si nécessaire.
3. Sécurité : Rappelle que tu es une IA à titre informatif.
"""

# --- 6. INTERFACE PRINCIPALE (CHAT) ---
st.title(f"📂 {st.session_state.active_dossier}")
st.caption(f"Consultation : {profil} | Loi de Finances {annee}")

# Affichage Historique
chat_actuel = st.session_state.dossiers[st.session_state.active_dossier]
for msg in chat_actuel:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Zone de Saisie
if prompt := st.chat_input(f"Posez une question pour {st.session_state.active_dossier}..."):
    
    # 1. Message Utilisateur
    st.session_state.dossiers[st.session_state.active_dossier].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Réponse IA
    with st.chat_message("assistant"):
        with st.spinner("Analyse juridique en cours..."):
            try:
                # Construction conversation
                historique_texte = system_instruction + "\n\n"
                for m in chat_actuel:
                    historique_texte += f"{m['role'].upper()}: {m['content']}\n"
                historique_texte += f"USER: {prompt}\nASSISTANT:"
                
                response = model.generate_content(historique_texte)
                st.markdown(response.text)
                
                # Sauvegarde
                st.session_state.dossiers[st.session_state.active_dossier].append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
