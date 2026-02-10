import streamlit as st
import google.generativeai as genai
import datetime

# --- 1. CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="Cabinet Patrimonial & Fiscal",
    page_icon="⚖️",
    layout="wide"
)

# --- 2. GESTION INTELLIGENTE DES DOSSIERS ---
if "dossiers" not in st.session_state:
    # On commence avec un dossier par défaut
    st.session_state.dossiers = {"Dossier 1": []}

if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

# Fonction pour récupérer la liste des dossiers
def get_dossier_names():
    return list(st.session_state.dossiers.keys())

# --- 3. BARRE LATÉRALE (LE BUREAU DU CGP) ---
with st.sidebar:
    # A. LE LOGO PRO (Balance de Justice Stylisée / Finance)
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        # Logo abstrait doré/noir (plus sérieux)
        st.image("https://cdn-icons-png.flaticon.com/512/2759/2759773.png", width=60)
    with col_title:
        st.markdown("<h3 style='margin-top: 5px; color: #D4AF37;'>EXPERT<br>PATRIMOINE</h3>", unsafe_allow_html=True)
    
    st.markdown("---")

    # B. SÉLECTEUR DE DOSSIER (Navigation)
    st.caption("📂 NAVIGATION CLIENTS")
    
    # Création nouveau dossier
    if st.button("➕ Nouveau Dossier Client", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    # Liste des dossiers existants
    dossier_list = get_dossier_names()
    
    # Sécurité si aucun dossier (ne devrait pas arriver, mais au cas où)
    if not dossier_list:
        st.session_state.dossiers = {"Dossier 1": []}
        dossier_list = ["Dossier 1"]
        st.session_state.active_dossier = "Dossier 1"

    # Vérifier que le dossier actif existe bien (si on vient d'en supprimer un)
    if st.session_state.active_dossier not in dossier_list:
        st.session_state.active_dossier = dossier_list[0]

    selected_dossier = st.radio(
        "Sélectionnez un dossier :",
        dossier_list,
        index=dossier_list.index(st.session_state.active_dossier),
        label_visibility="collapsed"
    )
    
    # Mise à jour si changement
    if selected_dossier != st.session_state.active_dossier:
        st.session_state.active_dossier = selected_dossier
        st.rerun()

    # C. GESTION DU DOSSIER ACTIF (Renommer / Supprimer)
    with st.expander(f"⚙️ Gérer : {st.session_state.active_dossier}", expanded=False):
        
        # 1. Renommer
        new_name_input = st.text_input("Renommer le dossier :", value=st.session_state.active_dossier)
        if st.button("Valider le nom"):
            if new_name_input and new_name_input != st.session_state.active_dossier:
                # On copie les données vers le nouveau nom
                st.session_state.dossiers[new_name_input] = st.session_state.dossiers.pop(st.session_state.active_dossier)
                st.session_state.active_dossier = new_name_input
                st.rerun()

        # 2. Supprimer
        st.markdown("---")
        if st.button("🗑️ Supprimer ce dossier", type="primary"):
            if len(dossier_list) > 1:
                del st.session_state.dossiers[st.session_state.active_dossier]
                # On retourne au premier de la liste
                st.session_state.active_dossier = list(st.session_state.dossiers.keys())[0]
                st.rerun()
            else:
                st.error("Impossible de supprimer le dernier dossier.")

    st.markdown("---")

    # D. PARAMÈTRES D'EXPERTISE
    st.caption("🧠 PARAMÈTRES DE L'ANALYSE")
    
    # Profil avec le mode "Général" par défaut
    profil = st.selectbox(
        "Profil de l'investisseur", 
        ["Mode Général (Recherche)", "Particulier (IR)", "Chef d'entreprise (TNS)", "Société (IS)", "Non-résident"]
    )
    
    annee_fiscale = st.selectbox("Loi de Finances", ["2026", "2025", "2024"])

# --- 4. CONNEXION IA ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        generation_config={"temperature": 0.2, "top_p": 0.95}
    )
except Exception as e:
    st.error("⚠️ Clé API manquante ou invalide.")
    st.stop()

# --- 5. LOGIQUE DU CERVEAU (Adaptation au Mode Général) ---
instruction_profil = ""
if "Général" in profil:
    instruction_profil = "Ton client effectue une recherche généraliste. Donne des définitions claires, les grands principes et les seuils fiscaux, sans personnaliser à outrance."
else:
    instruction_profil = f"Ton client est un profil spécifique : {profil}. Adapte ta stratégie fiscale à ce statut."

system_instruction = f"""
RÔLE : Tu es un Expert Senior en Ingénierie Patrimoniale (CGP) et Fiscalité.
CONTEXTE : Nous sommes en {annee_fiscale}. {instruction_profil}

RÈGLES D'OR :
1. JURIDIQUE : Tes sources sont le CGI (Code Général des Impôts), le BOFiP et le Code Civil.
2. PRÉCISION : Si tu cites un chiffre (abattement, tranche), il doit être exact pour l'année {annee_fiscale}.
3. FORMAT : Structure tes réponses (Titres, Listes à puces).
4. RESPONSABILITÉ : Rappelle que l'analyse est informative.
"""

# --- 6. ZONE DE CHAT PRINCIPALE ---
st.title(f"📂 {st.session_state.active_dossier}")

# Sous-titre dynamique
if "Général" in profil:
    st.info(f"Mode Recherche (Loi de Finances {annee_fiscale}) - Pas de profil spécifique appliqué.")
else:
    st.success(f"Consultation pour profil **{profil}** - Loi de Finances {annee_fiscale}")

# Récupération historique
historique_actuel = st.session_state.dossiers[st.session_state.active_dossier]

# Affichage des bulles de chat
for message in historique_actuel:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
prompt_label = f"Posez votre question sur {st.session_state.active_dossier}..."
if prompt := st.chat_input(prompt_label):
    
    # 1. Sauvegarde User
    st.session_state.dossiers[st.session_state.active_dossier].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Génération IA
    with st.chat_message("assistant"):
        with st.spinner("Consultation des textes juridiques..."):
            try:
                # Prompt complet
                full_prompt = system_instruction + "\n\nHistorique de ce dossier :\n"
                for msg in historique_actuel:
                    role = "CLIENT" if msg["role"] == "user" else "EXPERT"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += f"\nCLIENT: {prompt}\nEXPERT:"

                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
                # 3. Sauvegarde AI
                st.session_state.dossiers[st.session_state.active_dossier].append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Erreur technique : {e}")

# Footer discret
st.markdown("---")
st.caption("Cabinet Digital IA - Usage professionnel à titre informatif.")
