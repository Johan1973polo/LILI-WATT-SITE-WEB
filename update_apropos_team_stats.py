#!/usr/bin/env python3
"""
Script pour mettre à jour l'équipe et les statistiques sur la page À propos
"""
import re
from pathlib import Path

file_path = Path("/Users/strategyglobal/Desktop/liliwatt-website/apropos.html")

print(f"📝 Mise à jour de apropos.html...")

# Lire le contenu
content = file_path.read_text(encoding='utf-8')

# 1. Mettre à jour la section équipe (team-grid)
old_team = r'''      <div class="team-grid">
        <div class="team-member reveal">
          <div class="team-photo">
            \[Photo Johan - Fondateur\]
          </div>
          <div class="team-info">
            <h3 class="team-name">Johan STRATÉGY</h3>
            <div class="team-role">Fondateur & Directeur</div>
            <p class="team-bio">Expert du courtage en énergie depuis plus de 5 ans\. Ancien consultant énergie pour grands comptes, Johan a créé LILIWATT pour démocratiser l'accès aux meilleurs tarifs professionnels\.</p>
          </div>
        </div>

        <div class="team-member reveal">
          <div class="team-photo">
            \[Photo Marie - Conseillère commerciale\]
          </div>
          <div class="team-info">
            <h3 class="team-name">Marie DUBOIS</h3>
            <div class="team-role">Conseillère Commerciale Senior</div>
            <p class="team-bio">Spécialiste des secteurs CHR \(Cafés, Hôtels, Restaurants\) et artisans\. Marie accompagne nos clients dans leur transition énergétique avec pédagogie et efficacité\.</p>
          </div>
        </div>

        <div class="team-member reveal">
          <div class="team-photo">
            \[Photo Thomas - Analyste tarifs\]
          </div>
          <div class="team-info">
            <h3 class="team-name">Thomas MARTIN</h3>
            <div class="team-role">Analyste Tarifs & Marchés</div>
            <p class="team-bio">Veille quotidienne du marché de l'énergie et des grilles tarifaires\. Thomas garantit que nos clients accèdent toujours aux offres les plus compétitives du moment\.</p>
          </div>
        </div>
      </div>'''

new_team = '''      <div class="team-grid">
        <div class="team-member reveal">
          <div class="team-photo" style="background: linear-gradient(135deg, #7C3AED, #D946EF); font-size: 4rem; font-weight: 900; color: white; font-family: var(--font-heading);">
            JM
          </div>
          <div class="team-info">
            <h3 class="team-name">Johan M.</h3>
            <div class="team-role">Directeur Commercial</div>
            <p class="team-bio">Expert reconnu du courtage énergie B2B, Johan apporte son expertise pointue des marchés de l'énergie et sa maîtrise des négociations tarifaires. Fort d'une expérience significative dans le secteur, il pilote la stratégie commerciale de LILIWATT et assure à nos clients l'accès aux meilleures conditions du marché.</p>
          </div>
        </div>

        <div class="team-member reveal">
          <div class="team-photo" style="background: linear-gradient(135deg, #4C1D95, #7C3AED); font-size: 4rem; font-weight: 900; color: white; font-family: var(--font-heading);">
            KM
          </div>
          <div class="team-info">
            <h3 class="team-name">Kevin M.</h3>
            <div class="team-role">Président</div>
            <p class="team-bio">À la tête de LILISTRAT STRATÉGIE SAS, Kevin dirige la vision stratégique et le développement de LILIWATT. Son leadership et sa connaissance approfondie des enjeux énergétiques des entreprises françaises guident l'entreprise vers l'excellence opérationnelle et la satisfaction client.</p>
          </div>
        </div>

        <div class="team-member reveal">
          <div class="team-photo" style="background: linear-gradient(135deg, #6B21A8, #A855F7); font-size: 4rem; font-weight: 900; color: white; font-family: var(--font-heading);">
            EL
          </div>
          <div class="team-info">
            <h3 class="team-name">Emmanuel L.</h3>
            <div class="team-role">Ressources Humaines</div>
            <p class="team-bio">Responsable du développement des équipes et du recrutement, Emmanuel construit les talents de demain chez LILIWATT. Il orchestre la croissance de nos effectifs et veille à maintenir notre culture d'excellence et d'innovation au service de nos clients professionnels.</p>
          </div>
        </div>
      </div>'''

content = re.sub(old_team, new_team, content)
print("  ✓ Section équipe mise à jour")

# 2. Mettre à jour les statistiques
old_stats = r'''      <div class="stats reveal">
        <div class="stat-item">
          <span class="stat-number" data-count="200">0</span>
          <span class="stat-label">Contrats signés</span>
        </div>
        <div class="stat-item">
          <span class="stat-number" data-count="3">0</span>
          <span class="stat-label">Fournisseurs partenaires</span>
        </div>
        <div class="stat-item">
          <span class="stat-number" data-count="18">0</span>
          <span class="stat-label">% d'économies maximum</span>
        </div>
        <div class="stat-item">
          <span class="stat-number" data-count="2026">0</span>
          <span class="stat-label">Année de création</span>
        </div>
      </div>'''

new_stats = '''      <div class="stats reveal">
        <div class="stat-item">
          <span class="stat-number" data-count="18">0+</span>
          <span class="stat-label">Fournisseurs comparés</span>
        </div>
        <div class="stat-item">
          <span class="stat-number" data-count="18">0</span>
          <span class="stat-label">% d'économies maximum</span>
        </div>
        <div class="stat-item">
          <span class="stat-number" data-count="2026">0</span>
          <span class="stat-label">Année de création</span>
        </div>
        <div class="stat-item">
          <span class="stat-number" data-count="6">0+</span>
          <span class="stat-label">Secteurs accompagnés</span>
        </div>
      </div>'''

content = re.sub(old_stats, new_stats, content)
print("  ✓ Statistiques mises à jour")

# Écrire le fichier
file_path.write_text(content, encoding='utf-8')
print("✅ Fichier apropos.html mis à jour avec succès!")
