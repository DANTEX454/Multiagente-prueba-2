"""Oficina virtual pixel-art (ambiente de club oscuro con neones).
La escena es UN solo iframe que se mantiene vivo; Python le manda órdenes (gerente / area / listo)
por mensajes, así las animaciones no se cortan ni se reinician al cargar documentos."""
import json
import time

CX = {"gerente": 48, "contabilidad": 144, "proyectos": 240, "diagnostico": 336, "proyecciones": 432}
VELOCIDAD = 96   # px lógicos/segundo (mismo valor que en el JavaScript)


def duracion_area(area: str) -> float:
    """Segundos aproximados que tarda el gerente en levantarse, caminar y entregar el documento."""
    dist = 28 + abs(CX[area] - CX["gerente"]) + 28
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
 font-size:calc(var(--s)*4.6px);white-space:nowrap;color:#f2c36a;background:#3a2418;border:calc(var(--s)*1px) solid #a0622e;box-sizing:border-box;
 box-shadow:0 calc(var(--s)*1px) 0 rgba(0,0,0,.4);pointer-events:none;opacity:.92}
.neon.on{color:#fff6cc;border-color:#ffd37a;opacity:1;text-shadow:0 0 calc(var(--s)*3px) #ffd37a;box-shadow:0 0 calc(var(--s)*5px) rgba(255,200,110,.7)}
#sub{position:absolute;left:5%;right:5%;top:calc(238/270*100%);height:calc(30/270*100%);display:flex;align-items:center;justify-content:center;
 text-align:center;font-family:'Press Start 2P',monospace;font-size:calc(var(--s)*5px);line-height:1.5;color:#f2b53c;
 text-shadow:calc(var(--s)*.8px) calc(var(--s)*.8px) 0 #2a1208;pointer-events:none}
#sub.ok{color:#b8f5c8}#sub .n{color:#ffe9a8;margin-right:calc(var(--s)*3px)}
#hud{display:flex;justify-content:space-between;align-items:center;background:#0b0508;border-top:2px solid #a0622e;padding:8px 12px;
 font-family:'Press Start 2P',monospace;font-size:11px;color:#f6e8d8}
#hb span{display:inline-block;width:11px;height:11px;margin-left:4px;background:#2a1a22}
#hb span.f{background:#38d66b}#hb span.p{animation:pp .5s steps(1) infinite}@keyframes pp{50%{opacity:.2}}
</style></head><body>
<div id="wrap"><div id="stage"><canvas id="c" width="480" height="270"></canvas><div id="neons"></div><div id="sub"></div></div>
<div id="hud"><span id="ht">ESPERANDO DOCUMENTO</span><span id="hb"></span></div></div>
<script>
(()=>{
const W=480,H=270,ENT=188,HY=216,SP=__VEL__,STRIDE=46,TAU=6.2832;
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
const COF={x:395,y:206},SOFA={x:250,y:224,a:232,b:268};

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
 let thA=0,thB=0,kA=.06,kB=.06,seated=p==='benchread'||p==='benchsit'||p==='benchtalk';
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
  else if((p==='talk'||p==='benchtalk')&&!far){const up=Math.max(0,Math.sin(t*3)),r=ik(sx,sy,sx+d*(11+3*Math.sin(t*5)),sy+7-8*up,11,11,d>0?1:-1);ex=r[0];ey=r[1];hx_=r[2];hy_=r[3];}
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
 const open=((p==='talk'||p==='benchtalk')&&Math.floor(t*6)%2);pr(d>0?hxp+4:hxp-6,hy+4,2,open?2:1,K.mouth);
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

/* ============ fondo (sala cálida con ventana de ladrillo) ============ */
function poster(g,i,cx){const x=cx-42,y=116;R(g,x,y,28,34,'#3a2418');R(g,x+2,y+2,24,30,'#f0e6d0');
 if(i===1){R(g,x+3,y+3,22,28,'#f4f0e0');for(let r=0;r<6;r++){R(g,x+5,y+6+r*4,18,1,'#8a8a8a');R(g,x+17,y+5+r*4,6,2,'#3f6fd0');}}
 if(i===2){R(g,x+3,y+3,22,28,'#2a5fa8');[[5,7,10],[9,12,12],[13,17,9],[5,22,15]].forEach(q=>R(g,x+q[0],y+q[1],q[2],3,'#e0f0ff'));}
 if(i===3){R(g,x+3,y+3,22,28,'#16242a');[[4,17],[6,17],[8,17],[10,10],[12,24],[14,17],[16,17],[18,13],[20,20]].forEach(q=>R(g,x+q[0],y+q[1],2,3,'#4dffa0'));}
 if(i===4){R(g,x+3,y+3,22,28,'#1f3050');for(let k=0;k<17;k++)R(g,x+5+k,y+26-Math.round(k*1.1)-(k%3===0?1:0),2,2,'#ffb0e0');}
 if(i===0){R(g,x+3,y+3,22,28,'#ecdca0');R(g,x+6,y+8,16,2,'#9a8a50');R(g,x+6,y+13,16,2,'#9a8a50');R(g,x+10,y+20,8,8,'#c0304c');}}
function drawBG(){
 const g=bg.getContext('2d'),E=ENT;
 // pared lila
 R(g,0,0,W,192,'#6f5fae');R(g,0,0,W,40,'#675aa6');R(g,0,120,W,72,'#7767b6');
 for(let y=22;y<104;y+=12)for(let x=((y/12)%2)*8;x<W;x+=16){R(g,x+6,y,2,2,'#7a6ab8');R(g,x+4,y+2,6,2,'#7a6ab8');R(g,x+6,y+4,2,2,'#7a6ab8');}
 R(g,0,0,W,14,'#4a3d7a');R(g,0,14,W,3,'#a0622e');R(g,0,17,W,1,'#d28a4a');
 // ventana grande con vista a un edificio de ladrillo
 R(g,98,22,284,84,'#2a2540');R(g,102,26,276,74,'#9c4a36');
 for(let y=26,k=0;y<100;y+=5,k++){R(g,102,y+4,276,1,'#6e3024');for(let x=102+(k%2)*7;x<378;x+=14)R(g,x,y,1,5,'#6e3024');}
 [[130,34],[188,56],[246,32],[306,54],[346,34]].forEach(w=>{R(g,w[0],w[1],18,24,'#c9d3e6');R(g,w[0]+2,w[1]+2,6,9,'#eaf2fc');R(g,w[0]+10,w[1]+2,6,9,'#eaf2fc');R(g,w[0]+2,w[1]+13,6,9,'#dfe9f8');R(g,w[0]+10,w[1]+13,6,9,'#dfe9f8');});
 for(let k=1;k<6;k++)R(g,102+k*46-1,26,3,74,'#262034');R(g,102,50,276,3,'#262034');R(g,102,76,276,3,'#262034');
 R(g,94,102,292,5,'#a0622e');R(g,94,102,292,1,'#d28a4a');
 // cortinas
 [[70,0],[380,1]].forEach(c=>{const x=c[0];R(g,x,20,30,86,'#8f5f74');for(let k=0;k<6;k++){R(g,x+k*5,20,2,86,'#ab7a90');R(g,x+k*5+2,20,1,86,'#6e4458');}R(g,x,72,30,4,'#e0b24a');R(g,x,106,30,2,'#6e4458');});
 R(g,64,17,352,4,'#3a2a20');R(g,60,16,6,6,'#d9a441');R(g,414,16,6,6,'#d9a441');
 // cuadros laterales
 R(g,12,38,34,42,'#a0622e');R(g,15,41,28,36,'#bcd2a0');R(g,15,60,28,17,'#7fa86a');R(g,22,48,8,8,'#f4e8b0');
 R(g,436,38,34,42,'#a0622e');R(g,439,41,28,36,'#e0b8a8');R(g,444,50,18,18,'#c86a6a');R(g,448,54,10,10,'#f4d8b0');
 R(g,26,88,6,10,'#d9a441');R(g,450,88,6,10,'#d9a441');
 // zócalo y piso de madera
 R(g,0,186,W,4,'#7a4a28');R(g,0,186,W,1,'#b07840');
 R(g,0,190,W,44,'#b0703c');
 const ys=[190,196,203,212,222,234];
 for(let k=0;k<ys.length-1;k++){R(g,0,ys[k],W,1,'#8a5428');R(g,0,ys[k]+1,W,1,'#c88850');
  for(let x=(k*53)%71;x<W;x+=58+Math.floor(rr()*24))R(g,x,ys[k],1,ys[k+1]-ys[k],'#8a5428');}
 R(g,150,200,200,32,'#b05a3a');R(g,153,203,194,26,'#c87a4e');R(g,150,200,200,2,'#d9a070');R(g,150,230,200,2,'#8a3a28');
 for(let x=156;x<344;x+=12){R(g,x,206,6,14,'#b05a3a');R(g,x+2,209,2,8,'#e8b080');}
 // franja de ladrillo con el subtítulo
 R(g,0,234,W,36,'#6a2a28');R(g,0,234,W,3,'#2a1a14');R(g,0,237,W,1,'#9a4a3a');
 for(let y=238,k=0;y<270;y+=6,k++){R(g,0,y+5,W,1,'#4a1a1c');for(let x=(k%2)*12;x<W;x+=24)R(g,x,y,1,6,'#4a1a1c');}
 // cubículos bajos
 R(g,0,104,W,5,'#a0622e');R(g,0,104,W,1,'#d28a4a');R(g,0,109,W,2,'#4a2a18');
 AREAS.forEach((a,i)=>{const x0=i*96,cx=a.cx;
  R(g,x0+3,111,90,76,'#5e4d94');g.globalAlpha=.28;R(g,x0+3,111,90,76,a.tint);g.globalAlpha=1;
  R(g,x0+3,160,90,27,'#7a5234');for(let x=x0+4;x<x0+93;x+=6)R(g,x,160,1,27,'#5a3a22');
  poster(g,i,cx);
  R(g,cx+12,140,34,3,'#a0622e');R(g,cx+12,139,34,1,'#d28a4a');
  [['#2f8f4a',9],['#c0702a',11],['#2a6a9a',10],['#a02a2a',11],['#e0b441',9]].forEach((b,k)=>{const bx=cx+14+k*5;R(g,bx+1,139-b[1],3,b[1]-3,b[0]);R(g,bx+1,139-b[1]-3,2,4,b[0]);});
  R(g,cx+40,130,8,9,'#c0602a');R(g,cx+38,122,12,9,'#2fbf5b');R(g,cx+41,118,6,7,'#4aef80');
  R(g,cx,111,1,3,'#0c0508');R(g,cx-8,114,17,3,'#f0b040');R(g,cx-5,112,11,2,'#d0902a');
  R(g,cx-11,E-56,22,34,'#6a2a3a');R(g,cx-10,E-55,20,3,'#8a4458');R(g,cx-10,E-52,1,30,'#4a1a28');R(g,cx+9,E-52,1,30,'#8a4458');
 });
 for(let i=0;i<=5;i++){const px_=i===0?0:i===5?W-5:i*96-2;R(g,px_,104,5,84,'#6a3e22');R(g,px_+1,104,1,84,'#b07840');}
 // escritorios (frente)
 const f=fg.getContext('2d'),D=E-28;
 AREAS.forEach((a,i)=>{const cx=a.cx,hw=i===0?32:28;
  R(f,cx-hw,D,hw*2,3,'#d49860');R(f,cx-hw,D,hw*2,1,'#f0c088');
  R(f,cx-hw,D+3,hw*2,25,i===0?'#7a4a2a':'#a0622e');R(f,cx-hw,D+3,hw*2,1,'#6a3a1e');R(f,cx-hw,D+3,1,25,'#c88850');R(f,cx+hw-1,D+3,1,25,'#6a3a1e');
  R(f,cx+6,D+7,hw-9,8,'#8a5028');R(f,cx+6,D+17,hw-9,8,'#8a5028');R(f,cx+hw-14,D+10,6,2,'#f0c860');R(f,cx+hw-14,D+20,6,2,'#f0c860');
  R(f,cx-hw,E-2,hw*2,2,'#5a3418');
  if(i===0){R(f,cx-18,D+10,18,5,'#f0c860');R(f,cx-17,D+11,16,3,'#9a7a20');}
  R(f,cx-12,D-12,24,12,'#a8b2c0');R(f,cx-12,D-12,24,2,'#d8e0ea');R(f,cx-12,D-2,24,2,'#7a8492');R(f,cx-2,D-8,4,4,'#f0f4f8');
  R(f,cx+hw-14,D-8,6,8,'#f4ecdc');R(f,cx+hw-8,D-6,2,4,'#f4ecdc');R(f,cx+hw-14,D-8,6,2,'#7a4a1e');
  R(f,cx-hw+4,D-10,8,10,'#c0602a');R(f,cx-hw+2,D-18,12,9,'#2fbf5b');R(f,cx-hw+5,D-22,6,6,'#4aef80');
 });
}
function drawLights(){
 const g=gl.getContext('2d');const rad=(x,y,r,c)=>{const q=g.createRadialGradient(x,y,0,x,y,r);q.addColorStop(0,c);q.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=q;g.fillRect(x-r,y-r,r*2,r*2);};
 AREAS.forEach(a=>{rad(a.cx,118,54,'rgba(255,196,96,.26)');
  const q=g.createLinearGradient(0,116,0,164);q.addColorStop(0,'rgba(255,200,110,.18)');q.addColorStop(1,'rgba(255,200,110,0)');g.fillStyle=q;g.beginPath();g.moveTo(a.cx-7,116);g.lineTo(a.cx+7,116);g.lineTo(a.cx+36,164);g.lineTo(a.cx-36,164);g.fill();});
 const w=g.createLinearGradient(0,106,0,232);w.addColorStop(0,'rgba(190,215,255,.22)');w.addColorStop(1,'rgba(190,215,255,0)');g.fillStyle=w;g.beginPath();g.moveTo(112,106);g.lineTo(368,106);g.lineTo(430,232);g.lineTo(60,232);g.fill();
 rad(192,150,66,'rgba(255,170,70,.26)');rad(COF.x,COF.y-24,26,'rgba(255,120,80,.14)');
 const v=vg.getContext('2d'),q=v.createRadialGradient(240,130,120,240,130,330);q.addColorStop(0,'rgba(30,10,40,0)');q.addColorStop(1,'rgba(30,10,40,.40)');v.fillStyle=q;v.fillRect(0,0,W,H);}
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
function* stroll(a){yield* leaveDesk(a);const n=2+Math.floor(Math.random()*2);for(let k=0;k<n;k++){yield* go(a,[[rnd(30,450),rnd(204,228)]]);yield* wait(a,rnd(700,1800),'stand');}yield* enterDesk(a);}
function* readBench(a){yield* leaveDesk(a);yield* go(a,[[pick([SOFA.a,SOFA.b]),SOFA.y]]);a.dir=1;yield* wait(a,rnd(6000,9000),'benchread');yield* wait(a,500,'stand');yield* enterDesk(a);}
function* nap(a){yield* wait(a,rnd(6000,9000),'sleep');a.dir=0;a.say='Uf, me dormi...';yield* wait(a,1500,'sitwork');a.say='';}
const DIAL=[["Revisaste el balance?","Si, todo cuadra... casi","Casi?","Faltan 90 mil, ja"],["Almorzamos?","Donde?","Donde sea, hambre!","Dale, vamos"],["Que calor hoy!","Si, ni se respira","Y el ventilador?","Esta de adorno"],["Viste las ventas?","Subieron un 12%","Excelente!","Eso espero..."],["El jefe anda serio","Sera el cierre","Mejor trabajemos","Si, si"]];
function* chat(a){const c=actors.filter(b=>b!==a&&b.free);if(!c.length){yield* wait(a,1500);return;}
 const b=pick(c);b.free=false;const m={bx:false,done:false,cancel:false};a.meet=m;b.meet=m;const mxp=clamp((a.home.cx+b.home.cx)/2+rnd(-20,20),70,410);
 b.gen=(function*(){yield* leaveDesk(b);yield* go(b,[[mxp+16,HY]]);b.dir=-1;m.bx=true;while(!m.done)yield;b.meet=null;yield* enterDesk(b);})();
 yield* leaveDesk(a);yield* go(a,[[mxp-16,HY]]);a.dir=1;while(!m.bx&&!m.cancel)yield;
 const Ln=pick(DIAL);for(let i=0;i<Ln.length&&!m.cancel;i++){const sp=i%2?b:a,ls=i%2?a:b;sp.say=Ln[i];sp.pose='talk';ls.pose='stand';ls.say='';yield* wait(a,1900);}
 a.say='';b.say='';m.done=true;a.meet=null;yield* enterDesk(a);}
function* sofaChat(a){const c=actors.filter(b=>b!==a&&b.free);if(!c.length){yield* readBench(a);return;}
 const b=pick(c);b.free=false;const m={bx:false,done:false,cancel:false};a.meet=m;b.meet=m;
 b.gen=(function*(){yield* leaveDesk(b);yield* go(b,[[SOFA.b,SOFA.y]]);b.dir=-1;b.pose='benchsit';m.bx=true;while(!m.done)yield;b.meet=null;yield* wait(b,300,'stand');yield* enterDesk(b);})();
 yield* leaveDesk(a);yield* go(a,[[SOFA.a,SOFA.y]]);a.dir=1;a.pose='benchsit';while(!m.bx&&!m.cancel)yield;
 const Ln=pick(DIAL);for(let i=0;i<Ln.length&&!m.cancel;i++){const sp=i%2?b:a,ls=i%2?a:b;sp.say=Ln[i];sp.pose='benchtalk';ls.pose='benchsit';ls.say='';yield* wait(a,2000);}
 a.say='';b.say='';m.done=true;a.meet=null;yield* wait(a,300,'stand');yield* enterDesk(a);}
function* idle(a,first){a.free=true;yield* wait(a,first||rnd(2500,7000));
 for(;;){a.free=true;yield* wait(a,rnd(2500,7000));a.free=false;const r=Math.random();
  if(r<.16)yield* nap(a);else if(r<.34)yield* coffee(a);else if(r<.48)yield* stroll(a);else if(r<.60)yield* readBench(a);else if(r<.82)yield* sofaChat(a);else yield* chat(a);}}
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
const nEls=AREAS.map((a,i)=>{const e=document.createElement('div');e.className='neon';e.textContent=a.name;e.style.cssText='left:'+((i*96+10)/W*100)+'%;top:'+(91/H*100)+'%;width:'+(76/W*100)+'%;height:'+(13/H*100)+'%';neons.appendChild(e);return e;});
const sub=document.getElementById('sub');let subKey='';
function layout(){stage.style.setProperty('--s',cv.clientWidth/W);}window.addEventListener('resize',layout);layout();
function subtitle(){let best=null;actors.forEach(a=>{if(a.say!==a._l){a._l=a.say;a._ts=T;}if(a.say&&(!best||a._ts>best._ts))best=a;});
 let key='',txt='',nom='',ok=false;
 if(best){txt=best.say==='@work'?'Calculando'+'.'.repeat(1+Math.floor(T*2)%3):best.say;nom=best.home.name[0]+best.home.name.slice(1).toLowerCase();ok=best.kind==='ok';key=nom+txt+ok;}
 if(key===subKey)return;subKey=key;sub.className=ok?'ok':'';sub.textContent='';
 if(best){const n=document.createElement('span');n.className='n';n.textContent=nom+':';sub.appendChild(n);sub.appendChild(document.createTextNode(txt));}}

/* ============ dibujo ============ */
const props=[
 {y:COF.y,draw(){const x=COF.x,y=COF.y;R(ctx,x-9,y-38,18,4,'#6a2030');R(ctx,x-8,y-35,16,35,'#b03a4a');R(ctx,x-8,y-35,2,35,'#d05a68');R(ctx,x+6,y-35,2,35,'#7a2030');R(ctx,x-6,y-30,12,8,'#101418');R(ctx,x-4,y-28,Math.floor(T*2)%2?9:6,2,'#4dffa0');R(ctx,x-3,y-19,6,3,'#2a2a2a');R(ctx,x-3,y-15,6,6,'#f4ecdc');R(ctx,x-9,y-6,18,3,'#2a2a2a');R(ctx,x-8,y-3,3,3,'#5a1a28');R(ctx,x+5,y-3,3,3,'#5a1a28');}},
 {y:232,draw(){const x=15,y=232;R(ctx,x-13,y-32,26,3,'#a0622e');R(ctx,x-13,y-32,26,1,'#d28a4a');R(ctx,x-11,y-29,3,29,'#7a4a28');R(ctx,x+8,y-29,3,29,'#7a4a28');R(ctx,x-9,y-20,18,2,'#7a4a28');
  R(ctx,x-6,y-46,12,14,'#2a9a9a');R(ctx,x-6,y-46,3,14,'#4ac0c0');R(ctx,x-4,y-50,8,5,'#2a9a9a');
  [[-11,-62,9],[-3,-67,10],[3,-60,9],[-8,-55,8],[0,-56,8]].forEach(f=>{R(ctx,x+f[0],y+f[1],f[2],f[2],'#e8689a');R(ctx,x+f[0]+2,y+f[1]+2,f[2]-4,f[2]-4,'#f6a0c0');});R(ctx,x-1,y-52,2,6,'#2a7a3a');}},
 {y:216,draw(){const x=192,y=216;R(ctx,x-7,y-4,14,4,'#3a2418');R(ctx,x-1,y-62,3,58,'#3a2418');
  for(let r=0;r<16;r++)R(ctx,x-8-r/2,y-82+r,17+r,1,r<3?'#f4b860':'#d98a3a');R(ctx,x-9,y-67,26,2,'#a8601e');}},
 {y:222,draw(){const x=SOFA.x,y=SOFA.y-2;R(ctx,x-48,y-44,96,28,'#ddd0c2');R(ctx,x-48,y-44,96,3,'#f0e6da');R(ctx,x-48,y-17,96,2,'#b8a898');
  R(ctx,x-52,y-34,10,28,'#cbbcae');R(ctx,x-52,y-34,10,3,'#e6dacc');R(ctx,x+42,y-34,10,28,'#cbbcae');R(ctx,x+42,y-34,10,3,'#e6dacc');
  R(ctx,x-42,y-16,84,9,'#f2e8dc');R(ctx,x-42,y-16,84,1,'#ffffff');R(ctx,x-1,y-16,1,9,'#d8c8b8');R(ctx,x-50,y-7,100,6,'#c4b4a4');R(ctx,x-48,y-1,5,4,'#5a3a22');R(ctx,x+43,y-1,5,4,'#5a3a22');
  R(ctx,x+24,y-40,17,15,'#b02440');R(ctx,x+24,y-40,17,3,'#d04664');R(ctx,x+37,y-37,4,12,'#8a1a34');}},
 {y:234,draw(){const x=SOFA.x,y=234;R(ctx,x-34,y-17,68,5,'#a0622e');R(ctx,x-34,y-17,68,1,'#d49860');R(ctx,x-34,y-12,68,2,'#7a4a28');R(ctx,x-31,y-10,4,10,'#7a4a28');R(ctx,x+27,y-10,4,10,'#7a4a28');
  R(ctx,x-18,y-23,6,6,'#f4ecdc');R(ctx,x-16,y-22,2,1,'#7a4a1e');R(ctx,x+6,y-20,16,3,'#2a9a9a');R(ctx,x+8,y-22,12,2,'#f4f0e0');}},
 {y:234,draw(){const x=345,y=234;R(ctx,x-23,y-46,46,32,'#6a6a72');R(ctx,x-21,y-44,42,28,'#f6f6f2');R(ctx,x-21,y-30,42,1,'#c8c8c8');
  const cs=['#ff8a8a','#ffd24a','#7ad0ff','#9af09a','#c890ff','#ffb060'];for(let r=0;r<3;r++)for(let c=0;c<5;c++)R(ctx,x-19+c*8,y-43+r*9,6,6,cs[(r*5+c)%6]);
  R(ctx,x-21,y-14,42,2,'#6a6a72');R(ctx,x-18,y-12,3,12,'#4a4a52');R(ctx,x+15,y-12,3,12,'#4a4a52');}},
 {y:232,draw(){const x=440,y=232;R(ctx,x-20,y-20,40,20,'#a0622e');R(ctx,x-20,y-20,40,2,'#d49860');R(ctx,x-18,y-16,17,14,'#8a5028');R(ctx,x+1,y-16,17,14,'#8a5028');
  R(ctx,x-15,y-44,30,24,'#2a2a30');R(ctx,x-12,y-41,24,18,'#6f98ac');R(ctx,x-12,y-41,24,3,'#9cc0d0');for(let k=0;k<5;k++)R(ctx,x-12,y-39+k*4,24,1,'#5a8296');R(ctx,x+9,y-27,3,2,'#f0c060');
  R(ctx,x-8,y-52,1,8,'#8a8a90');R(ctx,x+8,y-52,1,8,'#8a8a90');R(ctx,x-9,y-53,3,1,'#8a8a90');R(ctx,x+7,y-53,3,1,'#8a8a90');}},
 {y:232,draw(){const x=466,y=232;R(ctx,x-8,y-13,16,13,'#c0602a');R(ctx,x-13,y-38,26,25,'#1f8f4a');R(ctx,x-9,y-48,18,12,'#2fbf5b');R(ctx,x-2,y-24,4,11,'#16753a');R(ctx,x-15,y-30,7,9,'#2fbf5b');R(ctx,x+9,y-34,7,9,'#2fbf5b');}}];
function fan(){const cx=240,cy=13,a=T*4;R(ctx,cx,0,2,6,'#241018');R(ctx,cx-4,6,9,4,'#5a2a38');
 for(let k=0;k<4;k++){const an=a+k*Math.PI/2,ex=cx+Math.cos(an)*46,ey=cy+Math.sin(an)*7,n=22;for(let s=2;s<=n;s++){const f=s/n,xx=cx+(ex-cx)*f,yy=cy+(ey-cy)*f,fr=Math.sin(an)>0;R(ctx,xx,yy,3,fr?3:2,fr?'#8a4252':'#4a2230');}}}
function drawActor(a,pass){const p=a.pose,sit=p==='sitwork'||p==='sitread'||p==='receive'||p==='sleep';if((p==='sleep')!==(pass==='front'))return;
 px.fill(0);if(sit)buildFront(a);else buildSide(a);tctx.putImageData(img,0,0);
 const X=Math.round(a.x),Y=Math.round(a.y);if(!sit){R(ctx,X-9,Y-1,18,2,'rgba(0,0,0,.34)');R(ctx,X-6,Y+1,12,1,'rgba(0,0,0,.25)');}
 ctx.drawImage(tmp,X-OX,Y-OY);
 if(p==='sleep'){for(let k=0;k<3;k++){const ph=(T*1.2+k*.33)%1;R(ctx,X+10+k*5+ph*4,Y-48-ph*22,4-k,1,'#fff6d0');R(ctx,X+12+k*5+ph*4,Y-47-ph*22,1,2,'#fff6d0');R(ctx,X+10+k*5+ph*4,Y-45-ph*22,4-k,1,'#fff6d0');}}
 if(p==='sitwork'){ctx.globalAlpha=.16+.05*Math.sin(T*9);R(ctx,X-7,Y-53,14,9,'#7fd0ff');ctx.globalAlpha=1;}}
let last=performance.now();
function frame(now){DT=Math.min(.05,(now-last)/1000);last=now;T+=DT;
 actors.forEach(a=>{const r=a.gen.next();if(r.done)a.gen=idle(a,rnd(2500,5000));});
 if(ST.pending>=0&&ST.phase==='trabajando'&&T-ST.t>1.2){const k=ST.pending;ST.pending=-1;startListo(k);}
 ctx.drawImage(bg,0,0);
 actors.filter(a=>a.y<=ENT+3&&a.pose!=='sleep').sort((p,q)=>p.y-q.y).forEach(a=>drawActor(a,'back'));
 ctx.drawImage(fg,0,0);
 actors.filter(a=>a.pose==='sleep').forEach(a=>drawActor(a,'front'));
 if(PAPER.at!==null){const h=AREAS[PAPER.at];R(ctx,h.cx-24,ENT-32,12,5,'#f6f2e8');R(ctx,h.cx-22,ENT-31,8,1,'#a0a8b4');}
 [...props.map(p=>({y:p.y,f:()=>p.draw()})),...actors.filter(a=>a.y>ENT+3).map(a=>({y:a.y,f:()=>drawActor(a,'back')}))].sort((p,q)=>p.y-q.y).forEach(o=>o.f());
 ctx.globalCompositeOperation='lighter';ctx.globalAlpha=.8+.2*Math.sin(T*3.1)*Math.sin(T*1.7);ctx.drawImage(gl,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
 ctx.drawImage(vg,0,0);subtitle();requestAnimationFrame(frame);}
drawBG();drawLights();requestAnimationFrame(frame);
})();
</script></body></html>"""


def html_escena() -> str:
    return ESCENA.replace("__VEL__", str(VELOCIDAD))
