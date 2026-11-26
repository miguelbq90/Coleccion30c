// ===== Sobre realista (maqueta): una carta real como ilustración, lámina metálica y solo «COLECCIONES» =====
(()=>{
const W=220,H=340,T=30,B=310,LT=47;
let uid=0;
function rasgado(seed){let r=seed||11;const rnd=()=>{r=(r*9301+49297)%233280;return r/233280};
  const p=[[10,LT-1]];for(let x=15;x<206;x+=5+rnd()*5)p.push([+x.toFixed(1),+(LT-3.5+rnd()*7).toFixed(1)]);p.push([210,LT+1]);return p}
const RG=rasgado(11);
const linea=pts=>pts.map((q,i)=>(i?'L':'M')+q[0]+' '+q[1]).join(' ');
const dientes=(y,dir)=>{let p='';for(let x=30;x<=210;x+=5)p+=` L${x} ${y+((x/5)%2?dir*5:0)}`;return p};
const selloSup=`M10 ${T} L10 9 L14 4 L18 4 L22 11 L26 4${dientes(4,1)} L210 9 L210 ${T} Z`;
const selloInf=(()=>{let p=`M10 ${B} L210 ${B} L210 ${H-6}`;for(let x=210;x>=10;x-=5)p+=` L${x} ${H-6+((x/5)%2?5:0)}`;return p+' Z'})();
const tiraForma=`M10 ${T} L210 ${T} L210 ${RG[RG.length-1][1]} `+RG.slice().reverse().map(q=>`L${q[0]} ${q[1]}`).join(' ')+' Z';
const frenteForma=linea(RG)+` C216.5 ${LT+80} 216.5 ${B-80} 210 ${B} L10 ${B} C3.5 ${B-80} 3.5 ${LT+80} 10 ${RG[0][1]} Z`;
const dentroForma=linea(RG.map(q=>[q[0],q[1]-3]))+` L210 ${B} L10 ${B} Z`;
const costillas=(y0,y1)=>Array.from({length:40},(_,i)=>`<line x1="${12+i*5}" y1="${y0+2}" x2="${12+i*5}" y2="${y1-2}"/>`).join('');
const arrugas=(y,dir)=>[[24,11,-3],[46,8,-1],[70,12,-2],[95,7,1],[121,10,1],[148,8,2],[172,12,3],[196,9,3]].map(([x,l,a])=>`<path d="M${x} ${y} q${a} ${dir*l/2} ${a*1.6} ${dir*l}"/>`).join('');
function defs(k){return `<defs>
<linearGradient id="${k}B" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#05041a" stop-opacity=".62"/><stop offset=".13" stop-color="#05041a" stop-opacity="0"/><stop offset=".87" stop-color="#05041a" stop-opacity="0"/><stop offset="1" stop-color="#05041a" stop-opacity=".62"/></linearGradient>
<linearGradient id="${k}V" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05041a" stop-opacity=".45"/><stop offset=".1" stop-color="#05041a" stop-opacity="0"/><stop offset=".62" stop-color="#05041a" stop-opacity="0"/><stop offset=".78" stop-color="#05041a" stop-opacity=".78"/><stop offset="1" stop-color="#05041a" stop-opacity=".9"/></linearGradient>
<linearGradient id="${k}H" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff9fd8"/><stop offset=".25" stop-color="#ffe98a"/><stop offset=".5" stop-color="#8ff5c9"/><stop offset=".75" stop-color="#8fcaff"/><stop offset="1" stop-color="#cdb3ff"/></linearGradient>
<linearGradient id="${k}S" x1="0" y1="0" x2="1" y2=".55"><stop offset=".3" stop-color="#fff" stop-opacity="0"/><stop offset=".41" stop-color="#fff" stop-opacity=".5"/><stop offset=".46" stop-color="#fff" stop-opacity=".08"/><stop offset=".52" stop-color="#fff" stop-opacity=".3"/><stop offset=".62" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="${k}P" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7f7fd"/><stop offset=".45" stop-color="#b6b5cf"/><stop offset=".7" stop-color="#e8e8f3"/><stop offset="1" stop-color="#9796b4"/></linearGradient>
<linearGradient id="${k}I" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9d9e6"/><stop offset=".5" stop-color="#f6f6fb"/><stop offset="1" stop-color="#a9a8c2"/></linearGradient>
<linearGradient id="${k}T" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#e6ebff"/><stop offset=".55" stop-color="#9aa6dc"/><stop offset="1" stop-color="#f2f4ff"/></linearGradient>
<clipPath id="${k}cF"><path d="${frenteForma}"/></clipPath><clipPath id="${k}cT"><path d="${tiraForma}"/></clipPath></defs>`}
// La ilustración: la carta ampliada, con la franja de arriba (nombre) bajo el cierre y la de abajo (ataques) bajo el letrero
const arte=(k,url)=>`<image href="${url}" x="-30" y="-14" width="280" height="391" preserveAspectRatio="xMidYMin slice"/>
 <rect x="0" y="0" width="${W}" height="${H}" fill="url(#${k}H)" style="mix-blend-mode:soft-light" opacity=".55"/>
 <rect x="0" y="0" width="${W}" height="${H}" fill="url(#${k}B)"/><rect x="0" y="0" width="${W}" height="${H}" fill="url(#${k}V)"/>
 <rect class="pk-brillo" x="-220" y="0" width="${W*3}" height="${H}" fill="url(#${k}S)"/>`;
const letrero=k=>`<text x="110" y="${B-22}" text-anchor="middle" font-family="Archivo Black,Impact,sans-serif" font-size="25" textLength="184" lengthAdjust="spacingAndGlyphs" fill="url(#${k}T)" stroke="#0b0930" stroke-width="7" paint-order="stroke" stroke-linejoin="round">COLECCIONES</text>
 <text x="110" y="${B-22}" text-anchor="middle" font-family="Archivo Black,Impact,sans-serif" font-size="25" textLength="184" lengthAdjust="spacingAndGlyphs" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width=".8">COLECCIONES</text>`;
window.sobreHTML=(url,extra='')=>{const k='zp'+(++uid);
 return `<div class="pk" ${extra}>
 <svg class="pk-dentro" viewBox="0 0 ${W} ${H}">${defs(k+'d')}<path d="${dentroForma}" fill="url(#${k}dI)"/></svg>
 <div class="pk-cartas"></div>
 <svg class="pk-frente" viewBox="0 0 ${W} ${H}">${defs(k)}
  <g clip-path="url(#${k}cF)">${arte(k,url)}${letrero(k)}
   <g fill="none" stroke-width="1.2" stroke-linecap="round"><g stroke="#fff" opacity=".35">${arrugas(B-1,-1)}</g><g stroke="#05041a" opacity=".25" transform="translate(1.5 0)">${arrugas(B-1,-1)}</g></g></g>
  <path d="${selloInf}" fill="url(#${k}P)" stroke="#fff" stroke-width="1.2" stroke-linejoin="round"/><g stroke="#7d7c99" stroke-width="1" opacity=".55">${costillas(B,H-6)}</g><path d="M10 ${B} H210" stroke="#8b8aa8" stroke-width="1.5"/>
  <path d="M10 ${LT} C3.5 ${LT+80} 3.5 ${B-80} 10 ${B}" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="1.4"/><path d="M210 ${LT} C216.5 ${LT+80} 216.5 ${B-80} 210 ${B}" fill="none" stroke="#fff" stroke-opacity=".4" stroke-width="1.4"/>
  <path class="pk-chispa" d="${linea(RG)}" fill="none" stroke="#fff6c2" stroke-width="2.6" stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
 </svg>
 <svg class="pk-tira" viewBox="0 0 ${W} ${H}">${defs(k+'t')}
  <g clip-path="url(#${k}tcT)">${arte(k+'t',url)}<g fill="none" stroke-width="1.2" stroke-linecap="round"><g stroke="#fff" opacity=".35">${arrugas(T+1,1)}</g></g></g>
  <path d="${selloSup}" fill="url(#${k}tP)" stroke="#fff" stroke-width="1.2" stroke-linejoin="round"/><g stroke="#7d7c99" stroke-width="1" opacity=".55">${costillas(4,T)}</g><path d="M10 ${T} H210" stroke="#8b8aa8" stroke-width="1.5"/>
 </svg>
 <div class="pk-flash"></div>${Array.from({length:12},(_,i)=>`<i class="pk-bit" style="--a:${i*30+8}deg;--d:${70+(i*37)%60}px;--c:${['#ffe98a','#8fcaff','#ff9fd8','#fff','#8ff5c9','#cdb3ff'][i%6]}"></i>`).join('')}
</div>`};
})();
