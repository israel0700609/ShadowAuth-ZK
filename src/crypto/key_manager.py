"""
Key Management and Identity Utilities.

This module handles the generation of cryptographic key pairs (e.g., ECDH)
and derives the corresponding "leaf commitments" that are inserted into the Merkle Tree.
"""

from typing import List, Dict, Tuple
from common import constants
import secrets
import poseidon_wrapper

BN128_SCALAR_FIELD = constants.BN128_SCALAR_FIELD


def generate_key_pair() -> Tuple[int, int]:
    """
    Generates a new, random private/public key pair.
    (For this ZKP context, the private key can simply be a secure random integer
    within the BN128 field, acting as the secret preimage).

    Returns:
        Tuple[int, int]: A tuple containing (private_key, public_key_or_commitment).
    """
    private_key = secrets.randbelow(BN128_SCALAR_FIELD)
    leaf_commitment = derive_leaf_commitment(private_key)
    return private_key, leaf_commitment


def derive_leaf_commitment(private_key: int) -> int:
    """
    Derives the Merkle leaf commitment from a private key.
    This exactly mirrors the `Poseidon(1)` operation at the start of the Circom circuit.

    Args:
        private_key (int): The secret integer.

    Returns:
        int: The leaf hash to be inserted into the Merkle Tree.
    """
    return poseidon_wrapper.poseidon_hash_single(private_key)


def generate_test_identities(count: int) -> Dict[str, List[int]]:
    """
    Generates a set of mock identities for testing purposes.

    Args:
        count (int): The number of identities to generate.

    Returns:
        Dict[str, List[int]]: A dictionary containing lists of generated keys, e.g.:
                              {"private_keys": [...], "leaf_commitments": [...]}
    """
    priv_keys = []
    leaves = []

    for _ in range(count):
        priv, leaf = generate_key_pair()
        priv_keys.append(priv)
        leaves.append(leaf)

    return {"private_keys": priv_keys, "leaf_commitments": leaves}
