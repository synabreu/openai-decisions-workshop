(() => {
  let mode='package', paused=matchMedia('(prefers-reduced-motion: reduce)').matches, version=0, ready=false, timer;
  const indices={package:0,urgency:0}, pending=new Map();
  const status=document.getElementById('status'), retry=document.getElementById('retry'), playback=document.getElementById('playback');
  function schedule(){clearTimeout(timer);if(ready&&!paused&&!document.hidden)timer=setTimeout(()=>{indices[mode]=(indices[mode]+1)%3;show();},5000);}
  function updatePlayback(){playback.textContent=paused?'Resume animation':'Pause animation';playback.setAttribute('aria-pressed',String(paused));schedule();}
  async function evaluate(selected,index){
    const key=selected+':'+index;
    if(!pending.has(key))pending.set(key,fetch('/api/score',{method:'POST',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:selected,index})}).then(async response=>{
      const data=await response.json();if(!response.ok)throw Error(data.error||'API 호출 실패');
      if(data.source!=='decisions_api'||!Number.isFinite(data.answer?.score))throw Error('올바르지 않은 API 응답입니다.');
      return data.answer;
    }).finally(()=>pending.delete(key)));
    return pending.get(key);
  }
  async function show(){
    clearTimeout(timer);ready=false;const current=++version,selected=mode,index=indices[mode];status.hidden=true;retry.hidden=true;
    document.querySelectorAll('[role=tab]').forEach(tab=>{const active=tab.id===mode+'-tab';tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;});
    document.querySelectorAll('[role=tabpanel]').forEach(panel=>panel.hidden=panel.id!==mode+'-panel');
    document.getElementById('score-example-title').textContent=mode==='package'?'How damaged is this package?':'How urgent is this request?';
    document.querySelectorAll('.package-image,.message-quote').forEach(element=>{const items=[...element.parentElement.children].filter(item=>item.className===element.className);const active=items.indexOf(element)===index;element.style.opacity=active?'1':'0';element.style.transform='none';element.setAttribute('aria-hidden',String(!active));});
    const panel=document.getElementById(mode+'-panel');panel.setAttribute('aria-busy','true');
    panel.querySelectorAll('.score-number,.damage-prob').forEach(element=>element.textContent='—');
    panel.querySelectorAll('.damage-fill').forEach(element=>element.style.transform='scaleX(0)');
    panel.querySelectorAll('[data-label-value]').forEach(element=>{element.dataset.labelValue='';element.setAttribute('aria-label','API 응답 대기');});
    panel.querySelectorAll('.damage-row').forEach(row=>row.removeAttribute('data-selected'));
    panel.querySelector('.severity-marker').style.visibility='hidden';
    document.querySelector('.package-scene').setAttribute('aria-label',['Undamaged package','Package with minor damage','Package with major damage'][index]);
    try{
      const answer=await evaluate(selected,index);if(current!==version)return;
      panel.querySelector('.score-number').textContent=answer.score.toFixed(2);
      const scoreValue=panel.querySelector('.score-value');scoreValue.dataset.labelValue=String(answer.score);scoreValue.setAttribute('aria-label','Score: '+answer.score+' out of 2');
      const marker=panel.querySelector('.severity-marker');marker.style.visibility='visible';marker.style.left=(answer.score/2*100)+'%';
      const max=Math.max(...answer.probabilities.map(item=>item.probability));
      panel.querySelectorAll('.damage-row').forEach(row=>{const label=row.querySelector('span').textContent, probability=answer.probabilities.find(item=>item.label===label).probability;row.querySelector('.damage-prob').textContent=probability.toFixed(2);row.querySelector('.damage-fill').style.transform=`scaleX(${probability})`;row.dataset.selected=String(probability===max);row.setAttribute('aria-label',label+': '+probability);});
      ready=true;schedule();
    }catch(error){if(current===version){status.textContent=error.message;status.hidden=false;retry.hidden=false;}}
    finally{if(current===version)panel.setAttribute('aria-busy','false');}
  }
  function select(next){if(next!==mode){mode=next;show();}}
  const tabs=[...document.querySelectorAll('[role=tab]')];
  tabs.forEach((tab,i)=>{tab.onclick=()=>select(tab.id.replace('-tab',''));tab.onkeydown=event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const target=tabs[event.key==='Home'?0:event.key==='End'?1:1-i];target.focus();select(target.id.replace('-tab',''));};});
  playback.onclick=()=>{paused=!paused;updatePlayback();};retry.onclick=show;
  document.addEventListener('visibilitychange',schedule);updatePlayback();show();
})();
