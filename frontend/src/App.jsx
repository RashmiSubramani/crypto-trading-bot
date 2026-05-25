import { useWebSocket } from "./hooks/useWebSocket";
import { useAlerts } from "./hooks/useAlerts";
import PnLCard from "./components/PnLCard";
import ActivePosition from "./components/ActivePosition";
import TradeHistory from "./components/TradeHistory";
import SignalPanel from "./components/SignalPanel";
import SignalHistory from "./components/SignalHistory";
import { Wifi, WifiOff } from "lucide-react";

const WS_URL = "ws://localhost:8000/ws";

export default function App() {
  const { data, connected } = useWebSocket(WS_URL);
  useAlerts(data);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center font-bold text-black text-sm">B</div>
          <div>
            <h1 className="font-bold text-white">Crypto Trading Bot</h1>
            <p className="text-xs text-gray-500">Powered by Claude AI • Binance Testnet</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {connected ? (
            <><Wifi size={14} className="text-green-400" /><span className="text-green-400 text-xs">Connected</span></>
          ) : (
            <><WifiOff size={14} className="text-red-400" /><span className="text-red-400 text-xs">Reconnecting...</span></>
          )}
        </div>
      </header>

      <main className="p-6 max-w-7xl mx-auto">
        {/* Top row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <PnLCard
            summary={data?.daily_summary}
            risk={data?.risk}
          />
          <div className="md:col-span-2">
            <ActivePosition
              activeTrades={data?.active_trades}
              prices={data?.prices}
            />
          </div>
        </div>

        {/* Middle row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <SignalPanel analysis={data?.analysis} />
          <TradeHistory trades={data?.recent_trades} />
        </div>

        {/* Signal History */}
        <div className="mb-4">
          <SignalHistory signals={data?.signal_history} />
        </div>

        {/* Risk info bar */}
        {data?.risk && (
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
            <div className="flex flex-wrap gap-6 text-sm">
              <div className="text-gray-400">
                Capital: <span className="text-white">${data.risk.capital_usdt ?? "—"}</span>
              </div>
              <div className="text-gray-400">
                Daily P&L: <span className={data.risk.daily_pnl >= 0 ? "text-green-400" : "text-red-400"}>
                  {data.risk.daily_pnl >= 0 ? "+" : ""}${data.risk.daily_pnl?.toFixed(2)}
                </span>
              </div>
              <div className="text-gray-400">
                Open trades: <span className="text-white">{data.risk.open_trades} / {data.risk.max_open ?? 2}</span>
              </div>
              <div className="text-gray-400">
                Trades today: <span className="text-white">{data.risk.trades_today}</span>
              </div>
              <div className="text-gray-400">
                Daily loss limit: <span className="text-red-400">-${Math.abs(data.risk.daily_loss_limit ?? 30)}</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
