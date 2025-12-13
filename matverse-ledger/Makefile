.PHONY: venv up down deploy pose pole index scan check claim snapshot

venv:
	bash scripts/bootstrap.sh

up:
	bash scripts/devnet_up.sh

down:
	bash scripts/devnet_down.sh

deploy:
	bash scripts/deploy_contracts.sh

pose:
	bash scripts/submit_pose.sh

pole:
	bash scripts/submit_pole.sh

index:
	bash scripts/indexer_run.sh

scan:
	bash scripts/scan_run.sh

check:
	python -m compileall bench indexer scan scripts

claim:
	python scripts/compile_claim.py --claim spec/claim.example.yaml --schema spec/claim.schema.json --hash-out .runtime/claim_hash.txt

# --- snapshot (SQLite -> dist/*.sqlite[.zst] + manifest.json) ---
SNAP_DB     ?= .runtime/matversescan.db
SNAP_OUT    ?= dist
SNAP_CHAIN  ?= 31337
SNAP_FROM   ?= 0
SNAP_TO     ?= latest
SNAP_PREFIX ?= mvscan

snapshot:
	python scripts/snapshot_sqlite.py \
	  --db $(SNAP_DB) \
	  --out $(SNAP_OUT) \
	  --chain-id $(SNAP_CHAIN) \
	  --from $(SNAP_FROM) \
	  --to $(SNAP_TO) \
	  --name-prefix $(SNAP_PREFIX)
