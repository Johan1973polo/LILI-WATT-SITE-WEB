import uuid
from datetime import datetime
from flask import render_template


def generate_mandat_data(data: dict) -> dict:
    """Prépare les données du mandat pour le template"""
    prenom = data.get('prenom', '')
    nom = data.get('nom', '')
    nom_complet = f"{prenom} {nom}".strip()
    adresse = data.get('adresse', '')
    pdl = data.get('pdl', '')
    pce = data.get('pce', '')

    return {
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


def generate_mandat_pdf(data: dict) -> bytes:
    """Compatibilité — retourne bytes vides, le PDF se fait côté client"""
    return b''
