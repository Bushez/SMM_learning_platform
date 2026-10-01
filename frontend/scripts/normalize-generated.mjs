import { readdir, readFile, writeFile } from "node:fs/promises";

const generatedRoot = new URL("../src/shared/api/generated/", import.meta.url);

async function normalizeDirectory(directoryUrl) {
  for (const entry of await readdir(directoryUrl, { withFileTypes: true })) {
    const entryUrl = new URL(`${entry.name}${entry.isDirectory() ? "/" : ""}`, directoryUrl);
    if (entry.isDirectory()) {
      await normalizeDirectory(entryUrl);
      continue;
    }
    if (!entry.name.endsWith(".ts")) {
      continue;
    }
    const content = await readFile(entryUrl, "utf8");
    await writeFile(entryUrl, `${content.replace(/[\t ]*\r?\n+$/u, "")}\n`, "utf8");
  }
}

await normalizeDirectory(generatedRoot);
