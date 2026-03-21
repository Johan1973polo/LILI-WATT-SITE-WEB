/**
 * LILIWATT - JavaScript principal
 * Animations, interactions et fonctionnalités
 */

// ========================================
// Configuration et constantes
// ========================================
const CONFIG = {
  scrollRevealDelay: 100,
  countUpDuration: 2000,
  headerScrollThreshold: 100
};

// ========================================
// DOM Ready
// ========================================
document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initMobileMenu();
  initScrollReveal();
  initCountUp();
  initAccordion();
  initUploadZone();
  initModals();
  initForms();
});

// ========================================
// Header sticky & scroll effects
// ========================================
function initHeader() {
  const header = document.querySelector('.header');

  if (!header) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > CONFIG.headerScrollThreshold) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });
}

// ========================================
// Menu mobile
// ========================================
function initMobileMenu() {
  const menuToggle = document.querySelector('.menu-toggle');
  const navMenu = document.querySelector('.nav-menu');
  const navLinks = document.querySelectorAll('.nav-link');

  if (!menuToggle || !navMenu) return;

  // Toggle menu
  menuToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    menuToggle.classList.toggle('active');
  });

  // Close menu on link click
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navMenu.classList.remove('active');
      menuToggle.classList.remove('active');
    });
  });

  // Close menu on outside click
  document.addEventListener('click', (e) => {
    if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
      navMenu.classList.remove('active');
      menuToggle.classList.remove('active');
    }
  });
}

// ========================================
// Scroll Reveal Animation - Bidirectionnelle
// ========================================
function initScrollReveal() {
  const revealElements = document.querySelectorAll('.reveal');

  if (!revealElements.length) return;

  const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Élément entre dans le viewport
        entry.target.classList.add('animate-in');
        entry.target.classList.remove('animate-out');
      } else {
        // Élément sort du viewport
        entry.target.classList.remove('animate-in');
        entry.target.classList.add('animate-out');
      }
    });
  }, observerOptions);

  revealElements.forEach(element => {
    observer.observe(element);
  });
}

// ========================================
// Count Up Animation - Bidirectionnelle
// ========================================
function initCountUp() {
  const countElements = document.querySelectorAll('[data-count]');

  if (!countElements.length) return;

  const observerOptions = {
    threshold: 0.5
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Élément entre dans le viewport - lancer l'animation
        animateCount(entry.target);
      } else {
        // Élément sort du viewport - réinitialiser à 0
        entry.target.textContent = '0';
        if (entry.target.animationFrame) {
          cancelAnimationFrame(entry.target.animationFrame);
        }
      }
    });
  }, observerOptions);

  countElements.forEach(element => {
    observer.observe(element);
  });
}

function animateCount(element) {
  const target = parseInt(element.dataset.count);
  const duration = CONFIG.countUpDuration;
  const increment = target / (duration / 16);
  let current = 0;

  // Annuler l'animation précédente si elle existe
  if (element.animationFrame) {
    cancelAnimationFrame(element.animationFrame);
  }

  const updateCount = () => {
    current += increment;

    if (current < target) {
      element.textContent = Math.floor(current);
      element.animationFrame = requestAnimationFrame(updateCount);
    } else {
      element.textContent = target;
      element.animationFrame = null;
    }
  };

  updateCount();
}

// ========================================
// Accordéon
// ========================================
function initAccordion() {
  const accordionHeaders = document.querySelectorAll('.accordion-header');

  if (!accordionHeaders.length) return;

  accordionHeaders.forEach(header => {
    header.addEventListener('click', () => {
      const accordionItem = header.parentElement;
      const isActive = accordionItem.classList.contains('active');

      // Close all accordion items
      document.querySelectorAll('.accordion-item').forEach(item => {
        item.classList.remove('active');
      });

      // Open clicked item if it wasn't active
      if (!isActive) {
        accordionItem.classList.add('active');
      }
    });
  });
}

// ========================================
// Upload Zone
// ========================================
function initUploadZone() {
  const uploadZone = document.querySelector('.upload-zone');
  const fileInput = document.querySelector('#file-upload');

  if (!uploadZone || !fileInput) return;

  // Click to browse
  uploadZone.addEventListener('click', () => {
    fileInput.click();
  });

  // Drag & drop
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = 'var(--elec)';
    uploadZone.style.background = 'rgba(217, 70, 239, 0.1)';
  });

  uploadZone.addEventListener('dragleave', () => {
    uploadZone.style.borderColor = 'var(--violet)';
    uploadZone.style.background = 'var(--card-bg)';
  });

  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.style.borderColor = 'var(--violet)';
    uploadZone.style.background = 'var(--card-bg)';

    const files = e.dataTransfer.files;
    handleFileUpload(files);
  });

  // File input change
  fileInput.addEventListener('change', (e) => {
    const files = e.target.files;
    handleFileUpload(files);
  });
}

function handleFileUpload(files) {
  if (files.length === 0) return;

  const file = files[0];
  console.log('Fichier uploadé:', file.name);

  // Show loading state
  const uploadZone = document.querySelector('.upload-zone');
  const originalContent = uploadZone.innerHTML;

  uploadZone.innerHTML = `
    <div class="upload-loading">
      <div class="spinner"></div>
      <p class="upload-text">Analyse en cours...</p>
      <p class="upload-subtext">${file.name}</p>
    </div>
  `;

  // Simulate upload and analysis (2 seconds)
  setTimeout(() => {
    showResults();
  }, 2000);
}

