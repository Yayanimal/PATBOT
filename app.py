import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import PyPDF2
import os
import base64
import random

# Gestion des erreurs d'import pour éviter le crash total
try:
    from duckduckgo_search import DDGS
except ImportError:
    st.error("⚠️ Module 'duckduckgo-search' manquant. Ajoutez-le dans requirements.txt")
    DDGS = None

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PATBOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

FILE_NOIR = "LOGONOIR.png"
FILE_BLANC = "LOGOBLANC.png"

SUGGESTIONS_DB = [
    {"icon": "📈", "label": "Taux & Marchés", "prompt": "Quels sont les taux d'emprunt actuels (OAT, Euribor) et la tendance immobilière ?"},
    {"icon": "🏢", "label": "Holding", "prompt": "Quelle stratégie Rémunération vs Dividendes privilégier en 2026 ?"},
    {"icon": "🏠", "label": "Immo : LMNP vs SCI", "prompt": "Comparatif chiffré LMNP réel vs SCI à l'IS pour un bien à 200k€."},
    {"icon": "👨‍👩‍👧‍👦", "label": "Protection Conjoint", "prompt": "Comment optimiser la donation au dernier vivant ?"},
    {"icon": "📉", "label": "Déficit Foncier", "prompt": "Explique le mécanisme du déficit foncier et son report."},
    {"icon": "👵", "label": "PER & Retraite", "prompt": "Le PER est-il intéressant pour une TMI à 41% ?"},
    {"icon": "🌍", "label": "Expatriation", "prompt": "Conséquences fiscales d'un départ au Portugal pour un retraité ?"},
    {"icon": "💰", "label": "Assurance Vie", "prompt": "Avantages du contrat luxembourgeois (FID) ?"}
]

