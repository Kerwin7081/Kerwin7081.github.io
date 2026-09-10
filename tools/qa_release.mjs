#!/usr/bin/env node

/**
 * Release-gate checks for the static EnyaClawd site.
 *
 * This intentionally uses only Node's standard library so the deploy job can
 * run it before uploading the GitHub Pages artifact.
 */

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";

const ROOT = resolve(process.cwd());
const BASE_URL = "https://enyaclawd.com";
const IGNORED_DIRECTORIES = new Set([
  ".git",
  ".github",
  "preview",
  "previews",
  "publish",
  "staging",
]);
const REQUIRED_FILES = [
  "index.html",
  "registry.json",
  "sitemap.xml",
  "robots.txt",
  "CNAME",
  "assets/enya-design-system-v1.css",
  "assets/enya-reader-v1.css",
  "assets/kerwin-system-v2.css",
];
const VALID_AXES = new Set([
  "physical-infrastructure",
  "compute-chain",
  "agent-economy",
  "capital-macro",
  "frontier-infrastructure",
]);
const VALID_CONTENT_TYPES = new Set([
  "earnings",
  "earnings-deep-dive",
  "deep-dive",
  "brief",
  "interactive",
  "tracker",
]);
const PUBLIC_CORE_ROUTES = [
  "/",
  "/library/",
  "/map/",
  "/method/",
  "/models/",
  "/series/",
  "/earnings/",
  "/404.html",
];

const errors = [];
const warnings = [];

function fail(message) {
  errors.push(message);
}

function warn(message) {
  warnings.push(message);
}

function readText(relativePath) {
  try {
    return readFileSync(join(ROOT, relativePath), "utf8");
  } catch (error) {
    fail(`cannot read ${relativePath}: ${error.message}`);
    return "";
  }
}

function discoverFiles(directory, predicate, result = []) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && IGNORED_DIRECTORIES.has(entry.name)) continue;
    const absolutePath = join(directory, entry.name);
    if (entry.isDirectory()) {
      discoverFiles(absolutePath, predicate, result);
    } else if (predicate(absolutePath)) {
      result.push(absolutePath);
    }
  }
  return result;
}

function normalizeRoute(value) {
  let route = String(value || "/").trim();
  if (!route.startsWith("/")) route = `/${route}`;
  return route || "/";
}

