import "./PlayerDisplay.css";
import PixelAvatar from "./PixelAvatar/PixelAvatar";

/**
 * Card de um jogador na mesa (cadeira). v2: sem economia (sem saldo/drinks).
 *
 * Props:
 *   - player: { id, name, persona, is_ai }
 *   - thinking: bool (anima borda)
 *   - isYou: bool (destaca o assento do jogador humano)
 */
export default function PlayerDisplay({ player, thinking = false, isYou = false }) {
  if (!player) return null;

  let accent = "amber";
  if (!player.is_ai) accent = "cyan";
  else if (thinking) accent = "purple";

  return (
    <div
      className={[
        "player-display",
        player.is_ai ? "player-display--ai" : "player-display--user",
        thinking ? "player-display--thinking" : "",
        isYou ? "player-display--you" : "",
      ].join(" ")}
    >
      {isYou && <span className="player-display-youtag">você</span>}
      <PixelAvatar persona={player.persona} accent={accent} size={48} />
      <div className="player-display-info">
        <div className="player-display-name">{player.name}</div>
        {player.persona?.role && (
          <div className="player-display-role">{player.persona.role}</div>
        )}
      </div>
    </div>
  );
}
