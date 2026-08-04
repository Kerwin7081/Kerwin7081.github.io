import fs from "node:fs";

const ENDPOINT = "https://api.hyperliquid.xyz/info";
const YAHOO_ENDPOINT = "https://query2.finance.yahoo.com/v8/finance/chart/";
const DRAM_ENDPOINT = "https://www.dramexchange.com/";
const DATA_PATH = "hyperliquid-weekend-stock-signal-20260803/data/latest.json";

const TARGETS = [
  "NVDA", "AMD", "MU", "TSM", "AVGO", "MSFT", "AMZN", "META", "GOOGL", "TSLA",
  "SMSN", "SKHX", "SNDK", "DRAM", "SP500", "XYZ100"
];

const KOREAN_TARGETS = { SMSN: "005930.KS", SKHX: "000660.KS" };

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

async function yahooChart(symbol) {
  const url = `${YAHOO_ENDPOINT}${encodeURIComponent(symbol)}?range=14d&interval=1d`;
  const response = await fetch(url, { headers: { "user-agent": "Mozilla/5.0 KerwinResearch/1.0" } });
  if (!response.ok) throw new Error(`Yahoo Finance ${symbol} ${response.status}`);
  const payload = await response.json();
  const result = payload?.chart?.result?.[0];
  if (!result) throw new Error(`Yahoo Finance empty result for ${symbol}`);
  const quote = result.indicators?.quote?.[0] || {};
  return (result.timestamp || []).map((timestamp, index) => ({
    timestamp,
    date: dateKey(timestamp, result.meta?.exchangeTimezoneName || "UTC"),
    close: numberOrNull(quote.close?.[index])
  })).filter((point) => point.close !== null);
}

async function dramSpot() {
  const response = await fetch(DRAM_ENDPOINT, {
    headers: { "user-agent": "Mozilla/5.0 KerwinResearch/1.0" }
  });
  if (!response.ok) throw new Error(`DRAMeXchange ${response.status}`);
  const html = await response.text();
  const marker = "DDR5 16Gb (2Gx8) 4800/5600";
  const start = html.indexOf(marker);
  if (start < 0) throw new Error("DRAMeXchange DDR5 16Gb row not found");
  const snippet = html.slice(start, start + 3600);
  const values = [...snippet.matchAll(/<td[^>]*class="tab_tr_gray"[^>]*>\s*([0-9.]+)\s*<\/td>/g)]
    .map((match) => Number(match[1]))
    .filter(Number.isFinite);
  if (values.length < 5) throw new Error("DRAMeXchange session average not found");
  const update = html.match(/Last Update:\s*([^<]+)/i)?.[1]?.replace(/\s+/g, " ").trim() || null;
  return {
    close: values[4],
    label: "DDR5 16Gb (2Gx8) 4800/5600",
    update
  };
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function dateKey(timestamp, timeZone) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone, year: "numeric", month: "2-digit", day: "2-digit"
  }).format(new Date(timestamp * 1000));
}

function isFriday(date) {
  return new Date(`${date}T12:00:00Z`).getUTCDay() === 5;
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

function lastFriday(points) {
  return points.filter((point) => isFriday(point.date)).at(-1) || points.at(-1) || null;
}

function nearestFx(points, date) {
  return points.filter((point) => point.date <= date).at(-1) || points.at(-1) || null;
}

async function collectKoreanBaselines() {
  const fx = await yahooChart("KRW=X");
  const baselines = {};
  for (const [symbol, ticker] of Object.entries(KOREAN_TARGETS)) {
    try {
      const local = lastFriday(await yahooChart(ticker));
      const rate = local ? nearestFx(fx, local.date) : null;
      if (!local || !rate || !rate.close) continue;
      baselines[symbol] = {
        close: Number((local.close / rate.close).toFixed(4)),
        date: local.date,
        source: `Yahoo Finance · ${ticker} ÷ KRW=X`,
        comparable: true,
        nativeClose: local.close,
        fx: rate.close,
        currency: "USD"
      };
    } catch (error) {
      console.warn(`Korean baseline skipped for ${symbol}: ${error.message}`);
    }
  }
  return baselines;
}

function dramFridayBaseline(history) {
  const friday = history.filter((point) => point.observedDate && isFriday(point.observedDate)).at(-1);
  return friday ? {
    close: friday.close,
    date: friday.observedDate,
    source: `DRAMeXchange · ${friday.label} session average`,
    comparable: false,
    proxy: true,
    proxyLabel: friday.label
  } : null;
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
const observedDate = observedAtHkt.slice(0, 10);
const existing = fs.existsSync(DATA_PATH) ? JSON.parse(fs.readFileSync(DATA_PATH, "utf8")) : {};
const previousAssets = Array.isArray(existing.assets)
  ? existing.assets
  : (existing.history?.at(-1)?.assets || []);
const history = [...(Array.isArray(existing.history) ? existing.history : []), { observedAtUtc, assets }].slice(-200);

let koreanBaselines = {};
try {
  koreanBaselines = await collectKoreanBaselines();
} catch (error) {
  console.warn(`Korean baselines unavailable: ${error.message}`);
}

let dramCurrent = null;
try {
  dramCurrent = await dramSpot();
} catch (error) {
  console.warn(`DRAMeXchange unavailable: ${error.message}`);
}

const dramHistory = [...(Array.isArray(existing.dramHistory) ? existing.dramHistory : [])];
if (dramCurrent) {
  dramHistory.push({
    observedAtUtc,
    observedAtHkt,
    observedDate,
    close: dramCurrent.close,
    label: dramCurrent.label,
    update: dramCurrent.update
  });
}
const trimmedDramHistory = dramHistory.slice(-200);
const cashBaseline = { ...(existing.cashBaseline || {}), ...koreanBaselines };
const fridayDram = dramFridayBaseline(trimmedDramHistory);
if (fridayDram) cashBaseline.DRAM = fridayDram;

const next = {
  schema_version: 1,
  observedAtUtc,
  observedAtHkt,
  source: ENDPOINT,
  dex: "xyz",
  mode: "github_actions_4h",
  cadenceHours: 4,
  cashBaseline,
  assets,
  previousAssets: Object.fromEntries(previousAssets.map((asset) => [asset.symbol, asset])),
  history,
  dramHistory: trimmedDramHistory,
  currentDramSpot: dramCurrent
};

fs.writeFileSync(DATA_PATH, `${JSON.stringify(next, null, 2)}\n`);
console.log(`Saved ${assets.length} assets at ${observedAtUtc}; history=${history.length}; Korean baselines=${Object.keys(koreanBaselines).join(",") || "none"}; DRAM=${dramCurrent?.close ?? "none"}`);
