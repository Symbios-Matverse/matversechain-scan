import argparse
from web3 import Web3
from db import init_db, Pose, Pole

# Assinaturas dos eventos
POSE_EVENT = "PoSERegistered(bytes32,address,string,bytes32,uint256)"
POLE_EVENT = "PoLERecorded(bytes32,address,uint8,uint256,uint256,uint256,uint256,bytes32,uint256)"

def topic(w3, sig: str):
    return w3.keccak(text=sig).hex()

def u6_to_float(x: int) -> float:
    return x / 1_000_000.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", required=True)
    ap.add_argument("--pose", required=True)
    ap.add_argument("--pole", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--from-block", type=int, default=0)
    args = ap.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc))
    Session = init_db(args.db)
    sess = Session()

    pose_topic = topic(w3, POSE_EVENT)
    pole_topic = topic(w3, POLE_EVENT)

    def fetch(addr, t0, from_block):
        logs = w3.eth.get_logs({
            "fromBlock": from_block,
            "toBlock": "latest",
            "address": Web3.to_checksum_address(addr),
            "topics": [t0],
        })
        return logs

    # PoSE
    pose_logs = fetch(args.pose, pose_topic, args.from_block)
    for lg in pose_logs:
        # decode manual: topics[1]=claimHash, topics[2]=submitter; data has metadataURI, proofHash, timestamp
        claim_hash = "0x" + lg["topics"][1].hex()[2:]
        submitter  = "0x" + lg["topics"][2].hex()[26:]  # last 20 bytes
        tx_hash = lg["transactionHash"].hex()
        bn = lg["blockNumber"]

        # ABI decode do data
        decoded = w3.codec.decode(["string","bytes32","uint256"], lg["data"])
        metadata_uri, proof_hash_bytes, ts = decoded
        proof_hash = "0x" + proof_hash_bytes.hex()

        exists = sess.query(Pose).filter_by(tx_hash=tx_hash).first()
        if not exists:
            sess.add(Pose(
                claim_hash=claim_hash,
                submitter=submitter,
                metadata_uri=metadata_uri,
                proof_hash=proof_hash,
                block_number=bn,
                tx_hash=tx_hash,
                timestamp=int(ts),
            ))

    # PoLE
    pole_logs = fetch(args.pole, pole_topic, args.from_block)
    for lg in pole_logs:
        claim_hash = "0x" + lg["topics"][1].hex()[2:]
        submitter  = "0x" + lg["topics"][2].hex()[26:]
        tx_hash = lg["transactionHash"].hex()
        bn = lg["blockNumber"]

        decoded = w3.codec.decode(
            ["uint8","uint256","uint256","uint256","uint256","bytes32","uint256"],
            lg["data"]
        )
        verdict, omega_u6, psi_u6, cvar_u6, latency_ms, run_hash_bytes, ts = decoded
        run_hash = "0x" + run_hash_bytes.hex()

        exists = sess.query(Pole).filter_by(tx_hash=tx_hash).first()
        if not exists:
            sess.add(Pole(
                claim_hash=claim_hash,
                submitter=submitter,
                verdict=int(verdict),
                omega_u6=int(omega_u6),
                psi_u6=int(psi_u6),
                cvar_u6=int(cvar_u6),
                latency_ms=int(latency_ms),
                run_hash=run_hash,
                block_number=bn,
                tx_hash=tx_hash,
                timestamp=int(ts),
            ))

    sess.commit()
    print(f"Indexed: PoSE logs={len(pose_logs)}, PoLE logs={len(pole_logs)}")
    print("DB:", args.db)

if __name__ == "__main__":
    main()
