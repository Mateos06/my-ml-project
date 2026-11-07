/* Motion enhances the reading order. It never captures or changes scrolling. */
(function (root) {
  'use strict';
  let active;

  function init() {
    if (active) {
      active.refresh();
      return active;
    }
    const lab = document.querySelector('.taxi-lab');
    if (!lab) return null;
    const reduced = root.matchMedia('(prefers-reduced-motion: reduce)');
    const smallScreen = root.matchMedia('(max-width: 900px)');
    const hero = lab.querySelector('.lab-hero');
    const nav = document.querySelector('.lab-nav');
    const progress = document.getElementById('reading-progress');
    const chapters = Array.from(lab.querySelector('.chapter[id]'));
    const links = Array.from(document.querySelectorAll('.lab-nav a[href^="#"]'));
    const counters = new Set();
    const reveals = new Set();
    const counterFrames = new Map();
    const listeners = [];
    let frame = 0;
    let disposed = false;
    let lastChapter = '';

    function listen(target, type, callback, options) {
      target.addEventListener(type, callback, options);
      listeners.push(() => target.removeEventListener(type, callback, options));
    }

    function finishCounter(element) {
      const target = Number(element.dataset.counter);
      if (!Number.isFinite(target)) return;
      const decimals = Math.min(4, Number(element.dataset.counterDecimals) ||
        (String(element.dataset.counter).split('.')[1] || '').length);
      element.textContent = target.toLocaleString('en-US', {
        minimumFractionDigits: decimals, maximumFractionDigits: decimals,
      });
      element.dataset.counterComplete = 'true';
      if (counterFrames.has(element)) {
        root.cancelAnimationFrame(counterFrames.get(element));
        counterFrames.delete(element);
      }
    }

    function animateCounter(element) {
      if (element.dataset.counterComplete === 'true') return;
      const target = Number(element.dataset.counter);
      if (!Number.isFinite(target)) return;
      if (reduced.matches || target < 10) {
        finishCounter(element);
        return;
      }
      // Existing DOM text contains the real result; no inferred number is used.
      const decimals = Math.min(4, Number(element.dataset.counterDecimals) ||
        (String(element.dataset.counter).split('.')[1] || '').length);
      const start = performance.now();
      const duration = 850;
      element.setAttribute('aria-label', element.textContent.trim());
      element.setAttribute('aria-live', 'off');
      const tick = (now) => {
        if (disposed || reduced.matches) {
          finishCounter(element);
          return;
        }
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        element.textContent = (target * eased).toLocaleString('en-US', {
          minimumFractionDigits: decimals, maximumFractionDigits: decimals,
        });
        if (t < 1) counterFrames.set(element, root.requestAnimationFrame(tick));
        else finishCounter(element);
      };
      counterFrames.set(element, root.requestAnimationFrame(tick));
    }

    function show(element) {
      element.classList.add('motion-visible');
      if (element.hasAttribute('data-counter')) animateCounter(element);
      observer?.unobserve(element);
    }

    const observer = 'IntersectionObserver' in root ? new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) show(entry.target);
      });
    }, { threshold: 0.07, rootMargin: '0px 0px -14px 0px' }) : null;

    function refresh() {
      if (disposed) return;
      // Animate independently readable exhibits, never an entire long chapter.
      const selector = [
        '.chapter-heading', '.target-playground', '.month-card',
        '.funnel-layout', '.payment-card', '.lesson-bar', '.chart-panel',
        '.map-layout', '.pipeline-track', '.feature-ledger', '.model-explainer',
        '.result-stat', '.decision-lab', '.predictor-layout', '.limits-grid article',
        '.failure-example', '.roadmap > details', '.reproduce-cta',
        '[data-motion-reveal]',
      ].join(',');
      Array.from(lab.querySelectorAll(selector)).forEach(element => {
        if (reveals.has(element)) return;
        reveals.add(element);
        element.classList.add('motion-reveal');
        const siblings = Array.from(element.parentElement.children).filter(sibling =>
          sibling.matches('.month-card, .payment-card, .result-stat, .failure-example, .roadmap > details, .limits-grid article'));
        const index = Math.max(0, siblings.indexOf(element));
        element.style.setProperty('--reveal-delay', `${Math.min(index, 3) * 55}ms`);
        if (observer && !reduced.matches) observer.observe(element);
        else show(element);
      });
      lab.querySelectorAll('[data-counter]').forEach(element => {
        if (counters.has(element)) return;
        counters.add(element);
        if (observer && !reduced.matches) observer.observe(element);
        else finishCounter(element);
      });
      schedule();
    }

    function update() {
      frame = 0;
      if (disposed) return;
      const scroll = root.scrollY || document.documentElement.scrollTop || 0;
      const range = Math.max(1, document.documentElement.scrollHeight - root.innerHeight);
      const fraction = Math.max(0, Math.min(1, scroll / range));
      if (progress) progress.style.transform = `scaleX(${fraction})`;
      if (nav) nav.classList.toggle('has-scrolled', scroll > 16);

      if (hero) {
        const rect = hero.getBoundingClientRect();
        const travel = Math.max(0, Math.min(rect.height, -rect.top));
        // Reduce both depth and travel on touch-sized layouts; keep content fixed.
        const amount = reduced.matches ? 0 : Math.min(smallScreen.matches ? 45 : 125,
          travel * (smallScreen.matches ? 0.08 : 0.2));
        hero.style.setProperty('--hero-parallax', `${amount.toFixed(1)}px`);
        hero.style.setProperty('--hero-depth-opacity',
          String(reduced.matches ? 1 : Math.max(0.55, 1 - travel / (rect.height * 2))));
        hero.classList.toggle('hero-in-view', rect.bottom > 0 && rect.top < root.innerHeight);
      }

      const readingLine = Math.min(230, root.innerHeight * 0.3);
      let current = '';
      chapters.forEach(chapter => {
        if (chapter.getBoundingClientRect().top <= readingLine) current = chapter.id;
      });
      if (current !== lastChapter) {
        lastChapter = current;
        const currentIndex = chapters.findIndex(chapter => chapter.id === current);
        // Map unlinked exhibits to the preceding linked chapter.
        let activeHash = '';
        for (let i = currentIndex; i >= 0; i -= 1) {
          const hash = `#${chapters[i].id}`;
          if (links.some(link => link.getAttribute('href') === hash)) {
            activeHash = hash;
            break;
          }
        }
        links.forEach(link => {
          const selected = link.getAttribute('href') === activeHash;
          link.classList.toggle('active', selected);
          if (selected) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
        chapters.forEach(chapter => chapter.classList.toggle('chapter-current', chapter.id === current));
        lab.dispatchEvent(new CustomEvent('taxi:chapter-visible', { detail: { id: current, index: currentIndex } }));
      }
    }

    function schedule() {
      if (!frame && !disposed) frame = root.requestAnimationFrame(update);
    }

    function applyPreference() {
      lab.classList.toggle('motion-enabled', !reduced.matches);
      lab.classList.toggle('motion-reduced', reduced.matches);
      if (reduced.matches) {
        reveals.forEach(element => element.classList.add('motion-visible'));
        counters.forEach(finishCounter);
      }
      schedule();
    }

    listen(root, 'scroll', schedule, { passive: true });
    listen(root, 'resize', schedule, { passive: true });
    listen(root, 'hashchange', schedule);
    listen(document, 'visibilitychange', schedule);
    listen(lab, 'focusin', event => {
      const element = event.target.closest('.motion-reveal');
      if (element) show(element);
    });
    listen(lab, 'toggle', schedule, true);
    if (reduced.addEventListener) listen(reduced, 'change', applyPreference);
    const resizeObserver = 'ResizeObserver' in root ? new ResizeObserver(schedule) : null;
    resizeObserver?.observe(lab);
    if (document.fonts?.ready) document.fonts.ready.then(schedule);
    lab.querySelectorAll('img').forEach(image => {
      if (!image.complete) listen(image, 'load', schedule, { once: true });
    });

    active = {
      refresh,
      reducedMotion: () => reduced.matches,
      dispose() {
        disposed = true;
        listeners.forEach(remove => remove());
        observer?.disconnect();
        resizeObserver?.disconnect();
        if (frame) root.cancelAnimationFrame(frame);
        counters.forEach(finishCounter);
        lab.classList.remove('motion-enabled');
        hero?.style.removeProperty('--hero-parallax');
        active = null;
      },
    };
    applyPreference();
    refresh();
    return active;
  }

  root.TaxiMotion = { init };
})(window);
