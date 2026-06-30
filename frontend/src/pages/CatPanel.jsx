import { useState, useEffect } from "react";
import { getCatItems, submitCatRatings } from "../services/api";
import { useT } from "../i18n/i18n";
import "./CatPanel.css";

const DIMS = ["novelty", "quality", "refinement"];

export default function CatPanel({ studyId }) {
  const t = useT();
  const [judgeId, setJudgeId] = useState("");
  const [started, setStarted] = useState(false);
  const [items, setItems] = useState([]);
  const [ratings, setRatings] = useState({});   // item_id -> {novelty,quality,refinement}
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!started) return;
    setLoading(true);
    getCatItems(studyId)
      .then((res) => setItems(res.data || []))
      .catch(() => setError(t("cat.load_error")))
      .finally(() => setLoading(false));
  }, [started, studyId]);

  const setRating = (itemId, dim, val) => {
    setRatings((prev) => ({ ...prev, [itemId]: { ...(prev[itemId] || {}), [dim]: val } }));
  };

  const ratedCount = items.filter((it) => {
    const r = ratings[it.item_id] || {};
    return DIMS.every((d) => r[d]);
  }).length;
  const allRated = items.length > 0 && ratedCount === items.length;

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = items.map((it) => ({ item_id: it.item_id, ...(ratings[it.item_id] || {}) }));
      await submitCatRatings(studyId, judgeId.trim(), payload);
      setDone(true);
    } catch {
      setError(t("cat.submit_error"));
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="cat-screen">
        <div className="cat-done">
          <h1>{t("cat.thanks_title")}</h1>
          <p>{t("cat.thanks_body")}</p>
        </div>
      </div>
    );
  }

  if (!started) {
    return (
      <div className="cat-screen">
        <div className="cat-intro">
          <h1>{t("cat.title")}</h1>
          <p>{t("cat.intro")}</p>
          <label className="cat-label">{t("cat.judge_name")}</label>
          <input
            className="cat-input"
            value={judgeId}
            onChange={(e) => setJudgeId(e.target.value)}
            placeholder={t("cat.judge_placeholder")}
          />
          <button
            className="cat-btn cat-btn--prim"
            disabled={!judgeId.trim()}
            onClick={() => setStarted(true)}
          >
            {t("cat.begin")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="cat-screen">
      <header className="cat-header">
        <h1>{t("cat.title")}</h1>
        <span className="cat-progress">{ratedCount}/{items.length}</span>
      </header>

      {error && <p className="cat-error">{error}</p>}
      {loading && <p className="cat-loading">{t("common.wait")}</p>}

      <div className="cat-list">
        {items.map((it, idx) => {
          const r = ratings[it.item_id] || {};
          return (
            <div key={it.item_id} className="cat-card">
              <div className="cat-card-num">#{idx + 1}</div>
              <p className="cat-card-text">{it.text}</p>
              <div className="cat-dims">
                {DIMS.map((dim) => (
                  <div key={dim} className="cat-dim">
                    <span className="cat-dim-label">{t(`cat.dim_${dim}`)}</span>
                    <div className="cat-scale">
                      {[1, 2, 3, 4, 5].map((v) => (
                        <button
                          key={v}
                          className={`cat-scale-btn ${r[dim] === v ? "cat-scale-btn--on" : ""}`}
                          onClick={() => setRating(it.item_id, dim, v)}
                          aria-label={`${t(`cat.dim_${dim}`)} ${v}`}
                        >
                          {v}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <footer className="cat-footer">
        <button className="cat-btn cat-btn--prim" disabled={!allRated || loading} onClick={handleSubmit}>
          {allRated ? t("cat.submit") : t("cat.rate_all")}
        </button>
      </footer>
    </div>
  );
}
