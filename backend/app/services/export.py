"""Exportação completa de uma sessão como ZIP.

Empacota tudo da pasta `data/sessions/<id>/` MAIS arquivos derivados
gerados na hora:
  - stats.json: agregações da sessão (rodadas, vencedores, stances, duração)
  - costs.json: dashboard de custos LLM
  - ideia.md: ideia organizada em markdown legível
  - README.md: explicação de cada arquivo

A ideia é que o pesquisador (ou o próprio usuário) tenha TUDO em um único
ZIP, sem precisar voltar à plataforma pra ver estatísticas ou converter
formatos.
"""
import io
import json
import zipfile
from pathlib import Path
from typing import List

from core import config
from core.exceptions import SessionNotFoundError
from persistence import paths


_README_TEMPLATE = """# Mesa de Bar — Sessão `{session_id}`

Pacote de dados gerado para análise externa.

## Conteúdo principal (capturado durante a sessão)

| Arquivo | Descrição |
|---|---|
| `manifest.json` | Metadados da sessão: id, timestamps, **protocolo**, **modelo LLM**, seed, idioma, **composição escolhida**, lista de personas com perfis completos, snapshot dos prompts ativos. |
| `protocol.json` | Cópia congelada do protocolo aplicado (rodadas, quem_avanca, cegueira de fonte na escolha, modo de raciocínio das personas, critério do juiz, viés do dono, memória, telemetria, instrumentos). |
| `events.jsonl` | Toda decisão da sessão como evento JSON append-only, uma linha por evento. |
| `llm_calls.jsonl` | Toda chamada LLM da sessão: prompt versionado (id+versão+sha256), prompt renderizado, parâmetros, resposta crua e parseada, tokens, latência. |
| `transcript.json` | Conversa final estruturada: tópico, mensagens, síntese final. |
| `transcript.md` | Mesma conversa em Markdown legível. |
| `final_idea.json` | Síntese do Dono do Bar + estruturação organizada (título, problema, solução, features, público, impacto, próximos passos). |
| `instruments/*.json` | Respostas aos questionários (pre_session, post_session). Cada arquivo contém ordem de resposta, tempo por item, duração total. |
| `instruments_def/*.json` | **Definição** (perguntas, escalas, rótulos, opções) de cada instrumento usado nesta sessão, na versão exata aplicada. Necessária pra pontuar/interpretar as respostas — os formulários podem mudar entre versões. |

## Conteúdo derivado (gerado no momento do download)

| Arquivo | Descrição |
|---|---|
| `stats.json` | Estatísticas agregadas: duração, rodadas, total apostado, distribuição de stances (complement/counter/redirect), vitórias e drinks por persona, fases percorridas. |
| `costs.json` | Dashboard de custos LLM: total de chamadas, tokens in/out, custo USD, latência média/mediana, breakdown por modelo / ator / prompt, lista das últimas chamadas. |
| `ideia.md` | A ideia organizada como markdown legível — pronto para colar em doc / wiki / email. |

## Formato dos eventos

Cada linha de `events.jsonl` segue:

```json
{{
  "event_id": "evt_...",
  "session_id": "{session_id}",
  "timestamp": "ISO-8601 UTC com ms",
  "elapsed_ms": 1234,
  "type": "round.proposal_submitted",
  "actor": "user | ai_<id> | judge | system",
  "phase": "discussion | closing",
  "round": 3,
  "payload": {{ ... }}
}}
```

Tipos de evento (v2) incluem: `session.created`, `study.assigned`,
`round.started`, `round.proposal_submitted`, `persona.reflected`,
`round.choices_revealed`, `player.picked`, `judge.picked`,
`round.choices_compared`, `player.judged`, `round.idea_advanced`,
`user.passed`, `input.keystroke_log`, `phase.entered`,
`instrument.submitted`, `session.summary_generated`, `lab.structured`.

## Reprodutibilidade

Pra reproduzir esta sessão:

1. Use o seed em `manifest.json["seed"]`
2. Use o protocolo em `protocol.json` (copie pra `protocols/replay.yaml`)
3. Use a mesma composição (se houver) — `manifest.json["composition"]`
4. Use os mesmos prompts (mesmas versões e hashes em `manifest.json["prompts"]`)

Os mesmos provedores de LLM podem dar respostas diferentes mesmo com seed fixo
(especialmente Gemini, que ainda não respeita seed na API). OpenAI com seed
tem reprodutibilidade aproximada.

---
Gerado pelo Mesa de Bar — exporte criado em runtime.
"""


