import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import base64

# --- 1. CONFIGURATION DE LA PAGE (STYLE ÉPURÉ) ---
st.set_page_config(
    page_title="PATBOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONNALISÉ POUR LE LOOK "CHATGPT" ---
st.markdown("""
<style>
    /* Masquer le menu hamburger standard et le footer pour faire plus "App" */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Style du titre de la sidebar */
    .sidebar-title {
        font-size: 24px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
        background: -webkit-linear-gradient(45deg, #D4AF37, #F0E68C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-subtitle {
        font-size: 12px;
        text-align: center;
        color: grey;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# NOMS DES FICHIERS (MAJUSCULES)
FILE_NOIR = "LOGONOIR.png"
FILE_BLANC = "LOGOBLANC.png"

# --- 2. LOGO DYNAMIQUE ---
def render_dynamic_logo():
    if not os.path.exists(FILE_NOIR) or not os.path.exists(FILE_BLANC):
        st.warning("⚠️ Images manquantes.")
        return

    with open(FILE_NOIR, "rb") as f: b64_noir = base64.b64encode(f.read()).decode()
    with open(FILE_BLANC, "rb") as f: b64_blanc = base64.b64encode(f.read()).decode()

    css = f"""
    <style>
    .logo-container {{ text-align: center; margin-bottom: 10px; }}
    .logo-container img {{ max-width: 120px; }}
    .logo-noir {{ display: block; }} .logo-blanc {{ display: none; }}
    @media (prefers-color-scheme: dark) {{
        .logo-noir {{ display: none; }} .logo-blanc {{ display: block; }}
    }}
    </style>
    <div class="logo-container">
        <img src="data:image/png;base64,{b64_noir}" class="logo-noir">
        <img src="data:image/png;base64,{b64_blanc}" class="logo-blanc">
    </div>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- 3. GÉNÉRATION PDF ---
def create_pdf(dossier_name, chat_history, profil, annee):
    class PDF(FPDF):
        def header(self):
            if os.path.exists(FILE_NOIR):
                self.image(FILE_NOIR, 10, 8, 25)
                self.set_xy(40, 10)
            
            self.set_font('Arial', 'B', 12)
            self.set_text_color(212, 175, 55)
            self.cell(0, 10, 'PATBOT - INTELLIGENCE PATRIMONIALE', 0, 1, 'L')
            self.line(10, 25, 200, 25)
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Titres
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"{dossier_name}", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Profil : {profil} | Réf : {annee}", 0, 1, 'L')
    pdf.ln(10)
    
    # Chat
    for message in chat_history:
        role = "UTILISATEUR" if message["role"] == "user" else "PATBOT"
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(212, 175, 55) if role == "PATBOT" else pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, role, 0, 1)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        try:
            text = message["content"].encode('latin-1', 'replace').decode('latin-1')
        except:
            text = message["content"]
        pdf.multi_cell(0, 5, text)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. IA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Clé API manquante.")
    st.stop()
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-flash-latest")
except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# --- 5. DONNÉES ---
PROFILS = {
    "🔍 Général": "Encyclopédie fiscale.",
    "👤 Jeune Actif": "PEA, RP, PER.",
    "👨‍👩‍👧‍👦 Famille": "Transmission, Protection.",
    "👔 Chef d'Entreprise": "Holding, Dutreil.",
    "🏖️ Retraité": "LMNP, Assurance Vie.",
    "🏢 Investisseur": "SCI, Déficit Foncier.",
    "🌍 Non-Résident": "International."
}
if "dossiers" not in st.session_state: st.session_state.dossiers = {"Conversation 1": []}
if "active" not in st.session_state: st.session_state.active = "Conversation 1"

# --- 6. SIDEBAR STYLE CHATGPT ---
with st.sidebar:
    # A. En-tête Centré
    render_dynamic_logo()
    st.markdown('<div class="sidebar-title">PATBOT</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Assistant Patrimonial IA</div>', unsafe_allow_html=True)
    
    # B. Bouton Nouveau Chat (Gros bouton primaire)
    if st.button("＋ Nouvelle conversation", type="primary", use_container_width=True):
        idx = len(st.session_state.dossiers) + 1
        name = f"Conversation {idx}"
        st.session_state.dossiers[name] = []
        st.session_state.active = name
        st.rerun()
    
    st.markdown("---")
    
    # C. Historique (Liste simple)
    st.caption("HISTORIQUE")
    dossiers = list(st.session_state.dossiers.keys())
    # Inversion pour avoir le plus récent en haut
    dossiers_reversed = list(reversed(dossiers))
    
    # Sécurité
    if st.session_state.active not in dossiers:
        st.session_state.active = dossiers[0] if dossiers else "Conversation 1"
        if not dossiers: st.session_state.dossiers = {"Conversation 1": []}

    choix = st.radio("Historique", dossiers_reversed, index=dossiers_reversed.index(st.session_state.active), label_visibility="collapsed")
    if choix != st.session_state.active:
        st.session_state.active = choix
        st.rerun()

    st.markdown("---")
    
    # D. Paramètres (Discrets en bas)
    with st.expander("⚙️ Réglages & Export"):
        p = st.selectbox("Profil", list(PROFILS.keys()))
        a = st.selectbox("Année", ["2026", "2025"])
        st.session_state.last_p = p
        st.session_state.last_a = a
        
        st.divider()
        new_name = st.text_input("Renommer le chat :", value=st.session_state.active)
        if st.button("Renommer"):
            if new_name and new_name != st.session_state.active:
                st.session_state.dossiers[new_name] = st.session_state.dossiers.pop(st.session_state.active)
                st.session_state.active = new_name
                st.rerun()
        
        if st.button("🗑️ Supprimer ce chat"):
            if len(dossiers) > 1:
                del st.session_state.dossiers[st.session_state.active]
                st.session_state.active = list(st.session_state.dossiers.keys())[0]
                st.rerun()

        if st.button("📥 Télécharger PDF"):
            if st.session_state.dossiers[st.session_state.active]:
                pdf_data = create_pdf(
                    st.session_state.active,
                    st.session_state.dossiers[st.session_state.active],
                    st.session_state.get("last_p", "Général"),
                    st.session_state.get("last_a", "2026")
                )
                st.download_button("Cliquez pour sauver", data=pdf_data, file_name="Patbot_Export.pdf", mime="application/pdf")

# --- 7. ZONE DE CHAT ---
# Titre discret (ou pas de titre pour faire comme ChatGPT)
# st.subheader(st.session_state.active) 

# Avatar Chat
bot_avatar = FILE_BLANC if os.path.exists(FILE_BLANC) else "🤖"

# Affichage Historique
for msg in st.session_state.dossiers[st.session_state.active]:
    av = bot_avatar if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])

# Input en bas
if prompt := st.chat_input("Posez votre question patrimoniale..."):
    st.session_state.dossiers[st.session_state.active].append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("Analyse en cours..."):
            try:
                ctx = f"ROLE: Assistant PATBOT. EXPERTISE: Gestion de Patrimoine. ANNEE: {st.session_state.last_a}. CIBLE: {st.session_state.last_p}. STYLE: Professionnel, clair, structuré.\n"
                for m in st.session_state.dossiers[st.session_state.active]:
                    ctx += f"{m['role']}: {m['content']}\n"
                ctx += f"user: {prompt}\nassistant:"
                
                resp = model.generate_content(ctx)
                st.markdown(resp.text)
                st.session_state.dossiers[st.session_state.active].append({"role": "assistant", "content": resp.text})
            except Exception as e: st.error(e)
