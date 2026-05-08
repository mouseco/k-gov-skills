#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");


const DEFAULT_ENV_FILE = process.env.KGOV_ENV_FILE || "C:\\Users\\mouse\\.openclaw\\.env";

function loadDotEnvFile(filePath = DEFAULT_ENV_FILE) {
  if (!filePath || !fs.existsSync(filePath)) return false;
  const text = fs.readFileSync(filePath, "utf8");
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const index = line.indexOf("=");
    const key = line.slice(0, index).trim();
    let value = line.slice(index + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (key && process.env[key] == null) process.env[key] = value;
  }
  return true;
}

loadDotEnvFile();

function printHelp() {
  process.stdout.write(`transport receipt collector

Commands:
  node collect_transport_receipts.cjs --help
  node collect_transport_receipts.cjs chrome-command --provider hipass [--profile-dir DIR] [--debugging-port PORT] [--chrome-path PATH]
  node collect_transport_receipts.cjs list --provider hipass --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--cdp-url URL] [--page-size N] [--auth-mode idpw|session] [--headless]
  node collect_transport_receipts.cjs collect --provider hipass --start-date YYYY-MM-DD --end-date YYYY-MM-DD --row-index N [--cdp-url URL] [--output-dir DIR] [--auth-mode idpw|session] [--headless]

Output:
  collect writes one PDF and one PNG for the selected receipt row.

Notes:
  - Default auth mode is idpw. The script loads C:\\Users\\mouse\\.openclaw\\.env by default.
  - Expected keys: KGOV_HIPASS_ID and KGOV_HIPASS_PW.
  - Use --auth-mode session to reuse a browser session after signing in manually.
  - Use --headless for v2 no-window ID/PW runs. Headless does not support manual session login.
  - If extra identity checks appear, stop and let the user finish them in the browser.
  - JPG is intentionally not produced.
`);
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith("--")) {
      args._.push(value);
      continue;
    }
    const key = value.slice(2).replace(/-([a-z])/g, (_, char) => char.toUpperCase());
    const next = argv[index + 1];
    args[key] = next && !next.startsWith("--") ? argv[++index] : true;
  }
  return args;
}

function isTruthy(value) {
  return value === true || value === "true" || value === "1" || value === "yes" || value === "on";
}

function requireArg(args, key, label) {
  if (!args[key]) {
    throw new Error(`Missing required --${label || key}`);
  }
  return args[key];
}

function assertProvider(args) {
  const provider = args.provider || "hipass";
  if (provider !== "hipass") {
    throw new Error(`Unsupported provider for this version: ${provider}`);
  }
}

function shellQuote(value) {
  return `"${String(value).replace(/"/g, '\\"')}"`;
}

