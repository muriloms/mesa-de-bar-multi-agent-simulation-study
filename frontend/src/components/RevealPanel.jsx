import { useT } from "../i18n/i18n";
import "./VotingPanel.css";
import "./RevealPanel.css";

/**
 * Revelação da rodada: autoria das ideias + escolha do jogador + escolha do
 * juiz + comparação. No mismatch, o jogador decide se concorda com o juiz.
 * Em ambos os casos, avança a rodada (advance).
 */
export default function RevealPanel({ reveal, user, onAdvance, disabled }) {
  const t = useT();
  if (!reveal) return null;

  const {
    options = [],
    player_pick_player_id, player_pick_name,
    judge_pick_player_id, judge_pick_name,
    match,
  } = reveal;

  const isUser = (pid) => user && pid === user.id;

  return (
    <div className="voting-overlay" role="dialog" aria-modal="true" aria-label={t("reveal.title")}>
      <div className="voting-modal reveal-modal">
        <div className="voting-header">
          <h2 className="voting-title">{t("reveal.title")}</h2>
          <p className="voting-sub">
            {match ? t("reveal.match_sub") : t("reveal.mismatch_sub")}
          </p>
        </div>

        {/* Comparação das escolhas */}
        <div className="reveal-compare">
          <div className={`reveal-pick reveal-pick--you ${match ? "reveal-pick--agree" : ""}`}>
            <span className="reveal-pick-who">{t("reveal.your_pick")}</span>
            <span className="reveal-pick-name">
              {isUser(player_pick_player_id) ? t("reveal.you") : player_pick_name}
            </span>
          </div>
          <div className="reveal-vs">{match ? "=" : "✕"}</div>
          <div className={`reveal-pick reveal-pick--judge ${match ? "reveal-pick--agree" : ""}`}>
            <span className="reveal-pick-who">{t("reveal.judge_pick")}</span>
            <span className="reveal-pick-name">
              {isUser(judge_pick_player_id) ? t("reveal.you") : judge_pick_name}
            </span>
          </div>
        </div>

        {/* Autoria de todas as ideias */}
        <div className="voting-list reveal-list">
          {options.map((o) => {
            const youPicked = o.player_id === player_pick_player_id;
            const judgePicked = o.player_id === judge_pick_player_id;
            return (
              <div key={o.ref} className="voting-card reveal-card" aria-disabled="true">
                <div className="voting-card-head">
                  <span className="voting-card-name">
                    {isUser(o.player_id) ? t("reveal.you") : o.player_name}
                    {!o.is_ai && !isUser(o.player_id) ? "" : ""}
                  </span>
                  <span className="reveal-badges">
                    {youPicked && <span className="reveal-badge reveal-badge--you">{t("reveal.badge_you")}</span>}
                    {judgePicked && <span className="reveal-badge reveal-badge--judge">{t("reveal.badge_judge")}</span>}
                  </span>
                </div>
                <div className="voting-card-text">"{o.idea_text}"</div>
              </div>
            );
          })}
        </div>

        {/* Ações de avanço */}
        <div className="reveal-actions">
          {match ? (
            <button className="reveal-btn reveal-btn--prim" onClick={() => onAdvance(null)} disabled={disabled}>
              {t("reveal.continue")}
            </button>
          ) : (
            <>
              <button className="reveal-btn" onClick={() => onAdvance(false)} disabled={disabled}>
                {t("reveal.keep_mine")}
              </button>
              <button className="reveal-btn reveal-btn--prim" onClick={() => onAdvance(true)} disabled={disabled}>
                {t("reveal.agree_judge")}
              </button>
            </>
          )}
          <p className="reveal-note">{t("reveal.advance_note")}</p>
        </div>
      </div>
    </div>
  );
}
