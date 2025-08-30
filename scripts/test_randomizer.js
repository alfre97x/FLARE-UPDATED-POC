/**
 * Test script for DataPurchaseRandomizer with Flare SRNG beacon (RandomNumberV2) on Coston2
 * New flow (beacon-based, no per-request):
 * 1) storeRandomness(userProvidedId) -> fetches SRNG.getRandomNumber() and stores it
 * 2) Read getRandomValue / getNormalizedRandomValue
 * 3) Read getRandomPriceVariation
 */

const { Web3 } = require('web3');
require('dotenv').config();

const RPC_URL = process.env.RPC_URL || 'https://coston2-api.flare.network/ext/C/rpc';
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const RANDOMIZER_ADDRESS = process.env.DATAPURCHASE_RANDOMIZER_ADDRESS;

if (!PRIVATE_KEY) {
  console.error('❌ PRIVATE_KEY not set in .env');
  process.exit(1);
}
if (!RANDOMIZER_ADDRESS) {
  console.error('❌ DATAPURCHASE_RANDOMIZER_ADDRESS not set in .env');
  process.exit(1);
}

// ABI aligned with beacon-based contract (storeRandomness/getters)
const randomizerABI = [
  // Events
  {
    anonymous: false,
    inputs: [
      { indexed: true, internalType: 'bytes32', name: 'userProvidedId', type: 'bytes32' },
      { indexed: false, internalType: 'uint256', name: 'randomValue', type: 'uint256' },
      { indexed: false, internalType: 'bool', name: 'isSecure', type: 'bool' },
      { indexed: false, internalType: 'uint256', name: 'randomTimestamp', type: 'uint256' }
    ],
    name: 'RandomnessStored',
    type: 'event'
  },

  // Functions
  {
    inputs: [{ internalType: 'bytes32', name: '_userProvidedId', type: 'bytes32' }],
    name: 'storeRandomness',
    outputs: [
      { internalType: 'uint256', name: 'randomValue', type: 'uint256' },
      { internalType: 'bool', name: 'isSecure', type: 'bool' },
      { internalType: 'uint256', name: 'randomTimestamp', type: 'uint256' }
    ],
    stateMutability: 'nonpayable',
    type: 'function'
  },
  {
    inputs: [{ internalType: 'bytes32', name: '_userProvidedId', type: 'bytes32' }],
    name: 'getRandomValue',
    outputs: [
      { internalType: 'uint256', name: 'randomValue', type: 'uint256' },
      { internalType: 'bool', name: 'fulfilled', type: 'bool' }
    ],
    stateMutability: 'view',
    type: 'function'
  },
  {
    inputs: [{ internalType: 'bytes32', name: '_userProvidedId', type: 'bytes32' }],
    name: 'getRandomnessMeta',
    outputs: [
      { internalType: 'bool', name: 'isSecure', type: 'bool' },
      { internalType: 'uint256', name: 'randomTimestamp', type: 'uint256' },
      { internalType: 'bool', name: 'fulfilled', type: 'bool' }
    ],
    stateMutability: 'view',
    type: 'function'
  },
  {
    inputs: [{ internalType: 'bytes32', name: '_userProvidedId', type: 'bytes32' }],
    name: 'getNormalizedRandomValue',
    outputs: [
      { internalType: 'uint256', name: 'normalizedValue', type: 'uint256' },
      { internalType: 'bool', name: 'fulfilled', type: 'bool' }
    ],
    stateMutability: 'view',
    type: 'function'
  },
  {
    inputs: [
      { internalType: 'bytes32', name: '_userProvidedId', type: 'bytes32' },
      { internalType: 'uint256', name: '_basePrice', type: 'uint256' },
      { internalType: 'uint256', name: '_variationPercent', type: 'uint256' }
    ],
    name: 'getRandomPriceVariation',
    outputs: [
      { internalType: 'uint256', name: 'finalPrice', type: 'uint256' },
      { internalType: 'int256', name: 'variationFactor', type: 'int256' },
      { internalType: 'bool', name: 'fulfilled', type: 'bool' }
    ],
    stateMutability: 'view',
    type: 'function'
  }
];

