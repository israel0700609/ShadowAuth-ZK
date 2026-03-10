"""
Poseidon Hash Wrapper for BN128 Scalar Field.
Uses a subprocess to call the official circomlibjs Node.js library,
guaranteeing 100% compatibility with the Circom ZK circuit.
"""

import subprocess
import os
from common import constants

BN128_SCALAR_FIELD = constants.BN128_SCALAR_FIELD

JS_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "poseidon_node.js")


def _run_node_poseidon(inputs: list) -> int:
    """Helper function to execute the JS script and capture the output."""
    str_inputs = [str(i) for i in inputs]
    try:
        result = subprocess.run(
            ["node", JS_SCRIPT_PATH] + str_inputs,
            capture_output=True,
            text=True,
            check=True,
        )
        return int(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Node.js execution failed: {e.stderr}")


def poseidon_hash_single(input_val: int) -> int:
    """Computes the Poseidon hash of a single integer input."""
    if input_val < 0 or input_val >= BN128_SCALAR_FIELD:
        raise ValueError("Input must be within the BN128 scalar field.")
    return _run_node_poseidon([input_val])


def poseidon_hash_pair(left: int, right: int) -> int:
    """Computes the Poseidon hash of two integer inputs (left and right)."""
    if (
        left < 0
        or left >= BN128_SCALAR_FIELD
        or right < 0
        or right >= BN128_SCALAR_FIELD
    ):
        raise ValueError("Inputs must be within the BN128 scalar field.")
    return _run_node_poseidon([left, right])
