import { useEffect, useRef, useState } from 'react';
import { getSimulationConfig, startSimulation, getSimulationStatus } from '../services/api';
import './SimulationScreen.css';

/**
 * Modo simulação (ativado quando plataforma.mode === 'simulation').
 * Tela 1: parâmetros (editáveis) + botão iniciar.
 * Tela 2: andamento da execução (etapas, progresso, resultado).
 */
export default function SimulationScreen() {
  const [cfg, setCfg] = useState(null);
  const [error, setError] = useState('');
  const [params, setParams] = useState({ n_games: 10, dry_run: false });
  const [runId, setRunId] = useState(null);
  const [status, setStatus] = useState(null);
  const poll = useRef(null);

  useEffect(() => {
    getSimulationConfig()
      .then((res) => {
        setCfg(res.data);
        const p = res.data.params || {};
        setParams({ n_games: p.n_games ?? 10, dry_run: p.dry_run ?? false });
      })
      .catch((e) => setError(e?.message || 'Falha ao carregar a configuração'));
    return () => poll.current && clearInterval(poll.current);
  }, []);

  const estimate = () => {
    // estimativa local proporcional ao plano carregado
    const base = cfg?.plan;
    if (!base) return null;
    const ratio = (params.n_games || 1) / (cfg.params?.n_games || 1);
    return {
      total: Math.round(base.total_sessions * ratio),
      calls: params.dry_run ? 0 : Math.round(base.approx_llm_calls * ratio),
      cells: base.cells,
      jogadores: base.jogadores,
    };
  };

  const handleStart = async () => {
    setError('');
    try {
      const res = await startSimulation({
        n_games: Number(params.n_games),
        dry_run: !!params.dry_run,
      });
      setRunId(res.data.run_id);
      setStatus({ status: 'running', completed: 0, total_sessions: res.data.plan.total_sessions });
      poll.current = setInterval(async () => {
        try {
          const s = await getSimulationStatus(res.data.run_id);
          setStatus(s.data);
          if (s.data.status === 'done' || s.data.status === 'error') {
            clearInterval(poll.current);
          }
        } catch (e) { /* mantém polling */ }
      }, 1000);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Falha ao iniciar a simulação');
    }
  };

  const est = estimate();
  const pct = status && status.total_sessions
    ? Math.round((status.completed / status.total_sessions) * 100) : 0;

  return (
    <div className="sim">
      <header className="sim-head">
        <p className="sim-eyebrow">Mesa de Bar · modo simulação</p>
        <h1 className="sim-title">Simulação — jogador por agente LLM</h1>
        <p className="sim-sub">O jogador humano é substituído por agentes LLM, varrendo a matriz de condições.</p>
      </header>

      {error && <p className="sim-error">⚠ {error}</p>}
      {!cfg && !error && <p className="sim-muted">Carregando parâmetros…</p>}

      {cfg && !runId && (
        <>
          {/* Parâmetros editáveis */}
          <section className="sim-card">
            <h2>Parâmetros</h2>
            <div className="sim-fields">
              <label className="sim-field">
                <span>Jogos por célula</span>
                <input type="number" min="1" value={params.n_games}
                  onChange={(e) => setParams({ ...params, n_games: e.target.value })} />
              </label>
              <label className="sim-check">
                <input type="checkbox" checked={params.dry_run}
                  onChange={(e) => setParams({ ...params, dry_run: e.target.checked })} />
                <span>Dry-run (só estima, não chama LLM)</span>
              </label>
            </div>

            {est && (
              <div className="sim-estimate">
                <div className="sim-stat"><b>{est.cells}</b><span>células</span></div>
                <div className="sim-stat"><b>{est.jogadores}</b><span>jogadores</span></div>
                <div className="sim-stat"><b>{est.total}</b><span>sessões</span></div>
                <div className="sim-stat"><b>{est.calls.toLocaleString()}</b><span>chamadas LLM (~)</span></div>
              </div>
            )}
          </section>

          {/* Matriz de condições (somente leitura — vem do arquivo) */}
          <section className="sim-card">
            <h2>Condições (de simulacao.yaml)</h2>
            <div className="sim-cond">
              {cfg.params?.condicoes && Object.entries(cfg.params.condicoes).map(([k, v]) => (
                <div className="sim-cond-row" key={k}>
                  <span className="sim-cond-key">{k}</span>
                  <span className="sim-cond-val">{Array.isArray(v) ? v.join(', ') : String(v)}</span>
                </div>
              ))}
            </div>
            <p className="sim-note">Para mudar as condições/personas, edite os arquivos em research_settings/ e reinicie.</p>
          </section>

          {/* Personas-jogador */}
          <section className="sim-card">
            <h2>Personas-jogador</h2>
            <div className="sim-players">
              {(cfg.jogadores_disponiveis || []).map((j) => (
                <div className="sim-player" key={j.id}>
                  <div className="sim-player-head">
                    <span className="sim-player-name">{j.name}</span>
                    <span className="sim-player-temp">T={j.temperature}</span>
                  </div>
                  {j.description && <p className="sim-player-desc">{j.description}</p>}
                  <div className="sim-player-traits">
                    {Object.entries(j.traits || {}).map(([k, v]) => (
                      <span className="sim-trait" key={k}>{k}: <b>{v}</b></span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <button className="sim-start" onClick={handleStart}>
            ▶ Iniciar simulação
          </button>
        </>
      )}

      {/* Tela de andamento */}
      {runId && (
        <section className="sim-card sim-progress">
          <h2>Andamento</h2>
          <p className="sim-run">execução: <b>{runId}</b></p>
          <div className={`sim-status sim-status--${status?.status || 'running'}`}>
            {status?.status === 'done' ? '✓ Concluída'
              : status?.status === 'error' ? '✗ Concluída com erros'
              : '⟳ Em execução…'}
          </div>
          <div className="sim-bar"><div className="sim-bar-fill" style={{ width: `${pct}%` }} /></div>
          <p className="sim-count">{status?.completed ?? 0} / {status?.total_sessions ?? 0} sessões ({pct}%)</p>
          {status?.current && <p className="sim-current">↳ {status.current}</p>}
          {status?.output_dir && <p className="sim-out">saída: {status.output_dir}</p>}
          {Array.isArray(status?.errors) && status.errors.length > 0 && (
            <div className="sim-errs">
              {status.errors.slice(0, 5).map((e, i) => <p key={i} className="sim-err">✗ {e}</p>)}
            </div>
          )}
          {(status?.status === 'done' || status?.status === 'error') && (
            <button className="sim-start" onClick={() => { setRunId(null); setStatus(null); }}>
              ← Nova simulação
            </button>
          )}
        </section>
      )}
    </div>
  );
}
