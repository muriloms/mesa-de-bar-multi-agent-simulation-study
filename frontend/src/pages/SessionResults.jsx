import { useEffect, useState } from 'react';
import { Remarkable } from 'remarkable';
import {
  getSessionStats,
  getSessionIdea,
  downloadSessionZip,
  downloadSessionIdeaJson,
  downloadSessionIdeaMarkdown,
} from '../services/api';
import { useT } from '../i18n/i18n';
import './SessionResults.css';

const md = new Remarkable({ html: false });

/**
 * Tela 3 pós-conversa: resultado da sessão.
 *
 * 4 blocos colapsáveis:
 *  1. Estatísticas da noite
 *  2. A ideia organizada (auto-gerada)
 *  3. Conversa completa
 *  4. Baixar dados
 *
 * Não menciona "Lab" — a estruturação ainda é gerada (backend usa
 * process_summary_for_lab) mas exposta aqui como "Ideia organizada".
 */
const SessionResults = ({ sessionId, gameState, onReset }) => {
  const t = useT();
  const [stats, setStats] = useState(null);
  const [idea, setIdea] = useState(null);
  const [ideaLoading, setIdeaLoading] = useState(true);
  const [collapsed, setCollapsed] = useState({
    stats: false,
    idea: false,
    conversation: true,  // longo, fica fechado por padrão
    downloads: false,
  });
  const [copied, setCopied] = useState(false);

  // Carrega stats + ideia em paralelo
  useEffect(() => {
    if (!sessionId) return;

    getSessionStats(sessionId)
      .then(res => setStats(res.data))
      .catch(err => console.error('Stats failed:', err));

    setIdeaLoading(true);
    getSessionIdea(sessionId)
      .then(res => setIdea(res.data))
      .catch(err => console.error('Idea failed:', err))
      .finally(() => setIdeaLoading(false));
  }, [sessionId]);

  const toggle = (key) => setCollapsed(c => ({ ...c, [key]: !c[key] }));

  // === Copiar ideia pro clipboard ===
  const handleCopy = async () => {
    if (!idea) return;
    const structured = idea.lab_idea || {};
    const lines = [];
    if (structured.title) lines.push(`# ${structured.title}\n`);
    if (structured.problem_statement) lines.push(`## ${t('results.idea_problem')}\n${structured.problem_statement}\n`);
    if (structured.core_solution) lines.push(`## ${t('results.idea_solution')}\n${structured.core_solution}\n`);
    const features = structured.key_features || [];
    if (features.length > 0) {
      lines.push(`## ${t('results.idea_features')}`);
      features.forEach(f => lines.push(`- ${f}`));
      lines.push('');
    }
    if (structured.target_audience) lines.push(`## ${t('results.idea_audience')}\n${structured.target_audience}\n`);
    if (structured.potential_impact) lines.push(`## ${t('results.idea_impact')}\n${structured.potential_impact}\n`);
    if (structured.next_steps) lines.push(`## ${t('results.idea_next_steps')}\n${structured.next_steps}\n`);
    if (idea.summary) lines.push(`---\n${idea.summary}`);

    try {
      await navigator.clipboard.writeText(lines.join('\n'));
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch (e) {
      alert(t('common.error_generic'));
    }
  };

  // === Format helpers ===
  const fmtDuration = (ms) => {
    if (!ms) return '—';
    const s = Math.round(ms / 1000);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  };

  const fmtMoney = (n) => `$ ${(n || 0).toFixed(2)}`;
  const fmtCost = (n) => `$ ${(n || 0).toFixed(4)}`;

  const structured = idea?.lab_idea || {};

  return (
    <div className="results-container">
      <header className="results-header">
        <h1 className="results-title">{t('results.title')}</h1>
        <p className="results-subtitle">{t('results.subtitle')}</p>
        {gameState?.topic && (
          <div className="results-topic">"{gameState.topic}"</div>
        )}
      </header>

      {/* === Destaque: baixar e enviar os dados === */}
      <section className="results-send">
        <span className="results-send-mark" aria-hidden="true">↓</span>
        <div className="results-send-text">
          <h2 className="results-send-title">{t('results.send_title')}</h2>
          <p className="results-send-body">{t('results.send_body')}</p>
        </div>
        <button
          className="results-send-btn"
          onClick={() => downloadSessionZip(sessionId)}
        >
          {t('results.send_button')}
        </button>
      </section>

      {/* === Bloco 1: Estatísticas === */}
      <section className="results-section">
        <button className="results-section-header" onClick={() => toggle('stats')}>
          <span className="results-section-arrow">{collapsed.stats ? '▸' : '▾'}</span>
          <span className="results-section-title">{t('results.section_stats')}</span>
        </button>
        {!collapsed.stats && stats && (
          <div className="results-section-body">
            <div className="results-stat-grid">
              <StatCard label={t('results.stat_duration')} value={fmtDuration(stats.duration_ms)} />
              <StatCard label={t('results.stat_rounds')} value={stats.rounds_played} />
              <StatCard label={t('results.stat_proposals')} value={stats.totals?.total_proposals || 0} />
              <StatCard label={t('results.stat_total_bid')} value={fmtMoney(stats.totals?.total_bid)} />
              <StatCard label={t('results.stat_avg_chars')} value={`${stats.totals?.avg_idea_chars || 0}`} />
              <StatCard label={t('results.stat_llm_calls')} value={stats.costs?.calls || 0} />
              <StatCard label={t('results.stat_llm_cost')} value={fmtCost(stats.costs?.cost_usd)} accent />
            </div>

            {/* Distribuição de stances */}
            <div className="results-subsection">
              <h3 className="results-subsection-title">{t('results.stat_stances')}</h3>
              <div className="results-stance-grid">
                <StanceBar label={t('results.stance_complement')} value={stats.stances?.complement || 0} total={stats.totals?.total_proposals || 1} color="complement" />
                <StanceBar label={t('results.stance_counter')} value={stats.stances?.counter || 0} total={stats.totals?.total_proposals || 1} color="counter" />
                <StanceBar label={t('results.stance_redirect')} value={stats.stances?.redirect || 0} total={stats.totals?.total_proposals || 1} color="redirect" />
                <StanceBar label={t('results.stance_none')} value={stats.stances?.none || 0} total={stats.totals?.total_proposals || 1} color="none" />
              </div>
            </div>

            {/* Vitórias por persona */}
            <div className="results-subsection">
              <h3 className="results-subsection-title">{t('results.stat_wins')}</h3>
              <div className="results-players-grid">
                {(stats.players || []).map(p => (
                  <div key={p.player_id} className="results-player-card">
                    <div className="results-player-name">{p.name}</div>
                    <div className="results-player-stats">
                      <span>🏆 {p.wins}</span>
                      <span>🥃 {p.drinks}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>

      {/* === Bloco 2: A ideia organizada === */}
      <section className="results-section">
        <button className="results-section-header" onClick={() => toggle('idea')}>
          <span className="results-section-arrow">{collapsed.idea ? '▸' : '▾'}</span>
          <span className="results-section-title">{t('results.section_idea')}</span>
        </button>
        {!collapsed.idea && (
          <div className="results-section-body">
            {ideaLoading && (
              <div className="results-idea-loading">{t('results.idea_loading')}</div>
            )}
            {!ideaLoading && idea && (
              <div className="results-idea">
                {structured.title && (
                  <h2 className="results-idea-title">{structured.title}</h2>
                )}
                {structured.problem_statement && (
                  <IdeaBlock label={t('results.idea_problem')} text={structured.problem_statement} />
                )}
                {structured.core_solution && (
                  <IdeaBlock label={t('results.idea_solution')} text={structured.core_solution} />
                )}
                {Array.isArray(structured.key_features) && structured.key_features.length > 0 && (
                  <div className="results-idea-block">
                    <h3 className="results-idea-label">{t('results.idea_features')}</h3>
                    <ul className="results-idea-list">
                      {structured.key_features.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
                {structured.target_audience && (
                  <IdeaBlock label={t('results.idea_audience')} text={structured.target_audience} />
                )}
                {structured.potential_impact && (
                  <IdeaBlock label={t('results.idea_impact')} text={structured.potential_impact} />
                )}
                {structured.next_steps && (
                  <IdeaBlock label={t('results.idea_next_steps')} text={structured.next_steps} />
                )}
              </div>
            )}
          </div>
        )}
      </section>

      {/* === Bloco 3: Conversa completa === */}
      <section className="results-section">
        <button className="results-section-header" onClick={() => toggle('conversation')}>
          <span className="results-section-arrow">{collapsed.conversation ? '▸' : '▾'}</span>
          <span className="results-section-title">{t('results.section_conversation')}</span>
        </button>
        {!collapsed.conversation && gameState?.conversation && (
          <div className="results-section-body">
            <div className="results-conversation">
              {gameState.conversation.map((msg, i) => (
                <div key={i} className="results-message">
                  <span className="results-message-name">{msg.player_name}:</span>
                  <span className="results-message-text">{msg.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* === Bloco 4: Downloads === */}
      <section className="results-section">
        <button className="results-section-header" onClick={() => toggle('downloads')}>
          <span className="results-section-arrow">{collapsed.downloads ? '▸' : '▾'}</span>
          <span className="results-section-title">{t('results.section_downloads')}</span>
        </button>
        {!collapsed.downloads && (
          <div className="results-section-body">
            <div className="results-downloads-grid">
              <button
                className="results-download-btn results-download-btn--zip"
                onClick={() => downloadSessionZip(sessionId)}
              >
                {t('results.download_zip')}
              </button>
              <button
                className="results-download-btn"
                onClick={() => downloadSessionIdeaJson(sessionId)}
              >
                {t('results.download_json')}
              </button>
              <button
                className="results-download-btn"
                onClick={() => downloadSessionIdeaMarkdown(sessionId)}
              >
                {t('results.download_md')}
              </button>
              <button
                className="results-download-btn"
                onClick={handleCopy}
              >
                {copied ? t('results.copied') : t('results.copy_idea')}
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Botão fim — nova sessão */}
      <div className="results-footer">
        <button className="results-new-session-btn" onClick={onReset}>
          {t('results.new_session')} →
        </button>
      </div>
    </div>
  );
};

const StatCard = ({ label, value, accent }) => (
  <div className={`results-stat-card ${accent ? 'results-stat-card--accent' : ''}`}>
    <div className="results-stat-value">{value}</div>
    <div className="results-stat-label">{label}</div>
  </div>
);

const StanceBar = ({ label, value, total, color }) => {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="results-stance-row">
      <div className="results-stance-label">{label}</div>
      <div className="results-stance-bar-track">
        <div
          className={`results-stance-bar-fill results-stance-bar-fill--${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="results-stance-count">{value}</div>
    </div>
  );
};

const IdeaBlock = ({ label, text }) => (
  <div className="results-idea-block">
    <h3 className="results-idea-label">{label}</h3>
    <p className="results-idea-text">{text}</p>
  </div>
);

export default SessionResults;
