import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import base64

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="PATBOT | Gestion Privée",
    page_icon="🏛️",
    layout="wide"
)

# NOMS DES FICHIERS (Doivent correspondre exactement à ton GitHub)
FILE_NOIR = "logo_noir.png"  # Utilisé pour le Mode Clair & le PDF
FILE_BLANC = "logo_blanc.png" # Utilisé pour le Mode Sombre & l'Avatar

# --- 2. FONCTION : LOGO DYNAMIQUE (CSS) ---
def render_dynamic_logo():
    """
    Affiche le logo Blanc si le site est en Mode Sombre.
    Affiche le logo Noir si le site est en Mode Clair.
    """
    if not os.path.exists(FILE_NOIR) or not os.path.exists(FILE_BLANC):
        st.warning(f"⚠️ Images introuvables. Assurez-vous d'avoir '{FILE_NOIR}' et '{FILE_BLANC}' à la racine.")
        return

    # Conversion en Base64 pour injection HTML
    with open(FILE_NOIR, "rb") as f:
        b64_noir = base64.b64encode(f.read()).decode()
    with open(FILE_BLANC, "rb") as f:
        b64_blanc = base64.b64encode(f.read()).decode()

    # CSS Intelligent
    css = f"""
    <style>
    .logo-container {{
        text-align: left;
        margin-bottom: 20px;
    }}
    .logo-container img {{
        max-width: 150px;
    }}
    /* PAR DÉFAUT (Mode Clair) -> On affiche le NOIR */
    .logo-noir {{ display: block; }}
    .logo-blanc {{ display: none; }}

    /* SI MODE SOMBRE DÉTECTÉ -> On affiche le BLANC */
    @media (prefers-color-scheme: dark) {{
        .logo-noir {{ display: none; }}
        .logo-blanc {{ display: block; }}
    }}
    </style>
    <div class="logo-container">
        <img src="data:image/png;base64,{b64_noir}" class="logo-noir">
        <img src="data:image/png;base64,{b64_blanc}" class="logo-blanc">
    </div>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- 3. FONCTION : GÉNÉRATION PDF (Logo Noir forcé) ---
def create_pdf(dossier_name, chat_history, profil, annee):
    class PDF(FPDF):
        def header(self):
            # Logo Noir (Papier blanc)
            if os.path.exists(FILE_NOIR):
                self.image(FILE_NOIR, 10, 8, 30)
                self.set_xy(45, 10) # Décalage du titre
            
            self.set_font('Arial', 'B', 12)
            self.set_text_color(212, 175, 55) # Or
            self.cell(0, 10, 'CABINET PATBOT - GESTION PRIVÉE', 0, 1, 'L')
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
    
    # En-tête Dossier
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Dossier : {dossier_name}", 0, 1, 'L')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Profil : {profil} | Loi de Finances {annee}", 0, 1, 'L')
    pdf.ln(10)
    
    # Conversation
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
        
        # Gestion encodage texte
        try:
            text = message["content"].encode('latin-1', 'replace').decode('latin-1')
        except:
            text = message["content"]
        pdf.multi_cell(0, 6, text)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. CONNEXION IA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Clé API manquante dans les secrets.")
    st.stop()
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-flash-latest")
except Exception as e:
    st.error(f"Erreur technique : {e}")
    st.stop()

# --- 5. DONNÉES & PROFILS ---
PROFILS = {
    "🔍 Mode Général": "Encyclopédie fiscale et patrimoniale.",
    "👤 Jeune Actif": "Stratégie : PEA, Résidence Principale, PER.",
    "👨‍👩‍👧‍👦 Famille": "Stratégie : Transmission, Protection conjoint, Succession.",
    "👔 Chef d'Entreprise": "Stratégie : Holding, Dutreil, Dividendes vs Salaire.",
    "🏖️ Retraité": "Stratégie : Revenus complémentaires (LMNP, SCPI), Assurance Vie.",
    "🏢 Investisseur Immo": "Stratégie : SCI (IS/IR), Déficit Foncier, Cash-flow.",
    "🌍 Non-Résident": "Stratégie : Convention fiscale, IFI, Retenue à la source."
}

# Gestion Session
if "dossiers" not in st.session_state: st.session_state.dossiers = {"Dossier 1": []}
if "active" not in st.session_state: st.session_state.active = "Dossier 1"

# --- 6. BARRE LATÉRALE (INTERFACE PRO) ---
with st.sidebar:
    # A. LOGO ADAPTATIF (Noir ou Blanc selon le thème)
    render_dynamic_logo()

    st.markdown("<h3 style='color:#D4AF37; margin:0;'>CABINET DIGITAL</h3><hr>", unsafe_allow_html=True)
    
    # B. NAVIGATION
    if st.button("➕ Nouveau Dossier", use_container_width=True):
        idx = len(st.session_state.dossiers) + 1
        name = f"Dossier {idx}"
        st.session_state.dossiers[name] = []
        st.session_state.active = name
        st.rerun()
        
    dossiers = list(st.session_state.dossiers.keys())
    # Sécurité suppression
    if st.session_state.active not in dossiers:
         st.session_state.active = dossiers[0] if dossiers else "Dossier 1"
         if not dossiers: st.session_state.dossiers = {"Dossier 1": []}

    choix = st.radio("Dossiers", dossiers, index=dossiers.index(st.session_state.active), label_visibility="collapsed")
    if choix != st.session_state.active:
        st.session_state.active = choix
        st.rerun()
        
    # C. OPTIONS & PDF
    with st.expander("⚙️ Options & PDF"):
        # Renommer
        new_name = st.text_input("Renommer :", value=st.session_state.active)
        if st.button("Valider"):
            if new_name and new_name != st.session_state.active:
                st.session_state.dossiers[new_name] = st.session_state.dossiers.pop(st.session_state.active)
                st.session_state.active = new_name
                st.rerun()

        # Supprimer
        if st.button("🗑️ Supprimer"):
            if len(dossiers) > 1:
                del st.session_state.dossiers[st.session_state.active]
                st.session_state.active = list(st.session_state.dossiers.keys())[0]
                st.rerun()
        
        st.markdown("---")
        
        # BOUTON PDF (Génère avec Logo Noir)
        if st.button("📄 Télécharger PDF"):
            if st.session_state.dossiers[st.session_state.active]:
                pdf_data = create_pdf(
                    st.session_state.active,
                    st.session_state.dossiers[st.session_state.active],
                    st.session_state.get("last_p", "Général"),
                    st.session_state.get("last_a", "2026")
                )
                st.download_button("⬇️ Sauvegarder", data=pdf_data, file_name=f"Rapport_{st.session_state.active}.pdf", mime="application/pdf")
            else:
                st.warning("Dossier vide.")

    st.markdown("---")
    p = st.selectbox("Profil", list(PROFILS.keys()))
    a = st.selectbox("Année Fiscale", ["2026", "2025", "2024"])
    st.session_state.last_p = p
    st.session_state.last_a = a

# --- 7. CHAT ---
st.title(f"📂 {st.session_state.active}")

# Avatar pour le chat (On utilise le blanc car l'interface chat est souvent sombre/neutre)
# Si tu veux que l'avatar change aussi, c'est plus complexe, donc on garde le blanc par défaut ici.
bot_avatar = FILE_BLANC if os.path.exists(FILE_BLANC) else "🏛️"

for msg in st.session_state.dossiers[st.session_state.active]:
    av = bot_avatar if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])

if prompt := st.chat_input("Votre question..."):
    st.session_state.dossiers[st.session_state.active].append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant", avatar=bot_avatar):
        with st.spinner("Analyse PATBOT..."):
            try:
                hist = f"ROLE: Expert PATBOT. CONTEXTE: {a}. PROFIL: {p} ({PROFILS[p]}). RÈGLES: CGI/BOFiP, Markdown, Structuré.\n"
                for m in st.session_state.dossiers[st.session_state.active]:
                    hist += f"{m['role']}: {m['content']}\n"
                hist += f"user: {prompt}\nassistant:"
                
                resp = model.generate_content(hist)
                st.markdown(resp.text)
                st.session_state.dossiers[st.session_state.active].append({"role": "assistant", "content": resp.text})
            except Exception as e: st.error(e)