const web3 = new Web3(RPC_URL);

// Set up account from private key
const privateKey = PRIVATE_KEY.startsWith('0x') ? PRIVATE_KEY : `0x${PRIVATE_KEY}`;
const account = web3.eth.accounts.privateKeyToAccount(privateKey);
web3.eth.accounts.wallet.add(account);
const fromAddress = account.address;

// Contract instance
const randomizer = new web3.eth.Contract(randomizerABI, RANDOMIZER_ADDRESS);

function makeUserProvidedId() {
  return web3.utils.keccak256('srng-beacon-test-' + Date.now());
}

async function ensureContractPresent() {
  const code = await web3.eth.getCode(RANDOMIZER_ADDRESS);
  if (!code || code === '0x' || code === '0x0') {
    throw new Error('No contract deployed at DATAPURCHASE_RANDOMIZER_ADDRESS');
  }
}

async function sendTx(method, from, gasMult = 1.2) {
  const gas = await method.estimateGas({ from });
  const gasWithBuffer = Math.floor(Number(gas) * gasMult);
  return method.send({ from, gas: gasWithBuffer.toString() });
}

async function run() {
  console.log('=== DataPurchaseRandomizer SRNG Beacon Test (Coston2) ===');
  console.log(`🔗 RPC: ${RPC_URL}`);
  console.log(`👤 From: ${fromAddress}`);
  console.log(`🏷️ Contract: ${RANDOMIZER_ADDRESS}`);

  await ensureContractPresent();
  console.log('✅ Contract code found');

  const userProvidedId = makeUserProvidedId();
  console.log(`📝 userProvidedId: ${userProvidedId}`);

  const balance = await web3.eth.getBalance(fromAddress);
  console.log(`💰 Balance: ${web3.utils.fromWei(balance, 'ether')} FLR`);

  // Store randomness (fetch from SRNG beacon and persist)
  console.log('\n--- Storing randomness from SRNG beacon ---');
  try {
    const receipt = await sendTx(randomizer.methods.storeRandomness(userProvidedId), fromAddress);
    console.log(`✅ storeRandomness tx: ${receipt.transactionHash}`);
    if (receipt.events && receipt.events.RandomnessStored) {
      const ev = receipt.events.RandomnessStored.returnValues;
      console.log(`📥 Event RandomnessStored: randomValue=${ev.randomValue}, isSecure=${ev.isSecure}, ts=${ev.randomTimestamp}`);
    }
  } catch (err) {
    console.error('❌ storeRandomness failed:', err?.message || err);
    process.exit(1);
  }

  // Verify stored value
  console.log('\n--- Verifying stored randomness ---');
  const res = await randomizer.methods.getRandomValue(userProvidedId).call();
  console.log(`📊 randomValue: ${res.randomValue}`);
  console.log(`✅ fulfilled: ${res.fulfilled}`);

  const meta = await randomizer.methods.getRandomnessMeta(userProvidedId).call();
  console.log(`🔒 isSecure: ${meta.isSecure}`);
  console.log(`⏱️ randomTimestamp: ${meta.randomTimestamp}`);
  console.log(`✅ fulfilled: ${meta.fulfilled}`);

  const norm = await randomizer.methods.getNormalizedRandomValue(userProvidedId).call();
  console.log(`📊 normalizedValue (0-999): ${norm.normalizedValue}`);
  console.log(`✅ fulfilled: ${norm.fulfilled}`);

  console.log('\n--- Testing random price variation ---');
  const basePrice = web3.utils.toWei('10', 'ether');
  const variationPercent = 10;
  const price = await randomizer.methods.getRandomPriceVariation(userProvidedId, basePrice, variationPercent).call();
  console.log(`💰 finalPrice: ${web3.utils.fromWei(price.finalPrice, 'ether')} FLR`);
  console.log(`📈 variationFactor: ${price.variationFactor}%`);
  console.log(`✅ fulfilled: ${price.fulfilled}`);

  console.log('\n=== Test Complete ===');
}

run().then(() => process.exit(0)).catch((err) => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
