// Deploy the DocumentIntegrity contract to the configured network.
//
//   npx hardhat run scripts/deploy.js --network localhost
//
// Prints the deployed contract address (plus a convenience line to copy into
// the backend .env as BLOCKCHAIN_CONTRACT_ADDRESS=...).

const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying DocumentIntegrity from account:", deployer.address);

  const factory = await ethers.getContractFactory("DocumentIntegrity");
  const contract = await factory.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("DocumentIntegrity deployed to:", address);
  console.log("");
  console.log("Copy this into your backend .env:");
  console.log(`BLOCKCHAIN_CONTRACT_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});