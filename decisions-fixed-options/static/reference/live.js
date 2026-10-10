(() => {
  const configs = {
    driving: {title:'Which lane should the car choose?', labels:['Lane 1','Lane 2','Lane 3']},
    routing: {title:'Which team should handle this?', labels:['Billing','Technical support','Account access']},
    document: {title:'What kind of document is this?', labels:['Invoice','Receipt','Contract']}
  };
  const blocked = [[1,2],[0,2],[0,1],[1],[2],[]];
  const indices = {driving:0,routing:0,document:0};
  let mode='driving', paused=matchMedia('(prefers-reduced-motion: reduce)').matches, timer, version=0, ready=false, samples;
  const pending=new Map();
  function notify(state,message) {parent.postMessage({type:'decisions-api-status',state,message},location.origin);}
  function schedule() {
    clearTimeout(timer);
    if(ready && !paused && !document.hidden) timer=setTimeout(()=>{indices[mode]=(indices[mode]+1)%samples[mode].length; show();},5000);
  }
  function request(selected,index) {
    const key=selected+':'+index;
    if(!pending.has(key)) pending.set(key,fetch('/api/choice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:selected,index})})
      .then(async response=>{const data=await response.json(); if(!response.ok) throw Error(data.error||'API 호출 실패'); if(data.source!=='decisions_api') throw Error('실제 API 응답이 아닙니다.'); return data;}).finally(()=>pending.delete(key)));
    return pending.get(key);
  }
  async function show() {
    clearTimeout(timer); ready=false;
    if(!samples) return;
    const current=++version, selected=mode, index=indices[mode], config=configs[mode];
    for(const name of Object.keys(configs)) {
      document.getElementById(name+'-panel').hidden=name!==mode;
      const tab=document.getElementById(name+'-tab'); tab.setAttribute('aria-selected',String(name===mode)); tab.tabIndex=name===mode?0:-1;
    }
    document.getElementById('choice-example-title').textContent=config.title;
    const panel=document.getElementById(mode+'-panel'), rows=[...panel.querySelectorAll('.prob-row')];
    rows.forEach(row=>{row.querySelector('.prob').textContent='—'; row.querySelector('.prob-fill').style.transform='scaleX(0)'; row.removeAttribute('data-selected'); row.dataset.labelValue=''; row.setAttribute('aria-label',row.querySelector('span').textContent+': API 응답 대기');});
    if(mode==='driving') {
      const scene=panel.querySelector('.driving-scene'); scene.setAttribute('aria-label',samples.driving[index]);
      panel.querySelectorAll('.barrier').forEach((barrier,i)=>{const lane=blocked[index][i]; barrier.style.opacity=lane===undefined?'0':'1'; barrier.style.transform=`translate(${(lane??0)*72}px, 100px)`;});
      panel.querySelector('.drive-car').style.transform='translateX(0)';
    } else {
      panel.querySelectorAll('.message-quote').forEach((quote,i)=>{quote.style.opacity=i===index?'1':'0'; quote.style.transform='none'; quote.setAttribute('aria-hidden',String(i!==index));});
    }
    notify('loading','실제 Decisions API로 판단 중입니다…');
    try {
      const data=await request(selected,index); if(current!==version) return;
      const values=config.labels.map(label=>data.probabilities?.[label]);
      if(values.some(value=>!Number.isFinite(value)||value<0||value>1)||!config.labels.includes(data.choice)) throw Error('API 확률 응답이 올바르지 않습니다.');
      rows.forEach((row,i)=>{row.querySelector('.prob').textContent=values[i].toFixed(2); row.querySelector('.prob-fill').style.transform=`scaleX(${values[i]})`; row.dataset.labelValue=String(values[i]); row.dataset.selected=String(config.labels[i]===data.choice); row.setAttribute('aria-label',config.labels[i]+': '+values[i]);});
      if(selected==='driving') panel.querySelector('.drive-car').style.transform=`translateX(${(config.labels.indexOf(data.choice)-1)*72}px)`;
      notify('success','실제 Decisions API 응답 · '+data.choice+' · probability (0~1)'+(data.cached?' · 이전 실제 응답 재사용':''));
      ready=true; schedule();
    } catch(error) {if(current===version) notify('error',error.message);}
  }
  function select(name) {if(name!==mode){mode=name; show();}}
  for(const name of Object.keys(configs)) document.getElementById(name+'-tab').addEventListener('click',()=>select(name));
  window.addEventListener('message',event=>{
    if(event.source!==parent||event.origin!==location.origin) return;
    const data=event.data;
    if(data?.type==='decisions-select') {const name=Object.keys(configs).find(name=>name+'-tab'===data.id); if(name) select(name);}
    if(data?.type==='decisions-playback'&&typeof data.paused==='boolean') {paused=data.paused; schedule();}
    if(data?.type==='decisions-retry') show();
  });
  document.addEventListener('visibilitychange',schedule);
  new ResizeObserver(()=>parent.postMessage({type:'decisions-height',height:document.documentElement.scrollHeight},location.origin)).observe(document.querySelector('main'));
  fetch('/static/samples.json').then(response=>{if(!response.ok) throw Error('예제를 불러오지 못했습니다.'); return response.json();}).then(data=>{samples=data; show();}).catch(error=>notify('error',error.message));
})();
