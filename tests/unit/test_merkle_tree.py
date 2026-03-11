"""
Comprehensive unit tests for:
  - src/crypto/poseidon_wrapper.py  (BN128 Poseidon via circomlibjs)
  - src/crypto/merkle_tree.py       (Fixed-depth binary Merkle Tree)
  - src/crypto/key_manager.py       (Key pair generation and leaf derivation)

Definition of Done:
  pytest tests/unit/test_merkle_tree.py -v passes
  Poseidon outputs match Circom/circomlibjs reference vectors.
  Merkle proofs are compatible with the ZK circuit witness format.
"""

import secrets

import pytest

import key_manager
import poseidon_wrapper
from merkle_tree import MerkleProof, MerkleTree

# BN128 scalar field prime
BN128_P = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# ---------------------------------------------------------------------------
# Canonical circomlibjs reference test vectors
# Source: https://github.com/iden3/circomlibjs (test/poseidon.js)
# These must match exactly to guarantee circuit compatibility.
# ---------------------------------------------------------------------------
POSEIDON_SINGLE_1 = (
    18586133768512220936620570745912940619677854269274689475585506675881198879027
)
POSEIDON_PAIR_1_2 = (
    7853200120776062878684798364095072458815029376092732009249414926327459813530
)


# ===========================================================================
# Poseidon wrapper — field arithmetic and reference vector validation
# ===========================================================================


class TestPoseidonWrapper:
    """Validate that poseidon_wrapper produces values identical to circomlibjs."""

    # --- Reference vector cross-validation ---

    def test_single_vector_input_1(self):
        """Poseidon([1]) must equal the canonical circomlibjs output."""
        assert poseidon_wrapper.poseidon_hash_single(1) == POSEIDON_SINGLE_1

    def test_pair_vector_inputs_1_2(self):
        """Poseidon([1, 2]) must equal the canonical circomlibjs output."""
        assert poseidon_wrapper.poseidon_hash_pair(1, 2) == POSEIDON_PAIR_1_2

    # --- Field membership ---

    def test_single_output_in_field(self):
        result = poseidon_wrapper.poseidon_hash_single(42)
        assert 0 <= result < BN128_P

    def test_pair_output_in_field(self):
        result = poseidon_wrapper.poseidon_hash_pair(100, 200)
        assert 0 <= result < BN128_P

    # --- Input validation ---

    def test_single_negative_input_raises(self):
        with pytest.raises(ValueError):
            poseidon_wrapper.poseidon_hash_single(-1)

    def test_single_field_overflow_raises(self):
        with pytest.raises(ValueError):
            poseidon_wrapper.poseidon_hash_single(BN128_P)

    def test_pair_left_overflow_raises(self):
        with pytest.raises(ValueError):
            poseidon_wrapper.poseidon_hash_pair(BN128_P, 0)

    def test_pair_right_overflow_raises(self):
        with pytest.raises(ValueError):
            poseidon_wrapper.poseidon_hash_pair(0, BN128_P)

    def test_pair_negative_left_raises(self):
        with pytest.raises(ValueError):
            poseidon_wrapper.poseidon_hash_pair(-1, 2)

    # --- Structural properties ---

    def test_deterministic_single(self):
        assert poseidon_wrapper.poseidon_hash_single(
            7
        ) == poseidon_wrapper.poseidon_hash_single(7)

    def test_deterministic_pair(self):
        assert poseidon_wrapper.poseidon_hash_pair(
            7, 13
        ) == poseidon_wrapper.poseidon_hash_pair(7, 13)

    def test_non_commutative(self):
        """H(a, b) != H(b, a) in general — order matters for the circuit."""
        assert poseidon_wrapper.poseidon_hash_pair(
            1, 2
        ) != poseidon_wrapper.poseidon_hash_pair(2, 1)

    def test_zero_inputs_produce_field_element(self):
        result = poseidon_wrapper.poseidon_hash_pair(0, 0)
        assert 0 <= result < BN128_P

    def test_large_valid_inputs(self):
        result = poseidon_wrapper.poseidon_hash_pair(BN128_P - 1, BN128_P - 2)
        assert 0 <= result < BN128_P


