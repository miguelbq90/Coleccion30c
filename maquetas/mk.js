// MAQUETAS: datos reales del catálogo TCGdex (logos, símbolos y una carta de portada por colección).
// Los números de cartas y valores son ejemplos.
(()=>{
const WANT=[
 {k:'30',en:n=>/30th|celebration/i.test(n)&&!/classic|^celebrations$/i.test(n),have:94,total:191,val:'240 €',cur:1,es:'Celebración 30.º Aniversario'},
 {k:'pe',en:n=>/^Prismatic Evolutions$/i.test(n),have:120,total:180,val:'310 €'},
 {k:'ss',en:n=>/^Surging Sparks$/i.test(n),have:60,total:252,val:'85 €'},
 {k:'151',en:n=>/^151$/.test(n),have:150,total:207,val:'420 €'},
 {k:'of',en:n=>/^Obsidian Flames$/i.test(n),have:41,total:230,val:'38 €'},
 {k:'tf',en:n=>/^Temporal Forces$/i.test(n),have:200,total:218,val:'95 €'},
 {k:'pf',en:n=>/^Paldean Fates$/i.test(n),have:12,total:245,val:'9 €'},
];
const A='https://api.tcgdex.net/v2/';
const j=u=>fetch(u).then(r=>r.ok?r.json():null).catch(()=>null);
window.MKLOG=[];
window.MKREADY=(async()=>{
  try{const c=JSON.parse(localStorage.getItem('mk-cache')||'null');if(c&&c.length){window.MKC=c;MKLOG.push({cache:true});return c}}catch(e){}
  const en=await j(A+'en/sets')||[];
  MKLOG.push({sets_30:en.filter(x=>/30th|celebration/i.test(x.name)).map(x=>x.id+' · '+x.name)});
  const out=[];
  for(const w of WANT){
    const s=en.filter(x=>w.en(x.name)).pop();
    let c={...w,name:w.es||'',logo:'',sym:'',cover:'',serie:''};
    if(s){
      const de=await j(A+'es/sets/'+s.id), dn=await j(A+'en/sets/'+s.id);
      const d=de||dn||{};
      c.id=s.id;c.name=w.es||(de&&de.name)||(dn&&dn.name)||s.name;
      c.logo=((de&&de.logo)||(dn&&dn.logo)||'');c.logo=c.logo?c.logo+'.png':'';c.logo2=(dn&&dn.logo)?dn.logo+'.png':'';
      c.sym=((de&&de.symbol)||(dn&&dn.symbol)||'');c.sym=c.sym?c.sym+'.png':'';
      c.serie=(de&&de.serie&&de.serie.name)||(dn&&dn.serie&&dn.serie.name)||'';
      const cards=(dn&&dn.cards)||(de&&de.cards)||[];const off=((dn||de||{}).cardCount||{}).official||cards.length;
      // La portada: la carta más cara de las «secretas» (las que pasan del número oficial)
      const cand=cards.filter(x=>parseInt(x.localId,10)>off).slice(0,70);
      const pr=await Promise.all(cand.map(x=>j(A+'en/cards/'+s.id+'-'+x.localId).then(d=>{const c=d&&d.pricing&&d.pricing.cardmarket;return {x,v:c?(c.avg||c.trend||c.avg30||0):0}})));
      pr.sort((a,b)=>b.v-a.v);
      const pick=(pr[0]&&pr[0].v>0?pr[0].x:null)||cards[Math.min(off,cards.length-1)]||cards[cards.length-1];
      const cde=de&&de.cards&&pick&&de.cards.find(x=>x.localId===pick.localId);
      const im=(cde&&cde.image)||(pick&&pick.image)||'';c.cover=im?im+'/high.webp':'';
      MKLOG.push({buscado:w.k,id:s.id,nombre_en:s.name,nombre_es:de&&de.name,logo_es:!!(de&&de.logo),logo_en:!!(dn&&dn.logo),portada:pick&&pick.localId,serie:c.serie});
    } else MKLOG.push({buscado:w.k,id:null});
    if(!c.cover&&w.cur){const im=document.querySelector('.p img');c.cover=im?im.src:''}
    if(!c.serie&&w.cur)c.serie='Megaevolución';
    out.push(c);
  }
  window.MKC=out;try{if(out.filter(c=>c.logo).length>=4)localStorage.setItem('mk-cache',JSON.stringify(out))}catch(e){}return out})();
const pc=c=>Math.round(c.have/c.total*100);
window.mkErr=(im)=>{const a=im.dataset.alt;if(a){im.removeAttribute('data-alt');im.src=a}else{const sp=document.createElement('span');sp.className='mk-nl';sp.textContent=im.dataset.n;im.replaceWith(sp)}};
const logo=(c,cls='')=>c.logo?`<img class="mk-logo ${cls}" src="${c.logo}" data-alt="${c.logo2&&c.logo2!==c.logo?c.logo2:''}" data-n="${c.name}" onerror="mkErr(this)" alt="">`:`<span class="mk-nl ${cls}">${c.name}</span>`;
window.mk=async m=>{const C=await MKREADY;const ad='<div class="mk-add">＋ Añadir colección</div>';
 const scr=h=>document.body.insertAdjacentHTML('beforeend',`<div class="mk-scr">${h}</div>`);
 const head=`<h2>Mis colecciones</h2><p class="sub2">${C.length} colecciones · toca una para entrar</p>`;
 if(m==='M1')scr(`<div class="m1">${head}${C.map(c=>`<div class="row${c.cur?' on':''}">${c.cover?`<img class="art" src="${c.cover}" alt="">`:''}<div class="lf">${logo(c)}<div class="st"><span>${c.have}/${c.total}</span><div class="mk-bar"><i style="width:${pc(c)}%"></i></div><span>${pc(c)} %</span></div></div><span class="pz">≈ ${c.val}</span></div>`).join('')}${ad}</div>`);
 if(m==='M2'){const series=[...new Set(C.map(c=>c.serie||'Otras'))];
   scr(`<div class="m2">${head}${series.map(s=>`<div class="ser">${s}</div><div class="gr">${C.filter(c=>(c.serie||'Otras')===s).map(c=>`<div class="tl${c.cur?' on':''}"><div class="top">${c.cover?`<img class="bg" src="${c.cover}" alt="">`:''}${logo(c)}</div><div class="bt"><b>${c.name}</b><span><div class="mk-bar"><i style="width:${pc(c)}%"></i></div>${pc(c)} %</span></div></div>`).join('')}</div>`).join('')}<div class="ser"> </div><div class="gr"><div class="mk-add"><span>＋</span>Añadir</div></div></div>`)}
 if(m==='M3'){const i=0,L=C[C.length-1],c=C[i],R=C[i+1];
   const card=(c,cl)=>`<div class="pt ${cl}">${c.cover?`<img class="bg" src="${c.cover}" alt="">`:''}${logo(c)}<div class="ft"><div class="r"><span>${c.have}/${c.total} · ${pc(c)} %</span><span>≈ ${c.val}</span></div><div class="mk-bar"><i style="width:${pc(c)}%"></i></div></div></div>`;
   scr(`<div class="m3">${head}<div class="car">${card(L,'l')}${card(R,'r')}${card(c,'')}</div><div class="dots">${C.map((x,k)=>`<i class="${k===i?'on':''}"></i>`).join('')}</div>${ad}</div>`)}
 if(m==='H1'||m==='H2'||m==='HS'){document.documentElement.classList.add('mkH');const c=C.find(x=>x.cur)||C[0];
   if(m==='H1')document.getElementById('colTit').insertAdjacentHTML('afterend',`<div class="mk-pill"><span class="sy">${c.sym?`<img src="${c.sym}" alt="">`:'✦'}</span>Mis colecciones <em>${C.length}</em> ▾</div>`);
   if(m==='H2'){const t=document.getElementById('colTit');t.style.display='none';t.insertAdjacentHTML('afterend',`<div class="mk-card"><div class="tx"><small>Colección</small>${logo(c)}</div><span class="ch">Cambiar ▾</span></div>`)}
   const f=document.querySelector('.tools .r1');f.insertAdjacentHTML('afterbegin',`<span class="mk-fab">${c.sym?`<img src="${c.sym}" alt="">`:'✦'}<em>${C.length}</em></span>`)}
};

// --- Sobre de Zuroku: dibujo propio (lámina holográfica, bordes dentados, la hoja de carpeta del icono y el nombre) ---
const PACK=`<svg viewBox="0 0 200 300" aria-hidden="true"><defs>
<linearGradient id="pkH" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff9fcf"/><stop offset=".25" stop-color="#ffe56b"/><stop offset=".5" stop-color="#7ff0b8"/><stop offset=".75" stop-color="#8fcaff"/><stop offset="1" stop-color="#c3a6ff"/></linearGradient>
<linearGradient id="pkS" x1="0" y1="0" x2="1" y2="0"><stop offset=".35" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset=".65" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="pkG" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff6a8"/><stop offset="1" stop-color="#fff6a8" stop-opacity="0"/></radialGradient></defs>
<ellipse class="glow" cx="100" cy="40" rx="120" ry="70" fill="url(#pkG)" opacity="0"/>
<path d="M10 52 L190 52 L190 284 l-10 8 -10 -8 -10 8 -10 -8 -10 8 -10 -8 -10 8 -10 -8 -10 8 -10 -8 -10 8 -10 -8 -10 8 -10 -8 -10 8 -10 -8 -10 8 Z" fill="url(#pkH)" stroke="#fff" stroke-width="4" stroke-linejoin="round"/>
<path d="M10 52 L190 52 L190 284 L10 284 Z" fill="url(#pkS)"/>
<rect x="26" y="70" width="148" height="44" rx="12" fill="#1b1b45"/>
<text x="100" y="101" text-anchor="middle" font-family="Archivo Black,Impact,sans-serif" font-size="26" fill="#ffd23f" stroke="#0d0c26" stroke-width="1">ZUROKU</text>
<g transform="translate(62 128)"><rect width="76" height="96" rx="10" fill="#2a2a66" stroke="#fff" stroke-width="4"/>
${[0,1,2].map(r=>[0,1,2].map(k=>`<rect x="${8+k*22}" y="${8+r*28}" width="16" height="22" rx="3" fill="${['#ff8fc8','#ffe56b','#7ff0b8','#7fc4ff','#c3a6ff','none','#ff8fc8','none','none'][r*3+k]}" stroke="${(r*3+k)%8==5||r*3+k>6?'#8a8ad6':'#fff'}" stroke-width="1.6" ${['none'].includes(['#ff8fc8','#ffe56b','#7ff0b8','#7fc4ff','#c3a6ff','none','#ff8fc8','none','none'][r*3+k])?'stroke-dasharray="3 2"':''}/>`).join('')).join('')}</g>
<text x="100" y="256" text-anchor="middle" font-family="DM Sans,system-ui,sans-serif" font-weight="800" font-size="13" letter-spacing="3" fill="#1b1b45">MIS COLECCIONES</text>
<g class="tear"><path d="M10 52 L10 22 l10 -8 10 8 10 -8 10 8 10 -8 10 8 10 -8 10 8 10 -8 10 8 10 -8 10 8 10 -8 10 8 10 -8 10 8 10 -8 10 8 L190 52 Z" fill="url(#pkH)" stroke="#fff" stroke-width="4" stroke-linejoin="round"/>
<path d="M16 40 H184" stroke="#1b1b45" stroke-width="2" stroke-dasharray="6 5" opacity=".6"/></g></svg>`;
const ponPack=(abierto)=>{const st=document.querySelector('.stage');const b=document.getElementById('b30').getBoundingClientRect(),sr=st.getBoundingClientRect();
  const cx=b.left-sr.left+b.width/2,cy=b.top-sr.top+b.height/2;
  st.insertAdjacentHTML('beforeend',`<div class="mk-pack" style="left:${cx-75}px;top:${cy-100}px">${PACK}</div>`);
  if(!abierto)st.insertAdjacentHTML('beforeend',`<div class="mk-hint" style="left:${cx+50}px;top:${cy+70}px">Toca para abrir ✨</div>`);
  return {st,cx,cy}};
const _mk=window.mk;
window.mk=async m=>{const C=await MKREADY;
 if(m==='S1'||m==='S2'){document.documentElement.classList.add('mkS');if(m==='S2')document.documentElement.classList.add('mkS2');
   const {st,cx,cy}=ponPack(m==='S2');
   if(m==='S2'){document.querySelector('.stage .mk-pack').remove();const F=[C[3],C[1],C[0],C[2],C[4]].filter(Boolean),X=[-124,-62,0,62,124],Y=[52,20,0,20,52],R=[-16,-8,0,8,16];
     document.body.insertAdjacentHTML('beforeend',`<div class="mk-open"><div class="tt">¿Qué colección abrimos?</div><span class="x">✕</span>${F.map((c,i)=>`<div class="fc${c.cur?' on':''}" style="left:calc(50% + ${X[i]}px);top:calc(22% + ${Y[i]}px);transform:rotate(${R[i]}deg);z-index:${i===2?5:3-Math.abs(i-2)}">${c.cover?`<img class="bg" src="${c.cover}" alt="">`:''}${c.logo?logo(c):`<span class="mk-nl">${c.name}</span>`}<div class="pc"><div class="mk-bar"><i style="width:${pc(c)}%"></i></div>${pc(c)} %</div></div>`).join('')}<div class="mk-pack">${PACK}</div><div class="mk-todas">Ver las ${C.length} colecciones ›</div></div>`)}
   return}
 if(m==='L2'){const fav=C.slice(0,3),rest=C.slice(3);
   const row=c=>`<div class="row${c.cur?' on':''}">${c.cover?`<img class="art" src="${c.cover}" alt="">`:''}<div class="lf">${logo(c)}<div class="st"><span>${c.have}/${c.total}</span><div class="mk-bar"><i style="width:${pc(c)}%"></i></div><span>${pc(c)} %</span></div></div><span class="pz">≈ ${c.val}</span></div>`;
   const series=[...new Set(rest.map(c=>c.serie||'Otras'))];
   document.body.insertAdjacentHTML('beforeend',`<div class="mk-scr"><div class="m1 m4"><h2>Mis colecciones</h2><p class="sub2">${C.length} colecciones</p><div class="bus">🔍 Buscar colección…</div><div class="sec">⭐ Estás completando</div>${fav.map(row).join('')}${series.map(s=>{const L=rest.filter(c=>(c.serie||'Otras')===s);return `<div class="sec">${s}</div><div class="fold">Ver ${L.length} colecciones <span class="lg">${L.slice(0,3).map(c=>c.logo?`<img src="${c.logo}" data-alt="${c.logo2||''}" onerror="mkErr(this)" alt="">`:'').join('')}</span> ▾</div>`}).join('')}<div class="mk-add" style="height:56px">＋ Añadir colección</div></div></div>`);return}
 return _mk(m)};
})();
