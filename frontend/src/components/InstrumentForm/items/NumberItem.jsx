/**
 * Item numérico (idade, quantidade...) com min/max/step e unidade opcional.
 */
export default function NumberItem({ item, value, onChange }) {
  const handle = (e) => {
    const v = e.target.value;
    if (v === "") { onChange(null); return; }
    onChange(Number(v));
  };
  return (
    <div className="instrument-number">
      <input
        type="number"
        className="instrument-input instrument-input--number"
        value={value ?? ""}
        min={item.min ?? undefined}
        max={item.max ?? undefined}
        step={item.step ?? 1}
        placeholder={item.placeholder || ""}
        onChange={handle}
      />
      {item.unit && <span className="instrument-number-unit">{item.unit}</span>}
    </div>
  );
}
