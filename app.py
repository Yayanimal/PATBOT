import streamlit as st
import google.generativeai as genai
import datetime

# --- 1. CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="Cabinet Patrimonial IA",
    page_icon="🏛️",
    layout="wide"
)

# --- 2. GESTION DE LA MÉMOIRE (MULTI-DOSSIERS) ---
# On initialise le "Classeur" s'il n'existe pas
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}  # Un premier dossier vide
if "current_dossier" not in st.session_state:
    st.session_state.current_dossier = "Dossier 1"
if "dossier_counter" not in st.session_state:
    st.session_state.dossier_counter = 1

def creer_nouveau_dossier():
    st.session_state.dossier_counter += 1
    nom_dossier = f"Dossier {st.session_state.dossier_counter}"
    st.session_state.dossiers[nom_dossier] = []
    st.session_state.current_dossier = nom_dossier

# --- 3. BARRE LATÉRALE (DESIGN PRO & NAVIGATION) ---
with st.sidebar:
    # --- HEADER PRO ---
    col1, col2 = st.columns([1, 4])
    with col1:
        # Logo "Banque Privée" (Doré et sobre)
        st.image("https://cdn-icons-png.flaticon.com/512/9322/9322127.png", width=50)
    with col2:
        st.markdown("<h3 style='margin: 0; padding-top: 10px; color: #C5A059;'>PATRIMOINE<br>ADVISOR</h3>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- GESTION DES DOSSIERS ---
    st.caption("📁 MES DOSSIERS CLIENTS")
    
    # Bouton pour créer un nouveau dossier
    if st.button("➕ Nouveau Client", use_container_width=True):
        creer_nouveau_dossier()
        st.rerun()

    # Liste déroulante pour changer de dossier
    liste_dossiers = list(st.session_state.dossiers.keys())
    selection = st.radio(
        "Dossier actif :",
        liste_dossiers,
        index=liste_dossiers.index(st.session_state.current_dossier),
        label_visibility="collapsed"
    )
    
    # Mise à jour du dossier courant si on change la sélection
    if selection != st.session_state.current_dossier:
        st.session_state.current_dossier = selection
        st.rerun()

    st.markdown("---")

    # --- PARAMÈTRES CONTEXTUELS ---
    st.caption("⚙️ CONTEXTE FISCAL")
    annee_fiscale = st.selectbox("Année de référence", ["2026", "2025", "2024"])
    profil = st.selectbox("Profil Investisseur", ["Particulier (IR)", "Chef d'entreprise (TNS)", "Société (IS)", "Non-résident"])
    
    st.info(f"Dossier en cours : **{st.session_state.current_dossier}**")

# --- 4. CONNEXION IA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # Modèle configuré
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        generation_config={"temperature": 0.2, "top_p": 0.95}
    )
except Exception as e:
    st.error("⚠️ Erreur de connexion API.")
    st.stop()

# --- 5. LOGIQUE DU CERVEAU (PROMPT EXPERT) ---
system_instruction = f"""
RÔLE : Tu es un Expert en Stratégie Patrimoniale et Fiscale (Senior).
CONTEXTE : Nous sommes en {annee_fiscale}. Ton client est : {profil}.

RÈGLES STRICTES :
1. JURIDIQUE : Base-toi uniquement sur le CGI (Code Général des Impôts) et le BOFiP.
2. MÉTHODE : 
   - Rappel de la règle.
   - Calcul précis (Si des chiffres sont donnés).
   - Conclusion stratégique.
3. FORMAT : Utilise du Markdown propre (Gras, Listes, Tableaux si besoin).
4. SÉCURITÉ : Mentionne toujours que cela ne remplace pas un acte notarié.
"""

# --- 6. ZONE DE CHAT PRINCIPALE ---
st.title(f"📂 {st.session_state.current_dossier}")
st.caption(f"Consultation pour profil {profil} - Loi de Finance {annee_fiscale}")

# Récupération de l'historique du dossier ACTIF uniquement
historique_actuel = st.session_state.dossiers[st.session_state.current_dossier]

# Affichage des messages
for message in historique_actuel:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input(f"Posez une question pour le {st.session_state.current_dossier}..."):
    
    # 1. Ajout message utilisateur dans le dossier courant
    st.session_state.dossiers[st.session_state.current_dossier].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Génération réponse
    with st.chat_message("assistant"):
        with st.spinner("Analyse experte en cours..."):
            try:
                # Construction du prompt avec le contexte spécifique
                full_prompt = system_instruction + "\n\nHistorique :\n"
                for msg in historique_actuel:
                    role = "CLIENT" if msg["role"] == "user" else "EXPERT"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += f"\nCLIENT: {prompt}\nEXPERT:"

                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
                # 3. Sauvegarde réponse dans le dossier courant
                st.session_state.dossiers[st.session_state.current_dossier].append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Erreur : {e}")
