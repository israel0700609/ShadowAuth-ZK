#!/usr/bin/env bash
set -Eeuo pipefail

trap 'echo "[ERROR] trusted_setup.sh failed at line ${LINENO}." >&2' ERR

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/circuits/build"
CIRCUIT_NAME="ShadowAuth"
R1CS_FILE="$BUILD_DIR/${CIRCUIT_NAME}.r1cs"

PTAU_POWER="${PTAU_POWER:-14}"
PTAU_FILE="${PTAU_FILE:-$BUILD_DIR/powersOfTau28_hez_final_${PTAU_POWER}.ptau}"
PTAU_URL="${PTAU_URL:-https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_${PTAU_POWER}.ptau}"

ZKEY_0000="$BUILD_DIR/${CIRCUIT_NAME}.0000.zkey"
ZKEY_0001="$BUILD_DIR/${CIRCUIT_NAME}.0001.zkey"
FINAL_ZKEY="$BUILD_DIR/proving_key.zkey"
VERIFICATION_KEY="$BUILD_DIR/verification_key.json"

ENTROPY="${ZKEY_ENTROPY:-ShadowAuth-$(date +%s)-$RANDOM}"
FORCE_REBUILD="${FORCE_REBUILD:-0}"

mkdir -p "$BUILD_DIR"

if ! command -v snarkjs >/dev/null 2>&1; then
	echo "Error: snarkjs is not installed or not in PATH."
	exit 1
fi

if [ ! -f "$R1CS_FILE" ]; then
	echo "Error: Missing R1CS file at $R1CS_FILE"
	echo "Run circuits/scripts/compile_circuit.sh first."
	exit 1
fi

download_file() {
	local url="$1"
	local output="$2"

	if command -v curl >/dev/null 2>&1; then
		curl -fsSL "$url" -o "$output"
	elif command -v wget >/dev/null 2>&1; then
		wget -qO "$output" "$url"
	else
		echo "Error: Neither curl nor wget is installed."
		return 1
	fi
}

prepare_ptau() {
	if [ -f "$PTAU_FILE" ]; then
		echo "Using existing ptau file: $PTAU_FILE"
		return 0
	fi

	echo "No local ptau file found. Attempting download: $PTAU_URL"
	if download_file "$PTAU_URL" "$PTAU_FILE"; then
		echo "Downloaded ptau file: $PTAU_FILE"
		return 0
	fi

	echo "Download failed. Generating ptau locally (this may take a while)."
	local pot_0000="$BUILD_DIR/pot${PTAU_POWER}_0000.ptau"
	local pot_0001="$BUILD_DIR/pot${PTAU_POWER}_0001.ptau"

	snarkjs powersoftau new bn128 "$PTAU_POWER" "$pot_0000" -v
	snarkjs powersoftau contribute "$pot_0000" "$pot_0001" \
		--name="ShadowAuth Phase1 contribution" \
		-v \
		-e="$ENTROPY"
	snarkjs powersoftau prepare phase2 "$pot_0001" "$PTAU_FILE" -v

	rm -f "$pot_0000" "$pot_0001"
	echo "Generated ptau file: $PTAU_FILE"
}

if [ "$FORCE_REBUILD" = "1" ]; then
	echo "FORCE_REBUILD=1 set, removing previous setup artifacts."
	rm -f "$ZKEY_0000" "$ZKEY_0001" "$FINAL_ZKEY" "$VERIFICATION_KEY"
fi

if [ -f "$FINAL_ZKEY" ] && [ -f "$VERIFICATION_KEY" ] && [ "$FORCE_REBUILD" != "1" ]; then
	echo "Trusted setup already completed."
	echo "Reusing: $FINAL_ZKEY"
	echo "Reusing: $VERIFICATION_KEY"
	exit 0
fi

prepare_ptau

echo "Running Groth16 setup (Phase 2)..."
snarkjs groth16 setup "$R1CS_FILE" "$PTAU_FILE" "$ZKEY_0000"

echo "Adding entropy contribution..."
snarkjs zkey contribute "$ZKEY_0000" "$ZKEY_0001" \
	--name="ShadowAuth Phase2 contribution" \
	-v \
	-e="$ENTROPY"

mv -f "$ZKEY_0001" "$FINAL_ZKEY"

echo "Exporting verification key..."
snarkjs zkey export verificationkey "$FINAL_ZKEY" "$VERIFICATION_KEY"

echo "Verifying final zkey against circuit and ptau..."
snarkjs zkey verify "$R1CS_FILE" "$PTAU_FILE" "$FINAL_ZKEY"

echo "Trusted setup complete."
echo "Proving key: $FINAL_ZKEY"
echo "Verification key: $VERIFICATION_KEY"
