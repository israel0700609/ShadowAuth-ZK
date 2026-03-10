# ShadowAuth-ZK — GitHub Issues (Copy-Paste Ready)

Below are the first **9 GitHub Issues** for the ShadowAuth-ZK project, with the first 3 fully expanded.

---

## Issue #1: Project Initialization & CI/CD Setup

**Title:** `chore: Project Initialization — Folder Structure, CI/CD, Linting & Formatting`

**Labels:** `chore`, `priority:high`, `milestone:foundation`

**Assignees:** —

### Description

Set up the foundational project infrastructure including directory scaffolding, dependency management, CI/CD pipeline, and code quality tooling.

### Acceptance Criteria

- [ ] Repository initialized with `main` and `dev` branches
- [ ] Complete folder structure created per the architecture spec:
  - `circuits/src/`, `circuits/build/`, `circuits/scripts/`
  - `src/client/`, `src/server/`, `src/network/`, `src/crypto/`, `src/common/`
  - `tests/unit/`, `tests/integration/`, `tests/circuits/`
  - `docs/`, `scripts/`, `keys/`
- [ ] `.gitignore` properly excludes build artifacts, keys, `.env`, venvs, and node_modules
- [ ] `pyproject.toml` configured with:
  - Project metadata
  - `ruff` linting (including `flake8-bandit` security rules)
  - `pytest` configuration with custom markers (`slow`, `integration`, `requires_root`)
  - `mypy` strict configuration
- [ ] `requirements.txt` and `requirements-dev.txt` defined
- [ ] `.pre-commit-config.yaml` with hooks for ruff, trailing whitespace, private key detection
- [ ] GitHub Actions CI workflow (`.github/workflows/ci.yml`) with:
  - Lint & format check job
  - Test job (matrix: Python 3.10, 3.11, 3.12)
  - Circuit test job (Node.js + Circom)
- [ ] `Makefile` with targets: `install`, `install-dev`, `lint`, `format`, `typecheck`, `test`, `test-cov`, `circuits`, `clean`
- [ ] `README.md` with architecture overview, protocol flow diagram, tech stack, and setup instructions
- [ ] `CONTRIBUTING.md` with branching strategy, commit convention, and PR checklist
- [ ] `CHANGELOG.md` initialized
- [ ] `.env.example` with all required environment variables documented

### Technical Notes

- Python 3.10+ minimum target
- Use `ruff` as the sole linter/formatter (replaces black, isort, flake8)
- Conventional Commits enforced via pre-commit and PR review
- Branch protection rules to be configured manually on GitHub after push

### Definition of Done

All CI checks pass on an empty project. `make install-dev && make lint && make test` succeeds.

---

## Issue #2: Cryptography — Python Merkle Tree & Poseidon Utilities

**Title:** `feat(crypto): Implement Merkle Tree with Poseidon Hash — Generation & Proof Extraction`

**Labels:** `feature`, `crypto`, `priority:high`, `milestone:core-crypto`

**Assignees:** —

### Description

