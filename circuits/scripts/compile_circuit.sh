#!/usr/bin/env bash
set -Eeuo pipefail

trap 'echo "[ERROR] compile_circuit.sh failed at line ${LINENO}." >&2' ERR

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/circuits/build"
SRC_DIR="$ROOT_DIR/circuits/src"
INCLUDE_DIR="$ROOT_DIR/node_modules"
CIRCUIT_NAME="ShadowAuth"
CIRCUIT_FILE="$SRC_DIR/${CIRCUIT_NAME}.circom"
R1CS_FILE="$BUILD_DIR/${CIRCUIT_NAME}.r1cs"

mkdir -p "$BUILD_DIR"

if ! command -v circom >/dev/null 2>&1 && ! command -v circom.exe >/dev/null 2>&1; then
	echo "Error: circom is not installed or not in PATH."
	exit 1
fi

if ! command -v snarkjs >/dev/null 2>&1 && ! command -v snarkjs.cmd >/dev/null 2>&1; then
	echo "Error: snarkjs is not installed or not in PATH."
	exit 1
fi

if [ ! -f "$CIRCUIT_FILE" ]; then
	echo "Error: Circuit source not found at $CIRCUIT_FILE."
	exit 1
fi

if [ ! -f "$INCLUDE_DIR/circomlib/circuits/poseidon.circom" ]; then
	echo "Error: circomlib not found at $INCLUDE_DIR/circomlib."
	echo "Run: npm install circomlib"
	exit 1
fi

echo "Compiling ${CIRCUIT_NAME}.circom..."
circom "$CIRCUIT_FILE" 2>/dev/null || circom.exe "$CIRCUIT_FILE" \
	--r1cs --wasm --sym \
	-l "$INCLUDE_DIR" \
	-o "$BUILD_DIR"

if [ ! -f "$R1CS_FILE" ]; then
	echo "Error: Expected R1CS output not found: $R1CS_FILE"
	exit 1
fi

echo "Circuit compilation complete. Artifacts in: $BUILD_DIR"

R1CS_INFO="$(npx snarkjs r1cs info "$R1CS_FILE")"
CONSTRAINT_LINE="$(printf "%s\n" "$R1CS_INFO" | grep -E "# of Constraints" | head -n1 || true)"
CONSTRAINT_COUNT="${CONSTRAINT_LINE##*:}"
CONSTRAINT_COUNT="$(printf "%s" "$CONSTRAINT_COUNT" | tr -d "[:space:]")"

if [ -z "$CONSTRAINT_COUNT" ]; then
	echo "Error: Could not parse constraint count from snarkjs output."
	echo "$R1CS_INFO"
	exit 1
fi

echo "Constraint count: $CONSTRAINT_COUNT"
