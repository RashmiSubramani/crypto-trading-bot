import { TrendingUp, TrendingDown, Clock, CheckCircle, XCircle } from "lucide-react";

function formatTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true });
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

export default function TradeHistory({ trades }) {
  if (!trades || trades.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Clock size={15} className="text-gray-500" />
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Trade History</h2>
        </div>
        <p className="text-gray-600 text-sm">No trades yet</p>
      </div>
    );
  }

  const closed = trades.filter(t => t.status === "closed");
  const totalPnl = closed.reduce((a, t) => a + (t.pnl ?? 0), 0);
  const wins = closed.filter(t => t.pnl > 0).length;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock size={15} className="text-gray-500" />
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Trade History</h2>
        </div>
        {closed.length > 0 && (
          <div className="flex items-center gap-3 text-xs">
            <span className="text-gray-500">{closed.length} closed</span>
            <span className={totalPnl >= 0 ? "text-green-400 font-semibold" : "text-red-400 font-semibold"}>
              {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
            </span>
            <span className="text-gray-500">{wins}W / {closed.length - wins}L</span>
          </div>
        )}
      </div>

      {/* Trade Cards */}
      <div className="space-y-2 max-h-[52rem] overflow-y-auto pr-1 scrollbar-thin">
        {trades.map((t, i) => {
          const pnl = t.pnl ?? 0;
          const isProfit = pnl >= 0;
          const isOpen = t.status === "open";
          const patterns = t.patterns?.split(", ") || [];

          return (
            <div key={i} className={`rounded-xl border p-3 ${
              isOpen ? "border-yellow-700/50 bg-yellow-900/5"
              : isProfit ? "border-green-800/50 bg-green-900/5"
              : "border-red-800/50 bg-red-900/5"
            }`}>
              {/* Top row */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {t.side === "BUY"
                    ? <TrendingUp size={14} className="text-green-400" />
                    : <TrendingDown size={14} className="text-red-400" />
                  }
                  <span className="text-white font-bold text-sm">{t.symbol}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                    t.side === "BUY" ? "bg-green-900/40 text-green-400" : "bg-red-900/40 text-red-400"
                  }`}>{t.side}</span>
                  {isOpen
                    ? <span className="text-xs bg-yellow-900/40 border border-yellow-700 text-yellow-400 px-2 py-0.5 rounded">OPEN</span>
                    : isProfit
                      ? <span className="flex items-center gap-1 text-xs bg-green-900/40 border border-green-700 text-green-400 px-2 py-0.5 rounded"><CheckCircle size={9} /> WIN</span>
                      : <span className="flex items-center gap-1 text-xs bg-red-900/40 border border-red-700 text-red-400 px-2 py-0.5 rounded"><XCircle size={9} /> LOSS</span>
                  }
                </div>
                <div className={`text-base font-bold ${isOpen ? "text-yellow-400" : isProfit ? "text-green-400" : "text-red-400"}`}>
                  {isOpen ? "..." : `${isProfit ? "+" : ""}$${pnl.toFixed(2)}`}
                </div>
              </div>

              {/* Price row */}
              <div className="grid grid-cols-4 gap-2 text-xs mb-2">
                <div className="bg-gray-800/60 rounded-lg p-2">
                  <div className="text-gray-500 mb-0.5">Entry</div>
                  <div className="text-white font-medium">${t.entry_price?.toFixed(2)}</div>
                </div>
                <div className="bg-gray-800/60 rounded-lg p-2">
                  <div className="text-gray-500 mb-0.5">Exit</div>
                  <div className="text-white font-medium">{t.exit_price ? `$${t.exit_price.toFixed(2)}` : "—"}</div>
                </div>
                <div className="bg-gray-800/60 rounded-lg p-2">
                  <div className="text-gray-500 mb-0.5">SL</div>
                  <div className="text-red-400 font-medium">${t.stop_loss?.toFixed(2)}</div>
                </div>
                <div className="bg-gray-800/60 rounded-lg p-2">
                  <div className="text-gray-500 mb-0.5">TP</div>
                  <div className="text-green-400 font-medium">${t.take_profit?.toFixed(2)}</div>
                </div>
              </div>

              {/* Bottom row */}
              <div className="flex items-center justify-between text-xs">
                <div className="flex flex-wrap gap-1">
                  {patterns.map((p, j) => (
                    <span key={j} className="bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">{p}</span>
                  ))}
                </div>
                <div className="flex items-center gap-2 text-gray-500 shrink-0 ml-2">
                  <span className={`px-1.5 py-0.5 rounded font-medium ${t.ai_score >= 75 ? "bg-green-900/30 text-green-400" : "bg-gray-800 text-gray-400"}`}>
                    AI {t.ai_score}
                  </span>
                  <span>{formatTime(t.opened_at)} · {formatDate(t.opened_at)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
