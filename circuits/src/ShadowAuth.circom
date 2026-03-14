pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";
include "MerkleTreeInclusionProof.circom";

template ShadowAuth(nLevels) {
	// Private witness inputs.
	signal input privateKey;
	signal input pathElements[nLevels];
	signal input pathIndices[nLevels];

	// Public inputs.
	signal input merkleRoot;
	signal input serverChallenge;
	signal input clientEphemeralPubKey;

	// Public output.
	signal output responseHash;

	signal publicKey;
	signal leafCommitment;

	component publicKeyHasher = Poseidon(1);
	publicKeyHasher.inputs[0] <== privateKey;
	publicKey <== publicKeyHasher.out;

	component leafCommitmentHasher = Poseidon(1);
	leafCommitmentHasher.inputs[0] <== publicKey;
	leafCommitment <== leafCommitmentHasher.out;

	component inclusion = MerkleTreeInclusionProof(nLevels);
	inclusion.leaf <== leafCommitment;

	for (var i = 0; i < nLevels; i++) {
		inclusion.pathElements[i] <== pathElements[i];
		inclusion.pathIndices[i] <== pathIndices[i];
	}

	inclusion.root === merkleRoot;

	component responseHasher = Poseidon(2);
	responseHasher.inputs[0] <== serverChallenge;
	responseHasher.inputs[1] <== clientEphemeralPubKey;
	responseHash <== responseHasher.out;
}

component main {public [merkleRoot, serverChallenge, clientEphemeralPubKey]} = ShadowAuth(20);
