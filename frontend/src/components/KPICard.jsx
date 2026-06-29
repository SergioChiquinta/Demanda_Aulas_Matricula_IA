// src/components/KPICard.jsx
export default function KPICard({ label, value, sub, accent }) {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={accent ? { color: accent } : {}}>
        {value ?? '—'}
      </div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}
