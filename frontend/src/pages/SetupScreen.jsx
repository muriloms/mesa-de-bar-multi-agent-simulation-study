import { useState, useEffect } from 'react';
import { listStudies } from '../services/api';
import { useT } from '../i18n/i18n';
import './SetupScreen.css';

const STUDY_ID = 'main';

const AI_ROLES = [
  ['✶', 'onb.ai_personas_t', 'onb.ai_personas_b', 'cyan'],
  ['⚄', 'onb.ai_draw_t',     'onb.ai_draw_b',     'amber'],
  ['⚖', 'onb.ai_judge_t',    'onb.ai_judge_b',    'pink'],
  ['⟡', 'onb.ai_owner_t',    'onb.ai_owner_b',    'purple'],
];

export default function SetupScreen({ onStartStudy, isLoading, defaultName = '', platformConfig }) {
  const t = useT();
  const [userName, setUserName] = useState(defaultName);
  const [studyId, setStudyId] = useState(STUDY_ID);
  const [chosenTopic, setChosenTopic] = useState('');        // theme choose/write
  const [chosenComposition, setChosenComposition] = useState(''); // table choose
  const [openComp, setOpenComp] = useState(null);            // composição expandida

  const themeMode = platformConfig?.theme?.mode || 'random';
  const tableMode = platformConfig?.table?.mode || 'random';
  const areas = platformConfig?.theme?.areas || [];
  const compositions = platformConfig?.table?.compositions || [];

  // Garante que o estudo principal existe; se não, cai no primeiro disponível.
  useEffect(() => {
    listStudies()
      .then((res) => {
        const list = res.data || [];
        if (!list.find((s) => s.id === STUDY_ID) && list.length) setStudyId(list[0].id);
      })
      .catch(() => {});
  }, []);

  const themeReady = themeMode === 'random' || chosenTopic.trim();
  const tableReady = tableMode === 'random' || chosenComposition;
  const canStart = userName.trim() && themeReady && tableReady;

  const handleStart = () => {
    if (!userName.trim()) { alert(t('onb.need_name')); return; }
    if (!themeReady) { alert(t('onb.need_theme')); return; }
    if (!tableReady) { alert(t('onb.need_table')); return; }
    onStartStudy(studyId, userName.trim(), {
      chosenTopic: themeMode === 'random' ? null : chosenTopic.trim(),
      chosenComposition: tableMode === 'random' ? null : chosenComposition,
    });
  };

  const flow = ['flow_theme', 'flow_round', 'flow_pick', 'flow_line', 'flow_final'];
  const steps = [1, 2, 3, 4, 5];

  return (
    <>
      <div className="onb">
        {/* HERO — letreiro de neon */}
        <header className="onb-hero">
          <p className="onb-eyebrow">{t('onb.eyebrow')}</p>
          <h1 className="onb-title">
            <span className="onb-title-line">MESA</span>
            <span className="onb-title-de">de</span>
            <span className="onb-title-line onb-title-line--neon">BAR</span>
          </h1>
          <p className="onb-tagline">{t('onb.tagline')}</p>
          <div className="onb-rule" aria-hidden="true" />
        </header>

        {/* O QUE É */}
        <section className="onb-card">
          <span className="onb-kicker">{t('onb.about_title')}</span>
          <p className="onb-body">{t('onb.about_body')}</p>
        </section>

        {/* COMO FUNCIONA A MESA */}
        <section className="onb-card">
          <span className="onb-kicker">{t('onb.game_title')}</span>
          <p className="onb-body">{t('onb.game_body')}</p>
          <div className="onb-flow" role="list">
            {flow.map((k, i) => (
              <div className="onb-flow-item" role="listitem" key={k}>
                <span className="onb-chip">{t(`onb.${k}`)}</span>
                {i < flow.length - 1 && <span className="onb-arrow" aria-hidden="true">→</span>}
              </div>
            ))}
          </div>
        </section>

        {/* QUEM SENTA COM VOCÊ (a IA) */}
        <section className="onb-card">
          <span className="onb-kicker">{t('onb.ai_title')}</span>
          <div className="onb-roles">
            {AI_ROLES.map(([glyph, tk, bk, color]) => (
              <div className="onb-role" key={tk}>
                <span className={`onb-role-glyph onb-role-glyph--${color}`} aria-hidden="true">{glyph}</span>
                <div>
                  <h3 className="onb-role-title">{t(tk)}</h3>
                  <p className="onb-role-body">{t(bk)}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* O ROTEIRO DA NOITE — comanda */}
        <section className="onb-tab">
          <div className="onb-tab-head">
            <span className="onb-kicker onb-kicker--dark">{t('onb.steps_title')}</span>
            <span className="onb-tab-sub">{t('onb.steps_sub')}</span>
          </div>
          <ol className="onb-steps">
            {steps.map((n) => (
              <li className="onb-step" key={n}>
                <span className="onb-step-num">{String(n).padStart(2, '0')}</span>
                <span className="onb-step-title">{t(`onb.step${n}_t`)}</span>
                <span className="onb-step-dots" aria-hidden="true" />
                <span className="onb-step-note">{t(`onb.step${n}_b`)}</span>
              </li>
            ))}
          </ol>
        </section>

        {/* DADOS E ANONIMATO */}
        <section className="onb-card">
          <span className="onb-kicker">{t('onb.data_title')}</span>
          <p className="onb-body">{t('onb.data_body')}</p>
          <p className="onb-fictitious">{t('onb.data_fictitious')}</p>
        </section>

        {/* DOWNLOAD — destaque */}
        <section className="onb-callout">
          <span className="onb-callout-mark" aria-hidden="true">↓</span>
          <div>
            <h3 className="onb-callout-title">{t('onb.download_title')}</h3>
            <p className="onb-callout-body">{t('onb.download_body')}</p>
          </div>
        </section>

        {/* CTA — sentar à mesa */}
        <section className="onb-cta">
          <label className="onb-cta-label" htmlFor="onb-name">{t('onb.name_label')}</label>
          <input
            id="onb-name"
            className="onb-input"
            type="text"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            placeholder={t('onb.name_placeholder')}
            maxLength={40}
            autoComplete="off"
          />
          <p className="onb-cta-hint">{t('onb.name_hint')}</p>

          {/* Escolha do TEMA (quando habilitado na plataforma) */}
          {themeMode === 'choose' && (
            <div className="onb-choice">
              <label className="onb-cta-label">{t('onb.theme_choose_label')}</label>
              <div className="onb-theme-list">
                {areas.map((a) => (
                  <div key={a.id} className="onb-theme-area">
                    <span className="onb-theme-area-title">{a.title}</span>
                    {(a.subtemas || []).map((s) => (
                      <button
                        type="button"
                        key={s}
                        className={`onb-theme-opt ${chosenTopic === s ? 'onb-theme-opt--on' : ''}`}
                        onClick={() => setChosenTopic(s)}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {themeMode === 'write' && (
            <div className="onb-choice">
              <label className="onb-cta-label" htmlFor="onb-theme-write">{t('onb.theme_write_label')}</label>
              <input
                id="onb-theme-write"
                className="onb-input"
                type="text"
                value={chosenTopic}
                onChange={(e) => setChosenTopic(e.target.value)}
                placeholder={t('onb.theme_write_ph')}
                maxLength={140}
              />
            </div>
          )}

          {/* Escolha da COMPOSIÇÃO da mesa (quando habilitado) */}
          {tableMode === 'choose' && (
            <div className="onb-choice">
              <label className="onb-cta-label">{t('onb.table_choose_label')}</label>
              <div className="onb-comp-grid">
                {compositions.map((c) => {
                  const selected = chosenComposition === c.id;
                  const open = openComp === c.id;
                  return (
                    <div key={c.id} className={`onb-comp ${selected ? 'onb-comp--on' : ''}`}>
                      <div className="onb-comp-head">
                        <span className="onb-comp-title">{c.title}</span>
                        <span className="onb-comp-count">{c.personas.length} personas</span>
                      </div>
                      {c.description && <p className="onb-comp-desc">{c.description}</p>}
                      <div className="onb-comp-personas">
                        {(open ? c.personas : c.personas.slice(0, 4)).map((p) => (
                          <div key={p.name} className="onb-persona">
                            <span className="onb-persona-name">{p.name}</span>
                            <span className="onb-persona-role">{p.role}</span>
                            {open && p.description && (
                              <span className="onb-persona-desc">{p.description}</span>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="onb-comp-actions">
                        {c.personas.length > 4 && (
                          <button type="button" className="onb-comp-more"
                            onClick={() => setOpenComp(open ? null : c.id)}>
                            {open ? t('onb.table_less') : t('onb.table_more')}
                          </button>
                        )}
                        <button type="button"
                          className={`onb-comp-pick ${selected ? 'onb-comp-pick--on' : ''}`}
                          onClick={() => setChosenComposition(c.id)}>
                          {selected ? t('onb.table_selected') : t('onb.table_select')}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <button
            type="button"
            className="onb-start"
            onClick={handleStart}
            disabled={isLoading || !canStart}
          >
            {isLoading ? t('onb.starting') : t('onb.start')}
          </button>
        </section>
      </div>
    </>
  );
}
