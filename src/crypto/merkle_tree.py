"""
Binary Merkle Tree implementation using the Poseidon hash function.

This module constructs a static, fixed-depth binary Merkle tree. It is used
to generate the public root (the commitment to the set of authorized users)
and to extract the Merkle inclusion proofs (sibling paths) required as
private inputs for the Circom ZKP circuit.
"""

from dataclasses import dataclass
from typing import List

import poseidon_wrapper


@dataclass
class MerkleProof:
    """
    Data Transfer Object containing the exact parameters needed for the ZKP circuit.

    Attributes:
        siblings (List[int]): The hash values of the sibling nodes along the path to the root.
        path_indices (List[int]): A list of 0s and 1s indicating whether the sibling
                                  is on the left (0) or the right (1).
    """

    siblings: List[int]
    path_indices: List[int]


class MerkleTree:
    """
    A fixed-depth binary Merkle Tree.

    Attributes:
        depth (int): The number of levels in the tree (excluding the root).
                     Determines maximum capacity (2^depth leaves).
        zero_value (int): The canonical hash value used to pad empty leaves.
        leaves (List[int]): The actual populated leaf values.
        tree (List[List[int]]): The 2D representation of the tree, where tree[0]
                                is the leaf layer and tree[-1] is the root.
    """
    def __init__(self, depth: int, leaves: List[int], zero_value: int = 0):
        """
        Initializes and constructs the Merkle Tree.

        Args:
            depth (int): The depth of the tree (must match circuit `nLevels`).
            leaves (List[int]): Initial list of valid leaf hashes (commitments).
            zero_value (int, optional): Value used for empty leaves. Defaults to 0.

        Raises:
            ValueError: If len(leaves) > 2**depth.
        """
        self.depth = depth
        self.zero_value = zero_value
        self.max_leaves = 2**depth
        self.leaves = leaves

        if len(self.leaves) > self.max_leaves:
            raise ValueError(
                f"Too many leaves. Max allowed for depth {depth} is {self.max_leaves}"
            )

        self.tree = []

        self.zero_hashes = [self.zero_value]
        for i in range(self.depth):
            next_zero_hash = poseidon_wrapper.poseidon_hash_pair(
                self.zero_hashes[i], self.zero_hashes[i]
            )
            self.zero_hashes.append(next_zero_hash)

        self._build_tree()

    def _build_tree(self) -> None:
        """
        Internal method to construct the tree levels using `poseidon_hash_pair`.
        Pads the initial leaf list with `zero_value` up to 2**depth.
        """
        padded_leaves = self.leaves.copy()
        while len(padded_leaves) < self.max_leaves:
            padded_leaves.append(self.zero_hashes[0])

        self.tree.append(padded_leaves)

        for i in range(self.depth):
            level_hashes = []

            for j in range(0, len(self.tree[i]), 2):
                left = self.tree[i][j]
                right = self.tree[i][j + 1]

                if left == self.zero_hashes[i] and right == self.zero_hashes[i]:
                    level_hashes.append(self.zero_hashes[i + 1])
                    continue

                parent_hash = poseidon_wrapper.poseidon_hash_pair(left, right)
                level_hashes.append(parent_hash)

            self.tree.append(level_hashes)

    def get_root(self) -> int:
        """
        Retrieves the Merkle root of the tree.

        Returns:
            int: The root hash (a public input for the ZKP circuit).
        """
        return self.tree[-1][0]

    def get_proof(self, leaf_index: int) -> MerkleProof:
        if leaf_index < 0 or leaf_index >= self.max_leaves:
            raise IndexError("Leaf index out of bounds.")

        current_index = leaf_index
        path_indices = []
        siblings = []

        for i in range(self.depth):
            is_right_node = (current_index + 1) % 2 == 0

            if is_right_node:
                path_indices.append(1)
                siblings.append(self.tree[i][current_index - 1])
            else:
                path_indices.append(0)
                siblings.append(self.tree[i][current_index + 1])

            current_index //= 2

        return MerkleProof(siblings=siblings, path_indices=path_indices)

    @staticmethod
    def verify_proof(leaf: int, proof: MerkleProof, root: int) -> bool:
        """
        Statically verifies a Merkle proof in Python (sanity check before ZKP).

        Args:
            leaf (int): The leaf hash to verify.
            proof (MerkleProof): The proof object containing siblings and indices.
            root (int): The expected Merkle root.

        Returns:
            bool: True if the calculated root matches the expected root, False otherwise.
        """
        current_hash = leaf

        for i in range(len(proof.siblings)):
            sibling = proof.siblings[i]
            direction = proof.path_indices[i]

            if direction == 0:
                current_hash = poseidon_wrapper.poseidon_hash_pair(
                    current_hash, sibling
                )
            else:
                current_hash = poseidon_wrapper.poseidon_hash_pair(
                    sibling, current_hash
                )

        return current_hash == root
