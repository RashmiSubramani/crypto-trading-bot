import { Brain, TrendingUp, TrendingDown, Minus, Clock } from "lucide-react";
import { useState, useEffect } from "react";

function CandleCountdown() {
  const [secondsLeft, setSecondsLeft] = useState(0);

  useEffect(() => {
    function calc() {
      const now = new Date();
      const seconds = now.getMinutes() * 60 + now.getSeconds();
      const interval = 15 * 60;
      return interval - (seconds % interval);
    }
    setSecondsLeft(calc());
    const timer = setInterval(() => setSecondsLeft(calc()), 1000);
    return () => clearInterval(timer);
  }, []);

  const m = Math.floor(secondsLeft / 60);
  const s = secondsLeft % 60;
  const urgent = secondsLeft <= 60;

  return (
    <div className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-md ${urgent ? "bg-yellow-900/40 text-yellow-400" : "bg-gray-800 text-gray-400"}`}>
      <Clock size={11} />
      <span>Next candle: <span className="font-mono font-semibold">{m}m {String(s).padStart(2, "0")}s</span></span>
    </div>
  );
}

export default function SignalPanel({ analysis }) {
  if (!analysis || analysis.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Live Analysis</h2>
          <CandleCountdown />
        </div>
        <p className="text-gray-600 text-sm">Waiting for market data...</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-purple-400" />
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Live Analysis</h2>
        </div>
        <CandleCountdown />
      </div>
      <div className="space-y-4">
        {analysis.map((item, i) => {
          const ind = item.indicators || {};
          const trend = item.trend_indicators || {};
          const patterns = item.patterns || [];

          return (
            <div key={i} className="border border-gray-700 rounded-lg p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-white font-bold text-lg">{item.symbol}</span>
                  <span className="text-gray-400 text-sm">${item.price?.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-1">
                  {ind.ema_trend === "bullish" ? (
                    <TrendingUp size={14} className="text-green-400" />
                  ) : ind.ema_trend === "bearish" ? (
                    <TrendingDown size={14} className="text-red-400" />
                  ) : (
                    <Minus size={14} className="text-gray-400" />
                  )}
                  <span className={`text-xs ${ind.ema_trend === "bullish" ? "text-green-400" : ind.ema_trend === "bearish" ? "text-red-400" : "text-gray-400"}`}>
                    {ind.ema_trend || "sideways"}
                  </span>
                </div>
              </div>

              {/* Patterns */}
              {patterns.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs text-gray-500 mb-1">Detected Patterns</div>
                  <div className="flex flex-wrap gap-1">
                    {patterns.map((p, j) => (
                      <span key={j} className={`text-xs px-2 py-0.5 rounded border ${
                        p.direction === "bullish"
                          ? "border-green-700 bg-green-900/30 text-green-400"
                          : p.direction === "bearish"
                          ? "border-red-700 bg-red-900/30 text-red-400"
                          : "border-gray-600 bg-gray-800 text-gray-400"
                      }`}>
                        {p.pattern}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Indicators grid */}
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">RSI</div>
                  <div className={`font-medium ${ind.rsi > 70 ? "text-red-400" : ind.rsi < 30 ? "text-green-400" : "text-white"}`}>
                    {ind.rsi}
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">MACD</div>
                  <div className={`font-medium ${ind.macd_hist > 0 ? "text-green-400" : "text-red-400"}`}>
                    {ind.macd_crossover !== "none" ? `↑ ${ind.macd_crossover}` : ind.macd_hist?.toFixed(4)}
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Supertrend</div>
                  <div className={`font-medium ${ind.supertrend_direction === "bullish" ? "text-green-400" : "text-red-400"}`}>
                    {ind.supertrend_direction}
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Volume</div>
                  <div className={`font-medium ${ind.volume_spike ? "text-yellow-400" : "text-white"}`}>
                    {ind.volume_spike ? "SPIKE" : "Normal"}
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">vs VWAP</div>
                  <div className={`font-medium ${ind.price_vs_vwap === "above" ? "text-green-400" : "text-red-400"}`}>
                    {ind.price_vs_vwap}
                  </div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">1h Trend</div>
                  <div className={`font-medium ${trend.ema_trend === "bullish" ? "text-green-400" : trend.ema_trend === "bearish" ? "text-red-400" : "text-gray-400"}`}>
                    {trend.ema_trend || "—"}
                  </div>
                </div>
              </div>

              {/* S/R */}
              <div className="mt-2 flex gap-3 text-xs text-gray-400">
                <span>Support: <span className="text-green-400">${ind.support}</span></span>
                <span>Resistance: <span className="text-red-400">${ind.resistance}</span></span>
              </div>

              {/* AI Score */}
              {item.ai_score !== undefined && (
                <div className="mt-3 border-t border-gray-700 pt-3">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">AI Score</span>
                      <span className={`text-sm font-bold ${item.ai_score >= 75 ? "text-green-400" : item.ai_score >= 50 ? "text-yellow-400" : "text-red-400"}`}>
                        {item.ai_score}/100
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                        item.ai_direction === "bullish" ? "bg-green-900/40 text-green-400" :
                        item.ai_direction === "bearish" ? "bg-red-900/40 text-red-400" :
                        "bg-gray-800 text-gray-400"
                      }`}>
                        {item.ai_direction?.toUpperCase()}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded ${item.ai_above_threshold ? "bg-green-900/40 text-green-400" : "bg-gray-800 text-gray-500"}`}>
                        {item.ai_above_threshold ? "TRADE" : "SKIP"}
                      </span>
                    </div>
                  </div>
                  {/* Score bar */}
                  <div className="w-full bg-gray-800 rounded-full h-1.5">
                    <div className={`h-1.5 rounded-full ${item.ai_score >= 75 ? "bg-green-500" : item.ai_score >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                      style={{ width: `${item.ai_score}%` }} />
                  </div>
                  {item.ai_reasoning && (
                    <p className="text-xs text-gray-500 mt-2 italic">{item.ai_reasoning}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