function defaultChromePath() {
  const candidates = [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || candidates[0];
}

function defaultProfileDir() {
  return path.join(os.homedir(), ".cache", "k-gov-skills", "hipass-chrome");
}

function buildChromeCommand(args) {
  const chromePath = args.chromePath || defaultChromePath();
  const profileDir = args.profileDir || defaultProfileDir();
  const debuggingPort = Number(args.debuggingPort || 9222);
  return [
    shellQuote(chromePath),
    `--user-data-dir=${shellQuote(profileDir)}`,
    `--remote-debugging-port=${debuggingPort}`,
    "--no-first-run",
    "--no-default-browser-check",
    "https://www.hipass.co.kr/comm/lginpg.do",
  ].join(" ");
}


const BASE_URL = "https://www.hipass.co.kr";
const LOGIN_URL = `${BASE_URL}/comm/lginpg.do`;
const USAGE_HISTORY_INIT_URL = `${BASE_URL}/usepculr/InitUsePculrTabSearch.do`;
const USAGE_HISTORY_LIST_URL = `${BASE_URL}/usepculr/UsePculrTabSearchList.do`;
const RECEIPT_URL = `${BASE_URL}/usepculr/UsePculrReceiptPrint.do`;
const DETAIL_URL = `${BASE_URL}/usepculr/UsePculrTabSearchListDetail.do`;

const ROW_COLUMN_KEYS = [
  "rowNumber",
  "workDateTime",
  "cardNumberMasked",
  "cardAlias",
  "vehicleType",
  "inTollgateName",
  "outTollgateName",
  "laneType",
  "transactionAmount",
  "billDate",
  "category",
  "baseToll",
  "paidToll",
  "billedAmount",
];

function stripTags(value) {
  return String(value || "")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&#39;/gi, "'")
    .replace(/&quot;/gi, '"')
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeCompactDate(value, fieldName) {
  const digits = String(value || "").replace(/\D/g, "");
  if (digits.length !== 8) {
    throw new Error(`${fieldName} must be a YYYYMMDD-compatible date`);
  }
  return digits;
}

function toStringOrDefault(value, fallback) {
  return value == null || value === "" ? fallback : String(value);
}

function buildUsageHistoryQuery(options = {}) {
  const startDate = normalizeCompactDate(options.startDate, "startDate");
  const endDate = normalizeCompactDate(options.endDate, "endDate");
  const pageSize = Number(toStringOrDefault(options.pageSize, "30"));
  if (![10, 30, 50, 80, 100].includes(pageSize)) {
    throw new Error("pageSize must be one of 10, 30, 50, 80, 100");
  }
  if (startDate > endDate) {
    throw new Error("startDate must be on or before endDate");
  }
  return {
    card_kind: toStringOrDefault(options.cardKind, "all"),
    card_com: toStringOrDefault(options.cardCom ?? options.cardCompany, "all"),
    ecd_no: toStringOrDefault(options.ecdNo ?? options.encryptedCardNumber, "all"),
    sDate: startDate,
    eDate: endDate,
    date_type: toStringOrDefault(options.dateType, "work"),
    biz_type: toStringOrDefault(options.bizType, "on"),
    pageSize: String(pageSize),
    pageNo: toStringOrDefault(options.pageNo, "1"),
    order_type: toStringOrDefault(options.orderType, "desc"),
    order_item: toStringOrDefault(options.orderItem, "date"),
    receipt_time_type: toStringOrDefault(options.receiptTimeType, "display"),
    in_ic_nm: toStringOrDefault(options.inIcName, ""),
    out_ic_nm: toStringOrDefault(options.outIcName, ""),
    in_ic_code: toStringOrDefault(options.inIcCode, ""),
    out_ic_code: toStringOrDefault(options.outIcCode, ""),
    w: toStringOrDefault(options.width, "742"),
    h: toStringOrDefault(options.height, "436"),
    inc_vat: toStringOrDefault(options.incVat, "nodisplay"),
  };
}

function detectSessionState({ url = "", html = "" } = {}) {
  const normalizedUrl = String(url || "");
  const normalizedHtml = String(html || "");
  if (/\/comm\/lginpg\.do(?:\?|$)/.test(normalizedUrl)) {
    return { authenticated: false, requiresLogin: true, reason: "login_redirect", messageType: null };
  }
  const messageTypeMatch = normalizedHtml.match(/var\s+mgs_type\s*=\s*(\d+)/);
  const messageType = messageTypeMatch ? Number(messageTypeMatch[1]) : null;
  if (messageType === 11) return { authenticated: false, requiresLogin: true, reason: "login_required", messageType };
  if (messageType === 12) return { authenticated: false, requiresLogin: true, reason: "session_out", messageType };
  if (/\/comm\/lginpg\.do/.test(normalizedHtml) && /\uB85C\uADF8\uC778/.test(normalizedHtml)) {
    return { authenticated: false, requiresLogin: true, reason: "login_redirect", messageType };
  }
  return { authenticated: true, requiresLogin: false, reason: null, messageType };
}

function parseHiddenFields(html) {
  const fields = {};
  for (const match of String(html || "").matchAll(/<input\b[^>]*name="([^"]+)"[^>]*value="([^"]*)"[^>]*>/gi)) {
    fields[match[1]] = match[2];
  }
  return fields;
}

function extractBodyRows(html) {
  const tbodyMatch = String(html || "").match(/<tbody[^>]*>([\s\S]*?)<\/tbody>/i);
  if (!tbodyMatch) return [];
  return [...tbodyMatch[1].matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)].map((match) => match[0]);
}

function extractCells(rowHtml) {
  return [...String(rowHtml || "").matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/gi)].map((match) => stripTags(match[1]));
}

