"""Oficina virtual estilo pixel-art oscuro (ambiente de club con neones).
Cada área tiene su cubículo. El gerente recibe el documento, se levanta, camina hasta el cubículo
del área encargada y se lo entrega. Cuando nadie trabaja, los personajes pasean, leen, duermen,
toman café y conversan."""
import json

# Cubículos: 0 = gerencia, 1..4 = áreas (centro x en una escena lógica de 320x180)
ORDEN = ["gerente", "contabilidad", "proyectos", "diagnostico", "proyecciones"]
CX = {"gerente": 32, "contabilidad": 96, "proyectos": 160, "diagnostico": 224, "proyecciones": 288}
VELOCIDAD = 64   # px lógicos por segundo (igual que en el JavaScript)
CARRIL = 158     # y del pasillo


def duracion_area(area: str) -> float:
    """Segundos que dura la escena 'area' (el gerente se levanta, camina y entrega el documento)."""
    dist = 36 + abs(CX[area] - CX["gerente"]) + 36
    return 4.2 + dist / VELOCIDAD


PLANTILLA = r"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
html,body{margin:0;background:transparent;overflow:hidden}
#wrap{max-width:960px;margin:0 auto;border:4px solid #0b0508;box-sizing:border-box;background:#0b0508;border-radius:4px}
#stage{position:relative;--s:3}
canvas{display:block;width:100%;height:auto;image-rendering:pixelated;image-rendering:crisp-edges}
.px{font-family:'Press Start 2P',monospace}
.neon{position:absolute;display:flex;align-items:center;justify-content:center;font-family:'Press Start 2P',monospace;
 font-size:calc(var(--s)*3.3px);white-space:nowrap;text-shadow:0 0 calc(var(--s)*1px) currentColor,0 0 calc(var(--s)*3px) currentColor;
 opacity:.85;animation:fl 7s steps(1) infinite;pointer-events:none}
