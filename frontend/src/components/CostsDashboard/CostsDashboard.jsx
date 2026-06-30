import { useEffect, useState } from "react";
import { getSessionCosts } from "../../services/api";
import { useT } from "../../i18n/i18n";
import "./CostsDashboard.css";

export default function CostsDashboard({ sessionId, onClose }) {
  const t = useT();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    let timer = null;

    const load = async () => {
      try {
        const res = await getSessionCosts(sessionId);
        if (!cancelled) {
          setData(res.data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError("Falha ao carregar custos.");
      }
      if (!cancelled) timer = setTimeout(load, 3000);
    };

    load();
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, [sessionId]);

  if (!data) {
    return (
      <div className="costs-overlay" onClick={onClose}>
        <div className="costs-modal" onClick={(e) => e.stopPropagation()}>
          <div className="costs-loading">{error || t("common.loading")}</div>
        </div>
      </div>
    );
  }

  const tot = data.total;
  const fmt$ = (n) => `$ ${(n || 0).toFixed(4)}`;
  const fmtTok = (n) => (n || 0).toLocaleString("pt-BR");

  return (
    <div className="costs-overlay" onClick={onClose}>
      <div className="costs-modal" onClick={(e) => e.stopPropagation()}>
        <header className="costs-header">
          <h2>{t("costs.title")}</h2>
          <button className="costs-close" onClick={onClose}>×</button>
        </header>

        {/* Totais */}
        <section className="costs-section">
          <h3>{t("costs.totals")}</h3>
          <div className="costs-grid">
            <Stat label={t("costs.calls")} value={tot.calls} />
            <Stat label={t("costs.tokens_in")} value={fmtTok(tot.tokens_in)} />
            <Stat label={t("costs.tokens_out")} value={fmtTok(tot.tokens_out)} />
            <Stat label={t("costs.cost_total")} value={fmt$(tot.cost_usd)} accent="amber" />
            <Stat label={t("costs.latency_avg")} value={`${tot.avg_latency_ms} ms`} />
            <Stat label={t("costs.latency_median")} value={`${tot.median_latency_ms} ms`} />
          </div>
        </section>

        {/* Por modelo */}
        <section className="costs-section">
          <h3>{t("costs.by_model")}</h3>
          <table className="costs-table">
            <thead>
              <tr>
                <th>{t("costs.by_model")}</th>
                <th>{t("costs.calls")}</th>
                <th>In</th>
                <th>Out</th>
                <th>{t("costs.cost_total")}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.by_model).map(([k, v]) => (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{v.calls}</td>
                  <td>{fmtTok(v.tokens_in)}</td>
                  <td>{fmtTok(v.tokens_out)}</td>
                  <td className="costs-cell-amber">{fmt$(v.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Por ator */}
        <section className="costs-section">
          <h3>{t("costs.by_actor")}</h3>
          <table className="costs-table">
            <thead>
              <tr>
                <th>{t("costs.by_actor")}</th>
                <th>{t("costs.calls")}</th>
                <th>In</th>
                <th>Out</th>
                <th>{t("costs.cost_total")}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.by_actor).map(([k, v]) => (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{v.calls}</td>
                  <td>{fmtTok(v.tokens_in)}</td>
                  <td>{fmtTok(v.tokens_out)}</td>
                  <td className="costs-cell-amber">{fmt$(v.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Por prompt */}
        <section className="costs-section">
          <h3>{t("costs.by_prompt")}</h3>
          <table className="costs-table">
            <thead>
              <tr>
                <th>{t("costs.by_prompt")}</th>
                <th>{t("costs.calls")}</th>
                <th>{t("costs.cost_total")}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.by_prompt).map(([k, v]) => (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{v.calls}</td>
                  <td className="costs-cell-amber">{fmt$(v.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Últimas chamadas */}
        <section className="costs-section">
          <h3>{t("costs.recent")}</h3>
          <table className="costs-table costs-table--small">
            <thead>
              <tr>
                <th>—</th>
                <th>{t("costs.by_prompt")}</th>
                <th>{t("costs.by_actor")}</th>
                <th>Tokens</th>
                <th>—</th>
                <th>{t("costs.cost_total")}</th>
                <th>—</th>
              </tr>
            </thead>
            <tbody>
              {data.recent.slice().reverse().map((c) => (
                <tr key={c.call_id}>
                  <td>{(c.timestamp || "").slice(11, 19)}</td>
                  <td>{c.prompt_id}</td>
                  <td>{c.actor || "—"}{c.actor_id && c.actor_id !== c.actor ? `:${c.actor_id}` : ""}</td>
                  <td>{c.tokens_in}/{c.tokens_out}</td>
                  <td>{c.latency_ms || "—"}ms</td>
                  <td className="costs-cell-amber">{fmt$(c.cost_usd)}</td>
                  <td className={c.parse_status === "ok" ? "costs-ok" : "costs-warn"}>{c.parse_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <footer className="costs-footer">
          {t("costs.footer")}
        </footer>
      </div>
    </div>
  );
}

function Stat({ label, value, accent }) {
  return (
    <div className="costs-stat">
      <div className="costs-stat-label">{label}</div>
      <div className={`costs-stat-value ${accent ? `costs-stat-value--${accent}` : ""}`}>{value}</div>
    </div>
  );
}