function parseFunctionArgs(onclick, functionName) {
  const match = String(onclick || "").match(new RegExp(`${functionName}\\(([^)]*)\\)`));
  if (!match) return [];
  return [...match[1].matchAll(/'([^']*)'|"([^"]*)"/g)].map((arg) => arg[1] || arg[2] || "");
}

function parseAmount(value) {
  const digits = String(value || "").replace(/[^\d]/g, "");
  return digits ? Number(digits) : 0;
}

function parseReceiptAction(rowHtml) {
  const candidatePattern = /<(a|button|input)\b([^>]*)>([\s\S]*?)<\/\1>|<input\b([^>]*)\/>/gi;
  const candidates = [];
  for (const match of String(rowHtml || "").matchAll(candidatePattern)) {
    const controlType = (match[1] || "input").toLowerCase();
    const attrs = (match[2] || match[4] || "").trim();
    const inlineText = controlType === "input" ? "" : stripTags(match[3] || "");
    const valueMatch = attrs.match(/\bvalue\s*=\s*"([^"]*)"|\bvalue\s*=\s*'([^']*)'/i);
    const classMatch = attrs.match(/\bclass\s*=\s*"([^"]*)"|\bclass\s*=\s*'([^']*)'/i);
    const onclickMatch = attrs.match(/\bonclick\s*=\s*"([^"]*)"|\bonclick\s*=\s*'([^']*)'/i);
    const label = stripTags(inlineText || valueMatch?.[1] || valueMatch?.[2] || "");
    candidates.push({ controlType, className: classMatch?.[1] || classMatch?.[2] || "", onclick: onclickMatch?.[1] || onclickMatch?.[2] || "", label });
  }
  return candidates.find((candidate) => /\uC601\uC218\uC99D|\uCD9C\uB825/.test(candidate.label) || /receipt/i.test(candidate.className)) || null;
}

function buildDetailRequest(detailRequest) {
  return {
    card_kind: detailRequest.card_kind,
    work_dates: detailRequest.work_dates,
    tolof_cd: detailRequest.tolof_cd,
    work_no: detailRequest.work_no,
    vhclProsNo: detailRequest.vhclProsNo,
  };
}

function buildReceiptRequest(receiptRequest, options = {}) {
  return {
    ...buildDetailRequest(receiptRequest),
    receipt_time_type: toStringOrDefault(receiptRequest.receipt_time_type, "display"),
    inc_vat: options.includeVat ? "display" : toStringOrDefault(receiptRequest.inc_vat, "nodisplay"),
    w: toStringOrDefault(receiptRequest.w, "742"),
    h: toStringOrDefault(receiptRequest.h, "436"),
  };
}

