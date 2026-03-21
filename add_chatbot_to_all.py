#!/usr/bin/env python3
"""
Script pour ajouter le chatbot LILI à toutes les pages HTML
"""
from pathlib import Path

# Fichiers HTML à modifier (sauf index.html déjà fait)
html_files = [
    "apropos.html",
    "blog.html",
    "contact.html",
    "recrutement.html",
    "offres.html",
    "blog-article.html",
    "extracteur.html"
]

base_path = Path("/Users/strategyglobal/Desktop/liliwatt-website")

# Le widget chatbot complet (HTML + CSS + JS)
chatbot_widget = '''
  <!-- ═══════════════════════════════════════════════════════════════════════ -->
  <!-- CHATBOT LILI FLOTTANT -->
  <!-- ═══════════════════════════════════════════════════════════════════════ -->
  <div id="lili-chat-widget">
    <!-- Bouton flottant -->
    <div id="lili-bubble" onclick="toggleChat()">
      <div class="lili-avatar-btn">
        <svg width="28" height="28" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M5 20C5 20 10 10 20 10C30 10 35 20 35 20C35 20 30 30 20 30C10 30 5 20 5 20Z" fill="white" opacity="0.9"/>
          <circle cx="20" cy="20" r="4" fill="#7C3AED"/>
        </svg>
      </div>
      <span class="lili-badge">LILI</span>
      <div class="lili-notification" id="lili-notif">💬</div>
    </div>

    <!-- Fenêtre de chat -->
    <div id="lili-window" style="display: none;">
      <div class="lili-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div class="lili-avatar">
            <svg width="24" height="24" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 20C5 20 10 10 20 10C30 10 35 20 35 20C35 20 30 30 20 30C10 30 5 20 5 20Z" fill="white" opacity="0.9"/>
              <circle cx="20" cy="20" r="4" fill="#7C3AED"/>
            </svg>
          </div>
          <div>
            <div style="font-weight: 600; font-size: 15px;">LILI</div>
            <div style="font-size: 11px; opacity: 0.9; display: flex; align-items: center; gap: 5px;">
              <span class="status-dot"></span>
              En ligne
            </div>
          </div>
        </div>
        <button onclick="toggleChat()" style="background: none; border: none; color: white; font-size: 24px; cursor: pointer; padding: 0; line-height: 1;">×</button>
      </div>

      <div class="lili-messages" id="lili-messages">
        <div class="lili-msg lili-bot">
          <div class="lili-msg-avatar">
            <svg width="20" height="20" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 20C5 20 10 10 20 10C30 10 35 20 35 20C35 20 30 30 20 30C10 30 5 20 5 20Z" fill="white" opacity="0.9"/>
              <circle cx="20" cy="20" r="4" fill="#7C3AED"/>
            </svg>
          </div>
          <div class="lili-msg-content">
            Bonjour ! Je suis LILI, votre conseillère énergie 😊<br><br>
            Comment puis-je vous aider aujourd'hui ?
          </div>
        </div>
        <div class="lili-suggestions">
          <button onclick="sendSuggestion('Quels sont vos tarifs ?')">💰 Vos tarifs ?</button>
          <button onclick="sendSuggestion('Comment comparer les fournisseurs ?')">⚡ Comparer les fournisseurs</button>
          <button onclick="sendSuggestion('Puis-je changer de fournisseur ?')">🔄 Changer de fournisseur</button>
        </div>
      </div>

      <div class="lili-input-zone">
        <input type="text" id="lili-input" placeholder="Posez votre question..." onkeypress="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  </div>

  <style>
    /* ═══════════════════════════════════════════════════════════════════════ */
    /* CHATBOT LILI - STYLES */
    /* ═══════════════════════════════════════════════════════════════════════ */
    #lili-chat-widget {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Bouton flottant */
    #lili-bubble {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: linear-gradient(135deg, #7C3AED, #D946EF);
      box-shadow: 0 8px 24px rgba(124, 58, 237, 0.4);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
      animation: pulse 2s infinite;
    }

    #lili-bubble:hover {
      transform: scale(1.1);
      box-shadow: 0 12px 32px rgba(124, 58, 237, 0.5);
    }

    @keyframes pulse {
      0%, 100% { box-shadow: 0 8px 24px rgba(124, 58, 237, 0.4); }
      50% { box-shadow: 0 8px 32px rgba(124, 58, 237, 0.6); }
    }

    .lili-avatar-btn {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .lili-badge {
      position: absolute;
      bottom: -8px;
      left: 50%;
      transform: translateX(-50%);
      background: white;
      color: #7C3AED;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .lili-notification {
      position: absolute;
      top: -5px;
      right: -5px;
      width: 28px;
      height: 28px;
      background: #EF4444;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      animation: blink 1.5s infinite;
      border: 2px solid white;
    }

    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    /* Fenêtre de chat */
    #lili-window {
      position: absolute;
      bottom: 80px;
      right: 0;
      width: 360px;
      height: 520px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 12px 48px rgba(0,0,0,0.2);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      animation: slideUp 0.3s ease;
    }

    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .lili-header {
      background: linear-gradient(135deg, #7C3AED, #D946EF);
      color: white;
      padding: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .lili-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #10B981;
      display: inline-block;
      animation: pulse-dot 2s infinite;
    }

    @keyframes pulse-dot {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    /* Zone de messages */
    .lili-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: #F9FAFB;
    }

    .lili-messages::-webkit-scrollbar {
      width: 6px;
    }

    .lili-messages::-webkit-scrollbar-thumb {
      background: #D1D5DB;
      border-radius: 3px;
    }

    .lili-msg {
      display: flex;
      gap: 10px;
      margin-bottom: 16px;
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .lili-msg-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: linear-gradient(135deg, #7C3AED, #D946EF);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .lili-msg-content {
      background: white;
      padding: 12px 16px;
      border-radius: 12px;
      max-width: 75%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      line-height: 1.5;
      font-size: 14px;
    }

    .lili-user {
      flex-direction: row-reverse;
    }

    .lili-user .lili-msg-avatar {
      background: linear-gradient(135deg, #6B7280, #9CA3AF);
    }

    .lili-user .lili-msg-content {
      background: linear-gradient(135deg, #7C3AED, #D946EF);
      color: white;
    }

    /* Suggestions */
    .lili-suggestions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .lili-suggestions button {
      background: white;
      border: 1px solid #E5E7EB;
      padding: 8px 14px;
      border-radius: 20px;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s;
      color: #374151;
    }

    .lili-suggestions button:hover {
      background: #F3F4F6;
      border-color: #7C3AED;
      color: #7C3AED;
    }

    /* Indicateur de frappe */
    .lili-typing {
      display: flex;
      gap: 10px;
      margin-bottom: 16px;
    }

    .lili-typing .lili-msg-content {
      display: flex;
      gap: 4px;
      padding: 12px 16px;
    }

    .typing-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #9CA3AF;
      animation: typing 1.4s infinite;
    }

    .typing-dot:nth-child(2) {
      animation-delay: 0.2s;
    }

    .typing-dot:nth-child(3) {
      animation-delay: 0.4s;
    }

    @keyframes typing {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-10px); }
    }

    /* Zone de saisie */
    .lili-input-zone {
      padding: 16px;
      background: white;
      border-top: 1px solid #E5E7EB;
      display: flex;
      gap: 10px;
    }

    #lili-input {
      flex: 1;
      border: 1px solid #E5E7EB;
      border-radius: 24px;
      padding: 10px 16px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }

    #lili-input:focus {
      border-color: #7C3AED;
    }

    .lili-input-zone button {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #7C3AED, #D946EF);
      border: none;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform 0.2s;
    }

    .lili-input-zone button:hover {
      transform: scale(1.1);
    }

    /* Mobile responsive */
    @media (max-width: 480px) {
      #lili-window {
        width: calc(100vw - 20px);
        height: 500px;
        right: 10px;
        bottom: 90px;
      }

      #lili-bubble {
        width: 56px;
        height: 56px;
      }
    }
  </style>

  <script>
    /* ═══════════════════════════════════════════════════════════════════════ */
    /* CHATBOT LILI - JAVASCRIPT */
    /* ═══════════════════════════════════════════════════════════════════════ */
    let chatHistory = [];

    function toggleChat() {
      const window = document.getElementById('lili-window');
      const notif = document.getElementById('lili-notif');

      if (window.style.display === 'none') {
        window.style.display = 'flex';
        notif.style.display = 'none';
      } else {
        window.style.display = 'none';
      }
    }

    function sendMessage() {
      const input = document.getElementById('lili-input');
      const message = input.value.trim();

      if (!message) return;

      // Afficher le message utilisateur
      addMessage(message, 'user');
      input.value = '';

      // Afficher l'indicateur de frappe
      showTyping();

      // Envoyer au backend
      fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          messages: chatHistory
        })
      })
      .then(res => res.json())
      .then(data => {
        hideTyping();
        if (data.success) {
          addMessage(data.reply, 'bot');
        } else {
          addMessage("Désolée, je rencontre un problème technique. Appelez-nous au 01 84 16 08 56 😊", 'bot');
        }
      })
      .catch(err => {
        hideTyping();
        console.error('Chat error:', err);
        addMessage("Désolée, je rencontre un problème technique. Appelez-nous au 01 84 16 08 56 😊", 'bot');
      });
    }

    function sendSuggestion(text) {
      document.getElementById('lili-input').value = text;
      sendMessage();
    }

    function addMessage(content, role) {
      const messagesDiv = document.getElementById('lili-messages');

      // Supprimer les suggestions après le premier message utilisateur
      const suggestions = messagesDiv.querySelector('.lili-suggestions');
      if (role === 'user' && suggestions) {
        suggestions.remove();
      }

      // Ajouter à l'historique
      chatHistory.push({
        role: role === 'user' ? 'user' : 'assistant',
        content: content
      });

      // Limiter à 10 messages
      if (chatHistory.length > 10) {
        chatHistory = chatHistory.slice(-10);
      }

      // Créer le message
      const msgDiv = document.createElement('div');
      msgDiv.className = role === 'user' ? 'lili-msg lili-user' : 'lili-msg lili-bot';

      msgDiv.innerHTML = `
        <div class="lili-msg-avatar">
          ${role === 'bot' ? `
            <svg width="20" height="20" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 20C5 20 10 10 20 10C30 10 35 20 35 20C35 20 30 30 20 30C10 30 5 20 5 20Z" fill="white" opacity="0.9"/>
              <circle cx="20" cy="20" r="4" fill="#7C3AED"/>
            </svg>
          ` : `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" fill="white" opacity="0.9"/>
              <path d="M12 14C13.1046 14 14 13.1046 14 12C14 10.8954 13.1046 10 12 10C10.8954 10 10 10.8954 10 12C10 13.1046 10.8954 14 12 14Z" fill="#6B7280"/>
            </svg>
          `}
        </div>
        <div class="lili-msg-content">${content}</div>
      `;

      messagesDiv.appendChild(msgDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function showTyping() {
      const messagesDiv = document.getElementById('lili-messages');
      const typingDiv = document.createElement('div');
      typingDiv.className = 'lili-typing';
      typingDiv.id = 'lili-typing-indicator';
      typingDiv.innerHTML = `
        <div class="lili-msg-avatar">
          <svg width="20" height="20" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 20C5 20 10 10 20 10C30 10 35 20 35 20C35 20 30 30 20 30C10 30 5 20 5 20Z" fill="white" opacity="0.9"/>
            <circle cx="20" cy="20" r="4" fill="#7C3AED"/>
          </svg>
        </div>
        <div class="lili-msg-content">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      `;
      messagesDiv.appendChild(typingDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function hideTyping() {
      const typingDiv = document.getElementById('lili-typing-indicator');
      if (typingDiv) {
        typingDiv.remove();
      }
    }

    // Auto-ouverture de la notification après 8 secondes
    setTimeout(() => {
      const notif = document.getElementById('lili-notif');
      if (notif && document.getElementById('lili-window').style.display === 'none') {
        notif.style.display = 'flex';
      }
    }, 8000);
  </script>

'''

total_changes = 0

for html_file in html_files:
    file_path = base_path / html_file

    if not file_path.exists():
        print(f"⚠️  Fichier non trouvé : {html_file}")
        continue

    print(f"\n📝 Traitement de {html_file}...")

    # Lire le contenu
    content = file_path.read_text(encoding='utf-8')

    # Vérifier si le chatbot n'est pas déjà présent
    if 'lili-chat-widget' in content:
        print(f"  ℹ️  Chatbot déjà présent, sauté")
        continue

    # Insérer le widget avant </body>
    if '</body>' in content:
        content = content.replace('</body>', f'{chatbot_widget}\n</body>')
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✅ Chatbot LILI ajouté avec succès")
        total_changes += 1
    else:
        print(f"  ⚠️  Balise </body> non trouvée")

print(f"\n🎉 Terminé ! Chatbot LILI ajouté à {total_changes} fichier(s)")
