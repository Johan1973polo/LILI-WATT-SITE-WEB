# Code de l'analyseur de factures intégré
# Ce fichier contient toutes les fonctions et variables de configuration

from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import json
import anthropic
from PIL import Image
import io
import base64
from pdf2image import convert_from_bytes
from werkzeug.utils import secure_filename
from utils.generate_mandat import generate_mandat_pdf

# Configuration
GOOGLE_SHEET_ID      = os.getenv("GOOGLE_SHEET_ID", "VOTRE_SHEET_ID_ICI")
GOOGLE_CREDS_FILE    = os.getenv("GOOGLE_CREDS_FILE", "liliwatt-26d5c1b213d4.json")
GMAIL_USER           = os.getenv("GMAIL_USER", "contact@liliwatt.fr")
GMAIL_APP_PASSWORD   = os.getenv("GMAIL_APP_PASSWORD", "VOTRE_APP_PASSWORD")
CONSEILLER_EMAIL     = os.getenv("CONSEILLER_EMAIL", "johan@liliwatt.fr")
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "")

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'heic'}
