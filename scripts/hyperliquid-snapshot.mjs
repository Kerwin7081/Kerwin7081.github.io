import fs from "node:fs";

const ENDPOINT = "https://api.hyperliquid.xyz/info";
const YAHOO_ENDPOINT = "https://query2.finance.yahoo.com/v8/finance/chart/";
const DATA_PATH = "hyperliquid-weekend-stock-signal-20260803/data/latest.json";

const TARGETS = [
  "NVDA", "AMD", "MU", "TSM", "AVGO", "MSFT", "AMZN", "META", "GOOGL", "TSLA",
  "SMSN", "SKHX", "SNDK", "DRAM", "KIOXIA", "CXMT", "UNITREE", "SP500", "XYZ100"
];

const KOREAN_TARGETS = { SMSN: "005930.KS", SKHX: "000660.KS" };
const US_STOCK_TARGETS = {
  NVDA: "NVDA", AMD: "AMD", MU: "MU", TSM: "TSM", AVGO: "AVGO",
  MSFT: "MSFT", AMZN: "AMZN", META: "META", GOOGL: "GOOGL", TSLA: "TSLA",
  SNDK: "SNDK"
};
const ETF_TARGETS = { DRAM: "DRAM" };
const INDEX_TARGETS = { SP500: "^GSPC", XYZ100: "^NDX" };

const CATEGORIES = {
  NVDA: "AI半导体", AMD: "AI半导体", MU: "存储", TSM: "晶圆代工", AVGO: "AI半导体",
  MSFT: "平台", AMZN: "平台", META: "平台", GOOGL: "平台", TSLA: "高波动",
  SMSN: "存储", SKHX: "存储", SNDK: "存储", DRAM: "存储", KIOXIA: "存储", CXMT: "存储", UNITREE: "扩展观察", SP500: "指数", XYZ100: "指数"
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

async function collectAdditionalBaselines() {
  let fx = [];
  try {
    fx = await yahooChart("KRW=X");
  } catch (error) {
    console.warn(`USD/KRW baseline unavailable: ${error.message}`);
  }
  const baselines = {};
  for (const [symbol, ticker] of Object.entries(US_STOCK_TARGETS)) {
    try {
      const close = lastFriday(await yahooChart(ticker));
      if (!close) continue;
      baselines[symbol] = {
        close: Number(close.close.toFixed(4)),
        date: close.date,
        source: `Yahoo Finance · ${ticker} cash close`,
        comparable: true,
        currency: "USD"
      };
    } catch (error) {
      console.warn(`US stock baseline skipped for ${symbol}: ${error.message}`);
    }
  }
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
  for (const [symbol, ticker] of Object.entries(ETF_TARGETS)) {
    try {
      const close = lastFriday(await yahooChart(ticker));
      if (!close) continue;
      baselines[symbol] = {
        close: Number(close.close.toFixed(4)),
        date: close.date,
        source: `Yahoo Finance · ${ticker} (Roundhill Memory ETF)`,
        comparable: true,
        currency: "USD",
        instrument: "Roundhill Memory ETF"
      };
    } catch (error) {
      console.warn(`ETF baseline skipped for ${symbol}: ${error.message}`);
    }
  }
  for (const [symbol, ticker] of Object.entries(INDEX_TARGETS)) {
    try {
      const close = lastFriday(await yahooChart(ticker));
      if (!close) continue;
      baselines[symbol] = {
        close: Number(close.close.toFixed(4)),
        date: close.date,
        source: `Yahoo Finance · ${ticker} cash index close`,
        comparable: true,
        currency: "USD",
        instrument: symbol === "SP500" ? "S&P 500 Index" : "Nasdaq 100 Index"
      };
    } catch (error) {
      console.warn(`Index baseline skipped for ${symbol}: ${error.message}`);
    }
  }
  return baselines;
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

let additionalBaselines = {};
try {
  additionalBaselines = await collectAdditionalBaselines();
} catch (error) {
  console.warn(`Additional cash baselines unavailable: ${error.message}`);
}

const cashBaseline = { ...(existing.cashBaseline || {}), ...additionalBaselines };
if (cashBaseline.DRAM?.proxy || cashBaseline.DRAM?.comparable === false) delete cashBaseline.DRAM;

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
  history
};

fs.writeFileSync(DATA_PATH, `${JSON.stringify(next, null, 2)}\n`);
console.log(`Saved ${assets.length} assets at ${observedAtUtc}; history=${history.length}; cash baselines=${Object.keys(additionalBaselines).join(",") || "none"}; DRAM=${cashBaseline.DRAM?.close ?? "none"}`);