# --- CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .sidebar-title {
        font-size: 20px; font-weight: 600; text-align: center; margin-top: 10px; color: #D4AF37;
    }
    div[data-testid="stFileUploader"] { padding-top: 0px; }
    section[data-testid="stFileUploaderDropzone"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px dashed #D4AF37;
        border-radius: 8px;
        padding: 10px;
    }
    div[data-testid="stToggle"] label { color: #D4AF37 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. FONCTIONS ---
def render_dynamic_logo():
    if not os.path.exists(FILE_NOIR) or not os.path.exists(FILE_BLANC): return
    with open(FILE_NOIR, "rb") as f: b64_n = base64.b64encode(f.read()).decode()
    with open(FILE_BLANC, "rb") as f: b64_b = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <style>
    .ln {{display:block; margin: 0 auto;}} .lb {{display:none; margin: 0 auto;}}
    @media (prefers-color-scheme: dark) {{ .ln {{display:none;}} .lb {{display:block;}} }}
    </style>
    <div style="text-align:center; margin-bottom:10px;">
        <img src="data:image/png;base64,{b64_n}" class="ln" width="130">
        <img src="data:image/png;base64,{b64_b}" class="lb" width="130">
    </div>
    """, unsafe_allow_html=True)

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Erreur lecture PDF: {e}"

def search_web_duckduckgo(query):
    if DDGS is None: return "Module de recherche non installé."
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='fr-fr', safesearch='off', max_results=3))
            if not results: return "Aucun résultat web."
            web_context = "--- INFO WEB LIVE ---\n"
            for res in results:
                web_context += f"• {res['title']} ({res['href']}): {res['body']}\n"
            return web_context
    except Exception as e:
        return f"Erreur Web: {e}"

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
        try: txt = msg["content"].encode('latin-1', 'replace').decode('latin-1')
        except: txt = msg["content"]
        pdf.multi_cell(0, 5, txt); pdf.ln(5)
    return bytes(pdf.output())

# --- 3. INIT SESSIONS ---
if "GOOGLE_API_KEY" not in st.secrets: st.error("Clé API manquante"); st.stop()
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-flash-latest")
except: st.error("Erreur connexion IA"); st.stop()

if "dossiers" not in st.session_state: st.session_state.dossiers = {"Nouvelle Discussion": []}
if "active" not in st.session_state: st.session_state.active = "Nouvelle Discussion"
if "prompt_trigger" not in st.session_state: st.session_state.prompt_trigger = None
if "doc_context" not in st.session_state: st.session_state.doc_context = ""
if "editing_title" not in st.session_state: st.session_state.editing_title = False
if "web_mode" not in st.session_state: st.session_state.web_mode = False
if "random_suggestions" not in st.session_state: st.session_state.random_suggestions = random.sample(SUGGESTIONS_DB, 4)

# --- 4. SIDEBAR ---
with st.sidebar:
    render_dynamic_logo()
    
    if st.button("＋ Nouvelle discussion", type="primary", use_container_width=True):
        idx = len(st.session_state.dossiers) + 1
        name = f"Discussion {idx}"
        st.session_state.dossiers[name] = []
        st.session_state.active = name
        st.session_state.doc_context = ""
        st.session_state.prompt_trigger = None
        st.session_state.web_mode = False
        st.session_state.random_suggestions = random.sample(SUGGESTIONS_DB, 4)
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛠️ Centre de Contrôle")
    
    web_on = st.toggle("🌐 Recherche Web Live", value=st.session_state.web_mode)
    if web_on != st.session_state.web_mode: st.session_state.web_mode = web_on; st.rerun()

    st.markdown("**📎 Analyser un PDF**")
    uploaded_file = st.file_uploader("Contrat, Bilan, Avis...", type="pdf", label_visibility="collapsed")
    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
        if text != st.session_state.doc_context:
            st.session_state.doc_context = text
            st.toast(f"✅ Analyse terminée : {uploaded_file.name}")
    else: st.session_state.doc_context = ""

    st.markdown("---")
    st.caption("HISTORIQUE")
    chats = list(st.session_state.dossiers.keys())[::-1]
    if st.session_state.active not in st.session_state.dossiers: st.session_state.active = chats[0]
    sel = st.radio("List", chats, index=chats.index(st.session_state.active), label_visibility="collapsed")
    if sel != st.session_state.active: st.session_state.active = sel; st.rerun()

    st.markdown("---")
    with st.expander("⚙️ Options"):
        p = st.selectbox("Profil", ["Général", "Chef d'Entreprise", "Retraité", "Investisseur", "Non-Résident"])
        a = st.selectbox("Année", ["2026", "2025"])
        st.session_state.last_p = p; st.session_state.last_a = a
        if st.button("🗑️ Supprimer"): 
            if len(chats) > 1: del st.session_state.dossiers[st.session_state.active]; st.session_state.active = list(st.session_state.dossiers.keys())[0]; st.rerun()
        if st.session_state.dossiers[st.session_state.active]:
            try:
                pdf_data = create_pdf(st.session_state.active, st.session_state.dossiers[st.session_state.active], p, a)
                st.download_button("📥 PDF", pdf_data, "Export.pdf", "application/pdf")
            except: pass

# --- 5. ZONE PRINCIPALE ---
chat_history = st.session_state.dossiers[st.session_state.active]
bot_avatar = FILE_BLANC if os.path.exists(FILE_BLANC) else "🤖"

# Titre
col_title, col_edit = st.columns([8, 1])
with col_title:
    if st.session_state.editing_title:
        new_name = st.text_input("Titre", value=st.session_state.active, label_visibility="collapsed")
        if new_name != st.session_state.active:
            st.session_state.dossiers[new_name] = st.session_state.dossiers.pop(st.session_state.active)
            st.session_state.active = new_name
            st.session_state.editing_title = False
            st.rerun()
    else:
        st.markdown(f"<h1 style='margin-top: -20px;'>{st.session_state.active}</h1>", unsafe_allow_html=True)
with col_edit:
    if st.button("✏️"): st.session_state.editing_title = not st.session_state.editing_title; st.rerun()

# Accueil (Suggestions)
if not chat_history:
    if os.path.exists(FILE_BLANC): st.image(FILE_BLANC, width=100)
    if st.session_state.doc_context: st.success("📂 Document chargé.")
    sug = st.session_state.random_suggestions
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"{sug[0]['icon']} {sug[0]['label']}", use_container_width=True): st.session_state.prompt_trigger = sug[0]['prompt']; st.rerun()
        if st.button(f"{sug[1]['icon']} {sug[1]['label']}", use_container_width=True): st.session_state.prompt_trigger = sug[1]['prompt']; st.rerun()
    with col2:
        if st.button(f"{sug[2]['icon']} {sug[2]['label']}", use_container_width=True): st.session_state.prompt_trigger = sug[2]['prompt']; st.rerun()
        if st.button(f"{sug[3]['icon']} {sug[3]['label']}", use_container_width=True): st.session_state.prompt_trigger = sug[3]['prompt']; st.rerun()

# Affichage des messages (Important: avant l'input)
for msg in chat_history:
    av = bot_avatar if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            with st.expander("📄 Copier"): st.code(msg["content"], language=None)

# --- 6. GESTION DES ENTRÉES (SYSTEME ROBUSTE) ---

# Cas 1 : Clic sur bouton suggestion (prioritaire)
if st.session_state.prompt_trigger:
    # On ajoute directement
    st.session_state.dossiers[st.session_state.active].append({"role": "user", "content": st.session_state.prompt_trigger})
    st.session_state.prompt_trigger = None # Reset
    st.rerun() # On recharge pour que l'IA réponde

# Cas 2 : Barre de chat (Toujours affichée en bas)
ph_text = "Recherche Web Active 🌐..." if st.session_state.web_mode else "Posez votre question à PATBOT..."
user_input = st.chat_input(ph_text)

if user_input:
    st.session_state.dossiers[st.session_state.active].append({"role": "user", "content": user_input})
    st.rerun()

# --- 7. REPONSE IA (S'exécute au rechargement) ---
# On vérifie si le dernier message est de l'utilisateur pour déclencher l'IA
if chat_history and chat_history[-1]["role"] == "user":
    last_msg = chat_history[-1]["content"]
    
    with st.chat_message("assistant", avatar=bot_avatar):
        status = "Recherche Web... 🌍" if st.session_state.web_mode else "Analyse..."
        with st.spinner(status):
            try:
                # 1. Recherche Web
                web_ctx = ""
                if st.session_state.web_mode: web_ctx = search_web_duckduckgo(last_msg)
                
                # 2. Contexte Doc
                doc_ctx = ""
                if st.session_state.doc_context: doc_ctx = f"\nDOC:\n{st.session_state.doc_context}\n"
                
                # 3. Prompt
                ctx = f"ROLE: PATBOT. PROFIL: {st.session_state.last_p}. ANNEE: {st.session_state.last_a}. {web_ctx} {doc_ctx}\n"
                # On ajoute l'historique (sauf le dernier message user qu'on vient d'ajouter)
                for m in chat_history[:-1]: ctx += f"{m['role']}: {m['content']}\n"
                ctx += f"user: {last_msg}\nassistant:"
                
                # 4. Génération
                resp = model.generate_content(ctx).text
                st.markdown(resp)
                with st.expander("📄 Copier"): st.code(resp, language=None)
                
                # 5. Sauvegarde
                st.session_state.dossiers[st.session_state.active].append({"role": "assistant", "content": resp})
                
                # 6. Auto-Rename (Si c'est le tout début de la conv)
                if len(chat_history) == 2: # 1 user + 1 bot
                    try:
                        t = model.generate_content(f"Titre court (3-5 mots) pour: {last_msg}").text.strip().replace('"','')
                        if len(t) > 2 and len(t) < 50:
                            old = st.session_state.active
                            st.session_state.dossiers[t] = st.session_state.dossiers.pop(old)
                            st.session_state.active = t
                            st.rerun()
                    except: pass
                    
            except Exception as e:
                st.error(f"Erreur: {e}")
