import json
import subprocess
import tempfile
import os
from typing import Dict, List, Tuple


class ZKVerifier:
    def __init__(self, vkey_path: str, snarkjs_path: str = "snarkjs"):
        self.vkey_path = vkey_path
        self.snarkjs_path = snarkjs_path

    def verify_snark_math(self, proof: Dict, public_signals: List[str]) -> bool:
        with tempfile.TemporaryDirectory() as tmp_dir:
            p_path = os.path.join(tmp_dir, "p.json")
            s_path = os.path.join(tmp_dir, "s.json")

            with open(p_path, "w") as f:
                json.dump(proof, f)
            with open(s_path, "w") as f:
                json.dump(public_signals, f)

            try:
                res = subprocess.run(
                    [
                        self.snarkjs_path,
                        "groth16",
                        "verify",
                        self.vkey_path,
                        s_path,
                        p_path,
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(
                    f"SnarkJS executable not found: {self.snarkjs_path}"
                ) from exc
            except OSError as exc:
                raise RuntimeError(f"Failed to execute SnarkJS verify: {exc}") from exc

            combined = f"{res.stdout}\n{res.stderr}".lower()
            if "invalid proof" in combined:
                return False

            return res.returncode == 0 and "ok" in combined

    def full_verify(
        self,
        proof: Dict,
        public_signals: List[str],
        expected_root: int,
        expected_challenge: int,
        expected_eph_key: int,
    ) -> Tuple[bool, str]:

        if not self.verify_snark_math(proof, public_signals):
            return False, ""

        if len(public_signals) < 5:
            return False, ""

        resp_hash = public_signals[0]
        actual_root = int(public_signals[2])
        actual_challenge = int(public_signals[3])
        actual_eph_key = int(public_signals[4])

        if actual_root != expected_root:
            return False, ""
        if actual_challenge != expected_challenge:
            return False, ""
        if actual_eph_key != expected_eph_key:
            return False, ""

        return True, resp_hash
