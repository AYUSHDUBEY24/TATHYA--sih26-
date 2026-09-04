# Hardhat local Ethereum node for the SIH26190 prototype.
# Builds inside Linux so the platform-specific Hardhat binaries match the
# container OS (mounting host node_modules across OSes breaks native modules).
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 8545

CMD ["npx", "hardhat", "node", "--hostname", "0.0.0.0", "--port", "8545"]
