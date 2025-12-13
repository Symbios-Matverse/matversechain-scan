# MatVerse Ledger (PoSE/PoLE) + MatVerseScan

Este repositório entrega um pipeline mínimo e robusto:
- Devnet EVM local (Anvil)
- Contratos PoSE e PoLE (Solidity) com eventos indexáveis
- Indexer Python (RPC -> SQLite)
- Explorer MatVerseScan (Gradio) para visualizar claims e execuções

## Requisitos
- Docker (opcional, mas recomendado)
- Python 3.11+
- Node (opcional) — aqui usamos Foundry
- Foundry (forge/cast/anvil)

## Quickstart (local)
```bash
bash scripts/bootstrap.sh
bash scripts/devnet_up.sh
bash scripts/deploy_contracts.sh

# Validar e compilar o claim de exemplo (gera hash determinístico usado pelos scripts)
python scripts/compile_claim.py \
  --claim spec/claim.example.yaml \
  --schema spec/claim.schema.json \
  --hash-out .runtime/claim_hash.txt
# (ou rode `make claim` para o mesmo efeito)

# Registrar um PoSE (claim)
bash scripts/submit_pose.sh

# Registrar um PoLE (execução + métricas)
bash scripts/submit_pole.sh

# Indexar eventos para SQLite
bash scripts/indexer_run.sh

# Abrir MatVerseScan (web)
bash scripts/scan_run.sh

# Gerar snapshot compacto do SQLite (para demo/Spaces)
make snapshot \
  SNAP_DB=.runtime/matversescan.db \
  SNAP_OUT=dist \
  SNAP_CHAIN=31337 \
  SNAP_FROM=0 \
  SNAP_TO=latest
```

## O que é PoSE e PoLE

* PoSE: registro imutável do hash do claim + metadados (URI) + proofHash
* PoLE: registro do hash do resultado + métricas (Ω, Ψ, CVaR, latency) + veredito

## Metas de engenharia

* Determinismo (seeds e ambiente versionados)
* Auditabilidade (event logs + hashes)
* Reprodutibilidade (bench scripts + tolerâncias)
* Leveza (scan é client; chain roda fora do HF)

## Notas de governança/comunicação

* A Hugging Face permite definir o **ordenamento padrão** da aba Community (Discussions/PRs) por repositório. Veja `docs/community-tab-sorting.md` para recomendações rápidas.

## Licença

MIT

