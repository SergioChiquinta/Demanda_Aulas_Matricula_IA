// src/components/Spinner.jsx
export default function Spinner({ text = 'Cargando...' }) {
  return (
    <div className="spinner-wrap">
      <div className="spinner" />
      <p>{text}</p>
    </div>
  );
}
