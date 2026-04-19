(function() {
  const state = { step: 1, action: 'buy', ticker: '', shares: 0, price: 0, currency: 'EUR', account: '' };
  const modalEl = () => document.getElementById('tradeModal');

  const setStep = (n) => {
    state.step = n;
    document.querySelectorAll('#tradeProgress .trade-dot').forEach((d, i) => d.classList.toggle('active', i <= n - 1));
    [1, 2, 3].forEach(s => {
      const el = document.getElementById('tradeStep' + s);
      if (el) el.hidden = s !== n;
    });
    const title = n === 1 ? 'Schritt 1 von 3 - Aktion' : n === 2 ? 'Schritt 2 von 3 - Menge' : 'Schritt 3 von 3 - Vorschau';
    const titleEl = document.getElementById('tradeStepTitle');
    if (titleEl) titleEl.textContent = title;
  };

  const readStep1 = () => {
    state.action = document.querySelector('.trade-action-btn.active')?.dataset.action || 'buy';
    state.ticker = document.getElementById('tradeTicker').value.trim().toUpperCase();
  };

  const readStep2 = () => {
    state.shares = parseFloat(document.getElementById('tradeShares').value) || 0;
    state.price = parseFloat(document.getElementById('tradePrice').value) || 0;
    state.currency = document.querySelector('input[name=trade_currency]:checked')?.value || state.currency || 'EUR';
    state.account = document.getElementById('tradeAccount').value;
  };

  const renderStep2 = () => {
    document.getElementById('tradeActionWord').textContent = state.action === 'buy' ? 'kaufst' : 'verkaufst';
    document.getElementById('tradeTickerDisplay').textContent = state.ticker;
    const updateTotal = () => {
      const s = parseFloat(document.getElementById('tradeShares').value) || 0;
      const p = parseFloat(document.getElementById('tradePrice').value) || 0;
      const cur = document.querySelector('input[name=trade_currency]:checked')?.value || document.getElementById('tradePriceCur').textContent;
      document.getElementById('tradePriceCur').textContent = cur;
      document.getElementById('tradeTotal').textContent = (s * p).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ' + cur;
    };
    document.getElementById('tradeShares').oninput = updateTotal;
    document.getElementById('tradePrice').oninput = updateTotal;
    document.querySelectorAll('input[name=trade_currency]').forEach(r => r.onchange = updateTotal);
    updateTotal();
  };

  const renderStep3 = () => {
    document.getElementById('tradePreviewLabel').textContent = state.action === 'buy' ? 'KAUF' : 'VERKAUF';
    document.getElementById('tradePreviewMain').textContent = state.shares.toLocaleString('de-DE') + ' × ' + state.ticker + ' @ ' + state.price.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ' + state.currency;
    document.getElementById('tradePreviewTotal').textContent = '= ' + (state.shares * state.price).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ' + state.currency;
    const accSelect = document.getElementById('tradeAccount');
    document.getElementById('tradePreviewAccount').textContent = accSelect.options[accSelect.selectedIndex]?.text || state.account;
  };

  const open = () => {
    setStep(1);
    modalEl()?.classList.add('open');
    setTimeout(() => document.getElementById('tradeTicker')?.focus(), 80);
  };

  const close = () => { modalEl()?.classList.remove('open'); };

  const next = () => {
    if (state.step === 1) {
      readStep1();
      if (!state.ticker) { window.toast?.error('Ticker fehlt', { detail: 'Bitte einen Ticker eingeben' }); return; }
      setStep(2); renderStep2();
    } else if (state.step === 2) {
      readStep2();
      if (state.shares <= 0) { window.toast?.error('Ungueltige Menge'); return; }
      if (state.price <= 0) { window.toast?.error('Ungueltiger Preis'); return; }
      setStep(3); renderStep3();
    }
  };

  const back = () => {
    if (state.step === 2) setStep(1);
    else if (state.step === 3) { setStep(2); renderStep2(); }
  };

  const submit = () => {
    const btn = document.getElementById('tradeSubmitBtn');
    btn.classList.add('loading'); btn.disabled = true;
    const payload = { action: state.action, ticker: state.ticker, shares: state.shares, price: state.price, trade_currency: state.currency, account: state.account };
    fetch('/api/trade', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      .then(r => r.json().then(d => ({ ok: r.ok, d })))
      .then(({ ok, d }) => {
        if (ok) {
          close();
          window.toast?.success('Trade gespeichert', { detail: `${state.shares} × ${state.ticker} @ ${state.price} ${state.currency}` });
          setTimeout(() => location.reload(), 600);
        } else {
          btn.classList.remove('loading'); btn.disabled = false;
          window.toast?.error('Fehler', { detail: d.error || 'Trade konnte nicht gespeichert werden' });
        }
      })
      .catch(() => {
        btn.classList.remove('loading'); btn.disabled = false;
        window.toast?.error('Verbindungsfehler', { detail: 'Pruefe deine Netzwerkverbindung' });
      });
  };

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.trade-action-btn');
    if (btn) {
      document.querySelectorAll('.trade-action-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
    if (e.target.id === 'tradeNext1') next();
    if (e.target.id === 'tradeNext2') next();
    if (e.target.id === 'tradeBack2') back();
    if (e.target.id === 'tradeBack3') back();
    if (e.target.id === 'tradeSubmitBtn') submit();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalEl()?.classList.contains('open')) close();
  });

  if (new URLSearchParams(location.search).get('trade') === '1') {
    document.addEventListener('DOMContentLoaded', open);
  }

  window.TradeModal = { open, close, next, back, submit };
})();
