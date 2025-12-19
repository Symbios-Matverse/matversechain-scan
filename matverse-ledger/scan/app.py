"""Gradio-based explorer for PoSE/PoLE data with core benchmark verification.

This UI is intentionally "data-only": it reads an indexed SQLite database for
PoSE/PoLE records and fetches matverse-core benchmark artifacts via the GitHub
API to compute canonical hashes. No remote code execution happens here.
"""

import os
from datetime import datetime

import pandas as pd
import gradio as gr
from fastapi import FastAPI
from sqlalchemy import create_engine, text

from benchmarks_core import load_core_benchmarks
from capt_api import router as capt_router


DB_PATH = os.environ.get("MATVERSE_DB", "matversescan.db")
DASHBOARD_URL = "https://app.base44.com/apps/693d491d7d92782a1a55f89e/editor/preview/Dashboard"
CAPT_DASHBOARD_URL = (
    "https://app.base44.com/apps/694471aafc033d574cd4579f/editor/preview/Dashboard"
)


def _engine():
    # engine por chamada é ok em DB pequeno; helper facilita evoluir
    return create_engine(f"sqlite:///{DB_PATH}")


def q(sql: str, params=None):
    eng = _engine()
    with eng.connect() as c:
        r = c.execute(text(sql), params or {})
        return [dict(x._mapping) for x in r.fetchall()]


def _add_readable_metrics(rows):
    for r in rows:
        r["omega"] = r["omega_u6"] / 1e6
        r["psi"] = r["psi_u6"] / 1e6
        r["cvar"] = r["cvar_u6"] / 1e6
    return rows


def list_pose():
    # pose tem id autoincrement: OK ordenar por id
    return q(
        "SELECT claim_hash, submitter, metadata_uri, proof_hash, timestamp, tx_hash "
        "FROM pose ORDER BY id DESC LIMIT 50"
    )


def list_pole():
    # pole NÃO tem id: ordenar por timestamp + tx_hash para ordem total
    rows = q(
        "SELECT claim_hash, submitter, verdict, omega_u6, psi_u6, cvar_u6, "
        "latency_ms, run_hash, timestamp, tx_hash "
        "FROM pole ORDER BY timestamp DESC, tx_hash DESC LIMIT 50",
    )
    return _add_readable_metrics(rows)


def find_claim(claim_hash: str):
    pose = q(
        "SELECT * FROM pose WHERE claim_hash=:h ORDER BY id DESC LIMIT 5",
        {"h": claim_hash},
    )
    pole = q(
        "SELECT * FROM pole WHERE claim_hash=:h ORDER BY timestamp DESC, tx_hash DESC LIMIT 20",
        {"h": claim_hash},
    )
    return pose, _add_readable_metrics(pole)


def list_core_benchmarks():
    rows = load_core_benchmarks()
    table = []
    for r in rows:
        table.append(
            [
                r.bench_dir,
                r.claim_id,
                r.version,
                r.frozen_date,
                r.h_m_calc,
                r.h_m_expected,
                "OK" if r.match else "FAIL",
                r.metrics,
                r.note,
            ]
        )
    return table


