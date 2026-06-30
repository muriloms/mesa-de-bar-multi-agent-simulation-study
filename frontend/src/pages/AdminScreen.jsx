import { useEffect, useState } from 'react';
import { getCatalog } from '../services/api';
import './AdminScreen.css';

/**
 * Painel de estrutura (acesso por ?admin=1).
 * Mostra, ao vivo, o que a plataforma leu dos arquivos de temas,
 * composições de mesa e formulários — com contagens, avisos e erros.
 */
export default function AdminScreen() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError('');
    getCatalog()
      .then((res) => setData(res.data))
      .catch((e) => setError(e?.message || 'Falha ao carregar o catálogo'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="admin">
      <header className="admin-head">
        <div>
          <p className="admin-eyebrow">Mesa de Bar · estrutura</p>
          <h1 className="admin-title">Painel de estrutura</h1>
          <p className="admin-sub">O que a plataforma leu dos arquivos no deploy atual.</p>
        </div>
        <button className="admin-reload" onClick={load} disabled={loading}>
          {loading ? '…' : '↻ recarregar'}
        </button>
      </header>

      {error && <p className="admin-error">⚠ {error}</p>}
      {!data && loading && <p className="admin-muted">Carregando…</p>}

      {data && (
        <>
          <div className={`admin-status ${data.ok ? 'admin-status--ok' : 'admin-status--bad'}`}>
            {data.ok ? '✓ Estrutura válida' : '✗ Há erros na estrutura'}
            <span className="admin-status-counts">
              {data.errors.length} erro(s) · {data.warnings.length} aviso(s) · mesa = {data.table_size}
            </span>
          </div>

          {(data.errors.length > 0 || data.warnings.length > 0) && (
            <section className="admin-issues">
              {data.errors.map((e, i) => <p key={`e${i}`} className="admin-issue admin-issue--err">✗ {e}</p>)}
              {data.warnings.map((w, i) => <p key={`w${i}`} className="admin-issue admin-issue--warn">! {w}</p>)}
            </section>
          )}

          {/* TEMAS */}
          <section className="admin-card">
            <div className="admin-card-head">
              <h2>Temas (assunto da mesa)</h2>
              <span className="admin-badge">{data.temas.areas_count} áreas · {data.temas.subtemas_count} subtemas</span>
            </div>
            <p className="admin-src">{data.temas.source}</p>
            <div className="admin-grid">
              {data.temas.areas.map((a) => (
                <div className="admin-pill" key={a.id}>
                  <span className="admin-pill-title">{a.title || a.id}</span>
                  <span className="admin-pill-meta">{a.subtemas_count} subtemas</span>
                </div>
              ))}
            </div>
          </section>

          {/* COMPOSIÇÃO DA MESA */}
          <section className="admin-card">
            <div className="admin-card-head">
              <h2>Composição da mesa</h2>
              <span className="admin-badge">{data.composicao_mesa.themes_count} temas · {data.composicao_mesa.personas_total} personas</span>
            </div>
            <p className="admin-src">{data.composicao_mesa.source}</p>
            <div className="admin-grid">
              {data.composicao_mesa.themes.map((t) => (
                <div className={`admin-pill ${t.personas_count < data.table_size ? 'admin-pill--warn' : ''}`} key={t.id}>
                  <span className="admin-pill-title">{t.title || t.id}</span>
                  <span className="admin-pill-meta">{t.personas_count} personas</span>
                </div>
              ))}
            </div>
          </section>

          {/* FORMULÁRIOS */}
          <section className="admin-card">
            <div className="admin-card-head">
              <h2>Formulários (pré/pós jogo)</h2>
              <span className="admin-badge">{data.formularios.forms_count} formulários · {data.formularios.items_total} itens</span>
            </div>
            <p className="admin-src">{data.formularios.source}</p>
            <div className="admin-forms">
              {data.formularios.forms.map((f) => (
                <div className="admin-form" key={f.id}>
                  <div className="admin-form-head">
                    <span className="admin-form-title">{f.title}</span>
                    <span className="admin-form-moment">{f.moment}</span>
                  </div>
                  <div className="admin-form-meta">
                    {f.items_count} itens · {f.required_count} obrigatórios · {f.sections_count} seções
                  </div>
                  <div className="admin-types">
                    {Object.entries(f.item_types).sort().map(([k, v]) => (
                      <span className="admin-type" key={k}>{k} <b>×{v}</b></span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
          {/* PLATAFORMA */}
          {data.plataforma && data.plataforma.config && (
            <section className="admin-card">
              <div className="admin-card-head">
                <h2>Plataforma (funcionalidades/dinâmicas)</h2>
              </div>
              <p className="admin-src">{data.plataforma.source}</p>
              <div className="admin-grid">
                {Object.entries(data.plataforma.config).map(([k, v]) => (
                  <div className="admin-pill" key={k}>
                    <span className="admin-pill-title">{String(v)}</span>
                    <span className="admin-pill-meta">{k}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* JUIZ */}
          {data.juiz && data.juiz.juiz && (
            <section className="admin-card">
              <div className="admin-card-head">
                <h2>Juiz</h2>
                <span className="admin-badge">{data.juiz.juiz.name}</span>
              </div>
              <p className="admin-src">{data.juiz.source}</p>
              <div className="admin-grid">
                <div className="admin-pill"><span className="admin-pill-title">{data.juiz.juiz.criterion}</span><span className="admin-pill-meta">critério</span></div>
                <div className="admin-pill"><span className="admin-pill-title">{String(data.juiz.juiz.blind_to_source)}</span><span className="admin-pill-meta">cego à autoria</span></div>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
