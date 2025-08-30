/**
 * Deployment script for DataPurchaseRandomizer contract (Flare SRNG via Contract Registry)
 */

const { ethers } = require("hardhat");
require("dotenv").config();

async function main() {
  console.log("Deploying DataPurchaseRandomizer (Flare SRNG) contract...");

  // Get the contract factory
  const DataPurchaseRandomizer = await ethers.getContractFactory("DataPurchaseRandomizer");

  // Flare Contract Registry address for Coston2
  // Prefer env override if provided
  const registryAddress =
    process.env.FLARE_CONTRACT_REGISTRY || "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019";

  console.log(`Using Contract Registry: ${registryAddress}`);

  // Deploy the contract with the registry address
  const randomizer = await DataPurchaseRandomizer.deploy(registryAddress);
  await randomizer.deployed();

  console.log(`DataPurchaseRandomizer deployed to: ${randomizer.address}`);

  // Optional: Verify on block explorer (if supported for the network)
  try {
    console.log("Waiting for block confirmations...");
    await randomizer.deployTransaction.wait(5); // Wait for 5 confirmations
    console.log("Verifying contract on block explorer...");
    await hre.run("verify:verify", {
      address: randomizer.address,
      constructorArguments: [registryAddress],
    });
    console.log("Contract verified successfully");
  } catch (error) {
    console.warn("Verification step skipped or failed:", error.message);
  }

  // Update .env output
  console.log("\nAdd the following to your .env file:");
  console.log(`DATAPURCHASE_RANDOMIZER_ADDRESS=${randomizer.address}`);
  console.log(`FLARE_CONTRACT_REGISTRY=${registryAddress}`);
}

// Execute the deployment
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