function parseUsageHistoryList(html) {
  const state = detectSessionState({ html });
  const hiddenFields = parseHiddenFields(html);
  const rows = extractBodyRows(html);
  const normalizedRows = rows.map((rowHtml, index) => {
    const cells = extractCells(rowHtml);
    if (cells.length < 10) return null;
    const hasSelectColumn = cells.length >= 11 && /^\d+$/.test(cells[1]);
    const offset = hasSelectColumn ? 1 : 0;
    const detailAction = [...String(rowHtml || "").matchAll(/<a\b[^>]*onclick="([^"]*viewDetail[^"]*)"[^>]*>/gi)][0]?.[1] || "";
    const receiptAction = [...String(rowHtml || "").matchAll(/<a\b[^>]*onclick="([^"]*printReceipt[^"]*)"[^>]*>/gi)][0]?.[1] || "";
    const detailArgs = parseFunctionArgs(detailAction, "viewDetail");
    const receiptArgs = parseFunctionArgs(receiptAction, "printReceipt");
    const row = {
      rowNumber: Number(cells[offset + 0]),
      workDateTime: cells[offset + 1],
      hipassCard: cells[offset + 2],
      cardAlias: cells[offset + 3],
      vehicleClass: cells[offset + 4],
      entryOffice: cells[offset + 5],
      exitOffice: cells[offset + 6],
      lane: cells[offset + 7],
      transactionAmount: parseAmount(cells[offset + 8]),
      billingDate: cells[offset + 9],
      chargeType: cells[offset + 10] || "",
      baseToll: parseAmount(cells[offset + 11]),
      payableToll: parseAmount(cells[offset + 12]),
      billAmount: parseAmount(cells[offset + 13] || cells[offset + 8]),
      detailRequest: buildDetailRequest({ card_kind: detailArgs[0], work_dates: detailArgs[1], tolof_cd: detailArgs[2], work_no: detailArgs[3], vhclProsNo: detailArgs[4] }),
      receiptRequest: buildReceiptRequest({ card_kind: receiptArgs[0], work_dates: receiptArgs[1], tolof_cd: receiptArgs[2], work_no: receiptArgs[3], vhclProsNo: receiptArgs[4], receipt_time_type: receiptArgs[5], inc_vat: receiptArgs[6], w: hiddenFields.w || "742", h: hiddenFields.h || "436" }),
    };
    return { row, item: {
      rowIndex: index + 1, rowNumber: row.rowNumber, workDateTime: row.workDateTime, cardNumberMasked: row.hipassCard,
      cardAlias: row.cardAlias, vehicleType: row.vehicleClass, inTollgateName: row.entryOffice, outTollgateName: row.exitOffice,
      laneType: row.lane, transactionAmount: `${row.transactionAmount.toLocaleString("en-US")}\uC6D0`, billDate: row.billingDate,
      category: row.chargeType, baseToll: `${row.baseToll.toLocaleString("en-US")}\uC6D0`, paidToll: `${row.payableToll.toLocaleString("en-US")}\uC6D0`,
      billedAmount: `${row.billAmount.toLocaleString("en-US")}\uC6D0`, rawHtml: rowHtml, receiptAction: parseReceiptAction(rowHtml),
      detailRequest: row.detailRequest, receiptRequest: row.receiptRequest,
    }};
  }).filter(Boolean);
  return {
    state,
    query: { card_kind: hiddenFields.card_kind || "", card_com: hiddenFields.card_com || "", ecd_no: hiddenFields.ecd_no || "", sDate: hiddenFields.sDate || "", eDate: hiddenFields.eDate || "", date_type: hiddenFields.date_type || "", biz_type: hiddenFields.biz_type || "", pageSize: hiddenFields.pageSize || "", pageNo: hiddenFields.pageNo || "", order_type: hiddenFields.order_type || "", order_item: hiddenFields.order_item || "" },
    rows: normalizedRows.map((entry) => entry.row),
    items: normalizedRows.map((entry) => entry.item),
    meta: { listUrl: USAGE_HISTORY_LIST_URL, receiptUrl: RECEIPT_URL, detailUrl: DETAIL_URL },
  };
}

function inspectHipassPage(html) {
  const normalizedHtml = String(html || "");
  const sessionTimeMatch = normalizedHtml.match(/id="session_time"[^>]*value="(\d+)"/i) || normalizedHtml.match(/var\s+session_time\s*=\s*(\d+)/);
  const sessionTimeSeconds = sessionTimeMatch ? Number(sessionTimeMatch[1]) : null;
  if (/sendLoginVerificationCode\.do/.test(normalizedHtml) || /\uAC1C\uC778\/\uC678\uAD6D\uC778\s*\uB85C\uADF8\uC778/.test(normalizedHtml)) return { pageType: "login", reloginRequired: true, sessionTimeSeconds, reason: "manual_login_required" };
  if (/CommonAuthCheck\.jsp/.test(normalizedHtml) || /var\s+mgs_type\s*=/.test(normalizedHtml)) return { pageType: "permission-check", reloginRequired: true, sessionTimeSeconds, reason: "common_auth_check" };
  if (/UsePculrTabSearchList\.do/.test(normalizedHtml) || /\uC0AC\uC6A9\uB0B4\uC5ED\s*\uC870\uD68C/.test(normalizedHtml)) return { pageType: "usage-history-list", reloginRequired: false, sessionTimeSeconds, reason: null };
  return { pageType: "unknown", reloginRequired: false, sessionTimeSeconds, reason: null };
}

