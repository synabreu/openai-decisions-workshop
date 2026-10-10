// Bridge the existing controls to the official isolated predicate demo.
(() => {
  const frame = document.getElementById('reference-demo');
  const toggle = document.getElementById('animation-toggle');
  const ids = {dent:'dent-tab', cancellation:'cancel-tab', answer_relevance:'relevance-tab'};
  let paused = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function send(message) { frame.contentWindow?.postMessage(message, location.origin); }
  function updateButton() { toggle.textContent = paused ? 'Resume animation' : 'Pause animation'; toggle.setAttribute('aria-pressed', String(paused)); }
  function sync() {
    const selected = document.querySelector('.tabs [aria-selected="true"]');
    send({type:'decisions-select', id:ids[selected.dataset.mode]});
    send({type:'decisions-playback', paused});
  }
  toggle.addEventListener('click', () => { paused = !paused; updateButton(); send({type:'decisions-playback', paused}); });
  new MutationObserver(sync).observe(document.querySelector('.tabs'), {subtree:true, attributes:true, attributeFilter:['aria-selected']});
  frame.addEventListener('load', sync);
  window.addEventListener('message', event => {
    if (event.source !== frame.contentWindow || event.origin !== location.origin) return;
    if (event.data?.type === 'decisions-api-status') {
      const note = document.querySelector('.demo-note');
      note.textContent = event.data.message;
      note.dataset.state = event.data.state;
      document.getElementById('api-retry').hidden = event.data.state !== 'error';
    }
    if (event.data?.type === 'decisions-height' && Number.isFinite(event.data.height)) frame.style.height = Math.max(200, Math.min(1200,event.data.height)) + 'px';
    if (event.data?.type === 'decisions-playback' && typeof event.data.paused === 'boolean') { paused = event.data.paused; updateButton(); }
  });
  updateButton();
  document.getElementById('api-retry').addEventListener('click', () => send({type:'decisions-retry'}));
})();
