(function () {
  'use strict';

  var body = document.body;
  if (!body) return;
  var path = location.pathname.toLowerCase();
  var isExperience = body.classList.contains('kw-experience') || /xiaoxiao-block-world|blockcraft-game|solar-system-3d-explorer/.test(path);

  installDarkSurfaceContrast();
  body.classList.add(isExperience ? 'kw-experience' : 'kw-research');
  normalizeLegacyGates();
  installAccessGate();

  if (isExperience) {
    if (!document.getElementById('site-corner')) {
      var exp = document.createElement('a');
      exp.className = 'kw-experience-link';
      exp.href = '/';
      exp.textContent = 'E · 返回 EnyaClawd';
      body.insertBefore(exp, body.firstChild);
    }
    return;
  }

  var title = (document.querySelector('h1, .title, .top-title') || {}).textContent || document.title;
  title = title.replace(/\s+/g, ' ').trim();

  var rail = document.createElement('header');
  rail.className = 'kw-site-rail';
  rail.setAttribute('aria-label', 'EnyaClawd 全站导航');
  rail.innerHTML =
    '<div class="kw-site-rail__inner">' +
      '<a class="kw-site-rail__brand" href="/" aria-label="返回 EnyaClawd 研究首页">' +
        '<span class="kw-site-rail__mark">E</span>' +
        '<span class="kw-site-rail__wordmark">EnyaClawd<small>Kerwin Research</small></span>' +
      '</a>' +
      '<div class="kw-site-rail__context">' + escapeHtml(title) + '</div>' +
      '<div class="kw-site-rail__actions">' +
        '<a class="kw-site-rail__button" href="/#latest" title="最近更新">⌁ <span>最近更新</span></a>' +
        '<a class="kw-site-rail__button" href="/" title="研究首页">⌂ <span>研究首页</span></a>' +
      '</div>' +
    '</div><div class="kw-progress" aria-hidden="true"><span></span></div>';
  body.insertBefore(rail, body.firstChild);

  var brand = document.querySelector('.enya-brand');
  if (!brand) {
    brand = document.createElement('section');
    brand.className = 'enya-brand kw-enya-brand';
    brand.innerHTML =
      '<div class="enya-brand-name">EnyaClawd</div>' +
      '<div class="enya-brand-tagline">Enya：香港首个由 OpenClaw 打造的女性投顾 Agent</div>' +
      '<div class="enya-brand-models">底层模型：GPT 5.6 Sol 及 Claude Fable 付费版</div>' +
      '<div class="enya-brand-copy">Kerwin 确定研究主题、投资逻辑与最终校对；Enya 负责资料组织、可视化呈现与持续更新。我们希望把复杂产业链压缩成能被理解、被验证、被持续跟踪的研究地图。</div>';
    var footer = document.querySelector('footer, .footer');
    var shell = document.querySelector('.shell') || body;
    if (footer && footer.parentNode) footer.parentNode.insertBefore(brand, footer);
    else shell.appendChild(brand);
  } else {
    brand.classList.add('kw-enya-brand');
    var tagline = brand.querySelector('.enya-brand-tagline');
    if (!tagline) {
      tagline = document.createElement('div');
      tagline.className = 'enya-brand-tagline';
      tagline.textContent = 'Enya：香港首个由 OpenClaw 打造的女性投顾 Agent';
      brand.appendChild(tagline);
    }
    tagline.textContent = 'Enya：香港首个由 OpenClaw 打造的女性投顾 Agent';
    var modelLine = brand.querySelector('.enya-brand-models');
    if (!modelLine) {
      modelLine = document.createElement('div');
      modelLine.className = 'enya-brand-models';
      modelLine.textContent = '底层模型：GPT 5.6 Sol 及 Claude Fable 付费版';
      if (tagline.nextSibling) brand.insertBefore(modelLine, tagline.nextSibling);
      else brand.appendChild(modelLine);
    }
    modelLine.textContent = '底层模型：GPT 5.6 Sol 及 Claude Fable 付费版';
    var roleCopy = brand.querySelector('.enya-brand-copy');
    if (!roleCopy) {
      roleCopy = document.createElement('div');
      roleCopy.className = 'enya-brand-copy';
      brand.appendChild(roleCopy);
    }
    roleCopy.textContent = 'Kerwin 确定研究主题、投资逻辑与最终校对；Enya 负责证据组织、可视化呈现与持续维护。';
  }

  var topButton = document.createElement('button');
  topButton.className = 'kw-to-top';
  topButton.type = 'button';
  topButton.setAttribute('aria-label', '返回顶部');
  topButton.textContent = '↑';
  topButton.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  body.appendChild(topButton);

  var progress = rail.querySelector('.kw-progress span');
  var ticking = false;
  function updateScroll() {
    var max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    var ratio = Math.min(1, Math.max(0, scrollY / max));
    progress.style.width = (ratio * 100).toFixed(2) + '%';
    topButton.classList.toggle('is-visible', scrollY > 640);
    ticking = false;
  }
  addEventListener('scroll', function () {
    if (!ticking) { requestAnimationFrame(updateScroll); ticking = true; }
  }, { passive: true });
  updateScroll();

  document.querySelectorAll('a[target="_blank"]').forEach(function (link) {
    link.rel = 'noopener noreferrer';
  });

  function installAccessGate() {
    body.classList.remove('kw-gate-granted');
    body.classList.add('kw-gate-pending');

    var gate = document.createElement('aside');
    gate.className = 'kw-access-gate';
    gate.setAttribute('aria-label', '页面访问互动');
    var pageTitle = String(document.title || 'Kerwin Research').split(/[｜|]/)[0].trim();
    gate.innerHTML =
      '<div class="kw-access-gate__paper">' +
        '<div class="kw-access-gate__masthead"><span>Kerwin Research Hub</span><span>Interactive Entry</span></div>' +
        '<div class="kw-access-gate__body">' +
          '<div class="kw-access-gate__seal" aria-hidden="true"><span>Kerwin</span><small>Research Hub</small></div>' +
          '<div class="kw-access-gate__copy">' +
            '<div class="kw-access-gate__kicker">Reader Access</div>' +
            '<div class="kw-access-gate__title">' + escapeHtml(pageTitle) + '</div>' +
            '<form class="kw-access-gate__form">' +
              '<label for="kw-access-key">输入 “k” 即可显示，不分大小写</label>' +
              '<div class="kw-access-gate__field">' +
                '<input id="kw-access-key" type="text" inputmode="text" maxlength="1" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="k" aria-describedby="kw-access-status">' +
                '<span>Auto enter</span>' +
              '</div>' +
              '<p class="kw-access-gate__status" id="kw-access-status" role="status" aria-live="polite"></p>' +
            '</form>' +
          '</div>' +
        '</div>' +
        '<div class="kw-access-gate__foot"><span>Enya：香港首个由 OpenClaw 打造的女性投顾 Agent</span><span>底层模型：GPT 5.6 Sol 及 Claude Fable 付费版</span></div>' +
      '</div>';
    body.insertBefore(gate, body.firstChild);

    var form = gate.querySelector('form');
    var input = gate.querySelector('input');
    var status = gate.querySelector('.kw-access-gate__status');
    var unlocking = false;
    var clearTimer = 0;

    function openPage() {
      if (unlocking) return;
      unlocking = true;
      if (clearTimer) clearTimeout(clearTimer);
      gate.classList.add('is-unlocking');
      status.textContent = '正在展开页面…';
      setTimeout(function () {
        body.classList.remove('kw-gate-pending');
        body.classList.add('kw-gate-granted');
        gate.setAttribute('aria-hidden', 'true');
        var firstFocus = document.querySelector('.kw-site-rail a, .kw-experience-link, main a, main button');
        if (firstFocus) firstFocus.focus();
      }, 140);
    }

    function checkInput() {
      var value = String(input.value || '').trim().toLowerCase();
      if (value === 'k') {
        openPage();
        return;
      }
      if (value) {
        status.textContent = '请输入 “k”，大小写均可。';
        if (clearTimer) clearTimeout(clearTimer);
        clearTimer = setTimeout(function () {
          if (!unlocking) {
            input.value = '';
            input.focus();
          }
        }, 260);
      }
    }

    input.addEventListener('input', checkInput);
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      checkInput();
    });
    setTimeout(function () { if (!unlocking) input.focus(); }, 60);
  }

  function normalizeLegacyGates() {
    var oldOverlays = document.querySelectorAll('#gate-overlay, #gate-prompt, #kw-legacy-gate-overlay');
    for (var i = 0; i < oldOverlays.length; i += 1) {
      if (oldOverlays[i].parentNode) oldOverlays[i].parentNode.removeChild(oldOverlays[i]);
    }
    var oldContent = document.querySelectorAll('.gated-content, #main-content, #gate-content');
    for (var j = 0; j < oldContent.length; j += 1) {
      oldContent[j].classList.add('visible');
      oldContent[j].style.display = 'block';
    }
    body.style.removeProperty('overflow');
    document.documentElement.style.removeProperty('overflow');
    clearLegacyGateStorage(window.sessionStorage);
    clearLegacyGateStorage(window.localStorage);
  }

  function clearLegacyGateStorage(storage) {
    try {
      for (var i = storage.length - 1; i >= 0; i -= 1) {
        var key = storage.key(i);
        if (key && /gate/i.test(key)) storage.removeItem(key);
      }
    } catch (error) {
      // Storage can be unavailable in constrained in-app browsers; the gate does not depend on it.
    }
  }

  function installDarkSurfaceContrast() {
    var lightText = '#fffaf5';
    var originals = typeof WeakMap === 'function' ? new WeakMap() : null;
    var queuedRoots = [];
    var scheduled = false;

    function parseColor(value) {
      var text = String(value || '').trim().toLowerCase();
      if (!text || text === 'transparent') return { r: 0, g: 0, b: 0, a: 0 };
      var match = text.match(/rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)/);
      if (!match) {
        var hex = text.match(/#([0-9a-f]{3,8})\b/i);
        if (!hex) return null;
        var hexValue = hex[1];
        if (hexValue.length === 3 || hexValue.length === 4) hexValue = hexValue.replace(/./g, function (digit) { return digit + digit; });
        if (hexValue.length !== 6 && hexValue.length !== 8) return null;
        return {
          r: parseInt(hexValue.slice(0, 2), 16),
          g: parseInt(hexValue.slice(2, 4), 16),
          b: parseInt(hexValue.slice(4, 6), 16),
          a: hexValue.length === 8 ? parseInt(hexValue.slice(6, 8), 16) / 255 : 1
        };
      }
      return {
        r: Number(match[1]),
        g: Number(match[2]),
        b: Number(match[3]),
        a: match[4] ? (/%$/.test(match[4]) ? Number(match[4].slice(0, -1)) / 100 : Number(match[4])) : 1
      };
    }

    function relativeLuminance(color) {
      function channel(value) {
        value /= 255;
        return value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
      }
      return 0.2126 * channel(color.r) + 0.7152 * channel(color.g) + 0.0722 * channel(color.b);
    }

    function contrastRatio(first, second) {
      var a = relativeLuminance(first);
      var b = relativeLuminance(second);
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    }

    function backgroundColors(element) {
      var node = element;
      while (node && node.nodeType === 1) {
        var style = getComputedStyle(node);
        var image = String(style.backgroundImage || '');
        var tokens = image.match(/rgba?\([^)]*\)|#[0-9a-f]{3,8}\b/gi) || [];
        var colors = [];
        for (var i = 0; i < tokens.length; i += 1) {
          var stop = parseColor(tokens[i]);
          if (stop && stop.a >= 0.72) colors.push(stop);
        }
        var solid = parseColor(style.backgroundColor);
        if (solid && solid.a >= 0.72) colors.push(solid);
        if (colors.length) return colors;
        node = node.parentElement;
      }
      return [{ r: 255, g: 255, b: 255, a: 1 }];
    }

    function carriesText(element) {
      if (/^(INPUT|TEXTAREA|BUTTON|SELECT|OPTION)$/.test(element.tagName)) return true;
      for (var i = 0; i < element.childNodes.length; i += 1) {
        var child = element.childNodes[i];
        if (child.nodeType === 3 && String(child.nodeValue || '').trim()) return true;
      }
      return false;
    }

    function restoreOriginal(element) {
      if (!originals || !originals.has(element)) return;
      var original = originals.get(element);
      if (original.value) element.style.setProperty('color', original.value, original.priority);
      else element.style.removeProperty('color');
      element.removeAttribute('data-kw-contrast-fixed');
    }

    function applyLightText(element) {
      if (originals && !originals.has(element)) {
        originals.set(element, {
          value: element.style.getPropertyValue('color'),
          priority: element.style.getPropertyPriority('color')
        });
      }
      element.style.setProperty('color', lightText, 'important');
      element.setAttribute('data-kw-contrast-fixed', 'true');
    }

    function inspect(element) {
      if (!element || element.nodeType !== 1 || !carriesText(element)) return;
      if (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(element.tagName)) return;
      restoreOriginal(element);
      var style = getComputedStyle(element);
      if (style.display === 'none' || Number(style.opacity || 1) === 0) return;
      var foreground = parseColor(style.color);
      if (!foreground || foreground.a < 0.7) return;
      var backgrounds = backgroundColors(element);
      var needsFix = false;
      for (var i = 0; i < backgrounds.length; i += 1) {
        var background = backgrounds[i];
        if (relativeLuminance(background) <= 0.18 && contrastRatio(foreground, background) < 4.5) {
          needsFix = true;
          break;
        }
      }
      if (needsFix) applyLightText(element);
      else if (originals) originals.delete(element);
    }

    function scan(root) {
      if (!root || root.nodeType !== 1) return;
      inspect(root);
      var elements = root.querySelectorAll('*');
      for (var i = 0; i < elements.length; i += 1) inspect(elements[i]);
    }

    function flush() {
      scheduled = false;
      var roots = queuedRoots.slice();
      queuedRoots.length = 0;
      for (var i = 0; i < roots.length; i += 1) scan(roots[i]);
    }

    function requestScan(root) {
      root = root && root.nodeType === 1 ? root : body;
      for (var i = 0; i < queuedRoots.length; i += 1) {
        if (queuedRoots[i] === root || queuedRoots[i].contains(root)) return;
      }
      queuedRoots.push(root);
      if (scheduled) return;
      scheduled = true;
      (window.requestAnimationFrame || function (callback) { return setTimeout(callback, 16); })(flush);
    }

    if (window.MutationObserver) {
      new MutationObserver(function (records) {
        for (var i = 0; i < records.length; i += 1) {
          var record = records[i];
          if (record.type === 'attributes') requestScan(record.target);
          for (var j = 0; j < record.addedNodes.length; j += 1) requestScan(record.addedNodes[j]);
        }
      }).observe(body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'hidden'] });
    }
    addEventListener('load', function () { requestScan(body); });
    addEventListener('resize', function () { requestScan(body); }, { passive: true });
    requestScan(body);
  }

  function escapeHtml(value) {
    var node = document.createElement('div');
    node.textContent = value || '';
    return node.innerHTML;
  }
})();
