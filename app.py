import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION DE LA PAGE & IDENTITÉ ---
st.set_page_config(page_title="Cabinet Patrimoine IA", page_icon="🏛️", layout="wide")

# URL du Logo (C'est ici que tu peux changer l'image si tu en as une perso)
# J'ai choisi un icône "Banque/Institution" doré très propre qui passe sur fond sombre.
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2600/2600219.png"

# --- 2. VÉRIFICATION CLÉ API ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ CLÉ MANQUANTE : Ajoutez GOOGLE_API_KEY dans les Secrets.")
    st.stop()

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-flash-latest")
except Exception as e:
    st.error(f"Erreur technique : {e}")
    st.stop()

# --- 3. PROFILS EXPERTS ---
PROFILS_DETAILS = {
    "🔍 Mode Général (Recherche)": 
        "Tu es une encyclopédie fiscale. Donne des définitions et des grands principes.",
    "👤 Jeune Actif / Cadre": 
        "Phase d'accumulation. Priorités : Épargne (PEA, AV), Résidence Principale, Défiscalisation (PER).",
    "👨‍👩‍👧‍👦 Famille & Patrimoine": 
        "Priorités : Protection du conjoint, Transmission, Optimisation successorale.",
    "👔 Chef d'Entreprise (TNS)": 
        "Priorités : Rémunération vs Dividendes, Holding, Pacte Dutreil, Cession, Retraite Madelin.",
    "🏖️ Retraité": 
        "Priorités : Compléments de revenus, Protection inflation, Succession, LMNP.",
    "🏢 Investisseur Immo": 
        "Priorités : SCI (IS/IR), LMNP Réel, Déficit Foncier, Cash-flow.",
    "🌍 Non-Résident": 
        "Priorités : Convention fiscale, Retenue à la source, IFI."
}

# --- 4. GESTION DOSSIERS ---
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}
if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

def get_dossier_names():
    return list(st.session_state.dossiers.keys())

# --- 5. BARRE LATÉRALE (SIDEBAR) AVEC LOGO ---
with st.sidebar:
    # A. LE LOGO MARQUE (En haut à gauche)
    col_logo, col_text = st.columns([1, 3])
    with col_logo:
        st.image(LOGO_URL, width=70)
    with col_text:
        st.markdown("""
            <h3 style='color: #D4AF37; margin-bottom: 0;'>CABINET IA</h3>
            <p style='font-size: 12px; color: grey; margin-top: -5px;'>Gestion Privée</p>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # B. NAVIGATION
    st.caption("🗂️ DOSSIERS CLIENTS")
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    dossiers_dispos = get_dossier_names()
    if st.session_state.active_dossier not in dossiers_dispos:
        st.session_state.active_dossier = dossiers_dispos[0]

    choix = st.radio("Sélection", dossiers_dispos, index=dossiers_dispos.index(st.session_state.active_dossier), label_visibility="collapsed")
    if choix != st.session_state.active_dossier:
        st.session_state.active_dossier = choix
        st.rerun()

    # C. PARAMÈTRES
    with st.expander("⚙️ Options"):
        new_name = st.text_input("Renommer :", value=st.session_state.active_dossier)
        if st.button("Valider"):
            if new_name and new_name != st.session_state.active_dossier:
                st.session_state.dossiers[new_name] = st.session_state.dossiers.pop(st.session_state.active_dossier)
                st.session_state.active_dossier = new_name
                st.rerun()
        if st.button("🗑️ Supprimer", type="primary"):
            if len(dossiers_dispos) > 1:
                del st.session_state.dossiers[st.session_state.active_dossier]
                st.session_state.active_dossier = list(st.session_state.dossiers.keys())[0]
                st.rerun()

    st.markdown("---")
    st.caption("⚖️ CONTEXTE")
    choix_profil = st.selectbox("Profil", list(PROFILS_DETAILS.keys()))
    annee = st.selectbox("Référentiel", ["2026", "2025", "2024"])

# --- 6. CERVEAU IA ---
system_instruction = f"""
RÔLE : Expert Senior en Gestion de Patrimoine.
CONTEXTE : {annee}. Profil : {choix_profil}.
RÈGLES :
1. Sources : CGI et BOFiP.
2. Structure : Introduction juridique > Calculs/Chiffres > Conseil Stratégique.
3. Sécurité : Rappelle le caractère informatif.
"""

# --- 7. ZONE DE CHAT (AVEC AVATAR) ---
st.title(f"📂 {st.session_state.active_dossier}")
st.info(f"**Expertise en cours :** {choix_profil} ({annee})")

chat_actuel = st.session_state.dossiers[st.session_state.active_dossier]

# Affichage des messages passés
for msg in chat_actuel:
    # Si c'est l'assistant, on met le LOGO. Si c'est l'utilisateur, on laisse par défaut (ou on met None)
    avatar_icon = LOGO_URL if msg["role"] == "assistant" else None
    
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# Nouvelle question
if prompt := st.chat_input("Votre question..."):
    # 1. User
    st.session_state.dossiers[st.session_state.active_dossier].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Assistant (Avec Avatar Logo)
    with st.chat_message("assistant", avatar=LOGO_URL):
        with st.spinner("Analyse en cours..."):
            try:
                history_text = system_instruction + "\n\n"
                for m in chat_actuel:
                    history_text += f"{m['role'].upper()}: {m['content']}\n"
                history_text += f"USER: {prompt}\nASSISTANT:"
                
                response = model.generate_content(history_text)
                st.markdown(response.text)
                st.session_state.dossiers[st.session_state.active_dossier].append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur : {e}")
