#!/usr/bin/env python3
"""
Script pour ajouter le smooth scroll et l'animation idle au chatbot LILI
"""
import re
from pathlib import Path

# Liste des fichiers HTML à mettre à jour
html_files = [
    "/Users/strategyglobal/Desktop/liliwatt-website/index.html",
    "/Users/strategyglobal/Desktop/liliwatt-website/contact.html",
    "/Users/strategyglobal/Desktop/liliwatt-website/recrutement.html",
    "/Users/strategyglobal/Desktop/liliwatt-website/apropos.html",
    "/Users/strategyglobal/Desktop/liliwatt-website/offres.html",
    "/Users/strategyglobal/Desktop/liliwatt-website/blog.html",
    "/Users/strategyglobal/Desktop/liliwatt-website/blog-article.html",
    "/Users/strategyglobal/Desktop/liliwatt-website/extracteur.html",
]

# CSS à rechercher
old_css = '''    #lili-chat-widget {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }'''

# Nouveau CSS avec position absolute
new_css = '''    #lili-chat-widget {
      position: absolute;
      right: 20px;
      z-index: 9999;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      transition: none;
      will-change: top;
    }'''

# Animation bounce à ajouter après @keyframes pulse
bounce_animation = '''
    /* Animation idle bounce pour chatbot */
    @keyframes chatbot-bounce {
      0%, 100% { transform: translateY(0px); }
      25% { transform: translateY(-10px); }
      50% { transform: translateY(0px); }
      75% { transform: translateY(4px); }
    }

    #lili-chat-widget.chatbot-idle {
      animation: chatbot-bounce 1.8s ease-in-out infinite;
    }
'''

# Nouveau code JavaScript à ajouter
new_js_code = '''
    /* ═══════════════════════════════════════════════════════════════════════ */
    /* CHATBOT SMOOTH SCROLL & IDLE ANIMATION */
    /* ═══════════════════════════════════════════════════════════════════════ */
    (function() {
      const chatbot = document.getElementById('lili-chat-widget');
      if (!chatbot) return;

      let targetY = window.innerHeight * 0.5;
      let currentY = targetY;
      let idleTimer;

      // Mise à jour de la position cible lors du scroll
      function updateTargetPosition() {
        const scrolled = window.scrollY;
        const windowH = window.innerHeight;
        targetY = scrolled + windowH * 0.5;
      }

      // Animation fluide du chatbot
      function animateChatbot() {
        currentY += (targetY - currentY) * 0.08;
        chatbot.style.top = currentY + 'px';
        chatbot.style.transform = 'translateY(-50%)';
        requestAnimationFrame(animateChatbot);
      }

      // Gestion de l'animation idle (rebond)
      function resetIdleTimer() {
        chatbot.classList.remove('chatbot-idle');
        clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
          chatbot.classList.add('chatbot-idle');
        }, 3000);
      }

      // Initialisation
      window.addEventListener('scroll', () => {
        updateTargetPosition();
        resetIdleTimer();
      });

      window.addEventListener('mousemove', resetIdleTimer);
      window.addEventListener('click', resetIdleTimer);

      updateTargetPosition();
      animateChatbot();
      resetIdleTimer();
    })();

'''

print("🔄 Mise à jour du chatbot LILI avec smooth scroll et animation idle...\n")

for file_path_str in html_files:
    file_path = Path(file_path_str)

    if not file_path.exists():
        print(f"⚠️  Fichier non trouvé : {file_path.name}")
        continue

    print(f"📝 Traitement de {file_path.name}...")
    content = file_path.read_text(encoding='utf-8')

    # 1. Remplacer le CSS du widget (position fixed → absolute)
    if old_css in content:
        content = content.replace(old_css, new_css)
        print(f"  ✓ CSS position: fixed → absolute")
    else:
        print(f"  ⚠️  CSS position non trouvé (peut-être déjà modifié)")

    # 2. Ajouter l'animation bounce après @keyframes pulse
    # Rechercher la fin de l'animation pulse
    pulse_pattern = r'(@keyframes pulse \{[^}]+\})'
    if re.search(pulse_pattern, content):
        content = re.sub(
            pulse_pattern,
            r'\1' + bounce_animation,
            content
        )
        print(f"  ✓ Animation bounce ajoutée")
    else:
        print(f"  ⚠️  @keyframes pulse non trouvé")

    # 3. Ajouter le JavaScript de smooth scroll avant la balise de fermeture </script>
    # Chercher le dernier </script> qui contient le code du chatbot
    # On va l'insérer juste avant la ligne "let chatHistory = [];"
    if "let chatHistory = [];" in content:
        content = content.replace(
            "let chatHistory = [];",
            new_js_code + "\n    let chatHistory = [];"
        )
        print(f"  ✓ JavaScript smooth scroll ajouté")
    else:
        print(f"  ⚠️  Point d'insertion JS non trouvé")

    # Écrire le fichier
    file_path.write_text(content, encoding='utf-8')
    print(f"  ✅ {file_path.name} mis à jour\n")

print("✅ Tous les fichiers ont été traités avec succès!")
print("\n🎯 Modifications appliquées :")
print("  • Position: fixed → absolute pour smooth scroll")
print("  • Animation bounce après 3 secondes d'inactivité")
print("  • Suivi fluide du scroll avec easing")