def export_session_zip(session_id: str) -> bytes:
    """Devolve bytes de um ZIP com a pasta da sessão + arquivos derivados."""
    session_dir = paths.session_dir(session_id)
    if not session_dir.exists():
        raise SessionNotFoundError(session_id)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Adiciona todos os arquivos persistidos preservando estrutura
        for path in sorted(session_dir.rglob("*")):
            if path.is_file():
                arcname = f"{session_id}/{path.relative_to(session_dir)}"
                zf.write(path, arcname=arcname)

        # 2. Arquivos derivados — gerados na hora.
        # Imports tardios pra evitar ciclo (services.stats usa services.costs).
        try:
            from services.stats import compute_session_stats
            stats = compute_session_stats(session_id)
            zf.writestr(
                f"{session_id}/stats.json",
                json.dumps(stats, ensure_ascii=False, indent=2),
            )
        except Exception as e:
            zf.writestr(
                f"{session_id}/stats.json",
                json.dumps({"error": str(e)}, ensure_ascii=False, indent=2),
            )

        try:
            from services.costs import compute_session_costs
            costs = compute_session_costs(session_id)
            zf.writestr(
                f"{session_id}/costs.json",
                json.dumps(costs, ensure_ascii=False, indent=2),
            )
        except Exception as e:
            zf.writestr(
                f"{session_id}/costs.json",
                json.dumps({"error": str(e)}, ensure_ascii=False, indent=2),
            )

        try:
            from services.idea_export import load_idea, idea_to_markdown
            idea = load_idea(session_id)
            # tópico vem do manifest
            manifest_path = session_dir / "manifest.json"
            topic = ""
            if manifest_path.exists():
                m = json.loads(manifest_path.read_text(encoding="utf-8"))
                topic = m.get("topic", "")
            md = idea_to_markdown(idea, topic=topic)
            zf.writestr(f"{session_id}/ideia.md", md)
        except Exception as e:
            zf.writestr(
                f"{session_id}/ideia.md",
                f"# Erro ao gerar ideia em markdown\n\n{e}\n",
            )

        # 2b. Definições dos instrumentos usados (perguntas/escalas/rótulos),
        # na versão exata — necessárias pra pontuar respostas que podem mudar.
        try:
            from instruments.loader import load_instrument
            used_ids = set()
            instruments_resp_dir = session_dir / "instruments"
            if instruments_resp_dir.exists():
                for f in instruments_resp_dir.glob("*.json"):
                    used_ids.add(f.stem)
            manifest_path = session_dir / "manifest.json"
            if manifest_path.exists():
                m = json.loads(manifest_path.read_text(encoding="utf-8"))
                for k in ("pre_session_instrument", "post_session_instrument"):
                    if m.get(k):
                        used_ids.add(m[k])
            for iid in sorted(used_ids):
                try:
                    inst = load_instrument(iid)
                    zf.writestr(
                        f"{session_id}/instruments_def/{iid}.json",
                        inst.model_dump_json(indent=2),
                    )
                except Exception:
                    continue
        except Exception:
            pass

        # 3. README explicativo (auto-gerado, não persistido)
        readme = _README_TEMPLATE.format(session_id=session_id)
        zf.writestr(f"{session_id}/README.md", readme)

    return buf.getvalue()


def list_sessions() -> List[dict]:
    """Lista sessões disponíveis com metadados básicos do manifest."""
    if not config.SESSIONS_DIR.exists():
        return []
    out = []
    for d in sorted(config.SESSIONS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        manifest_path = d / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({
            "session_id": m.get("session_id", d.name),
            "started_at": m.get("started_at"),
            "finished_at": m.get("finished_at"),
            "status": m.get("status"),
            "topic": m.get("topic", ""),
            "user_name": m.get("user_name", ""),
            "protocol_id": m.get("protocol_id"),
            "protocol_version": m.get("protocol_version"),
            "language": m.get("language"),
            "composition": m.get("composition"),
        })
    return out