.neon.on{opacity:1;text-shadow:0 0 calc(var(--s)*1px) #fff,0 0 calc(var(--s)*3px) currentColor,0 0 calc(var(--s)*6px) currentColor;animation:none}
@keyframes fl{0%,92%,96%,100%{opacity:.85}93%,97%{opacity:.35}}
.bub{position:absolute;transform:translate(-50%,-100%);background:#f6f0e0;color:#1a0c12;border:calc(var(--s)*.7px) solid #0b0508;
 padding:calc(var(--s)*1px) calc(var(--s)*1.6px);font-family:'Press Start 2P',monospace;font-size:calc(var(--s)*2.9px);line-height:1.5;
 text-align:center;max-width:34%;display:none;pointer-events:none;z-index:3;box-shadow:0 calc(var(--s)*.8px) 0 rgba(0,0,0,.45)}
.bub::after{content:"";position:absolute;left:50%;bottom:calc(var(--s)*-2.2px);margin-left:calc(var(--s)*-1px);border:calc(var(--s)*1.1px) solid transparent;border-top-color:#0b0508;border-bottom:0}
.bub.ok{background:#c9f7d4}
#hud{display:flex;justify-content:space-between;align-items:center;background:#0b0508;border-top:2px solid #ff4d78;padding:8px 12px;
 font-family:'Press Start 2P',monospace;font-size:11px;color:#f6e8d8;letter-spacing:.5px}
#hb span{display:inline-block;width:11px;height:11px;margin-left:4px;background:#2a1a22}
#hb span.f{background:#38d66b}#hb span.p{animation:pp .5s steps(1) infinite}
@keyframes pp{50%{opacity:.2}}
</style></head><body>
<div id="wrap"><div id="stage"><canvas id="c" width="320" height="180"></canvas><div id="neons"></div><div id="bubs"></div></div>
<div id="hud"><span id="ht"></span><span id="hb"></span></div></div>
<script>
(()=>{
const CFG=__CFG__;
const W=320,H=180,HY=__CARRIL__,SP=__VEL__;
const cv=document.getElementById('c'),ctx=cv.getContext('2d');ctx.imageSmoothingEnabled=false;
const mk=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;return c;};
const bg=mk(),fg=mk(),gl=mk(),vg=mk();
const R=(c,x,y,w,h,col)=>{c.fillStyle=col;c.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));};
const rnd=(a,b)=>a+Math.random()*(b-a),pick=a=>a[Math.floor(Math.random()*a.length)],clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
let seed=11;const rr=()=>{seed=(seed*16807)%2147483647;return (seed-1)/2147483646;};

const AREAS=[
 {id:'gerente',name:'GERENCIA',cx:32,shirt:'#8a2040',hair:'#1c1c1c',skin:'#e8b890',tint:'#c0334d',neon:'#ff4d78',pants:'#241a2e',suit:1,style:'A'},
 {id:'contabilidad',name:'CONTABILIDAD',cx:96,shirt:'#3f6fd0',hair:'#4a3222',skin:'#f0c8a0',tint:'#4a7bd0',neon:'#5aa8ff',pants:'#2a2a44',style:'B'},
 {id:'proyectos',name:'PROYECTOS',cx:160,shirt:'#3aa066',hair:'#1a1a1a',skin:'#c68e65',tint:'#3fa66a',neon:'#4dffa0',pants:'#2a3a30',style:'A'},
 {id:'diagnostico',name:'DIAGNOSTICO',cx:224,shirt:'#d8982a',hair:'#8a5a2b',skin:'#f2c9a0',tint:'#e0a030',neon:'#ffc233',pants:'#3a2c20',style:'C'},
 {id:'proyecciones',name:'PROYECCIONES',cx:288,shirt:'#9a58d0',hair:'#d9531e',skin:'#f4d0b0',tint:'#a060d8',neon:'#c78bff',pants:'#2e2440',style:'B'}];
const COF={x:300,y:152},BEN={x:128,y:156};

/* ------------------------------------------------ fondo estático */
function poster(g,i,cx){
 const x=cx-27,y=54;R(g,x,y,20,24,'#120a0e');R(g,x+1,y+1,18,22,'#2a1a22');
 if(i===1){R(g,x+2,y+2,16,20,'#e8e4d4');for(let r=0;r<5;r++){R(g,x+3,y+4+r*4,14,1,'#6b6b6b');R(g,x+12,y+3+r*4,4,2,'#3f6fd0');}}
 if(i===2){R(g,x+2,y+2,16,20,'#1f4b8a');R(g,x+3,y+5,8,2,'#cfe8ff');R(g,x+6,y+9,10,2,'#cfe8ff');R(g,x+9,y+13,7,2,'#cfe8ff');R(g,x+3,y+17,12,2,'#cfe8ff');}
 if(i===3){R(g,x+2,y+2,16,20,'#0c1418');[[3,12],[4,12],[5,12],[6,8],[7,16],[8,12],[9,12],[10,12],[11,12],[12,9],[13,15],[14,12],[15,12],[16,12]].forEach(p=>R(g,x+p[0],y+p[1],1,2,'#4dffa0'));}
 if(i===4){R(g,x+2,y+2,16,20,'#13202e');for(let k=0;k<13;k++)R(g,x+4+k,y+18-Math.round(k*0.9)-(k%3===0?1:0),2,2,'#c78bff');R(g,x+14,y+5,4,1,'#c78bff');R(g,x+17,y+5,1,4,'#c78bff');}
 if(i===0){R(g,x+2,y+2,16,20,'#e6d9a8');R(g,x+4,y+5,12,1,'#8a7a40');R(g,x+4,y+8,12,1,'#8a7a40');R(g,x+8,y+13,5,5,'#b02440');}
}
function drawBG(){
 const g=bg.getContext('2d');
 R(g,0,0,W,H,'#1a0b14');R(g,0,0,W,14,'#12070d');R(g,0,12,W,2,'#2a1220');
 R(g,0,14,W,112,'#3a1424');
 for(let y=16;y<96;y+=8)for(let x=((y/8)%2)*4;x<W;x+=8){R(g,x+2,y,1,1,'#4d1c32');R(g,x+1,y+1,3,1,'#4d1c32');R(g,x+2,y+2,1,1,'#4d1c32');R(g,x+2,y+5,1,1,'#2e1020');}
 AREAS.forEach((a,i)=>{g.globalAlpha=.17;R(g,i*64+4,40,56,86,a.tint);g.globalAlpha=1;});
 R(g,0,96,W,30,'#2a1019');for(let x=0;x<W;x+=6)R(g,x,98,1,28,'#1c0a12');
 R(g,0,95,W,2,'#6a2f40');R(g,0,97,W,1,'#3a1a26');R(g,0,124,W,3,'#4a2432');R(g,0,126,W,1,'#14080e');
 R(g,0,127,W,53,'#3a2228');
 const ys=[127,132,138,145,153,162,172,180];
 for(let k=0;k<ys.length-1;k++){R(g,0,ys[k],W,1,'#241218');R(g,0,ys[k]+1,W,1,'#46292f');
  for(let x=(k*37)%53;x<W;x+=48+Math.floor(rr()*14))R(g,x,ys[k],1,ys[k+1]-ys[k],'#241218');}
 R(g,62,146,196,28,'#5a1a2a');R(g,64,148,192,24,'#3d1220');for(let x=66;x<254;x+=8)R(g,x,150,4,20,'#4a1626');R(g,62,146,196,1,'#7a2a3a');
 for(let i=0;i<=5;i++){const px=i===0?0:i===5?W-4:i*64-2;R(g,px,36,4,90,'#1f0d14');R(g,px+1,36,1,90,'#3a1a26');}
 R(g,0,34,W,6,'#231019');R(g,0,34,W,1,'#4a2432');
 AREAS.forEach((a,i)=>{const x0=i*64,cx=a.cx;
  R(g,x0+6,20,52,14,'#10060b');R(g,x0+6,20,52,1,'#3a1a26');R(g,x0+6,33,52,1,'#3a1a26');
  poster(g,i,cx);
  R(g,cx+8,66,24,2,'#6a4430');R(g,cx+9,59,3,7,'#a33a3a');R(g,cx+12,58,2,8,'#3a6ab0');R(g,cx+14,60,3,6,'#3a9a60');R(g,cx+20,62,5,4,'#b45309');R(g,cx+20,57,5,5,'#2fbf5b');
  R(g,cx,40,1,15,'#0c0508');R(g,cx-6,55,13,2,'#d9a441');R(g,cx-4,53,9,2,'#b88331');
  R(g,cx-7,96,14,22,'#3a2030');R(g,cx-6,97,12,2,'#5a3248');R(g,cx-6,99,1,19,'#2a1220');
 });
 // frente: escritorios
 const f=fg.getContext('2d');
 AREAS.forEach((a,i)=>{const cx=a.cx,hw=i===0?20:18;
  R(f,cx-hw,112,hw*2,2,'#b07a4a');R(f,cx-hw,112,hw*2,1,'#d09a62');
  R(f,cx-hw,114,hw*2,10,i===0?'#4a2a22':'#6a4430');R(f,cx-hw,114,hw*2,1,'#3a2018');
  R(f,cx+4,116,hw-5,7,'#583626');R(f,cx+hw-9,119,3,1,'#d9a441');R(f,cx-hw,124,hw*2,1,'#14080e');
  if(i===0){R(f,cx-7,117,12,3,'#d9a441');R(f,cx-6,118,10,1,'#8a6a20');}
  R(f,cx-8,105,16,7,'#8f9aa8');R(f,cx-8,105,16,1,'#c0c8d2');R(f,cx-1,108,2,2,'#e8eef4');
  R(f,cx+hw-9,108,3,4,'#e8e0d0');R(f,cx+hw-6,109,1,2,'#e8e0d0');
 });
}
/* ------------------------------------------------ luces */
function drawLights(){
 const g=gl.getContext('2d');
 const rad=(x,y,r,c0)=>{const q=g.createRadialGradient(x,y,0,x,y,r);q.addColorStop(0,c0);q.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=q;g.fillRect(x-r,y-r,r*2,r*2);};
 AREAS.forEach(a=>{rad(a.cx,60,44,'rgba(255,170,70,.30)');rad(a.cx,112,30,'rgba(255,190,100,.16)');rad(a.cx,27,34,hex(a.neon,.20));});
 rad(COF.x,COF.y-18,26,'rgba(255,70,90,.14)');
 const v=vg.getContext('2d');const q=v.createRadialGradient(160,92,40,160,92,210);q.addColorStop(0,'rgba(10,0,14,0)');q.addColorStop(1,'rgba(10,0,14,.62)');v.fillStyle=q;v.fillRect(0,0,W,H);
}
function hex(h,a){return 'rgba('+parseInt(h.slice(1,3),16)+','+parseInt(h.slice(3,5),16)+','+parseInt(h.slice(5,7),16)+','+a+')';}

/* ------------------------------------------------ actores */
let T=0,DT=0;
const actors=AREAS.map((a,i)=>({i,home:a,look:a,x:a.cx,y:122,dir:0,pose:'sitwork',say:'',kind:'',free:false,hold:false,gen:null,seat:'sitwork'}));
const PAPER={at:null,k:0},HAND={arrived:false,given:false};

function* go(a,pts,sp){sp=sp||SP;for(const p of pts){for(;;){const dx=p[0]-a.x,dy=p[1]-a.y,d=Math.hypot(dx,dy),st=sp*DT;
 if(d<=st){a.x=p[0];a.y=p[1];break;}a.x+=dx/d*st;a.y+=dy/d*st;if(Math.abs(dx)>.4)a.dir=Math.sign(dx);a.pose='walk';yield;}}a.pose='stand';}
function* wait(a,ms,pose){if(pose)a.pose=pose;let t=0;while(t<ms){t+=DT*1000;yield;}}
function* leaveDesk(a){const c=a.home.cx;a.dir=0;yield* wait(a,300,'stand');yield* go(a,[[c+24,122],[c+24,HY]]);}
function* enterDesk(a){const c=a.home.cx;yield* go(a,[[a.x,HY],[c+24,HY],[c+24,122],[c,122]]);a.dir=0;yield* wait(a,250,'stand');a.pose='sitwork';}

/* conductas libres */
function* coffee(a){yield* leaveDesk(a);yield* go(a,[[COF.x-16,HY]]);a.dir=1;
 a.say=pick(['Un cafecito','Necesito cafe']);yield* wait(a,1000,'stand');a.say='';
 yield* wait(a,4200,'coffee');a.say=pick(['Ahhh, que rico','Ya revivi']);yield* wait(a,1300,'stand');a.say='';yield* enterDesk(a);}
function* stroll(a){yield* leaveDesk(a);const n=2+Math.floor(Math.random()*2);
 for(let k=0;k<n;k++){yield* go(a,[[rnd(20,300),rnd(150,168)]]);yield* wait(a,rnd(700,1800),'stand');}yield* enterDesk(a);}
function* readBench(a){yield* leaveDesk(a);yield* go(a,[[BEN.x,BEN.y]]);a.dir=1;yield* wait(a,rnd(6000,9000),'benchread');yield* wait(a,500,'stand');yield* enterDesk(a);}
function* nap(a){yield* wait(a,rnd(6000,9000),'sleep');a.dir=0;a.say='Uf, me dormi...';yield* wait(a,1500,'sitwork');a.say='';}
const DIAL=[["Revisaste el balance?","Si, todo cuadra... casi","Casi?","Faltan 90 mil, ja"],
 ["Almorzamos?","Donde?","Donde sea, hambre!","Dale, vamos"],
 ["Que calor hoy!","Si, ni se respira","Y el ventilador?","Esta de adorno"],
 ["Viste las ventas?","Subieron un 12%","Excelente!","Eso espero..."],
 ["El jefe anda serio","Sera el cierre","Mejor trabajemos","Si, si"]];
function* chat(a){const c=actors.filter(b=>b!==a&&b.free);if(!c.length){yield* wait(a,1500);return;}
 const b=pick(c);b.free=false;const m={bx:false,done:false};
 const mx=clamp((a.home.cx+b.home.cx)/2+rnd(-14,14),40,280);
 b.gen=(function*(){yield* leaveDesk(b);yield* go(b,[[mx+10,HY]]);b.dir=-1;m.bx=true;while(!m.done)yield;yield* enterDesk(b);})();
 yield* leaveDesk(a);yield* go(a,[[mx-10,HY]]);a.dir=1;while(!m.bx)yield;
 const L=pick(DIAL);for(let i=0;i<L.length;i++){const sp=i%2?b:a,ls=i%2?a:b;sp.say=L[i];sp.pose='talk';ls.pose='stand';ls.say='';yield* wait(a,1900);}
 a.say='';b.say='';m.done=true;yield* enterDesk(a);}
function* idle(a,first){a.free=true;yield* wait(a,first||rnd(2500,7000),a.seat);
 for(;;){a.free=true;yield* wait(a,rnd(2500,7000),'sitwork');a.free=false;const r=Math.random();
  if(r<.20)yield* nap(a);else if(r<.42)yield* coffee(a);else if(r<.60)yield* stroll(a);else if(r<.76)yield* readBench(a);else yield* chat(a);}}

/* guiones de la historia */
function* sGerente(a){PAPER.at=0;a.say='Revisando documento...';for(;;)yield* wait(a,500,'sitread');}
function* sAreaM(a,k){const w=actors[k];PAPER.at=0;a.say='Documento recibido';yield* wait(a,1100,'sitread');
 a.say='Esto es para '+AREAS[k].name;yield* wait(a,900,'sitread');a.say='';PAPER.at=null;a.hold=true;
 yield* leaveDesk(a);yield* go(a,[[w.home.cx+24,HY],[w.home.cx+24,122]]);a.dir=-1;
 HAND.arrived=true;a.say='Para ti';yield* wait(a,700,'hand');while(!HAND.given)yield;a.hold=false;PAPER.at=k;
 yield* wait(a,500,'stand');a.say='';
 yield* go(a,[[w.home.cx+24,HY],[a.home.cx+24,HY],[a.home.cx+24,122],[a.home.cx,122]]);a.dir=0;yield* wait(a,250,'stand');a.pose='sitwork';}
function* sAreaW(a){a.pose='sitwork';while(!HAND.arrived)yield* wait(a,100,'sitwork');
 yield* wait(a,900,'receive');HAND.given=true;a.say='Recibido';yield* wait(a,900,'sitwork');a.say='@work';for(;;)yield* wait(a,500,'sitwork');}
function* sListoW(a,k){const m=actors[0];PAPER.at=k;a.pose='sitwork';yield* wait(a,500,'sitwork');
 a.say='Listo!';a.kind='ok';yield* wait(a,1400,'sitwork');PAPER.at=null;a.hold=true;a.say='';a.kind='';
 yield* leaveDesk(a);yield* go(a,[[m.home.cx+24,HY],[m.home.cx+24,122]]);a.dir=-1;
 HAND.arrived=true;a.say='Aqui esta el informe';yield* wait(a,1500,'hand');HAND.given=true;a.hold=false;PAPER.at=0;a.say='';
 yield* wait(a,500,'stand');yield* go(a,[[m.home.cx+24,HY],[a.home.cx+24,HY],[a.home.cx+24,122],[a.home.cx,122]]);a.dir=0;yield* wait(a,250,'stand');a.pose='sitwork';}
function* sListoM(a){a.pose='sitwork';while(!HAND.arrived)yield* wait(a,100,'sitwork');yield* wait(a,1100,'receive');
 while(!HAND.given)yield;a.say='Excelente trabajo!';a.kind='ok';yield* wait(a,1800,'sitread');a.say='Trabajo terminado';yield* wait(a,2200,'sitread');a.say='';a.kind='';PAPER.at=null;}

const K=ORD(CFG.area);function ORD(id){return AREAS.findIndex(x=>x.id===id);}
actors.forEach(a=>{a.gen=idle(a,rnd(1200,4000));});
if(CFG.estado==='gerente'){actors[0].gen=sGerente(actors[0]);actors[0].free=false;actors.slice(1).forEach(a=>a.gen=idle(a,rnd(6000,12000)));}
if(CFG.estado==='area'&&K>0){actors[0].gen=sAreaM(actors[0],K);actors[K].gen=sAreaW(actors[K]);actors.forEach(a=>{if(a.i!==0&&a.i!==K)a.gen=idle(a,rnd(5000,12000));});}
if(CFG.estado==='listo'&&K>0){actors[0].gen=sListoM(actors[0]);actors[K].gen=sListoW(actors[K],K);actors.forEach(a=>{if(a.i!==0&&a.i!==K)a.gen=idle(a,rnd(5000,12000));});}

/* ------------------------------------------------ dibujo de personajes */
function paperSprite(x,y){R(ctx,x,y,6,7,'#111');R(ctx,x+1,y+1,4,5,'#f6f2e8');R(ctx,x+1,y+2,4,1,'#a0a8b4');R(ctx,x+1,y+4,3,1,'#a0a8b4');}
function person(a,front){
 const L=a.look,x=Math.round(a.x),y=Math.round(a.y),d=a.dir||1,sx=a.dir||0,p=a.pose;
 const seatd=(p==='sitwork'||p==='sitread'||p==='receive'||p==='sleep'),bench=p==='benchread';
 if((p==='sleep')!==!!front)return;
 let bob=0,lf=0,rf=0,aL=0,aR=0;
 if(p==='walk'){const f=Math.floor(T*9)%4;bob=f%2?1:0;lf=f===0?0:f===2?2:1;rf=f===2?0:f===0?2:1;aL=f===0?-1:f===2?1:0;aR=-aL;}
 const dy=seatd?3:bench?2:0,bt=y-20-bob+dy,ht=bt-8;
 if(!seatd)R(ctx,x-6,y,12,1,'rgba(0,0,0,.35)');
 if(p==='sleep'){ // cabeza sobre el escritorio
  R(ctx,x-5,106,10,5,L.shirt);R(ctx,x-9,109,18,3,L.shirt);R(ctx,x-4,103,9,6,L.skin);R(ctx,x-4,102,9,3,L.hair);R(ctx,x-3,107,2,1,'#1a1a1a');R(ctx,x+1,107,2,1,'#1a1a1a');return;}
 // piernas
 if(!seatd){
  if(bench){R(ctx,x,y-8,d>0?8:-8,4,L.pants);R(ctx,d>0?x+5:x-8,y-5,3,5,L.pants);R(ctx,d>0?x+5:x-8,y-1,4,1,'#15101a');R(ctx,x-d*4,y-9,4,5,L.pants);}
  else{R(ctx,x-4,y-10-bob,4,10+bob-lf,L.pants);R(ctx,x+1,y-10-bob,4,10+bob-rf,L.pants);R(ctx,x-4,y-lf-2,4,2,'#15101a');R(ctx,x+1,y-rf-2,4,2,'#15101a');}
 }
 // torso
 R(ctx,x-5,bt,10,10,L.shirt);R(ctx,x-5,bt+8,10,2,'rgba(0,0,0,.18)');
 if(L.suit){R(ctx,x-1,bt,2,6,'#ece8f0');R(ctx,x,bt+1,1,7,'#e0284a');R(ctx,x-5,bt,2,10,'#5e1630');R(ctx,x+3,bt,2,10,'#5e1630');}
 // brazos
 const sk=L.skin,sh=L.shirt;
 const arm=(ax,ay,h)=>{R(ctx,ax,ay,2,h,sh);R(ctx,ax,ay+h-1,2,2,sk);};
 if(p==='hand'||p==='receive'){
  const ex=p==='hand'?(d>0?x+4:x-12):x+4,w=8;R(ctx,ex,bt+3,w,2,sh);R(ctx,d>0||p==='receive'?ex+w:ex-1,bt+3,2,2,sk);
  if(p==='hand'&&a.hold)paperSprite(p==='hand'&&d>0?ex+w:ex-6,bt-1);
  arm(d>0&&p==='hand'?x-7:x-7,bt+1,9);
 }else if(p==='coffee'){const up=Math.floor(T*1.0)%2===0,ax=d>0?x+5:x-7;arm(d>0?x-7:x+5,bt+1,9);
  R(ctx,ax,bt+1,2,5,sh);const cx=d>0?x+5:x-7;R(ctx,cx,up?bt-4:bt+3,3,4,'#f4ecdc');R(ctx,cx,up?bt-4:bt+3,3,1,'#6a3a1a');if(up){R(ctx,cx,bt-1,2,2,sk);R(ctx,cx+1,bt-7+Math.floor(T*4)%2,1,2,'rgba(255,255,255,.5)');}}
 else if(p==='read'||p==='benchread'){arm(x-7,bt+1,6);arm(x+5,bt+1,6);R(ctx,x-4,bt+2,8,6,'#b02440');R(ctx,x-3,bt+3,6,4,'#f0e8d0');R(ctx,x,bt+3,1,4,'#b8a888');}
 else if(p==='talk'){const up=Math.floor(T*2)%2;arm(x-7,bt+1+aL,9);R(ctx,x+5,bt+(up?-3:1),2,up?7:9,sh);R(ctx,x+5,bt+(up?-4:8),2,2,sk);}
 else if(p==='sitwork'||p==='sitread'){const k=p==='sitwork'?Math.floor(T*10)%2:0;
  R(ctx,x-7,bt+1,2,6,sh);R(ctx,x+5,bt+1,2,6,sh);R(ctx,x-10,110+(k?-1:0),3,2,sk);R(ctx,x+7,110+(k?0:-1),3,2,sk);R(ctx,x-9,108,2,3,sh);R(ctx,x+7,108,2,3,sh);}
 else{arm(x-7,bt+1+aL,9);arm(x+5,bt+1+aR,9);}
 // cabeza
 const sm=p==='sitread'||p==='read'||p==='benchread'?1:0;
 R(ctx,x-4,ht,8,8,L.skin);
 if(L.style==='A'){R(ctx,x-4,ht,8,3,L.hair);R(ctx,x-4,ht+3,1,2,L.hair);R(ctx,x+3,ht+3,1,2,L.hair);}
 if(L.style==='B'){R(ctx,x-4,ht-1,8,4,L.hair);R(ctx,x-5,ht,2,11,L.hair);R(ctx,x+3,ht,2,11,L.hair);}
 if(L.style==='C'){R(ctx,x-4,ht,8,2,L.hair);R(ctx,x-4,ht+2,1,2,L.hair);R(ctx,x+3,ht+2,1,2,L.hair);R(ctx,x-3,ht+6,6,2,L.hair);}
 const ey=ht+4+sm;R(ctx,x-2+sx,ey,1,2,'#1a1a1a');R(ctx,x+1+sx,ey,1,2,'#1a1a1a');
 const open=p==='talk'&&Math.floor(T*6)%2;R(ctx,x-1+sx,ey+3,2,open?2:1,'#a0574a');
 if(p==='sitwork'){ctx.globalAlpha=.28;R(ctx,x-4,ht+3,8,3,'#7fd0ff');ctx.globalAlpha=1;}
 if(a.hold&&p!=='hand'&&p!=='stand'){paperSprite(d>0?x+5:x-11,bt+4);}
 if(a.hold&&p==='stand'&&!HAND.arrived)paperSprite(d>0?x+5:x-11,bt+4);
}
const props=[
 {y:COF.y,draw(){const x=COF.x,y=COF.y;R(ctx,x-9,y-32,18,3,'#5a1a28');R(ctx,x-8,y-30,16,30,'#8a2a3a');R(ctx,x-8,y-30,2,30,'#a33a4a');R(ctx,x-5,y-26,10,6,'#0c0a0e');R(ctx,x-4,y-25,Math.floor(T*2)%2?5:3,1,'#4dffa0');R(ctx,x-2,y-17,4,3,'#2a2a2a');R(ctx,x-2,y-13,4,5,'#f4ecdc');R(ctx,x-7,y-6,14,2,'#2a2a2a');R(ctx,x-6,y-4,2,4,'#3a1018');R(ctx,x+4,y-4,2,4,'#3a1018');}},
 {y:BEN.y-2,draw(){const x=BEN.x,y=BEN.y-2;R(ctx,x-17,y-26,34,3,'#5a3828');R(ctx,x-15,y-23,2,12,'#4a2e20');R(ctx,x+13,y-23,2,12,'#4a2e20');R(ctx,x-17,y-12,34,4,'#7a5038');R(ctx,x-17,y-12,34,1,'#9a6a48');R(ctx,x-15,y-8,3,8,'#3a2418');R(ctx,x+12,y-8,3,8,'#3a2418');}},
 {y:168,draw(){const x=10,y=168;R(ctx,x-5,y-8,10,8,'#7a3a1a');R(ctx,x-8,y-22,16,14,'#1f8f4a');R(ctx,x-5,y-26,10,6,'#2fbf5b');R(ctx,x-1,y-12,2,6,'#16753a');}},
 {y:168,draw(){const x=311,y=168;R(ctx,x-5,y-8,10,8,'#7a3a1a');R(ctx,x-8,y-22,16,14,'#1f8f4a');R(ctx,x-5,y-26,10,6,'#2fbf5b');R(ctx,x-1,y-12,2,6,'#16753a');}}];
function fan(){const cx=160,cy=9,a=T*5;R(ctx,cx,0,1,5,'#241018');R(ctx,cx-2,5,5,3,'#5a2a38');
 for(let k=0;k<4;k++){const an=a+k*Math.PI/2,ex=cx+Math.cos(an)*30,ey=cy+Math.sin(an)*5,n=14;
  for(let s=1;s<=n;s++){const px=cx+(ex-cx)*s/n,py=cy+(ey-cy)*s/n;R(ctx,px,py,2,Math.sin(an)>0?2:1,Math.sin(an)>0?'#7a3a48':'#4a2230');}}}

/* ------------------------------------------------ DOM: neones, burbujas, HUD */
const stage=document.getElementById('stage'),neons=document.getElementById('neons'),bubs=document.getElementById('bubs');
const nEls=AREAS.map((a,i)=>{const e=document.createElement('div');e.className='neon';e.textContent=a.name;e.style.cssText='left:'+((i*64+6)/W*100)+'%;top:'+(20/H*100)+'%;width:'+(52/W*100)+'%;height:'+(14/H*100)+'%;color:'+a.neon;neons.appendChild(e);return e;});
const bEls=actors.map(()=>{const e=document.createElement('div');e.className='bub';bubs.appendChild(e);return e;});
nEls.forEach((e,i)=>{if((CFG.estado==='gerente'&&i===0)||((CFG.estado==='area'||CFG.estado==='listo')&&i===K))e.classList.add('on');});
function layout(){stage.style.setProperty('--s',cv.clientWidth/W);}window.addEventListener('resize',layout);layout();
const NOM=K>0?AREAS[K].name:'';
document.getElementById('ht').textContent={espera:'ESPERANDO DOCUMENTO',gerente:'GERENTE REVISANDO',area:NOM+' TRABAJANDO',listo:'MISION COMPLETA!'}[CFG.estado]||'';
const nb={espera:0,gerente:3,area:7,listo:10}[CFG.estado]||0,hb=document.getElementById('hb');
for(let i=0;i<10;i++){const s=document.createElement('span');if(i<nb)s.className=(i===nb-1&&CFG.estado!=='listo')?'f p':'f';hb.appendChild(s);}
function bubbles(){actors.forEach((a,i)=>{const e=bEls[i];let t=a.say;
 if(t==='@work')t='Calculando'+'.'.repeat(1+Math.floor(T*2)%3);
 if(a.pose==='sleep'&&!t)t=['z','zz','zzz'][Math.floor(T*1.5)%3];
 if(!t){e.style.display='none';return;}
 e.style.display='block';e.textContent=t;e.className='bub'+(a.kind==='ok'?' ok':'');
 const seat=(a.pose==='sitwork'||a.pose==='sitread'||a.pose==='receive'||a.pose==='sleep');
 e.style.left=clamp(a.x/W*100,14,86)+'%';e.style.top=((a.y-(seat?30:36))/H*100)+'%';});}

/* ------------------------------------------------ bucle */
drawBG();drawLights();
let last=performance.now();
function frame(now){DT=Math.min(.05,(now-last)/1000);last=now;T+=DT;
 actors.forEach(a=>{const r=a.gen.next();if(r.done)a.gen=idle(a,rnd(2500,5000));});
 ctx.drawImage(bg,0,0);fan();
 actors.filter(a=>a.y<=125).sort((p,q)=>p.y-q.y).forEach(a=>person(a,false));
 ctx.drawImage(fg,0,0);
 actors.filter(a=>a.pose==='sleep').forEach(a=>person(a,true));
 if(PAPER.at!==null){const h=AREAS[PAPER.at];R(ctx,h.cx-17,109,8,3,'#f6f2e8');R(ctx,h.cx-16,110,5,1,'#a0a8b4');}
 const hall=[...props.map(p=>({y:p.y,f:()=>p.draw()})),...actors.filter(a=>a.y>125).map(a=>({y:a.y,f:()=>person(a,false)}))].sort((p,q)=>p.y-q.y);
 hall.forEach(o=>o.f());
 ctx.globalCompositeOperation='lighter';ctx.globalAlpha=.8+.2*Math.sin(T*3.1)*Math.sin(T*1.7);ctx.drawImage(gl,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
 ctx.drawImage(vg,0,0);bubbles();requestAnimationFrame(frame);}
requestAnimationFrame(frame);
})();
</script></body></html>"""


def html_oficina(estado="espera", area=None, mensaje=""):
    """estado: espera | gerente | area | listo"""
    cfg = json.dumps({"estado": estado, "area": area, "mensaje": mensaje})
    return (PLANTILLA.replace("__CFG__", cfg)
            .replace("__CARRIL__", str(CARRIL)).replace("__VEL__", str(VELOCIDAD)))
