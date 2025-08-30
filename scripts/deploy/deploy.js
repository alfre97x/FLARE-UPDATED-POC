async function main() {
  // Get the FDC verification address from environment variables
  const fdcVerificationAddress = process.env.FDC_VERIFICATION_ADDRESS;
  console.log("Using FDC verification address:", fdcVerificationAddress);
  
  // Get the contract factory
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contract with account:", deployer.address);
  
  const DataPurchase = await ethers.getContractFactory("DataPurchase");
  const contract = await DataPurchase.deploy(fdcVerificationAddress);
  
  console.log("Contract deployed to:", contract.address);
  console.log("Transaction hash:", contract.deployTransaction.hash);
  
  // Wait for the contract to be mined
  await contract.deployed();
  console.log("📡 Contract deployment confirmed!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
