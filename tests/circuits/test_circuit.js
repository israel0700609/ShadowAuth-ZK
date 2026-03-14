const assert = require("node:assert/strict");
const path = require("node:path");

const circomlibjs = require("circomlibjs");
const wasm_tester = require("circom_tester").wasm;

function toSignal(v) {
	return v.toString();
}

describe("ShadowAuth circuit", function () {
	this.timeout(180000);

	const nLevels = 20;
	const authorizedIndex = 7;

	let circuit;
	let poseidon;
	let F;

	function fr(value) {
		return BigInt(F.toString(value));
	}

	function p1(a) {
		return fr(poseidon([BigInt(a)]));
	}

	function p2(a, b) {
		return fr(poseidon([BigInt(a), BigInt(b)]));
	}

	function buildZeroHashes(levels) {
		const zeros = [0n];
		for (let i = 0; i < levels; i++) {
			zeros.push(p2(zeros[i], zeros[i]));
		}
		return zeros;
	}

	function buildMerklePathForSingleLeaf(leaf, index, levels) {
		const zeroHashes = buildZeroHashes(levels);
		const pathElements = [];
		const pathIndices = [];

		let current = leaf;
		for (let i = 0; i < levels; i++) {
			const bit = (index >> i) & 1;
			const sibling = zeroHashes[i];

			pathIndices.push(BigInt(bit));
			pathElements.push(sibling);

			if (bit === 0) {
				current = p2(current, sibling);
			} else {
				current = p2(sibling, current);
			}
		}

		return {
			root: current,
			pathElements,
			pathIndices,
		};
	}

	function buildValidInput(privateKey, serverChallenge, clientEphemeralPubKey) {
		const publicKey = p1(privateKey);
		const leafCommitment = p1(publicKey);
		const merkle = buildMerklePathForSingleLeaf(
			leafCommitment,
			authorizedIndex,
			nLevels
		);

		return {
			privateKey: toSignal(privateKey),
			pathElements: merkle.pathElements.map(toSignal),
			pathIndices: merkle.pathIndices.map(toSignal),
			merkleRoot: toSignal(merkle.root),
			serverChallenge: toSignal(serverChallenge),
			clientEphemeralPubKey: toSignal(clientEphemeralPubKey),
		};
	}

	before(async () => {
		poseidon = await circomlibjs.buildPoseidon();
		F = poseidon.F;

		circuit = await wasm_tester(
			path.join(__dirname, "../../circuits/src/ShadowAuth.circom"),
			{
				include: [path.join(__dirname, "../../node_modules")],
			}
		);
	});

	it("generates a valid witness for an authorized user", async () => {
		const input = buildValidInput(123456789n, 111n, 222n);

		const witness = await circuit.calculateWitness(input, true);
		const expectedResponse = p2(
			BigInt(input.serverChallenge),
			BigInt(input.clientEphemeralPubKey)
		);

		await circuit.assertOut(witness, {
			responseHash: toSignal(expectedResponse),
		});
	});

	it("rejects witness generation with a wrong private key", async () => {
		const valid = buildValidInput(987654321n, 333n, 444n);
		const invalid = {
			...valid,
			privateKey: toSignal(BigInt(valid.privateKey) + 1n),
		};

		await assert.rejects(async () => {
			await circuit.calculateWitness(invalid, true);
		});
	});

	it("rejects witness generation with a wrong Merkle root", async () => {
		const valid = buildValidInput(246813579n, 555n, 666n);
		const invalid = {
			...valid,
			merkleRoot: toSignal(BigInt(valid.merkleRoot) + 1n),
		};

		await assert.rejects(async () => {
			await circuit.calculateWitness(invalid, true);
		});
	});

	it("binds responseHash to serverChallenge to prevent replay", async () => {
		const privateKey = 1122334455n;
		const ephemeral = 778899n;

		const inputA = buildValidInput(privateKey, 123n, ephemeral);
		const witnessA = await circuit.calculateWitness(inputA, true);
		const responseA = p2(BigInt(inputA.serverChallenge), BigInt(inputA.clientEphemeralPubKey));
		await circuit.assertOut(witnessA, { responseHash: toSignal(responseA) });

		const inputB = buildValidInput(privateKey, 124n, ephemeral);
		const witnessB = await circuit.calculateWitness(inputB, true);
		const responseB = p2(BigInt(inputB.serverChallenge), BigInt(inputB.clientEphemeralPubKey));
		await circuit.assertOut(witnessB, { responseHash: toSignal(responseB) });

		assert.notEqual(toSignal(responseA), toSignal(responseB));

		await assert.rejects(async () => {
			await circuit.assertOut(witnessB, { responseHash: toSignal(responseA) });
		});
	});
});
