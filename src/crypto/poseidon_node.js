import {buildPoseidon} from 'circomlibjs'
async function main() {
    const poseidon = await buildPoseidon();
    
    const args = process.argv.slice(2);
    
    const res = poseidon(args);
    
    console.log(poseidon.F.toString(res));
}

main();