import streamlit as st
import google.generativeai as genai
import datetime

# --- 1. CONFIGURATION DE LA PAGE (Doit être la première ligne) ---
st.set_page_config(
    page_title="Copilot Patrimoine Pro",
    page_icon="🏛️",
    layout="wide"  # On passe en mode grand écran
)

# --- 2. FONCTIONS UTILITAIRES ---
def clear_chat():
    st.session_state.messages = []
    
# --- 3. BARRE LATÉRALE (SIDEBAR) - LE BUREAU DE L'EXPERT ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2600/2600219.png", width=80) # Une icône pro
    st.title("Espace Conseiller")
    st.markdown("---")
    
    # Bouton pour effacer la mémoire (Nouveau client)
    if st.button("🗑️ Nouveau Dossier Client", type="primary", use_container_width=True):
        clear_chat()
        st.rerun()

    st.markdown("### ⚙️ Contexte")
    # Petit bonus : on permet de régler l'année fiscale
    annee_fiscale = st.selectbox("Année Fiscale", ["2026", "2025", "2024"])
    profil = st.radio("Profil Client", ["Particulier", "Chef d'entreprise", "Non-résident"])

    st.markdown("---")
    st.warning(
        "⚠️ **AVERTISSEMENT JURIDIQUE**\n\n"
        "Cet assistant IA fournit des analyses à but informatif basées sur le CGI.\n"
        "Il ne remplace pas une consultation notariale ou un avocat fiscaliste.\n"
        "Vérifiez toujours les calculs avant engagement."
    )
    st.caption(f"Version du Bot : 1.2 | Modèle : Gemini Flash | {datetime.date.today()}")

# --- 4. CONNEXION SÉCURISÉE ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ Clé API introuvable.")
    st.stop()

# --- 5. CONFIGURATION DU CERVEAU ---
generation_config = {
    "temperature": 0.2, 
    "top_p": 0.95,
    "max_output_tokens": 8192,
}

try:
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest", 
        generation_config=generation_config
    )
except Exception as e:
    # Fallback si le dernier modèle bug
    model = genai.GenerativeModel("gemini-pro")

# --- 6. LA PERSONNALITÉ DE L'EXPERT (Mis à jour avec les variables) ---
system_instruction = f"""
RÔLE :
Tu es un Expert Senior en Gestion de Patrimoine (CGP) et Fiscalité Française.
Nous sommes en {annee_fiscale}. Ton client est un profil : {profil}.

RÈGLES D'OR :
1. BASE LÉGALE : Tes réponses s'appuient sur le Code Général des Impôts (CGI) et le BOFiP.
2. STRUCTURE : 
   - 1. Analyse Juridique
   - 2. Calculs / Simulation (Chiffrée obligatoirement)
   - 3. Recommandation Stratégique
   - 4. Points de vigilance (Risques)
3. SÉCURITÉ : Sois prudent. Si une loi est floue, dis-le.

TON :
Expert, pédagogue, structuré. Pas de blabla.
"""

# --- 7. ZONE PRINCIPALE (CHAT) ---
st.title("🏛️ Copilot Patrimoine & Fiscalité")
st.markdown(f"**Dossier en cours :** Analyse fiscale ({annee_fiscale}) pour profil *{profil}*.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Ex: Calcul de plus-value immobilière sur résidence secondaire..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Analyse des textes de loi et calculs en cours..."):
            try:
                full_prompt = system_instruction + "\n\nHistorique :\n"
                for msg in st.session_state.messages:
                    role = "CLIENT" if msg["role"] == "user" else "EXPERT"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += f"\nCLIENT: {prompt}\nEXPERT:"

                response = model.generate_content(full_prompt)
                message_placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Erreur : {e}")
