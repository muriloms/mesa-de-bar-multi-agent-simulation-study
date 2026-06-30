"""Testa o catálogo dinâmico de temas e composições de mesa."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from catalog.catalog import build_catalog, summary_line  # noqa: E402


def test_catalog_conta_temas_e_composicoes():
    c = build_catalog()
    assert c["ok"], f"catálogo com erros: {c['errors']}"
    # Temas: 5 áreas × 3 subtemas (estrutura atual)
    assert c["temas"]["areas_count"] == 5
    assert c["temas"]["subtemas_count"] == 15
    # Composições: 6 temas de mesa, todas com >= tamanho da mesa
    assert c["composicao_mesa"]["themes_count"] == 6
    assert c["composicao_mesa"]["personas_total"] == 36
    assert c["composicao_mesa"]["source"]


def test_catalog_avisa_pool_menor_que_mesa(tmp_path, monkeypatch):
    # Aponta a pasta de composições para um dir temporário com 1 tema pequeno
    d = tmp_path / "composicao_mesa"
    d.mkdir()
    (d / "duo.yaml").write_text(
        "id: duo\ntitle: Duo\npersonas:\n"
        "  - {name: A, description: x, role: r, goal: g, instructions: i}\n"
        "  - {name: B, description: x, role: r, goal: g, instructions: i}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MDB_COMPOSICAO_MESA_DIR", str(d))
    c = build_catalog()
    assert c["composicao_mesa"]["themes_count"] == 1
    assert any("duo" in w for w in c["warnings"])  # avisa pool < mesa


def test_summary_line_nao_quebra():
    assert "catálogo" in summary_line()


def test_catalog_inspeciona_formularios():
    c = build_catalog()
    fo = c["formularios"]
    assert fo["forms_count"] == 2
    assert fo["items_total"] > 0
    # cada formulário traz contagem de tipos e de obrigatórios
    for f in fo["forms"]:
        assert "item_types" in f and f["items_count"] >= 1
        assert f["moment"] in ("pre_session", "post_session", "post_round")


def test_number_type_aceito_pelo_modelo():
    from domain.instrument import InstrumentItem
    it = InstrumentItem(id="idade", type="number", question="Idade?",
                        min=18, max=99, unit="anos")
    assert it.type == "number" and it.min == 18 and it.unit == "anos"
