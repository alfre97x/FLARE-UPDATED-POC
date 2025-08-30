require("@nomiclabs/hardhat-ethers");
require("dotenv").config();

module.exports = {
  networks: {
    coston2: {
      url: process.env.RPC_URL,
      accounts: [process.env.PRIVATE_KEY]
    }
  },
  solidity: "0.8.19",
};
