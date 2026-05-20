import { useState, useEffect } from "react"
import axios from "axios"

const API = "http://localhost:8000"

function OutlookBadge({ outlook }) {
  const cls = `outlook-badge outlook-${outlook || "neutral"}`
  const icons = { bullish: "▲", bearish: "▼", neutral: "◆" }
  return (
    <span className={cls}>
      {icons[outlook] || "◆"} {outlook?.toUpperCase() || "—"}
    </span>
  )
}

function AgentCard({ data }) {
  if (!data) return <div className="card"><div className="loading">_ initialising agents...</div></div>

  const agents = [
    {
      name: "Market analyst",
      icon: "📈",
      bg: "rgba(26,107,204,0.12)",
      color: "#4da6ff",
      status: `Regime: ${data.market?.regime || "—"}`,
      conf: data.market?.confidence || 0,
    },
    {
      name: "Sentiment agent",
      icon: "💬",
      bg: "rgba(0,255,136,0.08)",
      color: "#00ff88",
      status: `Bearish ${Math.round((data.sentiment?.bearish || 0) * 100)}% · Bullish ${Math.round((data.sentiment?.bullish || 0) * 100)}%`,
      conf: data.sentiment?.confidence || 0,
    },
    {
      name: "Macro modeler",
      icon: "🗄️",
      bg: "rgba(10,46,26,0.4)",
      color: "#00cc66",
      status: "VAR model — 6mo horizon",
      conf: data.macro?.confidence || 0,
    },
    {
      name: "Orchestrator",
      icon: "🧠",
      bg: "rgba(77,166,255,0.08)",
      color: "#4da6ff",
      status: `${data.disagreements?.length || 0} disagreements detected`,
      conf: data.overall_confidence || 0,
    },
  ]

  return (
    <div className="card">
      <div className="card-title">Agent status</div>
      {agents.map((a) => (
        <div key={a.name} className="agent-row">
          <div className="agent-icon" style={{ background: a.bg }}>{a.icon}</div>
          <div className="agent-info">
            <div className="agent-name">{a.name}</div>
            <div className="agent-status">{a.status}</div>
            <div className="conf-bar-wrap">
              <div className="conf-bar" style={{ width: `${a.conf * 100}%`, background: a.color, boxShadow: `0 0 6px ${a.color}` }} />
            </div>
          </div>
          <div className="conf-value" style={{ color: a.color }}>{Math.round(a.conf * 100)}%</div>
        </div>
      ))}
    </div>
  )
}

function ForecastCard({ macro }) {
  if (!macro?.forecasts) return <div className="card card-blue"><div className="loading">_ loading forecasts...</div></div>

  const rows = [
    { label: "GDP", key: "GDP" },
    { label: "CPI inflation", key: "CPIAUCSL" },
    { label: "Unemployment", key: "UNRATE", unit: "%" },
    { label: "Fed funds rate", key: "FEDFUNDS", unit: "%" },
  ]

  return (
    <div className="card card-blue">
      <div className="card-title">6-month forecasts</div>
      {rows.map(({ label, key, unit = "" }) => {
        const f = macro.forecasts[key]
        if (!f) return null
        return (
          <div key={key} className="forecast-row">
            <div className="forecast-label">{label}</div>
            <div className="forecast-right">
              <span className="forecast-current">{f.current}{unit}</span>
              <span style={{ color: "var(--text-muted)", fontSize: 11 }}>→</span>
              <span className="forecast-predicted">{f.forecast_6mo}{unit}</span>
              <span className={`tag tag-${f.direction}`}>{f.direction === "up" ? "↑" : "↓"}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function SentimentCard({ sentiment }) {
  if (!sentiment) return <div className="card"><div className="loading">_ analysing sentiment...</div></div>
  const bull = Math.round((sentiment.bullish || 0) * 100)
  const bear = Math.round((sentiment.bearish || 0) * 100)
  const neu = Math.round((sentiment.neutral || 0) * 100)

  return (
    <div className="card">
      <div className="card-title">Market sentiment — NLP</div>
      <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "Space Mono", marginBottom: 4 }}>
        {sentiment.total_articles || 0} articles analysed
      </div>
      <div className="sentiment-bar">
        <div className="sent-bear" style={{ width: `${bear}%` }} />
        <div className="sent-neu" style={{ width: `${neu}%` }} />
        <div className="sent-bull" style={{ width: `${bull}%` }} />
      </div>
      <div className="sent-labels">
        <span style={{ color: "#ff4d6d" }}>▼ {bear}%</span>
        <span style={{ color: "var(--text-muted)" }}>{neu}%</span>
        <span style={{ color: "var(--green-neon)" }}>▲ {bull}%</span>
      </div>
      {sentiment.top_bullish_headlines?.length > 0 && (
        <div style={{ marginTop: 14, padding: "10px 12px", background: "rgba(0,255,136,0.04)", borderRadius: 8, border: "1px solid rgba(0,255,136,0.08)" }}>
          <div style={{ fontSize: 10, fontFamily: "Space Mono", color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 5 }}>TOP SIGNAL</div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6 }}>{sentiment.top_bullish_headlines[0]}</div>
        </div>
      )}
    </div>
  )
}

function SignalsCard({ data }) {
  if (!data) return <div className="card"><div className="loading">_ loading signals...</div></div>
  const signals = data.market?.signals || []
  const disagreements = data.disagreements || []
  const all = [
    ...signals.map(s => ({ text: s.signal, type: s.type })),
    ...disagreements.map(d => ({ text: d.detail, type: d.severity }))
  ]

  const dotColor = (t) => t === "bullish" ? "var(--green-neon)" : t === "bearish" || t === "high" ? "#ff4d6d" : t === "warning" || t === "medium" ? "#ffa500" : "var(--text-muted)"

  return (
    <div className="card card-blue">
      <div className="card-title">Key signals</div>
      {all.map((s, i) => (
        <div key={i} className="signal-row">
          <div className="signal-dot" style={{ background: dotColor(s.type), boxShadow: `0 0 4px ${dotColor(s.type)}` }} />
          <span className="signal-text">{s.text}</span>
          <span className={`tag tag-${s.type}`}>{s.type}</span>
        </div>
      ))}
    </div>
  )
}

function BacktestCard({ backtest }) {
  if (!backtest?.results) return <div className="card"><div className="loading">_ running backtest...</div></div>

  const colors = ["#4da6ff", "#00ff88", "#00cc66", "#1a6bcc"]
  const entries = Object.entries(backtest.results)

  return (
    <div className="card">
      <div className="card-title">Model accuracy — backtest</div>
      {entries.map(([key, val], i) => (
        <div key={key} className="progress-row">
          <div className="progress-label-row">
            <span>{val.label}</span>
            <span className="progress-pct" style={{ color: colors[i % colors.length] }}>{val.directional_accuracy}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{
              width: `${val.directional_accuracy}%`,
              background: colors[i % colors.length],
              boxShadow: `0 0 6px ${colors[i % colors.length]}40`
            }} />
          </div>
        </div>
      ))}
      <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "Space Mono" }}>OVERALL</span>
        <span style={{ fontSize: 16, fontWeight: 700, fontFamily: "Space Mono", color: "var(--green-neon)" }}>{backtest.overall_accuracy}%</span>
      </div>
    </div>
  )
}

