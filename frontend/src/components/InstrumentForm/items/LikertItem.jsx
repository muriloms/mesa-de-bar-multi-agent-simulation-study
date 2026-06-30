/**
 * Escala Likert 1-N com rótulos opcionais nas extremidades.
 *
 * Renderiza N botões redondos. Selecionado fica em destaque âmbar.
 * Mostra rótulo do ponto selecionado abaixo (se existir).
 */
export default function LikertItem({ item, value, onChange }) {
  const scale = item.scale || 5;
  const labels = item.labels || [];
  const points = Array.from({ length: scale }, (_, i) => i + 1);

  return (
    <div className="instrument-likert">
      <div className="instrument-likert-row">
        {points.map((n) => {
          const selected = value === n;
          const label = labels[n - 1];
          return (
            <button
              key={n}
              type="button"
              className={`likert-btn ${selected ? "likert-btn--on" : ""}`}
              onClick={() => onChange(n)}
              title={label || `Opção ${n}`}
            >
              {n}
            </button>
          );
        })}
      </div>
      {labels.length === scale && (
        <div className="instrument-likert-extremes">
          <span>{labels[0]}</span>
          <span>{labels[labels.length - 1]}</span>
        </div>
      )}
      {value && labels[value - 1] && (
        <div className="instrument-likert-current">
          {value}: <strong>{labels[value - 1]}</strong>
        </div>
      )}
    </div>
  );
}