def list_tables():
    eng = _engine()
    with eng.connect() as c:
        rows = c.execute(
            text(
                "SELECT name FROM sqlite_schema WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ).fetchall()
        return [r[0] for r in rows]


def table_info(table: str):
    eng = _engine()
    with eng.connect() as c:
        info_rows = c.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
        return [(row[1], row[2]) for row in info_rows]


def preview_table(table: str, limit: int):
    if not table:
        return pd.DataFrame()
    eng = _engine()
    with eng.connect() as c:
        return pd.read_sql(
            text(f'SELECT * FROM "{table}" ORDER BY rowid DESC LIMIT :limit'),
            c,
            params={"limit": limit},
        )


def search_hash(fragment: str, limit: int):
    if not fragment:
        return {}

    pattern = f"{fragment}%"
    results = {}
    eng = _engine()

    for table in list_tables():
        info = table_info(table)
        searchable_cols = [
            col
            for col, col_type in info
            if col_type is not None
            and ("CHAR" in col_type.upper() or "TEXT" in col_type.upper() or col.endswith("hash"))
        ]

        table_matches = []
        with eng.connect() as c:
            for col in searchable_cols:
                rows = c.execute(
                    text(
                        f'SELECT * FROM "{table}" WHERE "{col}" LIKE :pattern '
                        "ORDER BY rowid DESC LIMIT :limit"
                    ),
                    {"pattern": pattern, "limit": limit},
                ).fetchall()
                if rows:
                    table_matches.extend([dict(r._mapping) for r in rows])

        if table_matches:
            results[table] = table_matches[:limit]

    return results


def app_ui():
    with gr.Blocks(
        title="MatVerseScan — Proof Explorer", css=".gradio-container {max-width: 1200px;}"
    ) as demo:
        gr.Markdown(
            """
            # MatVerseScan — Public Proof Explorer

            - Snapshot: `matversescan.db` (read-only)
            - Fonte: https://github.com/Symbios-Matverse/matversechain-scan
            - Pipeline: OpenBox → eventos (hash + métricas + decisão) → matverse-ledger → snapshot SQLite → Space público
            """
        )

        with gr.Tabs():
            # ===== TAB 1: Proof Explorer (o que você já tem) =====
            with gr.Tab("Proof Explorer"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("## 1) Tabelas")
                        tables = list_tables()
                        tables_state = gr.State(value=tables)
                        table_dropdown = gr.Dropdown(
                            choices=tables,
                            value=tables[0] if tables else None,
                            label="Tabela",
                            interactive=True,
                        )
                        table_meta = gr.Dataframe(label="Colunas", interactive=False)
                        table_preview = gr.Dataframe(label="Preview (últimas linhas)", interactive=False)
                        limit_slider = gr.Slider(
                            label="Limite", minimum=10, maximum=200, value=50, step=10
                        )
                        refresh_tables = gr.Button("Atualizar lista de tabelas")

                    with gr.Column(scale=1):
                        gr.Markdown("## 2) Busca por hash/id")
                        hash_input = gr.Textbox(
                            label="Hash ou prefixo", placeholder="cole um hash ou prefixo", lines=1
                        )
                        hash_limit = gr.Slider(
                            label="Limite por tabela", minimum=5, maximum=200, step=5, value=20
                        )
                        search_btn = gr.Button("Buscar")
                        search_results = gr.JSON(label="Resultados")

                def _select(table: str, limit: int):
                    if not table:
                        return gr.update(), pd.DataFrame(), pd.DataFrame()
                    meta = pd.DataFrame(table_info(table), columns=["coluna", "tipo"])
                    preview = preview_table(table, limit)
                    return table, meta, preview

                table_dropdown.change(
                    _select, [table_dropdown, limit_slider], [table_dropdown, table_meta, table_preview]
                )
                limit_slider.change(
                    _select, [table_dropdown, limit_slider], [table_dropdown, table_meta, table_preview]
                )

                def _refresh_tables():
                    tables_list = list_tables()
                    return (
                        gr.Dropdown.update(
                            choices=tables_list, value=tables_list[0] if tables_list else None
                        ),
                        gr.State.update(value=tables_list),
                    )

                refresh_tables.click(_refresh_tables, None, [table_dropdown, tables_state])

                def _search(fragment: str, limit: int):
                    return search_hash(fragment, limit)

                search_btn.click(_search, [hash_input, hash_limit], search_results)

            # ===== TAB 2: Dashboard Espelho =====
            with gr.Tab("Dashboard (Espelho)"):
                gr.Markdown(
                    f"""
                    ## Dashboard Base44 (espelho)

                    Se o embed via iframe for bloqueado pelo Base44, use o link direto:

                    **Abrir em nova aba:** {DASHBOARD_URL}
                    """
                )

                gr.HTML(
                    f"""
                    <div style="width:100%; height:78vh; border:1px solid rgba(0,0,0,.12); border-radius:12px; overflow:hidden;">
                      <iframe
                        src="{DASHBOARD_URL}"
                        style="width:100%; height:100%; border:0;"
                        loading="lazy"
                        referrerpolicy="no-referrer"
                        allow="clipboard-read; clipboard-write; fullscreen"
                      ></iframe>
                    </div>
                    """
                )

            # ===== TAB 3: CAPT Runtime =====
            with gr.Tab("CAPT Runtime"):
                gr.Markdown(
                    f"""
                    ## CAPT Runtime (Base44)

                    **Abrir em nova aba:** {CAPT_DASHBOARD_URL}

                    **Endpoints CAPT**
                    - `POST /capt/chromeos/capture`
                    - `POST /capt/terabox/measure`
                    - `GET /capt/runtime/status`
                    - `POST /capt/benchmark/freeze`
                    """
                )

                gr.HTML(
                    f"""
                    <div style="width:100%; height:78vh; border:1px solid rgba(0,0,0,.12); border-radius:12px; overflow:hidden;">
                      <iframe
                        src="{CAPT_DASHBOARD_URL}"
                        style="width:100%; height:100%; border:0;"
                        loading="lazy"
                        referrerpolicy="no-referrer"
                        allow="clipboard-read; clipboard-write; fullscreen"
                      ></iframe>
                    </div>
                    """
                )

        gr.Markdown(
            f"""
            ---
            **Snapshot carregado:** `{os.path.abspath(DB_PATH)}`  
            **Última atualização (container):** {datetime.utcnow().isoformat(timespec='seconds')} UTC
            """
        )

    return demo


fastapi_app = FastAPI()
fastapi_app.include_router(capt_router)
app = gr.mount_gradio_app(fastapi_app, app_ui(), path="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "7860")))
