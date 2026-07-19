(function(){
'use strict';
var body=document.body;if(!body)return;
var path=location.pathname.toLowerCase();
var isExperience=/xiaoxiao-block-world|solar-system-3d-explorer/.test(path);
body.classList.add(isExperience?'kw-experience':'kw-research');
installAccessGate();
if(isExperience){
 if(!document.getElementById('site-corner')){var exp=document.createElement('a');exp.className='kw-experience-link';exp.href='/';exp.textContent='E · 返回 EnyaClawd';body.insertBefore(exp,body.firstChild);}return;
}
var title=(document.querySelector('h1,.title,.top-title')||{}).textContent||document.title;title=title.replace(/\s+/g,' ').trim();
var rail=document.createElement('header');rail.className='kw-site-rail';rail.setAttribute('aria-label','EnyaClawd 全站导航');
rail.innerHTML='<div class="kw-site-rail__inner"><a class="kw-site-rail__brand" href="/" aria-label="返回 EnyaClawd 研究首页"><span class="kw-site-rail__mark">E</span><span class="kw-site-rail__wordmark">EnyaClawd<small>Kerwin Research</small></span></a><div class="kw-site-rail__context">'+escapeHtml(title)+'</div><div class="kw-site-rail__actions"><a class="kw-site-rail__button" href="/#latest" title="最近更新">⌁ <span>最近更新</span></a><a class="kw-site-rail__button" href="/" title="研究首页">⌂ <span>研究首页</span></a></div></div><div class="kw-progress" aria-hidden="true"><span></span></div>';
body.insertBefore(rail,body.firstChild);
var brand=document.querySelector('.enya-brand');
if(!brand){brand=document.createElement('section');brand.className='enya-brand kw-enya-brand';brand.innerHTML='<div class="enya-brand-name">EnyaClawd</div><div class="enya-brand-tagline">Enya：香港首个由 OpenClaw 打造的女性投顾 Agent</div><div class="enya-brand-models">底层模型：GPT 5.6 Sol 及 Claude Fable 付费版</div><div class="enya-brand-copy">Kerwin 确定研究主题、投资逻辑与最终校对；Enya 负责资料组织、可视化呈现与持续更新。我们希望把复杂产业链压缩成能被理解、被验证、被持续跟踪的研究地图。</div>';var footer=document.querySelector('footer,.footer');var shell=document.querySelector('.shell')||body;if(footer&&footer.parentNode)footer.parentNode.insertBefore(brand,footer);else shell.appendChild(brand);}else{
 brand.classList.add('kw-enya-brand');
 var tagline=brand.querySelector('.enya-brand-tagline');if(!tagline){tagline=document.createElement('div');tagline.className='enya-brand-tagline';tagline.textContent='Enya：香港首个由 OpenClaw 打造的女性投顾 Agent';brand.appendChild(tagline);}
 var modelLine=brand.querySelector('.enya-brand-models');if(!modelLine){modelLine=document.createElement('div');modelLine.className='enya-brand-models';modelLine.textContent='底层模型：GPT 5.6 Sol 及 Claude Fable 付费版';if(tagline.nextSibling)brand.insertBefore(modelLine,tagline.nextSibling);else brand.appendChild(modelLine);}
}
var topButton=document.createElement('button');topButton.className='kw-to-top';topButton.type='button';topButton.setAttribute('aria-label','返回顶部');topButton.textContent='↑';topButton.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});body.appendChild(topButton);
var progress=rail.querySelector('.kw-progress span'),ticking=false;function updateScroll(){var max=Math.max(1,document.documentElement.scrollHeight-innerHeight);var ratio=Math.min(1,Math.max(0,scrollY/max));progress.style.width=(ratio*100).toFixed(2)+'%';topButton.classList.toggle('is-visible',scrollY>640);ticking=false;}addEventListener('scroll',function(){if(!ticking){requestAnimationFrame(updateScroll);ticking=true;}},{passive:true});updateScroll();
document.querySelectorAll('a[target="_blank"]').forEach(function(link){link.rel='noopener noreferrer';});
function installAccessGate(){
 body.classList.remove('kw-gate-granted');body.classList.add('kw-gate-pending');
 var gate=document.createElement('aside');gate.className='kw-access-gate';gate.setAttribute('aria-label','页面访问互动');var pageTitle=String(document.title||'Kerwin Research').split(/[｜|]/)[0].trim();
 gate.innerHTML='<div class="kw-access-gate__paper"><div class="kw-access-gate__masthead"><span>Kerwin Research Hub</span><span>Interactive Entry</span></div><div class="kw-access-gate__body"><div class="kw-access-gate__seal" aria-hidden="true"><span>Kerwin</span><small>Research Hub</small></div><div class="kw-access-gate__copy"><div class="kw-access-gate__kicker">Reader Access</div><div class="kw-access-gate__title">'+escapeHtml(pageTitle)+'</div><form class="kw-access-gate__form"><label for="kw-access-key">输入 k 即可显示</label><div class="kw-access-gate__field"><input id="kw-access-key" type="text" inputmode="text" maxlength="1" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="k" aria-describedby="kw-access-status"><span>Auto enter</span></div><p class="kw-access-gate__status" id="kw-access-status" role="status" aria-live="polite">大小写均可</p></form></div></div><div class="kw-access-gate__foot"><span>Enya：香港首个由 OpenClaw 打造的女性投顾 Agent</span><span>底层模型：GPT 5.6 Sol 及 Claude Fable 付费版</span></div></div>';
 body.insertBefore(gate,body.firstChild);var form=gate.querySelector('form'),input=gate.querySelector('input'),status=gate.querySelector('.kw-access-gate__status'),unlocking=false,clearTimer=0;
 function openPage(){if(unlocking)return;unlocking=true;if(clearTimer)clearTimeout(clearTimer);gate.classList.add('is-unlocking');status.textContent='正在展开页面…';setTimeout(function(){body.classList.remove('kw-gate-pending');body.classList.add('kw-gate-granted');gate.setAttribute('aria-hidden','true');var firstFocus=document.querySelector('.kw-site-rail a,.kw-experience-link,main a,main button');if(firstFocus)firstFocus.focus();},140);}
 function checkInput(){var value=String(input.value||'').trim().toLowerCase();if(value==='k'){openPage();return;}if(value){status.textContent='请输入 “k”，大小写均可。';if(clearTimer)clearTimeout(clearTimer);clearTimer=setTimeout(function(){if(!unlocking){input.value='';input.focus();}},260);}}
 input.addEventListener('input',checkInput);form.addEventListener('submit',function(e){e.preventDefault();checkInput();});setTimeout(function(){if(!unlocking)input.focus();},60);
}
function escapeHtml(value){var node=document.createElement('div');node.textContent=value||'';return node.innerHTML;}
})();