function routeToFile(route) {
  const cleanRoute = normalizeRoute(route).split(/[?#]/, 1)[0] || "/";
  if (cleanRoute === "/") return join(ROOT, "index.html");
  const relativeRoute = cleanRoute.replace(/^\/+/, "");
  const direct = join(ROOT, relativeRoute);
  if (relativeRoute.endsWith("/")) return join(direct, "index.html");
  if (existsSync(direct) && statSync(direct).isDirectory()) {
    return join(direct, "index.html");
  }
  if (existsSync(direct)) return direct;
  if (!relativeRoute.includes(".")) return join(direct, "index.html");
  return direct;
}

function decodeXml(value) {
  return value
    .replaceAll("&amp;", "&")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"')
    .replaceAll("&apos;", "'");
}

function stripUrl(value) {
  return value.trim().split(/[?#]/, 1)[0];
}

function checkRequiredFiles() {
  for (const file of REQUIRED_FILES) {
    if (!existsSync(join(ROOT, file))) fail(`missing required file: ${file}`);
  }
  if (readText("CNAME").trim() !== "enyaclawd.com") {
    fail("CNAME must contain enyaclawd.com");
  }
}

function loadRegistry() {
  let registry;
  try {
    registry = JSON.parse(readText("registry.json"));
  } catch (error) {
    fail(`registry.json is not valid JSON: ${error.message}`);
    return [];
  }
  if (!Array.isArray(registry)) {
    fail("registry.json top-level value must be an array");
    return [];
  }

  const seenSlugs = new Set();
  const featuredRanks = new Map();
  for (const [index, item] of registry.entries()) {
    const label = item && item.slug ? item.slug : `entry#${index + 1}`;
    if (!item || typeof item !== "object") {
      fail(`${label}: registry entry must be an object`);
      continue;
    }
    if (!item.slug || typeof item.slug !== "string") {
      fail(`${label}: missing slug`);
    } else if (seenSlugs.has(item.slug)) {
      fail(`${label}: duplicate slug`);
    } else {
      seenSlugs.add(item.slug);
    }
    if (item.homepage_approved !== true) continue;

    for (const field of [
      "title",
      "date",
      "deck",
      "tag",
      "published_at",
      "axis",
      "content_type",
    ]) {
      if (!item[field]) fail(`${label}: missing ${field}`);
    }
    if (!VALID_AXES.has(item.axis)) fail(`${label}: invalid axis`);
    if (!VALID_CONTENT_TYPES.has(item.content_type)) {
      fail(`${label}: invalid content_type`);
    }
    const rank = item.featured_rank;
    if (rank !== undefined) {
      if (![1, 2, 3].includes(rank)) {
        fail(`${label}: featured_rank must be 1, 2 or 3`);
      } else if (featuredRanks.has(rank)) {
        warn(
          `${label}: featured_rank ${rank} is also used by ${featuredRanks.get(rank)}; ` +
            "homepage ordering will use publication time as the tie-breaker",
        );
      } else {
        featuredRanks.set(rank, label);
      }
    }

    const route = normalizeRoute(item.path || `/${item.slug}/`);
    if (!existsSync(routeToFile(route))) {
      fail(`${label}: public route does not exist: ${route}`);
    }
  }
  return registry;
}

function checkSitemap(registry) {
  const sitemap = readText("sitemap.xml");
  const locations = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/gi)].map((match) =>
    decodeXml(match[1]),
  );
  if (!locations.length) {
    fail("sitemap.xml contains no <loc> entries");
    return;
  }
  if (new Set(locations).size !== locations.length) {
    fail("sitemap.xml contains duplicate URLs");
  }
  const approvedRoutes = registry
    .filter((item) => item && item.homepage_approved === true)
    .map((item) => `${BASE_URL}${normalizeRoute(item.path || `/${item.slug}/`)}`);
  const expected = new Set([`${BASE_URL}/`, ...approvedRoutes]);
  const actual = new Set(locations);
  for (const url of expected) {
    if (!actual.has(url)) fail(`sitemap missing registry route: ${url}`);
  }
  for (const url of actual) {
    if (!expected.has(url)) fail(`sitemap contains unregistered route: ${url}`);
  }
}

function checkHtmlPage(pagePath) {
  const html = readFileSync(pagePath, "utf8");
  const relativePage = relative(ROOT, pagePath).split(sep).join("/");
  const lower = html.toLowerCase();
  if (!/<title\b[^>]*>[\s\S]*?<\/title>/i.test(html)) {
    fail(`${relativePage}: missing <title>`);
  }
  if (!/<meta\b[^>]+name=["']viewport["']/i.test(html)) {
    fail(`${relativePage}: missing viewport meta`);
  }
  if (!/<meta\b[^>]+name=["']description["']/i.test(html)) {
    fail(`${relativePage}: missing meta description`);
  }

  const references = [
    ...html.matchAll(/\b(?:href|src)\s*=\s*["']([^"']+)["']/gi),
  ].map((match) => match[1]);
  for (const reference of references) {
    const value = stripUrl(reference);
    if (
      !value ||
      value.startsWith("#") ||
      value.startsWith("//") ||
      value.startsWith("/") && value.startsWith("//") ||
      /^(?:[a-z][a-z0-9+.-]*:)/i.test(value)
    ) {
      continue;
    }
    let decoded;
    try {
      decoded = decodeURIComponent(value);
    } catch {
      fail(`${relativePage}: malformed encoded local reference: ${reference}`);
      continue;
    }
    const candidate = decoded.startsWith("/")
      ? routeToFile(decoded)
      : resolve(pagePath, "..", decoded);
    if (!existsSync(candidate)) {
      fail(`${relativePage}: missing local reference: ${reference}`);
    }
  }

  const insecureReferences = references.filter((reference) => /^http:\/\//i.test(reference));
  if (insecureReferences.length) {
    warn(
      `${relativePage}: contains ${insecureReferences.length} insecure href/src reference(s); verify they are intentional`,
    );
  }
}

function publicPageFiles(registry) {
  const routes = [
    ...PUBLIC_CORE_ROUTES,
    ...registry
      .filter((item) => item && item.homepage_approved === true)
      .map((item) => item.path || `/${item.slug}/`),
  ];
  return new Set(
    routes
      .map((route) => routeToFile(route))
      .filter((file) => existsSync(file)),
  );
}

function checkJavaScriptSyntax() {
  const jsFiles = discoverFiles(ROOT, (file) => file.endsWith(".js"));
  for (const file of jsFiles) {
    const result = spawnSync(process.execPath, ["--check", file], {
      encoding: "utf8",
    });
    if (result.status !== 0) {
      const relativeFile = relative(ROOT, file).split(sep).join("/");
      fail(`${relativeFile}: JavaScript syntax check failed\n${result.stderr.trim()}`);
    }
  }
  if (!jsFiles.length) warn("no JavaScript files found for syntax checking");
}

function checkCssSyntaxSurface() {
  for (const file of [
    "assets/enya-design-system-v1.css",
    "assets/enya-reader-v1.css",
    "assets/kerwin-system-v2.css",
  ]) {
    const css = readText(file);
    let depth = 0;
    for (const character of css) {
      if (character === "{") depth += 1;
      if (character === "}") depth -= 1;
      if (depth < 0) break;
    }
    if (depth !== 0) fail(`${file}: unbalanced CSS braces`);
  }
}

checkRequiredFiles();
const registry = loadRegistry();
checkSitemap(registry);
const allHtmlPages = discoverFiles(ROOT, (file) => file.endsWith("index.html"));
const publicFiles = publicPageFiles(registry);
for (const page of publicFiles) checkHtmlPage(page);
checkJavaScriptSyntax();
checkCssSyntaxSurface();

if (warnings.length) {
  for (const message of warnings) console.log(`WARN  ${message}`);
}
if (errors.length) {
  for (const message of errors) console.error(`FAIL  ${message}`);
  console.error(`Release QA failed: ${errors.length} error(s), ${warnings.length} warning(s).`);
  process.exit(1);
}
console.log(
  `Release QA passed: ${publicFiles.size} catalog page(s) checked ` +
    `(${allHtmlPages.length} production entrypoint(s) discovered), ` +
    `${registry.length} registry record(s), ${warnings.length} warning(s).`,
);

