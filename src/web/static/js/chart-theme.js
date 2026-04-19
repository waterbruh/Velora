/* Velora chart theme: live CSS-token readers + palette for Chart.js / ApexCharts / TradingView. */
(function() {
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const isDark = () => window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

  window.VeloraChartTheme = {
    colors: ['#22d3ee', '#6366f1', '#3b82f6', '#8b5cf6', '#fbbf24', '#0891b2', '#f472b6', '#94a3b8', '#f87171'],
    bg:          () => css('--bg-canvas'),
    bodyBg:      () => css('--bg-body'),
    text:        () => css('--text-secondary'),
    textPrimary: () => css('--text-primary'),
    textMuted:   () => css('--text-muted'),
    accent:      () => css('--accent'),
    accentBg:    () => css('--accent-bg'),
    grid:        () => isDark() ? 'rgba(255,255,255,0.06)' : 'rgba(10,20,40,0.08)',
    border:      () => isDark() ? 'rgba(255,255,255,0.10)' : 'rgba(10,20,40,0.10)',
    tooltipBg:   () => isDark() ? 'rgba(10,15,31,0.92)' : 'rgba(255,255,255,0.95)',
    tooltipBorder: () => isDark() ? 'rgba(255,255,255,0.12)' : 'rgba(10,20,40,0.10)',
    green:       () => css('--gain'),
    red:         () => css('--loss'),
    yellow:      () => css('--warn'),
  };

  window.VeloraApex = {
    baseOptions() {
      const dark = isDark();
      return {
        chart: {
          foreColor: window.VeloraChartTheme.text(),
          toolbar: { show: false },
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
          background: 'transparent',
          animations: {
            enabled: true,
            easing: 'easeout',
            speed: 600,
            animateGradually: { enabled: true, delay: 80 },
          },
        },
        theme: { mode: dark ? 'dark' : 'light' },
        grid: {
          borderColor: window.VeloraChartTheme.grid(),
          strokeDashArray: 4,
          xaxis: { lines: { show: false } },
        },
        tooltip: {
          theme: dark ? 'dark' : 'light',
          style: { fontSize: '12px', fontFamily: 'Inter' },
          marker: { show: true },
        },
        colors: window.VeloraChartTheme.colors,
        dataLabels: { enabled: false },
        legend: {
          labels: { colors: window.VeloraChartTheme.text() },
          fontFamily: 'Inter',
          fontSize: '12px',
        },
        stroke: { curve: 'smooth', width: 2 },
      };
    },
  };
})();
