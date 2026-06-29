// src/components/OcupacionBadge.jsx
const MAP = {
  'Óptimo':       'badge-optimo',
  'Ajustado':     'badge-ajustado',
  'Excede aforo': 'badge-excede',
  'Subutilizado': 'badge-subutiliz',
  'Baja ocupación':'badge-baja',
};

export default function OcupacionBadge({ estado }) {
  const cls = MAP[estado] || 'badge-baja';
  return <span className={`badge ${cls}`}>{estado || '—'}</span>;
}
