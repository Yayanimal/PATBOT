import streamlit as st
import google.generativeai as genai

# 1. Configuration de la page
st.set_page_config(page_title="Expert Patrimoine IA", page_icon="🏛️")

st.title("🏛️ Copilot Gestion de Patrimoine")
st.markdown("Posez vos questions sur la fiscalité, l'immobilier ou la succession.")

# 2. Connexion à Google Gemini (via les secrets Streamlit)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Clé API manquante. Ajoutez-la dans les secrets Streamlit.")
    st.stop()

# 3. Définition du Cerveau (Le Modèle)
model = genai.GenerativeModel('gemini-pro')

# 4. Historique de chat (pour qu'il se souvienne de la conversation)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher les anciens messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Zone de saisie utilisateur
if prompt := st.chat_input("Ex: Quelle est la fiscalité du LMNP en 2026 ?"):
    # Afficher la question de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 6. Génération de la réponse
    with st.chat_message("assistant"):
        with st.spinner("Analyse juridique en cours..."):
            # Le "System Prompt" caché qui force le mode Expert
            consigne_expert = """
            Tu es un expert senior en Gestion de Patrimoine (CGP) en France.
            Tes réponses doivent être :
            1. Juridiquement précises (Droit français uniquement).
            2. Pédagogiques mais techniques.
            3. Prudentes (rappelle toujours que cela ne remplace pas un avis notarié).
            
            Si la question concerne un calcul, explique la méthode.
            """
            
            try:
                # On envoie la consigne + l'historique + la nouvelle question
                full_prompt = consigne_expert + "\n\nHistorique de conversation:\n" 
                for msg in st.session_state.messages:
                    full_prompt += f"{msg['role']}: {msg['content']}\n"
                
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
                # Sauvegarder la réponse
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")
