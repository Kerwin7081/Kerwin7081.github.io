(function () {
  'use strict';

  var AXES = [
    {id: 'physical-infrastructure', zh: '物理基础设施', desc: '电力、土地、许可与可交付容量。'},
    {id: 'compute-chain', zh: '算力产业链', desc: '芯片、系统、网络、存储与交付。'},
    {id: 'agent-economy', zh: 'Token 与 Agent', desc: 'Token 产能、Agent 工时与应用。'},
    {id: 'capital-macro', zh: '资本与宏观', desc: '融资、利率、信用、黄金与资本成本。'},
    {id: 'frontier-infrastructure', zh: '前沿基础设施', desc: '航天、数字金融与新市场结构。'}
  ];
  var axisById = {};
  AXES.forEach(function (axis) { axisById[axis.id] = axis; });

  var page = document.body.getAttribute('data-hub') || 'home';
  var pages = [];
  var axis = 'all';
  var series = '';
  var query = '';

  fetch('/registry.json', {cache: 'no-store'})
    .then(function (response) {
      if (!response.ok) throw new Error('registry');
      return response.json();
    })
    .then(function (registry) {
      if (!Array.isArray(registry)) throw new Error('registry-shape');
      pages = registry.filter(function (item) {
        return item && item.slug && item.homepage_approved === true;
      }).sort(sortDesc);
      render();
    })
    .catch(function () {
      setText('hub-date', '目录暂不可用');
      paint('#latest-list, #library-list, #earnings-list, #axis-list, #series-list', '<p class="empty">研究目录暂时无法载入，请稍后刷新。</p>');
    });

  function render() {
    var newest = pages[0];
    setText('hub-date', newest ? stamp(newest.updated_at || newest.published_at) + ' · HONG KONG' : '—');
    if (page === 'home') {
      setText('library-count', pages.length);
      setText('library-count-secondary', pages.length);
      renderTicker(homeRows(pages, 6));
      renderLatest(homeRows(pages, 4));
      renderHomeEarnings();
      renderHomeAxes();
    }
    if (page === 'library') renderLibrary();
    if (page === 'earnings') renderEarnings();
    if (page === 'map') renderMap();
    if (page === 'series') renderSeries();
  }

  function homeRows(source, limit) {
    var seen = {};
    return source.filter(function (item) {
      var key = item.series_id ? 'series:' + item.series_id : 'slug:' + item.slug;
      if (seen[key]) return false;
      seen[key] = true;
      return true;
    }).slice(0, limit);
  }

  function renderTicker(items) {
    var target = document.getElementById('ticker-items');
    if (!target) return;
    target.innerHTML = items.map(function (item) {
      return '<a href="' + esc(href(item)) + '"><b>' + esc(item.title || '') + '</b><small>' + esc(shortStamp(item)) + ' · ' + esc(axisName(item.axis)) + '</small></a>';
    }).join('');
  }

  function renderLatest(items) {
    var lead = document.getElementById('latest-lead');
    var target = document.getElementById('latest-list');
    if (!lead && !target) return;
    var primary = items[0];
    if (lead) {
      lead.innerHTML = primary ? '<a class="latest-feature" href="' + esc(href(primary)) + '"><span class="story-meta"><strong>' + esc(axisName(primary.axis)) + '</strong><span>' + esc(typeLabel(primary.content_type)) + '</span><time>' + esc(shortStamp(primary)) + '</time></span><h3>' + esc(primary.title || '') + '</h3><p>' + esc(primary.homepage_deck || primary.deck || '') + '</p><span class="story-more">阅读全文 <span aria-hidden="true">↗</span></span></a>' : '<p class="empty">暂无已批准的研究条目。</p>';
    }
    if (target) {
      var support = lead ? items.slice(1, 4) : items;
      target.innerHTML = support.map(function (item) {
        return '<a class="latest-row" href="' + esc(href(item)) + '"><time>' + esc(shortStamp(item)) + '</time><span class="latest-row__copy"><small>' + esc(axisName(item.axis)) + ' · ' + esc(typeLabel(item.content_type)) + '</small><strong>' + esc(item.title || '') + '</strong></span><span aria-hidden="true">↗</span></a>';
      }).join('');
    }
    var entry = document.getElementById('library-entry');
    if (entry) entry.textContent = '进入完整研究库 · ' + pages.length + ' 篇';
  }

  function renderHomeEarnings() {
    var target = document.getElementById('earnings-list');
    if (!target) return;
    var rows = pages.filter(isEarnings).slice(0, 3);
    if (!rows.length) {
      target.innerHTML = '<p class="empty">财报桌暂无已批准的研究。</p>';
      return;
    }
    var lead = rows[0];
    var company = String(lead.company || '').trim() || lead.title || '';
    var ticker = String(lead.ticker || '').trim();
    target.innerHTML = '<a class="earnings-feature" href="' + esc(href(lead)) + '"><span class="earnings-feature__eyebrow">Latest earnings research</span><p class="earnings-feature__meta">' + esc(shortStamp(lead)) + (ticker ? ' · ' + esc(ticker) : '') + ' · ' + esc(typeLabel(lead.content_type)) + '</p><h3>' + esc(company) + '</h3><p>' + esc(lead.homepage_deck || lead.deck || '') + '</p><span class="earnings-feature__read">阅读研究 ↗</span></a><div class="earnings-list">' + rows.slice(1).map(function (item) {
      var name = String(item.company || '').trim() || item.title || '';
      var symbol = String(item.ticker || '').trim();
      return '<a class="earnings-row" href="' + esc(href(item)) + '"><small>' + esc(shortStamp(item)) + (symbol ? ' · ' + esc(symbol) : '') + '</small><strong>' + esc(name) + '</strong><span>' + esc(item.title || '') + '</span></a>';
    }).join('') + '</div>';
  }

  function renderHomeAxes() {
    var target = document.getElementById('axis-list');
    if (!target) return;
    target.innerHTML = AXES.map(function (item, index) {
      var count = pages.filter(function (entry) { return entry.axis === item.id; }).length;
      return '<a class="axis-row" href="/library/?axis=' + encodeURIComponent(item.id) + '"><span class="axis-row__number">0' + (index + 1) + '</span><span class="axis-row__copy"><strong>' + esc(item.zh) + '</strong><small>' + esc(item.desc) + '</small></span><span class="axis-row__count">' + count + ' 篇</span></a>';
    }).join('');
  }

  function typeLabel(type) {
    var labels = {
      earnings: '财报研究',
      'earnings-deep-dive': '财报深度研究',
      'deep-dive': '深度研究',
      brief: '研究简报',
      interactive: '互动工具',
      tracker: '持续跟踪'
    };
    return labels[type] || '研究';
  }

  function renderLibrary() {
    var params = new URLSearchParams(location.search);
    axis = params.get('axis') || 'all';
    series = params.get('series') || '';
    var search = document.getElementById('search');
    if (search && !search.dataset.bound) {
      search.dataset.bound = '1';
      search.addEventListener('input', function () {
        query = String(search.value || '').trim().toLowerCase();
        paintLibrary();
      });
    }
    var filters = document.getElementById('axis-filters');
    if (filters) {
      var buttons = [{id: 'all', zh: '全部'}].concat(AXES);
      filters.innerHTML = buttons.map(function (item) {
        var count = item.id === 'all' ? pages.length : pages.filter(function (entry) { return entry.axis === item.id; }).length;
        var pressed = item.id === axis ? ' is-active' : '';
        return '<button type="button" class="' + pressed + '" data-axis="' + item.id + '">' + esc(item.zh) + ' ' + count + '</button>';
      }).join('');
      filters.onclick = function (event) {
        var button = event.target.closest('button');
        if (!button) return;
        axis = button.getAttribute('data-axis') || 'all';
        series = '';
        var url = axis === 'all' ? '/library/' : '/library/?axis=' + encodeURIComponent(axis);
        history.replaceState(null, '', url);
        paintLibrary();
      };
    }
    paintLibrary();
  }

  function paintLibrary() {
    var target = document.getElementById('library-list');
    if (!target) return;
    var rows = pages.filter(function (item) {
      if (axis !== 'all' && item.axis !== axis) return false;
      if (series && item.series_id !== series) return false;
      if (!query) return true;
      return haystack(item).indexOf(query) >= 0;
    });
    var note = document.getElementById('library-note');
    if (note) {
      var titled = rows[0] && rows[0].series_title;
      note.textContent = series ? ((titled || '系列') + ' · ' + rows.length + ' 篇') : (rows.length + ' 篇');
    }
    var filters = document.getElementById('axis-filters');
    if (filters) {
      filters.querySelectorAll('button').forEach(function (node) {
        node.classList.toggle('is-active', (node.getAttribute('data-axis') || 'all') === axis);
      });
    }
    target.innerHTML = rows.length ? rows.map(libraryRow).join('') : '<p class="empty">没有匹配的研究。</p>';
  }

  function libraryRow(item) {
    return '<a class="lib-row" href="' + esc(href(item)) + '"><time>' + esc(shortStamp(item)) + '</time><div><div class="kicker">' + esc(axisName(item.axis)) + '</div><h3>' + esc(item.title || '') + '</h3><p class="deck">' + esc(item.homepage_deck || item.deck || '') + '</p></div></a>';
  }

  function renderEarnings() {
    var target = document.getElementById('earnings-list');
    if (!target) return;
    var rows = pages.filter(isEarnings);
    target.innerHTML = rows.length ? rows.map(function (item) {
      var company = String(item.company || '').trim();
      var ticker = String(item.ticker || '').trim();
      var headline = company || item.title || '';
      var sub = company ? '<h3>' + esc(item.title || '') + '</h3>' : '';
      var meta = (ticker ? '<span class="ticker">' + esc(ticker) + '</span>' : '') + '<time>' + esc(stamp(item.updated_at || item.published_at)) + '</time>';
      return '<a class="earn-row" href="' + esc(href(item)) + '"><h2 class="company">' + esc(headline) + '</h2><p class="meta">' + meta + '</p>' + sub + '<p class="deck">' + esc(item.homepage_deck || item.deck || '') + '</p></a>';
    }).join('') : '<p class="empty">财报桌暂无已发布研究。</p>';
  }

  function renderMap() {
    var target = document.getElementById('axis-list');
    if (!target) return;
    target.innerHTML = AXES.map(function (item, index) {
      var count = pages.filter(function (entry) { return entry.axis === item.id; }).length;
      return '<a class="axis-row" href="/library/?axis=' + encodeURIComponent(item.id) + '"><b>0' + (index + 1) + '</b><div><strong>' + esc(item.zh) + '</strong><p class="deck">' + esc(item.desc) + '</p></div><span>' + count + ' 篇</span></a>';
    }).join('');
  }

  function renderSeries() {
    var target = document.getElementById('series-list');
    if (!target) return;
    var groups = {};
    pages.forEach(function (item) {
      if (!item.series_id) return;
      if (!groups[item.series_id]) groups[item.series_id] = {id: item.series_id, title: item.series_title || item.series_id, items: []};
      groups[item.series_id].items.push(item);
    });
    var list = Object.keys(groups).map(function (key) { return groups[key]; });
    list.sort(function (a, b) { return timeOf(b.items[0]) - timeOf(a.items[0]); });
    target.innerHTML = list.map(function (group) {
      return '<a class="series-row" href="/library/?series=' + encodeURIComponent(group.id) + '"><div><div class="kicker">' + group.items.length + ' 篇</div><h3>' + esc(group.title) + '</h3></div><span>进入系列</span></a>';
    }).join('');
  }

  function isEarnings(item) {
    return item.content_type === 'earnings' || item.content_type === 'earnings-deep-dive';
  }
  function axisName(id) {
    return (axisById[id] && axisById[id].zh) || '研究';
  }
  function href(item) {
    var path = item.path || '/' + item.slug + '/';
    return path.charAt(0) === '/' ? path : '/' + path;
  }
  function haystack(item) {
    return [item.title, item.homepage_deck, item.deck, item.tag, item.category, item.company, item.ticker, item.series_title, axisName(item.axis)].join(' ').toLowerCase();
  }
  function timeOf(item) {
    var value = Date.parse(item.updated_at || item.published_at || '');
    return isNaN(value) ? 0 : value;
  }
  function sortDesc(a, b) { return timeOf(b) - timeOf(a); }
  function stamp(value) {
    var match = String(value || '').match(/(\d{4})-(\d{2})-(\d{2})/);
    return match ? match[1] + '.' + match[2] + '.' + match[3] : '';
  }
  function shortStamp(item) {
    var full = stamp(item.updated_at || item.published_at || item.date);
    return full ? full.slice(5) : '';
  }
  function setText(id, value) {
    var node = document.getElementById(id);
    if (node) node.textContent = value;
  }
  function paint(selector, html) {
    document.querySelectorAll(selector).forEach(function (node) { node.innerHTML = html; });
  }
  function esc(value) {
    return String(value || '').replace(/[&<>"']/g, function (char) {
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char];
    });
  }
}());
