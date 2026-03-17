// ═══════════════════════════════════════════════════════════════
// CONSTELLATION ANIMATION — Fournisseurs LILIWATT
// Animation canvas avec 18 nœuds de fournisseurs interconnectés
// ═══════════════════════════════════════════════════════════════

(function() {
  'use strict';

  const canvas = document.getElementById('constellationCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const tooltip = document.getElementById('tooltip');

  // ─────────────────────────────────────────────────────────────
  // CONFIGURATION
  // ─────────────────────────────────────────────────────────────
  const config = {
    colors: {
      background: '#06060F',
      nodeViolet: '#7C3AED',
      nodeFuchsia: '#D946EF',
      lineColor: '#A78BFA',
      lineOpacity: 0.3,
      particleColor: '#A78BFA'
    },
    node: {
      radius: 8,
      haloRadius: 16,
      logoSize: 40,
      hoverScale: 1.3
    },
    animation: {
      floatSpeed: 0.15,
      particleSpeed: 0.3,
      particleCount: 30
    },
    center: {
      logoSize: 80
    }
  };

  // ─────────────────────────────────────────────────────────────
  // FOURNISSEURS — 18 nœuds
  // ─────────────────────────────────────────────────────────────
  const providers = [
    { name: 'Alpiq', logo: 'assets/images/fournisseurs/Logo_Alpiq.svg' },
    { name: 'Octopus Energy', logo: 'assets/images/fournisseurs/Logo_Octopus_Energy.png' },
    { name: 'TotalEnergies', logo: 'assets/images/fournisseurs/Logo_TotalEnergies.svg.png' },
    { name: 'ilek', logo: 'assets/images/fournisseurs/Logo_ilek.svg.png' },
    { name: 'Alterna', logo: 'assets/images/fournisseurs/alterna.webp' },
    { name: 'ENI', logo: 'assets/images/fournisseurs/eni.png' },
    { name: 'Gazel Energie', logo: 'assets/images/fournisseurs/gazel-energie.png' },
    { name: 'Iberdrola', logo: 'assets/images/fournisseurs/iberdrola.svg' },
    { name: 'ekWateur', logo: 'assets/images/fournisseurs/logo ekwateur.png' },
    { name: 'Engie', logo: 'assets/images/fournisseurs/logo engie.png' },
    { name: 'Endesa', logo: 'assets/images/fournisseurs/logo-endesa.png' },
    { name: 'Vattenfall', logo: 'assets/images/fournisseurs/logo-vattenfall.png' },
    { name: 'MET', logo: 'assets/images/fournisseurs/met-logo.svg' },
    { name: 'Mint Energie', logo: 'assets/images/fournisseurs/mint-energie.webp' },
    { name: 'Ohm Energie', logo: 'assets/images/fournisseurs/ohm-energie.png' },
    { name: 'Priméo Energie', logo: 'assets/images/fournisseurs/primeo_energie.png' },
    { name: 'Wekiwi', logo: 'assets/images/fournisseurs/wekiwi.png' },
    { name: 'EDF', logo: 'assets/images/fournisseurs/png-clipart-logo-de-l-electricite-energie-edf-group-energie-france-edf-energy-text-trademark.png' }
  ];

  // ─────────────────────────────────────────────────────────────
  // CANVAS SETUP
  // ─────────────────────────────────────────────────────────────
  let width, height, centerX, centerY;
  let nodes = [];
  let particles = [];
  let hoveredNode = null;
  let imagesLoaded = 0;
  let isReady = false;

  function resizeCanvas() {
    const container = canvas.parentElement;
    width = container.offsetWidth;
    height = container.offsetHeight;

    canvas.width = width;
    canvas.height = height;

    centerX = width / 2;
    centerY = height / 2;

    initializeNodes();
    initializeParticles();
  }

  // ─────────────────────────────────────────────────────────────
  // PRELOAD IMAGES
  // ─────────────────────────────────────────────────────────────
  const centerLogo = new Image();
  centerLogo.src = 'assets/images/logo-liliwatt.png';
  centerLogo.onload = () => checkImagesLoaded();
  centerLogo.onerror = () => checkImagesLoaded();

  providers.forEach(provider => {
    const img = new Image();
    img.src = provider.logo;
    img.onload = () => checkImagesLoaded();
    img.onerror = () => checkImagesLoaded();
    provider.image = img;
  });

  function checkImagesLoaded() {
    imagesLoaded++;
    if (imagesLoaded >= providers.length + 1) {
      isReady = true;
    }
  }

  // ─────────────────────────────────────────────────────────────
  // INITIALIZE NODES — Disposition en constellation
  // ─────────────────────────────────────────────────────────────
  function initializeNodes() {
    nodes = [];

    // Dispersion des nœuds en cercles concentriques
    const circles = [
      { count: 6, radius: Math.min(width, height) * 0.15 },
      { count: 6, radius: Math.min(width, height) * 0.25 },
      { count: 6, radius: Math.min(width, height) * 0.35 }
    ];

    let providerIndex = 0;

    circles.forEach(circle => {
      const angleStep = (Math.PI * 2) / circle.count;

      for (let i = 0; i < circle.count; i++) {
        if (providerIndex >= providers.length) break;

        const angle = angleStep * i + Math.random() * 0.3;
        const provider = providers[providerIndex];

        nodes.push({
          x: centerX + Math.cos(angle) * circle.radius,
          y: centerY + Math.sin(angle) * circle.radius,
          baseX: centerX + Math.cos(angle) * circle.radius,
          baseY: centerY + Math.sin(angle) * circle.radius,
          vx: (Math.random() - 0.5) * config.animation.floatSpeed,
          vy: (Math.random() - 0.5) * config.animation.floatSpeed,
          provider: provider,
          hovered: false
        });

        providerIndex++;
      }
    });
  }

  // ─────────────────────────────────────────────────────────────
  // INITIALIZE PARTICLES
  // ─────────────────────────────────────────────────────────────
  function initializeParticles() {
    particles = [];

    for (let i = 0; i < config.animation.particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * config.animation.particleSpeed,
        vy: (Math.random() - 0.5) * config.animation.particleSpeed,
        size: Math.random() * 2 + 1,
        opacity: Math.random() * 0.3
      });
    }
  }

  // ─────────────��───────────────────────────────────────────────
  // UPDATE — Animation des nœuds et particules
  // ─────────────────────────────────────────────────────────────
  function update() {
    // Update nodes — floating effect
    nodes.forEach(node => {
      // Floating animation
      node.x += node.vx;
      node.y += node.vy;

      // Bounds avec retour progressif vers position de base
      const maxDrift = 20;
      const dx = node.x - node.baseX;
      const dy = node.y - node.baseY;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance > maxDrift) {
        node.vx = -dx * 0.01;
        node.vy = -dy * 0.01;
      }

      // Random direction changes
      if (Math.random() < 0.01) {
        node.vx = (Math.random() - 0.5) * config.animation.floatSpeed;
        node.vy = (Math.random() - 0.5) * config.animation.floatSpeed;
      }
    });

    // Update particles
    particles.forEach(particle => {
      particle.x += particle.vx;
      particle.y += particle.vy;

      // Wrap around edges
      if (particle.x < 0) particle.x = width;
      if (particle.x > width) particle.x = 0;
      if (particle.y < 0) particle.y = height;
      if (particle.y > height) particle.y = 0;
    });
  }

  // ─────────────────────────────────────────────────────────────
  // DRAW — Render la constellation
  // ─────────────────────────────────────────────────────────────
  function draw() {
    // Clear canvas
    ctx.fillStyle = config.colors.background;
    ctx.fillRect(0, 0, width, height);

    if (!isReady) {
      // Loading message
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Chargement de la constellation...', centerX, centerY);
      return;
    }

    // Draw particles
    particles.forEach(particle => {
      ctx.fillStyle = `rgba(167, 139, 250, ${particle.opacity})`;
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw connections between nodes
    ctx.strokeStyle = config.colors.lineColor;
    ctx.globalAlpha = config.colors.lineOpacity;
    ctx.lineWidth = 1;

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x;
        const dy = nodes[j].y - nodes[i].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Only draw lines between close nodes
        const maxDistance = Math.min(width, height) * 0.25;
        if (distance < maxDistance) {
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;

    // Draw nodes
    nodes.forEach(node => {
      const scale = node.hovered ? config.node.hoverScale : 1;
      const nodeColor = node.hovered ? config.colors.nodeFuchsia : config.colors.nodeViolet;

      // Draw halo
      const gradient = ctx.createRadialGradient(
        node.x, node.y, 0,
        node.x, node.y, config.node.haloRadius * scale
      );
      gradient.addColorStop(0, nodeColor + '80');
      gradient.addColorStop(1, nodeColor + '00');

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(node.x, node.y, config.node.haloRadius * scale, 0, Math.PI * 2);
      ctx.fill();

      // Draw node circle
      ctx.fillStyle = nodeColor;
      ctx.beginPath();
      ctx.arc(node.x, node.y, config.node.radius * scale, 0, Math.PI * 2);
      ctx.fill();

      // Draw logo miniature
      if (node.provider.image && node.provider.image.complete) {
        const logoSize = config.node.logoSize * scale;
        ctx.save();
        ctx.globalAlpha = 0.9;
        ctx.drawImage(
          node.provider.image,
          node.x - logoSize / 2,
          node.y - logoSize / 2,
          logoSize,
          logoSize
        );
        ctx.restore();
      }
    });

    // Draw center LILIWATT logo
    if (centerLogo.complete) {
      const logoSize = config.center.logoSize;

      // Glow effect
      const centerGradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, logoSize
      );
      centerGradient.addColorStop(0, config.colors.nodeFuchsia + '40');
      centerGradient.addColorStop(1, config.colors.nodeFuchsia + '00');

      ctx.fillStyle = centerGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, logoSize, 0, Math.PI * 2);
      ctx.fill();

      // Logo
      ctx.save();
      ctx.shadowColor = config.colors.nodeFuchsia;
      ctx.shadowBlur = 20;
      ctx.drawImage(
        centerLogo,
        centerX - logoSize / 2,
        centerY - logoSize / 2,
        logoSize,
        logoSize
      );
      ctx.restore();
    }
  }

  // ─────────────────────────────────────────────────────────────
  // ANIMATION LOOP
  // ─────────────────────────────────────────────────────────────
  function animate() {
    update();
    draw();
    requestAnimationFrame(animate);
  }

  // ─────────────────────────────────────────────────────────────
  // MOUSE HOVER — Tooltip
  // ─────────────────────────────────────────────────────────────
  function handleMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let foundHover = false;

    nodes.forEach(node => {
      const dx = mouseX - node.x;
      const dy = mouseY - node.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < config.node.haloRadius) {
        node.hovered = true;
        foundHover = true;
        hoveredNode = node;

        // Show tooltip
        tooltip.textContent = node.provider.name;
        tooltip.style.left = `${e.clientX + 15}px`;
        tooltip.style.top = `${e.clientY - 10}px`;
        tooltip.style.opacity = '1';
      } else {
        node.hovered = false;
      }
    });

    if (!foundHover) {
      tooltip.style.opacity = '0';
      hoveredNode = null;
    }

    canvas.style.cursor = foundHover ? 'pointer' : 'default';
  }

  function handleMouseLeave() {
    nodes.forEach(node => node.hovered = false);
    tooltip.style.opacity = '0';
    hoveredNode = null;
    canvas.style.cursor = 'default';
  }

  // ─────────────────────────────────────────────────────────────
  // EVENT LISTENERS
  // ─────────────────────────────────────────────────────────────
  canvas.addEventListener('mousemove', handleMouseMove);
  canvas.addEventListener('mouseleave', handleMouseLeave);
  window.addEventListener('resize', resizeCanvas);

  // ──────────────────────────────────────────────────────��──────
  // INIT
  // ─────────────────────────────────────────────────────────────
  resizeCanvas();
  animate();

})();
