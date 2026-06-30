import { useState } from "react";
import PlayerSeat from "../components/PlayerSeat";
import PixelAvatar from "../components/PixelAvatar/PixelAvatar";
import ChoicePanel from "../components/ChoicePanel";
import RevealPanel from "../components/RevealPanel";
import UserInput from "../components/UserInput";
import BarAmbient from "../components/BarAmbient/BarAmbient";
import ActIndicator from "../components/ActIndicator/ActIndicator";
import ConversationPanel from "../components/ConversationPanel/ConversationPanel";
import { useT } from "../i18n/i18n";
import "./TableScreen.css";

const TableScreen = ({
  gameState,
  userAvatar,
  onSendIdea,
  onPick,
  onAdvance,
  onTelemetry,
  isLoading,
}) => {
  const t = useT();
  const [inputExpanded, setInputExpanded] = useState(false);

  if (!gameState) {
    return <div className="table-loading">{t("table.loading_table")}</div>;
  }

  const user = gameState.players.find((p) => !p.is_ai);
  const ais = gameState.players.filter((p) => p.is_ai);

  if (user && userAvatar && user.persona) {
    user.persona.icon = userAvatar;
  }

  // IAs ocupam o arco SUPERIOR da mesa; o jogador senta embaixo (90°).
  // IAs ocupam o arco do FUNDO/laterais da mesa, simétrico em torno do topo
  // (-90°). O jogador fica à frente (na caixa de escrita), não na mesa.
  // Assentos numa ELIPSE que acompanha a mesa (mais larga que alta), com as
  // IAs distribuídas UNIFORMEMENTE ao redor. Convenção do PlayerSeat:
  // 0°=topo, 90°=direita, 180°=baixo, -90°=esquerda → posição (r·sinθ, -r·cosθ).
  const numAis = ais.length;
  const SEAT_ANGLES = {
    1: [0],
    2: [-55, 55],
    3: [-120, 0, 120],
    4: [-135, -45, 45, 135], // diagonais: distribuição uniforme em volta da mesa
  };
  const seatAngles =
    SEAT_ANGLES[numAis] ||
    Array.from({ length: numAis }, (_, i) => -180 + ((i + 0.5) * 360) / numAis);

  // Raio da elipse no ângulo θ (semi-eixos RX, RY logo fora da borda da mesa).
  const SEAT_RX = 240;
  const SEAT_RY = 182;
  const seatRadius = (deg) => {
    const a = (deg * Math.PI) / 180;
    const s = Math.sin(a);
    const c = Math.cos(a);
    return 1 / Math.sqrt((s * s) / (SEAT_RX * SEAT_RX) + (c * c) / (SEAT_RY * SEAT_RY));
  };

  const phaseVisual = gameState.phase_name || "discussion";
  const round = gameState.round;
  const totalRounds = gameState.total_rounds || null;

  const phase = gameState.game_phase;
  const isClosing = phaseVisual === "closing";
  const isAiThinking = isLoading && phase === "proposing";
  const inputDisabled = isLoading || phase !== "proposing" || isClosing;

  return (
    <div className={`table-screen ${inputExpanded ? "table-screen--expanded" : ""}`}>
      <ActIndicator phase={phaseVisual} round={round} totalRounds={totalRounds} />

      <main className="bar-room">
        <BarAmbient showLamp={false} />

        <div className="bar-stage">
          <section className="bar-stage-main">
            {!inputExpanded && (
              <div className="bar-stage-table">
                <div className="table-container">
                  <div className="table-lamp" aria-hidden="true" />
                  <div className="table-surface">
                    <div className="table-stain table-stain--1" aria-hidden="true" />
                    <div className="table-stain table-stain--2" aria-hidden="true" />
                    <div className="table-glass table-glass--g1" aria-hidden="true" />
                    <div className="table-glass table-glass--g2" aria-hidden="true" />
                    <div className="table-ashtray" aria-hidden="true"><span className="table-cig" /></div>
                  </div>

                  {ais.map((ai, index) => {
                    const position = seatAngles[index] ?? 0;
                    return (
                      <PlayerSeat
                        key={ai.id}
                        player={ai}
                        position={position}
                        radius={seatRadius(position)}
                        thinking={isAiThinking}
                      />
                    );
                  })}
                </div>
              </div>
            )}

            <section className={`my-area ${inputExpanded ? "my-area--expanded" : ""}`}>
              <button
                className="my-area-toggle"
                onClick={() => setInputExpanded((v) => !v)}
                title={inputExpanded ? t("table.collapse") : t("table.expand")}
              >
                {inputExpanded ? t("table.collapse") : t("table.expand")}
              </button>

              {user && !inputExpanded && (
                <div className="my-seat">
                  <PixelAvatar persona={user.persona} accent="cyan" size={56} />
                  <span className="my-seat-tag">{t("table.you")}</span>
                  <span className="my-seat-name">{user.name}</span>
                </div>
              )}

              <div className="my-area-main">
                <div className="my-area-head">
                  <span className={`my-area-turn ${isAiThinking ? "my-area-turn--wait" : ""}`}>
                    {isAiThinking ? t("table.ais_thinking") : t("table.your_turn")}
                  </span>
                </div>
                <div className="my-area-input">
                  <UserInput
                    onSendIdea={onSendIdea}
                    onTelemetry={onTelemetry}
                    disabled={inputDisabled}
                    expanded={inputExpanded}
                  />
                </div>
              </div>
            </section>
          </section>

          <ConversationPanel
            topic={gameState.topic}
            conversation={gameState.conversation}
            phase={phaseVisual}
            round={round}
            thinking={isAiThinking}
          />
        </div>
      </main>

      {phase === "choosing" && (
        <ChoicePanel options={gameState.choice_options} onPick={onPick} disabled={isLoading} />
      )}

      {phase === "revealing" && (
        <RevealPanel reveal={gameState.round_reveal} user={user} onAdvance={onAdvance} disabled={isLoading} />
      )}
    </div>
  );
};

export default TableScreen;
