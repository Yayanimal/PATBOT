import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="PATBOT | Gestion Privée",
    page_icon="🏛️",
    layout="wide"
)

# --- 2. GESTION DU LOGO (CORRECTION DU NOM) ---
# J'ai mis le nom EXACT que j'ai vu sur ton GitHub (avec les espaces et .png)
LOGO_FILENAME = "PATBOT LOGO BLANC.png"

# --- 3. FONCTION PDF ---
def create_pdf(dossier_name, chat_history, profil, annee):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.set_text_color(212, 175, 55)
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
    
    # Titre
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Dossier : {dossier_name}", 0, 1, 'L')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Profil : {profil} | Loi de Finances {annee}", 0, 1, 'L')
    pdf.ln(10)
    
    # Contenu
    for message in chat_history:
        role = "CLIENT" if message["role"] == "user" else "EXPERT PATBOT"
        pdf.set_font("Arial", 'B', 11)
        if role == "EXPERT PATBOT":
            pdf.set_text_color(212, 175, 55)
        else:
            pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 10, role, 0, 1)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        text_content = message["content"].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, text_content)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. CONNEXION IA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Clé API manquante.")
    st.stop()

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-flash-latest")
except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# --- 5. PROFILS ---
PROFILS_DETAILS = {
    "🔍 Mode Général": "Encyclopédie fiscale.",
    "👤 Jeune Actif": "PEA, RP, PER.",
    "👨‍👩‍👧‍👦 Famille": "Transmission, Protection.",
    "👔 Chef d'Entreprise": "Holding, Dutreil, Dividendes.",
    "🏖️ Retraité": "LMNP, Assurance Vie, Succession.",
    "🏢 Investisseur Immo": "SCI, Déficit Foncier.",
    "🌍 Non-Résident": "Convention fiscale, IFI."
}

# --- 6. DOSSIERS ---
if "dossiers" not in st.session_state:
    st.session_state.dossiers = {"Dossier 1": []}
if "active_dossier" not in st.session_state:
    st.session_state.active_dossier = "Dossier 1"

def get_dossier_names(): return list(st.session_state.dossiers.keys())

# --- 7. BARRE LATÉRALE ---
with st.sidebar:
    # A. LOGO (Méthode Locale avec le BON NOM)
    if os.path.exists(LOGO_FILENAME):
        st.image(LOGO_FILENAME, width=150)
    else:
        st.warning(f"Image '{LOGO_FILENAME}' introuvable.")
        st.title("🏛️ PATBOT")

    st.markdown("""
        <h3 style='color: #D4AF37; margin: 0; padding-top: 5px;'>CABINET DIGITAL</h3>
        <hr style='margin-top: 5px; margin-bottom: 20px;'>
    """, unsafe_allow_html=True)
    
    # B. NAVIGATION
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        count = len(st.session_state.dossiers) + 1
        new_name = f"Dossier {count}"
        st.session_state.dossiers[new_name] = []
        st.session_state.active_dossier = new_name
        st.rerun()

    dossiers = get_dossier_names()
    if st.session_state.active_dossier not in dossiers:
        st.session_state.active_dossier = dossiers[0]
        
    choix = st.radio("Dossiers", dossiers, index=dossiers.index(st.session_state.active_dossier), label_visibility="collapsed")
    if choix != st.session_state.active_dossier:
        st.session_state.active_dossier = choix
        st.rerun()

    # C. OPTIONS & PDF
    with st.expander("⚙️ Options & PDF"):
        new_name = st.text_input("Renommer :", value=st.session_state.active_dossier)
        if st.button("Valider"):
            if new_name and new_name != st.session_state.active_dossier:
                st.session_state.dossiers[new_name] = st.session_state.dossiers.pop(st.session_state.active_dossier)
                st.session_state.active_dossier = new_name
                st.rerun()
        
        if st.button("🗑️ Supprimer", type="primary"):
            if len(dossiers) > 1:
                del st.session_state.dossiers[st.session_state.active_dossier]
                st.session_state.active_dossier = list(st.session_state.dossiers.keys())[0]
                st.rerun()
        
        st.markdown("---")
        if st.button("📄 Télécharger PDF"):
            if st.session_state.dossiers[st.session_state.active_dossier]:
                pdf_data = create_pdf(
                    st.session_state.active_dossier,
                    st.session_state.dossiers[st.session_state.active_dossier],
                    st.session_state.get("last_profil", "Général"),
                    st.session_state.get("last_annee", "2026")
                )
                st.download_button("⬇️ Sauvegarder", data=pdf_data, file_name=f"Rapport_{st.session_state.active_dossier}.pdf", mime="application/pdf")
            else:
                st.warning("Dossier vide.")

    st.markdown("---")
    profil = st.selectbox("Profil", list(PROFILS_DETAILS.keys()))
    annee = st.selectbox("Année", ["2026", "2025", "2024"])
    st.session_state.last_profil = profil
    st.session_state.last_annee = annee

# --- 8. CHAT ---
st.title(f"📂 {st.session_state.active_dossier}")

# Avatar (si image dispo)
user_avatar = None
bot_avatar = LOGO_FILENAME if os.path.exists(LOGO_FILENAME) else "🏛️"

for msg in st.session_state.dossiers[st.session_state.active_dossier]:
    avatar = bot_avatar if msg["role"] == "assistant" else user_avatar
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

system_instruction = f"RÔLE: Expert Patrimoine PATBOT. CONTEXTE: {annee}. PROFIL: {profil} ({PROFILS_DETAILS[profil]}). RÈGLES: CGI/BOFiP, Markdown, Structuré."

if prompt := st.chat_input("Question..."):
    st.session_state.dossiers[st.session_state.active_dossier].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("Analyse PATBOT..."):
            try:
                full_history = system_instruction + "\n"
                for m in st.session_state.dossiers[st.session_state.active_dossier]:
                    full_history += f"{m['role']}: {m['content']}\n"
                full_history += f"user: {prompt}\nassistant:"
                
                response = model.generate_content(full_history)
                st.markdown(response.text)
                st.session_state.dossiers[st.session_state.active_dossier].append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur : {e}")
