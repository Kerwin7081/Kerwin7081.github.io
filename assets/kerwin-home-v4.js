(function () {
  'use strict';

  var body = document.body;
  var gate = document.getElementById('home-gate');
  var form = document.getElementById('access-form');
  var input = document.getElementById('access-key');
  var error = document.getElementById('access-error');
  var unlocking = false;
  var clearTimer = 0;
  var allPages = [];
  var earningsPages = [];
  var visibleCount = 10;
  var activeFilter = 'all';
  var query = '';
  var manualPages = [
    {
      slug:'ai-factory-ballot-box-community-roi-20260824',
      title:'AI Factory Meets the Ballot Box｜谁来为 AI 基础设施付账？',
      date:'2026年8月24日',
      deck:'美国州际政策竞争系列⑤：以 Texas、Pennsylvania、Georgia、Virginia、Arizona 与 California 六州案例，研究居民电费、水资源、社区收益与地方审批如何通过 Take-or-Pay、Large-load Tariff、Community Benefit Agreement 和 Local Approval 进入 Time-to-Power、WACC 与 ROIC。',
      tag:'AI Infrastructure · Social License · 2026 Midterms',
      category:'AI Infrastructure · U.S. State Policy · 2026 Midterms',
      source:'enya',
      homepage_approved:true,
      published_at:'2026-08-24T13:19:00+08:00',
      layout_id:'kerwin-editorial-research-v1',
      mobile_qa_version:'1.2.0',
      desktop_qa_version:'1.0.0'
    },
    {
      slug:'us-ai-deployment-map-midterms-20260823',
      title:'美国50州 AI Deployment Map｜2026中期选举前的算力基础设施地图',
      date:'2026年8月23日',
      deck:'美国州际政策竞争系列④：以50州统一底表比较党派控制、电力、电网、土地、劳工、水资源、审批、社区许可、产业生态与2026州级选举暴露，建立 AI Deployment Capacity、Election Exposure 与 Probability-adjusted Energized MW 框架。',
      tag:'AI Infrastructure · U.S. State Policy · 2026 Midterms',
      category:'AI Infrastructure · U.S. State Policy · 2026 Midterms',
      source:'enya',
      homepage_approved:true,
      published_at:'2026-08-23T17:55:00+08:00',
      layout_id:'kerwin-editorial-research-v1',
      mobile_qa_version:'1.2.0',
      desktop_qa_version:'1.0.0'
    },
    {
      slug:'delaware-vs-texas-corporate-domicile-20260823',
      title:'Delaware vs Texas｜美国公司法的迁册战争',
      date:'2026年8月23日',
      deck:'美国州际政策竞争系列③：客观比较 Delaware 与 Texas 的公司法、专业法院、管理层自主权与少数股东保护，并以 Tesla、SpaceX、OpenAI、Anthropic、Stripe、Databricks、SB Energy 与 Cloverleaf 案例拆分法律注册地、总部和物理资产，最终建立 Governance WACC 与 Total Governance Cost 框架。',
      tag:'U.S. State Policy · Corporate Domicile · Governance WACC',
      category:'AI Infrastructure · U.S. State Policy · Corporate Law',
      source:'enya',
      homepage_approved:true,
      published_at:'2026-08-23T13:58:00+08:00',
      layout_id:'kerwin-editorial-research-v1',
      mobile_qa_version:'1.2.0',
      desktop_qa_version:'1.0.0'
    },
    {
      slug:'texas-industrial-os-20260820',
      title:'Texas Industrial OS｜为什么得州正在成为 AI、航天与重资本的制度型平台？',
      date:'2026年8月20日',
      deck:'美国州际政策竞争系列②：从公司法、税制、ERCOT 电力、土地、劳工、产业链与社区许可出发，把 Texas 作为一套把资本转化为物理产能的 Industrial OS 来研究，并建立 State Absorption Capacity 与 Probability-adjusted Energized MW 框架。',
      tag:'AI Infrastructure · U.S. State Policy · Texas Industrial OS',
      category:'AI Infrastructure · U.S. State Policy',
      source:'enya',
      homepage_approved:true,
      published_at:'2026-08-20T13:39:00+08:00',
      layout_id:'kerwin-editorial-research-v1',
      mobile_qa_version:'1.2.0',
      desktop_qa_version:'1.0.0'
    }
  ];
  body.classList.add('home-js', 'home-gate-pending');

  function grantAccess() {
    if (unlocking) return;
    unlocking = true;
    if (clearTimer) clearTimeout(clearTimer);
    if (error) error.textContent = '正在展开研究主页…';
    if (gate) gate.classList.add('is-unlocking');
    setTimeout(function () {
      body.classList.remove('home-gate-pending');
      body.classList.add('home-gate-granted');
      if (gate) {
        gate.setAttribute('aria-hidden', 'true');
        gate.hidden = true;
      }
      var focus = document.querySelector('.home-nav a, main a, main button');
      if (focus) focus.focus();
    }, 160);
  }

  function checkAccess() {
    var value = String(input && input.value || '').trim().toLowerCase();
    if (value === 'k') { grantAccess(); return; }
    if (value && error) {
      error.textContent = '请输入 “k”，大小写均可。';
      if (clearTimer) clearTimeout(clearTimer);
      clearTimer = setTimeout(function () {
        if (!unlocking && input) { input.value = ''; input.focus(); }
      }, 260);
    }
  }

  if (input) input.addEventListener('input', checkAccess);
  if (form) form.addEventListener('submit', function (event) { event.preventDefault(); checkAccess(); });
  if (input && window.matchMedia && window.matchMedia('(min-width: 761px)').matches) {
    setTimeout(function () { if (!unlocking) input.focus(); }, 80);
  }

  var themes = [
    {id:'ai', number:'01', name:'AI 系统与算力', short:'AI Systems', desc:'GPU、机架、电力、存储、光互联与 Agent。', test:/nvidia|英伟达|alphabet|google|gemini|ai |agent|算力|机架|gpu|edge|光互联|存储|hbm|nand|ssd|semiconductor|芯片|半导体|rubin|colossus|应用图谱/i},
    {id:'digital', number:'02', name:'数字金融与市场结构', short:'Digital Finance', desc:'支付、稳定币、RWA、交易所与机器经济。', test:/hyperliquid|hype|rwa|支付|stripe|digital asset|fintech|永续|交易所|比特币|稳定币|agent payment/i},
    {id:'macro', number:'03', name:'宏观与真实资产', short:'Macro & Assets', desc:'利率、美元、黄金、铜与跨资产配置。', test:/宏观|美联储|黄金|铜|美元|利率|fed|royalty|estate tax|遗产税|离岸信托|税务|trust|ipo compliance/i},
    {id:'companies', number:'04', name:'公司与战略研究', short:'Companies', desc:'商业模式、资本开支、产业地位与估值。', test:/alphabet|google|tesla|spacex|stripe|韩国|korea|financial ai|银行|公司|equity|三星|海力士|台积电|美国ai半导体/i},
    {id:'explore', number:'05', name:'实验与客户教育', short:'Explorations', desc:'地图、互动实验、科普工具与沟通素材。', test:/科普|互动|游戏|太阳系|警钟|案件|客户教育|block world|casefiles/i}
  ];

  fetch('/registry.json?v=' + Date.now(), {cache:'no-store'})
    .then(function (response) { if (!response.ok) throw new Error('registry'); return response.json(); })
    .then(function (registry) { if (!Array.isArray(registry)) throw new Error('registry-shape'); init(registry, true); })
    .catch(function () { init([], false); });

  function init(registry, available) {
    var map = {};
    manualPages.concat(registry || []).forEach(function (page) {
      if (page && page.slug && page.homepage_approved === true) map[page.slug] = page;
    });
    allPages = Object.keys(map).map(function (key) { return map[key]; }).sort(sortDesc);
    earningsPages = allPages.filter(isEarnings);
    setText('recent-count', available ? allPages.length : '—');
    setText('header-date', available && allPages[0] ? compactDate(allPages[0].date) : '—');
    renderTicker(available);
    renderRecent(available);
    renderEarnings(available);
    renderAxes();
    renderLibrary(available);
    bindControls();
  }

  function renderTicker(available) {
    var target = document.getElementById('ticker-items');
    if (!target) return;
    if (!available) { target.innerHTML = '<span>研究目录暂时不可用，请稍后刷新。</span>'; return; }
    target.innerHTML = allPages.slice(0, 8).map(function (page) {
      return '<a href="' + href(page) + '"><b>' + esc(shortTitle(page.title)) + '</b><small>' + esc(compactDate(page.date)) + '</small></a>';
    }).join('');
  }

  function renderRecent(available) {
    var lead = document.getElementById('recent-lead');
    var list = document.getElementById('recent-list');
    if (!lead || !list) return;
    if (!available || !allPages.length) {
      lead.innerHTML = '<div class="recent-lead__kicker">Recent Dispatch</div><h3>' + (available ? '暂无已发布研究' : '研究目录暂时无法载入') + '</h3><p>' + (available ? '目录更新后会显示最新一篇。' : '请稍后刷新。') + '</p>';
      list.innerHTML = '';
      return;
    }
    var leadPage = allPages[0];
    lead.innerHTML = '<div class="recent-lead__kicker">Recent Dispatch · ' + esc(compactDate(leadPage.date)) + '</div><h3>' + esc(leadPage.title || '') + '</h3><p>' + esc(leadPage.deck || '') + '</p><a class="story-link" href="' + href(leadPage) + '" aria-label="阅读 ' + esc(leadPage.title || '') + '"></a>';
    list.innerHTML = allPages.slice(1, 4).map(dispatchRow).join('');
  }

  function renderEarnings(available) {
    var lead = document.getElementById('earnings-lead');
    var list = document.getElementById('earnings-list');
    if (!lead || !list) return;
    if (!available || !earningsPages.length) {
      lead.innerHTML = '<div class="earnings-lead__fallback"><span>财报研究</span><b>' + (available ? '财报桌正在建立。' : '研究目录暂时无法载入，请稍后刷新。') + '</b></div>';
      list.innerHTML = '';
      return;
    }
    var page = earningsPages[0];
    lead.innerHTML = '<div class="earnings-lead__top"><b>' + esc(companyName(page)) + '</b><span>' + esc(compactDate(page.date)) + '</span></div><div class="earnings-lead__quarter">' + esc(quarterLabel(page)) + '</div><h3>' + esc(page.title || '') + '</h3><p>' + esc(page.deck || '') + '</p><div class="earnings-lead__foot"><span>财务质量 · 管理层指引 · 估值变量</span><b>阅读全文 ↗</b></div><a class="story-link" href="' + href(page) + '" aria-label="阅读 ' + esc(page.title || '') + '"></a>';
    list.innerHTML = earningsPages.slice(1, 5).map(function (item, index) { return '<article class="earnings-row"><div class="earnings-row__num">0' + (index + 2) + '</div><div><div class="earnings-row__meta"><span>' + esc(companyName(item)) + '</span><span>' + esc(compactDate(item.date)) + '</span></div><h3>' + esc(item.title || '') + '</h3><a class="story-link" href="' + href(item) + '" aria-label="阅读 ' + esc(item.title || '') + '"></a></div></article>'; }).join('');
  }

  function renderAxes() {
    var target = document.getElementById('axis-grid');
    if (!target) return;
    target.innerHTML = themes.map(function (theme) {
      var count = allPages.filter(function (page) { var ok = theme.test.test(haystack(page)); theme.test.lastIndex = 0; return ok; }).length;
      return '<a class="axis-row" href="#library" data-theme-link="' + theme.id + '"><b>' + theme.number + '</b><strong>' + theme.name + '</strong><span>' + theme.desc + ' · ' + count + ' 篇研究</span><i>↗</i></a>';
    }).join('');
  }

  function bindControls() {
    var search = document.getElementById('search-input');
    if (search) search.addEventListener('input', function () { query = String(search.value || '').trim().toLowerCase(); visibleCount = 10; renderLibrary(true); });
    document.querySelectorAll('.filter').forEach(function (button) { button.addEventListener('click', function () { setFilter(button.dataset.filter); }); });
    document.querySelectorAll('[data-theme-link]').forEach(function (link) { link.addEventListener('click', function () { setFilter(link.dataset.themeLink); }); });
    var more = document.getElementById('load-more');
    if (more) more.addEventListener('click', function () { visibleCount += 10; renderLibrary(true); });
  }

  function setFilter(filter) {
    activeFilter = filter || 'all';
    visibleCount = 10;
    document.querySelectorAll('.filter').forEach(function (button) { button.classList.toggle('is-active', button.dataset.filter === activeFilter); });
    renderLibrary(true);
  }

  function renderLibrary(available) {
    var target = document.getElementById('library-list');
    var more = document.getElementById('load-more');
    if (!target) return;
    if (!available) { target.innerHTML = '<div class="empty">研究目录暂时无法载入，请稍后刷新。</div>'; if (more) more.style.display = 'none'; return; }
    var filtered = allPages.filter(function (page) {
      var filterOk = true;
      if (activeFilter === 'earnings') filterOk = isEarnings(page);
      else {
        var theme = themes.find(function (item) { return item.id === activeFilter; });
        if (theme) { filterOk = theme.test.test(haystack(page)); theme.test.lastIndex = 0; }
      }
      return filterOk && (!query || haystack(page).indexOf(query) >= 0);
    });
    if (!filtered.length) { target.innerHTML = '<div class="empty">没有找到匹配专题，换一个关键词试试。</div>'; if (more) more.style.display = 'none'; return; }
    target.innerHTML = filtered.slice(0, visibleCount).map(libraryRow).join('');
    if (more) more.style.display = filtered.length > visibleCount ? 'inline-flex' : 'none';
  }

  function dispatchRow(page) { return '<article class="dispatch-row"><div class="dispatch-row__date">' + esc(compactDate(page.date)) + '</div><div><b>' + esc(page.title || '') + '</b><span>' + esc(page.tag || 'Research') + '</span></div><span>↗</span><a class="story-link" href="' + href(page) + '" aria-label="阅读 ' + esc(page.title || '') + '"></a></article>'; }
  function libraryRow(page) { var theme = themes.find(function (item) { var ok = item.test.test(haystack(page)); item.test.lastIndex = 0; return ok; }); return '<article class="library-row"><div class="library-row__meta"><span>' + esc(compactDate(page.date)) + '</span><small>' + esc((theme && theme.short) || page.tag || 'Research') + '</small></div><div><h3>' + esc(page.title || '未命名专题') + '</h3><p>' + esc(page.deck || '') + '</p></div><span class="library-row__arrow">↗</span><a class="story-link" href="' + href(page) + '" aria-label="阅读 ' + esc(page.title || '') + '"></a></article>'; }
  function isEarnings(page) { if (/AI Industry Applications|AI Application Casebook/i.test([page.category, page.tag].join(' '))) return false; return /earnings|财报|电话会|业绩会|results call/i.test([page.category, page.tag, page.title, page.deck, page.slug].join(' ')); }
  function companyName(page) { var text = haystack(page); if (/alphabet|google|goog/.test(text)) return 'ALPHABET · GOOG / GOOGL'; if (/tesla|tsla/.test(text)) return 'TESLA · TSLA'; var first = String(page.title || '财报').split(/[\n｜|]/)[0].trim(); return /[\u4e00-\u9fff]/.test(first) ? first : first.toUpperCase(); }
  function quarterLabel(page) { var match = String(page.title || '').match(/(20\d{2})\s*Q([1-4])/i); return match ? match[1] + ' · QUARTER ' + match[2] + ' EARNINGS' : 'EARNINGS & MANAGEMENT CALL'; }
  function href(page) { return page.path || '/' + page.slug + '/'; }
  function haystack(page) { return [page.title, page.deck, page.tag, page.category, page.slug].join(' ').toLowerCase(); }
  function shortTitle(title) { return String(title || '').split('\n')[0].replace(/全景研究|深度报告/g, '').trim(); }
  function compactDate(value) { var date = String(value || '').match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/); return date ? date[2].padStart(2, '0') + '.' + date[3].padStart(2, '0') : (value || '持续更新'); }
  function timeOf(page) { var time = Date.parse(page.published_at || ''); if (!Number.isNaN(time)) return time; return Number(String(page.date || '').replace(/\D/g, '')) || 0; }
  function sortDesc(a, b) { return timeOf(b) - timeOf(a); }
  function setText(id, value) { var node = document.getElementById(id); if (node) node.textContent = value; }
  function esc(value) { var node = document.createElement('div'); node.textContent = value || ''; return node.innerHTML; }

  var counterUrl = 'https://enyaclawd-counter.kerwin-finance.workers.dev?page=home';
  var counter = document.getElementById('counter-num');
  fetch(counterUrl).then(function (response) { return response.json(); }).then(function (data) { if (counter) counter.textContent = Number(data.count || 0).toLocaleString(); }).catch(function () { if (counter) counter.textContent = '·'; });
  fetch(counterUrl, {method:'POST'}).then(function (response) { return response.json(); }).then(function (data) { if (counter) counter.textContent = Number(data.count || 0).toLocaleString(); }).catch(function () {});
}());