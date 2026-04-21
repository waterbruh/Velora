/* Velora — Haptic Feedback Wrapper
 *
 * iOS Safari unterstützt navigator.vibrate nur auf Home-Screen-PWAs und
 * auch da begrenzt.  Wir nutzen es defensiv: wenn nicht verfügbar -> no-op.
 *
 * Usage:
 *   VeloraHaptics.light()    // 10ms, einzelner Tap
 *   VeloraHaptics.medium()   // 20ms, Action-Confirm
 *   VeloraHaptics.success()  // Double-Pulse
 *   VeloraHaptics.error()    // Lange + kurz
 */
(function () {
  function vibrate(pattern) {
    if ('vibrate' in navigator) {
      try { navigator.vibrate(pattern); } catch (_) {}
    }
  }
  window.VeloraHaptics = {
    light:   () => vibrate(10),
    medium:  () => vibrate(20),
    success: () => vibrate([10, 40, 15]),
    warn:    () => vibrate([20, 60, 20]),
    error:   () => vibrate([35, 40, 35, 40, 35]),
    selection: () => vibrate(5),
  };
})();
