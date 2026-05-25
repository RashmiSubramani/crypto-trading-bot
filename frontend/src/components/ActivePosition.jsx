import { ArrowUpCircle, ArrowDownCircle } from "lucide-react";

export default function ActivePosition({ activeTrades, prices }) {
  if (!activeTrades || activeTrades.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-3">Active Positions</h2>
        <p className="text-gray-600 text-sm">No open positions</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-3">
        Active Positions ({activeTrades.length})
      </h2>
      <div className="space-y-3">
        {activeTrades.map((trade, i) => {
          const currentPrice = prices?.[trade.symbol] ?? trade.entry;
          const unrealized =
            trade.side === "BUY"
              ? (currentPrice - trade.entry) * trade.quantity
              : (trade.entry - currentPrice) * trade.quantity;
          const isProfit = unrealized >= 0;

          return (
            <div key={i} className="border border-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {trade.side === "BUY" ? (
                    <ArrowUpCircle size={16} className="text-green-400" />
                  ) : (
                    <ArrowDownCircle size={16} className="text-red-400" />
                  )}
                  <span className="text-white font-medium">{trade.symbol}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${trade.side === "BUY" ? "bg-green-900/40 text-green-400" : "bg-red-900/40 text-red-400"}`}>
                    {trade.side}
                  </span>
                </div>
                <span className={`font-semibold ${isProfit ? "text-green-400" : "text-red-400"}`}>
                  {isProfit ? "+" : ""}${unrealized.toFixed(2)}
                </span>
              </div>
              <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-gray-400">
                <div>Entry: <span className="text-white">${trade.entry?.toFixed(2)}</span></div>
                <div>SL: <span className="text-red-400">${trade.sl?.toFixed(2)}</span></div>
                <div>TP: <span className="text-green-400">${trade.tp?.toFixed(2)}</span></div>
                <div>Qty: <span className="text-white">{trade.quantity}</span></div>
                <div>Value: <span className="text-white">${(trade.entry * trade.quantity)?.toFixed(2)}</span></div>
                <div>Current: <span className="text-white">${prices?.[trade.symbol]?.toFixed(2) ?? "—"}</span></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
