import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const groupsPath = path.join(root, "course", "notebook-groups.json");
const packetsDir = path.join(root, "packets", "theories");
const notebookUrl = "https://notebooklm.google.com/";

function parseMode(argv) {
  if (argv.includes("--dry-run")) return "dry-run";
  if (argv.includes("--live")) return "live";
  throw new Error("Use --dry-run or --live");
}

function loadGroups() {
  const raw = fs.readFileSync(groupsPath, "utf8");
  return JSON.parse(raw);
}

function packetPathsFor(group) {
  return group.packet_slugs.map((slug) => path.join(packetsDir, `${slug}.md`));
}

function assertPacketFilesExist(files) {
  const missing = files.filter((file) => !fs.existsSync(file));
  if (missing.length > 0) {
    throw new Error(`Missing packet files:\n${missing.join("\n")}`);
  }
}

async function dryRun(groups) {
  for (const group of groups) {
    const files = packetPathsFor(group);
    assertPacketFilesExist(files);
    console.log(`[dry-run] ${group.group_id}: ${group.title}`);
    console.log(`[dry-run] audio=${group.audio_format}/${group.audio_length}/${group.audio_language}`);
    for (const file of files) console.log(`[dry-run] upload ${file}`);
  }
}

async function liveRun(groups) {
  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch (error) {
    console.error("Playwright is not installed. Run: npm install");
    process.exit(2);
  }

  const userDataDir = path.join(root, ".browser-profiles", "notebooklm");
  const context = await chromium.launchPersistentContext(userDataDir, { headless: false });
  const page = await context.newPage();
  await page.goto(notebookUrl, { waitUntil: "domcontentloaded" });

  console.log("If Google asks for login, complete it in the opened browser window.");
  console.log("Automation will pause for 60 seconds before checking the NotebookLM page.");
  await page.waitForTimeout(60000);

  for (const group of groups) {
    const files = packetPathsFor(group);
    assertPacketFilesExist(files);
    console.log(`[live] ready to create ${group.group_id}: ${group.title}`);
    console.log(`[live] packet files:\n${files.join("\n")}`);
    console.log("[live] Stop here for the first authenticated observation. Record stable UI labels before enabling clicks.");
  }

  await context.close();
}

const mode = parseMode(process.argv.slice(2));
const groups = loadGroups();

if (mode === "dry-run") {
  await dryRun(groups);
} else {
  await liveRun(groups);
}
