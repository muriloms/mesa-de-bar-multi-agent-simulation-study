"""Verifica que export_session_zip inclui stats, costs, ideia.md e instruments."""
import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def _setup_minimal_session(tmp_path, monkeypatch):
    """Cria pasta de sessão mínima pra teste."""
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")

    sid = "test_export_sid"
    session_dir = tmp_path / "sessions" / sid
    session_dir.mkdir(parents=True)

    # Manifest com composition_id e personas_detail
    manifest = {
        "session_id": sid,
        "started_at": "2026-05-12T10:00:00.000Z",
        "finished_at": "2026-05-12T10:30:00.000Z",
        "status": "summary_ready",
        "protocol_id": "default",
        "protocol_version": "2.0.0",
        "language": "pt",
        "seed": 12345,
        "llm": {"provider": "google", "model": "gemini-1.5-flash"},
        "user_name": "Mateus",
        "topic": "Cidade do futuro",
        "personas": ["Tesla", "Curie"],
        "personas_detail": [
            {"name": "Tesla", "role": "Inventor", "goal": "g", "description": "d", "instructions": "i"},
        ],
        "composition": {
            "id": "inventores_cientistas",
            "title": "Inventores e cientistas",
            "description": "...",
            "tags": ["ciencia"],
        },
        "prompts": [{"id": "proposal", "version": "v1"}],
    }
    (session_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Events com 1 vencedor pra stats não dar 0 em tudo
    (session_dir / "events.jsonl").write_text(
        json.dumps({
            "event_id": "evt1",
            "session_id": sid,
            "timestamp": "2026-05-12T10:01:00.000Z",
            "elapsed_ms": 60000,
            "type": "round.started",
            "round": 1,
        }) + "\n", encoding="utf-8",
    )

    (session_dir / "transcript.json").write_text(
        json.dumps({
            "topic": "Cidade do futuro",
            "players": [{"id": 1, "name": "Mateus", "is_ai": False, "balance": 1000, "drinks": 0}],
            "conversation": [],
        }), encoding="utf-8",
    )

    # Instrumento respondido
    (session_dir / "instruments").mkdir()
    (session_dir / "instruments" / "pre_v1.json").write_text(
        json.dumps({"instrument_id": "pre_v1", "responses": [{"item_id": "q1", "value": "A"}]}),
        encoding="utf-8",
    )

    # final_idea
    (session_dir / "final_idea.json").write_text(
        json.dumps({
            "summary": "Síntese do dono",
            "lab_idea": {"title": "Cidade Vertical", "problem_statement": "X", "key_features": ["a", "b"]},
        }),
        encoding="utf-8",
    )

    # llm_calls vazio pra costs não dar erro
    (session_dir / "llm_calls.jsonl").write_text("", encoding="utf-8")

    return sid, session_dir


def test_export_inclui_arquivos_derivados(tmp_path, monkeypatch):
    sid, _ = _setup_minimal_session(tmp_path, monkeypatch)

    from services.export import export_session_zip
    zip_bytes = export_session_zip(sid)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()

    # Persistidos
    assert f"{sid}/manifest.json" in names
    assert f"{sid}/events.jsonl" in names
    assert f"{sid}/transcript.json" in names
    assert f"{sid}/final_idea.json" in names
    # Instrumentos respondidos
    assert f"{sid}/instruments/pre_v1.json" in names
    # Derivados gerados na hora
    assert f"{sid}/stats.json" in names
    assert f"{sid}/costs.json" in names
    assert f"{sid}/ideia.md" in names
    # README
    assert f"{sid}/README.md" in names


def test_export_stats_tem_conteudo(tmp_path, monkeypatch):
    sid, _ = _setup_minimal_session(tmp_path, monkeypatch)

    from services.export import export_session_zip
    zip_bytes = export_session_zip(sid)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(f"{sid}/stats.json") as f:
            stats = json.loads(f.read().decode("utf-8"))

    assert stats["session_id"] == sid
    assert stats["topic"] == "Cidade do futuro"
    assert "duration_ms" in stats
    assert "stances" in stats


def test_export_ideia_md_tem_titulo(tmp_path, monkeypatch):
    sid, _ = _setup_minimal_session(tmp_path, monkeypatch)

    from services.export import export_session_zip
    zip_bytes = export_session_zip(sid)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(f"{sid}/ideia.md") as f:
            md = f.read().decode("utf-8")

    assert "Cidade Vertical" in md
    assert "Síntese do dono" in md


def test_export_manifest_tem_composition(tmp_path, monkeypatch):
    sid, _ = _setup_minimal_session(tmp_path, monkeypatch)

    from services.export import export_session_zip
    zip_bytes = export_session_zip(sid)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(f"{sid}/manifest.json") as f:
            m = json.loads(f.read().decode("utf-8"))

    assert m["composition"]["id"] == "inventores_cientistas"
    assert m["composition"]["title"] == "Inventores e cientistas"
    assert m["llm"]["provider"] == "google"
    assert m["llm"]["model"] == "gemini-1.5-flash"
    assert "personas_detail" in m
