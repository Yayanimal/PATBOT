import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import PyPDF2
import os
import base64
import io

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PATBOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

FILE_NOIR = "LOGONOIR.png"
FILE_BLANC = "LOGOBLANC.png"

# --- CSS MODERNE ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .sidebar-title {
        font-size: 20px; font-weight: 600; text-align: center; margin-top: 10px; color: #D4AF37;
    }
    /* Style pour la zone d'upload */
    .stFileUploader {
        padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FONCTIONS UTILITAIRES ---
def render_dynamic_logo():
    if not os.path.exists(FILE_NOIR) or not os.path.exists(FILE_BLANC): return
    with open(FILE_NOIR, "rb") as f: b64_n = base64.b64encode(f.read()).decode()
    with open(FILE_BLANC, "rb") as f: b64_b = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <style>
    .ln {{display:block; margin: 0 auto;}} .lb {{display:none; margin: 0 auto;}}
    @media (prefers-color-scheme: dark) {{ .ln {{display:none;}} .lb {{display:block;}} }}
    </style>
    <div style="text-align:center;">
        <img src="data:image/png;base64,{b64_n}" class="ln" width="130">
        <img src="data:image/png;base64,{b64_b}" class="lb" width="130">
    </div>
    """, unsafe_allow_html=True)

def extract_text_from_pdf(uploaded_file):
    """Extrait le texte brut d'un PDF"""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Erreur de lecture : {e}"

def create_pdf(name, history, profil, annee):
    class PDF(FPDF):
        def header(self):
            if os.path.exists(FILE_NOIR): self.image(FILE_NOIR, 10, 8, 25)
            self.set_font('Arial', 'B', 12)
            self.set_text_color(212, 175, 55)
            self.cell(0, 10, '   ' * 15 + 'PATBOT - EXPERT IA', 0, 1, 'L')
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
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"{name}", 0, 1)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100)
    pdf.cell(0, 10, f"Profil: {profil} | Année: {annee}", 0, 1); pdf.ln(10)

    for msg in history:
        role = "MOI" if msg["role"] == "user" else "PATBOT"
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(212, 175, 55) if role == "PATBOT" else pdf.set_text_color(50)
        pdf.cell(0, 8, role, 0, 1)
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0)
        txt = msg["content"].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, txt); pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INIT IA & SESSION ---
if "GOOGLE_API_KEY" not in st.secrets: st.error("Clé API manquante"); st.stop()
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-flash-latest")
except: st.error("Erreur connexion IA"); st.stop()

if "dossiers" not in st.session_state: st.session_state.dossiers = {"Nouveau Chat": []}
if "active" not in st.session_state: st.session_state.active = "Nouveau Chat"
if "prompt_trigger" not in st.session_state: st.session_state.prompt_trigger = None
# Variable pour stocker le contenu du document analysé
if "doc_context" not in st.session_state: st.session_state.doc_context = ""

