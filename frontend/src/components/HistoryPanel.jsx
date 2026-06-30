import { useState } from "react";
import "./HistoryPanel.css";

/**
 * Histórico completo da conversa em um drawer lateral.
 * Fica colapsado por default; uma aba lateral expande/recolhe.
 *
 * As ações de "encerrar" e "nova ideia" foram movidas pro WaiterBar.
 * Aqui só lemos o histórico.
 */
export default function HistoryPanel({ conversation = [] }) {
  const [open, setOpen] = useState(false);

  return (
    <aside className={`history-panel ${open ? "history-panel--open" : ""}`}>
      <button
        className="history-tab"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Fechar histórico" : "Abrir histórico"}
        aria-expanded={open}
      >
        <span className="history-tab-text">
          {open ? "▶ FECHAR" : "◀ HISTÓRICO"}
        </span>
        <span className="history-tab-count">{conversation.length}</span>
      </button>

      <div className="history-content">
        <h3 className="history-title">Histórico da mesa</h3>
        <div className="history-log">
          {conversation.length === 0 && (
            <div className="history-empty">Ainda nada foi dito.</div>
          )}
          {conversation.map((msg, i) => (
            <div
              key={i}
              className={`history-msg ${msg.player_id === 0 ? "history-msg--narrator" : ""}`}
            >
              <span className="history-msg-who">{msg.player_name}:</span>
              <span className="history-msg-text"> {msg.message}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
