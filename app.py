import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Cabinet Patrimoine", page_icon="🏛️", layout="wide")

# --- 2. VÉRIFICATION CLÉ API ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ CLÉ MANQUANTE : Ajoutez GOOGLE_API_KEY dans les Secrets.")
    st.stop()

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error(f"Erreur technique : {e}")
    st.stop()

# --- 3. DÉFINITION DES PROFILS EXPERTS (La "Carte d'Identité") ---
# C'est ici qu'on "éduque" l'IA sur chaque type de client
PROFILS_DETAILS = {
    "🔍 Mode Général (Recherche)": 
        "Tu es une encyclopédie fiscale. Donne des définitions, des seuils et des principes généraux. Ne personnalise pas.",
        
    "👤 Jeune Actif / Cadre (Phase de constitution)": 
        "Le client est en phase d'accumulation. Priorités : Épargne progressive (PEA, AV), Achat Résidence Principale, Défiscalisation simple (PER).",
        
    "👨‍👩‍👧‍👦 Famille & Patrimoine (Protection & Transmission)": 
        "Le client a des enfants et un patrimoine établi. Priorités : Protection du conjoint (Donation au dernier vivant), Transmission anticipée, Optimisation successorale, Immobilier familial.",
        
    "👔 Chef d'Entreprise (TNS / Holding / Cession)": 
        "Le client est entrepreneur. Priorités : Arbitrage Rémunération/Dividendes, Holding, Pacte Dutreil, Cession d'entreprise (Apport-Cession 150-0 B ter), Retraite Madelin.",
        
    "🏖️ Retraité (Revenus & Transmission)": 
        "Le client est à la retraite. Priorités : Génération de revenus complémentaires immédiats (LMNP, SCPI), Protection contre l'inflation, Préparation de la succession (Assurance Vie avant/après 70 ans).",
        
    "🏢 Investisseur Immobilier (LMNP / SCI / Déficit)": 
        "Le client est un investisseur averti. Priorités : Choix SCI (IS/IR) vs Nom Propre, LMNP Réel, Déficit Foncier, Malraux/Monuments Historiques, calcul de Cash-flow et Rentabilité.",
        
    "🌍 Expatrié / Non-Résident": 
        "Le client ne vit pas en France mais y a des intérêts. Priorités : Convention fiscale internationale, Retenue à la source, IFI (sur immo français uniquement), Régime des impatriés."
}

# --- 4. GESTION DES DOSSIERS ---
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}
if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

def get_dossier_names():
    return list(st.session_state.dossiers.keys())

# --- 5. BARRE LATÉRALE ---
with st.sidebar:
    # Logo Texte Doré
    st.markdown("""
        <div style="text-align: left; margin-bottom: 20px;">
            <div style="font-size: 40px;">🏛️</div>
            <h1 style="color: #D4AF37; font-size: 24px; margin: 0;">CABINET IA</h1>
            <p style="color: #888; font-size: 13px; margin: 0;">Gestion Privée & Ingénierie</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("🗂️ GESTION CLIENTS")
    
    # Bouton Nouveau
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    dossiers_dispos = get_dossier_names()
    if st.session_state.active_dossier not in dossiers_dispos:
        st.session_state.active_dossier = dossiers_dispos[0]

    # Sélecteur Dossier
    choix = st.radio("Sélectionnez un dossier :", dossiers_dispos, index=dossiers_dispos.index(st.session_state.active_dossier), label_visibility="collapsed")
    if choix != st.session_state.active_dossier:
        st.session_state.active_dossier = choix
        st.rerun()

    # Options Dossier
    with st.expander("⚙️ Renommer / Supprimer"):
        new_name = st.text_input("Nom :", value=st.session_state.active_dossier)
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
    
    # --- SÉLECTEUR DE PROFIL AVANCÉ ---
    st.caption("⚖️ STRATÉGIE PATRIMONIALE")
    
    # On affiche les clés du dictionnaire (les noms avec emojis)
    choix_profil = st.selectbox("Type de Profil", list(PROFILS_DETAILS.keys()))
    
    annee = st.selectbox("Loi de Finances", ["2026", "2025", "2024"])

# --- 6. INTELLIGENCE ARTIFICIELLE ---

# On récupère la consigne cachée associée au profil choisi
consigne_specifique = PROFILS_DETAILS[choix_profil]

system_instruction = f"""
RÔLE : Tu es un Expert Senior en Ingénierie Patrimoniale et Fiscale (Niveau Master 2 Gestion de Patrimoine).
CONTEXTE ACTUEL : Loi de Finances {annee}.

PROFIL CLIENT : {choix_profil}
DÉTAILS STRATÉGIQUES À APPLIQUER : {consigne_specifique}

TES RÈGLES D'OR :
1. JURIDIQUE : Cite systématiquement les articles du CGI (Code Général des Impôts) ou du BOFiP pertinents.
2. PRÉCISION : Si le client demande un calcul, fais une simulation détaillée.
3. CONSEIL : Ne te contente pas de la loi, donne le "Conseil de l'expert" (ex: attention à l'abus de droit, attention au plafonnement des niches).
4. FORMAT : Utilise du Markdown (Gras, Titres, Listes) pour rendre la réponse lisible.
"""

# --- 7. INTERFACE DE CHAT ---
st.title(f"📂 {st.session_state.active_dossier}")

# Petit bandeau contextuel pour savoir qui on traite
st.info(f"**Profil analysé :** {choix_profil} | **Référentiel :** {annee}")

chat_actuel = st.session_state.dossiers[st.session_state.active_dossier]

for msg in chat_actuel:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Posez une question pour ce profil..."):
    st.session_state.dossiers[st.session_state.active_dossier].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyse experte en cours..."):
            try:
                # On envoie l'historique complet pour que l'IA ait la mémoire
                history_text = system_instruction + "\n\n"
                for m in chat_actuel:
                    history_text += f"{m['role'].upper()}: {m['content']}\n"
                history_text += f"USER: {prompt}\nASSISTANT:"
                
                response = model.generate_content(history_text)
                st.markdown(response.text)
                
                st.session_state.dossiers[st.session_state.active_dossier].append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur API : {e}")