# ===========================================================================
# Module-scoped fixtures — built once to minimise subprocess overhead
# ===========================================================================


@pytest.fixture(scope="module")
def sample_leaves():
    """Six distinct field-element leaves: Poseidon(1) … Poseidon(6)."""
    return [poseidon_wrapper.poseidon_hash_single(i) for i in range(1, 7)]


@pytest.fixture(scope="module")
def tree3(sample_leaves):
    """Depth-3 tree (capacity 8) with 6 real leaves — shared across the module."""
    return MerkleTree(depth=3, leaves=sample_leaves)


# ===========================================================================
# MerkleTree construction
# ===========================================================================


class TestMerkleTreeConstruction:
    def test_root_is_int(self, tree3):
        assert isinstance(tree3.get_root(), int)

    def test_root_in_field(self, tree3):
        assert 0 <= tree3.get_root() < BN128_P

    def test_level_count_equals_depth_plus_one(self, sample_leaves):
        depth = 3
        tree = MerkleTree(depth=depth, leaves=sample_leaves)
        assert len(tree.tree) == depth + 1

    def test_leaf_layer_padded_to_capacity(self, sample_leaves):
        depth = 3
        tree = MerkleTree(depth=depth, leaves=sample_leaves)
        assert len(tree.tree[0]) == 2**depth

    def test_root_layer_is_singleton(self, tree3):
        assert len(tree3.tree[-1]) == 1

    def test_too_many_leaves_raises(self):
        with pytest.raises(ValueError):
            MerkleTree(depth=2, leaves=[1, 2, 3, 4, 5])  # capacity is 4

    def test_same_leaves_deterministic_root(self, sample_leaves):
        t1 = MerkleTree(depth=3, leaves=sample_leaves)
        t2 = MerkleTree(depth=3, leaves=sample_leaves)
        assert t1.get_root() == t2.get_root()

    def test_different_leaves_different_root(self):
        l1 = [
            poseidon_wrapper.poseidon_hash_single(1),
            poseidon_wrapper.poseidon_hash_single(2),
        ]
        l2 = [
            poseidon_wrapper.poseidon_hash_single(3),
            poseidon_wrapper.poseidon_hash_single(4),
        ]
        assert (
            MerkleTree(depth=2, leaves=l1).get_root()
            != MerkleTree(depth=2, leaves=l2).get_root()
        )

    def test_empty_tree_root_equals_zero_hash_at_depth(self):
        depth = 3
        tree = MerkleTree(depth=depth, leaves=[])
        assert tree.get_root() == tree.zero_hashes[depth]

    def test_depth1_two_leaves_root_matches_poseidon_pair(self):
        """depth=1, two leaves: root = Poseidon(leaf0, leaf1) exactly."""
        l0 = poseidon_wrapper.poseidon_hash_single(1)
        l1 = poseidon_wrapper.poseidon_hash_single(2)
        tree = MerkleTree(depth=1, leaves=[l0, l1])
        assert tree.get_root() == poseidon_wrapper.poseidon_hash_pair(l0, l1)

    def test_depth1_single_leaf_root_padded_with_zero(self):
        """depth=1, one leaf: root = Poseidon(leaf, zero_value=0)."""
        leaf = poseidon_wrapper.poseidon_hash_single(5)
        tree = MerkleTree(depth=1, leaves=[leaf])
        assert tree.get_root() == poseidon_wrapper.poseidon_hash_pair(leaf, 0)

    def test_full_tree_builds_correctly(self):
        """A completely populated tree (2^depth leaves) must build without error."""
        depth = 3
        leaves = [poseidon_wrapper.poseidon_hash_single(i + 1) for i in range(2**depth)]
        tree = MerkleTree(depth=depth, leaves=leaves)
        assert 0 <= tree.get_root() < BN128_P


# ===========================================================================
# Zero-hash chain
# ===========================================================================


