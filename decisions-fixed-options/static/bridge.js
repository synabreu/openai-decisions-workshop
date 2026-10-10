(() => {
  const frame = document.getElementById('reference-demo');
  const toggle = document.getElementById('animation-toggle');
  let paused = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const send = message => frame.contentWindow?.postMessage(message, location.origin);
  function update() {
    toggle.textContent = paused ? 'Resume animation' : 'Pause animation';
    toggle.setAttribute('aria-pressed', String(paused));
  }
  function sync() {
    send({type:'decisions-select', id:document.querySelector('.tabs [aria-selected="true"]').dataset.mode + '-tab'});
    send({type:'decisions-playback', paused});
  }
  frame.addEventListener('load', sync);
  new MutationObserver(sync).observe(document.querySelector('.tabs'), {subtree:true, attributes:true, attributeFilter:['aria-selected']});
  toggle.addEventListener('click', () => { paused = !paused; update(); send({type:'decisions-playback', paused}); });
  window.addEventListener('message', event => {
    if (event.source !== frame.contentWindow || event.origin !== location.origin) return;
    if (event.data?.type === 'decisions-api-status') {
      document.querySelector('.demo-note').textContent = event.data.message;
      document.getElementById('api-retry').hidden = event.data.state !== 'error';
    }
    if (event.data?.type === 'decisions-height' && Number.isFinite(event.data.height)) frame.style.height = Math.max(200, Math.min(1200,event.data.height)) + 'px';
    if (event.data?.type === 'decisions-playback' && typeof event.data.paused === 'boolean') { paused = event.data.paused; update(); }
  });
  update();
  document.getElementById('api-retry').addEventListener('click', () => send({type:'decisions-retry'}));
})();
