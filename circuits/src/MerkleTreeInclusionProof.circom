pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/switcher.circom";

template MerkleTreeInclusionProof(nLevels) {
    signal input leaf;
    signal input pathElements[nLevels];
    signal input pathIndices[nLevels];

    signal output root;

    signal levelHashes[nLevels + 1];
    component switchers[nLevels];
    component hashers[nLevels];

    levelHashes[0] <== leaf;

    for (var i = 0; i < nLevels; i++) {
        pathIndices[i] * (pathIndices[i] - 1) === 0;

        switchers[i] = Switcher();
        switchers[i].sel <== pathIndices[i];
        switchers[i].L <== levelHashes[i];
        switchers[i].R <== pathElements[i];

        hashers[i] = Poseidon(2);
        hashers[i].inputs[0] <== switchers[i].outL;
        hashers[i].inputs[1] <== switchers[i].outR;

        levelHashes[i + 1] <== hashers[i].out;
    }

    root <== levelHashes[nLevels];
}