# --- 4. SIDEBAR ---
with st.sidebar:
    render_dynamic_logo()
    st.markdown('<div class="sidebar-title">PATBOT</div>', unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle discussion", type="primary", use_container_width=True):
        idx = len(st.session_state.dossiers) + 1
        name = f"Discussion {idx}"
        st.session_state.dossiers[name] = []
        st.session_state.active = name
        st.session_state.doc_context = "" # Reset du document
        st.session_state.prompt_trigger = None
        st.rerun()

    st.markdown("---")
    
    # ZONE D'UPLOAD FICHIER (NOUVEAU)
    with st.expander("📂 Analyser un document", expanded=True):
        uploaded_file = st.file_uploader("Glissez un PDF (Bilan, Avis d'impôt...)", type="pdf")
        if uploaded_file is not None:
            # On extrait le texte
            text = extract_text_from_pdf(uploaded_file)
            st.session_state.doc_context = text
            st.success("✅ Document lu ! PATBOT peut maintenant l'analyser.")
        else:
            st.session_state.doc_context = ""

    st.markdown("---")
    st.caption("HISTORIQUE")
    chats = list(st.session_state.dossiers.keys())[::-1]
    if st.session_state.active not in st.session_state.dossiers: st.session_state.active = chats[0]
    
    sel = st.radio("List", chats, index=chats.index(st.session_state.active), label_visibility="collapsed")
    if sel != st.session_state.active:
        st.session_state.active = sel
        st.rerun()

    st.markdown("---")
    with st.expander("⚙️ Options"):
        p = st.selectbox("Profil", ["Général", "Chef d'Entreprise", "Retraité", "Investisseur Immo", "Famille", "Non-Résident"])
        a = st.selectbox("Année", ["2026", "2025"])
        st.session_state.last_p = p; st.session_state.last_a = a
        if st.button("🗑️ Effacer"): 
            if len(chats) > 1: del st.session_state.dossiers[st.session_state.active]; st.session_state.active = list(st.session_state.dossiers.keys())[0]; st.rerun()
        if st.session_state.dossiers[st.session_state.active]:
            pdf = create_pdf(st.session_state.active, st.session_state.dossiers[st.session_state.active], p, a)
            st.download_button("📥 PDF", pdf, "Export.pdf", "application/pdf")

# --- 5. ZONE PRINCIPALE ---
chat_history = st.session_state.dossiers[st.session_state.active]

# ECRAN ACCUEIL
if not chat_history:
    if os.path.exists(FILE_BLANC): st.image(FILE_BLANC, width=100)
    st.markdown("<h1 style='text-align: center;'>Expertise Patrimoniale IA</h1>", unsafe_allow_html=True)
    
    if st.session_state.doc_context:
        st.info("💡 Un document est chargé. Vous pouvez demander : 'Analyse ce document' ou 'Fais-moi une synthèse'.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 Stratégie Holding", use_container_width=True):
            st.session_state.prompt_trigger = "Quelle est la meilleure stratégie Holding en 2026 ?"
            st.rerun()
        if st.button("📄 Synthèse du Document", use_container_width=True, disabled=(not st.session_state.doc_context)):
            st.session_state.prompt_trigger = "Fais-moi une synthèse structurée du document téléchargé (Chiffres clés, points d'attention)."
            st.rerun()
    with col2:
        if st.button("👨‍👩‍👧‍👦 Succession", use_container_width=True):
            st.session_state.prompt_trigger = "Explique le démembrement de propriété."
            st.rerun()
        if st.button("💰 Analyse Financière", use_container_width=True, disabled=(not st.session_state.doc_context)):
            st.session_state.prompt_trigger = "Analyse la santé financière à partir de ce document et propose des optimisations."
            st.rerun()

# AFFICHAGE CHAT
bot_avatar = FILE_BLANC if os.path.exists(FILE_BLANC) else "🤖"
for msg in chat_history:
    av = bot_avatar if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            with st.expander("📄 Copier"): st.code(msg["content"], language=None)

# INPUT USER
user_input = st.chat_input("Votre question...")
if st.session_state.prompt_trigger:
    user_input = st.session_state.prompt_trigger
    st.session_state.prompt_trigger = None

if user_input:
    st.session_state.dossiers[st.session_state.active].append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)
    
    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("Analyse..."):
            try:
                # ON INJECTE LE DOCUMENT DANS LE CERVEAU DE L'IA
                doc_prompt = ""
                if st.session_state.doc_context:
                    doc_prompt = f"\n\n--- DOCUMENT TÉLÉCHARGÉ PAR LE CLIENT ---\n{st.session_state.doc_context}\n--- FIN DU DOCUMENT ---\nInstruction : Utilise ce document pour répondre si la question s'y rapporte.\n"

                ctx = f"ROLE: PATBOT, Expert Patrimoine. ANNEE: {st.session_state.last_a}. PROFIL: {st.session_state.last_p}. STYLE: Pro & Structuré.{doc_prompt}\n"
                for m in st.session_state.dossiers[st.session_state.active]: ctx += f"{m['role']}: {m['content']}\n"
                ctx += f"user: {user_input}\nassistant:"
                
                resp = model.generate_content(ctx).text
                st.markdown(resp)
                with st.expander("📄 Copier"): st.code(resp, language=None)
                st.session_state.dossiers[st.session_state.active].append({"role": "assistant", "content": resp})
            except Exception as e: st.error(f"Erreur: {e}")
