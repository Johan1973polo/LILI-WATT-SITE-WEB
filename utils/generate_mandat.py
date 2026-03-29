#!/usr/bin/env python3
"""
Générateur de mandat de courtage LILIWATT en PDF
Version 3.0 - WeasyPrint + Template HTML
"""

import io
import uuid
from datetime import datetime
from flask import render_template
from weasyprint import HTML


def generate_mandat_pdf(data: dict) -> bytes:
    """
    Génère le PDF mandat via WeasyPrint + template HTML Jinja2.

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

    # Générer le PDF avec WeasyPrint
    pdf_bytes = HTML(string=html_content).write_pdf()

    return pdf_bytes
