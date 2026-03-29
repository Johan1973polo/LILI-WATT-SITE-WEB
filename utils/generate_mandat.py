#!/usr/bin/env python3
"""
Générateur de mandat de courtage LILIWATT en PDF
Version 3.1 - xhtml2pdf (compatible Render sans dépendances système)
"""

import io
import uuid
from datetime import datetime
from flask import render_template
from xhtml2pdf import pisa


def generate_mandat_pdf(data: dict) -> bytes:
    """
    Génère le PDF mandat via xhtml2pdf + template HTML Jinja2.

    xhtml2pdf est une bibliothèque Python pure sans dépendances système,
    contrairement à WeasyPrint qui nécessite Cairo/Pango.

    Args:
        data (dict): Dictionnaire contenant les informations du prospect
            - prenom: str
            - nom: str
            - nom_entreprise: str ou None
            - siren: str ou None
            - adresse: str
            - tel: str
            - email: str
            - pdl: str ou None
            - pce: str ou None
            - puissance_kva: str ou None
            - fourn: str
            - nom_offre: str ou None
            - ip: str
            - date_signature: str (JJ/MM/AAAA HH:MM)

    Returns:
        bytes: PDF en bytes
    """

    # Construire le nom complet
    prenom = data.get('prenom', '')
    nom = data.get('nom', '')
    nom_complet = f"{prenom} {nom}".strip()

    # Valeurs avec fallback
    adresse = data.get('adresse', '')
    pdl = data.get('pdl', '')
    pce = data.get('pce', '')

    # Contexte pour le template Jinja2
    context = {
        'nom_prenom': nom_complet or 'Non renseigné',
        'email': data.get('email', 'Non renseigné'),
        'telephone': data.get('tel', 'Non renseigné'),
        'adresse': adresse if adresse else 'Non renseignée',
        'adresse_class': '' if adresse else 'empty',
        'pdl': pdl if pdl else 'Non renseigné',
        'pdl_class': '' if pdl else 'empty',
        'pce': pce if pce else 'Non renseigné',
        'pce_class': '' if pce else 'empty',
        'fournisseur': data.get('fourn', 'Non renseigné'),
        'date_signature': data.get('date_signature',
            datetime.now().strftime('%d/%m/%Y à %H:%M')),
        'ip': data.get('ip', 'Non renseignée'),
        'doc_id': str(uuid.uuid4())[:8].upper(),
    }

    # Rendre le template HTML
    html_content = render_template('mandat_template.html', **context)

    # Générer le PDF avec xhtml2pdf
    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)

    if pisa_status.err:
        print(f"⚠️  Erreur génération PDF xhtml2pdf: {pisa_status.err}")

    buffer.seek(0)
    return buffer.read()
