"""Tests do carregamento de composições."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def test_list_compositions_finds_all(monkeypatch):
    """Garante que todas as composições carregam sem erro de YAML."""
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("MDB_COMPOSITIONS_DIR", str(repo_root / "compositions"))

    # força recarregar
    import importlib
    from compositions import loader as comp_loader
    importlib.reload(comp_loader)

    comps = comp_loader.list_compositions()
    assert len(comps) >= 12, f"esperado >=12 composições, achou {len(comps)}"

    # cada uma deve ter exatamente 4 personas
    for c in comps:
        assert len(c.personas) == 4, f"{c.id} tem {len(c.personas)} personas (esperado 4)"
        for p in c.personas:
            assert p.name and p.role and p.goal and p.instructions, \
                f"{c.id}/{p.name} tem campo vazio"


def test_load_specific_composition(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("MDB_COMPOSITIONS_DIR", str(repo_root / "compositions"))

    import importlib
    from compositions import loader as comp_loader
    importlib.reload(comp_loader)

    c = comp_loader.load_composition("filosofos_classicos")
    assert c.id == "filosofos_classicos"
    assert c.title == "Filósofos clássicos"
    names = {p.name for p in c.personas}
    assert "Sócrates" in names
    assert "Nietzsche" in names


def test_composition_not_found_raises(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("MDB_COMPOSITIONS_DIR", str(repo_root / "compositions"))

    import importlib
    from compositions import loader as comp_loader
    importlib.reload(comp_loader)

    from core.exceptions import MesaDeBarError
    import pytest
    with pytest.raises(MesaDeBarError):
        comp_loader.load_composition("nao_existe_jamais_v99")
