import "./BarAmbient.css";

/**
 * Camadas decorativas do bar — puramente visuais. Renderiza no fundo
 * da TableScreen, sob a mesa e jogadores.
 *
 * Props:
 *   - showCounter (default true): balcão ao fundo com prateleira+espelho+jukebox+neon
 *   - showLamp    (default true): lâmpada amarela pendurada com halo
 *   - showVignette(default true): vinheta escura nas bordas
 */
export default function BarAmbient({
  showCounter = true,
  showLamp = true,
  showVignette = true,
}) {
  return (
    <>
      {showCounter && (
        <div className="bar-counter" aria-hidden="true">
          <div className="bar-shelves">
            <div className="bar-shelf-row">
              <span className="bar-bot bar-bot--g" style={{ left: "1%" }} />
              <span className="bar-bot bar-bot--r" style={{ left: "5%" }} />
              <span className="bar-bot bar-bot--b" style={{ left: "9%" }} />
              <span className="bar-bot bar-bot--y" style={{ left: "13%" }} />
              <span className="bar-bot bar-bot--g" style={{ left: "17%" }} />
              <span className="bar-bot bar-bot--r" style={{ left: "21%" }} />
              <span className="bar-bot bar-bot--b" style={{ left: "25%" }} />
              <span className="bar-bot bar-bot--y" style={{ left: "29%" }} />
              <span className="bar-bot bar-bot--g" style={{ left: "33%" }} />
              <span className="bar-bot bar-bot--r" style={{ left: "37%" }} />
              <span className="bar-bot bar-bot--b" style={{ left: "41%" }} />
              <span className="bar-bot bar-bot--y" style={{ left: "45%" }} />
            </div>
            <div className="bar-shelf-row">
              <span className="bar-bot bar-bot--r" style={{ left: "3%" }} />
              <span className="bar-bot bar-bot--b" style={{ left: "7%" }} />
              <span className="bar-bot bar-bot--g" style={{ left: "11%" }} />
              <span className="bar-bot bar-bot--y" style={{ left: "15%" }} />
              <span className="bar-bot bar-bot--r" style={{ left: "19%" }} />
              <span className="bar-bot bar-bot--g" style={{ left: "23%" }} />
              <span className="bar-bot bar-bot--b" style={{ left: "27%" }} />
              <span className="bar-bot bar-bot--y" style={{ left: "31%" }} />
              <span className="bar-bot bar-bot--r" style={{ left: "35%" }} />
              <span className="bar-bot bar-bot--g" style={{ left: "39%" }} />
              <span className="bar-bot bar-bot--y" style={{ left: "43%" }} />
            </div>
          </div>
          <div className="bar-mirror" />
          <div className="bar-juke">
            <span className="bar-juke-light" />
          </div>
          <div className="bar-neon">BAR</div>
        </div>
      )}

      {showLamp && (
        <div className="bar-lamp" aria-hidden="true">
          <div className="bar-lamp-cord" />
          <div className="bar-lamp-cone" />
          <div className="bar-lamp-bulb" />
        </div>
      )}

      {showLamp && <div className="bar-halo" aria-hidden="true" />}

      {showVignette && <div className="bar-vignette" aria-hidden="true" />}
    </>
  );
}
