import { useEffect, useRef, useState } from "react";
import TextItem from "./items/TextItem";
import NumberItem from "./items/NumberItem";
import LikertItem from "./items/LikertItem";
import { SingleSelectItem, MultiSelectItem } from "./items/SelectItems";
import SliderItem from "./items/SliderItem";
import RankingItem from "./items/RankingItem";
import { useT } from "../../i18n/i18n";
import "./InstrumentForm.css";

export default function InstrumentForm({ instrument, onSubmit, onCancel, allowSkip = false }) {
  const t = useT();
  const [values, setValues] = useState({});
  const startedAtRef = useRef(null);
  const itemFirstTouchRef = useRef({});  // { itemId: ms }
  const itemLastTouchRef = useRef({});   // { itemId: ms }
  const orderRef = useRef([]);            // ordem 1ª interação

  // Inicializa start
  useEffect(() => {
    startedAtRef.current = {
      iso: new Date().toISOString(),
      perf: performance.now(),
    };
  }, [instrument.id]);

  const allItems = instrument.sections.flatMap(s => s.items);

  const setValue = (item, value) => {
    const itemId = item.id;
    const now = performance.now();
    if (!itemFirstTouchRef.current[itemId]) {
      itemFirstTouchRef.current[itemId] = now;
      orderRef.current.push(itemId);
    }
    itemLastTouchRef.current[itemId] = now;
    setValues((prev) => ({ ...prev, [itemId]: value }));
  };

  const renderItem = (item) => {
    const value = values[item.id];
    const onChange = (v) => setValue(item, v);
    switch (item.type) {
      case "text_short":
      case "text_long":
        return <TextItem item={item} value={value} onChange={onChange} />;
      case "number":
        return <NumberItem item={item} value={value} onChange={onChange} />;
      case "likert":
        return <LikertItem item={item} value={value} onChange={onChange} />;
      case "single_select":
        return <SingleSelectItem item={item} value={value} onChange={onChange} />;
      case "multi_select":
        return <MultiSelectItem item={item} value={value} onChange={onChange} />;
      case "slider":
        return <SliderItem item={item} value={value} onChange={onChange} />;
      case "ranking":
        return <RankingItem item={item} value={value} onChange={onChange} />;
      default:
        return <em>Tipo de item não suportado: {item.type}</em>;
    }
  };

  // Verifica se itens required estão respondidos
  const requiredMissing = allItems
    .filter(it => it.required && !hasValue(values[it.id], it.type))
    .map(it => it.id);
  const canSubmit = requiredMissing.length === 0;

  const handleSubmit = () => {
    const start = startedAtRef.current;
    if (!start) return;
    const submittedAt = new Date().toISOString();
    const duration = Math.round(performance.now() - start.perf);

    const responses = Object.entries(values).map(([item_id, value]) => {
      const first = itemFirstTouchRef.current[item_id];
      const last = itemLastTouchRef.current[item_id];
      return {
        item_id,
        value,
        time_spent_ms: (first != null && last != null) ? Math.round(last - first) : null,
        answered_at: null,  // valor agregado já está no order
      };
    });

    onSubmit({
      started_at: start.iso,
      submitted_at: submittedAt,
      duration_ms: duration,
      responses,
      response_order: orderRef.current.slice(),
    });
  };

  return (
    <div className="instrument-overlay">
      <div className="instrument-modal">
        <header className="instrument-header">
          <div>
            <h2 className="instrument-title">{instrument.title}</h2>
            {instrument.description && (
              <p className="instrument-description">{instrument.description}</p>
            )}
          </div>
        </header>

        <div className="instrument-privacy" role="note">
          <span className="instrument-privacy-mark" aria-hidden="true">🔒</span>
          <p className="instrument-privacy-text">{t("instrument.privacy_notice")}</p>
        </div>

        <div className="instrument-body">
          {instrument.sections.map((section) => (
            <section key={section.id} className="instrument-section">
              {section.title && <h3 className="instrument-section-title">{section.title}</h3>}
              {section.description && <p className="instrument-section-desc">{section.description}</p>}
              <div className="instrument-items">
                {section.items.map((item) => (
                  <div key={item.id} className={`instrument-item ${item.required && !hasValue(values[item.id], item.type) ? "instrument-item--required" : ""}`}>
                    <label className="instrument-item-question">
                      {item.question}
                      {item.required && <span className="required-mark"> *</span>}
                    </label>
                    {item.description && <p className="instrument-item-desc">{item.description}</p>}
                    <div className="instrument-item-control">
                      {renderItem(item)}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>

        <footer className="instrument-footer">
          <div className="instrument-footer-status">
            {!canSubmit && (
              <span className="instrument-warn">
                {t("instrument.missing_required", { count: requiredMissing.length })}
              </span>
            )}
          </div>
          <div className="instrument-footer-actions">
            {allowSkip && onCancel && (
              <button type="button" className="instrument-btn-skip" onClick={onCancel}>
                {t("instrument.skip")}
              </button>
            )}
            <button
              type="button"
              className="instrument-btn-submit"
              onClick={handleSubmit}
              disabled={!canSubmit}
            >
              {t("instrument.submit")}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

function hasValue(v, type) {
  if (v === null || v === undefined) return false;
  if (type === "text_short" || type === "text_long") return typeof v === "string" && v.trim().length > 0;
  if (type === "multi_select") return Array.isArray(v) && v.length > 0;
  if (type === "ranking") return Array.isArray(v) && v.length > 0;
  if (typeof v === "number") return true;
  if (typeof v === "string") return v.length > 0;
  return Boolean(v);
}
