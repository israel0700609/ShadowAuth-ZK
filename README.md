<p align="center">
  <h1 align="center">🛡️ ShadowAuth-ZK</h1>
  <p align="center">
    <strong>Zero-Knowledge Proof Anonymous Peer Authentication over Network Covert Channels</strong>
  </p>
  <p align="center">
    <a href="#overview">Overview</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#usage">Usage</a> •
    <a href="#contributing">Contributing</a> •
    <a href="#license">License</a>
  </p>
</p>

---

## Overview

**ShadowAuth-ZK** is a Zero-Knowledge Proof (ZKP) based Anonymous Peer Authentication system operating over Network Covert Channels. It allows a client to prove authorization to a server **without revealing its specific identity, credentials, or triggering Deep Packet Inspection (DPI) and Intrusion Detection Systems (IDS)**.

### Key Mechanisms

| Mechanism | Description |
|---|---|
| **Authorization** | Merkle Tree of authorized user public keys |
| **Authentication (ZKP)** | Circom-based zk-SNARK (Groth16) proving knowledge of a private key corresponding to a leaf in the Merkle Tree |
| **Anti-Replay & Session Binding** | The ZKP circuit binds a Server Challenge (Nonce) and a Client Ephemeral Public Key (ECDH) into a `responseHash` constraint |
| **Transport** | Covert channel communication (ICMP/Ping or DNS tunneling) to evade firewall detection |

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         ShadowAuth-ZK                            │
│                                                                  │
│  ┌─────────────┐    Covert Channel     ┌──────────────────────┐  │
│  │   Client     │  (ICMP / DNS Tunnel) │   Server              │  │
│  │             │◄────────────────────►│                      │  │
│  │  • CLI       │                      │  • Listener          │  │
│  │  • Prover    │                      │  • Challenge Gen     │  │
│  │  • Handshake │                      │  • Verifier          │  │
│  └──────┬──────┘                      └──────────┬───────────┘  │
│         │                                        │               │
│  ┌──────┴──────────────────────────────────────┴───────────┐   │
│  │                    Shared Libraries                       │   │
│  │  • Merkle Tree (Poseidon Hash)                           │   │
│  │  • ECDH Key Derivation                                   │   │
│  │  • AES-256-GCM Session Encryption                        │   │
│  │  • ZK Circuit (Groth16 via SnarkJS)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Protocol Flow

```
Client                                          Server
  │                                               │
  │  ──── [1] HELLO (covert) ────────────────►   │
  │                                               │
  │  ◄─── [2] CHALLENGE (nonce) ─────────────    │
  │                                               │
  │  Generate ephemeral ECDH keypair              │
  │  Compute ZK proof:                            │
  │    - Merkle inclusion of pubkey               │
  │    - Bind nonce + ephemeral pubkey            │
  │                                               │
  │  ──── [3] ZK_PROOF + ephemeral_pub ──────►   │
  │                                               │
  │                          Verify Groth16 proof │
  │                          Derive shared secret │
  │                                               │
  │  ◄─── [4] SESSION_ACK (AES encrypted) ──    │
  │                                               │
  │  ════ [5] Encrypted Session ═══════════════  │
  │                                               │
```

## Tech Stack

| Layer | Technology |
|---|---|
| ZK Circuits | [Circom 2](https://docs.circom.io/) + [SnarkJS](https://github.com/iden3/snarkjs) |
| Proving System | Groth16 (BN128) |
| Networking | Python 3.10+ / [Scapy](https://scapy.net/) |
| Cryptography | `cryptography` (ECDH, AES-256-GCM), Poseidon Hash |
| Testing | Pytest (Python), Mocha (Circuits) |
| CI/CD | GitHub Actions |

## Project Structure

```
ShadowAuth-ZK/
├── circuits/
│   ├── src/                    # Circom circuit source files
│   │   ├── ShadowAuth.circom
│   │   ├── MerkleTreeInclusionProof.circom
│   │   └── Poseidon.circom
│   ├── build/                  # Compiled circuit artifacts (gitignored)
│   └── scripts/                # Circuit compilation & setup scripts
│       ├── compile_circuit.sh
│       ├── trusted_setup.sh
│       └── generate_witness.sh
├── src/
│   ├── client/                 # Client CLI, prover, handshake
│   ├── server/                 # Server listener, verifier, challenge
│   ├── network/                # Covert channel transport (ICMP/DNS)
│   ├── crypto/                 # Merkle tree, ECDH, AES, key management
│   └── common/                 # Config, constants, logging
├── tests/
│   ├── unit/                   # Pytest unit tests
│   ├── integration/            # End-to-end integration tests
│   └── circuits/               # Circuit-level tests (JS/Mocha)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROTOCOL_FLOW.md
│   └── diagrams/
├── scripts/                    # Environment & key generation scripts
├── keys/                       # Generated keys (gitignored)
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile
└── README.md
```

## Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+ & npm
- **Circom** 2.1+ ([Installation](https://docs.circom.io/getting-started/installation/))
- **SnarkJS** (`npm install -g snarkjs`)
- Root/Administrator privileges (required for raw socket operations)

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-org>/ShadowAuth-ZK.git
cd ShadowAuth-ZK

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node.js dependencies (for circuit testing)
npm install

# Compile circuits and run trusted setup
chmod +x circuits/scripts/*.sh
./circuits/scripts/compile_circuit.sh
./circuits/scripts/trusted_setup.sh
```

### Quick Start

```bash
# Generate Merkle tree from authorized keys
python -m src.crypto.key_manager generate --output keys/

# Start the server (requires elevated privileges)
sudo python -m src.server.listener --transport icmp --port 0

# Run the client handshake
sudo python -m src.client.cli --target <server-ip> --transport icmp
```

## Usage

### Running Tests

```bash
# Run all Python tests
pytest tests/ -v

# Run circuit tests
npm test

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Linting & Formatting

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type checking
mypy src/
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, branching strategy, and the process for submitting pull requests.

### Branch Naming Convention

| Branch Pattern | Purpose |
|---|---|
| `main` | Production-ready, stable releases |
| `dev` | Integration branch — all features merge here first |
| `feature/<issue>-<short-desc>` | Feature development |
| `fix/<issue>-<short-desc>` | Bug fixes |
| `chore/<short-desc>` | Maintenance tasks |

### Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

feat(circuits): add Merkle inclusion proof circuit
fix(network): handle fragmented ICMP payloads
docs(readme): update installation instructions
test(crypto): add ECDH key derivation tests
chore(ci): configure GitHub Actions pipeline
```

## Security

> **⚠️ Disclaimer:** This project is for **educational and research purposes only**. Covert channel techniques should only be used in authorized environments. Unauthorized use may violate local laws and regulations.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with 🔐 cryptographic rigor and 🕵️ operational stealth.
</p>
