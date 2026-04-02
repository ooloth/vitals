import fs from "fs";
import path from "path";
import { parse } from "smol-toml";
import { VitalsConfigSchema, type VitalsConfig } from "./schema";

const CONFIG_PATH = path.join(process.cwd(), "vitals.config.toml");

export function loadConfig(): VitalsConfig {
  const raw = fs.readFileSync(CONFIG_PATH, "utf-8");
  const parsed = parse(raw);
  return VitalsConfigSchema.parse(parsed);
}
