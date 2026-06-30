"""Verificador de deploy do catálogo.

Uso (a partir de backend/app):
    python -m catalog

Imprime a estrutura lida (áreas, subtemas, temas de mesa, personas) e os
avisos. Sai com código 1 se houver ERROS (útil em pipeline de deploy).
"""
import json
import sys

from catalog.catalog import build_catalog


def main() -> int:
    c = build_catalog()
    t, m = c["temas"], c["composicao_mesa"]

    print("=== TEMAS (assunto da mesa) ===")
    print(f"fonte: {t['source']}")
    print(f"áreas: {t['areas_count']} · subtemas: {t['subtemas_count']}")
    for a in t["areas"]:
        print(f"  - {a['id']}: {a['subtemas_count']} subtema(s)  [{a.get('title')}]")

    print("\n=== COMPOSIÇÃO DA MESA ===")
    print(f"fonte: {m['source']}")
    print(f"temas: {m['themes_count']} · personas: {m['personas_total']} · mesa = {c['table_size']}")
    for th in m["themes"]:
        print(f"  - {th['id']}: {th['personas_count']} persona(s)  [{th.get('title')}]")

    fo = c["formularios"]
    print("\n=== FORMULÁRIOS (pré/pós jogo) ===")
    print(f"fonte: {fo['source']}")
    print(f"formulários: {fo['forms_count']} · itens: {fo['items_total']}")
    for fm in fo["forms"]:
        tipos = ", ".join(f"{k}×{v}" for k, v in sorted(fm["item_types"].items()))
        print(f"  - {fm['id']} [{fm['moment']}]: {fm['items_count']} itens "
              f"({fm['required_count']} obrigatórios) · {tipos}")

    if c["warnings"]:
        print("\n=== AVISOS ===")
        for w in c["warnings"]:
            print(f"  ! {w}")
    if c["errors"]:
        print("\n=== ERROS ===")
        for e in c["errors"]:
            print(f"  ✗ {e}")

    print("\n" + ("OK ✓" if c["ok"] else "FALHOU ✗"))
    return 0 if c["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
