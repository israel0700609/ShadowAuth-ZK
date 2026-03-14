#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/circuits/build"
SRC_DIR="$ROOT_DIR/circuits/src"
INCLUDE_DIR="$ROOT_DIR/node_modules"

mkdir -p "$BUILD_DIR"

if ! command -v circom >/dev/null 2>&1; then
	echo "Error: circom is not installed or not in PATH."
	exit 1
fi

if [ ! -f "$INCLUDE_DIR/circomlib/circuits/poseidon.circom" ]; then
	echo "Error: circomlib not found at $INCLUDE_DIR/circomlib."
	echo "Run: npm install circomlib"
	exit 1
fi

echo "Compiling ShadowAuth.circom..."
circom "$SRC_DIR/ShadowAuth.circom" \
	--r1cs --wasm --sym \
	-l "$INCLUDE_DIR" \
	-o "$BUILD_DIR"

echo "Circuit compilation complete. Artifacts in: $BUILD_DIR"
