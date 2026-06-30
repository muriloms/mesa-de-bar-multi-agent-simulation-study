import { useEffect, useState } from "react";
import { useT } from "../i18n/i18n";

/**
 * Overlay de loading com contador de segundos e mensagens rotativas.
 *
 * Substitui o div estático. Dá feedback de progresso ao usuário
 * mesmo sem streaming.
 */
const ROTATION_MS = 3000;  // troca de mensagem a cada 3s

export default function LoadingOverlay() {
  const t = useT();
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    const start = performance.now();
    const interval = setInterval(() => {
      setElapsedMs(Math.round(performance.now() - start));
    }, 100);
    return () => clearInterval(interval);
  }, []);

  const seconds = (elapsedMs / 1000).toFixed(1);

  // Mensagens que rotacionam pra dar sensação de progresso
  const messages = [
    t("common.loading"),
    t("loading.thinking"),
    t("loading.gathering"),
  ];
  const messageIdx = Math.floor(elapsedMs / ROTATION_MS) % messages.length;
  const message = messages[messageIdx];

  return (
    <div className="loading-overlay">
      <div className="loading-message">{message}</div>
      <div className="loading-elapsed">{seconds}s</div>
    </div>
  );
}
