const scs=[...document.querySelectorAll('#film .sc')];const bg=document.querySelector('#film .bg');
function music(ac,dur){
  const g=ac.createGain();g.gain.value=.035;const rv=ac.createConvolver(),len=ac.sampleRate*3,b=ac.createBuffer(2,len,ac.sampleRate);
  for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<len;i++)d[i]=(Math.random()*2-1)*Math.pow(1-i/len,3)}
  rv.buffer=b;g.connect(rv);rv.connect(ac.destination);g.connect(ac.destination);
  const prog=[[57,64,69,72],[53,60,65,69],[48,55,64,67],[55,62,67,71]],mel=[76,74,72,74,76,79,76,74,72,71,72,74];const t0=ac.currentTime+.1;
  for(let i=0;i<dur/0.75;i++){const ch=prog[Math.floor(i/8)%4],n=i%8===0?ch:(i%2?[]:[mel[(i/2)%mel.length|0]]);
    for(const m of n){const o=ac.createOscillator(),e=ac.createGain();o.type='sine';o.frequency.value=440*Math.pow(2,(m-69)/12);const t=t0+i*.75;
      e.gain.setValueAtTime(0,t);e.gain.linearRampToValueAtTime(i%8===0?.28:.4,t+.02);e.gain.exponentialRampToValueAtTime(.001,t+2.6);o.connect(e);e.connect(g);o.start(t);o.stop(t+2.7)}}
  g.gain.setValueAtTime(.035,t0+dur-3);g.gain.linearRampToValueAtTime(0,t0+dur)}
document.getElementById('play').onclick=e=>{const btn=e.currentTarget;btn.style.display='none';
  try{music(new (window.AudioContext||window.webkitAudioContext)(),30)}catch(_){}
  const st=performance.now();const played=new Set();
  (function tick(){const s=(performance.now()-st)/1000;document.getElementById('film').classList.toggle('alt',s>=12&&s<24);scs.forEach((el,i)=>{const a=+el.dataset.t,b=i+1<scs.length?+scs[i+1].dataset.t:30;const on=s>=a&&s<b;el.classList.toggle('on',on);if(on&&!played.has(i)){played.add(i);const au=el.querySelector('audio');if(au){au.currentTime=0;setTimeout(()=>au.play().catch(()=>{}),150)}}});
    if(s<30)requestAnimationFrame(tick);else{btn.style.display='block'}})()};
scs[0].classList.add('on');