async function loadChromium() {
  for (const moduleName of ["playwright-core", "playwright"]) {
    try { const loaded = require(moduleName); if (loaded.chromium) return loaded.chromium; } catch { }
  }
  throw new Error("playwright-core or playwright is required. Install one of them in the environment running this skill.");
}

async function connectToChrome(options = {}) {
  const chromium = await loadChromium();
  if (isTruthy(options.headless)) {
    const launchOptions = {
      headless: true,
      args: ["--disable-popup-blocking", "--no-first-run", "--no-default-browser-check"],
    };
    if (options.browserChannel) {
      launchOptions.channel = options.browserChannel;
    } else if (process.platform === "win32") {
      launchOptions.executablePath = defaultChromePath();
    }
    return chromium.launch(launchOptions);
  }
  return chromium.connectOverCDP(options.cdpUrl || "http://127.0.0.1:9222");
}

async function submitUsageHistorySearch(page, query) {
  await page.evaluate((submittedQuery) => {
    const form = document.forms.hpForm || document.getElementById("hpForm");
    if (!form) throw new Error("Hi-Pass form hpForm was not found");
    const setFieldValue = (name, value) => {
      const element = form.elements.namedItem(name);
      const stringValue = String(value);
      if (!element) { const hidden = document.createElement("input"); hidden.type = "hidden"; hidden.name = name; hidden.value = stringValue; form.appendChild(hidden); return; }
      if (typeof element.length === "number" && element.tagName == null) { Array.from(element).forEach((candidate) => { candidate.checked = candidate.value === stringValue; }); return; }
      element.value = stringValue;
    };
    Object.entries(submittedQuery).forEach(([name, value]) => setFieldValue(name, value));
    const searchButton = [...document.querySelectorAll('a,button,input[type="button"],input[type="submit"]')].find((element) => /fn_search_usepculr/.test(element.getAttribute("onclick") || ""));
    if (searchButton) {
      searchButton.click();
      return;
    }
    form.action = "/usepculr/UsePculrTabSearchList.do";
    form.target = "if_main_post";
    form.submit();
  }, query);
}

async function listUsageHistory(options = {}) {
  const browser = await connectToChrome(options);
  try {
    const { page } = await getAutomationPage(browser);
    await ensureHipassSignedIn(page, options);
    const query = buildUsageHistoryQuery(options);
    await submitUsageHistorySearch(page, query);
    const frame = await waitForUsageHistoryFrame(page);
    await frame.waitForLoadState("domcontentloaded").catch(() => {});
    const html = await frame.content();
    const parsed = parseUsageHistoryList(html);
    return { query, ...parsed };
  } finally {
    await browser.close().catch(() => {});
  }
}

function getHipassRuntime() {
  return { USAGE_HISTORY_INIT_URL, buildUsageHistoryQuery, connectToChrome, inspectHipassPage, parseUsageHistoryList, listUsageHistory };
}

function compactDate(value, fallback) {
  const raw = value || fallback;
  const digits = String(raw || "").replace(/\D/g, "");
  if (digits.length < 8) {
    throw new Error(`Invalid date value: ${raw}`);
  }
  return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
}

