const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

test("landing page mentions brand", () => {
  const page = fs.readFileSync(path.join(__dirname, "..", "app", "page.tsx"), "utf8");
  assert.match(page, /REVERSEFORGE AI/);
});

test("api client has tenant-sensitive endpoints", () => {
  const api = fs.readFileSync(path.join(__dirname, "..", "lib", "api.ts"), "utf8");
  assert.match(api, /analysis-runs/);
  assert.match(api, /reviewClaim/);
});
