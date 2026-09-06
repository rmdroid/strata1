'use strict';
(() => {
  const config = JSON.parse(document.getElementById('page-config').textContent);
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const store = {get(k){try{return localStorage.getItem(k)}catch{return null}},set(k,v){try{localStorage.setItem(k,v)}catch{}}};
  let analyticsAllowed = store.get('strata-privacy-v2') === 'analytics';
  function startAnalytics(){
    if(!analyticsAllowed || $('#strata-analytics') || !/^https?:$/.test(location.protocol)) return;
    const s=document.createElement('script');s.id='strata-analytics';s.defer=true;
    s.src='https://cv.rm-on.de/script.js';s.dataset.websiteId='28f6bd1a-632b-4037-97cf-2e41681101e1';document.head.append(s);
  }
  function track(event,data={}) {if(analyticsAllowed && window.umami) window.umami.track(event,{language:config.lang,...data});}
  const notice=$('#privacy-notice');
  if(notice && !store.get('strata-privacy-v2')) notice.hidden=false;
  $$('[data-consent]').forEach(b=>b.addEventListener('click',()=>{
    const previouslyAllowed=analyticsAllowed;
    analyticsAllowed=b.dataset.consent==='analytics';store.set('strata-privacy-v2',b.dataset.consent);
    notice.hidden=true;
    if(analyticsAllowed)startAnalytics();else if(previouslyAllowed)location.reload();
  }));
  $$('[data-privacy-settings]').forEach(b=>b.addEventListener('click',()=>{notice.hidden=false;$('[data-consent]',notice).focus()}));
  startAnalytics();
  $$('[data-store]').forEach(a=>a.addEventListener('click',()=>track('app-store-click',{placement:a.dataset.store})));
  $$('[data-layer-select]').forEach(button=>button.addEventListener('click',()=>{
    const index=Number(button.dataset.layerSelect);
    $$('[data-layer-select]').forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
    $$('.layer').forEach(el=>el.classList.toggle('is-active',Number(el.dataset.layerIndex)===index));
    $('#layer-caption').textContent=config.categories[index].detail;
  }));
  let category=0,format='csv',currentText='';
  const dates=['2026-03-01','2026-03-02','2026-03-03','2026-03-04'];
  const values=[[8240,9106,7652,10283],[7.4,8.1,6.8,7.7],[62,60,64,61],[72.4,72.3,72.5,72.2],[1850,2100,1900,2200],[10,15,10,20]];
  function renderExport(){
    if(!$('#export-output'))return;
    const c=config.categories[category];
    const rows=dates.map((date,i)=>({date,type:c.metric,value:values[category][i],unit:c.unit}));
    const headers=config.headers;
    const out=$('#export-output');out.replaceChildren();
    if(format==='csv'){
      const table=document.createElement('table');table.setAttribute('aria-label',config.tableLabel);
      const thead=document.createElement('thead'),tr=document.createElement('tr');
      headers.forEach(h=>{const th=document.createElement('th');th.scope='col';th.textContent=h;tr.append(th)});thead.append(tr);table.append(thead);
      const tbody=document.createElement('tbody');
      rows.forEach(row=>{const tr=document.createElement('tr');Object.values(row).forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td)});tbody.append(tr)});
      table.append(tbody);out.append(table);
      currentText=['date,type,value,unit',...rows.map(r=>Object.values(r).join(','))].join('\n')+'\n';
    } else {
      currentText=format==='json'?JSON.stringify({example:true,category:c.id,records:rows},null,2):'# '+c.name+' — '+config.sample+'\n\n| '+headers.join(' | ')+' |\n| --- | --- | --- | --- |\n'+rows.map(r=>'| '+Object.values(r).join(' | ')+' |').join('\n')+'\n';
      const pre=document.createElement('pre');pre.textContent=currentText;out.append(pre);
    }
    $('#export-title').textContent=config.formats[format].title;
    $('#export-desc').textContent=config.formats[format].desc;
    $('#file-label').textContent='strata-example-'+c.id+'.'+(format==='markdown'?'md':format);
    $$('[data-category]').forEach((b,i)=>b.setAttribute('aria-pressed',String(i===category)));
    $$('[data-format]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.format===format)));
  }
  $$('[data-category]').forEach(b=>b.addEventListener('click',()=>{category=Number(b.dataset.category);renderExport();track('export-category',{category:config.categories[category].id})}));
  $$('[data-format]').forEach(b=>b.addEventListener('click',()=>{format=b.dataset.format;renderExport();track('export-format',{format})}));
  $('#download-sample')?.addEventListener('click',()=>{
    const mime={csv:'text/csv',json:'application/json',markdown:'text/markdown'}[format];
    const blob=new Blob([currentText],{type:mime+';charset=utf-8'});const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download=$('#file-label').textContent;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);track('sample-download',{format});
  });
  renderExport();
  let dialogTrigger=null;
  function openDialog(dialog,trigger){if(!dialog)return;dialogTrigger=trigger;dialog.showModal();document.body.classList.add('modal-open')}
  function closeDialog(dialog){dialog.close()}
  $$('dialog').forEach(dialog=>{
    $$('[data-close]',dialog).forEach(b=>b.addEventListener('click',()=>closeDialog(dialog)));
    dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeDialog(dialog)}});
    dialog.addEventListener('close',()=>{document.body.classList.remove('modal-open');dialogTrigger?.focus()});
  });
  $$('[data-contact]').forEach(b=>b.addEventListener('click',e=>{
    const dialog=$('#contact-dialog');if(!dialog)return;e.preventDefault();
    const form=$('#contact-form');form.elements.purpose.value=b.dataset.contact==='updates'?'updates':'support';syncPurpose();
    $('#form-status').textContent='';openDialog(dialog,b);
  }));
  let shot=0;
  function renderShot(){
    const data=config.screens[shot];$('#gallery-image').src='assets/'+config.lang+'/'+data.file+'.webp';$('#gallery-image').alt=data.title;$('#gallery-image').width=data.width;$('#gallery-image').height=data.height;
    $('#gallery-title').textContent=data.title;$('#gallery-caption').textContent=(shot+1)+' / '+config.screens.length+' · '+config.originalScreens;
  }
  $$('[data-shot]').forEach(b=>b.addEventListener('click',()=>{shot=Number(b.dataset.shot);renderShot();openDialog($('#gallery-dialog'),b)}));
  $$('[data-gallery-step]').forEach(b=>b.addEventListener('click',()=>{shot=(shot+Number(b.dataset.galleryStep)+config.screens.length)%config.screens.length;renderShot()}));
  $('#gallery-dialog')?.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();shot=(shot+(e.key==='ArrowRight'?1:-1)+config.screens.length)%config.screens.length;renderShot()}});
  const form=$('#contact-form');
  function syncPurpose(){if(!form)return;const newsletter=form.elements.purpose.value==='updates';$('#message-field').hidden=newsletter;form.elements.message.required=!newsletter;$('#consent-copy').textContent=newsletter?config.newsletterConsent:config.contactConsent;form.elements.consent.checked=false;$('#form-status').textContent=''}
  form?.elements.purpose.addEventListener('change',syncPurpose);
  form?.addEventListener('submit',async e=>{
    e.preventDefault();if(!form.reportValidity())return;
    if(form.elements.website.value)return;
    const submit=$('#form-submit'),status=$('#form-status'),isNewsletter=form.elements.purpose.value==='updates';
    const name=form.elements.name.value.trim(),email=form.elements.email.value.trim(),message=form.elements.message.value.trim();
    if(!email||(!isNewsletter&&!message)){status.textContent=config.validation;status.className='form-status error';return}
    submit.disabled=true;status.className='form-status';status.textContent=config.sending;
    const intent=isNewsletter?'Strata App Updates / Newsletter':'Strata App Support';
    const page=location.origin+location.pathname;
    const payload={name:name||email,email,message:isNewsletter?intent+'\nName: '+(name||email)+'\nE-Mail: '+email+'\nQuelle: Strata App Landingpage\nSeite: '+page:message+'\n\nQuelle: Strata App Support\nSeite: '+page,source:isNewsletter?'strata-landingpage-updates':'strata-landingpage-support',page,interest:intent,language:config.lang,consent:true};
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),15000);
    try{
      const response=await fetch('https://n8n.top-beraternetzwerk.de/webhook/termine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:controller.signal});
      if(!response.ok)throw Error('request_failed');
      form.reset();syncPurpose();status.className='form-status';status.textContent=config.sent;track('contact-submitted',{purpose:isNewsletter?'updates':'support'});
    }catch{status.className='form-status error';status.textContent=config.failed}
    finally{clearTimeout(timeout);submit.disabled=false}
  });
})();
