// src/components/HorarioGrid.jsx
import { forwardRef, Fragment } from 'react';
import { DIAS, DIAS_LABEL, colorForCurso, construirGrilla } from '../utils/horarioGrid';

/**
 * Grilla semanal de horario (día x franja horaria) reutilizada por la
 * vista administrativa y la del estudiante.
 *
 * secciones: array de filas devueltas por /api/horarios/* (join completo).
 * misSeccionIds: Set<number> opcional — resalta esas secciones (borde UTP).
 * conflictoBloqueIds: Set<number> opcional — marca en rojo esos bloques.
 */
const HorarioGrid = forwardRef(function HorarioGrid(
  { secciones, misSeccionIds, conflictoBloqueIds, vacioTexto },
  ref
) {
  if (!secciones || secciones.length === 0) {
    return (
      <div className="card">
        <div className="card-body" style={{ textAlign: 'center', padding: '50px 0', color: '#aaa' }}>
          {vacioTexto || 'No hay secciones para mostrar.'}
        </div>
      </div>
    );
  }

  const filas = construirGrilla(secciones);

  return (
    <div ref={ref} className="horario-grid-wrap" style={{ background: '#fff', padding: 12, borderRadius: 12 }}>
      <div className="horario-grid">
        <div className="hg-head">Hora</div>
        {DIAS.map((d) => <div key={d} className="hg-head">{DIAS_LABEL[d]}</div>)}

        {filas.map((fila) => (
          <Fragment key={fila.orden}>
            <div className="hg-hora">{fila.hora}</div>
            {DIAS.map((dia) => {
              const items = fila.celdas[dia];
              return (
                <div key={`${fila.orden}-${dia}`} className="hg-cell">
                  {items.map((s) => {
                    const esMia = misSeccionIds?.has(s.id_seccion);
                    const enConflicto = esMia && conflictoBloqueIds?.has(s.id_bloque);
                    const clases = ['horario-chip', esMia && 'mia', enConflicto && 'conflicto'].filter(Boolean).join(' ');
                    return (
                      <div
                        key={s.id_seccion}
                        className={clases}
                        style={{ background: colorForCurso(s.nombre_curso) }}
                        title={`${s.nombre_curso} · ${s.codigo_seccion} · ${s.codigo_aula} · ${s.nombre_docente}`}
                      >
                        <div className="hc-curso">{s.nombre_curso}</div>
                        <div className="hc-sub">{s.codigo_aula} · {s.codigo_seccion}</div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
    </div>
  );
});

export default HorarioGrid;
