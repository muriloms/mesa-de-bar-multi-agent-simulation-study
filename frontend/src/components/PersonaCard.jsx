import "./PersonaCard.css";
import PixelAvatar from "./PixelAvatar/PixelAvatar";

export default function PersonaCard({ persona, onClick }) {
  const isEmpty = !persona?.name?.trim();

  return (
    <button type="button" className="persona-card" onClick={onClick}>
      {isEmpty ? (
        <div className="persona-card-icon">+</div>
      ) : (
        <PixelAvatar persona={persona} accent="amber" size={48} />
      )}
      {isEmpty ? (
        <div className="persona-card-empty">Clique pra definir</div>
      ) : (
        <>
          <div className="persona-card-name">{persona.name}</div>
          {persona.role && <div className="persona-card-role">{persona.role}</div>}
        </>
      )}
    </button>
  );
}
