import { expect } from "chai";
import { ethers } from "hardhat";

describe("DistributionMath", function () {
  let lib: any;

  beforeEach(async function () {
    const F = await ethers.getContractFactory("DistributionMathHarness");
    lib = await F.deploy();
    await lib.waitForDeployment();
  });

  it("computes increment correctly", async function () {
    const supply = ethers.parseEther("1000000");
    const fees = ethers.parseEther("1000");
    const inc = await lib.computeIncrement(fees, supply);
    expect(inc).to.be.gt(0);
  });

  it("returns zero increment if supply is zero", async function () {
    const inc = await lib.computeIncrement(1000, 0);
    expect(inc).to.equal(0);
  });

  it("computes claimable proportionally", async function () {
    const balance = ethers.parseEther("100");
    const globalIndex = ethers.parseEther("10");
    const holderIndex = ethers.parseEther("5");
    const amount = await lib.claimable(balance, globalIndex, holderIndex);
    expect(amount).to.be.gt(0);
  });
});
