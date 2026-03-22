#!/usr/bin/env python3
"""
Générateur de mandat de courtage LILIWATT en PDF
Version 2.0 - Avec gestion automatique des débordements de page
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime
import io
import os

# Chemin de base absolu pour les assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)  # liliwatt-analyseur/


# ═══════════════════════════════════════════════════════════
# CONSTANTES COULEURS LILIWATT
# ═══════════════════════════════════════════════════════════
VIOLET = colors.HexColor('#7C3AED')
VIOLET_L = colors.HexColor('#A78BFA')
FUCHSIA = colors.HexColor('#D946EF')
NOIR = colors.HexColor('#06060F')
GRIS_CLAIR = colors.HexColor('#F5F3FF')
GRIS_TEXTE = colors.HexColor('#6B7280')
VERT_SIGNATURE = colors.HexColor('#34D399')
BLANC = colors.white


# ═══════════════════════════════════════════════════════════
# CONSTANTES GESTION DE PAGE (CRITIQUES)
# ═══════════════════════════════════════════════════════════
PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.27 x 841.89 points
MARGIN_BOTTOM = 80  # MINIMUM 80 POINTS EN BAS DE PAGE
MARGIN_TOP = 100    # Espace réservé en haut après header
HEADER_HEIGHT = 60 * mm  # ~170 points
FOOTER_START = 25 * mm   # Position Y du footer (~70 points)


# ═══════════════════════════════════════════════════════════
# FONCTION CRITIQUE : GESTION DÉBORDEMENT PAGE
# ═══════════════════════════════════════════════════════════
def check_page_break(c, y, needed_height, width):
    """
    Vérifie si on a assez d'espace pour dessiner un bloc.
    Si y - needed_height < MARGIN_BOTTOM → nouvelle page + header + footer

    Args:
        c: canvas ReportLab
        y: position Y actuelle
        needed_height: hauteur nécessaire en points
        width: largeur de page

    Returns:
        y: nouvelle position Y (soit inchangée, soit en haut de nouvelle page)
    """
    if y - needed_height < MARGIN_BOTTOM:
        # Dessiner footer sur page actuelle avant de tourner
        draw_footer(c, width)

        # Nouvelle page
        c.showPage()

        # Dessiner header sur nouvelle page
        draw_header(c, width)

        # Réinitialiser Y en haut (sous le header)
        y = PAGE_HEIGHT - HEADER_HEIGHT - 20 * mm

    return y


# ═══════════════════════════════════════════════════════════
# EN-TÊTE DE PAGE (AVEC LOGO)
# ═══════════════════════════════════════════════════════════
def draw_header(c, width, date_signature=None):
    """
    Dessine l'en-tête violet avec logo LILIWATT

    Si date_signature est fournie : header complet (page 1)
    Sinon : header compact pour pages suivantes (60 points max)

    Args:
        c: canvas
        width: largeur page
        date_signature: date de signature (optionnel, pour première page)
    """
    height = PAGE_HEIGHT

    # HEADER COMPACT pour pages 2+ (sans date_signature)
    if not date_signature:
        # Bandeau violet compact (40mm au lieu de 60mm)
        header_compact_height = 40 * mm
        c.setFillColor(VIOLET)
        c.rect(0, height - header_compact_height, width, header_compact_height, fill=1, stroke=0)

        # Logo (plus petit)
        logo_path = os.path.join(PARENT_DIR, 'assets', 'images', 'logo-sans-fond.png')
        try:
            if os.path.exists(logo_path):
                logo = ImageReader(logo_path)
                c.drawImage(logo, 20*mm, height - 25*mm,
                           width=40, height=30,
                           mask='auto', preserveAspectRatio=True)
            else:
                c.setFillColor(BLANC)
                c.setFont("Helvetica-Bold", 16)
                c.drawString(20*mm, height - 20*mm, "LILIWATT")
                print(f"⚠️  Logo introuvable : {logo_path}")
        except Exception as e:
            c.setFillColor(BLANC)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(20*mm, height - 20*mm, "LILIWATT")
            print(f"⚠️  Erreur chargement logo: {e}")

        # Titre à droite
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 20*mm, height - 20*mm, "MANDAT DE COURTAGE")

        # Ligne fuchsia
        c.setStrokeColor(FUCHSIA)
        c.setLineWidth(1.5)
        c.line(0, height - header_compact_height - 1*mm, width, height - header_compact_height - 1*mm)
        return

    # HEADER COMPLET pour page 1 (avec date_signature)
    # Bandeau violet
    c.setFillColor(VIOLET)
    c.rect(0, height - HEADER_HEIGHT, width, HEADER_HEIGHT, fill=1, stroke=0)

    # Charger et dessiner le logo (avec chemin absolu corrigé)
    logo_path = os.path.join(PARENT_DIR, 'assets', 'images', 'logo-sans-fond.png')

    try:
        if os.path.exists(logo_path):
            # Logo PNG avec fond transparent
            logo = ImageReader(logo_path)
            logo_height = 70  # pixels de hauteur (augmenté à 70 points minimum)
            # Ratio pour garder proportions (approximatif)
            logo_width = logo_height * 3  # ajuster selon ratio réel
            c.drawImage(logo, 20*mm, height - 30*mm,
                       width=logo_width, height=logo_height,
                       mask='auto', preserveAspectRatio=True)
        else:
            # Fallback: texte si logo introuvable
            c.setFillColor(BLANC)
            c.setFont("Helvetica-Bold", 28)
            c.drawString(20*mm, height - 25*mm, "LILIWATT")
            print(f"⚠️  Logo introuvable : {logo_path}")
    except Exception as e:
        # Fallback en cas d'erreur de chargement
        print(f"⚠️  Erreur chargement logo: {e}")
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 28)
        c.drawString(20*mm, height - 25*mm, "LILIWATT")

    # Point fuchsia décoratif
    c.setFillColor(FUCHSIA)
    c.circle(18*mm, height - 22*mm, 3*mm, fill=1, stroke=0)

    # Sous-titre
    c.setFillColor(VIOLET_L)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, height - 40*mm, "COURTAGE ÉNERGIE  ·  B2B & B2C")

    # Titre mandat à droite (seulement sur première page)
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 20*mm, height - 22*mm, "MANDAT DE COURTAGE")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 20*mm, height - 30*mm, f"Signé le {date_signature}")

    # Ligne décorative fuchsia
    c.setStrokeColor(FUCHSIA)
    c.setLineWidth(2)
    c.line(0, height - HEADER_HEIGHT - 2*mm, width, height - HEADER_HEIGHT - 2*mm)


# ═══════════════════════════════════════════════════════════
# PIED DE PAGE (FIXE À y=40 POINTS)
# ═══════════════════════════════════════════════════════════
def draw_footer(c, width):
    """
    Dessine le pied de page à position fixe y=40 points (~14mm)
    """
    footer_y = 40  # Position fixe en points

    # Ligne de séparation
    c.setStrokeColor(VIOLET)
    c.setLineWidth(0.5)
    c.line(15*mm, footer_y + 25, width - 15*mm, footer_y + 25)

    # Nom LILIWATT
    c.setFillColor(VIOLET)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width/2, footer_y + 18, "LILIWATT")

    # Coordonnées
    c.setFillColor(GRIS_TEXTE)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(width/2, footer_y + 10,
                       "LILISTRAT STRATÉGIE SAS  ·  contact@liliwatt.fr  ·  www.liliwatt.fr")

    # Numéro de document
    c.drawCentredString(width/2, footer_y + 2,
                       f"Document : LW-{datetime.now().strftime('%Y%m%d%H%M%S')}")


# ═══════════════════════════════════════════════════════════
# FONCTIONS HELPER POUR SECTIONS
# ═══════════════════════════════════════════════════════════
def section_title(c, text, y_pos, width):
    """
    Dessine un titre de section avec fond violet
    Retourne la nouvelle position Y
    """
    c.setFillColor(VIOLET)
    c.rect(15*mm, y_pos - 2*mm, width - 30*mm, 8*mm, fill=1, stroke=0)
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y_pos, text)
    return y_pos - 12*mm


def field_line(c, label, value, y_pos, label_x=20, value_x=75):
    """
    Dessine une ligne label: valeur
    Retourne la nouvelle position Y
    """
    c.setFillColor(GRIS_TEXTE)
    c.setFont("Helvetica", 9)
    c.drawString(label_x*mm, y_pos, label)
    c.setFillColor(NOIR)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(value_x*mm, y_pos, str(value) if value else "—")
    return y_pos - 6*mm


# ═══════════════════════════════════════════════════════════
# FONCTION PRINCIPALE : GÉNÉRATION PDF
# ═══════════════════════════════════════════════════════════
def generate_mandat_pdf(data: dict) -> bytes:
    """
    Génère le PDF mandat et retourne les bytes.

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

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width = PAGE_WIDTH

    # ═══════════════════════════════════════════════════════
    # PAGE 1 : EN-TÊTE AVEC DATE
    # ═══════════════════════════════════════════════════════
    draw_header(c, width, date_signature=data.get('date_signature', ''))

    # Position de départ sous l'en-tête
    y = PAGE_HEIGHT - HEADER_HEIGHT - 20*mm


    # ═══════════════════════════════════════════════════════
    # SECTION 1 : LE MANDANT (CLIENT)
    # ═══════════════════════════════════════════════════════
    # Vérifier si on a assez de place (estimation: 70mm de hauteur)
    y = check_page_break(c, y, 70*mm, width)

    y = section_title(c, "LE MANDANT (CLIENT)", y, width)

    nom_complet = f"{data.get('prenom', '')} {data.get('nom', '')}".strip()
    if data.get('nom_entreprise'):
        y = field_line(c, "Raison sociale :", data['nom_entreprise'].upper(), y)
        y = field_line(c, "Représentant :", nom_complet, y)
    else:
        y = field_line(c, "Nom / Prénom :", nom_complet, y)

    if data.get('siren'):
        y = field_line(c, "SIREN :", data['siren'], y)

    y = field_line(c, "Adresse :", data.get('adresse', ''), y)
    y = field_line(c, "Téléphone :", data.get('tel', ''), y)
    y = field_line(c, "Email :", data.get('email', ''), y)

    y -= 8*mm  # Espacement entre sections


    # ═══════════════════════════════════════════════════════
    # SECTION 2 : SITE DE CONSOMMATION
    # ═══════════════════════════════════════════════════════
    y = check_page_break(c, y, 60*mm, width)

    y = section_title(c, "SITE DE CONSOMMATION", y, width)

    # PDL et PCE TOUJOURS affichés (obligatoires)
    pdl_value = data.get('pdl') if data.get('pdl') else "À compléter par le conseiller"
    y = field_line(c, "PDL (Électricité) :", pdl_value, y)

    pce_value = data.get('pce') if data.get('pce') else "À compléter par le conseiller"
    y = field_line(c, "PCE (Gaz) :", pce_value, y)

    if data.get('puissance_kva'):
        # Éviter doublon "kVA kVA" si la valeur contient déjà "kVA"
        puissance_value = str(data['puissance_kva'])
        if 'kva' not in puissance_value.lower():
            puissance_value = f"{puissance_value} kVA"
        y = field_line(c, "Puissance souscrite :", puissance_value, y)

    y = field_line(c, "Fournisseur actuel :", data.get('fourn', '—'), y)
    if data.get('nom_offre'):
        y = field_line(c, "Offre actuelle :", data['nom_offre'], y)

    y -= 8*mm


    # ═══════════════════════════════════════════════════════
    # SECTION 3 : LE MANDATAIRE
    # ═══════════════════════════════════════════════════════
    y = check_page_break(c, y, 50*mm, width)

    y = section_title(c, "LE MANDATAIRE", y, width)
    y = field_line(c, "Société :", "LILISTRAT STRATÉGIE SAS", y)
    y = field_line(c, "Marque commerciale :", "LILIWATT", y)
    y = field_line(c, "Email :", "contact@liliwatt.fr", y)
    y = field_line(c, "Site :", "www.liliwatt.fr", y)

    y -= 8*mm


    # ═══════════════════════════════════════════════════════
    # SECTION 4 : OBJET DU MANDAT
    # ═══════════════════════════════════════════════════════
    y = check_page_break(c, y, 65*mm, width)

    y = section_title(c, "OBJET DU MANDAT", y, width)

    objet_text = "Le Mandant confie à LILIWATT un mandat non exclusif de courtage en énergie afin de :"
    c.setFillColor(NOIR)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, y, objet_text)
    y -= 7*mm

    items = [
        "Rechercher les meilleures offres d'énergie du marché",
        "Négocier les tarifs auprès des fournisseurs partenaires",
        "Accéder aux données de consommation Enedis / GRDF",
        "Transmettre les données aux fournisseurs dans le cadre d'une demande d'offre",
        "Accompagner le changement de fournisseur le cas échéant",
    ]
    for item in items:
        c.setFillColor(FUCHSIA)
        c.circle(23*mm, y + 1.5*mm, 1*mm, fill=1, stroke=0)
        c.setFillColor(NOIR)
        c.setFont("Helvetica", 9)
        c.drawString(26*mm, y, item)
        y -= 5.5*mm

    y -= 5*mm


    # ═══════════════════════════════════════════════════════
    # SECTION 5 : CONDITIONS
    # ═══════════════════════════════════════════════════════
    y = check_page_break(c, y, 70*mm, width)

    y = section_title(c, "CONDITIONS", y, width)

    conditions = [
        ("Durée :", "12 mois à compter de la date de signature, renouvelable par tacite reconduction"),
        ("Rémunération :", "LILIWATT est rémunéré directement par les fournisseurs. Aucun frais au Mandant."),
        ("Résiliation :", "Résiliable à tout moment par email à contact@liliwatt.fr"),
        ("Exclusivité :", "Mandat non exclusif — le Mandant reste libre de contracter directement"),
    ]

    for label, val in conditions:
        # Vérifier si on a assez de place pour cette condition (max 3 lignes = 18mm)
        y = check_page_break(c, y, 18*mm, width)

        c.setFillColor(GRIS_TEXTE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20*mm, y, label)
        c.setFillColor(NOIR)
        c.setFont("Helvetica", 8.5)

        # Wrap le texte long
        max_width = 130*mm
        if c.stringWidth(val, "Helvetica", 8.5) > max_width:
            words = val.split()
            line = ""
            for word in words:
                if c.stringWidth(line + word, "Helvetica", 8.5) < max_width:
                    line += word + " "
                else:
                    c.drawString(55*mm, y, line.strip())
                    y -= 4.5*mm
                    line = word + " "
            if line:
                c.drawString(55*mm, y, line.strip())
        else:
            c.drawString(55*mm, y, val)
        y -= 6*mm

    y -= 5*mm


    # ═══════════════════════════════════════════════════════
    # SECTION 6 : DONNÉES PERSONNELLES (RGPD)
    # ═══════════════════════════════════════════════════════
    y = check_page_break(c, y, 50*mm, width)

    y = section_title(c, "DONNÉES PERSONNELLES (RGPD)", y, width)

    rgpd_text = (
        "Conformément au RGPD (UE 2016/679), les données collectées sont utilisées uniquement dans le cadre "
        "de ce mandat. Elles ne sont jamais revendues. Droit d'accès et suppression : contact@liliwatt.fr"
    )
    c.setFillColor(NOIR)
    c.setFont("Helvetica", 8.5)

    # Wrap text
    words = rgpd_text.split()
    line = ""
    max_width = 165*mm
    for word in words:
        if c.stringWidth(line + word, "Helvetica", 8.5) < max_width:
            line += word + " "
        else:
            c.drawString(20*mm, y, line.strip())
            y -= 5*mm
            line = word + " "
    if line:
        c.drawString(20*mm, y, line.strip())
        y -= 5*mm

    y -= 8*mm


    # ═══════════════════════════════════════════════════════
    # SECTION 7 : SIGNATURE ÉLECTRONIQUE (AVEC ENCADRÉ VERT)
    # ═══════════════════════════════════════════════════════
    # Calculer la hauteur exacte nécessaire pour le bloc signature
    # Titre (10pt) : 2mm
    # Checkmark : 9mm
    # Info signataire : 16mm
    # Note légale ligne 1 : 23mm
    # Note légale ligne 2 : 28mm
    # Padding bas : 33mm
    # Total : ~38mm de hauteur nécessaire
    signature_box_height = 38*mm

    y = check_page_break(c, y, signature_box_height + 5*mm, width)

    # Position de départ du rectangle (y_start est en haut)
    box_y_start = y
    box_y_bottom = y - signature_box_height

    # Fond gris clair avec bordure violette
    c.setFillColor(GRIS_CLAIR)
    c.rect(15*mm, box_y_bottom, width - 30*mm, signature_box_height, fill=1, stroke=0)
    c.setStrokeColor(VIOLET)
    c.setLineWidth(0.5)
    c.rect(15*mm, box_y_bottom, width - 30*mm, signature_box_height, fill=0, stroke=1)

    # Titre
    c.setFillColor(VIOLET)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y - 6*mm, "SIGNATURE ÉLECTRONIQUE")

    # Checkmark vert + date
    c.setFillColor(VERT_SIGNATURE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20*mm, y - 13*mm, f"✓  Accepté en ligne le {data.get('date_signature', '')}")

    # Informations signataire
    c.setFillColor(GRIS_TEXTE)
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, y - 20*mm,
                f"Par : {nom_complet}  |  Email : {data.get('email', '')}  |  IP : {data.get('ip', 'xxx.xxx.xxx.xxx')}")

    # Note légale (sur 2 lignes explicites pour être sûr que ça rentre)
    c.setFillColor(GRIS_TEXTE)
    c.setFont("Helvetica", 7.5)
    c.drawString(20*mm, y - 27*mm,
                "La case cochée par le signataire vaut consentement au sens de l'article 7 du RGPD")
    c.drawString(20*mm, y - 33*mm,
                "et constitue une preuve de signature électronique.")


    # ═══════════════════════════════════════════════════════
    # PIED DE PAGE FINAL
    # ═══════════════════════════════════════════════════════
    draw_footer(c, width)

    # Finaliser le PDF
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
