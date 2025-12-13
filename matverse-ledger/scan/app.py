import os
import gradio as gr
from sqlalchemy import create_engine, text

DB = os.environ.get("MATVERSE_DB", "matversescan.db")


def _engine():
    # engine por chamada é ok em DB pequeno, mas deixo o helper para facilitar evoluir
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
    # pole NÃO tem id: ordenar por timestamp (ou block_number) + tx_hash para ordem total
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


with gr.Blocks(title="MatVerseScan") as demo:
    gr.Markdown(
        "# MatVerseScan\n"
        "Explorer leve para PoSE/PoLE indexado em SQLite.\n\n"
        "Observação: este app não executa a blockchain. Ele apenas lê o banco indexado."
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


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))
