# Notebook de análise — Mesa de Bar (simulação)

Analisa um run de simulação (`data/sim_runs/<run_id>/`) ponta a ponta: parsing,
integridade, tokens/custo, métricas semânticas, dinâmica do loop, estatística,
qualitativa e exportações.

## Como rodar
1. Instale as dependências:
   ```bash
   pip install -r requirements_analise.txt
   ```
2. Aponte para o run na **célula 0** (`DATA_ROOT`) ou via ambiente:
   ```bash
   export MDB_RUN_DIR="data/sim_runs/sim_20260630_133248"
   jupyter lab Mesa_de_Bar_Analise_Simulacao.ipynb
   ```
3. Rode todas as células. Saídas em `analise_saidas/` (tabelas CSV + figuras PNG).

## Notas importantes
- **Embeddings:** com `sentence-transformers` instalado e rede, usa o modelo
  multilíngue `paraphrase-multilingual-mpnet-base-v2`. Sem isso, cai para TF-IDF
  (as métricas continuam comparáveis *dentro* do run, mas para o estudo final
  fixe o modelo multilíngue).
- **Preços:** ajuste `PRICES` (célula 0) com os valores vigentes da sua conta.
- **Custo subcontado:** o `llm_calls.jsonl` não registra as chamadas do
  **jogador-agente** (só personas/juiz/dono). O notebook sinaliza isso; para custo
  completo, instrumente as chamadas do jogador-agente no runner.
- **Piloto vs estudo:** com poucas células/sessões, análises que exigem variação
  (diversidade coletiva, fatores A/C/D, modelos mistos) são puladas com aviso.
  O mesmo notebook escala para o desenho completo sem mudanças.
- **Originalidade:** sem a condição B0 (geração independente), usa um *reference
  set* substituto (ideias da 1ª rodada). Quando rodar B0, troque para ela.
