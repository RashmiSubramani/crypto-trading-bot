import { TrendingUp, TrendingDown, Activity } from "lucide-react";

export default function PnLCard({ summary, risk }) {
  const pnl = summary?.total_pnl ?? 0;
  const wins = summary?.wins ?? 0;
  const losses = summary?.losses ?? 0;
  const total = summary?.total ?? 0;
  const winRate = total > 0 ? ((wins / total) * 100).toFixed(0) : 0;
  const isProfit = pnl >= 0;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Today's P&L</h2>
        <Activity size={16} className="text-gray-500" />
      </div>

      <div className={`text-3xl font-bold mb-1 ${isProfit ? "text-green-400" : "text-red-400"}`}>
        {isProfit ? "+" : ""}${pnl.toFixed(2)}
      </div>

      <div className="flex gap-4 mt-3 text-sm">
        <div className="flex items-center gap-1 text-green-400">
          <TrendingUp size={14} />
          <span>{wins}W</span>
        </div>
        <div className="flex items-center gap-1 text-red-400">
          <TrendingDown size={14} />
          <span>{losses}L</span>
        </div>
        <div className="text-gray-400">{total} trades</div>
        <div className="text-yellow-400">{winRate}% win rate</div>
      </div>

      {risk?.trading_halted && (
        <div className="mt-3 bg-red-900/40 border border-red-700 rounded-lg px-3 py-2 text-red-400 text-xs">
          TRADING HALTED — {risk.halt_reason}
        </div>
      )}

      {!risk?.trading_halted && (
        <div className="mt-3 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-green-400 text-xs">Bot Active</span>
          {risk?.testnet && (
            <span className="ml-2 bg-yellow-900/40 border border-yellow-700 text-yellow-400 text-xs px-2 py-0.5 rounded">
              TESTNET
            </span>
          )}
        </div>
      )}
    </div>
  );
}
