// Official sample presentation, evaluated lazily by the server's Decisions API.
(() => {
  const modes = {
    dent: {tab:'dent-tab', panel:'dent-panel', title:'Does this item have a dent?', selector:'.number', count:5},
    cancellation: {tab:'cancel-tab', panel:'cancel-panel', title:'Does this customer want to cancel their subscription?', selector:'.cancel-number', count:3, quotes:'.cancel-quote'},
    answer_relevance: {tab:'relevance-tab', panel:'relevance-panel', title:'Does the answer directly address the question?', selector:'.relevance-number', count:3, quotes:'.relevance-quote'}
  };
  const images = ['can','bottle','travel-cup','dented-mug','dimpled-tin'];
  const imageElements = new Map([...document.querySelectorAll('[data-item] img')].map(img => [img.parentElement.dataset.item,img.cloneNode()]));
  let mode='dent', paused=matchMedia('(prefers-reduced-motion: reduce)').matches, timer, generation=0, ready=false;
  const indexes = {dent:0,cancellation:0,answer_relevance:0};
  const pending = new Map();
  function notify(state, message) { parent.postMessage({type:'decisions-api-status',state,message},location.origin); }
  function schedule() {
    clearTimeout(timer);
    if (!paused && ready && !document.hidden) timer=setTimeout(() => {indexes[mode]=(indexes[mode]+1)%modes[mode].count; show();},5000);
  }
  async function fetchSample(selected,index) {
    const key=selected+':'+index;
    if (!pending.has(key)) {
      const promise=fetch('/api/predicate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:selected,index})})
        .then(async response => {const data=await response.json(); if(!response.ok) throw Error(data.error || 'API 호출에 실패했습니다.'); if(data.source!=='decisions_api' || !Number.isFinite(data.probability) || data.probability<0 || data.probability>1) throw Error('올바르지 않은 API 응답입니다.'); return data;})
        .finally(() => pending.delete(key));
      pending.set(key,promise);
    }
    return pending.get(key);
  }
  async function show() {
    clearTimeout(timer); ready=false;
    const version=++generation, selected=mode, index=indexes[selected], config=modes[selected];
    for(const [name,item] of Object.entries(modes)) {
      document.getElementById(item.panel).hidden=name!==mode;
      const tab=document.getElementById(item.tab); tab.setAttribute('aria-selected',String(name===mode)); tab.tabIndex=name===mode?0:-1;
    }
    document.getElementById('probability-example-title').textContent=config.title;
    const panel=document.getElementById(config.panel), number=panel.querySelector(config.selector), output=number.closest('[data-label-value]');
    number.textContent='—'; output.dataset.labelValue=''; output.setAttribute('aria-label','probability: API 응답 대기');
    if(selected==='dent') {
      const carousel=panel.querySelector('.carousel'); carousel.replaceChildren(); carousel.dataset.current=images[index];
      for(const [position,offset] of [['previous',-1],['current',0],['next',1]]) {
        const name=images[(index+offset+images.length)%images.length], slide=document.createElement('div');
        slide.className='slide'; slide.dataset.position=position; slide.dataset.item=name; slide.setAttribute('aria-hidden',String(offset!==0)); slide.append(imageElements.get(name).cloneNode()); carousel.append(slide);
      }
    } else {
      panel.querySelectorAll(config.quotes).forEach((quote,i) => {quote.style.opacity=i===index?'1':'0'; quote.style.transform='none'; quote.setAttribute('aria-hidden',String(i!==index));});
    }
    notify('loading','실제 Decisions API로 판단 중입니다…');
    try {
      const result=await fetchSample(selected,index);
      if(version!==generation) return;
      number.textContent=result.probability.toFixed(2); output.dataset.labelValue=String(result.probability); output.setAttribute('aria-label','probability: '+result.probability);
      notify('success', '실제 Decisions API 응답 · probability (0~1)' + (result.cached?' · 이전 실제 응답 재사용':''));
      ready=true; schedule();
    } catch(error) {if(version===generation) notify('error',error.message);}
  }
  function select(name) {if(name!==mode) {mode=name; show();}}
  function setPaused(value) {paused=value; document.querySelector('.carousel').setAttribute('aria-pressed',String(paused)); schedule();}
  for(const [name,config] of Object.entries(modes)) document.getElementById(config.tab).addEventListener('click',()=>select(name));
  document.querySelector('.carousel').addEventListener('click',()=>{setPaused(!paused); parent.postMessage({type:'decisions-playback',paused},location.origin);});
  window.addEventListener('message',event=>{
    if(event.source!==parent || event.origin!==location.origin) return;
    const data=event.data;
    if(data?.type==='decisions-select') {const name=Object.keys(modes).find(name=>modes[name].tab===data.id); if(name) select(name);}
    if(data?.type==='decisions-playback' && typeof data.paused==='boolean') setPaused(data.paused);
    if(data?.type==='decisions-retry') show();
  });
  document.addEventListener('visibilitychange',schedule);
  new ResizeObserver(()=>parent.postMessage({type:'decisions-height',height:document.documentElement.scrollHeight},location.origin)).observe(document.querySelector('main'));
  show();
})();
