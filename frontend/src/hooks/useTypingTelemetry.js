import { useRef, useCallback } from "react";

/**
 * Hook de telemetria de digitação.
 *
 * Cada vez que `record()` é chamado (no onKeyDown ou onPaste do input),
 * registra `{t, k}` ou `{t, k:"<paste>", n}` em ordem.
 *
 * `start()` inicializa um novo "round" de captura.
 * `flush()` devolve { events, metrics } e zera tudo.
 *
 * Métricas calculadas:
 *  - time_to_first_keystroke_ms
 *  - total_keystrokes (sem contar Backspace/Delete/setas)
 *  - total_edits (Backspace + Delete)
 *  - total_pastes
 *  - longest_pause_ms (gap maior entre eventos consecutivos)
 *  - total_duration_ms
 *  - final_length (texto final passado pelo chamador)
 */
const NON_CHAR_KEYS = new Set([
  "Shift", "Control", "Alt", "Meta", "Tab", "CapsLock",
  "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
  "Escape", "Home", "End", "PageUp", "PageDown",
]);

export function useTypingTelemetry() {
  const startedAtRef = useRef(null);
  const eventsRef = useRef([]);

  const start = useCallback(() => {
    startedAtRef.current = performance.now();
    eventsRef.current = [];
  }, []);

  const record = useCallback((event) => {
    if (startedAtRef.current === null) {
      startedAtRef.current = performance.now();
    }
    const t = Math.round(performance.now() - startedAtRef.current);

    if (event.type === "paste") {
      const text = event.clipboardData?.getData("text") || "";
      eventsRef.current.push({ t, k: "<paste>", n: text.length });
      return;
    }

    // keydown
    const k = event.key;
    if (NON_CHAR_KEYS.has(k)) return; // ignora teclas modificadoras
    eventsRef.current.push({ t, k });
  }, []);

  const flush = useCallback((finalText = "") => {
    const events = eventsRef.current.slice();
    const startedAt = startedAtRef.current;

    if (!events.length || startedAt === null) {
      eventsRef.current = [];
      startedAtRef.current = null;
      return {
        events: [],
        metrics: {
          time_to_first_keystroke_ms: null,
          total_keystrokes: 0,
          total_edits: 0,
          total_pastes: 0,
          longest_pause_ms: 0,
          total_duration_ms: 0,
          final_length: finalText.length,
        },
      };
    }

    const totalDuration = events[events.length - 1].t;
    const ttf = events[0].t;

    let edits = 0;
    let pastes = 0;
    let keys = 0;
    let longestPause = 0;
    let lastT = 0;

    for (const e of events) {
      const gap = e.t - lastT;
      if (gap > longestPause) longestPause = gap;
      lastT = e.t;

      if (e.k === "Backspace" || e.k === "Delete") edits++;
      else if (e.k === "<paste>") pastes++;
      else keys++;
    }

    const metrics = {
      time_to_first_keystroke_ms: ttf,
      total_keystrokes: keys,
      total_edits: edits,
      total_pastes: pastes,
      longest_pause_ms: longestPause,
      total_duration_ms: totalDuration,
      final_length: finalText.length,
    };

    eventsRef.current = [];
    startedAtRef.current = null;
    return { events, metrics };
  }, []);

  return { start, record, flush };
}