Implement a binary Merkle Tree in Python using the **Poseidon hash function** (matching Circom's native `Poseidon` implementation). This is the authorization backbone — the root of the tree is a public commitment to the set of authorized users, and a Merkle proof is the witness for the ZK circuit.

### Acceptance Criteria

- [ ] **`src/crypto/poseidon_wrapper.py`** — Poseidon hash wrapper:
  - Implement a Python-compatible Poseidon hash function that produces outputs **identical** to Circom's `circomlib/poseidon` over BN128's scalar field
  - Support hashing 2 inputs (for binary Merkle tree) and 1 input (for leaf hashing)
  - Include a test vector validation against known Circom outputs
- [ ] **`src/crypto/merkle_tree.py`** — Merkle Tree implementation:
  - `MerkleTree` class accepting a list of leaf values (public key commitments)
  - Fixed-depth tree (configurable, default `TREE_DEPTH=20`)
  - Pad empty leaves with a canonical zero value
  - Methods:
    - `get_root() -> int` — returns the Merkle root
    - `get_proof(leaf_index: int) -> MerkleProof` — returns sibling path + path indices
    - `verify_proof(leaf: int, proof: MerkleProof, root: int) -> bool` — static verification
  - `MerkleProof` dataclass: `siblings: list[int]`, `path_indices: list[int]`
- [ ] **`src/crypto/key_manager.py`** — Key management utilities:
  - Generate a set of test key pairs (ECDH on secp256k1 or Curve25519)
  - Derive a "leaf commitment" from each public key (e.g., `Poseidon(pubkey_x, pubkey_y)`)
  - Serialize/deserialize key sets to JSON for testing
- [ ] **Unit tests** (`tests/unit/test_merkle_tree.py`):
  - Test tree construction with known inputs and verify root
  - Test proof generation and verification (valid proofs pass, tampered proofs fail)
  - Test edge cases: single-leaf tree, full tree, out-of-bounds index
  - Cross-validate Poseidon outputs against Circom-generated test vectors

### Technical Notes

- **Critical:** The Python Poseidon implementation MUST produce the same field outputs as Circom's. Use a reference implementation such as `poseidon-py` or port the constants from `circomlib`.
- All arithmetic operates over the BN128 scalar field ($p = 21888242871839275222246405745257275088548364400416034343698204186575808495617$).
- The Merkle tree depth must match the circuit parameter (`nLevels`) exactly.
- Leaf values are field elements, not raw bytes.

### Dependencies

- Depends on: Issue #1 (project structure)
- Blocks: Issue #3 (circuit needs matching tree logic), Issue #5 (prover needs proof generation)

### Definition of Done

`pytest tests/unit/test_merkle_tree.py -v` passes. Poseidon outputs match Circom reference vectors. Merkle proofs are compatible with the circuit witness format.

---

## Issue #3: ZK Circuits — Core Authentication Circuit (`ShadowAuth.circom`)

**Title:** `feat(circuits): Implement Core ZK Authentication Circuit — Merkle Inclusion + Challenge + ECDH Binding`

**Labels:** `feature`, `circuits`, `priority:high`, `milestone:core-zk`

**Assignees:** —

### Description

Design and implement the core zk-SNARK circuit in **Circom 2** that enables anonymous authentication. The circuit proves three things simultaneously:

1. **Merkle Inclusion:** The prover knows a private key whose corresponding public key is a leaf in the authorized Merkle Tree (committed to by a known root).
2. **Challenge Binding:** The proof is bound to a server-issued nonce, preventing replay attacks.
3. **ECDH Ephemeral Key Binding:** The proof is bound to a client-generated ephemeral public key, enabling secure session derivation.

### Acceptance Criteria

- [ ] **`circuits/src/MerkleTreeInclusionProof.circom`**:
  - Template `MerkleTreeInclusionProof(nLevels)` (parameterized depth)
  - Inputs: `leaf`, `pathElements[nLevels]`, `pathIndices[nLevels]`
  - Output: `root`
  - Uses Poseidon hash from `circomlib`
- [ ] **`circuits/src/ShadowAuth.circom`** — Main circuit:
  - **Private inputs:**
    - `privateKey` — the user's secret key (field element)
    - `pathElements[nLevels]` — Merkle sibling path
    - `pathIndices[nLevels]` — left/right path indicators (0 or 1)
  - **Public inputs:**
    - `merkleRoot` — the committed root of acceptable users
    - `serverChallenge` — nonce issued by the server
    - `clientEphemeralPubKey` — ECDH ephemeral public key (x-coordinate or hash)
  - **Public output:**
    - `responseHash` — `Poseidon(serverChallenge, clientEphemeralPubKey)` binding the session
  - **Constraints:**
    1. Derive `publicKey` from `privateKey` (simplified: `Poseidon(privateKey)` or use a scalar-to-point gadget)
    2. Compute `leafCommitment = Poseidon(publicKey)`
    3. Verify `MerkleTreeInclusionProof(leafCommitment, path, indices) == merkleRoot`
    4. Compute `responseHash = Poseidon(serverChallenge, clientEphemeralPubKey)` and expose as output
  - Total constraints should be manageable for Groth16 (target < 100K constraints at depth 20)
- [ ] **Circuit tests** (`tests/circuits/test_circuit.js`):
  - Use `circom_tester` or `snarkjs` to:
    - Test valid witness generation (authorized user, correct proof → passes)
    - Test invalid witness rejection (wrong private key → fails)
    - Test wrong Merkle root rejection
    - Test replay resistance (changing `serverChallenge` invalidates proof)

### Technical Notes

- Use `circomlib` for Poseidon, Mux, and comparator components.
- The circuit should be compiled targeting **BN128** (default for Groth16).
- `nLevels = 20` by default (supports ~1M authorized users).
- The `privateKey → publicKey` derivation is simplified to `Poseidon(privateKey)` for Phase 1. A full EC scalar multiplication (Baby Jubjub) can replace this in Phase 2.
- All values are elements of the BN128 scalar field.

### Circuit Diagram

```
                            ┌─────────────────────────────┐
   privateKey (private) ──► │  Poseidon(privateKey)        │──► publicKey
                            └─────────────────────────────┘
                                        │
                                        ▼
                            ┌─────────────────────────────┐
                            │  Poseidon(publicKey)         │──► leafCommitment
                            └─────────────────────────────┘
                                        │
                                        ▼
                            ┌─────────────────────────────┐
   pathElements (private)──►│  MerkleTreeInclusionProof    │
   pathIndices  (private)──►│  (nLevels = 20)              │──► computedRoot
                            └─────────────────────────────┘
                                        │
                                        ▼
                            ┌─────────────────────────────┐
   merkleRoot (public) ───► │  computedRoot === merkleRoot  │  (constraint)
                            └─────────────────────────────┘

                            ┌─────────────────────────────┐
   serverChallenge (pub)──► │  Poseidon(challenge,         │
   clientEphPubKey (pub)──► │          ephPubKey)          │──► responseHash (public output)
                            └─────────────────────────────┘
```

### Dependencies

- Depends on: Issue #1 (project structure), Issue #2 (Merkle tree logic must match)
- Blocks: Issue #4 (compilation scripts), Issue #5 (Python prover wrappers)

### Definition of Done

Circuit compiles with `circom --r1cs --wasm --sym`. Valid witness generates successfully. Invalid witnesses are rejected. Circuit constraint count is documented.

---

## Issues #4–#9 (Summary Titles for Backlog)

| # | Title | Labels | Milestone |
|---|---|---|---|
| 4 | `chore(circuits): Compilation & Trusted Setup Scripts` | `chore`, `circuits` | `core-zk` |
| 5 | `feat(crypto): Python ZKP Wrappers — SnarkJS Prover & Verifier` | `feature`, `crypto` | `core-zk` |
| 6 | `feat(network): Covert Channel Transport Layer — ICMP & DNS` | `feature`, `network` | `transport` |
| 7 | `feat(server): Server Listener & Challenge Generator` | `feature`, `server` | `application` |
| 8 | `feat(client): Client CLI & Handshake Flow` | `feature`, `client` | `application` |
| 9 | `feat(crypto): ECDH Key Agreement & AES-256-GCM Session` | `feature`, `crypto` | `session` |
