// src/context/PrediccionContext.jsx
import { createContext, useContext, useReducer, useMemo, useCallback } from 'react';
import api from '../api/client';

// ── Constraints de validación por campo ─────────────────────
const FIELD_CONSTRAINTS = {
  alumnos_nuevos:        { min: 0,  max: 120 },
  alumnos_prerrequisito: { min: 0,  max: 120 },
  alumnos_repitentes:    { min: 0,  max: 80  },
  capacidad_aula:        { min: 1,  max: 120 },
  duracion_semanas:      { min: 1,  max: 24  },
  docentes_disponibles:  { min: 0,  max: 20  },
  laboratorio:           { min: 0,  max: 1   },
};

const ESCENARIOS_VALIDOS = ['Conservador (+MAE)', 'Base IA', 'Optimista (-MAE)'];

const DEFAULT_FORM = {
  alumnos_nuevos: 25,
  alumnos_prerrequisito: 20,
  alumnos_repitentes: 8,
  capacidad_aula: 40,
  duracion_semanas: 18,
  docentes_disponibles: 2,
  laboratorio: 0,
  escenario: 'Conservador (+MAE)',
};

const INITIAL_STATE = {
  form:         { ...DEFAULT_FORM },
  result:       null,
  status:       'idle',   // 'idle' | 'loading' | 'success' | 'error'
  error:        null,
  lastSyncedAt: null,
};

// ── Validación de campo con clamping ────────────────────────
function clampField(key, rawValue) {
  const constraint = FIELD_CONSTRAINTS[key];
  if (!constraint) return rawValue;
  const parsed = typeof rawValue === 'number' ? rawValue : parseInt(rawValue, 10);
  if (Number.isNaN(parsed)) return constraint.min;
  return Math.max(constraint.min, Math.min(constraint.max, parsed));
}

// ── Validación del response del backend ─────────────────────
function validateResult(data) {
  if (!data || typeof data !== 'object') return false;
  const required = [
    'pred_base', 'pred_min', 'pred_max', 'demanda_plan',
    'capacidad_efectiva', 'aulas_recomendadas', 'ocupacion_promedio',
    'secciones',
  ];
  return required.every(k => k in data) && Array.isArray(data.secciones);
}

// ── Reducer puro ────────────────────────────────────────────
function prediccionReducer(state, action) {
  switch (action.type) {
    case 'SET_FIELD': {
      const { key, value } = action.payload;
      if (key === 'escenario') {
        if (!ESCENARIOS_VALIDOS.includes(value)) return state;
        return { ...state, form: { ...state.form, escenario: value } };
      }
      const clamped = clampField(key, value);
      return { ...state, form: { ...state.form, [key]: clamped } };
    }
    case 'RESET_FORM':
      return { ...INITIAL_STATE };

    case 'FETCH_START':
      return { ...state, status: 'loading', error: null };

    case 'FETCH_SUCCESS': {
      const result = action.payload;
      if (!validateResult(result)) {
        return {
          ...state,
          status: 'error',
          error: 'Respuesta del servidor con estructura inválida.',
        };
      }
      return {
        ...state,
        result,
        status: 'success',
        error: null,
        lastSyncedAt: Date.now(),
      };
    }
    case 'FETCH_ERROR':
      return { ...state, status: 'error', error: action.payload, result: null };

    default:
      return state;
  }
}

// ── Context ─────────────────────────────────────────────────
const PrediccionContext = createContext(null);

export function PrediccionProvider({ children }) {
  const [state, dispatch] = useReducer(prediccionReducer, INITIAL_STATE);

  // ── Acciones memoizadas ─────────────────────────────────
  const setField = useCallback((key, value) => {
    dispatch({ type: 'SET_FIELD', payload: { key, value } });
  }, []);

  const resetForm = useCallback(() => {
    dispatch({ type: 'RESET_FORM' });
  }, []);

  const ejecutarPrediccion = useCallback(async () => {
    dispatch({ type: 'FETCH_START' });
    try {
      const res = await api.post('/prediccion/simular', state.form);
      dispatch({ type: 'FETCH_SUCCESS', payload: res.data });
    } catch (err) {
      const msg = err.response?.data?.error || err.message;
      dispatch({ type: 'FETCH_ERROR', payload: msg });
    }
  }, [state.form]);

  // ── Valores derivados memoizados ────────────────────────
  const derived = useMemo(() => {
    const { form, result, status } = state;
    const factorLab = form.laboratorio === 1 ? 0.85 : 1.0;
    const capacidadEfectiva = Math.max(1, Math.floor(form.capacidad_aula * factorLab));

    return {
      capacidadEfectiva,
      demandaPlan:          result?.demanda_plan ?? null,
      docentesDisponibles:  form.docentes_disponibles,
      hasValidResult:       status === 'success' && result !== null,
      ocupacionPromedio:    result?.ocupacion_promedio ?? null,
      aulasRecomendadas:    result?.aulas_recomendadas ?? null,
    };
  }, [state]);

  const value = useMemo(() => ({
    state,
    dispatch,
    setField,
    resetForm,
    ejecutarPrediccion,
    derived,
  }), [state, setField, resetForm, ejecutarPrediccion, derived]);

  return (
    <PrediccionContext.Provider value={value}>
      {children}
    </PrediccionContext.Provider>
  );
}

// ── Hook de consumo ─────────────────────────────────────────
export function usePrediccion() {
  const ctx = useContext(PrediccionContext);
  if (!ctx) {
    throw new Error('usePrediccion debe usarse dentro de <PrediccionProvider>');
  }
  return ctx;
}
