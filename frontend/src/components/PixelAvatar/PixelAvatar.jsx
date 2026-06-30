import { useState, useEffect } from "react";
import "./PixelAvatar.css";

/**
 * Avatar de uma persona.
 *
 * Ordem de fallback:
 *   1. persona.icon é base64 (data:image/...)  → renderiza imagem
 *   2. persona.icon é path/URL (/images/x.png) → renderiza imagem
 *      (com fallback pra default-ai.png se falhar)
 *   3. sem icon → sprite procedural pixel-art baseado no nome
 *
 * size: aresta em px (padrão 42).
 */

function isImageRef(s) {
  if (!s || typeof s !== "string") return false;
  return s.startsWith("data:image") || s.startsWith("/") || s.startsWith("http");
}

function hashStr(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

const SKIN  = ["#e8c89a", "#d8b88a", "#c89878", "#a07858"];
const HAIR  = ["#3a2510", "#7a5530", "#a04050", "#5a3a8a", "#1a4060", "#3a6020"];
const SHIRT = ["#5a3a8a", "#7a5530", "#3a6020", "#a04050", "#1a4060", "#5ec9ff"];
const HAT   = ["#7a5530", "#3a2510", "#a04050", "#1a4060", null, null];
const ACC   = ["beard", "mustache", "glasses", null, null, null];

function pick(arr, h) { return arr[h % arr.length]; }

export default function PixelAvatar({ persona, size = 42, accent = "amber" }) {
  const icon = persona?.icon;
  const [imgSrc, setImgSrc] = useState(isImageRef(icon) ? icon : null);

  useEffect(() => {
    setImgSrc(isImageRef(icon) ? icon : null);
  }, [icon]);

  // Imagem (base64 OU path)
  if (imgSrc) {
    return (
      <div
        className={`pixel-avatar pixel-avatar--img pixel-avatar--${accent}`}
        style={{ width: size, height: size }}
      >
        <img
          src={imgSrc}
          alt={persona?.name || ""}
          onError={() => setImgSrc("/images/default-ai.png")}
        />
      </div>
    );
  }

  // Sprite procedural
  const name = persona?.name || "?";
  const h = hashStr(name);
  const skin  = pick(SKIN, h);
  const hair  = pick(HAIR, h >> 3);
  const shirt = pick(SHIRT, h >> 6);
  const hat   = pick(HAT, h >> 9);
  const acc   = pick(ACC, h >> 12);

  return (
    <div
      className={`pixel-avatar pixel-avatar--${accent}`}
      style={{ width: size, height: size }}
      aria-label={`Avatar de ${name}`}
    >
      <svg viewBox="0 0 16 16" shapeRendering="crispEdges" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <rect x="0" y="0" width="16" height="16" fill="var(--wood-darker)" />
        {hat ? (
          <>
            <rect x="3" y="2" width="10" height="2" fill={hat} />
            <rect x="2" y="3" width="12" height="2" fill={hat} />
          </>
        ) : (
          <>
            <rect x="3" y="2" width="10" height="3" fill={hair} />
            <rect x="2" y="3" width="12" height="2" fill={hair} />
          </>
        )}
        <rect x="4" y={hat ? "5" : "4"} width="8" height="6" fill={skin} />
        <rect x="6" y="7" width="1" height="1" fill="#1a0e08" />
        <rect x="9" y="7" width="1" height="1" fill="#1a0e08" />
        {acc === "glasses" && (
          <>
            <rect x="5" y="6" width="3" height="2" fill="none" stroke="#1a0e08" strokeWidth="0.5" />
            <rect x="8" y="6" width="3" height="2" fill="none" stroke="#1a0e08" strokeWidth="0.5" />
          </>
        )}
        {acc === "mustache" && <rect x="6" y="9" width="4" height="1" fill={hair} />}
        {acc === "beard" && (
          <>
            <rect x="5" y="9" width="6" height="2" fill={hair} />
            <rect x="4" y="10" width="8" height="1" fill={hair} />
          </>
        )}
        {!acc && <rect x="6" y="9" width="4" height="1" fill="#3a2510" />}
        <rect x="2" y="11" width="12" height="5" fill={shirt} />
        <rect x="2" y="11" width="12" height="1" fill="rgba(0,0,0,0.3)" />
      </svg>
    </div>
  );
}
