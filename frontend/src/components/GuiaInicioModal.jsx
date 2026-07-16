// src/components/GuiaInicioModal.jsx
// Modal tipo wizard: pasos deslizan horizontalmente, contenido según rol.
import { useState, useEffect } from 'react';

export default function GuiaInicioModal({ abierto, onCerrar, titulo, pasos }) {
  const [pasoActual, setPasoActual] = useState(0);

  useEffect(() => {
    if (abierto) setPasoActual(0);
  }, [abierto]);

  if (!abierto) return null;

  // El primer slide es la pantalla de bienvenida y no cuenta como "página":
  // las páginas numeradas son las restantes (1..totalPaginas).
  const totalPaginas = pasos.length - 1;
  const esBienvenida = pasoActual === 0;
  const esUltimo = pasoActual === pasos.length - 1;
  const siguiente = () => setPasoActual((p) => Math.min(pasos.length - 1, p + 1));
  const anterior = () => setPasoActual((p) => Math.max(0, p - 1));

  return (
    <div className="guia-overlay" onClick={onCerrar}>
      <div className="guia-modal" onClick={(e) => e.stopPropagation()}>
        {/* Capa de fondo (vidrio esmerilado) separada del contenido: el blur
            es costoso de recalcular, así que vive en su propia capa estática
            y no interfiere con la animación de los pasos, que corre encima. */}
        <div className="guia-modal-bg" />

        <div className="guia-modal-content">
          <button className="guia-close" onClick={onCerrar} aria-label="Cerrar guía">✕</button>
          <div className="guia-titulo">{titulo}</div>

          <div className="guia-track-wrap">
            <div className="guia-track" style={{ transform: `translateX(-${pasoActual * 100}%) translateZ(0)` }}>
              {pasos.map((p, i) => (
                <div className="guia-paso" key={i}>
                  <div className="guia-paso-icono">{p.icono}</div>
                  <div className="guia-paso-titulo">{p.titulo}</div>
                  <div className="guia-paso-texto">{p.texto}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="guia-dots">
            {pasos.slice(1).map((_, i) => (
              <span
                key={i}
                className={`guia-dot${i + 1 === pasoActual ? ' activo' : ''}`}
                onClick={() => setPasoActual(i + 1)}
              />
            ))}
          </div>

          <div className="guia-nav">
            <button
              className="btn btn-outline"
              style={{ padding: '7px 14px', fontSize: 12 }}
              onClick={anterior}
              disabled={pasoActual === 0}
            >
              ← Anterior
            </button>
            <span className="guia-contador">
              {esBienvenida ? 'Bienvenida' : `Página ${pasoActual} de ${totalPaginas}`}
            </span>
            {esUltimo ? (
              <button className="btn btn-primary" style={{ padding: '7px 14px', fontSize: 12 }} onClick={onCerrar}>
                Entendido
              </button>
            ) : (
              <button className="btn btn-primary" style={{ padding: '7px 14px', fontSize: 12 }} onClick={siguiente}>
                Siguiente →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
