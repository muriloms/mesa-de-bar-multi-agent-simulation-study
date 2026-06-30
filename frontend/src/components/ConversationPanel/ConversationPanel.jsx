import { useEffect, useRef, useState } from "react";
import { useT } from "../../i18n/i18n";
import "./ConversationPanel.css";

/**
 * Painel lateral direito — a "linha de ideias" da mesa.
 * Cada ideia que avança vira um cartão. O jogador pode EXPANDIR qualquer
 * ideia (botão de lupa) pra ler o texto ampliado e nítido.
 */
const COLORS = ["#ff5a8c", "#5ee0ff", "#6df57b", "#c79bf0", "#f0a020", "#ff8c2c"];
function colorFor(playerId) {
  if (playerId === 0) return "#a08868";
  return COLORS[(playerId - 1) % COLORS.length];
}

export default function ConversationPanel({ topic, conversation = [], phase, round, thinking = false, thinkingText }) {
  const t = useT();
  const feedRef = useRef(null);
  const [expanded, setExpanded] = useState(null);   // {name, message, color} | null
  const lastMsgIndex = conversation.length - 1;
  const thinkingLabel = thinkingText || t("conversation.thinking_label");

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [conversation.length, thinking]);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") setExpanded(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <aside className="conv-panel">
      <header className="conv-header">
        <div className="conv-section-label">{t("conversation.topic_label")}</div>
        <h2 className="conv-topic">"{topic}"</h2>
        <div className="conv-meta">
          {round != null && <span>{`Rodada ${round}`}</span>}
          {phase && <span className="conv-meta-phase">{labelForPhase(phase, t)}</span>}
        </div>
        <div className="conv-line-label">{t("conversation.line_label")}</div>
      </header>

      <div className="conv-feed" ref={feedRef}>
        {conversation.length === 0 && !thinking && (
          <div className="conv-empty">{t("conversation.empty")}</div>
        )}

        {conversation.map((msg, i) => {
          const isLast = i === lastMsgIndex;
          const isNarrator = msg.player_id === 0;
          const color = colorFor(msg.player_id);
          return (
            <div
              key={i}
              className={["conv-bubble", isLast ? "conv-bubble--last" : "", isNarrator ? "conv-bubble--narrator" : ""].join(" ")}
              style={{ "--bubble-color": color }}
            >
              <div className="conv-bubble-head">
                <span className="conv-bubble-who" style={{ color }}>{msg.player_name}</span>
                {isLast && !isNarrator && (
                  <span className="conv-current-tag">{t("conversation.current")}</span>
                )}
                {!isNarrator && (
                  <button
                    type="button"
                    className={`conv-expand-btn ${isLast ? "conv-expand-btn--labeled" : ""}`}
                    onClick={() => setExpanded({ name: msg.player_name, message: msg.message, color })}
                    title={t("conversation.expand")}
                    aria-label={t("conversation.expand")}
                  >
                    {isLast ? `⤢ ${t("conversation.expand_short")}` : "⤢"}
                  </button>
                )}
              </div>
              <div className="conv-bubble-text">{msg.message}</div>
            </div>
          );
        })}

        {thinking && (
          <div className="conv-thinking">
            <span className="conv-thinking-label">▶ {thinkingLabel}</span>
            <span className="conv-thinking-dots"><span></span><span></span><span></span></span>
          </div>
        )}
      </div>

      {expanded && (
        <div className="conv-modal-overlay" onClick={() => setExpanded(null)} role="dialog" aria-modal="true">
          <div className="conv-modal" onClick={(e) => e.stopPropagation()} style={{ "--bubble-color": expanded.color }}>
            <div className="conv-modal-head">
              <span className="conv-modal-who" style={{ color: expanded.color }}>{expanded.name}</span>
              <button type="button" className="conv-modal-close" onClick={() => setExpanded(null)} aria-label={t("common.close")}>✕</button>
            </div>
            <p className="conv-modal-text">{expanded.message}</p>
          </div>
        </div>
      )}
    </aside>
  );
}

function labelForPhase(p, t) {
  const map = {
    proposing: t("conversation.phase_discussion"),
    choosing: t("conversation.phase_voting"),
    revealing: t("conversation.phase_voting"),
    finished: t("conversation.phase_finished"),
    discussion: t("conversation.phase_discussion"),
    closing: t("conversation.phase_closing"),
  };
  return map[p] || p;
}
