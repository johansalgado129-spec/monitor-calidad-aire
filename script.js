(() => {
  const deck = document.getElementById('deck');
  const slides = [...document.querySelectorAll('.slide')];
  const dots = [...document.querySelectorAll('.dot')];
  const counter = document.getElementById('counter');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const fullscreenBtn = document.getElementById('fullscreenBtn');
  const dialog = document.getElementById('imageDialog');
  const dialogImage = document.getElementById('dialogImage');
  const dialogCaption = document.getElementById('dialogCaption');
  const closeDialog = document.getElementById('closeDialog');
  let current = 0;

  function goTo(index) {
    current = Math.max(0, Math.min(slides.length - 1, index));
    slides[current].scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block:'start'});
    updateNav();
  }

  function updateNav() {
    dots.forEach((dot, i) => dot.classList.toggle('active', i === current));
    counter.textContent = `${current + 1} / ${slides.length}`;
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === slides.length - 1;
  }

  dots.forEach((dot, i) => dot.addEventListener('click', () => goTo(i)));
  prevBtn.addEventListener('click', () => goTo(current - 1));
  nextBtn.addEventListener('click', () => goTo(current + 1));

  document.addEventListener('keydown', (e) => {
    if (dialog.open) {
      if (e.key === 'Escape') dialog.close();
      return;
    }
    if (['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)) { e.preventDefault(); goTo(current + 1); }
    if (['ArrowLeft','ArrowUp','PageUp'].includes(e.key)) { e.preventDefault(); goTo(current - 1); }
    if (e.key === 'Home') { e.preventDefault(); goTo(0); }
    if (e.key === 'End') { e.preventDefault(); goTo(slides.length - 1); }
  });

  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter(e => e.isIntersecting).sort((a,b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    const idx = slides.indexOf(visible.target);
    if (idx >= 0) { current = idx; updateNav(); }
  }, {root: deck, threshold:[0.5,0.7]});
  slides.forEach(s => observer.observe(s));

  document.querySelectorAll('[data-image]').forEach(btn => {
    btn.addEventListener('click', () => {
      dialogImage.src = btn.dataset.image;
      dialogImage.alt = btn.dataset.caption || 'Evidencia ampliada';
      dialogCaption.textContent = btn.dataset.caption || '';
      if (typeof dialog.showModal === 'function') dialog.showModal();
    });
  });
  closeDialog.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });

  fullscreenBtn.addEventListener('click', async () => {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch (_) {}
  });
  document.addEventListener('fullscreenchange', () => {
    fullscreenBtn.textContent = document.fullscreenElement ? 'Salir' : 'Presentar';
  });

  updateNav();
})();
