import { useEffect, useRef } from "react";

function playTone(frequency, duration, type = "sine", volume = 0.3) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);
    gainNode.gain.setValueAtTime(volume, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + duration);
  } catch (e) {}
}

// 🔔 Candle closed — soft double beep
function playCandleSound() {
  playTone(520, 0.12, "sine", 0.2);
  setTimeout(() => playTone(620, 0.12, "sine", 0.2), 150);
}

// 📈 Pattern detected — ascending 3-tone chime
function playPatternSound() {
  playTone(440, 0.15, "triangle", 0.25);
  setTimeout(() => playTone(550, 0.15, "triangle", 0.25), 180);
  setTimeout(() => playTone(660, 0.2, "triangle", 0.3), 360);
}

// 🚀 Trade placed — triumphant ascending chord
function playTradeSound() {
  playTone(523, 0.3, "sine", 0.35);
  setTimeout(() => playTone(659, 0.3, "sine", 0.35), 100);
  setTimeout(() => playTone(784, 0.4, "sine", 0.4), 200);
  setTimeout(() => playTone(1047, 0.5, "sine", 0.35), 350);
}

// ❌ Stop loss hit — descending warning tone
function playStopLossSound() {
  playTone(440, 0.2, "sawtooth", 0.25);
  setTimeout(() => playTone(330, 0.2, "sawtooth", 0.25), 220);
  setTimeout(() => playTone(220, 0.3, "sawtooth", 0.3), 440);
}

export function useAlerts(data) {
  const prevSignalCount = useRef(0);
  const prevTradeCount = useRef(0);
  const prevActiveCount = useRef(0);
  const lastCandleTime = useRef(null);

  useEffect(() => {
    if (!data) return;

    const signals = data.signal_history || [];
    const trades = data.recent_trades || [];
    const active = data.active_trades || [];

    // ── Candle closed alert (new signal appeared) ──────────────────────────
    if (signals.length > prevSignalCount.current && prevSignalCount.current > 0) {
      const newSignals = signals.slice(0, signals.length - prevSignalCount.current);
      const hasPattern = newSignals.some(s => s.patterns && s.patterns.length > 0);
      if (hasPattern) {
        playPatternSound();
      } else {
        playCandleSound();
      }
    }
    prevSignalCount.current = signals.length;

    // ── New trade placed ───────────────────────────────────────────────────
    if (trades.length > prevTradeCount.current && prevTradeCount.current > 0) {
      playTradeSound();
    }
    prevTradeCount.current = trades.length;

    // ── Active trade closed (stop loss or take profit hit) ─────────────────
    if (active.length < prevActiveCount.current && prevActiveCount.current > 0) {
      // Check if last closed trade was a loss
      const lastTrade = trades[0];
      if (lastTrade?.pnl < 0) {
        playStopLossSound();
      } else {
        playTradeSound();
      }
    }
    prevActiveCount.current = active.length;

  }, [data]);
}
