(function () {
  'use strict';

  var path = location.pathname.toLowerCase();
  var isExperience = /xiaoxiao-block-world|solar-system-3d-explorer/.test(path);
  var body = document.body;
  if (!body) return;

  if (isExperience) {
    body.classList.add('kw-experience');
    if (!document.getElementById('site-corner')) {
      var exp = document.createElement('a');
      exp.className = 'kw-experience-link';
      exp.href = '/';
      exp.textContent = 'E · 返回 EnyaClawd';
      body.insertBefore(exp, body.firstChild);
    }
    return;
  }

  body.classList.add('kw-research');

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

  function escapeHtml(value) {
    var node = document.createElement('div');
    node.textContent = value || '';
    return node.innerHTML;
  }
})();
