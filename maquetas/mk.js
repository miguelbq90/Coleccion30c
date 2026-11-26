// MAQUETAS: datos reales del catálogo TCGdex (logos, símbolos y una carta de portada por colección).
// Los números de cartas y valores son ejemplos.
(()=>{
const WANT=[
 {k:'30',en:n=>/30th/i.test(n),have:94,total:191,val:'240 €',cur:1,es:'Celebración 30.º Aniversario'},
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
  const en=await j(A+'en/sets')||[];
  const out=[];
  for(const w of WANT){
    const s=en.filter(x=>w.en(x.name)).pop();
    let c={...w,name:w.es||'',logo:'',sym:'',cover:'',serie:''};
    if(s){
      const de=await j(A+'es/sets/'+s.id), dn=await j(A+'en/sets/'+s.id);
      const d=de||dn||{};
      c.id=s.id;c.name=w.es||(de&&de.name)||(dn&&dn.name)||s.name;
      c.logo=((de&&de.logo)||(dn&&dn.logo)||'');c.logo=c.logo?c.logo+'.png':'';
      c.sym=((de&&de.symbol)||(dn&&dn.symbol)||'');c.sym=c.sym?c.sym+'.png':'';
      c.serie=(de&&de.serie&&de.serie.name)||(dn&&dn.serie&&dn.serie.name)||'';
      const cards=(dn&&dn.cards)||(de&&de.cards)||[];const off=((dn||de||{}).cardCount||{}).official||cards.length;
      const pick=cards[Math.min(off,cards.length-1)]||cards[cards.length-1];
      const cde=de&&de.cards&&pick&&de.cards.find(x=>x.localId===pick.localId);
      const im=(cde&&cde.image)||(pick&&pick.image)||'';c.cover=im?im+'/high.webp':'';
      MKLOG.push({buscado:w.k,id:s.id,nombre_en:s.name,nombre_es:de&&de.name,logo_es:!!(de&&de.logo),logo_en:!!(dn&&dn.logo),portada:pick&&pick.localId,serie:c.serie});
    } else MKLOG.push({buscado:w.k,id:null});
    if(!c.cover&&w.cur){const im=document.querySelector('.p img');c.cover=im?im.src:''}
    if(!c.serie&&w.cur)c.serie='Megaevolución';
    out.push(c);
  }
  window.MKC=out;return out})();
const pc=c=>Math.round(c.have/c.total*100);
const logo=(c,cls='')=>c.logo?`<img class="mk-logo ${cls}" src="${c.logo}" alt="">`:`<span class="mk-nl ${cls}">${c.name}</span>`;
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
   if(m==='H2'){const t=document.getElementById('colTit');t.style.display='none';t.insertAdjacentHTML('afterend',`<div class="mk-card">${logo(c)}<div class="tx"><small>Colección</small><b>${c.name}</b></div><span class="ch">Cambiar ▾</span></div>`)}
   const f=document.querySelector('.tools .r1');f.insertAdjacentHTML('afterbegin',`<span class="mk-fab">${c.sym?`<img src="${c.sym}" alt="">`:'✦'}<em>${C.length}</em></span>`)}
};
})();
