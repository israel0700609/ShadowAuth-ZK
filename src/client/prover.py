import os
import json
import subprocess
import tempfile
from typing import Tuple, Dict, Any


class ZKProver:
    def __init__(self, wasm_path: str, zkey_path: str, snarkjs_path: str = "snarkjs"):
        self.wasm_path = wasm_path
        self.zkey_path = zkey_path
        self.snarkjs_path = snarkjs_path

    def generate_proof(self, inputs: Dict[str, Any]) -> Tuple[Dict, list]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, "input.json")
            proof_path = os.path.join(tmp_dir, "proof.json")
            public_path = os.path.join(tmp_dir, "public.json")

            with open(input_path, "w") as f:
                json.dump(inputs, f)

            try:
                subprocess.run(
                    [
                        self.snarkjs_path,
                        "groth16",
                        "fullprove",
                        input_path,
                        self.wasm_path,
                        self.zkey_path,
                        proof_path,
                        public_path,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                with open(proof_path, "r") as f:
                    proof = json.load(f)
                with open(public_path, "r") as f:
                    public_signals = json.load(f)

                return proof, public_signals
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Proof generation failed: {e.stderr}")

    def prepare_circuit_inputs(
        self,
        private_key: int,
        merkle_proof: Any,
        root: int,
        challenge: int,
        eph_pub_key: int,
    ) -> Dict[str, Any]:
        return {
            "privateKey": str(private_key),
            "pathElements": [str(x) for x in merkle_proof.siblings],
            "pathIndices": merkle_proof.path_indices,
            "merkleRoot": str(root),
            "serverChallenge": str(challenge),
            "clientEphemeralPubKey": str(eph_pub_key),
        }
