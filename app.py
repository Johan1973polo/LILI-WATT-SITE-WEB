mandats_temp = {}
factures_temp = {}  # Stockage temporaire factures  # Stockage temporaire des mandats
from flask import Flask, render_template, send_file, redirect, request, jsonify
from flask_caching import Cache
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests
import os
import re
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
import anthropic
from PIL import Image
import io
import base64
from pdf2image import convert_from_bytes
from werkzeug.utils import secure_filename
from utils.generate_mandat import generate_mandat_pdf, generate_mandat_data
from io import BytesIO

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__,
            static_folder='assets',
            static_url_path='/assets',
            template_folder='templates')

# Configuration du cache (1 heure)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Configuration upload (16MB max)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ─── CONFIG EXTRACTEUR ───────────────────────────────────────────
GOOGLE_SHEET_ID      = os.getenv("GOOGLE_SHEET_ID", "VOTRE_SHEET_ID_ICI")
GOOGLE_CREDS_FILE    = os.getenv("GOOGLE_CREDS_FILE", "credentials.json")
GMAIL_USER           = os.getenv("GMAIL_USER", "contact@liliwatt.fr")
GMAIL_PASSWORD       = os.getenv("GMAIL_PASSWORD", "VOTRE_APP_PASSWORD")
CONSEILLER_EMAIL     = os.getenv("CONSEILLER_EMAIL", "contact@liliwatt.fr")
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
PDFSHIFT_API_KEY     = os.getenv("PDFSHIFT_API_KEY", "")

# Client Anthropic
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'heic', 'heif', 'webp'}

# ──── FONCTION UTILITAIRE ────────────────────────────────────
def temps_relatif(date_str):
    """Convertit une date ISO en temps relatif (ex: il y a 2h)"""
    try:
        pub = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = now - pub

        if diff.days > 0:
            return f"il y a {diff.days}j"
        elif diff.seconds >= 3600:
            return f"il y a {diff.seconds // 3600}h"
        else:
            return f"il y a {diff.seconds // 60} min"
    except:
        return "récent"

# Rendre la fonction disponible dans les templates
app.jinja_env.globals.update(temps_relatif=temps_relatif)

