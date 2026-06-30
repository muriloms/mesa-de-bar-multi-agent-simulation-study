import { useState, useRef } from "react";
import { useTypingTelemetry } from "../hooks/useTypingTelemetry";
import { useT } from "../i18n/i18n";
import "./UserInput.css";

/**
 * Entrada da ideia do jogador (v2 estudo): só propor — sem modo "passar".
 */
export default function UserInput({ onSendIdea, onTelemetry, disabled = false, expanded = false }) {
  const t = useT();
  const [message, setMessage] = useState("");
  const telemetry = useTypingTelemetry();
  const startedRef = useRef(false);

  const ensureStarted = () => {
    if (!startedRef.current) { telemetry.start(); startedRef.current = true; }
  };
  const handleChange = (e) => { ensureStarted(); setMessage(e.target.value); };
  const handleKeyDown = (e) => { ensureStarted(); telemetry.record(e); };
  const handlePaste = (e) => { ensureStarted(); telemetry.record(e); };

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    if (typeof onTelemetry === "function") {
      const data = telemetry.flush(trimmed);
      if (data.events.length) onTelemetry("idea", data);
    } else {
      telemetry.flush(trimmed);
    }
    startedRef.current = false;
    onSendIdea && onSendIdea(trimmed);
    setMessage("");
  };

  return (
    <form className={`user-input ${expanded ? "user-input--expanded" : ""}`} onSubmit={handleSubmit}>
      <label className="user-input-label">{t("table.your_proposal")}</label>
      <textarea
        className="user-input-textarea"
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onPaste={handlePaste}
        placeholder={disabled ? t("common.wait") : t("table.input_placeholder_idea")}
        disabled={disabled}
        rows={expanded ? 12 : 3}
      />
      <div className="user-input-actions user-input-actions--single">
        <button type="submit" className="user-input-btn user-input-btn--prim" disabled={disabled || !message.trim()}>
          {t("table.submit_idea")}
        </button>
      </div>
    </form>
  );
}
