(()=>{'use strict';
const css='/assets/enya-reader-v1.css?v=20260909reader',js='/assets/enya-reader-v1.js?v=20260909reader';
function mount(){
  const main=document.querySelector('main,[role="main"],#main,#main-content,.brief,.page,.wrap');
  if(!main||document.querySelector('.enya-reader'))return Boolean(main);
  if(!document.querySelector('link[data-enya-reader-css]')){const link=document.createElement('link');link.rel='stylesheet';link.href=css;link.dataset.enyaReaderCss='';document.head.append(link)}
  if(!document.querySelector('script[data-enya-reader-script]')){const script=document.createElement('script');script.src=js;script.dataset.enyaReaderScript='';document.body.append(script)}
  return true;
}
let tries=0;function wait(){if(mount()||tries++>120)return;setTimeout(wait,100)}wait();
})();

