/* Velora toast system: glass notifications with auto-dismiss + progress bar. */
(function() {
  const ICONS = { success: '\u2713', error: '\u00D7', warn: '\u26A0', info: '\u2139' };
  let stack;

  function ensureStack() {
    if (!stack || !document.body.contains(stack)) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    return stack;
  }

  function show(type, title, opts) {
    opts = opts || {};
    const el = document.createElement('div');
    el.className = 'toast ' + type;
    const duration = opts.duration != null
      ? opts.duration
      : (type === 'error' || type === 'warn' ? 6000 : 4000);
    el.innerHTML = `
      <span class="toast-icon">${ICONS[type] || ''}</span>
      <div class="toast-body">
        <div class="toast-title"></div>
        ${opts.detail ? '<div class="toast-detail"></div>' : ''}
      </div>
      <button class="toast-close" aria-label="Close">\u00D7</button>
      <span class="toast-progress" style="animation-duration: ${duration}ms;"></span>
    `;
    el.querySelector('.toast-title').textContent = title;
    if (opts.detail) el.querySelector('.toast-detail').textContent = opts.detail;

    const remove = () => {
      el.classList.add('removing');
      setTimeout(() => { if (el.parentNode) el.remove(); }, 220);
    };
    el.querySelector('.toast-close').addEventListener('click', remove);
    ensureStack().appendChild(el);
    while (stack.children.length > 3) stack.firstElementChild.remove();
    const timer = setTimeout(remove, duration);
    el.addEventListener('click', (e) => {
      if (e.target.closest('.toast-close')) return;
      clearTimeout(timer);
      remove();
    });
    return el;
  }

  window.toast = {
    success: (t, o) => show('success', t, o),
    error:   (t, o) => show('error',   t, o),
    warn:    (t, o) => show('warn',    t, o),
    info:    (t, o) => show('info',    t, o),
  };
})();
