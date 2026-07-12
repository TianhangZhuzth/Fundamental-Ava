import { ethers } from "hardhat";
import fs from "fs";

const INTERVAL = parseInt(process.env.KEEPER_INTERVAL || "3600") * 1000;

async function main() {
  const d = JSON.parse(fs.readFileSync("deployments/robinhood/addresses.json", "utf8"));
  const keeper = await ethers.getContractAt("AlloyKeeper", d.AlloyKeeper);

  async function tick() {
    try {
      const coins = await keeper.getPendingCoins();
      if (!coins.length) { console.log(`[${new Date().toISOString()}] idle`); return; }
      for (const coin of coins) {
        const tx = await keeper.distribute(coin, { gasLimit: 500_000 });
        await tx.wait();
        console.log(`distributed ${coin} — tx: ${tx.hash}`);
      }
    } catch (e) { console.error("tick error:", e); }
  }

  console.log(`Keeper running. interval=${INTERVAL/1000}s`);
  await tick();
  setInterval(tick, INTERVAL);
}
main().catch(console.error);






