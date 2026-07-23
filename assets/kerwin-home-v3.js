(function () {
  'use strict';

  var body = document.body;
  var gate = document.getElementById('access-gate');
  var accessForm = document.getElementById('access-form');
  var accessKey = document.getElementById('access-key');
  var accessError = document.getElementById('access-error');
  var gateUnlocking = false;
  var clearTimer = 0;

  function grantAccess() {
    if (gateUnlocking) return;
    gateUnlocking = true;
    if (clearTimer) clearTimeout(clearTimer);
    if (accessError) accessError.textContent = '正在展开研究主页…';
    if (gate) gate.classList.add('is-unlocking');
    setTimeout(function () {
      body.classList.remove('access-pending');
      body.classList.add('access-granted');
      if (gate) gate.setAttribute('aria-hidden', 'true');
      var firstFocus = document.querySelector('.site-header a, main a, main button');
      if (firstFocus) firstFocus.focus();
    }, 140);
  }

  function checkAccess() {
    var value = String(accessKey && accessKey.value || '').trim().toLowerCase();
    if (value === 'k') {
      grantAccess();
      return;
    }
    if (value && accessError) {
      accessError.textContent = '请输入 “k”，大小写均可。';
      if (clearTimer) clearTimeout(clearTimer);
      clearTimer = setTimeout(function () {
        if (!gateUnlocking && accessKey) {
          accessKey.value = '';
          accessKey.focus();
        }
      }, 260);
    }
  }

  if (accessKey) {
    accessKey.addEventListener('input', checkAccess);
    setTimeout(function () { if (!gateUnlocking) accessKey.focus(); }, 60);
  }
  if (accessForm) {
    accessForm.addEventListener('submit', function (event) {
      event.preventDefault();
      checkAccess();
    });
  }

  var legacyPages = [
    {slug:'google-ai-industry-use-cases-20260723',title:'谷歌电话会折射出的AI行业应用图谱\n从搜索、广告到金融、制药、机器人与空间智能的24个落地案例',date:'2026年7月23日',published_at:'2026-07-23T21:30:00+08:00',deck:'从Alphabet 2026 Q2电话会出发，以条目式结构拆解24个AI实际应用案例，并补充Google官方客户案例、商业价值与投资映射。',tag:'AI Application Casebook',category:'AI Industry Applications',source:'enya',homepage_approved:true},
    {slug:'gold-btc-dollar-leash-royalty-streaming-2026',title:'黄金、比特币与美元狗绳\nRoyalty / Streaming 与铜矿周期',date:'2026年6月15日',published_at:'2026-06-15T22:00:00+08:00',deck:'黄金 ETF、royalty / streaming、铜矿周期、加息逆转，以及黄金和比特币作为美元体系压力外溢阀门的投资框架。',tag:'宏观研究',source:'enya',homepage_approved:true},
    {slug:'nvidia-agent-platform-2026',title:'NVIDIA Agent 平台战略\nAgent 加速成为 AI 时代的新应用层',date:'2026年6月4日',published_at:'2026-06-04T11:30:00+08:00',deck:'从 OpenClaw 实践出发，串联 NVIDIA OpenShell、NemoClaw、Nemotron 与企业应用案例。',tag:'AI Research',source:'enya',homepage_approved:true},
    {slug:'us-estate-tax-hk-investor-guide',title:'香港投资人持有美股的遗产税盲区',date:'2026年6月2日',published_at:'2026-06-02T12:00:00+08:00',deck:'从美国 situs assets、Form 706-NA、40%阶梯税率到离岸架构，梳理香港投资人的关键风险。',tag:'客户教育',source:'enya',homepage_approved:true},
    {slug:'edge-computing-series',title:'NVIDIA Edge Computing\n五篇系列总览',date:'2026年5月30日',published_at:'2026-05-30T13:30:00+08:00',deck:'从机器人、汽车、边缘网络、视觉感知到本地智能体，串联 Edge Computing 投资图谱。',tag:'AI Research',source:'enya',homepage_approved:true},
    {slug:'nvidia-edge-ai-pc-local-agent',title:'Edge 系列第五篇\nAI PC / Workstation / Local Agent',date:'2026年5月30日',published_at:'2026-05-30T12:30:00+08:00',deck:'拆解 AI PC、Workstation、本地智能体、手机端侧 AI 与企业私有 AI 服务器。',tag:'AI Research',source:'enya',homepage_approved:true},
    {slug:'nvidia-edge-vision-ai-video-agent',title:'Edge 系列第四篇\nVision AI / 视频智能体',date:'2026年5月26日',published_at:'2026-05-26T10:30:00+08:00',deck:'拆解 Vision AI、视频智能体、NVIDIA Metropolis 与城市、工业和仓储场景。',tag:'AI Research',source:'enya',homepage_approved:true},
    {slug:'colossus-compute-revaluation',title:'出人意料\n马斯克的算力资产这么大？',date:'2026年5月21日',published_at:'2026-05-21T17:00:00+08:00',deck:'从 Colossus 算力租赁费用，对比 GPU、电力和云服务收入量级，重估算力中心资产价值。',tag:'AI Research',source:'enya',homepage_approved:true},
    {slug:'dissect-enya-openclaw-investment-brief',title:'拆解 Enya\nOpenClaw 部署投资启示录',date:'2026年5月19日',published_at:'2026-05-19T12:20:00+08:00',deck:'从 Enya / OpenClaw 部署案例，拆解 Agent 经济对 CPU、NVMe SSD、NAND、互联和企业软件的需求。',tag:'AI基础设施',source:'codex',homepage_approved:true}
  ];

  var themes = [
    {id:'ai',number:'01',name:'AI 系统与算力',short:'AI Systems',desc:'GPU、机架、电力、存储、光互联、Agent、行业应用与边缘计算。',test:/nvidia|英伟达|alphabet|google|gemini|ai |agent|算力|机架|gpu|edge|光互联|存储|hbm|nand|ssd|semiconductor|芯片|半导体|rubin|colossus|应用图谱/i},
    {id:'digital',number:'02',name:'数字金融与市场结构',short:'Digital Finance',desc:'加密资产、RWA、支付、稳定币与新一代交易基础设施。',test:/hyperliquid|hype|rwa|支付|stripe|digital asset|fintech|永续|交易所|比特币|稳定币/i},
    {id:'macro',number:'03',name:'宏观与真实资产',short:'Macro & Assets',desc:'利率、美元、黄金、铜、政策机构与跨资产配置框架。',test:/宏观|美联储|黄金|铜|美元|利率|fed|royalty|estate tax|遗产税/i},
    {id:'companies',number:'04',name:'公司与战略研究',short:'Companies',desc:'围绕产业链地位、资本开支、商业模式和估值的公司专题。',test:/alphabet|google|tesla|spacex|stripe|韩国|korea|financial ai|银行|公司|equity|三星|海力士|台积电|美国ai半导体/i},
    {id:'explore',number:'05',name:'实验与客户教育',short:'Explorations',desc:'把复杂概念变成地图、互动实验、科普工具和客户沟通素材。',test:/科普|互动|游戏|太阳系|警钟|案件|客户教育|block world|casefiles/i}
  ];

  var allPages = [];
  var earningsPages = [];
  var visibleCount = 12;
  var activeFilter = 'all';
  var query = '';

  fetch('/registry.json?v=' + Date.now(), {cache:'no-store'})
    .then(function (r) { if (!r.ok) throw new Error('registry'); return r.json(); })
    .then(init)
    .catch(function () { init([]); });

  function init(registry) {
    var map = {};
    registry.concat(legacyPages).forEach(function (p) {
      if (p && p.slug && p.homepage_approved === true) map[p.slug] = p;
    });
    allPages = Object.keys(map).map(function (k) { return map[k]; }).sort(sortDesc);
    earningsPages = allPages.filter(isEarnings);
    renderStats();
    renderTicker();
    renderEarnings();
    renderFeatured();
    renderThemes();
    renderArticles();
    bindControls();
  }

  function renderStats() {
    setText('stat-reports', allPages.length);
    setText('stat-earnings', earningsPages.length);
    setText('stat-updated', compactDate(allPages[0] && allPages[0].date));
  }

  function renderTicker() {
    var el = document.getElementById('ticker-items');
    if (!el) return;
    el.innerHTML = allPages.slice(0, 8).map(function (p) {
      var marker = isEarnings(p) ? '财报' : '专题';
      return '<a class="ticker-item" href="' + href(p) + '"><span class="ticker-kind">' + marker + '</span><b>' + esc(shortTitle(p.title)) + '</b><span>' + esc(compactDate(p.date)) + '</span></a>';
    }).join('');
  }

  function renderEarnings() {
    var lead = document.getElementById('earnings-lead');
    var list = document.getElementById('earnings-list');
    var count = document.getElementById('earnings-count');
    if (count) count.textContent = earningsPages.length + ' 篇';
    if (!lead || !list) return;
    if (!earningsPages.length) {
      lead.innerHTML = '<div class="empty">财报专栏正在建立。</div>';
      list.innerHTML = '';
      return;
    }
    var p = earningsPages[0];
    lead.innerHTML = '<div class="earnings-lead__top"><span class="earnings-company">' + esc(companyName(p)) + '</span><span>' + esc(p.date || '') + '</span></div>' +
      '<div class="earnings-quarter">' + esc(quarterLabel(p)) + '</div>' +
      '<h3>' + esc(p.title || '') + '</h3><p>' + esc(p.deck || '') + '</p>' +
      '<div class="earnings-lead__footer"><span>详细纪要 · 财务质量 · 管理层指引 · 估值变量</span><b>阅读全文 ↗</b></div>' +
      '<a class="story-link" href="' + href(p) + '" aria-label="阅读 ' + esc(p.title || '') + '"></a>';
    list.innerHTML = earningsPages.slice(1, 5).map(function (x, index) {
      return '<article class="earnings-item"><div class="earnings-item__index">0' + (index + 2) + '</div><div><div class="earnings-item__meta"><span>' + esc(companyName(x)) + '</span><span>' + esc(x.date || '') + '</span></div><h3>' + esc(x.title || '') + '</h3><p>' + esc(x.deck || '') + '</p></div><span class="earnings-item__arrow">↗</span><a class="story-link" href="' + href(x) + '" aria-label="阅读 ' + esc(x.title || '') + '"></a></article>';
    }).join('') || '<div class="earnings-placeholder"><b>下一家公司</b><span>后续财报及电话会议页面会自动进入本栏目。</span></div>';
  }

  function renderFeatured() {
    var researchPages = allPages.filter(function (p) { return !isEarnings(p); });
    var priority = ['google-ai-industry-use-cases-20260723','ai-memory-hbm-nand-cmx-20260722','china-open-model-global-token-value-chain-20260722'];
    var chosen = priority.map(function (slug) { return researchPages.find(function (p) { return p.slug === slug; }); }).filter(Boolean);
    researchPages.forEach(function (p) { if (chosen.length < 3 && chosen.indexOf(p) < 0) chosen.push(p); });
    var main = document.getElementById('feature-main');
    var side = document.getElementById('feature-side');
    if (!main || !chosen[0]) return;
    var p = chosen[0];
    main.innerHTML = '<div class="feature-main__visual"><div class="feature-orbit"><i></i><i></i><i></i></div></div>' +
      '<div class="feature-main__content"><div class="story-meta"><span class="story-tag">Lead Research</span><span>' + esc(p.date || '') + '</span><span>' + esc(p.tag || 'Research') + '</span></div><h3>' + esc(p.title || '') + '</h3><p>' + esc(p.deck || '') + '</p></div><a class="story-link" href="' + href(p) + '" aria-label="阅读 ' + esc(p.title || '') + '"></a>';
    side.innerHTML = chosen.slice(1,3).map(function (x) {
      return '<article class="side-story"><div class="story-meta"><span class="story-tag">Featured</span><span>' + esc(x.date || '') + '</span></div><h3>' + esc(x.title || '') + '</h3><p>' + esc(x.deck || '') + '</p><span class="side-story__arrow">↗</span><a class="story-link" href="' + href(x) + '" aria-label="阅读 ' + esc(x.title || '') + '"></a></article>';
    }).join('');
  }

  function renderThemes() {
    var el = document.getElementById('themes');
    if (!el) return;
    el.innerHTML = themes.map(function (t) {
      var count = allPages.filter(function (p) { var ok = t.test.test(haystack(p)); t.test.lastIndex = 0; return ok; }).length;
      return '<a class="theme-card" href="#latest" data-theme-link="' + t.id + '"><span class="theme-number">' + t.number + '</span><h3>' + t.name + '</h3><p>' + t.desc + '</p><span class="theme-count">' + count + ' 篇研究 · ' + t.short + '</span></a>';
    }).join('');
  }

  function bindControls() {
    var input = document.getElementById('search-input');
    if (input) input.addEventListener('input', function () { query = input.value.trim().toLowerCase(); visibleCount = 12; renderArticles(); });
    document.querySelectorAll('.filter').forEach(function (button) {
      button.addEventListener('click', function () { setFilter(button.dataset.filter); });
    });
    document.querySelectorAll('[data-theme-link]').forEach(function (link) {
      link.addEventListener('click', function () { setFilter(link.dataset.themeLink); });
    });
    var more = document.getElementById('load-more');
    if (more) more.addEventListener('click', function () { visibleCount += 12; renderArticles(); });
  }

  function setFilter(filter) {
    activeFilter = filter || 'all';
    visibleCount = 12;
    document.querySelectorAll('.filter').forEach(function (b) { b.classList.toggle('is-active', b.dataset.filter === activeFilter); });
    renderArticles();
  }

  function renderArticles() {
    var el = document.getElementById('article-grid');
    var more = document.getElementById('load-more');
    if (!el) return;
    var filtered = allPages.filter(function (p) {
      var filterOk = true;
      if (activeFilter === 'earnings') filterOk = isEarnings(p);
      else {
        var theme = themes.find(function (t) { return t.id === activeFilter; });
        if (theme) {
          filterOk = theme.test.test(haystack(p));
          theme.test.lastIndex = 0;
        }
      }
      return filterOk && (!query || haystack(p).indexOf(query) >= 0);
    });
    if (!filtered.length) {
      el.innerHTML = '<div class="empty">没有找到匹配专题，换一个关键词试试。</div>';
      if (more) more.style.display = 'none';
      return;
    }
    el.innerHTML = filtered.slice(0, visibleCount).map(articleCard).join('');
    if (more) more.style.display = filtered.length > visibleCount ? 'inline-flex' : 'none';
  }

  function articleCard(p) {
    var theme = themes.find(function (t) { var ok = t.test.test(haystack(p)); t.test.lastIndex = 0; return ok; });
    var label = isEarnings(p) ? 'Earnings Call' : ((theme && theme.short) || p.tag || 'Research');
    var className = isEarnings(p) ? 'article article--earnings' : 'article';
    return '<article class="' + className + '"><div class="article__meta"><span>' + esc(p.date || '') + '</span><span class="article__tag">' + esc(label) + '</span></div><h3>' + esc(p.title || '未命名专题') + '</h3><p>' + esc(p.deck || '') + '</p><div class="article__footer"><span>KERWIN RESEARCH</span><span class="article__arrow">↗</span></div><a href="' + href(p) + '" aria-label="阅读 ' + esc(p.title || '') + '"></a></article>';
  }

  function isEarnings(p) {
    return /earnings|财报|电话会|业绩会|results call/i.test([p.category,p.tag,p.title,p.deck,p.slug].join(' '));
  }

  function companyName(p) {
    var text = haystack(p);
    if (/alphabet|google|goog/.test(text)) return 'ALPHABET · GOOG / GOOGL';
    if (/tesla|tsla/.test(text)) return 'TESLA · TSLA';
    return String(p.title || 'COMPANY EARNINGS').split(/[\n｜|]/)[0].toUpperCase();
  }

  function quarterLabel(p) {
    var match = String(p.title || '').match(/(20\d{2})\s*Q([1-4])/i);
    return match ? match[1] + ' · QUARTER ' + match[2] + ' EARNINGS' : 'EARNINGS & MANAGEMENT CALL';
  }

  function href(p) { return p.source === 'codex' ? '/' + p.slug + '.html' : '/' + p.slug + '/'; }
  function haystack(p) { return [p.title,p.deck,p.tag,p.category,p.slug].join(' ').toLowerCase(); }
  function shortTitle(s) { return String(s || '').split('\n')[0].replace(/全景研究|深度报告/g,'').trim(); }
  function compactDate(s) { var d=String(s||'').match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/); return d ? d[2] + '.' + d[3] : (s || '持续更新'); }
  function sortDesc(a,b) { return timeOf(b) - timeOf(a); }
  function timeOf(p) { var t=Date.parse(p.published_at || ''); if(!Number.isNaN(t)) return t; var s=String(p.date||'').replace(/\D/g,''); return Number(s) || 0; }
  function setText(id,value) { var el=document.getElementById(id); if(el) el.textContent=value; }
  function esc(value) { var node=document.createElement('div'); node.textContent=value||''; return node.innerHTML; }

  var counterUrl='https://enyaclawd-counter.kerwin-finance.workers.dev?page=home';
  var counter=document.getElementById('counter-num');
  fetch(counterUrl).then(function(r){return r.json();}).then(function(d){if(counter)counter.textContent=Number(d.count||0).toLocaleString();}).catch(function(){if(counter)counter.textContent='·';});
  fetch(counterUrl,{method:'POST'}).then(function(r){return r.json();}).then(function(d){if(counter)counter.textContent=Number(d.count||0).toLocaleString();}).catch(function(){});
})();