export default function App() {
  const [forecast, setForecast] = useState(null)
  const [backtest, setBacktest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [activeNav, setActiveNav] = useState("dashboard")

  const fetchData = async () => {
    setLoading(true)
    try {
      const [fRes, bRes] = await Promise.all([
        axios.get(`${API}/forecast`),
        axios.get(`${API}/backtest`),
      ])
      setForecast(fRes.data)
      setBacktest(bRes.data)
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (e) {
      console.error("API error:", e)
    }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: "◈" },
    { id: "agents", label: "Agents", icon: "◎" },
    { id: "forecasts", label: "Forecasts", icon: "◐" },
    { id: "signals", label: "Signals", icon: "◉" },
  ]

  return (
    <div className="app">
      <div className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-text">
            <span className="logo-macro">MACRO</span>
            <span className="logo-engine">ENGINE</span>
          </div>
          <div className="logo-sub">AI Forecasting System</div>
        </div>

        <div className="nav-section" style={{ marginTop: "0.5rem" }}>Navigation</div>
        {navItems.map(n => (
          <div
            key={n.id}
            className={`nav-item ${activeNav === n.id ? "active" : ""}`}
            onClick={() => setActiveNav(n.id)}
          >
            <span className="nav-icon">{n.icon}</span>
            {n.label}
          </div>
        ))}

        <div className="sidebar-footer">
          <div className="status-indicator">
            <div className="pulse-dot" />
            <span>SYSTEM ONLINE</span>
          </div>
          {lastUpdated && (
            <div style={{ fontSize: 10, color: "var(--text-muted)", fontFamily: "Space Mono", marginTop: 4 }}>
              {lastUpdated}
            </div>
          )}
        </div>
      </div>

      <div className="main">
        <div className="topbar">
          <div>
            <div className="topbar-title">AI-Powered Multi-Agent System</div>
            <h1>Macroeconomic Forecast Dashboard</h1>
          </div>
          <div className="topbar-right">
            <div className="live-badge">
              <div className="pulse-dot" />
              LIVE
            </div>
            <button className="refresh-btn" onClick={fetchData}>↺ Refresh</button>
          </div>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-label">Overall outlook</div>
            <div style={{ marginTop: 6 }}>
              {forecast ? <OutlookBadge outlook={forecast.outlook} /> : <span style={{ color: "var(--text-muted)", fontFamily: "Space Mono" }}>—</span>}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Model confidence</div>
            <div className="metric-value">{forecast ? `${Math.round(forecast.overall_confidence * 100)}%` : "—"}</div>
            <div className="metric-sub neutral">Blended · all agents</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">GDP forecast 6mo</div>
            <div className="metric-value" style={{ fontSize: 20 }}>
              {forecast?.macro?.forecasts?.GDP ? forecast.macro.forecasts.GDP.forecast_6mo.toLocaleString() : "—"}
            </div>
            <div className={`metric-sub ${forecast?.macro?.forecasts?.GDP?.direction === "up" ? "up" : "down"}`}>
              {forecast?.macro?.forecasts?.GDP?.direction === "up" ? "▲ Rising" : "▼ Falling"}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Agent disagreements</div>
            <div className="metric-value">{forecast ? forecast.disagreements?.length : "—"}</div>
            <div className="metric-sub neutral">Detected signals</div>
          </div>
        </div>

        <div className="grid2">
          <AgentCard data={forecast} />
          <ForecastCard macro={forecast?.macro} />
        </div>

        <div className="grid3">
          <SentimentCard sentiment={forecast?.sentiment} />
          <SignalsCard data={forecast} />
          <BacktestCard backtest={backtest} />
        </div>
      </div>
    </div>
  )
}