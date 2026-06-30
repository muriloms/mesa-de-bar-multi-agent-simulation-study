import { useT } from "../../i18n/i18n";
import "./ActIndicator.css";

export default function ActIndicator({ phase = "discussion", round, totalRounds }) {
  const t = useT();
  const isClosing = phase === "closing";

  return (
    <header className="act-header">
      <div className="act-brand">▌ MESA DE <span className="act-brand-b">BAR</span> ▐</div>
      <div className="act-bar">
        <span className={`act-step ${!isClosing ? "act-step--on" : ""}`}>
          {t("table.act_discussion")}
        </span>
        <span className={`act-step ${isClosing ? "act-step--on" : ""}`}>
          {t("table.act_closing")}
        </span>
        {round != null && !isClosing && (
          <span className="act-pill">
            {totalRounds ? t("table.round_label", { round, total: totalRounds }) : `RODADA ${round}`}
          </span>
        )}
        {totalRounds && !isClosing && (
          <span className="act-pips" role="img" aria-label={t("table.round_label", { round, total: totalRounds })}>
            {Array.from({ length: totalRounds }).map((_, i) => (
              <span
                key={i}
                className={`act-pip ${i < round ? "act-pip--on" : ""} ${i === round - 1 ? "act-pip--cur" : ""}`}
              />
            ))}
          </span>
        )}
      </div>
    </header>
  );
}
