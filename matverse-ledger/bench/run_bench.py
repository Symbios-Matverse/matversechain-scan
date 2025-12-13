import argparse, json, time, os, hashlib, random

def sha256_hex(b: bytes) -> str:
    return "0x" + hashlib.sha256(b).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=1337)
    args = ap.parse_args()

    random.seed(args.seed)

    # Simulação mínima: substitua pelo seu executável real depois.
    # Aqui geramos métricas estáveis por seed.
    omega = 0.92 + (random.random()-0.5)*0.01
    psi   = 0.89 + (random.random()-0.5)*0.02
    cvar  = 0.04 + (random.random()-0.5)*0.01
    latency_ms = int(40 + random.random()*20)

    verdict = "ACCEPT" if (omega > 0.90 and cvar < 0.06) else "REJECT"

    payload = {
        "seed": args.seed,
        "omega": round(omega, 6),
        "psi": round(psi, 6),
        "cvar": round(cvar, 6),
        "latency_ms": latency_ms,
        "verdict": verdict,
    }

    run_hash = sha256_hex(json.dumps(payload, sort_keys=True).encode())
    payload["run_hash"] = run_hash

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("bench:", payload)

if __name__ == "__main__":
    main()
