import streamlit as st
import google.generativeai as genai

# 1. Configuration de la page
st.set_page_config(page_title="Expert Patrimoine IA", page_icon="🏛️")
st.title("🏛️ Copilot Patrimoine (Yan1s)")
st.caption("Propulsé par Gemini 2.0 Flash - Expert Droit & Fiscalité")

# 2. Connexion sécurisée
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Clé API introuvable. Vérifiez les 'Secrets' de Streamlit.")
    st.stop()

# 3. Le Cerveau (Configuration mise à jour pour ta liste)
# On utilise le modèle que nous avons vu dans ta liste : gemini-2.0-flash
generation_config = {
    "temperature": 0.2, # 0.2 pour être très précis et rigoureux (pas de créativité folle)
    "top_p": 0.95,
    "max_output_tokens": 8192,
}

try:
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest", 
        generation_config=generation_config
    )
except Exception as e:
    st.error(f"Erreur de modèle : {e}")
    st.stop()

# 4. Mémoire de la conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. Affichage de l'historique
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    # On affiche différemment si c'est l'utilisateur ou l'IA
    with st.chat_message(role):
        st.markdown(content)

# 6. Gestion de la question utilisateur
if prompt := st.chat_input("Posez votre question fiscale ou patrimoniale..."):
    # Afficher la question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Générer la réponse
    with st.chat_message("assistant"):
        with st.spinner("Analyse des textes de loi en cours..."):
            try:
                # Le Prompt Système (La personnalité de l'expert)
                system_instruction = """
                Tu es un expert senior en Gestion de Patrimoine et Fiscalité Française.
                Tes règles d'or :
                1. Tes réponses doivent être basées STRICTEMENT sur le droit français (CGI, Code Civil).
                2. Cite toujours les articles de loi ou le BOFiP quand c'est pertinent.
                3. Si tu as un doute, dis-le. Ne jamais inventer une loi.
                4. Sois structuré, clair et pédagogue.
                """
                
                # Construction de la conversation pour l'IA
                chat = model.start_chat(history=[])
                # On envoie le contexte + la question
                full_query = f"{system_instruction}\n\nQuestion actuelle du client : {prompt}"
                
                response = chat.send_message(full_query)
                st.markdown(response.text)
                
                # Sauvegarde
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
