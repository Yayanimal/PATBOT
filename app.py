import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import base64

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="PATBOT | Gestion Privée",
    page_icon="🏛️",
    layout="wide"
)

# --- 2. TON LOGO (Lien GitHub Raw reconstitué) ---
# C'est le lien direct vers ton image blanche pour le mode sombre
LOGO_URL = "https://raw.githubusercontent.com/yayanimal/PATBOT/main/logo_blanc.jpg"

# --- 3. FONCTION DE GÉNÉRATION PDF (Rapport Client) ---
def create_pdf(dossier_name, chat_history, profil, annee):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.set_text_color(212, 175, 55) # Couleur Or
            self.cell(0, 10, 'CABINET PATBOT - GESTION PRIVÉE', 0, 1, 'C')
            self.line(10, 20, 200, 20)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # En-tête du dossier
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Dossier : {dossier_name}", 0, 1, 'L')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Profil : {profil} | Loi de Finances {annee}", 0, 1, 'L')
    pdf.ln(10)
    
    # Contenu de la conversation
    for message in chat_history:
        role = "CLIENT" if message["role"] == "user" else "EXPERT PATBOT"
        
        pdf.set_font("Arial", 'B', 11)
        if role == "EXPERT PATBOT":
            pdf.set_text_color(212, 175, 55) # Or pour le bot
        else:
            pdf.set_text_color(50, 50, 50) # Gris pour le client
            
        pdf.cell(0, 10, role, 0, 1)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        
        # Nettoyage des caractères spéciaux (Emoji support limité en PDF standard)
        text_content = message["content"].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, text_content)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. CONNEXION IA (Modèle Flash Latest) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ La clé API est manquante dans les Secrets.")
    st.stop()

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Le modèle qui fonctionne sur ton compte :
    model = genai.GenerativeModel("gemini-flash-latest")
except Exception as e:
    st.error(f"Erreur de connexion Google : {e}")
    st.stop()

# --- 5. PROFILS EXPERTS (Intelligence Métier) ---
PROFILS_DETAILS = {
    "🔍 Mode Général": "Encyclopédie fiscale. Définitions et grands principes.",
    "👤 Jeune Actif": "Accumulation. PEA, Résidence Principale, PER.",
    "👨‍👩‍👧‍👦 Famille": "Protection conjoint, Transmission, Optimisation successorale.",
    "👔 Chef d'Entreprise": "Dividendes vs Salaire, Holding, Dutreil, Cession.",
    "🏖️ Retraité": "Revenus complémentaires, LMNP, Succession, Assurance Vie.",
    "🏢 Investisseur Immo": "SCI IS/IR, Déficit Foncier, Cash-flow, Malraux.",
    "🌍 Non-Résident": "Conventions fiscales, Retenue à la source, IFI."
}

# --- 6. GESTION DES DOSSIERS ---
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}
if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

def get_dossier_names(): return list(st.session_state.dossiers.keys())

