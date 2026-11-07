"""Oficina virtual pixel-art (ambiente de club oscuro con neones).
La escena es UN solo iframe que se mantiene vivo; Python le manda órdenes (gerente / area / listo)
por mensajes, así las animaciones no se cortan ni se reinician al cargar documentos."""
import json
import time

CX = {"gerente": 48, "contabilidad": 144, "proyectos": 240, "diagnostico": 336, "proyecciones": 432}
VELOCIDAD = 96   # px lógicos/segundo (mismo valor que en el JavaScript)


def duracion_area(area: str) -> float:
    """Segundos aproximados que tarda el gerente en levantarse, caminar y entregar el documento."""
    dist = 52 + abs(CX[area] - CX["gerente"]) + 52
    return 5.0 + dist / VELOCIDAD


def comando_html(estado: str, area: str | None = None) -> str:
    """Mini-iframe invisible que le avisa a la escena qué hacer."""
    msg = json.dumps({"oficina": 1, "estado": estado, "area": area, "id": time.time()})
    return ("<script>(function(){var m=" + msg + ";var f=window.parent.frames;"
            "for(var i=0;i<f.length;i++){try{f[i].postMessage(m,'*')}catch(e){}}})();</script>")


ESCENA = r"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
html,body{margin:0;background:transparent;overflow:hidden}
#wrap{max-width:960px;margin:0 auto;border:4px solid #0b0508;box-sizing:border-box;background:#0b0508;border-radius:4px}
#stage{position:relative;--s:2}
canvas{display:block;width:100%;height:auto;image-rendering:pixelated;image-rendering:crisp-edges}
.neon{position:absolute;display:flex;align-items:center;justify-content:center;font-family:'Press Start 2P',monospace;
 font-size:calc(var(--s)*5.4px);white-space:nowrap;opacity:.8;animation:fl 7s steps(1) infinite;pointer-events:none;
 text-shadow:0 0 calc(var(--s)*1.5px) currentColor,0 0 calc(var(--s)*5px) currentColor}
