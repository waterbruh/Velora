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

  const isMobile = () => window.matchMedia && window.matchMedia('(max-width: 767.98px)').matches;

  window.VeloraApex = {
    baseOptions() {
      const dark = isDark();
      const mobile = isMobile();
      return {
        chart: {
          foreColor: window.VeloraChartTheme.text(),
          toolbar: { show: false },
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
          background: 'transparent',
          width: '100%',
          // Mobile: Animationen reduzieren (weniger GPU-Last, schnelleres Initial-Paint)
          animations: mobile ? {
            enabled: false,
          } : {
            enabled: true,
            easing: 'easeout',
            speed: 600,
            animateGradually: { enabled: true, delay: 80 },
          },
          redrawOnWindowResize: true,
          redrawOnParentResize: true,
        },
        theme: { mode: dark ? 'dark' : 'light' },
        grid: {
          borderColor: window.VeloraChartTheme.grid(),
          strokeDashArray: 4,
          xaxis: { lines: { show: false } },
          padding: mobile ? { left: 4, right: 4, top: 0, bottom: 0 } : undefined,
        },
        tooltip: {
          theme: dark ? 'dark' : 'light',
          style: { fontSize: mobile ? '11px' : '12px', fontFamily: 'Inter' },
          marker: { show: true },
        },
        colors: window.VeloraChartTheme.colors,
        dataLabels: { enabled: false },
        legend: {
          labels: { colors: window.VeloraChartTheme.text() },
          fontFamily: 'Inter',
          fontSize: mobile ? '10px' : '12px',
          markers: { width: mobile ? 8 : 10, height: mobile ? 8 : 10 },
          itemMargin: mobile ? { horizontal: 6, vertical: 2 } : undefined,
        },
        stroke: { curve: 'smooth', width: 2 },
        responsive: [{
          breakpoint: 480,
          options: {
            chart: { height: 200 },
            legend: { fontSize: '9px', position: 'bottom' },
            plotOptions: { pie: { donut: { size: '60%' } } },
          },
        }],
      };
    },
    isMobile,
  };
})();