# --- 7. BARRE LATÉRALE (INTERFACE PRO) ---
with st.sidebar:
    # A. LOGO & MARQUE
    try:
        st.image(LOGO_URL, width=120) # Ton logo blanc
    except:
        st.warning("Logo en chargement...")
        st.title("PATBOT")

    st.markdown("""
        <h3 style='color: #D4AF37; margin: 0; padding-top: 10px;'>CABINET DIGITAL</h3>
        <p style='font-size: 12px; color: #888;'>Powered by Patbot AI</p>
        <hr style='margin-top: 5px; margin-bottom: 20px;'>
    """, unsafe_allow_html=True)
    
    # B. NAVIGATION
    st.caption("🗂️ DOSSIERS CLIENTS")
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    dossiers = get_dossier_names()
    # Sécurité liste vide
    if not dossiers:
        st.session_state.dossiers = {"Dossier 1": []}
        dossiers = ["Dossier 1"]
    
    if st.session_state.active_dossier not in dossiers:
        st.session_state.active_dossier = dossiers[0]

    choix = st.radio("Sélection", dossiers, index=dossiers.index(st.session_state.active_dossier), label_visibility="collapsed")
    if choix != st.session_state.active_dossier:
        st.session_state.active_dossier = choix
        st.rerun()

    # C. OUTILS (Renommer / Supprimer / PDF)
    with st.expander("⚙️ Options & Export PDF"):
        # Renommer
        new_name = st.text_input("Nom du dossier :", value=st.session_state.active_dossier)
        if st.button("Renommer"):
            if new_name and new_name != st.session_state.active_dossier:
                st.session_state.dossiers[new_name] = st.session_state.dossiers.pop(st.session_state.active_dossier)
                st.session_state.active_dossier = new_name
                st.rerun()
        
        # Supprimer
        if st.button("🗑️ Supprimer le dossier", type="primary"):
            if len(dossiers) > 1:
                del st.session_state.dossiers[st.session_state.active_dossier]
                st.session_state.active_dossier = list(st.session_state.dossiers.keys())[0]
                st.rerun()
            else:
                st.error("Impossible de supprimer le dernier dossier.")
        
        st.markdown("---")
        
        # EXPORT PDF
        if st.button("📄 Générer Rapport PDF"):
            if st.session_state.dossiers[st.session_state.active_dossier]:
                pdf_bytes = create_pdf(
                    st.session_state.active_dossier,
                    st.session_state.dossiers[st.session_state.active_dossier],
                    st.session_state.get("last_profil", "Général"),
                    st.session_state.get("last_annee", "2026")
                )
                st.download_button(
                    label="⬇️ Télécharger le PDF",
                    data=pdf_bytes,
                    file_name=f"Rapport_{st.session_state.active_dossier}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("Le dossier est vide.")

    st.markdown("---")
    
    # D. PARAMÈTRES
    st.caption("⚖️ CONTEXTE FISCAL")
    profil = st.selectbox("Profil Client", list(PROFILS_DETAILS.keys()))
    annee = st.selectbox("Année de référence", ["2026", "2025", "2024"])
    
    # Sauvegarde des choix pour le PDF
    st.session_state.last_profil = profil
    st.session_state.last_annee = annee

# --- 8. PROMPT SYSTÈME ---
system_instruction = f"""
RÔLE : Tu es l'IA PATBOT, Expert Senior en Gestion de Patrimoine et Fiscalité.
CONTEXTE : Année {annee}.
PROFIL CLIENT : {profil} ({PROFILS_DETAILS[profil]})

TES RÈGLES :
1. JURIDIQUE : Tes réponses doivent être basées sur le CGI et le BOFiP.
2. PRÉCISION : Fais des simulations chiffrées si on te donne des montants.
3. PRÉSENTATION : Utilise du Markdown (Gras, Titres, Listes) pour être clair.
"""

# --- 9. INTERFACE DE CHAT ---
st.title(f"📂 {st.session_state.active_dossier}")

# Historique des messages
for msg in st.session_state.dossiers[st.session_state.active_dossier]:
    # Avatar : Ton logo pour le bot, rien pour l'user
    avatar_img = LOGO_URL if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar_img):
        st.markdown(msg["content"])

# Zone de saisie
if prompt := st.chat_input(f"Question pour le dossier {st.session_state.active_dossier}..."):
    
    # 1. User
    st.session_state.dossiers[st.session_state.active_dossier].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. IA PATBOT
    with st.chat_message("assistant", avatar=LOGO_URL):
        with st.spinner("Analyse PATBOT en cours..."):
            try:
                # Historique complet pour la mémoire
                history_text = system_instruction + "\n\n"
                for m in st.session_state.dossiers[st.session_state.active_dossier]:
                    history_text += f"{m['role'].upper()}: {m['content']}\n"
                history_text += f"USER: {prompt}\nASSISTANT:"
                
                response = model.generate_content(history_text)
                st.markdown(response.text)
                
                st.session_state.dossiers[st.session_state.active_dossier].append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
