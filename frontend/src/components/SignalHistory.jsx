import { useState } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell
} from "recharts";
import { TrendingUp, TrendingDown, Minus, Zap, BarChart2, Activity, CheckCircle, XCircle } from "lucide-react";

const COIN_COLORS = {
  BTCUSDT: "#f59e0b",
  ETHUSDT: "#6366f1",
  SOLUSDT: "#8b5cf6",
  XRPUSDT: "#06b6d4",
  DOGEUSDT: "#ec4899",
  TRXUSDT: "#10b981",
};

function getColor(symbol) {
  return COIN_COLORS[symbol] || "#94a3b8";
}

function formatTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: true });
}

// ── Score Timeline Chart ──────────────────────────────────────────────────────
function ScoreTimeline({ signals }) {
  const symbols = [...new Set(signals.map(s => s.symbol))];

  // Build time-indexed data: [{time, BTCUSDT: 72, SOLUSDT: 78, ...}]
  const timeMap = {};
  signals.forEach(s => {
    const t = formatTime(s.detected_at);
    if (!timeMap[t]) timeMap[t] = { time: t };
    timeMap[t][s.symbol] = s.ai_score;
    if (s.acted_on) timeMap[t][`${s.symbol}_traded`] = s.ai_score;
  });
  const data = Object.values(timeMap).reverse();

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 text-xs shadow-xl">
        <p className="text-gray-400 mb-2">{label}</p>
        {payload.map((p, i) => (
          <div key={i} className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-gray-300">{p.dataKey}:</span>
            <span className="font-bold" style={{ color: p.color }}>{p.value}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={15} className="text-blue-400" />
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">AI Score Timeline</h3>
        <span className="ml-auto text-xs text-gray-600">per 15m candle</span>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 10 }} />
          <YAxis domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={75} stroke="#22c55e" strokeDasharray="4 4" label={{ value: "Trade zone", fill: "#22c55e", fontSize: 10 }} />
          <ReferenceLine y={50} stroke="#eab308" strokeDasharray="4 4" label={{ value: "Weak", fill: "#eab308", fontSize: 10 }} />
          <Legend wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
          {symbols.map(sym => (
            <Line
              key={sym}
              type="monotone"
              dataKey={sym}
              stroke={getColor(sym)}
              strokeWidth={2}
              dot={{ r: 3, fill: getColor(sym) }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Pattern Frequency Chart ───────────────────────────────────────────────────
function PatternFrequency({ signals }) {
  const counts = {};
  signals.forEach(s => {
    s.patterns?.split(", ").forEach(p => {
      if (p) counts[p] = (counts[p] || 0) + 1;
    });
  });

  const data = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, count]) => ({ name: name.replace(" ", "\n"), count }));

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <BarChart2 size={15} className="text-purple-400" />
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Pattern Frequency</h3>
        <span className="ml-auto text-xs text-gray-600">top 10</span>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="name" tick={{ fill: "#6b7280", fontSize: 9 }} angle={-35} textAnchor="end" />
          <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#9ca3af" }}
            itemStyle={{ color: "#a78bfa" }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={`hsl(${260 + i * 15}, 70%, ${55 + i * 2}%)`} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Score Distribution Chart ──────────────────────────────────────────────────
function ScoreDistribution({ signals }) {
  const bands = [
    { label: "0–49\nPoor", range: [0, 49], color: "#ef4444" },
    { label: "50–74\nWeak", range: [50, 74], color: "#eab308" },
    { label: "75–84\nGood", range: [75, 84], color: "#22c55e" },
    { label: "85–100\nExcellent", range: [85, 100], color: "#10b981" },
  ];

  const data = bands.map(b => ({
    label: b.label,
    count: signals.filter(s => s.ai_score >= b.range[0] && s.ai_score <= b.range[1]).length,
    color: b.color,
  }));

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Zap size={15} className="text-yellow-400" />
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Score Distribution</h3>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="label" tick={{ fill: "#6b7280", fontSize: 10 }} />
          <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#9ca3af" }}
          />
          <Bar dataKey="count" radius={[6, 6, 0, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.color} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Signal Log ────────────────────────────────────────────────────────────────
function SignalLog({ signals }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={15} className="text-gray-400" />
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Signal Log</h3>
        <span className="ml-auto text-xs text-gray-600">{signals.length} total</span>
      </div>
      <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
        {signals.map((s, i) => (
          <div key={i} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs border ${
            s.acted_on ? "bg-green-900/10 border-green-800/40" : "bg-gray-800/40 border-gray-800"
          }`}>
            <span className="text-gray-600 w-16 shrink-0">{formatTime(s.detected_at)}</span>
            <span className="font-semibold text-white w-20 shrink-0">{s.symbol}</span>
            <span className={`font-bold w-8 shrink-0 ${s.ai_score >= 75 ? "text-green-400" : s.ai_score >= 50 ? "text-yellow-400" : "text-red-400"}`}>
              {s.ai_score}
            </span>
            <span className="text-gray-500 flex-1 truncate">{s.patterns}</span>
            {s.direction === "bullish" ? <TrendingUp size={11} className="text-green-400 shrink-0" /> :
             s.direction === "bearish" ? <TrendingDown size={11} className="text-red-400 shrink-0" /> :
             <Minus size={11} className="text-gray-600 shrink-0" />}
            {s.acted_on
              ? <CheckCircle size={11} className="text-green-400 shrink-0" />
              : <XCircle size={11} className="text-gray-600 shrink-0" />}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Export ───────────────────────────────────────────────────────────────
export default function SignalHistory({ signals }) {
  const [tab, setTab] = useState("charts");

  if (!signals || signals.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <Zap size={15} className="text-yellow-400" />
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider">Market History</h2>
        </div>
        <p className="text-gray-600 text-sm">No signals yet — waiting for first candle...</p>
      </div>
    );
  }

  const traded = signals.filter(s => s.acted_on).length;
  const avgScore = Math.round(signals.reduce((a, s) => a + s.ai_score, 0) / signals.length);
  const topScore = Math.max(...signals.map(s => s.ai_score));

  return (
    <div>
      {/* Section header + stats */}
      <div className="flex items-center gap-4 mb-4 flex-wrap">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-yellow-400" />
          <h2 className="text-white font-semibold">Market History</h2>
        </div>
        <div className="flex gap-3 ml-auto flex-wrap text-xs">
          <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-center">
            <div className="text-gray-500">Signals</div>
            <div className="text-white font-bold text-base">{signals.length}</div>
          </div>
          <div className="bg-gray-900 border border-green-800 rounded-lg px-3 py-2 text-center">
            <div className="text-gray-500">Traded</div>
            <div className="text-green-400 font-bold text-base">{traded}</div>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-center">
            <div className="text-gray-500">Avg Score</div>
            <div className={`font-bold text-base ${avgScore >= 75 ? "text-green-400" : avgScore >= 50 ? "text-yellow-400" : "text-red-400"}`}>{avgScore}</div>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-center">
            <div className="text-gray-500">Best Score</div>
            <div className="text-blue-400 font-bold text-base">{topScore}</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        {["charts", "log"].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
              tab === t ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}>
            {t === "charts" ? "Charts" : "Signal Log"}
          </button>
        ))}
      </div>

      {tab === "charts" ? (
        <div className="space-y-4">
          <ScoreTimeline signals={signals} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <PatternFrequency signals={signals} />
            <ScoreDistribution signals={signals} />
          </div>
        </div>
      ) : (
        <SignalLog signals={signals} />
      )}
    </div>
  );
}