.neon.on{opacity:1;animation:none;text-shadow:0 0 calc(var(--s)*1px) #fff,0 0 calc(var(--s)*4px) currentColor,0 0 calc(var(--s)*10px) currentColor}
@keyframes fl{0%,91%,95%,100%{opacity:.8}92%,96%{opacity:.3}}
.bub{position:absolute;transform:translate(-50%,-100%);background:#f6f0e0;color:#1a0c12;border:calc(var(--s)*1px) solid #0b0508;
 padding:calc(var(--s)*1.6px) calc(var(--s)*2.4px);font-family:'Press Start 2P',monospace;font-size:calc(var(--s)*4.2px);line-height:1.5;
 text-align:center;max-width:30%;display:none;pointer-events:none;z-index:3;box-shadow:0 calc(var(--s)*1.2px) 0 rgba(0,0,0,.45)}
.bub::after{content:"";position:absolute;left:50%;bottom:calc(var(--s)*-3.4px);margin-left:calc(var(--s)*-1.6px);border:calc(var(--s)*1.7px) solid transparent;border-top-color:#0b0508;border-bottom:0}
.bub.ok{background:#c9f7d4}
#hud{display:flex;justify-content:space-between;align-items:center;background:#0b0508;border-top:2px solid #ff4d78;padding:8px 12px;
 font-family:'Press Start 2P',monospace;font-size:11px;color:#f6e8d8}
#hb span{display:inline-block;width:11px;height:11px;margin-left:4px;background:#2a1a22}
#hb span.f{background:#38d66b}#hb span.p{animation:pp .5s steps(1) infinite}@keyframes pp{50%{opacity:.2}}
</style></head><body>
<div id="wrap"><div id="stage"><canvas id="c" width="480" height="270"></canvas><div id="neons"></div><div id="bubs"></div></div>
<div id="hud"><span id="ht">ESPERANDO DOCUMENTO</span><span id="hb"></span></div></div>
<script>
(()=>{
const W=480,H=270,ENT=184,HY=236,SP=__VEL__,STRIDE=46,TAU=6.2832;
const cv=document.getElementById('c'),ctx=cv.getContext('2d');ctx.imageSmoothingEnabled=false;
const mk=(w,h)=>{const c=document.createElement('canvas');c.width=w||W;c.height=h||H;return c;};
const bg=mk(),fg=mk(),gl=mk(),vg=mk();
const R=(c,x,y,w,h,col)=>{c.fillStyle=col;c.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));};
const rnd=(a,b)=>a+Math.random()*(b-a),pick=a=>a[Math.floor(Math.random()*a.length)],clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
let seed=11;const rr=()=>{seed=(seed*16807)%2147483647;return (seed-1)/2147483646;};

const AREAS=[
 {id:'gerente',name:'GERENCIA',cx:48,vest:'#6a1c3a',hair:'#2a2630',skin:'#e6b48c',pants:'#221a2c',neon:'#ff4d78',tint:'#c0334d',st:'A',tie:1},
 {id:'contabilidad',name:'CONTABILIDAD',cx:144,vest:'#2f5fb8',hair:'#e0508a',skin:'#f1c9a5',pants:'#2a2a44',neon:'#5aa8ff',tint:'#4a7bd0',st:'B',long:1},
 {id:'proyectos',name:'PROYECTOS',cx:240,vest:'#2a8a58',hair:'#1c1a1e',skin:'#b98258',pants:'#26332c',neon:'#4dffa0',tint:'#3fa66a',st:'C',beard:1},
 {id:'diagnostico',name:'DIAGNOSTICO',cx:336,vest:'#c0801e',hair:'#c9a050',skin:'#f4d0b0',pants:'#3a2c20',neon:'#ffc233',tint:'#e0a030',st:'D',glasses:1},
 {id:'proyecciones',name:'PROYECCIONES',cx:432,vest:'#8a48c0',hair:'#c8501e',skin:'#f6d6bc',pants:'#2e2440',neon:'#c78bff',tint:'#a060d8',st:'E',curly:1}];
const COF={x:438,y:226},BEN={x:190,y:246};

/* ============ motor de sprites: cápsulas y elipses con sombreado de 3 tonos ============ */
const BW=96,BH=104,OX=48,OY=92,img=new ImageData(BW,BH),px=new Uint32Array(img.data.buffer),tmp=mk(BW,BH),tctx=tmp.getContext('2d');
const hx=h=>[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];
const mx=(a,b,t)=>[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t];
const c32=c=>(255<<24)|(Math.round(c[2])<<16)|(Math.round(c[1])<<8)|Math.round(c[0]);
const RC={};function ramp(h,far){const k=h+(far?'f':'');if(RC[k])return RC[k];let b=hx(h);if(far)b=mx(b,[24,10,32],.38);
 return RC[k]=[c32(mx(b,[14,5,22],.8)),c32(mx(b,[26,10,40],.42)),c32(b),c32(mx(b,[255,236,210],.26))];}
function cap(ax,ay,bx,by,r,rp){ax+=OX;ay+=OY;bx+=OX;by+=OY;const x0=Math.floor(Math.min(ax,bx)-r-2),x1=Math.ceil(Math.max(ax,bx)+r+2),y0=Math.floor(Math.min(ay,by)-r-2),y1=Math.ceil(Math.max(ay,by)+r+2);
 const dx=bx-ax,dy=by-ay,L2=dx*dx+dy*dy||1e-6;
 for(let y=Math.max(0,y0);y<=Math.min(BH-1,y1);y++)for(let x=Math.max(0,x0);x<=Math.min(BW-1,x1);x++){
  let t=((x+.5-ax)*dx+(y+.5-ay)*dy)/L2;t=t<0?0:t>1?1:t;const ox=x+.5-(ax+dx*t),oy=y+.5-(ay+dy*t),d=Math.sqrt(ox*ox+oy*oy);
  if(d>r+.9)continue;if(d>r){px[y*BW+x]=rp[0];continue;}
  const lit=(-ox*.55-oy*.83)/Math.max(d,.01)*Math.min(1,d/r*1.3);px[y*BW+x]=lit>.4?rp[3]:lit<-.2?rp[1]:rp[2];}}
function ell(cx,cy,rx,ry,rp){cx+=OX;cy+=OY;const m=Math.min(rx,ry),o=((m+.9)/m);
 for(let y=Math.max(0,Math.floor(cy-ry-2));y<=Math.min(BH-1,Math.ceil(cy+ry+2));y++)for(let x=Math.max(0,Math.floor(cx-rx-2));x<=Math.min(BW-1,Math.ceil(cx+rx+2));x++){
  const nx=(x+.5-cx)/rx,ny=(y+.5-cy)/ry,n=nx*nx+ny*ny;if(n>o*o)continue;if(n>1){px[y*BW+x]=rp[0];continue;}
  const lit=-(nx*.55+ny*.83);px[y*BW+x]=lit>.42?rp[3]:lit<-.22?rp[1]:rp[2];}}
function pr(x,y,w,h,c){x=Math.round(x+OX);y=Math.round(y+OY);for(let j=0;j<h;j++)for(let i=0;i<w;i++){const X=x+i,Y=y+j;if(X>=0&&Y>=0&&X<BW&&Y<BH)px[Y*BW+X]=c;}}
const K={ink:c32([22,12,24]),white:c32([250,248,240]),mouth:c32([160,87,74]),paper:c32([246,242,232]),pline:c32([160,168,180]),cup:c32([244,236,220]),cof:c32([110,58,26]),redb:c32([176,36,64]),page:c32([240,232,208]),tie:c32([214,40,73])};
function ik(sx,sy,tx,ty,l1,l2,sg){const dx=tx-sx,dy=ty-sy,dd=Math.min(Math.hypot(dx,dy),l1+l2-.05),a=Math.atan2(dy,dx),c=clamp((l1*l1+dd*dd-l2*l2)/(2*l1*dd),-1,1),b=Math.acos(c),e=a+sg*b;
 return [sx+Math.cos(e)*l1,sy+Math.sin(e)*l1,sx+Math.cos(a)*dd,sy+Math.sin(a)*dd];}
function paperAt(x,y){pr(x-1,y-6,9,11,K.ink);pr(x,y-5,7,9,K.paper);pr(x+1,y-3,5,1,K.pline);pr(x+1,y-1,4,1,K.pline);pr(x+1,y+1,5,1,K.pline);}

/* ---- vista de perfil (caminar, café, leer, conversar, entregar) ---- */
function buildSide(a){
 const L=a.look,d=a.dir||1,p=a.pose,ph=a.phase,t=T;
 const sk=ramp(L.skin),skF=ramp(L.skin,1),sh=ramp('#e8e2ee'),shF=ramp('#e8e2ee',1),vs=ramp(L.vest),pn=ramp(L.pants),pnF=ramp(L.pants,1),so=ramp('#1c1220'),soF=ramp('#1c1220',1),hr=ramp(L.hair),hrF=ramp(L.hair,1);
 let thA=0,thB=0,kA=.06,kB=.06,seated=p==='benchread';
 if(p==='walk'){const s=Math.sin(ph),c=Math.cos(ph);thA=.62*s;thB=-.62*s;kA=.1+.9*Math.max(0,c);kB=.1+.9*Math.max(0,-c);}
 const leg=(th,k)=>{const kx=d*Math.sin(th)*14,ky=Math.cos(th)*14,a2=th-k;return{kx,ky,fx:kx+d*Math.sin(a2)*14,fy:ky+Math.cos(a2)*14};};
 let A=leg(thA,kA),B=leg(thB,kB),hipY;
 if(seated){hipY=-14;A={kx:d*14,ky:0,fx:d*13,fy:14};B={kx:d*12,ky:0,fx:d*11,fy:14};}else hipY=-Math.max(A.fy,B.fy);
 const lean=p==='walk'?d*1.5:0,br=(p==='stand'||p==='coffee'||p==='talk')?Math.sin(t*2)*.35:0;
 const Sx=lean*.7+d*1,Sy=hipY-17+br,Hx=Sx+d*1.5+(p==='read'||p==='benchread'?d*1:0),Hy=Sy-10.5+(p==='read'||p==='benchread'?1.5:0);
 // pierna lejana, pierna cercana
 const drawLeg=(g,th,far)=>{const P=far?pnF:pn,S=far?soF:so;cap(0,hipY,g.kx,hipY+g.ky,3.6,P);cap(g.kx,hipY+g.ky,g.fx,hipY+g.fy,3,P);cap(g.fx-d*1.5,hipY+g.fy-1.8,g.fx+d*4.8,hipY+g.fy-1.8,2.2,S);};
 // brazos
 const arm=(far)=>{let ex,ey,hx_,hy_;const S2=far?shF:sh;
  const sx=Sx,sy=Sy;
  if(p==='coffee'&&!far){const u=.5+.5*Math.sin(t*1.4),tx=sx+d*(7-1*u)+(Hx+d*6-sx-d*7)*u,ty=(sy+14)*(1-u)+(Hy+5)*u,r=ik(sx,sy,tx,ty,11,11,d>0?1:-1);ex=r[0];ey=r[1];hx_=r[2];hy_=r[3];}
  else if((p==='read'||p==='benchread')){const r=ik(sx,sy,sx+d*8,sy+9+(far?1:0),11,11,d>0?1:-1);ex=r[0];ey=r[1];hx_=r[2];hy_=r[3];}
  else if(p==='talk'&&!far){const up=Math.max(0,Math.sin(t*3)),r=ik(sx,sy,sx+d*(11+3*Math.sin(t*5)),sy+7-8*up,11,11,d>0?1:-1);ex=r[0];ey=r[1];hx_=r[2];hy_=r[3];}
  else if(p==='hand'&&!far){const r=ik(sx,sy,sx+d*22,sy+5,11,11,d>0?1:-1);ex=r[0];ey=r[1];hx_=r[2];hy_=r[3];}
  else if(a.hold&&!far){const r=ik(sx,sy,sx+d*8,sy+13,11,11,d>0?1:-1);ex=r[0];ey=r[1];hx_=r[2];hy_=r[3];}
  else{const al=(p==='walk'?(far?1:-1)*.62*Math.sin(ph):(far?.05:.08)),f=p==='walk'?.45:.18;ex=sx+d*Math.sin(al)*11;ey=sy+Math.cos(al)*11;hx_=ex+d*Math.sin(al+f)*11;hy_=ey+Math.cos(al+f)*11;}
  cap(sx,sy,ex,ey,2.7,S2);cap(ex,ey,hx_,hy_,2.5,S2);ell(hx_,hy_+.5,2.3,2.3,far?skF:sk);return [hx_,hy_];};
 // cabello trasero + pelo largo
 const hy=Hy,hxp=Hx;
 const armFar=arm(true);
 drawLeg(B,thB,true);drawLeg(A,thA,false);
 // torso (chaleco sobre camisa)
 cap(0,hipY-2,Sx,Sy+1,6.6,sh);cap(d*.8,hipY-3,Sx+d*.8,Sy+2,5.7,vs);
 R_pr_belt();
 function R_pr_belt(){pr(-5,hipY-2,10,2,K.ink);}
 if(L.tie)pr(d>0?Sx+4:Sx-6,Sy+3,2,9,K.tie);
 cap(Sx,Sy-1,Hx,Hy+5,2.5,sk);
 // libro
 if(p==='read'||p==='benchread'){pr(Sx+d*3-(d>0?0:10),Sy+2,10,8,K.ink);pr(Sx+d*3-(d>0?-1:9),Sy+3,8,6,K.redb);pr(Sx+d*3-(d>0?-3:7),Sy+4,4,4,K.page);}
 // cabeza (perfil)
 if(L.long)cap(hxp-d*4,hy,hxp-d*5.5,hy+15,4.4,hr);
 ell(hxp-d*1.6,hy-1.2,7.6,8.6,hr);
 ell(hxp+d*.8,hy+.8,6.4,7.4,sk);
 ell(hxp-d*2.4,hy+1.5,1.8,2.2,sk);
 pr(d>0?hxp+6:hxp-8,hy,2,3,K.ink===0?0:c32(hx(L.skin)));
 ell(hxp+d*3,hy-6.3,4.3,2.5,hr);
 const ey=hy-1+((p==='read'||p==='benchread')?2:0);
 pr(d>0?hxp+3:hxp-5,ey,2,2,K.ink);pr(d>0?hxp+3:hxp-5,ey-2,3,1,c32(hx(L.hair)));
 const open=(p==='talk'&&Math.floor(t*6)%2);pr(d>0?hxp+4:hxp-6,hy+4,2,open?2:1,K.mouth);
 if(L.beard)ell(hxp+d*3,hy+5.5,3.6,3,hr);
 if(L.glasses){pr(d>0?hxp+2:hxp-7,ey-1,5,3,K.ink);pr(d>0?hxp+3:hxp-6,ey,3,1,c32([180,220,240]));}
 // brazo cercano y objetos
 const hn=arm(false);
 if(p==='coffee'){const u=.5+.5*Math.sin(t*1.4);pr(hn[0]+(d>0?-1:-3),hn[1]-6,4,6,K.ink);pr(hn[0]+(d>0?0:-2),hn[1]-5,3,4,K.cup);pr(hn[0]+(d>0?0:-2),hn[1]-5,3,1,K.cof);if(u>.6)pr(hn[0]+1,hn[1]-12+Math.floor(t*4)%2,1,3,c32([255,255,255]));}
 if(a.hold&&(p==='hand'||p==='walk'||p==='stand'))paperAt(hn[0]+(d>0?1:-7),hn[1]-1);
}
/* ---- vista frontal (sentados en su escritorio) ---- */
function buildFront(a){
 const L=a.look,p=a.pose,t=T;
 const sk=ramp(L.skin),sh=ramp('#e8e2ee'),vs=ramp(L.vest),hr=ramp(L.hair),hrB=ramp(L.hair,1);
 const dn=(p==='sitread')?2:0,hy=-49+dn,br=Math.sin(t*2)*.3;
 if(p==='sleep'){cap(-8,-33,8,-33,4.5,vs);cap(-13,-29,13,-29,3.4,sh);ell(0,-33,6.6,5.8,sk);ell(0,-36,7.4,4,hr);pr(-4,-32,3,1,K.ink);pr(1,-32,3,1,K.ink);return;}
 if(L.long||L.curly)ell(0,hy+2,L.curly?10.5:9.2,L.curly?10:11.5,hrB);
 cap(-7,-38+br,7,-38+br,4.2,vs);ell(0,-31,9,9.6,vs);
 pr(-3,-42+br,7,3,c32([232,226,238]));pr(-2,-39+br,5,2,c32([232,226,238]));
 if(L.tie){pr(-1,-40,3,3,K.tie);pr(-1,-37,3,8,K.tie);}else{pr(0,-36,1,1,K.ink);pr(0,-32,1,1,K.ink);pr(0,-28,1,1,K.ink);}
 // brazos
 const k=p==='sitwork'?Math.floor(t*9)%2:0;
 const armL=()=>{const r=ik(-8,-37,-13,-29-(k?1:0),9,9,-1);cap(-8,-37,r[0]-1,r[1],2.6,sh);cap(r[0]-1,r[1],-13,-29-(k?1:0),2.4,sh);ell(-13,-28.5-(k?1:0),2.4,2.2,sk);};
 armL();
 if(p==='receive'){const r=ik(8,-37,28,-36,10,10,1);cap(8,-37,r[0],r[1],2.6,sh);cap(r[0],r[1],r[2],r[3],2.4,sh);ell(r[2],r[3],2.5,2.3,sk);}
 else{const r=ik(8,-37,13,-29-(k?0:1),9,9,1);cap(8,-37,r[0]+1,r[1],2.6,sh);cap(r[0]+1,r[1],13,-29-(k?0:1),2.4,sh);ell(13,-28.5-(k?0:1),2.4,2.2,sk);}
 if(L.long){cap(-7,hy+4,-9,hy+17,3.6,hr);cap(7,hy+4,9,hy+17,3.6,hr);}
 // cabeza
 cap(0,-44,0,-41,3,sk);ell(-6.4,hy+1,1.7,2.3,sk);ell(6.4,hy+1,1.7,2.3,sk);
 ell(0,hy+1,6.3,7.4,sk);
 if(L.st==='A'){ell(0,hy-6.4,7,3.2,hr);pr(-7,hy-4,2,5,c32(hx(L.hair)));pr(5,hy-4,2,5,c32(hx(L.hair)));}
 else if(L.st==='B'){ell(0,hy-6.2,7,3.6,hr);pr(-1,hy-8,1,4,hr[0]);ell(-4,hy-4,3,3,hr);}
 else if(L.st==='C'){ell(0,hy-6.6,7,3,hr);}
 else if(L.st==='D'){ell(0,hy-6.3,7.4,3.6,hr);ell(-6.2,hy+1,2,4,hr);ell(6.2,hy+1,2,4,hr);}
 else{ell(0,hy-6.5,8,4,hr);ell(-7,hy-1,3,3.6,hr);ell(7,hy-1,3,3.6,hr);}
 const ey=hy+(p==='sitread'?1:0);
 pr(-4,ey-2,3,1,c32(hx(L.hair)));pr(2,ey-2,3,1,c32(hx(L.hair)));
 pr(-4,ey,2,2,K.ink);pr(3,ey,2,2,K.ink);pr(-4,ey,1,1,K.white);pr(3,ey,1,1,K.white);
 pr(0,ey+2,1,2,ramp(L.skin)[1]);
 const open=(p==='talk'&&Math.floor(t*6)%2);pr(-1,ey+5,3,open?2:1,K.mouth);
 if(L.beard){ell(0,ey+6.5,4.6,3,hr);pr(-1,ey+5,3,1,K.mouth);}
 if(L.glasses){pr(-5,ey-1,5,4,K.ink);pr(1,ey-1,5,4,K.ink);pr(-4,ey,3,2,c32([190,226,244]));pr(2,ey,3,2,c32([190,226,244]));pr(0,ey,1,1,K.ink);}
}

/* ============ fondo ============ */
function poster(g,i,cx){const x=cx-42,y=80;R(g,x,y,28,34,'#120a0e');R(g,x+2,y+2,24,30,'#2a1a22');
 if(i===1){R(g,x+3,y+3,22,28,'#e8e4d4');for(let r=0;r<6;r++){R(g,x+5,y+6+r*4,18,1,'#6b6b6b');R(g,x+17,y+5+r*4,6,2,'#3f6fd0');}}
 if(i===2){R(g,x+3,y+3,22,28,'#1f4b8a');[[5,7,10],[9,12,12],[13,17,9],[5,22,15]].forEach(q=>R(g,x+q[0],y+q[1],q[2],3,'#cfe8ff'));}
 if(i===3){R(g,x+3,y+3,22,28,'#0c1418');[[4,17],[6,17],[8,17],[10,10],[12,24],[14,17],[16,17],[18,13],[20,20]].forEach(q=>R(g,x+q[0],y+q[1],2,3,'#4dffa0'));}
 if(i===4){R(g,x+3,y+3,22,28,'#13202e');for(let k=0;k<17;k++)R(g,x+5+k,y+26-Math.round(k*1.1)-(k%3===0?1:0),2,2,'#c78bff');}
 if(i===0){R(g,x+3,y+3,22,28,'#e6d9a8');R(g,x+6,y+8,16,2,'#8a7a40');R(g,x+6,y+13,16,2,'#8a7a40');R(g,x+10,y+20,8,8,'#b02440');}}
function drawBG(){
 const g=bg.getContext('2d');
 R(g,0,0,W,H,'#1a0b14');R(g,0,0,W,22,'#12070d');for(let x=0;x<W;x+=48)R(g,x,0,2,22,'#1c0c16');R(g,0,20,W,3,'#2a1220');
 R(g,0,23,W,165,'#3a1424');
 for(let y=26;y<140;y+=10)for(let x=((y/10)%2)*6;x<W;x+=12){R(g,x+4,y,2,2,'#52203a');R(g,x+2,y+2,6,2,'#52203a');R(g,x+4,y+4,2,2,'#52203a');R(g,x+5,y+8,1,1,'#2e1020');}
 AREAS.forEach((a,i)=>{g.globalAlpha=.2;R(g,i*96+6,58,84,130,a.tint);g.globalAlpha=1;});
 R(g,0,142,W,46,'#2a1019');for(let x=0;x<W;x+=8){R(g,x,146,1,42,'#1c0a12');R(g,x+1,146,1,42,'#331522');}
 R(g,0,140,W,3,'#6a2f40');R(g,0,143,W,1,'#3a1a26');R(g,0,184,W,5,'#4a2432');R(g,0,188,W,1,'#14080e');
 R(g,0,189,W,81,'#3a2228');
 const ys=[189,197,206,217,230,246,264,270];
 for(let k=0;k<ys.length-1;k++){R(g,0,ys[k],W,1,'#241218');R(g,0,ys[k]+1,W,1,'#4a2c33');
  for(let x=(k*53)%71;x<W;x+=60+Math.floor(rr()*22))R(g,x,ys[k],1,ys[k+1]-ys[k],'#241218');
  if(k>1)for(let x=(k*31)%40;x<W;x+=44)R(g,x,ys[k]+2+Math.floor(rr()*3),12,1,'#2d1a20');}
 R(g,92,214,300,44,'#5a1a2a');R(g,95,217,294,38,'#3d1220');for(let x=98;x<386;x+=10)R(g,x,220,5,32,'#4a1626');R(g,92,214,300,2,'#7a2a3a');R(g,92,256,300,2,'#2a0c14');
 
 for(let i=0;i<=5;i++){const px_=i===0?0:i===5?W-6:i*96-3;R(g,px_,50,6,138,'#1f0d14');R(g,px_+1,50,1,138,'#3a1a26');}
 for(let i=1;i<5;i++){R(g,i*96-1,60,2,126,AREAS[i].neon);}
 R(g,0,48,W,10,'#231019');R(g,0,48,W,1,'#4a2432');R(g,0,57,W,1,'#14080e');
 AREAS.forEach((a,i)=>{const x0=i*96,cx=a.cx;
  R(g,x0+8,28,80,20,'#10060b');R(g,x0+8,28,80,1,'#3a1a26');R(g,x0+8,47,80,1,'#3a1a26');
  poster(g,i,cx);
  R(g,cx+12,112,34,3,'#6a4430');R(g,cx+12,111,34,1,'#8a5a3c');
  [['#2f8f4a',9],['#a8602a',11],['#2a6a9a',10],['#8a2a2a',11],['#d9a441',9]].forEach((b,k)=>{const bx=cx+14+k*5;R(g,bx+1,111-b[1],3,b[1]-3,b[0]);R(g,bx+1,111-b[1]-3,2,4,b[0]);R(g,bx+1,111-b[1]+1,1,b[1]-6,'#ffffff44'.slice(0,7)==='#ffffff'?b[0]:b[0]);});
  R(g,cx+40,102,8,9,'#b45309');R(g,cx+38,94,12,9,'#2fbf5b');R(g,cx+41,90,6,7,'#3adf70');
  R(g,cx,58,1,28,'#0c0508');R(g,cx-10,86,21,3,'#d9a441');R(g,cx-7,82,15,4,'#b88331');R(g,cx-4,80,9,2,'#8a6020');
  R(g,cx-11,132,22,34,'#3a2030');R(g,cx-10,133,20,3,'#5a3248');R(g,cx-10,136,1,30,'#2a1220');R(g,cx+9,136,1,30,'#4a2a3c');
 });
 const f=fg.getContext('2d');
 AREAS.forEach((a,i)=>{const cx=a.cx,hw=i===0?32:28;
  R(f,cx-hw,156,hw*2,3,'#b07a4a');R(f,cx-hw,156,hw*2,1,'#d49e66');
  R(f,cx-hw,159,hw*2,25,i===0?'#4a2a22':'#6a4430');R(f,cx-hw,159,hw*2,1,'#3a2018');R(f,cx-hw,159,1,25,'#7a5238');R(f,cx+hw-1,159,1,25,'#4a2e20');
  R(f,cx+6,163,hw-9,8,'#583626');R(f,cx+6,173,hw-9,8,'#583626');R(f,cx+hw-14,166,6,2,'#d9a441');R(f,cx+hw-14,176,6,2,'#d9a441');
  R(f,cx-hw,184,hw*2,2,'#14080e');
  if(i===0){R(f,cx-18,166,18,5,'#d9a441');R(f,cx-17,167,16,3,'#8a6a20');}
  R(f,cx-12,144,24,12,'#8f9aa8');R(f,cx-12,144,24,2,'#c6ced8');R(f,cx-12,154,24,2,'#6a7482');R(f,cx-2,148,4,4,'#e8eef4');
  R(f,cx+hw-14,148,6,8,'#e8e0d0');R(f,cx+hw-8,150,2,4,'#e8e0d0');R(f,cx+hw-14,148,6,2,'#6a3a1a');
  R(f,cx-hw+4,146,8,10,'#b45309');R(f,cx-hw+2,138,12,9,'#2fbf5b');R(f,cx-hw+5,134,6,6,'#3adf70');
 });
}
function drawLights(){
 const g=gl.getContext('2d');const rad=(x,y,r,c)=>{const q=g.createRadialGradient(x,y,0,x,y,r);q.addColorStop(0,c);q.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=q;g.fillRect(x-r,y-r,r*2,r*2);};
 AREAS.forEach(a=>{rad(a.cx,84,70,'rgba(255,170,70,.30)');rad(a.cx,36,60,rgba(a.neon,.22));
  const q=g.createLinearGradient(0,88,0,160);q.addColorStop(0,'rgba(255,190,100,.14)');q.addColorStop(1,'rgba(255,190,100,0)');g.fillStyle=q;g.beginPath();g.moveTo(a.cx-6,88);g.lineTo(a.cx+6,88);g.lineTo(a.cx+36,160);g.lineTo(a.cx-36,160);g.fill();});
 for(let i=1;i<5;i++){const q=g.createLinearGradient(i*96-16,0,i*96+16,0);const c=AREAS[i].neon;q.addColorStop(0,rgba(c,0));q.addColorStop(.5,rgba(c,.30));q.addColorStop(1,rgba(c,0));g.fillStyle=q;g.fillRect(i*96-16,60,32,126);}
 rad(COF.x,COF.y-24,34,'rgba(255,70,90,.16)');rad(352,214,50,'rgba(255,190,110,.22)');rad(140,236,60,'rgba(255,170,80,.10)');rad(340,236,60,'rgba(255,170,80,.10)');
 const v=vg.getContext('2d'),q=v.createRadialGradient(240,140,70,240,140,320);q.addColorStop(0,'rgba(10,0,14,0)');q.addColorStop(1,'rgba(10,0,14,.64)');v.fillStyle=q;v.fillRect(0,0,W,H);}
function rgba(h,a){const c=hx(h);return 'rgba('+c[0]+','+c[1]+','+c[2]+','+a+')';}

/* ============ actores y guiones ============ */
let T=0,DT=0;
const actors=AREAS.map((a,i)=>({i,home:a,look:a,x:a.cx,y:ENT,dir:0,pose:'sitwork',phase:0,say:'',kind:'',free:false,hold:false,atDesk:true,meet:null,gen:null}));
const PAPER={at:null},HAND={arrived:false,given:false},ST={phase:'idle',t:0,pending:-1};
function* go(a,pts,sp){sp=sp||SP;for(const p of pts){for(;;){const dx=p[0]-a.x,dy=p[1]-a.y,d=Math.hypot(dx,dy),st=sp*DT;
 if(d<=st){a.x=p[0];a.y=p[1];break;}a.x+=dx/d*st;a.y+=dy/d*st;a.phase+=st/STRIDE*TAU;if(Math.abs(dx)>.4)a.dir=Math.sign(dx);a.pose='walk';yield;}}a.pose='stand';}
function* wait(a,ms,pose){if(pose)a.pose=pose;let t=0;while(t<ms){t+=DT*1000;yield;}}
function* leaveDesk(a){const c=a.home.cx;a.dir=0;yield* wait(a,300,'stand');a.atDesk=false;yield* go(a,[[c+37,ENT],[c+37,HY]]);}
function* enterDesk(a){const c=a.home.cx;
 if(a.y<=ENT+1&&Math.abs(a.x-(c+37))<3)yield* go(a,[[c,ENT]]);else yield* go(a,[[a.x,HY],[c+37,HY],[c+37,ENT],[c,ENT]]);
 a.dir=0;yield* wait(a,250,'stand');a.pose='sitwork';a.atDesk=true;}
function* toDesk(a){if(!a.atDesk)yield* enterDesk(a);a.pose='sitwork';}
function takeover(a,g){if(a.meet){a.meet.cancel=true;a.meet.done=true;a.meet=null;}a.free=false;a.hold=false;a.say='';a.kind='';a.gen=g;}
/* conductas libres */
function* coffee(a){yield* leaveDesk(a);yield* go(a,[[COF.x-30,HY]]);a.dir=1;a.say=pick(['Un cafecito','Necesito cafe']);yield* wait(a,1000,'stand');a.say='';
 yield* wait(a,4600,'coffee');a.say=pick(['Ahhh, que rico','Ya revivi']);yield* wait(a,1300,'stand');a.say='';yield* enterDesk(a);}
function* stroll(a){yield* leaveDesk(a);const n=2+Math.floor(Math.random()*2);for(let k=0;k<n;k++){yield* go(a,[[rnd(30,450),rnd(214,258)]]);yield* wait(a,rnd(700,1800),'stand');}yield* enterDesk(a);}
function* readBench(a){yield* leaveDesk(a);yield* go(a,[[BEN.x,BEN.y]]);a.dir=1;yield* wait(a,rnd(6000,9000),'benchread');yield* wait(a,500,'stand');yield* enterDesk(a);}
function* nap(a){yield* wait(a,rnd(6000,9000),'sleep');a.dir=0;a.say='Uf, me dormi...';yield* wait(a,1500,'sitwork');a.say='';}
const DIAL=[["Revisaste el balance?","Si, todo cuadra... casi","Casi?","Faltan 90 mil, ja"],["Almorzamos?","Donde?","Donde sea, hambre!","Dale, vamos"],["Que calor hoy!","Si, ni se respira","Y el ventilador?","Esta de adorno"],["Viste las ventas?","Subieron un 12%","Excelente!","Eso espero..."],["El jefe anda serio","Sera el cierre","Mejor trabajemos","Si, si"]];
function* chat(a){const c=actors.filter(b=>b!==a&&b.free);if(!c.length){yield* wait(a,1500);return;}
 const b=pick(c);b.free=false;const m={bx:false,done:false,cancel:false};a.meet=m;b.meet=m;const mxp=clamp((a.home.cx+b.home.cx)/2+rnd(-20,20),70,410);
 b.gen=(function*(){yield* leaveDesk(b);yield* go(b,[[mxp+16,HY]]);b.dir=-1;m.bx=true;while(!m.done)yield;b.meet=null;yield* enterDesk(b);})();
 yield* leaveDesk(a);yield* go(a,[[mxp-16,HY]]);a.dir=1;while(!m.bx&&!m.cancel)yield;
 const Ln=pick(DIAL);for(let i=0;i<Ln.length&&!m.cancel;i++){const sp=i%2?b:a,ls=i%2?a:b;sp.say=Ln[i];sp.pose='talk';ls.pose='stand';ls.say='';yield* wait(a,1900);}
 a.say='';b.say='';m.done=true;a.meet=null;yield* enterDesk(a);}
function* idle(a,first){a.free=true;yield* wait(a,first||rnd(2500,7000));
 for(;;){a.free=true;yield* wait(a,rnd(2500,7000));a.free=false;const r=Math.random();
  if(r<.2)yield* nap(a);else if(r<.42)yield* coffee(a);else if(r<.6)yield* stroll(a);else if(r<.76)yield* readBench(a);else yield* chat(a);}}
/* historia */
function* sGerente(a){yield* toDesk(a);PAPER.at=0;a.say='Revisando documento...';for(;;)yield* wait(a,500,'sitread');}
function* sAreaM(a,k){const w=actors[k];yield* toDesk(a);PAPER.at=0;a.say='Documento recibido';yield* wait(a,1100,'sitread');
 a.say='Esto es para '+AREAS[k].name;yield* wait(a,900,'sitread');a.say='';PAPER.at=null;a.hold=true;
 yield* leaveDesk(a);yield* go(a,[[w.home.cx+37,HY],[w.home.cx+37,ENT]]);a.dir=-1;
 while(!w.atDesk)yield* wait(a,100,'stand');
 HAND.arrived=true;a.say='Para ti';yield* wait(a,700,'hand');while(!HAND.given)yield;a.hold=false;PAPER.at=k;
 yield* wait(a,500,'stand');a.say='';yield* enterDesk(a);}
function* sAreaW(a){yield* toDesk(a);ST.phase='yendo';while(!HAND.arrived)yield* wait(a,100,'sitwork');
 yield* wait(a,900,'receive');HAND.given=true;a.say='Recibido';yield* wait(a,900,'sitwork');a.say='@work';ST.phase='trabajando';ST.t=T;for(;;)yield* wait(a,500,'sitwork');}
function* sListoW(a,k){const m=actors[0];yield* toDesk(a);PAPER.at=k;yield* wait(a,500,'sitwork');a.say='Listo!';a.kind='ok';yield* wait(a,1400,'sitwork');PAPER.at=null;a.hold=true;a.say='';a.kind='';
 yield* leaveDesk(a);yield* go(a,[[m.home.cx+37,HY],[m.home.cx+37,ENT]]);a.dir=-1;while(!m.atDesk)yield* wait(a,100,'stand');
 HAND.arrived=true;a.say='Aqui esta el informe';yield* wait(a,1500,'hand');HAND.given=true;a.hold=false;PAPER.at=0;a.say='';ST.phase='idle';
 yield* wait(a,500,'stand');yield* enterDesk(a);}
function* sListoM(a){yield* toDesk(a);while(!HAND.arrived)yield* wait(a,100,'sitwork');yield* wait(a,1100,'receive');
 while(!HAND.given)yield;a.say='Excelente trabajo!';a.kind='ok';yield* wait(a,1800,'sitread');a.say='Trabajo terminado';yield* wait(a,2200,'sitread');a.say='';a.kind='';PAPER.at=null;}
const NOMBRES={espera:'ESPERANDO DOCUMENTO',gerente:'GERENTE REVISANDO',listo:'MISION COMPLETA!'};
const hb=document.getElementById('hb'),ht=document.getElementById('ht'),neons=document.getElementById('neons'),bubs=document.getElementById('bubs'),stage=document.getElementById('stage');
for(let i=0;i<10;i++)hb.appendChild(document.createElement('span'));
function hud(estado,k){const n={espera:0,gerente:3,area:7,listo:10}[estado]||0;ht.textContent=estado==='area'?AREAS[k].name+' TRABAJANDO':NOMBRES[estado]||'';
 [...hb.children].forEach((s,i)=>{s.className=i<n?((i===n-1&&estado!=='listo')?'f p':'f'):'';});
 nEls.forEach((e,i)=>e.classList.toggle('on',(estado==='gerente'&&i===0)||((estado==='area'||estado==='listo')&&i===k)));}
function cmd(estado,area){const k=AREAS.findIndex(x=>x.id===area);hud(estado,k);
 if(estado==='gerente'){ST.phase='gerente';ST.pending=-1;takeover(actors[0],sGerente(actors[0]));}
 else if(estado==='area'&&k>0){HAND.arrived=false;HAND.given=false;ST.pending=-1;ST.phase='yendo';takeover(actors[0],sAreaM(actors[0],k));takeover(actors[k],sAreaW(actors[k]));}
 else if(estado==='listo'&&k>0){if(ST.phase==='yendo'||ST.phase==='gerente'&&false){ST.pending=k;}else startListo(k);}
 else if(estado==='espera'){ST.pending=-1;}}
function startListo(k){HAND.arrived=false;HAND.given=false;takeover(actors[k],sListoW(actors[k],k));takeover(actors[0],sListoM(actors[0]));}
window.addEventListener('message',e=>{const m=e.data;if(m&&m.oficina)cmd(m.estado,m.area);});
actors.forEach(a=>{a.gen=idle(a,rnd(1200,4500));});

/* ============ DOM: neones y burbujas ============ */
const nEls=AREAS.map((a,i)=>{const e=document.createElement('div');e.className='neon';e.textContent=a.name;e.style.cssText='left:'+((i*96+8)/W*100)+'%;top:'+(28/H*100)+'%;width:'+(80/W*100)+'%;height:'+(20/H*100)+'%;color:'+a.neon;neons.appendChild(e);return e;});
const bEls=actors.map(()=>{const e=document.createElement('div');e.className='bub';bubs.appendChild(e);return e;});
function layout(){stage.style.setProperty('--s',cv.clientWidth/W);}window.addEventListener('resize',layout);layout();
function bubbles(){actors.forEach((a,i)=>{const e=bEls[i];let t=a.say;if(t==='@work')t='Calculando'+'.'.repeat(1+Math.floor(T*2)%3);
 if(a.pose==='sleep'&&!t)t=['z','zz','zzz'][Math.floor(T*1.5)%3];if(!t){e.style.display='none';return;}
 e.style.display='block';e.textContent=t;e.className='bub'+(a.kind==='ok'?' ok':'');
 const seat=a.pose==='sitwork'||a.pose==='sitread'||a.pose==='receive'||a.pose==='sleep';
 e.style.left=clamp(a.x/W*100,12,88)+'%';e.style.top=((a.y-(seat?62:76))/H*100)+'%';});}

/* ============ dibujo ============ */
const props=[
 {y:COF.y,draw(){const x=COF.x,y=COF.y;R(ctx,x-13,y-50,26,5,'#5a1a28');R(ctx,x-12,y-46,24,46,'#8a2a3a');R(ctx,x-12,y-46,3,46,'#a8404f');R(ctx,x+9,y-46,3,46,'#5a1a28');R(ctx,x-8,y-40,16,10,'#0c0a0e');R(ctx,x-6,y-38,Math.floor(T*2)%2?11:7,2,'#4dffa0');R(ctx,x-6,y-34,5,1,'#4dffa0');R(ctx,x-3,y-26,6,4,'#2a2a2a');R(ctx,x-3,y-20,6,8,'#f4ecdc');R(ctx,x-10,y-9,20,3,'#2a2a2a');R(ctx,x-9,y-6,3,6,'#3a1018');R(ctx,x+6,y-6,3,6,'#3a1018');}},
 {y:BEN.y-2,draw(){const x=BEN.x,y=BEN.y-2;R(ctx,x-26,y-40,52,4,'#5a3828');R(ctx,x-24,y-36,3,18,'#4a2e20');R(ctx,x+21,y-36,3,18,'#4a2e20');R(ctx,x-26,y-19,52,6,'#7a5038');R(ctx,x-26,y-19,52,1,'#9a6a48');R(ctx,x-24,y-13,4,13,'#3a2418');R(ctx,x+20,y-13,4,13,'#3a2418');}},
 {y:244,draw(){const x=26,y=244;R(ctx,x-1,y-70,3,70,'#3a2418');R(ctx,x-9,y-70,19,3,'#4a2e20');R(ctx,x-7,y-5,15,5,'#2a1810');[[-8,-64],[8,-64],[-5,-58],[6,-58]].forEach(h=>R(ctx,x+h[0],y+h[1],3,3,'#b88331'));R(ctx,x+2,y-62,13,34,'#1c1a26');R(ctx,x+3,y-62,3,34,'#2c2a3a');R(ctx,x+3,y-62,13,3,'#14121c');}},
 {y:250,draw(){const x=352,y=250;R(ctx,x-1,y-60,3,60,'#3a2418');R(ctx,x-9,y-3,19,3,'#2a1810');R(ctx,x-11,y-72,23,13,'#e8b860');R(ctx,x-11,y-72,23,2,'#fff0c0');R(ctx,x-9,y-60,19,2,'#9a7020');}},
 {y:262,draw(){const x=464,y=262;R(ctx,x-7,y-12,15,12,'#7a3a1a');R(ctx,x-12,y-34,25,22,'#1f8f4a');R(ctx,x-8,y-42,17,10,'#2fbf5b');R(ctx,x-2,y-22,4,10,'#16753a');R(ctx,x-14,y-26,6,8,'#2fbf5b');}}];
function fan(){const cx=240,cy=13,a=T*4;R(ctx,cx,0,2,6,'#241018');R(ctx,cx-4,6,9,4,'#5a2a38');
 for(let k=0;k<4;k++){const an=a+k*Math.PI/2,ex=cx+Math.cos(an)*46,ey=cy+Math.sin(an)*7,n=22;for(let s=2;s<=n;s++){const f=s/n,xx=cx+(ex-cx)*f,yy=cy+(ey-cy)*f,fr=Math.sin(an)>0;R(ctx,xx,yy,3,fr?3:2,fr?'#8a4252':'#4a2230');}}}
function drawActor(a,pass){const p=a.pose,sit=p==='sitwork'||p==='sitread'||p==='receive'||p==='sleep';if((p==='sleep')!==(pass==='front'))return;
 px.fill(0);if(sit)buildFront(a);else buildSide(a);tctx.putImageData(img,0,0);
 const X=Math.round(a.x),Y=Math.round(a.y);if(!sit){R(ctx,X-9,Y-1,18,2,'rgba(0,0,0,.34)');R(ctx,X-6,Y+1,12,1,'rgba(0,0,0,.25)');}
 ctx.drawImage(tmp,X-OX,Y-OY);
 if(p==='sitwork'){ctx.globalAlpha=.16+.05*Math.sin(T*9);R(ctx,X-7,Y-53,14,9,'#7fd0ff');ctx.globalAlpha=1;}}
let last=performance.now();
function frame(now){DT=Math.min(.05,(now-last)/1000);last=now;T+=DT;
 actors.forEach(a=>{const r=a.gen.next();if(r.done)a.gen=idle(a,rnd(2500,5000));});
 if(ST.pending>=0&&ST.phase==='trabajando'&&T-ST.t>1.2){const k=ST.pending;ST.pending=-1;startListo(k);}
 ctx.drawImage(bg,0,0);fan();
 actors.filter(a=>a.y<=ENT+3&&a.pose!=='sleep').sort((p,q)=>p.y-q.y).forEach(a=>drawActor(a,'back'));
 ctx.drawImage(fg,0,0);
 actors.filter(a=>a.pose==='sleep').forEach(a=>drawActor(a,'front'));
 if(PAPER.at!==null){const h=AREAS[PAPER.at];R(ctx,h.cx-24,152,12,5,'#f6f2e8');R(ctx,h.cx-22,153,8,1,'#a0a8b4');}
 [...props.map(p=>({y:p.y,f:()=>p.draw()})),...actors.filter(a=>a.y>ENT+3).map(a=>({y:a.y,f:()=>drawActor(a,'back')}))].sort((p,q)=>p.y-q.y).forEach(o=>o.f());
 ctx.globalCompositeOperation='lighter';ctx.globalAlpha=.8+.2*Math.sin(T*3.1)*Math.sin(T*1.7);ctx.drawImage(gl,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
 ctx.drawImage(vg,0,0);bubbles();requestAnimationFrame(frame);}
drawBG();drawLights();requestAnimationFrame(frame);
})();
</script></body></html>"""


def html_escena() -> str:
    return ESCENA.replace("__VEL__", str(VELOCIDAD))
