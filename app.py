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
