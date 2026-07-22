(function(){
'use strict';
var slug='ai-memory-hbm-nand-cmx-20260722';
function esc(value){var node=document.createElement('div');node.textContent=value||'';return node.innerHTML;}
function href(p){return p.source==='codex'?'/'+p.slug+'.html':'/'+p.slug+'/';}
function apply(){fetch('/registry.json?v='+Date.now(),{cache:'no-store'}).then(function(r){return r.json();}).then(function(items){var p=(items||[]).find(function(x){return x.slug===slug;});if(!p)return;var main=document.getElementById('feature-main');if(main){main.innerHTML='<div class="feature-main__visual"><div class="feature-orbit"><i></i><i></i><i></i></div></div><div class="feature-main__content"><div class="story-meta"><span class="story-tag">Lead Research</span><span>'+esc(p.date||'')+'</span><span>'+esc(p.tag||'Research')+'</span></div><h3>'+esc(p.title||'')+'</h3><p>'+esc(p.deck||'')+'</p></div><a class="story-link" href="'+href(p)+'" aria-label="阅读 '+esc(p.title||'')+'"></a>';}
var updated=document.getElementById('stat-updated');if(updated)updated.textContent='7.22';
}).catch(function(){});}
function start(){setTimeout(apply,650);setTimeout(apply,1600);}
if(document.readyState==='complete')start();else addEventListener('load',start);
})();