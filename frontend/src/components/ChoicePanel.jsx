import { useT } from "../i18n/i18n";
import "./VotingPanel.css";

/**
 * Escolha da melhor ideia da rodada. As opções vêm ANÔNIMAS (choice_options
 * com {ref, idea_text}); a autoria só é revelada depois, no RevealPanel.
 */
export default function ChoicePanel({ options = [], onPick, disabled }) {
  const t = useT();
  return (
    <div className="voting-overlay" role="dialog" aria-modal="true" aria-label={t("choice.title")}>
      <div className="voting-modal">
        <div className="voting-header">
          <h2 className="voting-title">{t("choice.title")}</h2>
          <p className="voting-sub">{t("choice.subtitle")}</p>
        </div>

        <div className="voting-list">
          {options.map((o, idx) => (
            <button
              key={o.ref}
              className="voting-card"
              onClick={() => onPick(o.ref)}
              disabled={disabled}
            >
              <div className="voting-card-head">
                <span className="voting-card-name">{t("choice.option_label", { n: idx + 1 })}</span>
              </div>
              <div className="voting-card-text">"{o.idea_text}"</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
