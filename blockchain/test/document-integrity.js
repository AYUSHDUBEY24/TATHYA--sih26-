const { expect } = require("chai");
const { ethers } = require("hardhat");

const HASH_A = "0x" + "ab".repeat(32);
const HASH_B = "0x" + "cd".repeat(32);
const KEY = "DOC-0001:1";

describe("DocumentIntegrity", function () {
  let contract;

  beforeEach(async function () {
    const factory = await ethers.getContractFactory("DocumentIntegrity");
    contract = await factory.deploy();
    await contract.waitForDeployment();
  });

  it("rejects an empty document-version key", async function () {
    await expect(
      contract.registerDocumentHash("", HASH_A)
    ).to.be.revertedWith("empty document-version key");
  });

  it("rejects an empty document hash", async function () {
    await expect(
      contract.registerDocumentHash(KEY, ethers.ZeroHash)
    ).to.be.revertedWith("empty document hash");
  });

  it("rejects duplicate registration for the same key", async function () {
    await contract.registerDocumentHash(KEY, HASH_A);
    await expect(
      contract.registerDocumentHash(KEY, HASH_B)
    ).to.be.revertedWith("hash already registered for this key");
  });

  it("accepts a different key with a different hash", async function () {
    await contract.registerDocumentHash(KEY, HASH_A);
    await contract.registerDocumentHash("DOC-0001:2", HASH_B);
    expect(await contract.isAnchored(KEY)).to.equal(true);
    expect(await contract.isAnchored("DOC-0001:2")).to.equal(true);
  });

  it("emits a HashRegistered event", async function () {
    await expect(contract.registerDocumentHash(KEY, HASH_A)).to.emit(
      contract,
      "HashRegistered"
    );
  });

  it("stores and returns the anchored hash", async function () {
    await contract.registerDocumentHash(KEY, HASH_A);
    const [hash, timestamp] = await contract.getAnchor(KEY);
    expect(hash).to.equal(HASH_A);
    expect(timestamp).to.be.gt(0);
  });

  it("records a non-zero timestamp (block time)", async function () {
    await contract.registerDocumentHash(KEY, HASH_A);
    const [hash, timestamp] = await contract.getAnchor(KEY);
    expect(timestamp).to.be.greaterThan(0n);
  });

  it("isAnchored returns false for unknown keys", async function () {
    expect(await contract.isAnchored("unknown:1")).to.equal(false);
  });

  it("getAnchor reverts for unknown keys", async function () {
    await expect(contract.getAnchor("unknown:1")).to.be.revertedWith(
      "key not anchored"
    );
  });
});