import { ethers } from "hardhat";
import fs from "fs";

async function main() {
  const d = JSON.parse(fs.readFileSync("deployments/robinhood/addresses.json", "utf8"));
  const lp = await ethers.getContractAt("AlloyLaunchpad", d.AlloyLaunchpad);
  const count = await lp.coinCount();
  console.log(`Coins launched: ${count}`);
  for (let i = 0; i < Number(count); i++) {
    const coin = await lp.getCoin(i);
    console.log(`  [${i}] ${coin.name} (${coin.symbol}) — ${coin.addr}`);
  }
}
main().catch(console.error);
