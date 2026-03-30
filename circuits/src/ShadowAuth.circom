pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";
include "MerkleTreeInclusionProof.circom";

template ShadowAuth(nLevels) {
    signal input privateKey;
    signal input pathElements[nLevels];
    signal input pathIndices[nLevels];

    signal input merkleRoot;
    signal input serverChallenge;
    signal input clientEphemeralPubKey;

    signal output responseHash;
    signal output nullifier;

    component pubKeyHasher = Poseidon(1);
    pubKeyHasher.inputs[0] <== privateKey;
    signal publicKey <== pubKeyHasher.out;

    component nullifierHasher = Poseidon(1);
    nullifierHasher.inputs[0] <== publicKey;
    nullifier <== nullifierHasher.out;

    component inclusion = MerkleTreeInclusionProof(nLevels);
    inclusion.leaf <== nullifier;
    for (var i = 0; i < nLevels; i++) {
        inclusion.pathElements[i] <== pathElements[i];
        inclusion.pathIndices[i] <== pathIndices[i];
    }

    inclusion.root === merkleRoot;

    component responseHasher = Poseidon(3);
    responseHasher.inputs[0] <== serverChallenge;
    responseHasher.inputs[1] <== clientEphemeralPubKey;
    responseHasher.inputs[2] <== privateKey;
    
    responseHash <== responseHasher.out;
}

component main {public [merkleRoot, serverChallenge, clientEphemeralPubKey]} = ShadowAuth(20);
