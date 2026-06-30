/**
 * Single select: clique escolhe uma opção entre várias.
 */
export function SingleSelectItem({ item, value, onChange }) {
  return (
    <div className="instrument-options">
      {(item.options || []).map((opt) => (
        <button
          key={opt}
          type="button"
          className={`option-btn ${value === opt ? "option-btn--on" : ""}`}
          onClick={() => onChange(opt)}
        >
          {value === opt ? "● " : "○ "}{opt}
        </button>
      ))}
    </div>
  );
}

/**
 * Multi select: clique liga/desliga cada opção. Valor é array.
 */
export function MultiSelectItem({ item, value, onChange }) {
  const arr = Array.isArray(value) ? value : [];
  const toggle = (opt) => {
    const next = arr.includes(opt) ? arr.filter(x => x !== opt) : [...arr, opt];
    onChange(next);
  };
  return (
    <div className="instrument-options">
      {(item.options || []).map((opt) => {
        const on = arr.includes(opt);
        return (
          <button
            key={opt}
            type="button"
            className={`option-btn ${on ? "option-btn--on" : ""}`}
            onClick={() => toggle(opt)}
          >
            {on ? "▣ " : "▢ "}{opt}
          </button>
        );
      })}
    </div>
  );
}
