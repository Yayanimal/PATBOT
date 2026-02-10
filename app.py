import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PATBOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Noms des fichiers images (Doivent être sur GitHub)
FILE_NOIR = "LOGONOIR.png"
FILE_BLANC = "LOGOBLANC.png"

# --- CSS MODERNE (STYLE CHATGPT) ---
st.markdown("""
<style>
    /* Masquer menu et footer Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Style Titre Sidebar */
    .sidebar-title {
        font-size: 20px;
        font-weight: 600;
        text-align: center;
        margin-top: 10px;
        color: #D4AF37; /* Or */
    }
    
    /* Style de l'écran d'accueil (Welcome Screen) */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 50px;
        text-align: center;
    }
    .welcome-logo {
        width: 80px;
        margin-bottom: 20px;
        opacity: 0.8;
    }
    .welcome-text {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .suggestion-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        max-width: 600px;
        margin: 0 auto;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FONCTIONS UTILITAIRES ---
def render_dynamic_logo():
    """Affiche le logo adapté au thème dans la sidebar"""
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
# Variable pour gérer les clics sur les suggestions
if "prompt_trigger" not in st.session_state: st.session_state.prompt_trigger = None

# --- 4. SIDEBAR ---
with st.sidebar:
    render_dynamic_logo()
    st.markdown('<div class="sidebar-title">PATBOT</div>', unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle discussion", type="primary", use_container_width=True):
        idx = len(st.session_state.dossiers) + 1
        name = f"Discussion {idx}"
        st.session_state.dossiers[name] = []
        st.session_state.active = name
        st.session_state.prompt_trigger = None
        st.rerun()

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

# A. ÉCRAN D'ACCUEIL (Si chat vide)
if not chat_history:
    # Affiche le logo au milieu
    if os.path.exists(FILE_BLANC):
        st.image(FILE_BLANC, width=100, output_format="PNG") # On peut centrer avec des colonnes si besoin
    
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 30px;'>Comment puis-je vous aider ?</h1>
    """, unsafe_allow_html=True)

    # Cartes de suggestion
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 Stratégie Holding & Dividendes", use_container_width=True):
            st.session_state.prompt_trigger = "Quelle est la meilleure stratégie entre Salaire et Dividendes avec une Holding en 2026 ?"
            st.rerun()
        if st.button("🏠 Investissement LMNP vs Nu", use_container_width=True):
            st.session_state.prompt_trigger = "Quels sont les avantages du LMNP par rapport au foncier classique pour un TMI à 30% ?"
            st.rerun()
    with col2:
        if st.button("👨‍👩‍👧‍👦 Préparer sa Succession", use_container_width=True):
            st.session_state.prompt_trigger = "Comment fonctionne le démembrement de propriété pour réduire les droits de succession ?"
            st.rerun()
        if st.button("📈 Optimisation Fiscale 2026", use_container_width=True):
            st.session_state.prompt_trigger = "Quelles sont les nouveautés fiscales importantes de la Loi de Finances 2026 ?"
            st.rerun()

# B. AFFICHAGE DES MESSAGES
bot_avatar = FILE_BLANC if os.path.exists(FILE_BLANC) else "🤖"

for msg in chat_history:
    av = bot_avatar if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])
        
        # AJOUT DU BOUTON COPIER (Uniquement pour le bot)
        if msg["role"] == "assistant":
            # On utilise un expander discret pour ne pas polluer l'interface
            with st.expander("📄 Copier la réponse"):
                st.code(msg["content"], language=None) 
                # st.code ajoute nativement un bouton "Copier" en haut à droite du bloc

# C. GESTION DE L'ENTRÉE (Input ou Suggestion)
user_input = st.chat_input("Posez votre question à PATBOT...")

# Si on a cliqué sur un bouton de suggestion, on l'utilise comme input
if st.session_state.prompt_trigger:
    user_input = st.session_state.prompt_trigger
    st.session_state.prompt_trigger = None # Reset

if user_input:
    # 1. User
    st.session_state.dossiers[st.session_state.active].append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)
    
    # 2. IA
    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("PATBOT réfléchit..."):
            try:
                ctx = f"ROLE: PATBOT, Expert Patrimoine. ANNEE: {st.session_state.last_a}. CIBLE: {st.session_state.last_p}. STYLE: Professionnel, Markdown.\n"
                for m in st.session_state.dossiers[st.session_state.active]: ctx += f"{m['role']}: {m['content']}\n"
                ctx += f"user: {user_input}\nassistant:"
                
                resp = model.generate_content(ctx).text
                st.markdown(resp)
                
                # Bouton copier pour la nouvelle réponse
                with st.expander("📄 Copier la réponse"):
                    st.code(resp, language=None)
                
                st.session_state.dossiers[st.session_state.active].append({"role": "assistant", "content": resp})
            except Exception as e: st.error(f"Erreur: {e}")
