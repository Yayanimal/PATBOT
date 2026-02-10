import streamlit as st
import sys
import subprocess

st.title("🛠️ Mode Réparation")

# 1. Vérification forcée de la version installée
try:
    import google.generativeai as genai
    version = genai.__version__
except:
    version = "Non installé"

st.write(f"**Version de l'outil Google installée :** `{version}`")
st.info("Pour que ça marche, il FAUT que la version soit supérieure à 0.8.3")

# 2. Test de la Clé API
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ Pas de clé trouvée dans les Secrets !")
    st.stop()
else:
    st.success(f"✅ Clé trouvée : {api_key[:5]}...")

# 3. Demander à Google quels modèles sont dispos pour TOI
if st.button("Lancer le Test de Connexion Google"):
    genai.configure(api_key=api_key)
    try:
        st.write("📞 Appel à Google en cours...")
        modeles = genai.list_models()
        
        found_models = []
        for m in modeles:
            if 'generateContent' in m.supported_generation_methods:
                found_models.append(m.name)
        
        if found_models:
            st.success(f"✅ Victoire ! Google nous répond. Voici les modèles disponibles pour ta clé :")
            st.json(found_models)
            st.write("Copie le nom d'un modèle ci-dessus (ex: `models/gemini-1.5-flash`) pour la suite.")
        else:
            st.warning("⚠️ Google répond, mais ne liste aucun modèle de texte. C'est bizarre.")
            
    except Exception as e:
        st.error(f"❌ Erreur critique : {e}")
