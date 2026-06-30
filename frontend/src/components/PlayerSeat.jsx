import PlayerDisplay from "./PlayerDisplay";
import "./PlayerSeat.css";

/**
 * Posiciona um PlayerDisplay angularmente em volta da mesa.
 * `position` = ângulo em graus (0=topo, 90=direita, 180=baixo, -90/270=esquerda).
 * `radius` = distância do centro (px).
 */
export default function PlayerSeat({ player, position, radius = 250, thinking = false, isYou = false }) {
  const style = { "--angle": `${position}deg`, "--radius": `${radius}px` };
  return (
    <div className="seat-container" style={style}>
      <div className="seat-content">
        <PlayerDisplay player={player} thinking={thinking} isYou={isYou} />
      </div>
    </div>
  );
}
