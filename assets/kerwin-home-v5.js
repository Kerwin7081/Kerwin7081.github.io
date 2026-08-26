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
  var visibleCount = 12;
  var activeAxis = 'all';
  var activeType = 'all';
  var activeSeries = '';
  var query = '';

  var axes = [
    {id:'physical-infrastructure', number:'01', name:'AI 物理基础设施', short:'Physical Infrastructure', desc:'Power、Land、Data Center、NeoCloud 与 Time-to-Power。'},
    {id:'compute-chain', number:'02', name:'算力供应链', short:'Compute Chain', desc:'GPU / ASIC、HBM、存储、光互联、网络与供电系统。'},
    {id:'agent-economy', number:'03', name:'Token 与 Agent 经济', short:'Agent Economy', desc:'Token 产能、Agent Hour、AI 平台、模型与应用。'},
    {id:'capital-macro', number:'04', name:'AI 融资、宏观与资本成本', short:'Capital & Macro', desc:'融资结构、WACC、利率、流动性与资本循环。'},
    {id:'frontier-infrastructure', number:'05', name:'前沿基础设施', short:'Frontier Infrastructure', desc:'航天经济、数字金融、机器支付与新市场结构。'}
  ];

  var typeLabels = {
    earnings: 'Earnings',
    'deep-dive': 'Deep Dive',
    brief: 'Research Brief',
    interactive: 'Interactive',
    tracker: 'Tracker'
  };

  var statusLabels = {
    'new': 'New',
    updated: 'Updated',
    tracking: 'Tracking',
    evergreen: 'Evergreen'
  };

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
    if (value === 'k') {
      grantAccess();
      return;
    }
    if (value && error) {
      error.textContent = '请输入 “k”，大小写均可。';
      if (clearTimer) clearTimeout(clearTimer);
      clearTimer = setTimeout(function () {
        if (!unlocking && input) {
          input.value = '';
          if (window.matchMedia && window.matchMedia('(min-width: 761px)').matches) input.focus();
        }
      }, 350);
    }
  }

  if (input) input.addEventListener('input', checkAccess);
  if (form) form.addEventListener('submit', function (event) {
    event.preventDefault();
    checkAccess();
  });
  if (input && window.matchMedia && window.matchMedia('(min-width: 761px)').matches) {
    setTimeout(function () {
      if (!unlocking) input.focus();
    }, 80);
  }

  fetch('/registry.json?v=20260826v5', {cache:'no-cache'})
    .then(function (response) {
      if (!response.ok) throw new Error('registry');
      return response.json();
    })
    .then(function (registry) {
      if (!Array.isArray(registry)) throw new Error('registry-shape');
      init(registry, true);
    })
    .catch(function () {
      init([], false);
    });

  function init(registry, available) {
    if (!available) {
      body.classList.add('home-data-unavailable');
      renderTicker(false);
      setText('recent-count', '精选');
      disableDataControls();
      return;
    }

    var map = {};
    registry.forEach(function (page) {
      if (page && page.slug && page.homepage_approved === true) map[page.slug] = page;
    });
    allPages = Object.keys(map).map(function (key) { return map[key]; }).sort(sortDesc);
    earningsPages = allPages.filter(function (page) { return page.content_type === 'earnings'; });
    setText('recent-count', allPages.length);
    setText('header-date', allPages[0] ? compactDate(allPages[0].updated_at || allPages[0].date) : '—');
    renderTicker(true);
    renderRecent();
    renderEarnings();
    renderAxes();
    renderSeries();
    renderLibrary();
    bindControls();
  }

  function disableDataControls() {
    document.querySelectorAll('.library-tools button, #search-input, #load-more').forEach(function (control) {
      control.disabled = true;
    });
  }

  function renderTicker(available) {
    var target = document.getElementById('ticker-items');
    if (!target) return;
    if (!available) {
      target.innerHTML = '<span>动态目录暂时不可用 · 下方精选研究仍可直接阅读</span>';
      return;
    }
    target.innerHTML = dedupeBySeries(allPages, 7).map(function (page) {
      return '<a href="' + href(page) + '"><b>' + esc(shortTitle(page.title)) + '</b><small>' + esc(compactDate(page.updated_at || page.date)) + '</small></a>';
    }).join('');
  }

  function renderRecent() {
    var lead = document.getElementById('recent-lead');
    var list = document.getElementById('recent-list');
    if (!lead || !list || !allPages.length) return;
    var ranked = allPages.slice().sort(featureSort);
    var leadPage = ranked[0];
    var auxiliary = selectRecentAuxiliary(ranked, leadPage, 3);
    lead.innerHTML = '<div class="recent-lead__kicker">Featured Research · ' + esc(compactDate(leadPage.updated_at || leadPage.date)) + '</div><h3>' + esc(leadPage.title || '') + '</h3><p>' + esc(summary(leadPage)) + '</p><a class="story-link" href="' + href(leadPage) + '" aria-label="阅读 ' + esc(leadPage.title || '') + '"></a>';
    list.innerHTML = auxiliary.map(dispatchRow).join('');
  }

  function selectRecentAuxiliary(ranked, leadPage, limit) {
    var selected = [];
    var selectedSlugs = {};
    var usedSeries = {};
    var usedAxes = {};
    selectedSlugs[leadPage.slug] = true;
    if (leadPage.series_id) usedSeries[leadPage.series_id] = true;
    if (leadPage.axis) usedAxes[leadPage.axis] = true;

    ranked.forEach(function (page) {
      if (selected.length >= limit || selectedSlugs[page.slug] || !page.featured_rank) return;
      if (page.series_id && usedSeries[page.series_id]) return;
      selected.push(page);
      selectedSlugs[page.slug] = true;
      if (page.series_id) usedSeries[page.series_id] = true;
      if (page.axis) usedAxes[page.axis] = true;
    });

    ranked.forEach(function (page) {
      if (selected.length >= limit || selectedSlugs[page.slug]) return;
      if (page.series_id && usedSeries[page.series_id]) return;
      if (page.axis && usedAxes[page.axis]) return;
      selected.push(page);
      selectedSlugs[page.slug] = true;
      if (page.series_id) usedSeries[page.series_id] = true;
      if (page.axis) usedAxes[page.axis] = true;
    });

    ranked.forEach(function (page) {
      if (selected.length >= limit || selectedSlugs[page.slug]) return;
      if (page.series_id && usedSeries[page.series_id]) return;
      selected.push(page);
      selectedSlugs[page.slug] = true;
      if (page.series_id) usedSeries[page.series_id] = true;
    });
    return selected;
  }

  function renderEarnings() {
    var lead = document.getElementById('earnings-lead');
    var list = document.getElementById('earnings-list');
    if (!lead || !list || !earningsPages.length) return;
    var page = earningsPages[0];
    lead.innerHTML = '<div class="earnings-lead__top"><b>' + esc(companyName(page)) + '</b><span>' + esc(compactDate(page.updated_at || page.date)) + '</span></div><div class="earnings-lead__quarter">' + esc(quarterLabel(page)) + '</div><h3>' + esc(page.title || '') + '</h3><p>' + esc(summary(page)) + '</p><div class="earnings-lead__foot"><span>财务质量 · 管理层指引 · 估值变量</span><b>阅读全文 ↗</b></div><a class="story-link" href="' + href(page) + '" aria-label="阅读 ' + esc(page.title || '') + '"></a>';
    list.innerHTML = earningsPages.slice(1, 5).map(function (item, index) {
      return '<article class="earnings-row"><div class="earnings-row__num">0' + (index + 2) + '</div><div><div class="earnings-row__meta"><span>' + esc(companyName(item)) + '</span><span>' + esc(compactDate(item.updated_at || item.date)) + '</span></div><h3>' + esc(item.title || '') + '</h3><a class="story-link" href="' + href(item) + '" aria-label="阅读 ' + esc(item.title || '') + '"></a></div></article>';
    }).join('');
  }

  function renderAxes() {
    var target = document.getElementById('axis-grid');
    if (!target) return;
    target.innerHTML = axes.map(function (axis) {
      var count = allPages.filter(function (page) { return page.axis === axis.id; }).length;
      return '<a class="axis-row" href="#library" data-axis-link="' + axis.id + '"><b>' + axis.number + '</b><strong>' + axis.name + '</strong><span>' + axis.desc + '</span><i>' + count + '</i></a>';
    }).join('');
  }

  function renderSeries() {
    var target = document.getElementById('series-strip');
    if (!target) return;
    var groups = {};
    allPages.forEach(function (page) {
      if (!page.series_id) return;
      if (!groups[page.series_id]) groups[page.series_id] = {id:page.series_id, title:page.series_title || page.series_id, pages:[]};
      groups[page.series_id].pages.push(page);
    });
    var series = Object.keys(groups).map(function (key) {
      var group = groups[key];
      group.pages.sort(sortDesc);
      group.latest = timeOf(group.pages[0]);
      return group;
    }).filter(function (group) { return group.pages.length >= 2; }).sort(function (a, b) { return b.latest - a.latest; }).slice(0, 3);
    target.innerHTML = series.map(function (group) {
      return '<a href="#library" data-series-link="' + esc(group.id) + '"><b>' + esc(group.title) + '</b><span>' + group.pages.length + ' 篇 · ' + esc(seriesRange(group.pages)) + '</span></a>';
    }).join('');
  }

  function bindControls() {
    var search = document.getElementById('search-input');
    if (search) search.addEventListener('input', function () {
      query = String(search.value || '').trim().toLowerCase();
      visibleCount = 12;
      renderLibrary();
    });
    document.querySelectorAll('[data-axis-filter]').forEach(function (button) {
      button.addEventListener('click', function () { setAxis(button.getAttribute('data-axis-filter')); });
    });
    document.querySelectorAll('[data-type-filter]').forEach(function (button) {
      button.addEventListener('click', function () { setType(button.getAttribute('data-type-filter')); });
    });
    document.querySelectorAll('[data-axis-link]').forEach(function (link) {
      link.addEventListener('click', function () { setAxis(link.getAttribute('data-axis-link')); });
    });
    document.querySelectorAll('[data-series-link]').forEach(function (link) {
      link.addEventListener('click', function () { setSeries(link.getAttribute('data-series-link')); });
    });
    var more = document.getElementById('load-more');
    if (more) more.addEventListener('click', function () {
      visibleCount += 12;
      renderLibrary();
    });
    var context = document.getElementById('library-context');
    if (context) context.addEventListener('click', function (event) {
      if (event.target && event.target.getAttribute('data-clear-series') === 'true') setSeries('');
    });
  }

  function setAxis(axis) {
    activeAxis = axis || 'all';
    activeSeries = '';
    visibleCount = 12;
    document.querySelectorAll('[data-axis-filter]').forEach(function (button) {
      button.classList.toggle('is-active', button.getAttribute('data-axis-filter') === activeAxis);
    });
    renderLibrary();
  }

  function setType(type) {
    activeType = type || 'all';
    activeSeries = '';
    visibleCount = 12;
    document.querySelectorAll('[data-type-filter]').forEach(function (button) {
      button.classList.toggle('is-active', button.getAttribute('data-type-filter') === activeType);
    });
    renderLibrary();
  }

  function setSeries(series) {
    activeSeries = series || '';
    activeAxis = 'all';
    activeType = 'all';
    visibleCount = 12;
    document.querySelectorAll('[data-axis-filter]').forEach(function (button) {
      button.classList.toggle('is-active', button.getAttribute('data-axis-filter') === 'all');
    });
    document.querySelectorAll('[data-type-filter]').forEach(function (button) {
      button.classList.toggle('is-active', button.getAttribute('data-type-filter') === 'all');
    });
    renderLibrary();
  }

  function renderLibrary() {
    var target = document.getElementById('library-list');
    var more = document.getElementById('load-more');
    var context = document.getElementById('library-context');
    if (!target) return;
    var filtered = allPages.filter(function (page) {
      var axisOk = activeAxis === 'all' || page.axis === activeAxis;
      var typeOk = activeType === 'all' || page.content_type === activeType;
      var seriesOk = !activeSeries || page.series_id === activeSeries;
      var queryOk = !query || haystack(page).indexOf(query) >= 0;
      return axisOk && typeOk && seriesOk && queryOk;
    });
    if (activeSeries && context) {
      var seriesPage = filtered[0];
      context.hidden = false;
      context.innerHTML = '<span>系列筛选：' + esc(seriesPage && seriesPage.series_title || activeSeries) + ' · ' + filtered.length + ' 篇</span><button type="button" data-clear-series="true">清除系列</button>';
    } else if (context) {
      context.hidden = true;
      context.innerHTML = '';
    }
    if (!filtered.length) {
      target.innerHTML = '<div class="empty">没有找到匹配专题，换一个关键词或筛选条件试试。</div>';
      if (more) more.style.display = 'none';
      return;
    }
    target.innerHTML = filtered.slice(0, visibleCount).map(libraryRow).join('');
    if (more) more.style.display = filtered.length > visibleCount ? 'inline-flex' : 'none';
  }

  function dispatchRow(page) {
    return '<article class="dispatch-row"><div class="dispatch-row__date">' + esc(compactDate(page.updated_at || page.date)) + '</div><div><b>' + esc(page.title || '') + '</b><span>' + esc(page.series_title || axisName(page.axis)) + '</span></div><span>↗</span><a class="story-link" href="' + href(page) + '" aria-label="阅读 ' + esc(page.title || '') + '"></a></article>';
  }

  function libraryRow(page) {
    var badges = [];
    if (page.series_title) badges.push('<span>' + esc(page.series_title) + (page.series_order ? ' · ' + page.series_order : '') + '</span>');
    if (page.status && page.status !== 'evergreen') badges.push('<span class="is-status-' + esc(page.status) + '">' + esc(statusLabels[page.status] || page.status) + '</span>');
    return '<article class="library-row"><div class="library-row__meta"><span>' + esc(compactDate(page.updated_at || page.date)) + '</span><small>' + esc(axisName(page.axis)) + '</small></div><div><h3>' + esc(page.title || '未命名专题') + '</h3><p>' + esc(summary(page)) + '</p>' + (badges.length ? '<div class="library-row__badges">' + badges.join('') + '</div>' : '') + '</div><span class="library-row__arrow">↗</span><a class="story-link" href="' + href(page) + '" aria-label="阅读 ' + esc(page.title || '') + '"></a></article>';
  }

  function dedupeBySeries(pages, limit) {
    var selected = [];
    var seen = {};
    pages.forEach(function (page) {
      if (selected.length >= limit) return;
      var key = page.series_id || page.slug;
      if (seen[key]) return;
      seen[key] = true;
      selected.push(page);
    });
    return selected;
  }

  function seriesRange(pages) {
    var ordered = pages.filter(function (page) { return typeof page.series_order === 'number'; }).sort(function (a, b) { return a.series_order - b.series_order; });
    if (!ordered.length) return '持续更新';
    var first = ordered[0].series_order;
    var last = ordered[ordered.length - 1].series_order;
    return first === last ? '第 ' + last + ' 篇' : '第 ' + first + '–' + last + ' 篇';
  }

  function axisName(id) {
    var name = 'Research';
    axes.forEach(function (axis) {
      if (axis.id === id) name = axis.short;
    });
    return name;
  }

  function companyName(page) {
    var text = haystack(page);
    if (/alphabet|google|goog/.test(text)) return 'ALPHABET · GOOG / GOOGL';
    if (/tesla|tsla/.test(text)) return 'TESLA · TSLA';
    if (/nokia/.test(text)) return 'NOKIA · NOK';
    var first = String(page.title || '财报').split(/[\n｜|]/)[0].trim();
    return /[\u4e00-\u9fff]/.test(first) ? first : first.toUpperCase();
  }

  function quarterLabel(page) {
    var match = String(page.title || '').match(/(20\d{2})\s*Q([1-4])/i);
    return match ? match[1] + ' · QUARTER ' + match[2] + ' EARNINGS' : 'EARNINGS & MANAGEMENT CALL';
  }

  function summary(page) {
    return page.homepage_deck || page.deck || '';
  }

  function href(page) {
    return page.path || '/' + page.slug + '/';
  }

  function haystack(page) {
    return [page.title, page.homepage_deck, page.deck, page.tag, page.category, page.series_title, axisName(page.axis), typeLabels[page.content_type], page.slug].join(' ').toLowerCase();
  }

  function shortTitle(title) {
    return String(title || '').split('\n')[0].replace(/全景研究|深度报告/g, '').trim();
  }

  function compactDate(value) {
    var date = String(value || '').match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/);
    return date ? two(date[2]) + '.' + two(date[3]) : (value || '持续更新');
  }

  function two(value) {
    var text = String(value || '');
    return text.length < 2 ? '0' + text : text;
  }

  function timeOf(page) {
    var time = Date.parse(page.updated_at || page.published_at || '');
    if (!isNaN(time)) return time;
    return Number(String(page.date || '').replace(/\D/g, '')) || 0;
  }

  function sortDesc(a, b) {
    return timeOf(b) - timeOf(a);
  }

  function featureSort(a, b) {
    var aRank = Number(a.featured_rank || 99);
    var bRank = Number(b.featured_rank || 99);
    if (aRank !== bRank) return aRank - bRank;
    return sortDesc(a, b);
  }

  function setText(id, value) {
    var node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  function esc(value) {
    var node = document.createElement('div');
    node.textContent = value || '';
    return node.innerHTML;
  }

  var counterUrl = 'https://enyaclawd-counter.kerwin-finance.workers.dev?page=home';
  var counter = document.getElementById('counter-num');
  fetch(counterUrl, {method:'POST'})
    .then(function (response) { return response.json(); })
    .then(function (data) { if (counter) counter.textContent = Number(data.count || 0).toLocaleString(); })
    .catch(function () {
      fetch(counterUrl)
        .then(function (response) { return response.json(); })
        .then(function (data) { if (counter) counter.textContent = Number(data.count || 0).toLocaleString(); })
        .catch(function () { if (counter) counter.textContent = '·'; });
    });
}());
