#!/usr/bin/env python3
"""
Générateur de mandat de courtage LILIWATT en PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from datetime import datetime
import io


# COULEURS LILIWATT
VIOLET = colors.HexColor('#7C3AED')
VIOLET_L = colors.HexColor('#A78BFA')
FUCHSIA = colors.HexColor('#D946EF')
NOIR = colors.HexColor('#06060F')
GRIS_CLAIR = colors.HexColor('#F5F3FF')
GRIS_TEXTE = colors.HexColor('#6B7280')
BLANC = colors.white


def draw_footer(canvas, width):
    """Dessine le pied de page à position fixe"""
    canvas.setStrokeColor(VIOLET)
    canvas.setLineWidth(0.5)
    canvas.line(15*mm, 25*mm, width - 15*mm, 25*mm)

    canvas.setFillColor(VIOLET)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawCentredString(width/2, 18*mm, "LILIWATT")

    canvas.setFillColor(GRIS_TEXTE)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(width/2, 12*mm, "LILISTRAT STRATÉGIE SAS  ·  contact@liliwatt.fr  ·  www.liliwatt.fr")
    canvas.drawCentredString(width/2, 6*mm, f"Numéro de document : LW-{datetime.now().strftime('%Y%m%d%H%M%S')}")


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
    width, height = A4

    # ── BANDEAU EN-TÊTE VIOLET ──────────────────────────
    c.setFillColor(VIOLET)
    c.rect(0, height - 60*mm, width, 60*mm, fill=1, stroke=0)

    # Logo texte LILIWATT
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(20*mm, height - 25*mm, "LILIWATT")

    # Point fuchsia décoratif
    c.setFillColor(FUCHSIA)
    c.circle(18*mm, height - 22*mm, 3*mm, fill=1, stroke=0)

    # Sous-titre
    c.setFillColor(VIOLET_L)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, height - 33*mm, "COURTAGE ÉNERGIE  ·  B2B & B2C")

    # Titre mandat à droite
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 20*mm, height - 22*mm, "MANDAT DE COURTAGE")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 20*mm, height - 30*mm, f"Signé le {data.get('date_signature', '')}")

    # Ligne décorative fuchsia
    c.setStrokeColor(FUCHSIA)
    c.setLineWidth(2)
    c.line(0, height - 62*mm, width, height - 62*mm)

    # ── FONCTIONS HELPER ────────────────────────────────
    def section_title(canvas, text, y_pos):
        """Dessine un titre de section avec fond violet"""
        canvas.setFillColor(VIOLET)
        canvas.rect(15*mm, y_pos - 2*mm, width - 30*mm, 8*mm, fill=1, stroke=0)
        canvas.setFillColor(BLANC)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(20*mm, y_pos, text)
        return y_pos - 12*mm

    def field_line(canvas, label, value, y_pos, label_x=20, value_x=75):
        """Dessine une ligne label: valeur"""
        canvas.setFillColor(GRIS_TEXTE)
        canvas.setFont("Helvetica", 9)
        canvas.drawString(label_x*mm, y_pos, label)
        canvas.setFillColor(NOIR)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(value_x*mm, y_pos, str(value) if value else "—")
        return y_pos - 6*mm

    # ── SECTION : MANDANT ───────────────────────────────
    y = height - 80*mm
    y = section_title(c, "LE MANDANT (CLIENT)", y)

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

    y -= 5*mm

    # ── SECTION SITE DE CONSOMMATION ────────────────────
    y = section_title(c, "SITE DE CONSOMMATION", y)

    # PDL et PCE TOUJOURS affichés (obligatoires)
    pdl_value = data.get('pdl') if data.get('pdl') else "À compléter par le conseiller"
    y = field_line(c, "PDL (Électricité) :", pdl_value, y)

    pce_value = data.get('pce') if data.get('pce') else "À compléter par le conseiller"
    y = field_line(c, "PCE (Gaz) :", pce_value, y)

    if data.get('puissance_kva'):
        y = field_line(c, "Puissance souscrite :", f"{data['puissance_kva']} kVA", y)

    y = field_line(c, "Fournisseur actuel :", data.get('fourn', '—'), y)
    if data.get('nom_offre'):
        y = field_line(c, "Offre actuelle :", data['nom_offre'], y)

    y -= 5*mm

    # ── SECTION MANDATAIRE ──────────────────────────────
    y = section_title(c, "LE MANDATAIRE", y)
    y = field_line(c, "Société :", "LILISTRAT STRATÉGIE SAS", y)
    y = field_line(c, "Marque commerciale :", "LILIWATT", y)
    y = field_line(c, "Email :", "contact@liliwatt.fr", y)
    y = field_line(c, "Site :", "www.liliwatt.fr", y)

    y -= 5*mm

    # ── SECTION OBJET ───────────────────────────────────
    y = section_title(c, "OBJET DU MANDAT", y)

    objet_text = "Le Mandant confie à LILIWATT un mandat non exclusif de courtage en énergie afin de :"
    c.setFillColor(NOIR)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, y, objet_text)
    y -= 6*mm

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

    y -= 3*mm

    # ── SECTION CONDITIONS ──────────────────────────────
    y = section_title(c, "CONDITIONS", y)

    conditions = [
        ("Durée :", "12 mois à compter de la date de signature, renouvelable par tacite reconduction"),
        ("Rémunération :", "LILIWATT est rémunéré directement par les fournisseurs. Aucun frais au Mandant."),
        ("Résiliation :", "Résiliable à tout moment par email à contact@liliwatt.fr"),
        ("Exclusivité :", "Mandat non exclusif — le Mandant reste libre de contracter directement"),
    ]
    for label, val in conditions:
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
        y -= 5.5*mm

    y -= 3*mm

    # ── SECTION RGPD ────────────────────────────────────
    y = section_title(c, "DONNÉES PERSONNELLES (RGPD)", y)

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

    y -= 5*mm

    # ── SECTION SIGNATURE ÉLECTRONIQUE ──────────────────
    # Vérifier si on a assez de place (besoin de 50mm minimum pour signature + pied de page)
    FOOTER_HEIGHT = 25*mm  # Hauteur du pied de page
    SIGNATURE_HEIGHT = 26*mm  # Hauteur du bloc signature
    MIN_Y = FOOTER_HEIGHT + SIGNATURE_HEIGHT + 5*mm  # Marge de sécurité

    if y < MIN_Y:
        # Ajouter pied de page sur cette page
        draw_footer(c, width)
        # Créer nouvelle page
        c.showPage()
        # Réinitialiser y en haut de la nouvelle page
        y = height - 40*mm

    c.setFillColor(GRIS_CLAIR)
    c.rect(15*mm, y - 22*mm, width - 30*mm, 26*mm, fill=1, stroke=0)
    c.setStrokeColor(VIOLET)
    c.setLineWidth(0.5)
    c.rect(15*mm, y - 22*mm, width - 30*mm, 26*mm, fill=0, stroke=1)

    c.setFillColor(VIOLET)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y, "SIGNATURE ÉLECTRONIQUE")

    c.setFillColor(colors.HexColor('#34D399'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20*mm, y - 7*mm, f"✓  Accepté en ligne le {data.get('date_signature', '')}")

    c.setFillColor(GRIS_TEXTE)
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, y - 13*mm, f"Par : {nom_complet}  |  Email : {data.get('email', '')}  |  IP : {data.get('ip', 'xxx.xxx.xxx.xxx')}")

    c.setFillColor(GRIS_TEXTE)
    c.setFont("Helvetica", 7.5)
    c.drawString(20*mm, y - 19*mm,
                 "La case cochée par le signataire vaut consentement au sens de l'article 7 du RGPD et constitue une preuve de signature électronique.")

    # ── PIED DE PAGE ────────────────────────────────────
    draw_footer(c, width)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
