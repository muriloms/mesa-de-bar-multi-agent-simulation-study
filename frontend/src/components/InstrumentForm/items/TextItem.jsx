/**
 * Item de texto livre (curto ou longo).
 */
export default function TextItem({ item, value, onChange }) {
  const isLong = item.type === "text_long";
  const Tag = isLong ? "textarea" : "input";
  return (
    <Tag
      className={`instrument-input ${isLong ? "instrument-input--long" : ""}`}
      type={isLong ? undefined : "text"}
      value={value || ""}
      placeholder={item.placeholder || ""}
      maxLength={item.max_length || undefined}
      rows={isLong ? 4 : undefined}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}