# Chemin de base pour les fichiers statiques HTML
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def serve_html(filename):
    """Sert un fichier HTML depuis le répertoire racine"""
    filepath = os.path.join(BASE_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        from flask import Response
        return Response(content, mimetype='text/html')
    except FileNotFoundError:
        from flask import abort
        abort(404)

@app.route('/logo2.png')
def serve_logo():
    """Sert le logo depuis le répertoire parent"""
    from flask import send_from_directory
    parent_dir = os.path.dirname(BASE_DIR)
    return send_from_directory(parent_dir, 'logo2.png')

@app.route('/images/<path:filename>')
def serve_images(filename):
    """Sert les images depuis le dossier images"""
    from flask import send_from_directory
    return send_from_directory('images', filename)

# ─── GOOGLE SHEETS ─────────────────────────────────────────
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    return sheet

# ─── GOOGLE DRIVE ──────────────────────────────────────────
def get_drive_service():
    scopes = [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)
    service = build('drive', 'v3', credentials=creds)
    return service

def find_or_create_folder(service, folder_name, parent_id=None):
    """Trouve un dossier par nom ou le crée s'il n'existe pas"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])

    if items:
        return items[0]['id']
    else:
        # Créer le dossier
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]

        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

def upload_invoice_to_drive(file_bytes, filename, lead_data):
    """Upload une facture sur Google Drive dans le dossier approprié"""
    try:
        service = get_drive_service()

        # Structure: Leads LILIWATT / [DATE] - [NOM] - [MONTANT]€
        root_folder_id = find_or_create_folder(service, "Leads LILIWATT")

        # Nom du sous-dossier
        date_str = datetime.now().strftime("%Y%m%d")
        nom = lead_data.get('nom', 'Inconnu')
        montant = lead_data.get('montant', 0)
        subfolder_name = f"{date_str} - {nom} - {montant}€"

        subfolder_id = find_or_create_folder(service, subfolder_name, root_folder_id)

        # Upload le fichier
        file_metadata = {
            'name': filename,
            'parents': [subfolder_id]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes),
            mimetype='application/pdf' if filename.endswith('.pdf') else 'image/jpeg',
            resumable=True
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        print(f"✅ Facture uploadée sur Drive : {file.get('webViewLink')}")
        return {
            "success": True,
            "file_id": file.get('id'),
            "link": file.get('webViewLink')
        }

    except Exception as e:
        print(f"❌ Erreur upload Drive : {e}")
        return {"success": False, "error": str(e)}

def save_mandat_to_drive(pdf_bytes, filename, lead_data):
    """Sauvegarde le PDF du mandat dans Google Drive"""
    try:
        service = get_drive_service()

        # Structure: Leads LILIWATT / [DATE] - [NOM] - [MONTANT]€ / mandat.pdf
        root_folder_id = find_or_create_folder(service, "Leads LILIWATT")

        # Nom du sous-dossier (même que pour la facture)
        date_str = datetime.now().strftime("%Y%m%d")
        nom = lead_data.get('nom', 'Inconnu')
        montant = lead_data.get('montant', 0)
        subfolder_name = f"{date_str} - {nom} - {montant}€"

        subfolder_id = find_or_create_folder(service, subfolder_name, root_folder_id)

        # Upload le PDF du mandat
        file_metadata = {
            'name': filename,
            'parents': [subfolder_id]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            resumable=True
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        print(f"✅ Mandat sauvegardé sur Drive : {file.get('webViewLink')}")
        return {
            "success": True,
            "file_id": file.get('id'),
            "link": file.get('webViewLink')
        }

    except Exception as e:
        print(f"❌ Erreur sauvegarde mandat Drive : {e}")
        return {"success": False, "error": str(e)}

def save_lead(data):
    try:
        sheet = get_sheet()
        # Ajouter en-têtes si la feuille est vide
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "Date":
            sheet.insert_row([
                # Informations de base
                "Date", "Heure", "Prénom", "Nom", "Téléphone", "Email",

                # Identification
                "Type énergie", "Nom entreprise", "SIREN", "Adresse",

                # Facturation
                "Montant facture TTC", "Période", "Nb jours", "Fournisseur", "Nom offre", "Secteur",

                # Électricité - Contrat
                "PDL", "Puissance kVA", "Segment", "Option tarifaire", "Type contrat élec", "Date fin contrat",

                # Électricité - Prix
                "Prix kWh Base (c€)", "Prix kWh HP (c€)", "Prix kWh HC (c€)",
                "Abonnement élec HT/mois", "Conso élec kWh",

                # Gaz
                "PCE", "Prix kWh gaz (c€)", "Abonnement gaz HT/mois", "Conso gaz kWh", "Type contrat gaz",

                # Économies
                "Économies élec min (€)", "Économies élec max (€)",
                "Économies gaz min (€)", "Économies gaz max (€)",
                "TOTAL Économies min (€)", "TOTAL Économies max (€)",
                "Économies min (%)", "Économies max (%)", "Montant annuel (€)",

                # RGPD & Mandat
                "Mandat signé", "Lien Drive mandat", "IP signature", "Date signature mandat"
            ], 1)

        now = datetime.now()
        row = [
            # Informations de base
            now.strftime("%d/%m/%Y"),
            now.strftime("%H:%M"),
            data.get("prenom", ""),
            data.get("nom", ""),
            data.get("tel", ""),
            data.get("email", ""),

            # Identification
            data.get("type_energie", ""),
            data.get("nom_entreprise", ""),
            data.get("siren", ""),
            data.get("adresse", ""),

            # Facturation
            data.get("montant", ""),
            data.get("periode", ""),
            data.get("nb_jours_periode", ""),
            data.get("fourn", ""),
            data.get("nom_offre", ""),
            data.get("secteur", ""),

            # Électricité - Contrat
            data.get("pdl", ""),
            data.get("puissance_kva", ""),
            data.get("segment", ""),
            data.get("option_tarifaire", ""),
            data.get("contrat", ""),
            data.get("date_fin_contrat", ""),

            # Électricité - Prix
            data.get("prix_kwh_base_centimes", ""),
            data.get("prix_kwh_hp_centimes", ""),
            data.get("prix_kwh_hc_centimes", ""),
            data.get("abonnement_elec_ht_mois", ""),
            data.get("consommation_elec_kwh", ""),

            # Gaz
            data.get("pce", ""),
            data.get("prix_kwh_gaz_centimes", ""),
            data.get("abonnement_gaz_ht_mois", ""),
            data.get("consommation_gaz_kwh", ""),
            data.get("contrat_gaz", ""),

            # Économies
            data.get("eco_elec_min", ""),
            data.get("eco_elec_max", ""),
            data.get("eco_gaz_min", ""),
            data.get("eco_gaz_max", ""),
            data.get("eco_min", ""),
            data.get("eco_max", ""),
            data.get("pct_min", ""),
            data.get("pct_max", ""),
            data.get("montant_annuel", ""),

            # RGPD & Mandat
            data.get("mandat_signe", ""),
            data.get("mandat_drive_url", ""),
            data.get("ip_signature", ""),
            data.get("date_signature_mandat", ""),
        ]

        # IMPORTANT : Ne pas utiliser append_row() car ça décale les colonnes
        # si des cellules vides existent au milieu de la ligne
        # Trouver la prochaine ligne vide depuis la colonne A
        col_a = sheet.col_values(1)  # Récupère toutes les valeurs de colonne A
        next_row = len(col_a) + 1     # Prochaine ligne disponible

        # Écrire les données en partant exactement de la colonne A
        sheet.update(f'A{next_row}', [row])

        return True
    except Exception as e:
        print(f"Erreur Google Sheets : {e}")
        return False

# ─── CALCUL ÉCONOMIES ──────────────────────────────────────
def calcul_economies(montant, periode, contrat, type_energie="electricite", contrat_gaz=None, montant_elec=None, montant_gaz=None):
    """
    Calcule les économies pour électricité et/ou gaz

    Args:
        montant: montant total de la facture
        periode: mensuel/bimestriel/trimestriel
        contrat: type de contrat électricité
        type_energie: "electricite", "gaz", ou "les_deux"
        contrat_gaz: type de contrat gaz si applicable
        montant_elec: montant électricité si les_deux
        montant_gaz: montant gaz si les_deux
    """
    # Validation montant vide ou invalide
    if not montant or str(montant).strip() == '':
        return {
            "montant_annuel": 0,
            "eco_elec_min": 0,
            "eco_elec_max": 0,
            "eco_gaz_min": 0,
            "eco_gaz_max": 0,
            "eco_min": 0,
            "eco_max": 0,
            "pct_min": 0,
            "pct_max": 0,
        }

    # Annualisation
    facteurs = {"mensuel": 12, "bimestriel": 6, "trimestriel": 4}
    facteur = facteurs.get(periode, 12)

    # Taux d'économies selon type de contrat ÉLECTRICITÉ
    taux_elec = {
        "trv":     {"min": 10, "max": 22},
        "indexe":  {"min": 8,  "max": 18},
        "fixe":    {"min": 3,  "max": 10},
        "inconnu": {"min": 7,  "max": 18},
    }

    # Taux d'économies selon type de contrat GAZ
    taux_gaz = {
        "trv":     {"min": 10, "max": 20},
        "indexe":  {"min": 8,  "max": 15},
        "fixe":    {"min": 3,  "max": 8},
        "inconnu": {"min": 7,  "max": 15},
    }

    eco_elec_min = 0
    eco_elec_max = 0
    eco_gaz_min = 0
    eco_gaz_max = 0
    montant_annuel = 0
    pct_min = 0
    pct_max = 0

    try:
        if type_energie == "electricite":
            annuel = float(str(montant).replace(',', '.').replace(' ', '')) * facteur
            r = taux_elec.get(contrat, taux_elec["inconnu"])
            eco_elec_min = round(annuel * r["min"] / 100)
            eco_elec_max = round(annuel * r["max"] / 100)
            montant_annuel = round(annuel)
            pct_min = r["min"]
            pct_max = r["max"]

        elif type_energie == "gaz":
            annuel = float(str(montant).replace(',', '.').replace(' ', '')) * facteur
            r = taux_gaz.get(contrat_gaz or contrat, taux_gaz["inconnu"])
            eco_gaz_min = round(annuel * r["min"] / 100)
            eco_gaz_max = round(annuel * r["max"] / 100)
            montant_annuel = round(annuel)
            pct_min = r["min"]
            pct_max = r["max"]

        elif type_energie == "les_deux":
            # Si montants séparés fournis
            if montant_elec and montant_gaz:
                annuel_elec = float(str(montant_elec).replace(',', '.').replace(' ', '')) * facteur
                annuel_gaz = float(str(montant_gaz).replace(',', '.').replace(' ', '')) * facteur
            else:
                # Sinon, on estime 60% élec / 40% gaz
                annuel_total = float(str(montant).replace(',', '.').replace(' ', '')) * facteur
                annuel_elec = annuel_total * 0.6
                annuel_gaz = annuel_total * 0.4

            # Calcul économies électricité
            r_elec = taux_elec.get(contrat, taux_elec["inconnu"])
            eco_elec_min = round(annuel_elec * r_elec["min"] / 100)
            eco_elec_max = round(annuel_elec * r_elec["max"] / 100)

            # Calcul économies gaz
            r_gaz = taux_gaz.get(contrat_gaz or "inconnu", taux_gaz["inconnu"])
            eco_gaz_min = round(annuel_gaz * r_gaz["min"] / 100)
            eco_gaz_max = round(annuel_gaz * r_gaz["max"] / 100)

            montant_annuel = round(annuel_elec + annuel_gaz)
            # Pourcentage global moyen
            pct_min = round(((eco_elec_min + eco_gaz_min) / montant_annuel) * 100)
            pct_max = round(((eco_elec_max + eco_gaz_max) / montant_annuel) * 100)

    except (ValueError, TypeError) as e:
        print(f"⚠️ Erreur conversion montant dans calcul_economies : {e}")
        return {
            "montant_annuel": 0,
            "eco_elec_min": 0,
            "eco_elec_max": 0,
            "eco_gaz_min": 0,
            "eco_gaz_max": 0,
            "eco_min": 0,
            "eco_max": 0,
            "pct_min": 0,
            "pct_max": 0,
        }

    return {
        "montant_annuel": montant_annuel,
        "eco_elec_min": eco_elec_min,
        "eco_elec_max": eco_elec_max,
        "eco_gaz_min": eco_gaz_min,
        "eco_gaz_max": eco_gaz_max,
        "eco_min": eco_elec_min + eco_gaz_min,
        "eco_max": eco_elec_max + eco_gaz_max,
        "pct_min": pct_min,
        "pct_max": pct_max,
    }

# ─── INFOS CONTRAT ─────────────────────────────────────────
def infos_contrat(contrat):
    contrats = {
        "trv": {
            "tag":   "Tarif réglementé détecté",
            "classe": "warn",
            "titre": "TRV — souvent non optimisé pour les pros",
            "desc":  "Le tarif réglementé EDF/Engie est rarement le plus compétitif pour les professionnels. Des offres de marché permettent des économies immédiates."
        },
        "indexe": {
            "tag":   "Contrat indexé détecté",
            "classe": "warn",
            "titre": "Prix variable — vous êtes exposé aux hausses",
            "desc":  "Votre prix suit les fluctuations du marché de gros. Un contrat à prix fixe vous protège contre les pics de prix."
        },
        "fixe": {
            "tag":   "Contrat fixe détecté",
            "classe": "ok",
            "titre": "Prix garanti — optimisation possible au renouvellement",
            "desc":  "Votre contrat vous protège des hausses. Une renégociation à l'échéance peut tout de même générer des économies significatives."
        },
        "inconnu": {
            "tag":   "Contrat à identifier",
            "classe": "info",
            "titre": "Type de contrat indéterminé",
            "desc":  "Votre conseiller LILIWATT analysera votre contrat exact et identifiera le meilleur levier d'optimisation pour votre situation."
        }
    }
    return contrats.get(contrat, contrats["inconnu"])

# ─── EMAILS ────────────────────────────────────────────────
def send_email_prospect(data, eco):
    """Email prospect - SANS pièce jointe PDF"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Votre analyse LILIWATT — {eco['eco_min']}€ à {eco['eco_max']}€ d'économies potentielles"
        msg["From"]    = "LILIWATT <contact@liliwatt.fr>"
        msg["Reply-To"] = "contact@liliwatt.fr"
        msg["To"]      = data["email"]

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#1a1a2e">
          <div style="background:#06060F;padding:24px;border-radius:8px 8px 0 0;text-align:center">
            <span style="font-family:monospace;font-size:18px;font-weight:900;color:#A78BFA;letter-spacing:4px">LILIWATT</span>
            <p style="color:#6B7280;font-size:11px;letter-spacing:3px;margin:4px 0 0">COURTAGE ÉNERGIE · B2B & B2C</p>
          </div>
          <div style="background:#ffffff;padding:32px;border:1px solid #e5e7eb">
            <p style="font-size:16px;color:#374151">Bonjour <strong>{data['prenom']}</strong>,</p>
            <p style="color:#6B7280">Votre analyse de facture LILIWATT est prête.</p>

            <div style="background:#f5f3ff;border:2px solid #7C3AED;border-radius:8px;padding:24px;text-align:center;margin:24px 0">
              <p style="font-size:12px;color:#7C3AED;letter-spacing:2px;text-transform:uppercase;margin:0 0 8px">Potentiel d'économies annuel</p>
              <p style="font-size:36px;font-weight:700;color:#1a1a2e;margin:0">{eco['eco_min']:,} € — {eco['eco_max']:,} €</p>
              <p style="font-size:13px;color:#6B7280;margin:8px 0 0">soit {eco['pct_min']}% à {eco['pct_max']}% sur votre facture actuelle</p>
            </div>

            <p style="color:#374151">Votre mandat de courtage a été enregistré. Un conseiller LILIWATT vous contactera sous <strong>24h ouvrées</strong> pour vous présenter les meilleures offres disponibles.</p>
            <p style="color:#6B7280;font-size:13px">Sans frais · Sans engagement · Sans coupure</p>
          </div>
          <div style="background:#f9fafb;padding:16px;border-radius:0 0 8px 8px;text-align:center">
            <p style="font-size:11px;color:#9CA3AF;margin:0">LILIWATT — Courtage en énergie</p>
            <p style="font-size:11px;color:#9CA3AF;margin:4px 0 0">contact@liliwatt.fr · www.liliwatt.fr</p>
          </div>
        </div>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.zoho.eu", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, data["email"], msg.as_string())
        return True
    except Exception as e:
        print(f"Erreur email prospect : {e}")
        return False

def send_alert_conseiller(data, eco, doc_id=None, facture_id=None):
    """Email conseiller - génère et joint le PDF du mandat depuis le HTML + la facture"""
    print(f"📧 send_alert_conseiller appelé avec facture_id={facture_id}, doc_id={doc_id}")
    print(f"📦 factures_temp contient : {list(factures_temp.keys())}")
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"🔔 Nouveau mandat signé — {data['prenom']} {data['nom']} — {eco['eco_min']}€ à {eco['eco_max']}€"
        msg["From"]    = "LILIWATT Leads <contact@liliwatt.fr>"
        msg["Reply-To"] = "contact@liliwatt.fr"
        msg["To"]      = CONSEILLER_EMAIL

        # Générer le PDF du mandat depuis le HTML pour l'email
        mandat_pdf_bytes = None
        mandat_filename = None
        if doc_id and doc_id in mandats_temp:
            try:
                mandat_data = mandats_temp[doc_id]
                # Rendre le template HTML
                html_content = render_template('mandat_template.html', **mandat_data)
                # Convertir HTML en PDF via PDFShift
                response = requests.post(
                    'https://api.pdfshift.io/v3/convert/pdf',
                    headers={'X-API-Key': PDFSHIFT_API_KEY, 'Content-Type': 'application/json'},
                    json={'source': html_content, 'sandbox': False}
                )
                if response.status_code == 200:
                    mandat_pdf_bytes = response.content
                    mandat_filename = f"mandat_{data.get('nom', '')}_{doc_id}.pdf"
            except Exception as e:
                print(f"Erreur génération PDF mandat : {e}")

        # Récupérer la facture si disponible
        facture_bytes = None
        facture_filename = None
        print(f"🔍 Vérification facture_id: {facture_id}")
        if facture_id:
            print(f"✅ facture_id présent: {facture_id}")
            if facture_id in factures_temp:
                print(f"✅ facture_id trouvé dans factures_temp")
                try:
                    facture_data = factures_temp[facture_id]
                    print(f"📄 facture_data: {facture_data}")
                    # Lire depuis disque
                    file_path = facture_data.get('file_path')
                    print(f"📂 file_path: {file_path}")
                    if file_path and os.path.exists(file_path):
                        print(f"✅ Fichier existe sur disque: {file_path}")
                        with open(file_path, 'rb') as fp:
                            facture_bytes = fp.read()
                        print(f"✅ Facture lue ({len(facture_bytes)} bytes)")
                        os.remove(file_path)  # Nettoyer après envoi
                        print(f"🗑️ Fichier supprimé: {file_path}")
                    else:
                        print(f"⚠️ Fichier n'existe pas sur disque, fallback vers file_bytes")
                        facture_bytes = facture_data.get('file_bytes', b'')
                    facture_filename = facture_data['filename']
                    print(f"📎 Facture récupérée pour email : {facture_filename}")
                except Exception as e:
                    print(f"❌ Erreur récupération facture : {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"❌ facture_id '{facture_id}' NOT FOUND dans factures_temp")
                print(f"📦 Keys disponibles: {list(factures_temp.keys())}")
        else:
            print(f"❌ facture_id est None ou vide")

        mandat_section = ""
        if mandat_pdf_bytes:
            mandat_section = f"""
              <tr><td colspan="2"><hr style="border:none;border-top:1px solid #e5e7eb;margin:8px 0"></td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Mandat signé</td>
                  <td>
                    <span style="color:#10B981;font-weight:600">✅ PDF du mandat joint ci-dessous</span>
                    <br><span style="font-size:11px;color:#6B7280;">Document généré électroniquement</span>
                  </td></tr>
            """

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto">
          <div style="background:#7C3AED;padding:16px 24px;border-radius:8px 8px 0 0">
            <span style="color:#fff;font-weight:700;font-size:16px">🔔 Nouveau mandat signé LILIWATT</span>
          </div>
          <div style="background:#fff;padding:24px;border:1px solid #e5e7eb">
            <table style="width:100%;font-size:14px;border-collapse:collapse">
              <tr><td style="color:#6B7280;padding:6px 0;width:40%">Nom</td><td style="font-weight:600">{data.get('prenom', '')} {data.get('nom', '')}</td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Téléphone</td><td><a href="tel:{data.get('tel', '')}" style="color:#7C3AED;font-weight:600">{data.get('tel', '')}</a></td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Email</td><td><a href="mailto:{data.get('email', '')}" style="color:#7C3AED">{data.get('email', '')}</a></td></tr>
              <tr><td colspan="2"><hr style="border:none;border-top:1px solid #e5e7eb;margin:8px 0"></td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Facture</td><td>{data.get('montant', 0)}€ / {data.get('periode', '1 mois')}</td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Fournisseur</td><td>{data.get('fourn', 'N/A')}</td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Secteur</td><td>{data.get('secteur', 'N/A')}</td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Contrat</td><td>{data.get('contrat', 'N/A')}</td></tr>
              <tr><td colspan="2"><hr style="border:none;border-top:1px solid #e5e7eb;margin:8px 0"></td></tr>
              <tr><td style="color:#6B7280;padding:6px 0">Économies estimées</td>
                  <td style="font-size:18px;font-weight:700;color:#7C3AED">{eco['eco_min']:,}€ — {eco['eco_max']:,}€/an</td></tr>
              {mandat_section}
            </table>
          </div>
          <div style="background:#f5f3ff;padding:12px 24px;border-radius:0 0 8px 8px;text-align:center">
            <p style="font-size:12px;color:#7C3AED;margin:0">Rappeler sous 24h · Lead entrant le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
          </div>
        </div>
        """

        msg_html = MIMEMultipart("alternative")
        msg_html.attach(MIMEText(html, "html"))
        msg.attach(msg_html)

        # Ajouter le PDF en pièce jointe
        if mandat_pdf_bytes and mandat_filename:
            pdf_attachment = MIMEApplication(mandat_pdf_bytes, _subtype="pdf")
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=mandat_filename)
            msg.attach(pdf_attachment)

        # Ajouter la facture en pièce jointe
        if facture_bytes and facture_filename:
            ext = facture_filename.rsplit('.', 1)[1].lower() if '.' in facture_filename else ''
            if ext == 'pdf':
                facture_attachment = MIMEApplication(facture_bytes, _subtype="pdf")
            elif ext in ['jpg', 'jpeg']:
                facture_attachment = MIMEApplication(facture_bytes, _subtype="jpeg")
            elif ext == 'png':
                facture_attachment = MIMEApplication(facture_bytes, _subtype="png")
            else:
                facture_attachment = MIMEApplication(facture_bytes)

            facture_attachment.add_header('Content-Disposition', 'attachment', filename=facture_filename)
            msg.attach(facture_attachment)
            print(f"✅ Facture attachée à l'email : {facture_filename}")

        with smtplib.SMTP_SSL("smtp.zoho.eu", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, CONSEILLER_EMAIL, msg.as_string())
            print(f"✅ Email conseiller envoyé avec succès à {CONSEILLER_EMAIL}")
        return True
    except Exception as e:
        import traceback
        print(f"❌ Erreur email conseiller : {e}")
        print(f"❌ Traceback complet : {traceback.format_exc()}")
        return False

def send_contact_email(nom, email, telephone, message, sujet):
    """Email pour formulaire de contact générique"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[LILIWATT] {sujet} — {nom}"
        msg["From"]    = "LILIWATT <contact@liliwatt.fr>"
        msg["To"]      = "contact@liliwatt.fr"
        msg["Reply-To"] = email

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #7C3AED; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0; font-family: monospace; letter-spacing: 4px;">LILIWATT</h1>
            <p style="color: #A78BFA; margin: 5px 0; font-size: 12px; letter-spacing: 2px;">
              Nouveau message reçu
            </p>
          </div>
          <div style="background: #0D0D1F; padding: 30px; color: #F0EEFF;">
            <p><strong style="color: #A78BFA;">Nom :</strong> {nom}</p>
            <p><strong style="color: #A78BFA;">Email :</strong> <a href="mailto:{email}" style="color: #D946EF;">{email}</a></p>
            <p><strong style="color: #A78BFA;">Téléphone :</strong> {telephone if telephone else 'Non fourni'}</p>
            <p><strong style="color: #A78BFA;">Sujet :</strong> {sujet}</p>
            <div style="background: #1E1B4B; padding: 15px; border-radius: 8px; margin-top: 15px;">
              <p style="margin: 0; white-space: pre-wrap;">{message}</p>
            </div>
          </div>
          <div style="background: #06060F; padding: 15px; text-align: center; color: #6B7280; font-size: 12px;">
            LILIWATT · contact@liliwatt.fr · <a href="https://liliwatt.fr" style="color: #A78BFA;">liliwatt.fr</a>
          </div>
        </div>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.zoho.eu", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, "contact@liliwatt.fr", msg.as_string())
        return True
    except Exception as e:
        print(f"Erreur email contact : {e}")
        return False

def send_recrutement_email(nom, email, telephone, poste, message, cv_filename=None, cv_bytes=None):
    """Email pour formulaire de recrutement avec CV en pièce jointe"""
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"[LILIWATT RECRUTEMENT] Candidature de {nom} — {poste}"
        msg["From"]    = "LILIWATT <contact@liliwatt.fr>"
        msg["To"]      = "recrutement@liliwatt.fr"
        msg["Reply-To"] = email

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #7C3AED; padding: 20px; text-align: center;">
            <h1 style="color: white; margin: 0; font-family: monospace; letter-spacing: 4px;">LILIWATT</h1>
            <p style="color: #A78BFA; margin: 5px 0; font-size: 12px; letter-spacing: 2px;">
              Nouvelle candidature reçue
            </p>
          </div>
          <div style="background: #0D0D1F; padding: 30px; color: #F0EEFF;">
            <p><strong style="color: #A78BFA;">Poste visé :</strong> <span style="color: #D946EF; font-weight: 600;">{poste}</span></p>
            <hr style="border: none; border-top: 1px solid #1E1B4B; margin: 15px 0;">
            <p><strong style="color: #A78BFA;">Nom :</strong> {nom}</p>
            <p><strong style="color: #A78BFA;">Email :</strong> <a href="mailto:{email}" style="color: #D946EF;">{email}</a></p>
            <p><strong style="color: #A78BFA;">Téléphone :</strong> {telephone if telephone else 'Non fourni'}</p>
            <hr style="border: none; border-top: 1px solid #1E1B4B; margin: 15px 0;">
            <p><strong style="color: #A78BFA;">Message / Lettre de motivation :</strong></p>
            <div style="background: #1E1B4B; padding: 15px; border-radius: 8px; margin-top: 10px;">
              <p style="margin: 0; white-space: pre-wrap;">{message if message else '(Aucun message fourni)'}</p>
            </div>
            {f'<p style="margin-top: 15px;"><strong style="color: #A78BFA;">CV joint :</strong> 📎 {cv_filename}</p>' if cv_filename else ''}
          </div>
          <div style="background: #06060F; padding: 15px; text-align: center; color: #6B7280; font-size: 12px;">
            LILIWATT · recrutement@liliwatt.fr · <a href="https://liliwatt.fr" style="color: #A78BFA;">liliwatt.fr</a>
          </div>
        </div>
        """

        # Attacher le corps HTML
        msg_html = MIMEMultipart("alternative")
        msg_html.attach(MIMEText(html, "html"))
        msg.attach(msg_html)

        # Ajouter le CV en pièce jointe si fourni
        if cv_bytes and cv_filename:
            # Déterminer le type MIME selon l'extension
            ext = cv_filename.rsplit('.', 1)[1].lower() if '.' in cv_filename else ''
            if ext == 'pdf':
                cv_attachment = MIMEApplication(cv_bytes, _subtype="pdf")
            elif ext in ['doc', 'docx']:
                cv_attachment = MIMEApplication(cv_bytes, _subtype="vnd.openxmlformats-officedocument.wordprocessingml.document")
            else:
                cv_attachment = MIMEApplication(cv_bytes)

            cv_attachment.add_header('Content-Disposition', 'attachment', filename=cv_filename)
            msg.attach(cv_attachment)

        with smtplib.SMTP_SSL("smtp.zoho.eu", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, "recrutement@liliwatt.fr", msg.as_string())
        return True
    except Exception as e:
        print(f"Erreur email recrutement : {e}")
        return False

# ─── CLAUDE VISION — ANALYSE DE FACTURE ────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_base64(image):
    """Convertit une image PIL en base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def analyze_invoice_with_claude(image_bytes, file_extension):
    """Analyse une facture avec Claude Vision API"""
    import time
    import base64

    try:
        # Variables pour stocker le contenu à envoyer à Claude
        content_images = []  # Liste d'images (pour support multi-pages PDF)
        media_type = None

        # Normaliser l'extension
        file_extension = file_extension.lower()

        # Si c'est un PDF, essayer de convertir en image, sinon utiliser le PDF directement
        if file_extension == 'pdf':
            print(f"📄 Conversion PDF en cours...")
            # Chemin poppler : macOS (/opt/homebrew/bin) vs Linux (/usr/bin)
            import platform
            system_os = platform.system()
            print(f"   🖥️ Système d'exploitation : {system_os}")

            poppler_path = "/opt/homebrew/bin" if system_os == "Darwin" else None
            print(f"   📁 Chemin poppler : {poppler_path if poppler_path else 'Chemin système par défaut'}")

            try:
                # Convertir jusqu'à 3 pages maximum
                if poppler_path:
                    images = convert_from_bytes(
                        image_bytes,
                        first_page=1,
                        last_page=3,  # Lire jusqu'à 3 pages
                        poppler_path=poppler_path
                    )
                else:
                    # Sur Linux/Render, utiliser le chemin système par défaut
                    images = convert_from_bytes(
                        image_bytes,
                        first_page=1,
                        last_page=3  # Lire jusqu'à 3 pages
                    )
                if not images:
                    raise Exception("Aucune image générée par pdf2image")

                print(f"✅ PDF converti en {len(images)} page(s)")

                # Convertir toutes les pages (max 3) en base64
                for i, image in enumerate(images[:3], 1):  # Limiter à 3 pages max
                    print(f"🔄 Conversion page {i} en base64...")
                    image_b64 = image_to_base64(image)
                    content_images.append(image_b64)
                    print(f"✅ Page {i} convertie : {len(image_b64)} caractères")

                media_type = "image/png"
                print(f"✅ {len(content_images)} page(s) prête(s) pour Claude")

            except Exception as pdf_error:
                print(f"⚠️ Conversion PDF→image échouée : {pdf_error}")
                import traceback
                print(f"   Traceback : {traceback.format_exc()}")

                # FALLBACK : Envoyer le PDF directement à Claude (supporté nativement)
                print(f"🔄 FALLBACK : Envoi du PDF directement à Claude...")
                pdf_b64 = base64.b64encode(image_bytes).decode('utf-8')
                content_images = [pdf_b64]
                media_type = "application/pdf"
                print(f"✅ Base64 PDF créé : {len(pdf_b64)} caractères")

        elif file_extension in ['heic', 'heif']:
            # Convertir HEIC/HEIF en JPEG
            print(f"🖼️ Conversion HEIC/HEIF → JPEG...")
            try:
                image = Image.open(io.BytesIO(image_bytes))
                # Convertir en RGB si nécessaire (HEIC peut être en RGBA)
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Sauvegarder en JPEG
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=95)
                image_bytes = buffer.getvalue()

                print(f"✅ HEIC converti en JPEG : {image.size}")

                # Convertir en base64
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                content_images = [image_b64]
                media_type = "image/jpeg"
                print(f"✅ Base64 JPEG créé : {len(image_b64)} caractères")
            except Exception as heic_error:
                print(f"❌ Erreur conversion HEIC : {heic_error}")
                raise Exception(f"Format HEIC non supporté ou fichier corrompu : {heic_error}")

        elif file_extension in ['jpg', 'jpeg']:
            # JPG/JPEG - traitement direct
            print(f"🖼️ Image JPEG détectée, traitement direct...")
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            content_images = [image_b64]
            media_type = "image/jpeg"
            print(f"✅ Base64 JPEG créé : {len(image_b64)} caractères")

        elif file_extension == 'png':
            # PNG - traitement direct
            print(f"🖼️ Image PNG détectée, traitement direct...")
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            content_images = [image_b64]
            media_type = "image/png"
            print(f"✅ Base64 PNG créé : {len(image_b64)} caractères")

        elif file_extension == 'webp':
            # WEBP - traitement direct
            print(f"🖼️ Image WEBP détectée, traitement direct...")
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            content_images = [image_b64]
            media_type = "image/webp"
            print(f"✅ Base64 WEBP créé : {len(image_b64)} caractères")

        else:
            # Format inconnu - essayer de charger comme image générique
            print(f"🖼️ Format {file_extension.upper()} - tentative chargement générique...")
            try:
                image = Image.open(io.BytesIO(image_bytes))
                print(f"✅ Image chargée : {image.size}")

                # Convertir en base64 PNG
                print(f"🔄 Conversion base64 PNG...")
                image_b64 = image_to_base64(image)
                content_images = [image_b64]
                media_type = "image/png"
                print(f"✅ Base64 créé : {len(image_b64)} caractères")
            except Exception as img_error:
                print(f"❌ Erreur chargement image : {img_error}")
                raise Exception(f"Format {file_extension} non supporté : {img_error}")

        # Prompt d'extraction amélioré avec instructions détaillées
        prompt = """Tu es un expert comptable spécialisé en factures d'énergie françaises B2B et B2C.

Analyse TOUTES les pages de cette facture avec une attention maximale et extrait ces informations. Cherche sur TOUTES les pages, notamment la dernière qui contient souvent les détails du contrat.

Retourne UNIQUEMENT ce JSON sans aucun texte autour :

{
  "fournisseur": "nom exact du fournisseur (EDF, ENGIE, TotalEnergies, etc.) - visible sur le logo ou l'en-tête",
  "offre": "nom exact de l'offre commerciale (ex: Maitriz'Elec, Zen, Tempo, etc.)",
  "option_tarifaire": "BASE ou HPHC ou C4 ou C5 ou autre option tarifaire exacte",
  "puissance_souscrite": "puissance en kVA (cherche 'puissance souscrite' ou 'kVA')",
  "pdl": "numéro PDL ou PRM sans espaces (14 chiffres)",
  "abonnement_mensuel_ht": "montant abonnement mensuel HT en euros (cherche 'Abonnement du ... au ...')",
  "consommation_annuelle_kwh": "consommation totale en kWh visible sur la facture",
  "consommation_periode_kwh": "consommation de la période facturée en kWh",
  "prix_kwh_ht": "prix unitaire en euros HT par kWh (cherche 'Prix unitaire' ou '€/kWh')",
  "montant_facture_ttc": "montant TOTAL TTC à payer en euros (cherche 'MONTANT TTC', 'Net à payer', 'Total TTC')",
  "periode_debut": "date début consommation format DD/MM/YYYY",
  "periode_fin": "date fin consommation format DD/MM/YYYY",
  "type_contrat": "fixe si offre à prix fixe, variable sinon",
  "date_fin_contrat": "date échéance du contrat format DD/MM/YYYY (cherche 'Date échéance', 'Fin de contrat')",
  "energie": "electricite ou gaz",
  "segment": "C1 C2 C3 C4 C5 ou particulier selon le type de compteur et puissance"
}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après, sans markdown, sans backticks."""

        # Appel à Claude Vision avec retry logic
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                model_name = "claude-haiku-4-5-20251001"
                print(f"🤖 Appel Claude Vision (tentative {attempt + 1}/{max_retries})...")
                print(f"   📌 Modèle : {model_name}")
                print(f"   📌 Max tokens : 1024")
                print(f"   📌 Nombre d'images : {len(content_images)}")
                print(f"   📌 Type de média : {media_type}")
                print(f"   📌 Taille prompt : {len(prompt)} caractères")

                # Déterminer le type de contenu pour l'API
                content_type = "document" if media_type == "application/pdf" else "image"

                # Construire la liste de content items (une image par item)
                content_items = []
                for i, img_b64 in enumerate(content_images, 1):
                    if media_type == "application/pdf":
                        content_items.append({
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        })
                    else:
                        content_items.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        })
                    print(f"   📄 Image {i} ajoutée au payload ({len(img_b64)} caractères)")

                # Ajouter le prompt à la fin
                content_items.append({
                    "type": "text",
                    "text": prompt
                })

                # Log du payload summary
                payload_summary = {
                    "model": model_name,
                    "max_tokens": 1024,
                    "nb_images": len(content_images),
                    "type_media": media_type
                }
                print(f"   📦 Payload summary : {json.dumps(payload_summary, indent=2)}")
                print(f"📊 Nombre de pages envoyées à Claude : {len(content_images)}")

                try:
                    message = anthropic_client.messages.create(
                        model=model_name,
                        max_tokens=1024,
                        messages=[
                            {
                                "role": "user",
                                "content": content_items
                            }
                        ],
                    )
                    print(f"✅ Réponse Claude reçue")
                    print(f"   API Response: {message}")
                    print(f"   📊 Status : {message.stop_reason}")
                    print(f"   📊 Tokens utilisés : input={message.usage.input_tokens}, output={message.usage.output_tokens}")
                    print(f"   📊 ID message : {message.id}")
                except Exception as api_call_error:
                    print(f"API ERROR:")
                    import traceback
                    print(traceback.format_exc())
                    raise

                break  # Success, exit retry loop

            except Exception as api_error:
                print(f"⚠️ Erreur API Claude (tentative {attempt + 1}) : {api_error}")
                import traceback
                print(f"   Traceback API error:\n{traceback.format_exc()}")
                if attempt < max_retries - 1:
                    print(f"⏳ Nouvelle tentative dans {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"❌ Échec après {max_retries} tentatives")
                    return {"error": f"API Claude temporairement indisponible : {str(api_error)}"}

        # Extraire le JSON de la réponse
        response_text = message.content[0].text.strip()

        # Log de la réponse brute pour débogage
        print("=" * 60)
        print("RÉPONSE BRUTE DE CLAUDE :")
        print(response_text)
        print("=" * 60)

        # Nettoyer le texte pour extraire uniquement le JSON (regex robuste)
        # D'abord essayer de retirer les backticks markdown si présents
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Ensuite utiliser regex pour extraire le JSON même s'il y a du texte autour
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()
            print(f"✅ JSON extrait par regex : {len(response_text)} caractères")
        else:
            print(f"⚠️ Aucun JSON détecté par regex, tentative parsing direct")

        # Parser le JSON
        try:
            data = json.loads(response_text)
            print(f"✅ JSON parsé avec succès : {data}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON : {e}")
            print(f"Réponse nettoyée : {response_text}")
            return {"error": "Format de réponse invalide de Claude", "raw": response_text}

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        print(f"❌ Erreur générale analyse facture : {e}")
        import traceback
        print("=== TRACEBACK COMPLET analyze_invoice_with_claude ===")
        print(traceback.format_exc())
        print("=" * 60)
        return {"error": str(e)}

# ──── ROUTES PAGES STATIQUES ─────────────────────────────────
@app.route('/')
def index():
    return serve_html('index.html')

@app.route('/apropos')
@app.route('/apropos.html')
def apropos():
    return serve_html('apropos.html')

@app.route('/offres')
@app.route('/offres.html')
def offres():
    return serve_html('offres.html')

@app.route('/recrutement')
@app.route('/recrutement.html')
def recrutement():
    return serve_html('recrutement.html')

@app.route('/contact')
@app.route('/contact.html')
def contact():
    return serve_html('contact.html')

@app.route('/c2e')
@app.route('/c2e.html')
def c2e():
    """Page C2E - Certificats d'Économies d'Énergie et aides à la rénovation"""
    return serve_html('c2e.html')

@app.route('/mentions-legales')
@app.route('/mentions-legales.html')
def mentions_legales():
    """Mentions légales"""
    return serve_html('mentions-legales.html')

@app.route('/politique-confidentialite')
@app.route('/politique-confidentialite.html')
def politique_confidentialite():
    """Politique de confidentialité et RGPD"""
    return serve_html('politique-confidentialite.html')

@app.route('/rgpd')
@app.route('/rgpd.html')
def rgpd():
    """Page d'exercice des droits RGPD"""
    return serve_html('rgpd.html')

@app.route('/extracteur')
def extracteur():
    """Page extracteur de factures avec Claude Vision AI"""
    return render_template('extracteur.html')

@app.route('/extracteur.html')
def extracteur_html():
    """Redirection de /extracteur.html vers /extracteur"""
    return redirect('/extracteur', code=301)

@app.route('/blog-article.html')
def blog_article():
    return serve_html('blog-article.html')

@app.route('/blog-reduire-facture-electricite-2026.html')
def blog_reduire_facture():
    return serve_html('blog-reduire-facture-electricite-2026.html')

# ──── ROUTES API EXTRACTEUR ──────────────────────────────────
@app.route("/api/analyze-invoice", methods=["POST"])
def analyze_invoice():
    """Endpoint pour analyser une facture uploadée"""
    try:
        print("=== ANALYZE INVOICE CALLED ===")
        print(f"File received: {request.files}")
        print(f"API Key present: {bool(os.environ.get('ANTHROPIC_API_KEY'))}")

        print("\n" + "="*60)
        print("📥 NOUVEAU UPLOAD DE FACTURE")
        print("="*60)

        # Vérifier la configuration API
        api_key_status = "✅ Configurée" if ANTHROPIC_API_KEY else "❌ MANQUANTE"
        print(f"🔑 ANTHROPIC_API_KEY : {api_key_status}")
        if ANTHROPIC_API_KEY:
            print(f"   Longueur clé : {len(ANTHROPIC_API_KEY)} caractères")
            print(f"   Préfixe : {ANTHROPIC_API_KEY[:10]}...")
        else:
            print(f"   ⚠️ Vérification os.environ : {bool(os.environ.get('ANTHROPIC_API_KEY'))}")

        # Vérifier qu'un fichier est présent
        print(f"📋 Headers requête : {dict(request.headers)}")
        print(f"📦 Fichiers dans la requête : {list(request.files.keys())}")

        if 'file' not in request.files:
            print("❌ ERREUR : Aucun fichier dans la requête")
            return jsonify({"success": False, "error": "Aucun fichier fourni"}), 400

        file = request.files['file']
        print(f"✅ Fichier reçu : {file.filename}")

        if file.filename == '':
            print("❌ ERREUR : Nom de fichier vide")
            return jsonify({"success": False, "error": "Nom de fichier vide"}), 400

        if not allowed_file(file.filename):
            print(f"❌ ERREUR : Format non accepté : {file.filename}")
            return jsonify({"success": False, "error": "Format de fichier non accepté"}), 400

        # Lire le fichier
        print(f"📖 Lecture du fichier...")
        file_bytes = file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(file.filename)

        print(f"✅ Fichier lu avec succès")
        print(f"   - Nom sécurisé : {filename}")
        print(f"   - Extension : {file_extension}")
        print(f"   - Taille : {file_size_mb:.2f} MB ({len(file_bytes)} bytes)")

        # Analyser avec Claude
        print(f"🤖 Appel de analyze_invoice_with_claude()...")
        result = analyze_invoice_with_claude(file_bytes, file_extension)

        print(f"📊 Résultat de l'analyse : {result.get('success', False)}")
        
        # Stocker la facture sur disque (survit aux redémarrages worker)
        import uuid
        facture_id = str(uuid.uuid4())[:8].upper()
        temp_dir = '/tmp/liliwatt_factures'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{facture_id}_{filename}")
        with open(temp_path, 'wb') as tmp_f:
            tmp_f.write(file_bytes)
        factures_temp[facture_id] = {
            'file_path': temp_path,
            'filename': filename,
            'extension': file_extension
        }
        result['facture_id'] = facture_id
        print(f"💾 Facture stockée sur disque avec ID: {facture_id} -> {temp_path}")

        # Envoyer email immédiat avec la facture au conseiller
        try:
            print(f"📧 Envoi email immédiat au conseiller avec facture {facture_id}")

            msg = MIMEMultipart("mixed")
            msg["From"] = GMAIL_USER
            msg["To"] = CONSEILLER_EMAIL
            msg["Subject"] = f"📄 Nouvelle facture uploadée — {filename}"

            # Extraire les données détectées pour l'email
            provider = result.get('data', {}).get('fournisseur', 'Non détecté')
            segment = result.get('data', {}).get('segment', 'Non détecté')
            montant = result.get('data', {}).get('montant', 'Non détecté')

            html_body = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <h2 style="color:#d32f2f;">⚠️ Nouvelle facture uploadée</h2>
                <p><strong>ATTENTION :</strong> Le visiteur n'a pas encore complété le formulaire.</p>
                <p>Cette facture a été uploadée et analysée, mais le visiteur n'a pas encore soumis ses coordonnées.</p>

                <h3>Informations de la facture :</h3>
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="background:#f5f5f5;">
                        <td style="padding:8px;border:1px solid #ddd;"><strong>ID Facture</strong></td>
                        <td style="padding:8px;border:1px solid #ddd;">{facture_id}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px;border:1px solid #ddd;"><strong>Nom du fichier</strong></td>
                        <td style="padding:8px;border:1px solid #ddd;">{filename}</td>
                    </tr>
                    <tr style="background:#f5f5f5;">
                        <td style="padding:8px;border:1px solid #ddd;"><strong>Fournisseur détecté</strong></td>
                        <td style="padding:8px;border:1px solid #ddd;">{provider}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px;border:1px solid #ddd;"><strong>Segment</strong></td>
                        <td style="padding:8px;border:1px solid #ddd;">{segment}</td>
                    </tr>
                    <tr style="background:#f5f5f5;">
                        <td style="padding:8px;border:1px solid #ddd;"><strong>Montant TTC</strong></td>
                        <td style="padding:8px;border:1px solid #ddd;">{montant}</td>
                    </tr>
                </table>

                <p style="margin-top:20px;color:#666;">
                    <em>La facture est jointe à cet email. Si le visiteur complète le formulaire,
                    vous recevrez un second email avec toutes ses coordonnées.</em>
                </p>
            </div>
            """

            msg.attach(MIMEText(html_body, "html"))

            # Attacher la facture
            with open(temp_path, 'rb') as f:
                facture_attachment = MIMEApplication(f.read(), _subtype=file_extension.lstrip('.'))
                facture_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(facture_attachment)

            # Envoyer l'email
            with smtplib.SMTP_SSL("smtp.zoho.eu", 465) as server:
                server.login(GMAIL_USER, GMAIL_PASSWORD)
                server.sendmail(GMAIL_USER, CONSEILLER_EMAIL, msg.as_string())

            print(f"✅ Email immédiat envoyé au conseiller avec succès")
        except Exception as e:
            print(f"⚠️ Erreur envoi email immédiat (non bloquant) : {e}")
            import traceback
            traceback.print_exc()

        if "error" in result:
            print(f"❌ ERREUR retournée par analyze_invoice_with_claude : {result['error']}")
            return jsonify({"success": False, "error": result["error"]}), 500

        # Upload vers Google Drive si extraction réussie
        # DÉSACTIVÉ TEMPORAIREMENT (Service Account sans quota - erreur 403)
        if result.get("success") and result.get("data"):
            print(f"⚠️ Upload Google Drive désactivé temporairement (quota 403)")
            result["drive"] = {
                "success": False,
                "link": None,
                "error": "Upload Drive désactivé"
            }
            # print(f"📤 Upload vers Google Drive...")
            # lead_data = {
            #     "nom": "Lead",
            #     "montant": result["data"].get("montant", 0)
            # }
            # drive_result = upload_invoice_to_drive(file_bytes, filename, lead_data)
            # result["drive"] = drive_result
            # print(f"✅ Upload Drive : {drive_result.get('success', False)}")

        print(f"✅ SUCCÈS - Retour de la réponse")
        print("="*60 + "\n")
        return jsonify(result)

    except Exception as e:
        print(f"❌ EXCEPTION CRITIQUE dans endpoint analyze-invoice : {e}")
        print(f"   Type d'erreur : {type(e).__name__}")
        import traceback
        print("=== TRACEBACK COMPLET ENDPOINT ===")
        print(traceback.format_exc())
        print("=" * 60)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/submit-lead", methods=["POST"])
def submit_lead():
    try:
        data = request.get_json()

        # Récupérer le montant, avec fallback sur montant_facture_ttc
        montant = data.get("montant") or data.get("montant_facture_ttc") or 0
        periode = data.get("periode") or data.get("periode_couverte") or "mensuel"

        # Convertir période si nécessaire
        if periode and isinstance(periode, int):
            if periode == 1:
                periode = "mensuel"
            elif periode == 2:
                periode = "bimestriel"
            elif periode == 3:
                periode = "trimestriel"

        # Calcul économies avec support gaz
        eco = calcul_economies(
            montant=montant,
            periode=periode,
            contrat=data.get("contrat", "inconnu"),
            type_energie=data.get("type_energie", "electricite"),
            contrat_gaz=data.get("contrat_gaz"),
            montant_elec=data.get("montant_elec"),
            montant_gaz=data.get("montant_gaz")
        )

        # Infos contrat (électricité)
        infos = infos_contrat(data.get("contrat", "inconnu"))

        # ── GÉNÉRATION DU MANDAT DE COURTAGE ──
        mandat_pdf_bytes = None
        mandat_filename = None
        mandat_drive_url = None
        doc_id = None

        # Générer le PDF du mandat si consentement RGPD
        if data.get("rgpd_consent"):
            date_signature = datetime.now().strftime('%d/%m/%Y à %H:%M')
            client_ip = request.remote_addr

            # Générer les données du mandat et stocker temporairement
            mandat_data = generate_mandat_data({
                'prenom': data.get('prenom'),
                'nom': data.get('nom'),
                'nom_entreprise': data.get('nom_entreprise'),
                'siren': data.get('siren'),
                'adresse': data.get('adresse', ''),
                'tel': data.get('tel'),
                'email': data.get('email'),
                'pdl': data.get('pdl'),
                'pce': data.get('pce'),
                'puissance_kva': data.get('puissance_kva'),
                'fourn': data.get('fourn'),
                'nom_offre': data.get('nom_offre'),
                'ip': client_ip,
                'date_signature': date_signature,
            })
            doc_id = mandat_data.get('doc_id')
            mandats_temp[doc_id] = mandat_data
            mandat_drive_url = f"/mandat/{doc_id}"
            mandat_pdf_bytes = None
            mandat_filename = None

            # Ajouter les données du mandat aux données du lead
            data['mandat_signe'] = "OUI"
            data['mandat_drive_url'] = mandat_drive_url or ""
            data['ip_signature'] = client_ip
            data['date_signature_mandat'] = date_signature

        # Fusionner pour Google Sheets (inclut toutes les nouvelles colonnes)
        lead_data = {**data, **eco}

        # Sauvegarder dans Google Sheets
        saved = save_lead(lead_data)

        # Envoyer emails
        send_email_prospect(data, eco)  # Prospect sans PDF
        facture_id = data.get('facture_id')
        print(f"📤 submit-lead: facture_id extrait = {facture_id}")
        print(f"📤 submit-lead: data keys = {list(data.keys())}")
        send_alert_conseiller(data, eco, doc_id, facture_id)  # Conseiller avec PDF mandat + facture

        return jsonify({
            "success": True,
            "eco": eco,
            "infos_contrat": infos,
            "saved": saved,
            "mandat_url": mandat_drive_url
        })

    except Exception as e:
        print(f"❌ Erreur submit_lead : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/contact", methods=["POST"])
def contact_form():
    """Endpoint pour formulaire de contact générique"""
    try:
        print("📧 Réception requête /api/contact")
        data = request.get_json()

        if not data:
            print("❌ Aucune donnée JSON reçue")
            return jsonify({"success": False, "error": "Aucune donnée reçue"}), 400

        nom = data.get('nom', '')
        email = data.get('email', '')
        telephone = data.get('telephone', '')
        message = data.get('message', '')
        sujet = data.get('sujet', 'Nouveau message LILIWATT')

        print(f"📨 Envoi email pour: {nom} ({email})")
        print(f"📝 Sujet: {sujet}")

        # Envoi email à contact@liliwatt.fr
        success = send_contact_email(nom, email, telephone, message, sujet)

        if success:
            print("✅ Email envoyé avec succès")
            return jsonify({"success": True, "message": "Message envoyé avec succès"})
        else:
            print("❌ Échec envoi email")
            return jsonify({"success": False, "error": "Erreur lors de l'envoi de l'email"}), 500

    except Exception as e:
        print(f"❌ ERREUR API contact : {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500

@app.route("/api/recrutement", methods=["POST"])
def recrutement_form():
    """Endpoint pour formulaire de recrutement avec upload CV"""
    try:
        print("📧 Réception requête /api/recrutement")

        # Récupérer les données du formulaire multipart
        nom = request.form.get('nom', '')
        email = request.form.get('email', '')
        telephone = request.form.get('telephone', '')
        poste = request.form.get('poste', 'Candidature spontanée')
        message = request.form.get('message', '')

        print(f"📨 Candidature de: {nom} ({email}) pour: {poste}")

        # Récupérer le CV s'il est présent
        cv_filename = None
        cv_bytes = None
        if 'cv' in request.files:
            cv_file = request.files['cv']
            if cv_file.filename:
                cv_filename = secure_filename(cv_file.filename)
                cv_bytes = cv_file.read()
                print(f"📎 CV joint: {cv_filename} ({len(cv_bytes)} octets)")

        # Envoi email à recrutement@liliwatt.fr
        success = send_recrutement_email(nom, email, telephone, poste, message, cv_filename, cv_bytes)

        if success:
            print("✅ Email de candidature envoyé avec succès")
            return jsonify({"success": True, "message": "Candidature envoyée avec succès"})
        else:
            print("❌ Échec envoi email candidature")
            return jsonify({"success": False, "error": "Erreur lors de l'envoi de la candidature"}), 500

    except Exception as e:
        print(f"❌ ERREUR API recrutement : {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/api/contact-c2e', methods=['POST', 'OPTIONS'])
def contact_c2e():
    """Endpoint pour demandes de contact depuis le simulateur C2E"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        print("=== CONTACT C2E APPELÉ ===")
        data = request.get_json()
        print(f"Data reçue : {data}")
        print(f"GMAIL_USER : {os.environ.get('GMAIL_USER')}")

        prenom = data.get('prenom', '')
        nom    = data.get('nom', '')
        tel    = data.get('tel', '')
        email  = data.get('email', '')
        source = data.get('source', 'C2E')

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[LILIWATT C2E] Demande de contact — {prenom} {nom}'
        msg['From'] = f'LILIWATT <{GMAIL_USER}>'
        msg['To'] = 'contact@liliwatt.fr'
        msg['Reply-To'] = email

        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <div style="background:linear-gradient(135deg,#7c3aed,#a855f7);
            padding:24px;border-radius:12px 12px 0 0;text-align:center;">
            <h2 style="color:#fff;margin:0;">Nouvelle demande C2E</h2>
            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">
              {source}</p>
          </div>
          <div style="background:#f5f3ff;padding:24px;border-radius:0 0 12px 12px;">
            <table style="width:100%;font-size:15px;">
              <tr><td style="color:#6b7280;padding:6px 0;">Prénom</td>
                  <td style="font-weight:600;color:#1e1b4b;">{prenom}</td></tr>
              <tr><td style="color:#6b7280;padding:6px 0;">Nom</td>
                  <td style="font-weight:600;color:#1e1b4b;">{nom}</td></tr>
              <tr><td style="color:#6b7280;padding:6px 0;">Téléphone</td>
                  <td style="font-weight:600;color:#1e1b4b;">{tel}</td></tr>
              <tr><td style="color:#6b7280;padding:6px 0;">Email</td>
                  <td style="font-weight:600;color:#7c3aed;">{email}</td></tr>
            </table>
          </div>
        </div>"""

        msg.attach(MIMEText(html_body, 'html'))

        print("Envoi email via SMTP...")
        with smtplib.SMTP("smtp.zoho.eu", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, 'contact@liliwatt.fr', msg.as_string())

        print("Email envoyé avec succès")
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        print(f'Erreur contact_c2e : {e}')
        import traceback
        traceback.print_exc()
        response = jsonify({'success': False, 'error': str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/rgpd-demande', methods=['POST', 'OPTIONS'])
def rgpd_demande():
    """Endpoint pour demandes RGPD depuis la page rgpd.html"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        print("=== DEMANDE RGPD REÇUE ===")
        data = request.get_json()
        print(f"Data reçue : {data}")

        nom = data.get('nom', '')
        prenom = data.get('prenom', '')
        email = data.get('email', '')
        type_demande = data.get('type_demande', '')
        description = data.get('description', '')

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[LILIWATT RGPD] Demande {type_demande} — {prenom} {nom}'
        msg['From'] = f'LILIWATT <{GMAIL_USER}>'
        msg['To'] = 'dpo@liliwatt.fr'
        msg['Reply-To'] = email

        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
          <div style="background:linear-gradient(135deg,#7c3aed,#a855f7);
            padding:24px;border-radius:12px 12px 0 0;text-align:center;">
            <h2 style="color:#fff;margin:0;">Demande RGPD reçue</h2>
            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">
              Type : {type_demande}</p>
          </div>
          <div style="background:#f5f3ff;padding:24px;border-radius:0 0 12px 12px;">
            <table style="width:100%;font-size:15px;border-collapse:collapse;">
              <tr><td style="color:#6b7280;padding:8px 0;width:160px;">Prénom</td>
                <td style="font-weight:600;color:#1e1b4b;">{prenom}</td></tr>
              <tr><td style="color:#6b7280;padding:8px 0;">Nom</td>
                <td style="font-weight:600;color:#1e1b4b;">{nom}</td></tr>
              <tr><td style="color:#6b7280;padding:8px 0;">Email</td>
                <td style="color:#7c3aed;">{email}</td></tr>
              <tr><td style="color:#6b7280;padding:8px 0;">Type demande</td>
                <td style="font-weight:600;color:#1e1b4b;">{type_demande}</td></tr>
              <tr><td style="color:#6b7280;padding:8px 0;vertical-align:top;">Description</td>
                <td style="color:#1e1b4b;">{description}</td></tr>
            </table>
            <div style="margin-top:20px;padding:16px;background:#ede9fe;
              border-radius:8px;border-left:4px solid #7c3aed;">
              <p style="margin:0;font-size:13px;color:#6b7280;">
                ⚠️ Délai légal de réponse : 1 mois à compter de la réception (art. 12 RGPD)
              </p>
            </div>
          </div>
        </div>"""

        msg.attach(MIMEText(html_body, 'html'))

        print("Envoi email RGPD via SMTP...")
        with smtplib.SMTP("smtp.zoho.eu", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, 'dpo@liliwatt.fr', msg.as_string())

        print("Email RGPD envoyé avec succès")
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        print(f'Erreur rgpd_demande : {e}')
        import traceback
        traceback.print_exc()
        response = jsonify({'success': False, 'error': str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/api/c2e/simuler', methods=['POST'])
def c2e_simuler():
    """Endpoint proxy pour simulateur C2E - Certificats d'Économies d'Énergie"""
    try:
        data = request.get_json()

        # Mapping parameters to France Rénov API
        statut = data.get('statut', 'propriétaire occupant')
        personnes = int(data.get('personnes', 2))
        revenu = int(data.get('revenu', 30000))
        type_logement = data.get('type_logement', 'maison')
        code_postal = data.get('code_postal', '75001')
        age_logement = data.get('age_logement', 'au moins 15 ans')
        dpe_actuel = int(data.get('dpe_actuel', 5))

        # Build API URL with parameters
        params = {
            'vous . propriétaire . statut': 'propriétaire' if 'proprio' in statut.lower() else 'locataire',
            'ménage . personnes': personnes,
            'ménage . revenu': revenu,
            'logement . type': f"'{type_logement}'",
            'logement . commune': f"'{code_postal}'",
            'logement . propriétaire occupant': 'oui' if 'occupant' in statut.lower() else 'non',
            'logement . résidence principale propriétaire': 'oui',
            'logement . période de construction': f"'{age_logement}'",
            'DPE . actuel': dpe_actuel,
            'fields': 'eligibilite'
        }

        import urllib.parse
        query = '&'.join([f"{urllib.parse.quote(k)}={urllib.parse.quote(str(v))}"
                          for k, v in params.items()])

        api_url = f"https://mesaides.france-renov.gouv.fr/api/v1/?{query}"

        # Call external API
        import urllib.request
        import json as json_lib
        req = urllib.request.Request(
            api_url,
            headers={'Accept': 'application/json', 'User-Agent': 'LILIWATT/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json_lib.loads(resp.read())

        # Parse results
        aides = []
        if result:
            for key, value in result.items():
                if value and value != 0:
                    aides.append({
                        'nom': key.replace('.', ' ').title(),
                        'montant': value if isinstance(value, (int, float)) else None,
                        'description': 'Aide calculée selon votre situation'
                    })

        return jsonify({'success': True, 'aides': aides})

    except Exception as e:
        print(f"Erreur API C2E : {e}")
        return jsonify({'success': False, 'aides': []}), 200

@app.route("/admin/leads")
def admin_leads():
    """Page admin simple pour voir les leads"""
    try:
        sheet = get_sheet()
        rows = sheet.get_all_records()
        return render_template("admin.html", leads=rows)
    except Exception as e:
        return f"Erreur : {e}", 500

# ──── ROUTE BLOG NEWSAPI ─────────────────────────────────────
@app.route('/blog')
@cache.cached(timeout=7200)  # Cache 2 heures — news servies instantanément
def blog():
    """Page blog dynamique avec articles NewsAPI"""
    try:
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': '(énergie OR électricité OR gaz) AND (France OR prix OR tarif OR facture)',
            'language': 'fr',
            'sortBy': 'publishedAt',
            'pageSize': 12,
            'apiKey': os.getenv('NEWS_API_KEY'),
            'excludeDomains': 'remove.bg'  # Exclure les domaines spam
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        articles = data.get('articles', [])

        # Mots-clés à exclure (hors sujet énergie)
        exclude_keywords = [
            'sport', 'football', 'tennis', 'rugby',
            'cinéma', 'film', 'série', 'musique',
            'crypto', 'bitcoin', 'nft',
            'people', 'célébrité', 'star',
            'jeu vidéo', 'gaming', 'esport',
            'météo', 'horoscope',
            'recette', 'cuisine',
            'mode', 'beauté', 'fashion'
        ]

        # Filtrer les articles sans image, incomplets et hors sujet
        filtered_articles = []
        for a in articles:
            # Vérifier présence des champs essentiels
            if not (a.get('urlToImage') and a.get('title') and a.get('description')):
                continue

            # Vérifier si l'article contient des mots-clés hors sujet
            title_lower = a.get('title', '').lower()
            desc_lower = a.get('description', '').lower()

            is_off_topic = any(
                keyword in title_lower or keyword in desc_lower
                for keyword in exclude_keywords
            )

            if not is_off_topic:
                filtered_articles.append(a)

        return render_template('blog.html', articles=filtered_articles)

    except Exception as e:
        print(f"❌ Erreur NewsAPI : {e}")
        # En cas d'erreur, afficher une page avec message
        return render_template('blog.html', articles=[], error=str(e))

# ──── ROUTE BLOG STATIQUE (FALLBACK) ─────────────────────────
@app.route('/blog.html')
def blog_static():
    """Redirection vers /blog"""
    return redirect('/blog', code=301)

# ──── SEO : SITEMAP.XML ──────────────────────────────────────
@app.route('/sitemap.xml')
def sitemap():
    """Génère le sitemap.xml pour Google"""
    pages = [
        ('/', '2026-03-16', 'weekly', '1.0'),
        ('/blog', '2026-03-16', 'daily', '0.9'),
        ('/extracteur', '2026-03-16', 'monthly', '0.8'),
        ('/offres.html', '2026-03-16', 'monthly', '0.8'),
        ('/apropos.html', '2026-03-16', 'monthly', '0.7'),
        ('/contact.html', '2026-03-16', 'monthly', '0.7'),
        ('/recrutement.html', '2026-03-16', 'monthly', '0.6'),
    ]

    xml = render_template('sitemap.xml', pages=pages)
    return xml, 200, {'Content-Type': 'application/xml'}

# ──── SEO : ROBOTS.TXT ───────────────────────────────────────
@app.route('/robots.txt')
def robots():
    """Génère robots.txt pour les crawlers"""
    return """User-agent: *
Allow: /

# Sitemap
Sitemap: https://liliwatt.fr/sitemap.xml

# Crawl-delay pour être sympa avec les serveurs
Crawl-delay: 1
""", 200, {'Content-Type': 'text/plain'}

# ──── CHATBOT LILI - IA CLAUDE ──────────────────────────────────────────────

LILI_SYSTEM_PROMPT = """Tu es LILI, conseillère énergie LILIWATT.
Réponds TOUJOURS en 1-2 phrases maximum, jamais plus.
Pose les questions UNE PAR UNE, jamais plusieurs à la fois.
Sois chaleureuse et directe.

IMPORTANT — DEUX PARCOURS DISTINCTS :

PARCOURS 1 — ANALYSE FACTURE ÉNERGIE :
Si la personne veut analyser sa facture ou réduire ses coûts énergie,
pose ces questions UNE PAR UNE avec OPTIONS :
1. "Vous consommez de l'électricité, du gaz ou les deux ?
[OPTIONS: Électricité|Gaz|Les deux]"
2. "Quel est votre fournisseur actuel ?
[OPTIONS: EDF|Engie|TotalEnergies|Vattenfall|Je ne sais pas]"
3. "Quel est votre budget énergie mensuel ?
[OPTIONS: Moins de 200€|200-500€|500€-1000€|Plus de 1000€]"
Puis conclure : "Pour connaître vos économies exactes, analysez votre facture gratuitement en 30 secondes 👇
[OPTIONS: Analyser ma facture sur liliwatt.fr/extracteur]"
→ Ce bouton ouvre : window.open('/extracteur', '_blank')

PARCOURS 2 — AIDES RÉNOVATION ÉNERGÉTIQUE :
Si la personne parle de rénovation, travaux, isolation, chauffage,
MaPrimeRénov, CEE, aides, subventions,
pose ces questions UNE PAR UNE avec OPTIONS :
1. "Quel type de travaux envisagez-vous ?
[OPTIONS: Isolation|Chauffage/Pompe à chaleur|Fenêtres|Eau chaude sanitaire|Ventilation|Plusieurs types]"
2. "Êtes-vous propriétaire ou locataire ?
[OPTIONS: Propriétaire occupant|Propriétaire bailleur|Locataire|Copropriété]"
3. "Quel est votre code postal ?
[OPTIONS: Je le saisis dans le formulaire]"
Puis conclure avec : "Découvrez toutes vos aides en quelques clics !
Simulez gratuitement vos aides MaPrimeRénov, CEE et ANAH 👇
[OPTIONS: Simuler mes aides sur liliwatt.fr/c2e.html]"
→ Ce bouton ouvre : window.open('/c2e.html', '_blank')

Quand tu poses une question à choix, termine TOUJOURS
ta réponse par une ligne spéciale au format :
[OPTIONS: option1|option2|option3|option4]

Exemples :
"Quel est votre secteur d'activité ?
[OPTIONS: Restaurant|Bureau|Commerce|Boulangerie|Hôtel|Autre]"

"Quel est votre fournisseur actuel ?
[OPTIONS: EDF|Engie|TotalEnergies|Vattenfall|Je ne sais pas]"

"Quel est votre budget énergie mensuel ?
[OPTIONS: Moins de 200€|200-500€|500€-1000€|Plus de 1000€]"

Si la personne répond librement sans cliquer →
continue la conversation normalement sans format OPTIONS.

LILIWATT : courtage énergie B2B/B2C, analyse gratuite,
économies moyennes 18%, sans coupure.
Aides rénovation : MaPrimeRénov, CEE, Éco-PTZ, ANAH.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉQUIPE LILIWATT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Kévin Moreau : Président
- Johan Mallet : Directeur Commercial
- Emmanuel Leray : Chargé RH

Contact : 01 84 16 08 56
Extracteur : liliwatt.fr/extracteur"""

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Route API pour le chatbot LILI - IA Claude"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'ok': True})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        print(f"=== CHAT LILI APPELÉ ===")
        data = request.get_json()
        messages = data.get('messages', [])

        # Debug message
        if messages and len(messages) > 0:
            last_msg = messages[-1]
            if last_msg.get('role') == 'user':
                print(f"Message reçu : {last_msg.get('content', '')[:100]}")

        # Debug: vérifier la présence de la clé API
        api_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"Clé API présente : {bool(api_key)}")
        print(f"Longueur clé : {len(api_key) if api_key else 0}")
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY non définie dans les variables d'environnement")

        # Limiter l'historique à 10 messages
        if len(messages) > 10:
            messages = messages[-10:]

        print(f"Nombre de messages dans l'historique : {len(messages)}")
        print(f"Modèle utilisé : claude-haiku-4-5-20251001")

        client = anthropic.Anthropic(api_key=api_key)

        response_api = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            system=LILI_SYSTEM_PROMPT,
            messages=messages
        )

        reply = response_api.content[0].text
        print(f"Réponse générée : {reply[:100]}...")

        # Détecter un numéro de téléphone dans le dernier message utilisateur
        last_user_msg = ""
        for m in reversed(messages):
            if m.get('role') == 'user':
                last_user_msg = m.get('content', '')
                break

        phone_pattern = re.compile(r'(?:(?:\+33|0033|0)[1-9])(?:[.\-\s]?\d{2}){4}')
        phone_found = phone_pattern.search(last_user_msg)

        if phone_found:
            try:
                phone = phone_found.group(0)
                print(f"📞 Numéro détecté : {phone}")

                # Extraire contexte conversation
                context = ""
                for m in messages[-6:]:
                    role = "Visiteur" if m.get('role') == 'user' else "LILI"
                    msg_content = m.get('content', '')[:100]
                    context += f"{role} : {msg_content}\n"

                msg_email = MIMEMultipart('alternative')
                msg_email['Subject'] = f'🔔 LILI — Nouveau lead téléphone : {phone}'
                msg_email['From'] = f'LILIWATT <{os.environ.get("GMAIL_USER")}>'
                msg_email['To'] = 'contact@liliwatt.fr'

                html_body = f'''<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<div style="background:linear-gradient(135deg,#7c3aed,#a855f7);padding:24px;border-radius:12px 12px 0 0;text-align:center;">
<h2 style="color:#fff;margin:0;">📞 Nouveau lead LILI</h2>
<p style="color:rgba(255,255,255,0.85);margin:8px 0 0;">Un visiteur a partagé son numéro dans le chat</p>
</div>
<div style="background:#f5f3ff;padding:24px;border-radius:0 0 12px 12px;">
<table style="width:100%;font-size:15px;border-collapse:collapse;">
<tr><td style="color:#6b7280;padding:8px 0;width:140px;">📞 Téléphone</td>
<td style="font-weight:700;color:#7c3aed;font-size:18px;">{phone}</td></tr>
</table>
<div style="margin-top:20px;padding:16px;background:white;border-radius:8px;border-left:4px solid #7c3aed;">
<p style="margin:0 0 8px;font-weight:700;color:#1e1b4b;">Contexte de la conversation :</p>
<pre style="margin:0;font-size:13px;color:#374151;white-space:pre-wrap;">{context}</pre>
</div>
<div style="margin-top:16px;text-align:center;">
<a href="tel:{phone}" style="background:linear-gradient(135deg,#7c3aed,#a855f7);color:white;padding:12px 28px;border-radius:50px;text-decoration:none;font-weight:700;font-size:15px;">📞 Appeler maintenant</a>
</div></div></div>'''

                msg_email.attach(MIMEText(html_body, 'html'))

                with smtplib.SMTP('smtp.zoho.eu', 587) as s:
                    s.starttls()
                    s.login(os.environ.get('GMAIL_USER'), os.environ.get('GMAIL_PASSWORD'))
                    s.sendmail(os.environ.get('GMAIL_USER'), 'contact@liliwatt.fr', msg_email.as_string())
                print(f"✅ Email lead envoyé pour {phone}")
            except Exception as email_err:
                print(f"⚠️ Erreur envoi email lead : {email_err}")

        print(f"=== CHAT LILI TERMINÉ AVEC SUCCÈS ===")

        response = jsonify({
            'success': True,
            'reply': reply
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({
            'success': False,
            'reply': "Désolée, je rencontre un problème technique. Appelez-nous au 01 84 16 08 56 😊"
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

# ──── ROUTE 404 ──────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404 - Page non trouvée</h1><p>Cette page n'existe pas.</p><a href='/'>Retour à l'accueil</a>", 404


@app.route('/mandat/<doc_id>')
def afficher_mandat(doc_id):
    """Affiche le mandat en HTML pour impression PDF"""
    # Récupérer les données depuis la session ou un fichier temp
    data = mandats_temp.get(doc_id, {})
    if not data:
        return "Mandat non trouvé", 404
    return render_template('mandat_template.html', **data)

if __name__ == '__main__':
    print("🚀 LILIWATT Website lancé sur http://localhost:8080")
    print("📰 Blog NewsAPI disponible sur http://localhost:8080/blog")
    app.run(debug=True, port=8080, host='127.0.0.1')
