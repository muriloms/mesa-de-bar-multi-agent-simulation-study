/**
 * Slider numérico contínuo.
 */
export default function SliderItem({ item, value, onChange }) {
  const min = item.min ?? 0;
  const max = item.max ?? 100;
  const step = item.step ?? 1;
  const current = value !== null && value !== undefined ? value : (item.default ?? Math.round((min + max) / 2));

  return (
    <div className="instrument-slider">
      <div className="instrument-slider-row">
        <span className="instrument-slider-label">{item.min_label || min}</span>
        <input
          type="range"
          className="instrument-slider-range"
          min={min}
          max={max}
          step={step}
          value={current}
          onChange={(e) => onChange(parseFloat(e.target.value))}
        />
        <span className="instrument-slider-label">{item.max_label || max}</span>
      </div>
      <div className="instrument-slider-value">{current}</div>
    </div>
  );
}
