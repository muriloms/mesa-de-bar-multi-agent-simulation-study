import { useEffect, useState } from "react";

/**
 * Ranking via drag-and-drop nativo HTML5.
 *
 * Inicializa com a ordem das `options` do item, ou com o `value` salvo.
 * Em mobile, fallback usa botões ↑/↓ pra subir/descer cada item.
 */
export default function RankingItem({ item, value, onChange }) {
  const initial = Array.isArray(value) && value.length === (item.options?.length || 0)
    ? value
    : (item.options || []);

  const [order, setOrder] = useState(initial);
  const [dragging, setDragging] = useState(null);

  // Sincroniza se as options mudarem
  useEffect(() => {
    if (!Array.isArray(value) || value.length !== (item.options?.length || 0)) {
      setOrder(item.options || []);
      onChange(item.options || []);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.options]);

  const move = (idx, delta) => {
    const target = idx + delta;
    if (target < 0 || target >= order.length) return;
    const next = order.slice();
    [next[idx], next[target]] = [next[target], next[idx]];
    setOrder(next);
    onChange(next);
  };

  const handleDragStart = (idx) => setDragging(idx);
  const handleDragOver = (e, idx) => {
    e.preventDefault();
    if (dragging === null || dragging === idx) return;
    const next = order.slice();
    const [moved] = next.splice(dragging, 1);
    next.splice(idx, 0, moved);
    setDragging(idx);
    setOrder(next);
    onChange(next);
  };
  const handleDragEnd = () => setDragging(null);

  return (
    <ol className="instrument-ranking">
      {order.map((opt, i) => (
        <li
          key={opt}
          className={`ranking-row ${dragging === i ? "ranking-row--drag" : ""}`}
          draggable
          onDragStart={() => handleDragStart(i)}
          onDragOver={(e) => handleDragOver(e, i)}
          onDragEnd={handleDragEnd}
        >
          <span className="ranking-rank">{i + 1}.</span>
          <span className="ranking-text">{opt}</span>
          <span className="ranking-controls">
            <button
              type="button"
              className="ranking-btn"
              onClick={() => move(i, -1)}
              disabled={i === 0}
              aria-label="Subir"
              title="Subir"
            >▲</button>
            <button
              type="button"
              className="ranking-btn"
              onClick={() => move(i, 1)}
              disabled={i === order.length - 1}
              aria-label="Descer"
              title="Descer"
            >▼</button>
            <span className="ranking-grip" title="Arraste para reordenar">⋮⋮</span>
          </span>
        </li>
      ))}
    </ol>
  );
}
