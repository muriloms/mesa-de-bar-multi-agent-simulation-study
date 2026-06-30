import { Remarkable } from 'remarkable';
import { useT } from '../i18n/i18n';
import './EndGameSummary.css';

const md = new Remarkable({ html: false });

/**
 * Tela 1 pós-conversa: A carta do Dono do Bar.
 *
 * Design "carta" — papel envelhecido, tipografia serifada, avatar do
 * Dono em destaque, assinatura no fim. Foco no texto da síntese.
 *
 * Único CTA: "Continuar" → vai pra pesquisa pós-sessão.
 */
const EndGameSummary = ({ summary, ownerAvatar, onContinue }) => {
  const t = useT();
  const hasSummary = typeof summary === 'string' && summary.trim().length > 0;

  return (
    <div className="letter-overlay">
      <div className="letter-paper">
        <header className="letter-header">
          <div className="letter-avatar">
            {ownerAvatar ? (
              <img src={ownerAvatar} alt="Dono do Bar" />
            ) : (
              <div className="letter-avatar-placeholder" aria-label="Dono do Bar">
                {/* SVG simples — silhueta de garçom/barman.
                    Quando o usuário trocar pra PNG, é só passar `ownerAvatar`. */}
                <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="32" cy="22" r="11" fill="currentColor" opacity="0.7" />
                  <path d="M10 60 C 10 44, 20 38, 32 38 C 44 38, 54 44, 54 60 Z"
                        fill="currentColor" opacity="0.7" />
                  <path d="M22 16 L 32 8 L 42 16 L 42 22 L 22 22 Z"
                        fill="currentColor" opacity="0.85" />
                </svg>
              </div>
            )}
          </div>
          <h1 className="letter-title">{t('summary.title')}</h1>
        </header>

        <p className="letter-intro">"{t('summary.letter_intro')}"</p>

        {hasSummary ? (
          <div
            className="letter-body"
            dangerouslySetInnerHTML={{ __html: md.render(summary) }}
          />
        ) : (
          <div className="letter-body letter-body--empty">
            <em>{t('summary.no_summary')}</em>
          </div>
        )}

        <div className="letter-signature">
          {t('summary.owner_signature')}
        </div>

        <div className="letter-actions">
          <button className="letter-btn" onClick={onContinue}>
            {t('summary.continue')} →
          </button>
        </div>
      </div>
    </div>
  );
};

export default EndGameSummary;
