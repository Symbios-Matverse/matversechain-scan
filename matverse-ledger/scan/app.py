"""Gradio-based explorer for PoSE/PoLE data with core benchmark verification.

This UI is intentionally "data-only": it reads an indexed SQLite database for
PoSE/PoLE records and fetches matverse-core benchmark artifacts via the GitHub
API to compute canonical hashes. No remote code execution happens here.
"""

import os

import gradio as gr
from sqlalchemy import create_engine, text

from benchmarks_core import load_core_benchmarks


DB = os.environ.get("MATVERSE_DB", "matversescan.db")


def _engine():
    # engine por chamada é ok em DB pequeno; helper facilita evoluir
    return create_engine(f"sqlite:///{DB}")


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


with gr.Blocks(title="MatVerseScan") as demo:
    gr.Markdown(
        "# MatVerseScan\n"
        "Explorer leve para PoSE/PoLE indexado em SQLite.\n\n"
        "Observação: este app não executa a blockchain. Ele apenas lê o banco indexado.\n"
        "Benchmarks do core são verificados por hash canônico (data-only), sem executar código remoto."
    )

    with gr.Tab("PoSE (claims)"):
        btn1 = gr.Button("Atualizar lista")
        out1 = gr.JSON()
        btn1.click(fn=list_pose, outputs=out1)

    with gr.Tab("PoLE (execuções)"):
        btn2 = gr.Button("Atualizar lista")
        out2 = gr.JSON()
        btn2.click(fn=list_pole, outputs=out2)

    with gr.Tab("Buscar por claim_hash"):
        inp = gr.Textbox(label="claim_hash (0x...)")
        btn3 = gr.Button("Buscar")
        out_pose = gr.JSON(label="PoSE")
        out_pole = gr.JSON(label="PoLE")
        btn3.click(fn=find_claim, inputs=inp, outputs=[out_pose, out_pole])

    with gr.Tab("Benchmarks (matverse-core)"):
        gr.Markdown(
            "Leitura pública de `matverse-core/benchmarks/` via GitHub API.\n\n"
            "Requisitos por benchmark:\n"
            "- `spec/claim_v1.0.0.json`\n"
            "- `observable/expected_output.json`\n"
            "- `observable/M_canonical.json`\n\n"
            "Config opcional:\n"
            "- `CORE_OWNER`, `CORE_REPO`, `CORE_REF`\n"
            "- `GITHUB_TOKEN` (evita rate-limit em produção)"
        )

        btn4 = gr.Button("Carregar / Recarregar")
        df = gr.Dataframe(
            headers=[
                "Dir",
                "Claim",
                "Version",
                "Frozen",
                "H(M) calc",
                "H(M) expected",
                "Match",
                "Metrics",
                "Note",
            ],
            value=[],
            wrap=True,
        )
        btn4.click(fn=list_core_benchmarks, inputs=[], outputs=[df])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))
