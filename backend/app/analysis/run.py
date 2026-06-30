"""CLI de análise. Uso:
    cd backend/app
    python -m analysis.run --study main --backend hash --out ../../data/analysis
"""
import argparse
import json
from pathlib import Path

from analysis import report as report_mod
from analysis import dataset
from analysis.cat_export import build_cat_bundle, JUDGE_README


def main():
    ap = argparse.ArgumentParser(description="Análise automática Mesa de Bar (Fase C)")
    ap.add_argument("--study", default=None, help="Filtra por study_id")
    ap.add_argument("--backend", default=None, help="google | local | hash")
    ap.add_argument("--out", default="data/analysis", help="Diretório de saída")
    ap.add_argument("--include-proposals", action="store_true",
                    help="Inclui propostas individuais no export CAT")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rep = report_mod.analyze(study_id=args.study, backend=args.backend)

    # relatório (sem os vetores pesados)
    slim = {k: v for k, v in rep.items() if k not in ("ideas", "finals")}
    (out / "report.json").write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(report_mod.to_markdown(rep), encoding="utf-8")

    # dataset tidy (ideias com métricas, sem vetores)
    tidy = [{k: v for k, v in it.items() if not k.startswith("_")} for it in rep["ideas"]]
    (out / "ideas.json").write_text(json.dumps(tidy, ensure_ascii=False, indent=2), encoding="utf-8")

    # bundle CAT
    finals = [{k: v for k, v in f.items() if not k.startswith("_")} for f in rep["finals"]]
    proposals = tidy if args.include_proposals else None
    bundle = build_cat_bundle(finals, proposal_records=proposals)
    (out / "cat_items.csv").write_text(bundle["items_csv"], encoding="utf-8")
    (out / "cat_key.csv").write_text(bundle["key_csv"], encoding="utf-8")
    (out / "cat_items.json").write_text(json.dumps(bundle["items"], ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "cat_README.md").write_text(JUDGE_README, encoding="utf-8")

    print(f"OK — {rep['n_sessions']} sessões, {rep['n_ideas']} ideias, "
          f"{bundle['n_items']} itens CAT. Saída em {out}/")
    print(report_mod.to_markdown(rep))


if __name__ == "__main__":
    main()