class TestZeroHashes:
    def test_zero_hashes_length_is_depth_plus_one(self):
        depth = 4
        tree = MerkleTree(depth=depth, leaves=[])
        assert len(tree.zero_hashes) == depth + 1

    def test_zero_hashes_base_equals_zero_value(self):
        tree = MerkleTree(depth=3, leaves=[], zero_value=0)
        assert tree.zero_hashes[0] == 0

    def test_zero_hashes_chain_recurrence(self):
        """Each level: zero_hashes[i+1] == Poseidon(zero_hashes[i], zero_hashes[i])."""
        tree = MerkleTree(depth=4, leaves=[])
        for i in range(tree.depth):
            expected = poseidon_wrapper.poseidon_hash_pair(
                tree.zero_hashes[i], tree.zero_hashes[i]
            )
            assert tree.zero_hashes[i + 1] == expected

    def test_empty_tree_root_is_top_zero_hash(self):
        depth = 4
        tree = MerkleTree(depth=depth, leaves=[])
        assert tree.get_root() == tree.zero_hashes[depth]


# ===========================================================================
# Merkle proof structure, generation, and verification
# ===========================================================================


class TestMerkleProof:
    def test_proof_siblings_has_depth_entries(self, tree3):
        proof = tree3.get_proof(0)
        assert len(proof.siblings) == tree3.depth

    def test_proof_path_indices_has_depth_entries(self, tree3):
        proof = tree3.get_proof(0)
        assert len(proof.path_indices) == tree3.depth

    def test_path_indices_are_binary(self, tree3, sample_leaves):
        for i in range(len(sample_leaves)):
            proof = tree3.get_proof(i)
            assert all(
                b in (0, 1) for b in proof.path_indices
            ), f"Non-binary path at index {i}"

    def test_valid_proof_for_every_real_leaf(self, tree3, sample_leaves):
        root = tree3.get_root()
        for i, leaf in enumerate(sample_leaves):
            proof = tree3.get_proof(i)
            assert MerkleTree.verify_proof(
                leaf, proof, root
            ), f"Proof failed for leaf index {i}"

    def test_valid_proof_for_padded_zero_leaf(self, tree3, sample_leaves):
        """The first zero-padded slot must also produce a valid proof."""
        root = tree3.get_root()
        padded_idx = len(sample_leaves)
        proof = tree3.get_proof(padded_idx)
        assert MerkleTree.verify_proof(0, proof, root)

    def test_tampered_leaf_fails_verification(self, tree3, sample_leaves):
        root = tree3.get_root()
        proof = tree3.get_proof(0)
        tampered = (sample_leaves[0] + 1) % BN128_P
        assert not MerkleTree.verify_proof(tampered, proof, root)

    def test_tampered_sibling_fails_verification(self, tree3, sample_leaves):
        root = tree3.get_root()
        proof = tree3.get_proof(0)
        bad_siblings = list(proof.siblings)
        bad_siblings[0] = (bad_siblings[0] + 1) % BN128_P
        bad_proof = MerkleProof(siblings=bad_siblings, path_indices=proof.path_indices)
        assert not MerkleTree.verify_proof(sample_leaves[0], bad_proof, root)

    def test_wrong_root_fails_verification(self, tree3, sample_leaves):
        proof = tree3.get_proof(0)
        wrong_root = (tree3.get_root() + 1) % BN128_P
        assert not MerkleTree.verify_proof(sample_leaves[0], proof, wrong_root)

    def test_cross_leaf_proof_fails(self, tree3, sample_leaves):
        """A proof for leaf[1] cannot verify leaf[0]."""
        root = tree3.get_root()
        proof_1 = tree3.get_proof(1)
        assert not MerkleTree.verify_proof(sample_leaves[0], proof_1, root)

    def test_leftmost_leaf_all_path_indices_zero(self, tree3):
        """Index 0 is always a left child at every level → all path_indices == 0."""
        proof = tree3.get_proof(0)
        assert all(idx == 0 for idx in proof.path_indices)

    def test_second_leaf_first_path_index_is_one(self, tree3):
        """Index 1 is a right child at level 0 → path_indices[0] == 1."""
        proof = tree3.get_proof(1)
        assert proof.path_indices[0] == 1

    def test_rightmost_leaf_all_path_indices_one(self):
        """Index 2^depth - 1 is a right child at every level → all path_indices == 1."""
        depth = 2
        leaves = [poseidon_wrapper.poseidon_hash_single(i + 1) for i in range(2**depth)]
        tree = MerkleTree(depth=depth, leaves=leaves)
        proof = tree.get_proof(2**depth - 1)
        assert proof.path_indices == [1] * depth


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    def test_negative_index_raises(self):
        tree = MerkleTree(depth=2, leaves=[1, 2])
        with pytest.raises(IndexError):
            tree.get_proof(-1)

    def test_index_at_capacity_raises(self):
        """get_proof(2**depth) must raise — valid indices are 0 … 2**depth-1."""
        tree = MerkleTree(depth=2, leaves=[1, 2])
        with pytest.raises(IndexError):
            tree.get_proof(4)

    def test_depth1_single_leaf_proof_verifies(self):
        leaf = poseidon_wrapper.poseidon_hash_single(99)
        tree = MerkleTree(depth=1, leaves=[leaf])
        assert MerkleTree.verify_proof(leaf, tree.get_proof(0), tree.get_root())

    def test_depth1_full_tree_both_leaves_verify(self):
        l0 = poseidon_wrapper.poseidon_hash_single(10)
        l1 = poseidon_wrapper.poseidon_hash_single(20)
        tree = MerkleTree(depth=1, leaves=[l0, l1])
        root = tree.get_root()
        assert MerkleTree.verify_proof(l0, tree.get_proof(0), root)
        assert MerkleTree.verify_proof(l1, tree.get_proof(1), root)

    def test_custom_zero_value_changes_root(self):
        leaf = poseidon_wrapper.poseidon_hash_single(7)
        t_default = MerkleTree(depth=2, leaves=[leaf], zero_value=0)
        t_custom = MerkleTree(depth=2, leaves=[leaf], zero_value=1)
        assert t_default.get_root() != t_custom.get_root()

    def test_last_real_leaf_in_large_tree(self):
        depth = 4
        leaves = [poseidon_wrapper.poseidon_hash_single(i + 1) for i in range(10)]
        tree = MerkleTree(depth=depth, leaves=leaves)
        last = len(leaves) - 1
        assert MerkleTree.verify_proof(
            leaves[last], tree.get_proof(last), tree.get_root()
        )

    def test_merkleproof_dataclass_fields(self):
        proof = MerkleProof(siblings=[10, 20], path_indices=[0, 1])
        assert proof.siblings == [10, 20]
        assert proof.path_indices == [0, 1]


