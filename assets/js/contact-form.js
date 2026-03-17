// ═══════════════════════════════════════════════════════════════
// FORMULAIRE DE CONTACT — LILIWATT
// Gestion de l'envoi par email via /api/contact
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {
  const contactForm = document.querySelector('form.contact-form');

  if (!contactForm) return;

  contactForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Récupérer les données du formulaire
    const formData = {
      nom: contactForm.querySelector('[name="nom"]')?.value || '',
      email: contactForm.querySelector('[name="email"]')?.value || '',
      telephone: contactForm.querySelector('[name="telephone"]')?.value || '',
      message: contactForm.querySelector('[name="message"]')?.value || '',
      sujet: contactForm.querySelector('[name="sujet"]')?.value || 'Contact site web'
    };

    // Ajouter les informations supplémentaires si présentes (pour page contact)
    const societe = contactForm.querySelector('[name="societe"]')?.value;
    const secteur = contactForm.querySelector('[name="secteur"]')?.value;
    const fournisseur = contactForm.querySelector('[name="fournisseur"]')?.value;
    const montant = contactForm.querySelector('[name="montant"]')?.value;

    if (societe || secteur || fournisseur || montant) {
      formData.message = `Société: ${societe || 'N/A'}
Secteur: ${secteur || 'N/A'}
Fournisseur actuel: ${fournisseur || 'N/A'}
Montant estimé: ${montant || 'N/A'}

${formData.message || '(Aucun message supplémentaire)'}`;
    }

    // Désactiver le bouton submit
    const submitBtn = contactForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Envoi en cours...';

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Afficher message de succès
        contactForm.innerHTML = `
          <div style="text-align: center; padding: 60px 20px; background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(217, 70, 239, 0.1)); border-radius: 12px; border: 2px solid #7C3AED;">
            <div style="font-size: 64px; margin-bottom: 16px;">✅</div>
            <h3 style="color: #7C3AED; margin-bottom: 12px; font-size: 24px;">Message envoyé avec succès !</h3>
            <p style="color: #A78BFA; margin-bottom: 8px; font-size: 16px;">
              Merci pour votre demande.
            </p>
            <p style="color: #6B7280; font-size: 14px;">
              Nous vous répondons sous 24h à <strong style="color: #D946EF;">${formData.email}</strong>
            </p>
          </div>
        `;
      } else {
        throw new Error(result.error || 'Erreur lors de l\'envoi');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Une erreur est survenue lors de l\'envoi. Veuillez réessayer ou nous contacter directement par téléphone.');

      // Réactiver le bouton
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
});