function safeFilePart(value) {
  return String(value || "unknown")
    .replace(/[\\/:*?"<>|]/g, "_")
    .replace(/\s+/g, "")
    .replace(/_+/g, "_")
    .slice(0, 80) || "unknown";
}

function amountDigits(value) {
  const digits = String(value || "").replace(/\D/g, "");
  return digits || "0";
}

function buildBaseName(entry) {
  const date = compactDate(entry.workDateTime || entry.billDate, "19700101");
  const start = safeFilePart(entry.inTollgateName || entry.entryOffice || entry.inTollgate || "in");
  const end = safeFilePart(entry.outTollgateName || entry.exitOffice || entry.outTollgate || "out");
  const amount = amountDigits(entry.transactionAmount || entry.billedAmount || entry.paidToll);
  return `${date}_hipass_${start}-${end}_${amount}`;
}

async function getAutomationPage(browser) {
  const context = browser.contexts()[0] || (await browser.newContext());
  const page = context.pages()[0] || (await context.newPage());
  return { context, page };
}


function resolveAuthMode(args = {}) {
  return args.authMode || process.env.KGOV_HIPASS_AUTH_MODE || "idpw";
}

function resolveHipassCredentials(args = {}) {
  const id = args.hipassId || process.env.KGOV_HIPASS_ID || process.env.HIPASS_ID;
  const pw = process.env.KGOV_HIPASS_PW || process.env.HIPASS_PW;
  if (!id || !pw) {
    throw new Error("Hi-Pass ID/PW auth requires KGOV_HIPASS_ID and KGOV_HIPASS_PW in the local environment. Use --auth-mode session for manual browser login.");
  }
  return { id, pw };
}

async function autoLoginWithIdPw(page, args = {}) {
  const { id, pw } = resolveHipassCredentials(args);
  await page.goto(LOGIN_URL, { waitUntil: "domcontentloaded" });
  await page.waitForSelector('#user_id, input[name="user_id"], #per_user_id, input[name="per_user_id"]', { timeout: 10000 });
  await page.locator('#per_user_id').fill(id);
  await page.locator('#per_passwd').fill(pw);
  await page.evaluate(() => {
    const loginType = document.querySelector('#login_type, input[name="login_type"]');
    if (loginType) loginType.value = "2";
    const userType = document.querySelector('#user_type, input[name="user_type"]');
    if (userType && !userType.value) userType.value = "2";
  });

  const responsePromise = page.waitForResponse((response) => /\/comm\/login\.do|\/comm\/IdPwLogin/.test(response.url()), { timeout: 10000 }).catch(() => null);
  const navigationPromise = page.waitForNavigation({ waitUntil: "domcontentloaded", timeout: 10000 }).catch(() => null);
  const loginButton = page.locator('#per_login');
  if (await loginButton.count()) {
    await loginButton.click();
  } else {
    await page.evaluate(() => {
      if (typeof window.fn_login === "function") {
        window.fn_login("2");
        return;
      }
      throw new Error("Could not find a Hi-Pass login button or fn_login function");
    });
  }
  await Promise.race([responsePromise, navigationPromise, page.waitForTimeout(3000)]);
  await page.waitForURL((url) => !/\/comm\/lginpg\.do/.test(url.href), { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1000);
  if (!/\/comm\/lginpg\.do/.test(page.url())) {
    return;
  }
  const html = await page.content();
  if (/sendLoginVerificationCode\.do|chkLoginVerificationCode\.do|\uC778\uC99D\uBC88\uD638|\uD734\uB300\uC804\uD654|\uC774\uBA54\uC77C\s*\uC778\uC99D|\uACF5\uB3D9\uC778\uC99D\uC11C|\uC544\uC774\uD540|captcha/i.test(html)) {
    throw new Error("Hi-Pass requested extra identity verification. Stop automation and finish verification manually in the browser.");
  }
}

async function ensureHipassSignedIn(page, args = {}) {
  await page.goto(USAGE_HISTORY_INIT_URL, { waitUntil: "domcontentloaded" });
  let info = inspectHipassPage(await page.content());
  if (!info.reloginRequired) return info;
  const authMode = resolveAuthMode(args);
  if (isTruthy(args.headless) && authMode === "session") throw new Error("Headless mode cannot reuse a manually signed-in browser session. Use ID/PW auth or remove --headless.");
  if (authMode === "session") throw new Error("Hi-Pass session is not signed in or has expired. Sign in manually in the same Chrome profile, then retry.");
  if (authMode !== "idpw") throw new Error(`Unsupported auth mode: ${authMode}`);
  await autoLoginWithIdPw(page, args);
  await page.goto(USAGE_HISTORY_INIT_URL, { waitUntil: "domcontentloaded" });
  info = inspectHipassPage(await page.content());
  if (info.reloginRequired) throw new Error("Hi-Pass ID/PW login did not reach the usage-history page. Check credentials or finish any browser prompt manually.");
  return info;
}

async function waitForUsageHistoryFrame(page) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const frame = page.frames().find((candidate) => candidate.name() === "if_main_post");
    if (frame && frame.url() !== "about:blank") {
      return frame;
    }
    await page.waitForTimeout(250);
  }
  throw new Error("Timed out waiting for Hi-Pass usage-history frame");
}

async function openReceiptPopupForRow({ runtime, args }) {
  const {
    USAGE_HISTORY_INIT_URL,
    buildUsageHistoryQuery,
    connectToChrome,
    inspectHipassPage,
    parseUsageHistoryList,
  } = runtime;

  const browser = await connectToChrome({ cdpUrl: args.cdpUrl || "http://127.0.0.1:9222", headless: args.headless, browserChannel: args.browserChannel });
  let popup = null;
  try {
    const { context, page } = await getAutomationPage(browser);
    await ensureHipassSignedIn(page, args);

    const query = buildUsageHistoryQuery({
      startDate: args.startDate,
      endDate: args.endDate,
      pageSize: args.pageSize,
      pageNo: args.pageNo,
      ecdNo: args.ecdNo || args.encryptedCardNumber,
      receiptTimeType: args.receiptTimeType,
    });

    await page.evaluate((submittedQuery) => {
      const form = document.forms.hpForm || document.getElementById("hpForm");
      if (!form) {
        throw new Error("Hi-Pass form hpForm was not found");
      }
      const setFieldValue = (name, value) => {
        const element = form.elements.namedItem(name);
        const stringValue = String(value);
        if (!element) {
          const hidden = document.createElement("input");
          hidden.type = "hidden";
          hidden.name = name;
          hidden.value = stringValue;
          form.appendChild(hidden);
          return;
        }
        if (typeof element.length === "number" && element.tagName == null) {
          Array.from(element).forEach((candidate) => {
            candidate.checked = candidate.value === stringValue;
          });
          return;
        }
        element.value = stringValue;
      };
      Object.entries(submittedQuery).forEach(([name, value]) => setFieldValue(name, value));
      const searchButton = [...document.querySelectorAll('a,button,input[type="button"],input[type="submit"]')].find((element) => /fn_search_usepculr/.test(element.getAttribute("onclick") || ""));
      if (searchButton) {
        searchButton.click();
        return;
      }
      form.action = "/usepculr/UsePculrTabSearchList.do";
      form.target = "if_main_post";
      form.submit();
    }, query);

    const frame = await waitForUsageHistoryFrame(page);
    await frame.waitForLoadState("domcontentloaded").catch(() => {});
    const html = await frame.content();
    const parsed = parseUsageHistoryList(html);
    const rowIndex = Number(args.rowIndex || 1);
    const entry = parsed.rows[rowIndex - 1];
    if (!entry) {
      throw new Error(`Could not find Hi-Pass usage-history row ${rowIndex}`);
    }

    const popupPromise = context.waitForEvent("page", { timeout: 7000 }).catch(() => null);
    await frame.locator("table tbody tr").nth(rowIndex - 1).evaluate((element) => {
      const checkbox = element.querySelector('input[name="chkIdx"]');
      if (!checkbox) throw new Error("Could not find a receipt selection checkbox in the selected row");
      if (!checkbox.checked) checkbox.click();
      checkbox.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await frame.locator('#billSelect, a[onclick*="fn_print_receipt_html"]').last().click();

    popup = await popupPromise;
    if (!popup) {
      popup = context.pages().find((candidate) => /UsePculrReceiptPrint/.test(candidate.url())) || null;
    }
    if (!popup) {
      throw new Error("Receipt popup did not open. The site may have blocked the popup or changed the output flow.");
    }
    await popup.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});
    return { browser, popup, entry, query };
  } catch (error) {
    await browser.close().catch(() => {});
    throw error;
  }
}

async function saveReceipt({ popup, entry, args }) {
  const outputDir = path.resolve(args.outputDir || path.join("outputs", "receipts", compactDate(args.startDate).slice(0, 7)));
  fs.mkdirSync(outputDir, { recursive: true });

  const baseName = buildBaseName(entry);
  const pdfPath = path.join(outputDir, `${baseName}.pdf`);
  const pngPath = path.join(outputDir, `${baseName}.png`);

  await popup.emulateMedia({ media: "print" }).catch(() => {});
  await popup.pdf({ path: pdfPath, printBackground: true, preferCSSPageSize: true });

  await popup.emulateMedia({ media: "screen" }).catch(() => {});
  await popup.setViewportSize({ width: 700, height: 900 }).catch(() => {});
  const receiptClip = await popup.evaluate(() => {
    const candidates = [...document.querySelectorAll("div, table, td, section, article")]
      .map((element) => {
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        const text = (element.innerText || element.textContent || "").replace(/\s+/g, " ").trim();
        const hasBorder = [style.borderTopWidth, style.borderRightWidth, style.borderBottomWidth, style.borderLeftWidth]
          .some((width) => Number.parseFloat(width) >= 1);
        const looksLikeReceipt = /Hi-Pass|\uD558\uC774\uD328\uC2A4|\uC601\uC218\uC99D|\uD604\uB300\uCE74\uB4DC|\uC0AC\uC5C5\uC790/.test(text);
        return { x: rect.x, y: rect.y, width: rect.width, height: rect.height, hasBorder, looksLikeReceipt, textLength: text.length };
      })
      .filter((rect) => rect.x >= 0 && rect.x < 380 && rect.y > 100 && rect.width >= 120 && rect.width <= 320 && rect.height >= 180 && rect.height <= 420)
      .sort((a, b) => Number(b.hasBorder) - Number(a.hasBorder) || Number(b.looksLikeReceipt) - Number(a.looksLikeReceipt) || b.textLength - a.textLength);
    const best = candidates[0];
    if (!best) return null;
    const pad = 4;
    return {
      x: Math.max(0, Math.floor(best.x - pad)),
      y: Math.max(0, Math.floor(best.y - pad)),
      width: Math.ceil(best.width + pad * 2),
      height: Math.ceil(best.height + pad * 2),
    };
  }).catch(() => null);
  const clip = receiptClip || { x: 15, y: 235, width: 230, height: 330 };
  await popup.screenshot({ path: pngPath, clip });

  return { pdfPath, pngPath, baseName, pngCrop: clip };
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0 || argv[0] === "--help" || argv[0] === "help") {
    printHelp();
    return;
  }

  const command = argv[0];
  const args = parseArgs(argv.slice(1));
  assertProvider(args);

  if (command === "chrome-command") {
    process.stdout.write(`${buildChromeCommand(args)}\n`);
    return;
  }

  if (command === "list") {
    const runtime = getHipassRuntime();
    const result = await runtime.listUsageHistory({
      cdpUrl: args.cdpUrl,
      startDate: requireArg(args, "startDate", "start-date YYYY-MM-DD"),
      endDate: requireArg(args, "endDate", "end-date YYYY-MM-DD"),
      pageSize: args.pageSize,
      pageNo: args.pageNo,
      ecdNo: args.ecdNo || args.encryptedCardNumber,
      receiptTimeType: args.receiptTimeType,
      authMode: args.authMode,
      headless: args.headless,
      browserChannel: args.browserChannel,
    });
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (command === "collect") {
    requireArg(args, "startDate", "start-date YYYY-MM-DD");
    requireArg(args, "endDate", "end-date YYYY-MM-DD");
    requireArg(args, "rowIndex", "row-index N");
    const runtime = getHipassRuntime();
    const session = await openReceiptPopupForRow({ runtime, args });
    try {
      const saved = await saveReceipt({ popup: session.popup, entry: session.entry, args });
      process.stdout.write(`${JSON.stringify({ provider: "hipass", entry: session.entry, output: saved }, null, 2)}\n`);
    } finally {
      await session.browser.close().catch(() => {});
    }
    return;
  }

  throw new Error(`Unsupported command: ${command}`);
}

main().catch((error) => {
  console.error(error.message || error);
  process.exitCode = 1;
});

