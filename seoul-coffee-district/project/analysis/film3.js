(function(){
const film=document.getElementById('film'); if(!film) return;
const scs=[...film.querySelectorAll('.sc')], g=film.querySelector('.fmap .mapg'), pk=film.querySelector('.fmap .pick'), bar=film.querySelector('.bar i'), btn=document.getElementById('play');
function zoom(on){ if(!g||!pk) return; if(!on){g.style.transform='';return}
  const x=+pk.getAttribute('cx'), y=+pk.getAttribute('cy'), vb=g.ownerSVGElement.viewBox.baseVal, k=3.2;
  g.style.transform=`translate(${vb.width/2-x*k}px,${vb.height/2-y*k}px) scale(${k})`; }
function music(ac,dur){
  const g2=ac.createGain();g2.gain.value=.03;g2.connect(ac.destination);
  const prog=[[57,64,69,72],[53,60,65,69],[48,55,64,67],[55,62,67,71]],t0=ac.currentTime+.1;
  for(let i=0;i<dur/0.75;i++){const n=i%8===0?prog[Math.floor(i/8)%4]:(i%4===2?[prog[Math.floor(i/8)%4][3]+12]:[]);
    for(const m of n){const o=ac.createOscillator(),e=ac.createGain();o.type='sine';o.frequency.value=440*Math.pow(2,(m-69)/12);const t=t0+i*.75;
      e.gain.setValueAtTime(0,t);e.gain.linearRampToValueAtTime(.3,t+.02);e.gain.exponentialRampToValueAtTime(.001,t+2.6);o.connect(e);e.connect(g2);o.start(t);o.stop(t+2.7)}}
  g2.gain.setValueAtTime(.03,t0+dur-2);g2.gain.linearRampToValueAtTime(0,t0+dur)}
function show(i){ scs.forEach((el,j)=>el.classList.toggle('on',j===i)); const m=scs[i]?scs[i].dataset.mode:'all'; film.dataset.mode=m; zoom(m==='pick'); }
show(0);
btn&&btn.addEventListener('click',()=>{btn.style.display='none';
  try{music(new (window.AudioContext||window.webkitAudioContext)(),34)}catch(_){}
  const aus=scs.map(s=>s.querySelector('audio')); const starts=[];let acc=0;aus.forEach(a=>{starts.push(acc);acc+=Math.max(4.6,(a&&isFinite(a.duration)?a.duration:4.6)+0.6)});const TOT=acc;
  const st=performance.now(); let cur=-1;
  (function tick(){const s=(performance.now()-st)/1000; let i=0;for(let k=0;k<starts.length;k++){if(s>=starts[k])i=k}
    if(i!==cur){cur=i;show(i);const au=scs[i]&&scs[i].querySelector('audio');if(au){au.currentTime=0;setTimeout(()=>au.play().catch(()=>{}),200)}}
    if(bar) bar.style.width=Math.min(100,s/TOT*100)+'%';
    if(s<TOT) requestAnimationFrame(tick); else {btn.textContent='▶ 다시 보기';btn.style.display='block';}})();
});
})();