function showResults() {
  const resultsSection = document.querySelector('#results-section');
  if (resultsSection) {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ========================================
// Modals
// ========================================
function initModals() {
  const modalTriggers = document.querySelectorAll('[data-modal]');
  const modals = document.querySelectorAll('.modal');
  const modalCloses = document.querySelectorAll('.modal-close');

  // Open modals
  modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = trigger.dataset.modal;
      const modal = document.querySelector(`#${modalId}`);
      if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  // Close modals
  modalCloses.forEach(close => {
    close.addEventListener('click', () => {
      const modal = close.closest('.modal');
      if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Close on outside click
  modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Close on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      modals.forEach(modal => {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      });
    }
  });
}

// ========================================
// Forms
// ========================================
function initForms() {
  const forms = document.querySelectorAll('form');

  forms.forEach(form => {
    form.addEventListener('submit', handleFormSubmit);
  });
}

function handleFormSubmit(e) {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);

  // Validation basique
  const requiredFields = form.querySelectorAll('[required]');
  let isValid = true;

  requiredFields.forEach(field => {
    if (!field.value.trim()) {
      isValid = false;
      field.style.borderColor = '#EF4444';
    } else {
      field.style.borderColor = 'var(--border)';
    }
  });

  if (!isValid) {
    alert('Veuillez remplir tous les champs obligatoires.');
    return;
  }

  // Show success message
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.textContent;

  submitBtn.textContent = 'Envoi en cours...';
  submitBtn.disabled = true;

  // Simulate API call
  setTimeout(() => {
    submitBtn.textContent = '✓ Message envoyé !';
    submitBtn.style.background = '#10B981';

    // Reset form after 2 seconds
    setTimeout(() => {
      form.reset();
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
      submitBtn.style.background = '';

      // Close modal if form is in modal
      const modal = form.closest('.modal');
      if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    }, 2000);
  }, 1500);
}

// ========================================
// Smooth scroll for anchor links
// ========================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');

    if (href === '#') return;

    e.preventDefault();
    const target = document.querySelector(href);

    if (target) {
      const headerHeight = document.querySelector('.header')?.offsetHeight || 0;
      const targetPosition = target.offsetTop - headerHeight - 20;

      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    }
  });
});

// ========================================
// Toggle example results (for extracteur page)
// ========================================
function showExampleResults() {
  const resultsSection = document.querySelector('#results-section');
  if (resultsSection) {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Make function globally available
window.showExampleResults = showExampleResults;

// ========================================
// Progress bars animation
// ========================================
function initProgressBars() {
  const progressBars = document.querySelectorAll('.progress-bar');

  if (!progressBars.length) return;

  const observerOptions = {
    threshold: 0.5
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bar = entry.target;
        const width = bar.dataset.width || '0';

        setTimeout(() => {
          bar.style.width = width + '%';
        }, 200);

        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  progressBars.forEach(bar => {
    observer.observe(bar);
  });
}

// Initialize progress bars on page load
document.addEventListener('DOMContentLoaded', initProgressBars);

// ========================================
// Utilities
// ========================================

// Add CSS animation for spinner
const style = document.createElement('style');
style.textContent = `
  .spinner {
    width: 50px;
    height: 50px;
    border: 4px solid var(--border);
    border-top-color: var(--violet);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .progress-bar {
    height: 8px;
    background: linear-gradient(90deg, var(--violet), var(--elec));
    border-radius: 10px;
    width: 0;
    transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--glow);
  }

  .progress-container {
    background: var(--card-bg);
    border-radius: 10px;
    overflow: hidden;
    margin: 0.5rem 0;
  }
`;
document.head.appendChild(style);
// ========================================
// Sélecteur de thème — Test A/B/C/D/E
// ========================================
function initThemeSelector() {
  const buttons = document.querySelectorAll('.theme-btn');
  const body = document.body;
  
  // Appliquer le thème E par défaut
  body.classList.add('theme-e');
  
  buttons.forEach(button => {
    button.addEventListener('click', () => {
      // Retirer toutes les classes de thème
      body.className = '';
      
      // Retirer la classe active de tous les boutons
      buttons.forEach(btn => btn.classList.remove('active'));
      
      // Ajouter la classe active au bouton cliqué
      button.classList.add('active');
      
      // Appliquer le nouveau thème
      const theme = button.dataset.theme;
      if (theme) {
        body.classList.add(theme);
      }
      
      // Sauvegarder le choix dans localStorage
      localStorage.setItem('liliwatt-theme', theme);
      
      // Effet visuel de feedback
      button.style.transform = 'scale(1.15)';
      setTimeout(() => {
        button.style.transform = '';
      }, 200);
    });
  });
  
  // Restaurer le thème sauvegardé si disponible
  const savedTheme = localStorage.getItem('liliwatt-theme');
  if (savedTheme !== null) {
    body.className = '';
    if (savedTheme) {
      body.classList.add(savedTheme);
    }
    
    // Mettre à jour le bouton actif
    buttons.forEach(btn => {
      btn.classList.remove('active');
      if (btn.dataset.theme === savedTheme) {
        btn.classList.add('active');
      }
    });
  }
}

// Initialiser le sélecteur de thème
document.addEventListener('DOMContentLoaded', initThemeSelector);
