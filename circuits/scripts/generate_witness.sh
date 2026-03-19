#!/usr/bin/env bash
set -Eeuo pipefail

trap 'echo "[ERROR] generate_witness.sh failed at line ${LINENO}." >&2' ERR

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/circuits/build"
CIRCUIT_NAME="ShadowAuth"

WASM_DIR="$BUILD_DIR/${CIRCUIT_NAME}_js"
WASM_FILE="$WASM_DIR/${CIRCUIT_NAME}.wasm"
WITNESS_GEN_JS="$WASM_DIR/generate_witness.js"

INPUT_JSON="${1:-}"
OUTPUT_WITNESS="${2:-$BUILD_DIR/witness.wtns}"

if [ -z "$INPUT_JSON" ]; then
	echo "Usage: $0 <input.json> [output.wtns]"
	exit 1
fi

if ! command -v node >/dev/null 2>&1; then
	echo "Error: node is not installed or not in PATH."
	exit 1
fi

if [ ! -f "$WITNESS_GEN_JS" ] || [ ! -f "$WASM_FILE" ]; then
	echo "Error: Missing witness generator artifacts in $WASM_DIR"
	echo "Run circuits/scripts/compile_circuit.sh first."
	exit 1
fi

if [ ! -f "$INPUT_JSON" ]; then
	echo "Error: Input JSON not found at $INPUT_JSON"
	exit 1
fi

mkdir -p "$(dirname "$OUTPUT_WITNESS")"

echo "Generating witness from: $INPUT_JSON"
node "$WITNESS_GEN_JS" "$WASM_FILE" "$INPUT_JSON" "$OUTPUT_WITNESS"

if [ ! -f "$OUTPUT_WITNESS" ]; then
	echo "Error: Witness output was not created: $OUTPUT_WITNESS"
	exit 1
fi

echo "Witness generated: $OUTPUT_WITNESS"
