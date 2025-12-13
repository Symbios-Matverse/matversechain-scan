# matversechain-scan

Repositório de integração para o MatVerse Ledger v0.1, contendo o scaffold completo em `matverse-ledger/` com contratos PoSE/PoLE, pipeline local (Anvil/Foundry), indexação para SQLite e o explorer MatVerseScan (Gradio).

## Estrutura
- `matverse-ledger/`: código-fonte, scripts e documentação do ledger/scan.
- `LICENSE`: licença MIT aplicada a todo o conteúdo.

## Como começar
Entre em `matverse-ledger/` e siga o README local para o fluxo completo:

```bash
cd matverse-ledger
make venv
make claim
make up
make deploy
make pose
make pole
make index
make scan
```

Para gerar um snapshot do SQLite para demos/Spaces:

```bash
cd matverse-ledger
make snapshot SNAP_DB=.runtime/matversescan.db SNAP_OUT=dist SNAP_CHAIN=31337 SNAP_FROM=0 SNAP_TO=latest
```

> Dica: o PR sugerido no prompt já traz título e corpo prontos para uso no GitHub.
