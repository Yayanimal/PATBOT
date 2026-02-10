import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Expert Patrimoine IA", page_icon="🏛️")
st.title("🏛️ Copilot Patrimoine (Yan1s)")
st.caption("Expertise Juridique & Fiscale - Propulsé par Gemini Flash")

# --- 2. CONNEXION SÉCURISÉE (CLÉ API) ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ Clé API introuvable. Veuillez la configurer dans les 'Secrets' de Streamlit.")
    st.stop()

# --- 3. CONFIGURATION DU CERVEAU (LE MODÈLE) ---
# Paramètres pour une réponse précise (faible température = moins d'inventions)
generation_config = {
    "temperature": 0.2, 
    "top_p": 0.95,
    "max_output_tokens": 8192,
}

try:
    # On utilise LE modèle qui fonctionne sur ton compte
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest", 
        generation_config=generation_config
    )
except Exception as e:
    st.error(f"Erreur de chargement du modèle : {e}")
    st.stop()

# --- 4. LA PERSONNALITÉ DE L'EXPERT (SYSTÈME) ---
system_instruction = """
RÔLE :
Tu es un Expert Senior en Gestion de Patrimoine (CGP) et Fiscalité Française.
Ton interlocuteur est un investisseur ou un professionnel qui attend de la rigueur.

RÈGLES D'OR :
1. BASE LÉGALE : Tes réponses doivent s'appuyer strictement sur le Code Général des Impôts (CGI), le BOFiP et le Code Civil français.
2. PRÉCISION : Ne dis jamais "environ". Si tu ne sais pas, dis "Je dois vérifier le texte officiel".
3. STRUCTURE : Utilise des listes à puces. Sépare le Juridique (La règle) de la Stratégie (Le conseil).
4. SÉCURITÉ : Rappelle systématiquement que ton analyse est informative et ne remplace pas un notaire.
5. CONTEXTE : Nous sommes en 2026, prends en compte les lois de finances récentes.

TON :
Professionnel, direct, sans phrases creuses.
"""

# --- 5. GESTION DE LA MÉMOIRE (HISTORIQUE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher les anciens messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. INTERACTION AVEC L'UTILISATEUR ---
if prompt := st.chat_input("Posez votre question fiscale ou patrimoniale..."):
    
    # A. On affiche la question de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. On génère la réponse
    with st.chat_message("assistant"):
        with st.spinner("Consultation des textes de loi en cours..."):
            try:
                # On prépare le contexte complet pour l'IA
                # On lui rappelle qui elle est (system_instruction) + l'historique de la conversation
                full_prompt = system_instruction + "\n\nHistorique de la conversation :\n"
                
                for msg in st.session_state.messages:
                    role_label = "CLIENT" if msg["role"] == "user" else "EXPERT"
                    full_prompt += f"{role_label}: {msg['content']}\n"
                
                full_prompt += f"\nCLIENT (Question actuelle): {prompt}\nEXPERT:"

                # Appel à Google
                response = model.generate_content(full_prompt)
                
                # Affichage
                st.markdown(response.text)
                
                # Sauvegarde en mémoire
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
