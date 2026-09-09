(()=>{'use strict';
const configs=[
  {ids:['employees','adoption','requests','days','inputTokens','outputTokens','inputPrice','outputPrice'],outputs:['annualCost','monthlyCost','requestCount','perEmployee'],message:'请检查员工数、采用率、请求量、工作日、Token 与价格；数值必须为有限的非负数，采用率不能超过 100%。'},
  {ids:['tokens','layers','kvheads','precision'],outputs:['kvGb','iphoneEq','pbSessions'],message:'请检查 Token、层数和 KV Heads；它们必须为有限的正数，KV 精度需使用支持的选项。'}
];
const config=configs.find(item=>item.ids.every(id=>document.getElementById(id)));if(!config)return;
const fields=config.ids.map(id=>document.getElementById(id));const defaults=fields.map(field=>field.defaultValue);
const section=fields[0].closest('section')||document.body;const host=section.querySelector('.calculator,.calc')||fields[0].parentElement;
const tools=document.createElement('div');tools.className='enya-model-tools';tools.innerHTML='<button type="button" data-reset>恢复原始假设</button><span class="enya-reader__note">交互测算仅用于建立量级感，不代表公司实际合同或财务预测。</span><span class="enya-model-message" role="status" aria-live="polite"></span>';host.before(tools);
const status=tools.querySelector('.enya-model-message');const reset=tools.querySelector('[data-reset]');
fields.forEach((field,index)=>{const label=field.closest('.field')?.querySelector('label');if(label&&!field.getAttribute('aria-label'))field.setAttribute('aria-label',label.textContent.trim());field.dataset.enyaDefault=defaults[index]});
function values(){return Object.fromEntries(fields.map(field=>[field.id,Number(field.value)]))}
function valid(){const v=values();if(Object.values(v).some(value=>!Number.isFinite(value)))return false;if(config.ids[0]==='employees')return v.employees>0&&v.adoption>=0&&v.adoption<=100&&v.requests>=0&&v.days>0&&v.inputTokens>=0&&v.outputTokens>=0&&v.inputPrice>=0&&v.outputPrice>=0&&Number.isFinite(v.employees*v.adoption/100*v.requests*v.days*((v.inputTokens*v.inputPrice+v.outputTokens*v.outputPrice)/1000000));return v.tokens>0&&v.layers>0&&v.kvheads>0&&[2,1,.5].includes(v.precision)&&Number.isFinite(v.tokens*v.layers*2*v.kvheads*128*v.precision)}
function clearOutputs(){config.outputs.forEach(id=>{const el=document.getElementById(id);if(el)el.textContent='—'})}
function check(){const ok=valid();fields.forEach(field=>{if(ok)field.removeAttribute('aria-invalid');else field.setAttribute('aria-invalid','true');if(ok)field.removeAttribute('aria-errormessage');else field.setAttribute('aria-errormessage','enya-model-message')});document.body.classList.toggle('enya-model-invalid',!ok);status.id='enya-model-message';status.textContent=ok?'当前假设可计算。':config.message;if(!ok)clearOutputs();return ok}
fields.forEach(field=>field.addEventListener('input',()=>queueMicrotask(check),{capture:true}));fields.forEach(field=>field.addEventListener('change',check));reset.addEventListener('click',()=>{fields.forEach((field,index)=>{field.value=defaults[index];field.dispatchEvent(new Event('input',{bubbles:true}))});check()});check();
})();