# ===========================================================================
# Key manager — leaf commitment integration
# ===========================================================================


class TestKeyManagerIntegration:
    def test_leaf_commitment_is_field_element(self):
        _priv, leaf = key_manager.generate_key_pair()
        assert 0 <= leaf < BN128_P

    def test_leaf_commitment_equals_poseidon_single(self):
        """derive_leaf_commitment(k) must equal poseidon_hash_single(k)."""
        priv = secrets.randbelow(BN128_P)
        assert key_manager.derive_leaf_commitment(
            priv
        ) == poseidon_wrapper.poseidon_hash_single(priv)

    def test_generate_test_identities_correct_counts(self):
        n = 5
        idents = key_manager.generate_test_identities(n)
        assert len(idents["private_keys"]) == n
        assert len(idents["leaf_commitments"]) == n

    def test_key_manager_leaves_valid_in_merkle_tree(self):
        """Commitments from key_manager must be valid Merkle leaves with passing proofs."""
        idents = key_manager.generate_test_identities(4)
        leaves = idents["leaf_commitments"]
        tree = MerkleTree(depth=3, leaves=leaves)
        root = tree.get_root()
        for i, leaf in enumerate(leaves):
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(
                leaf, proof, root
            ), f"key_manager leaf {i} failed"

    def test_private_keys_unique(self):
        """Randomly generated private keys should be unique (collision negligible)."""
        idents = key_manager.generate_test_identities(10)
        keys = idents["private_keys"]
        assert len(set(keys)) == len(keys)

    def test_leaf_commitments_unique(self):
        """Each distinct private key must map to a distinct leaf commitment."""
        idents = key_manager.generate_test_identities(10)
        leaves = idents["leaf_commitments"]
        assert len(set(leaves)) == len(leaves)
