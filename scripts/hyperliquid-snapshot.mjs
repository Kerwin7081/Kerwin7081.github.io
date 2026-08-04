import fs from "node:fs";

const ENDPOINT = "https://api.hyperliquid.xyz/info";
const DATA_PATH = "hyperliquid-weekend-stock-signal-20260803/data/latest.json";

const TARGETS = [
  "NVDA", "AMD", "MU", "TSM", "AVGO", "MSFT", "AMZN", "META", "GOOGL", "TSLA",
  "SMSN", "SKHX", "SNDK", "DRAM", "SP500", "XYZ100"
];

const CATEGORIES = {
  NVDA: "AI半导体", AMD: "AI半导体", MU: "存储", TSM: "晶圆代工", AVGO: "AI半导体",
  MSFT: "平台", AMZN: "平台", META: "平台", GOOGL: "平台", TSLA: "高波动",
  SMSN: "存储", SKHX: "存储", SNDK: "存储", DRAM: "存储", SP500: "指数", XYZ100: "指数"
};

async function post(payload) {
  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error(`Hyperliquid API ${response.status}`);
  return response.json();
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function coinName(item) {
  return typeof item === "string" ? item : item?.name;
}

function findMid(mids, symbol) {
  const direct = mids?.[symbol] ?? mids?.[`xyz:${symbol}`] ?? mids?.[`XYZ:${symbol}`];
  if (direct !== undefined) return numberOrNull(direct);
  const key = Object.keys(mids || {}).find((candidate) => candidate.endsWith(`:${symbol}`));
  return key ? numberOrNull(mids[key]) : null;
}

const [metaAndContexts, mids] = await Promise.all([
  post({ type: "metaAndAssetCtxs", dex: "xyz" }),
  post({ type: "allMids", dex: "xyz" })
]);

const [meta, contexts] = metaAndContexts;
const universe = meta?.universe || [];
const contextByCoin = new Map();
universe.forEach((item, index) => {
  const name = coinName(item);
  if (name && contexts?.[index]) contextByCoin.set(name, contexts[index]);
});

const assets = TARGETS.map((symbol) => {
  const context = contextByCoin.get(symbol) || {};
  const midPx = numberOrNull(context.midPx) ?? findMid(mids, symbol);
  if (midPx === null) return null;
  return {
    symbol,
    category: CATEGORIES[symbol] || "其他",
    midPx,
    markPx: numberOrNull(context.markPx),
    oraclePx: numberOrNull(context.oraclePx),
    funding: numberOrNull(context.funding),
    openInterest: numberOrNull(context.openInterest),
    prevDayPx: numberOrNull(context.prevDayPx)
  };
}).filter(Boolean);

if (assets.length < 8) throw new Error(`Too few xyz assets returned: ${assets.length}`);

const observedAtUtc = new Date().toISOString();
const observedAtHkt = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString().replace("Z", "+08:00");
const existing = fs.existsSync(DATA_PATH) ? JSON.parse(fs.readFileSync(DATA_PATH, "utf8")) : {};
const previousAssets = Array.isArray(existing.assets)
  ? existing.assets
  : (existing.history?.at(-1)?.assets || []);
const history = [...(Array.isArray(existing.history) ? existing.history : []), { observedAtUtc, assets }].slice(-200);

const next = {
  schema_version: 1,
  observedAtUtc,
  observedAtHkt,
  source: ENDPOINT,
  dex: "xyz",
  mode: "github_actions_4h",
  cadenceHours: 4,
  cashBaseline: existing.cashBaseline || {},
  assets,
  previousAssets: Object.fromEntries(previousAssets.map((asset) => [asset.symbol, asset])),
  history
};

fs.writeFileSync(DATA_PATH, `${JSON.stringify(next, null, 2)}\n`);
console.log(`Saved ${assets.length} assets at ${observedAtUtc}; history=${history.length}`);
