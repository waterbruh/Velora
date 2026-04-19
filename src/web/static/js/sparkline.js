/* Velora sparkline: tiny inline SVG trend renderer with auto-mount via data attribute. */
(function() {
  function render(el, data, opts) {
    opts = opts || {};
    if (!el || !Array.isArray(data) || data.length < 2) return;
    const width = opts.width != null ? opts.width : 80;
    const height = opts.height != null ? opts.height : 24;
    const pad = 2;
    const w = width - pad * 2;
    const h = height - pad * 2;
    const min = Math.min.apply(null, data);
    const max = Math.max.apply(null, data);
    const range = max - min || 1;
    const pts = data.map((v, i) => ({
      x: pad + (i / (data.length - 1)) * w,
      y: pad + h - ((v - min) / range) * h,
    }));
    const isPositive = data[data.length - 1] >= data[0];
    const stroke = (!opts.stroke || opts.stroke === 'auto')
      ? (isPositive ? 'var(--gain)' : 'var(--loss)')
      : opts.stroke;
    const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
    const last = pts[pts.length - 1];
    el.innerHTML = `<svg class="sparkline" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" aria-hidden="true"><path d="${d}" stroke="${stroke}" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="${last.x.toFixed(1)}" cy="${last.y.toFixed(1)}" r="2" fill="${stroke}"/></svg>`;
  }

  function autoRender() {
    document.querySelectorAll('[data-sparkline]').forEach(el => {
      try {
        const data = JSON.parse(el.getAttribute('data-sparkline'));
        const opts = {
          width: parseInt(el.dataset.width, 10) || 80,
          height: parseInt(el.dataset.height, 10) || 24,
          stroke: el.dataset.stroke || 'auto',
        };
        render(el, data, opts);
      } catch (e) { /* ignore malformed */ }
    });
  }

  window.Sparkline = { render, autoRender };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoRender);
  } else {
    autoRender();
  }
})();
