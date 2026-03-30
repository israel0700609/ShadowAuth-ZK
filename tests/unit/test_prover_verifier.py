import pytest
import os
import copy
import json
from typing import Dict, Any

from src.client.prover import ZKProver
from src.server.verifier import ZKVerifier
from src.crypto.merkle_tree import MerkleTree
from src.crypto.poseidon_wrapper import poseidon_hash_single

CIRCUITS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "circuits", "build")
WASM_PATH = os.path.join(CIRCUITS_DIR, "ShadowAuth_js", "ShadowAuth.wasm")
ZKEY_PATH = os.path.join(CIRCUITS_DIR, "proving_key.zkey")
VKEY_PATH = os.path.join(CIRCUITS_DIR, "verification_key.json")

SNARKJS_CMD = "snarkjs.cmd" if os.name == "nt" else "snarkjs"


@pytest.fixture
def prover():
    return ZKProver(WASM_PATH, ZKEY_PATH, snarkjs_path=SNARKJS_CMD)


@pytest.fixture
def verifier():
    return ZKVerifier(VKEY_PATH, snarkjs_path=SNARKJS_CMD)


@pytest.fixture
def valid_inputs():
    private_key = "123456789"

    public_key = poseidon_hash_single(int(private_key))
    nullifier = poseidon_hash_single(public_key)

    tree = MerkleTree(depth=20, leaves=[nullifier])

    merkle_proof = tree.get_proof(0)

    return {
        "privateKey": private_key,
        "pathElements": [str(x) for x in merkle_proof.siblings],
        "pathIndices": [str(x) for x in merkle_proof.path_indices],
        "merkleRoot": str(tree.get_root()),
        "serverChallenge": "111",
        "clientEphemeralPubKey": "222",
    }


def test_proof_generation_and_verification_roundtrip(prover, verifier, valid_inputs):
    if not os.path.exists(ZKEY_PATH):
        pytest.skip("ZK artifacts not built")

    proof, public_signals = prover.generate_proof(valid_inputs)
    assert "pi_a" in proof
    assert len(public_signals) == 5

    expected_root = int(valid_inputs["merkleRoot"])
    expected_challenge = int(valid_inputs["serverChallenge"])
    expected_eph = int(valid_inputs["clientEphemeralPubKey"])

    is_valid, _ = verifier.full_verify(
        proof, public_signals, expected_root, expected_challenge, expected_eph
    )
    assert is_valid is True


def test_verification_fails_on_tampered_proof(prover, verifier, valid_inputs):
    if not os.path.exists(ZKEY_PATH):
        pytest.skip("ZK artifacts not built")

    proof, public_signals = prover.generate_proof(valid_inputs)

    is_valid, _ = verifier.full_verify(
        proof,
        public_signals,
        int(valid_inputs["merkleRoot"]),
        999,
        int(valid_inputs["clientEphemeralPubKey"]),
    )
    assert is_valid is False


def test_proof_generation_fails_on_invalid_inputs(prover, valid_inputs):
    if not os.path.exists(ZKEY_PATH):
        pytest.skip("ZK artifacts not built")

    invalid_inputs = copy.deepcopy(valid_inputs)
    invalid_inputs["merkleRoot"] = "999999999"

    with pytest.raises(RuntimeError):
        prover.generate_proof(invalid_inputs)
