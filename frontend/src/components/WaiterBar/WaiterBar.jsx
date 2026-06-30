import { useT } from "../../i18n/i18n";
import "./WaiterBar.css";

export default function WaiterBar({
  onDelegate,
  onWaiterSummary,
  onWaiterProvoke,
  onShowCosts,
  onDownloadZip,
  onEndConversation,
  onReset,
  canDelegate = false,
  sessionMeta = "",
  disabled = false,
  endHighlighted = false,
}) {
  const t = useT();
  return (
    <footer className="waiter-bar">
      <span className="waiter-lbl">▶ {t("waiter.label")}</span>

      <button
        className="waiter-btn waiter-btn--costs"
        onClick={onShowCosts}
      >
        {t("waiter.costs")}
      </button>

      {onDownloadZip && (
        <button
          className="waiter-btn waiter-btn--download"
          onClick={onDownloadZip}
        >
          {t("waiter.download")}
        </button>
      )}

      <span className="waiter-spacer" />

      {onEndConversation && (
        <button
          className={`waiter-btn waiter-btn--end ${endHighlighted ? "waiter-btn--pulse" : ""}`}
          onClick={onEndConversation}
          disabled={disabled}
        >
          {endHighlighted ? t("waiter.end_now") : t("waiter.end")}
        </button>
      )}

      {onReset && (
        <button
          className="waiter-btn waiter-btn--reset"
          onClick={onReset}
          disabled={disabled}
        >
          {t("waiter.new_table")}
        </button>
      )}

      {sessionMeta && <span className="waiter-meta">{sessionMeta}</span>}
    </footer>
  );
}
