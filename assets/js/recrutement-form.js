// ═══════════════════════════════════════════════════════════════
// FORMULAIRES DE RECRUTEMENT — LILIWATT
// Gestion de l'envoi par email via /api/recrutement
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {
  // Sélectionner tous les formulaires de candidature dans les modaux
  const recruitmentForms = document.querySelectorAll('#apply-modal-1 form, #apply-modal-2 form, #apply-modal-spontanee form');

  // Mapper les IDs de modal aux noms de poste
  const posteMap = {
    'apply-modal-1': 'Conseiller Commercial Énergie B2B',
    'apply-modal-2': 'Téléprospecteur(trice) Énergie',
    'apply-modal-spontanee': 'Candidature spontanée'
  };

  recruitmentForms.forEach(function(form) {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();

      // Trouver le modal parent pour identifier le poste
      const modal = form.closest('[id^="apply-modal"]');
      const modalId = modal ? modal.id : 'apply-modal-spontanee';
      const poste = posteMap[modalId] || 'Candidature spontanée';

      // Récupérer les données du formulaire
      const formData = new FormData();

      // Champs obligatoires
      const nomInput = form.querySelector('input[type="text"]');
      const emailInput = form.querySelector('input[type="email"]');
      const telInput = form.querySelector('input[type="tel"]');
      const cvInput = form.querySelector('input[type="file"]');

      // Champs optionnels
      const posteInput = form.querySelector('input[placeholder*="Commercial"], input[placeholder*="Analyste"]');
      const messageTextarea = form.querySelector('textarea');

      // Valider les champs obligatoires
      if (!nomInput || !emailInput || !telInput || !cvInput) {
        alert('Erreur : certains champs obligatoires sont manquants.');
        return;
      }

      const nom = nomInput.value.trim();
      const email = emailInput.value.trim();
      const telephone = telInput.value.trim();
      const cvFile = cvInput.files[0];

      if (!nom || !email || !telephone) {
        alert('Veuillez remplir tous les champs obligatoires.');
        return;
      }

      if (!cvFile) {
        alert('Veuillez joindre votre CV.');
        return;
      }

      // Ajouter les données au FormData
      formData.append('nom', nom);
      formData.append('email', email);
      formData.append('telephone', telephone);
      formData.append('poste', posteInput ? posteInput.value.trim() || poste : poste);
      formData.append('message', messageTextarea ? messageTextarea.value.trim() : '');
      formData.append('cv', cvFile);

      // Désactiver le bouton submit
      const submitBtn = form.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Envoi en cours...';

      try {
        const response = await fetch('/api/recrutement', {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
          // Fermer le modal
          if (modal) {
            modal.style.display = 'none';
          }

          // Afficher message de succès
          const successMessage = document.createElement('div');
          successMessage.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.95), rgba(217, 70, 239, 0.95));
            color: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(124, 58, 237, 0.5);
            z-index: 10000;
            text-align: center;
            max-width: 500px;
          `;
          successMessage.innerHTML = `
            <div style="font-size: 64px; margin-bottom: 16px;">✅</div>
            <h3 style="margin-bottom: 12px; font-size: 24px;">Candidature envoyée !</h3>
            <p style="margin-bottom: 8px; font-size: 16px;">
              Merci pour votre candidature.
            </p>
            <p style="font-size: 14px; opacity: 0.9;">
              Nous vous recontacterons sous 5 jours ouvrés si votre profil correspond à nos besoins.
            </p>
            <p style="font-size: 12px; opacity: 0.7; margin-top: 20px;">
              recrutement@liliwatt.fr
            </p>
          `;
          document.body.appendChild(successMessage);

          // Retirer le message après 6 secondes
          setTimeout(() => {
            successMessage.remove();
          }, 6000);

          // Réinitialiser le formulaire
          form.reset();

        } else {
          throw new Error(result.error || 'Erreur lors de l\'envoi');
        }
      } catch (error) {
        console.error('Erreur:', error);
        alert('Une erreur est survenue lors de l\'envoi de votre candidature. Veuillez réessayer ou nous contacter directement à recrutement@liliwatt.fr');

        // Réactiver le bouton
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  });
});
