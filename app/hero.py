"""The customer field: this shop's customers as a 3D cloud you can turn.

Not a backdrop with text over it. The field is the thing you look at, so it gets
the whole panel: height is uplift, so the few customers worth messaging stand
above everyone else, and the darts flying out of the corner go to exactly those
people. The pitch and the product end up being the same picture.

Used by the sign-in gate, which is the first thing anyone sees.
"""

import json

import streamlit.components.v1 as components
from lib import LABEL_COLORS

HERO = """
<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:__BG__;overflow:hidden;
  font-family:"Source Sans Pro",-apple-system,"Segoe UI",Roboto,sans-serif}
.panel{position:relative;height:100%;border-radius:__RADIUS__;overflow:hidden;background:__BG__}
canvas{position:absolute;inset:0;width:100%;height:100%;touch-action:none;cursor:grab}
canvas:active{cursor:grabbing}
.vig{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(120% 110% at 50% 45%,transparent 52%,rgba(7,20,16,.72) 100%)}
.legend{position:absolute;left:16px;bottom:14px;display:flex;gap:14px;flex-wrap:wrap;
  pointer-events:none;font-size:12px}
.key{display:flex;align-items:center;gap:6px;color:#A9C3B5}
.key i{width:9px;height:9px;border-radius:50%;flex:none}
.key b{color:#EAF3ED;font-weight:700}
.grab{position:absolute;right:16px;bottom:14px;font-size:11px;color:#7E9C8C;
  pointer-events:none;transition:opacity .5s}
@media (prefers-reduced-motion:reduce){*{transition-duration:.01ms!important}}
</style></head><body>
<div class="panel">
  <canvas id="cv" aria-label="Rotatable 3D field of this shop's customers"></canvas>
  <div class="vig"></div>
  <div class="legend" id="legend"></div>
  <span class="grab" id="grab">drag to turn</span>
</div>
<script>
(function(){
  "use strict";
  var DATA=__DATA__, COLORS=__COLORS__, BARE=__BARE__;
  var reduce=window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if(!DATA.length) return;
  // As a page background the field carries no furniture: the headline sits over
  // it, so a legend and axis labels would just be clutter behind the words.
  if(BARE){
    // A scrim down the left so the headline always reads, whatever drifts past.
    document.querySelector(".vig").style.background =
      "linear-gradient(to right, __BG__ 0%, __BG__ 30%, __BG__dd 44%, transparent 68%)";
    document.getElementById("legend").style.display="none";
  }

  function extent(k){ var lo=Infinity,hi=-Infinity;
    DATA.forEach(function(d){ if(d[k]<lo)lo=d[k]; if(d[k]>hi)hi=d[k]; }); return [lo,hi]; }
  var eGap=extent("gap"), eUp=extent("up"), eSpend=extent("spend");
  function span(v,e){ return e[1]===e[0]?0:(v-e[0])/(e[1]-e[0])*2-1; }
  var ZERO=span(0,eUp)*1.05;
  DATA.forEach(function(d){
    d.x=span(d.gap,eGap)*1.05; d.y=span(d.up,eUp)*1.05; d.z=span(d.spend,eSpend)*1.05; });

  var cv=document.getElementById("cv"), ctx=cv.getContext("2d"), grab=document.getElementById("grab");
  var W=0,H=0,k=1,yaw=-0.6,pitch=0.36,dist=4.2,spin=!reduce,beams=[],last=0;

  function size(){
    var r=cv.getBoundingClientRect(); if(!r.width||!r.height) return;
    var dpr=Math.min(window.devicePixelRatio||1,2);
    W=r.width; H=r.height; cv.width=Math.round(W*dpr); cv.height=Math.round(H*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0); k=Math.min(W,H)*(BARE?0.40:0.46);
  }
  function project(x,y,z){
    var cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
    var x1=x*cy-z*sy, z1=x*sy+z*cy, y1=y*cp-z1*sp, z2=y*sp+z1*cp;
    var w=dist/(dist+z2);
    // Pushed right as a background, so the cloud sits beside the headline
    // instead of behind it.
    return {sx:W/2+x1*w*k+(BARE?W*0.24:0), sy:H/2-y1*w*k, w:w, d:z2};
  }
  function seg(a,b,alpha,width){
    var p=project(a[0],a[1],a[2]), q=project(b[0],b[1],b[2]);
    ctx.globalAlpha=alpha; ctx.lineWidth=width||1;
    ctx.beginPath(); ctx.moveTo(p.sx,p.sy); ctx.lineTo(q.sx,q.sy); ctx.stroke(); ctx.globalAlpha=1;
  }
  function label(text,x,y,z){
    var p=project(x,y,z), pad=10, half=ctx.measureText(text).width/2;
    ctx.fillText(text, Math.min(Math.max(p.sx,pad+half),W-pad-half),
                       Math.min(Math.max(p.sy,pad+7),H-pad-7));
  }
  var LIT={};
  function lit(hex){
    if(LIT[hex]) return LIT[hex];
    var m=/^#?([0-9a-f]{6})$/i.exec(hex); if(!m){ LIT[hex]=hex; return hex; }
    var n=parseInt(m[1],16), out="#";
    [(n>>16)&255,(n>>8)&255,n&255].forEach(function(c){
      out+=Math.round(c+(255-c)*0.55).toString(16).padStart(2,"0"); });
    LIT[hex]=out; return out;
  }

  var ORIGIN=[-1.25,ZERO,-1.25];
  var MOVABLE=DATA.filter(function(d){ return d.lab==="Persuadable"; });
  function addBeam(){
    if(!MOVABLE.length) return;
    beams.push({t:MOVABLE[Math.floor(Math.random()*MOVABLE.length)],at:0});
    if(beams.length>6) beams.shift();
  }

  function draw(){
    if(!W){ size(); if(!W) return; }
    ctx.clearRect(0,0,W,H);

    ctx.strokeStyle=BARE?"#1E3A30":"#2F6253";
    for(var g=-1;g<=1;g+=0.5){
      seg([-1.05,ZERO,g],[1.05,ZERO,g],BARE?0.5:0.6);
      seg([g,ZERO,-1.05],[g,ZERO,1.05],BARE?0.5:0.6);
    }
    if(!BARE){
      ctx.strokeStyle="#9FBDAE";
      seg([-1.05,ZERO,-1.05],[1.05,ZERO,-1.05],0.6,1.5);
      seg([-1.05,ZERO,-1.05],[-1.05,ZERO,1.05],0.6,1.5);
      seg([-1.05,ZERO,-1.05],[-1.05,1.1,-1.05],0.6,1.5);
      ctx.font='600 11px -apple-system,"Segoe UI",sans-serif';
      ctx.fillStyle="#9FBDAE"; ctx.textAlign="center"; ctx.textBaseline="middle";
      label("uplift", -1.05, 1.2, -1.05);
      label(eGap[1]+" days since visit", 1.16, ZERO, -1.05);
      label("$"+Math.round(eSpend[1])+" basket", -1.05, ZERO, 1.18);
    }

    DATA.forEach(function(d){
      var p=project(d.x,d.y,d.z);
      d.sx=p.sx; d.sy=p.sy; d.depth=p.d; d.sr=Math.max(2.8,8.5*p.w);
    });

    var o=project(ORIGIN[0],ORIGIN[1],ORIGIN[2]);
    beams.forEach(function(b){
      var e=Math.min(1,b.at), ease=1-Math.pow(1-e,3), t=b.t;
      if(t.sx===undefined) return;
      var px=o.sx+(t.sx-o.sx)*ease, py=o.sy+(t.sy-o.sy)*ease, tail=Math.max(0,ease-0.2);
      ctx.globalAlpha=0.65*(1-e*0.6); ctx.strokeStyle=lit(COLORS["Persuadable"]); ctx.lineWidth=1.4;
      ctx.beginPath(); ctx.moveTo(o.sx+(t.sx-o.sx)*tail,o.sy+(t.sy-o.sy)*tail);
      ctx.lineTo(px,py); ctx.stroke();
      ctx.globalAlpha=1-e*0.45; ctx.fillStyle=lit(COLORS["Persuadable"]);
      ctx.beginPath(); ctx.arc(px,py,2.6,0,Math.PI*2); ctx.fill(); ctx.globalAlpha=1;
    });

    DATA.slice().sort(function(a,b){ return b.depth-a.depth; }).forEach(function(d){
      var near=1-Math.min(1,Math.max(0,(d.depth+1.4)/2.9));
      var col=COLORS[d.lab]||"#9CA3AF", r=d.sr;
      // a faint halo so each sphere separates from the dark panel
      ctx.globalAlpha=(0.07+near*0.1); ctx.fillStyle=col;
      ctx.beginPath(); ctx.arc(d.sx,d.sy,r*1.7,0,Math.PI*2); ctx.fill();
      var grad=ctx.createRadialGradient(d.sx-r*0.33,d.sy-r*0.38,r*0.08,d.sx,d.sy,r);
      grad.addColorStop(0,"#ffffff"); grad.addColorStop(0.28,lit(col));
      grad.addColorStop(0.72,col); grad.addColorStop(1,"rgba(0,0,0,0.45)");
      ctx.globalAlpha=0.55+near*0.45; ctx.fillStyle=grad;
      ctx.beginPath(); ctx.arc(d.sx,d.sy,r,0,Math.PI*2); ctx.fill(); ctx.globalAlpha=1;
    });
  }
  function tick(ts){
    if(spin) yaw+=0.0022;
    if(!reduce){
      for(var i=beams.length-1;i>=0;i--){ beams[i].at+=0.018; if(beams[i].at>1.3) beams.splice(i,1); }
      if(ts-last>750){ addBeam(); last=ts; }
    }
    draw(); requestAnimationFrame(tick);
  }

  var counts={};
  DATA.forEach(function(d){ counts[d.lab]=(counts[d.lab]||0)+1; });
  document.getElementById("legend").innerHTML =
    ["Persuadable","Sure Thing","Lost Cause"].filter(function(l){ return counts[l]; })
    .map(function(l){ return '<span class="key"><i style="background:'+COLORS[l]+'"></i>'
      +'<b>'+counts[l]+'</b> '+l+'</span>'; }).join("");

  var drag=false,lx=0,ly=0;
  cv.addEventListener("pointerdown",function(e){
    drag=true; lx=e.clientX; ly=e.clientY; cv.setPointerCapture(e.pointerId);
    if(spin){ spin=false; grab.style.opacity=0; }
  });
  cv.addEventListener("pointermove",function(e){
    if(!drag) return;
    yaw -= (e.clientX-lx)*0.008;                 // the near face follows the hand
    pitch = Math.max(-1.2,Math.min(1.2,pitch+(e.clientY-ly)*0.006));
    lx=e.clientX; ly=e.clientY; draw();
  });
  cv.addEventListener("pointerup",function(){ drag=false; });

  if(window.ResizeObserver) new ResizeObserver(function(){ size(); draw(); }).observe(cv);
  else window.addEventListener("resize",function(){ size(); draw(); });
  size(); draw(); requestAnimationFrame(tick);
})();
</script></body></html>
"""


def render_hero(df, height=430, background=False, bg_color="#0B201A"):
    """Draw the customer field. `df` is the customers table from `lib.load_customers`.

    `background=True` strips the legend, axis labels and rounded edge, and shifts
    the cloud right, for use as a full-page backdrop with text over it.
    """
    rows = [
        {
            "lab": r.label,
            "up": round(float(r.uplift) * 100, 1),
            "gap": int(r.days_since_last_visit),
            "spend": round(float(r.avg_spend_sgd), 2),
        }
        for _, r in df.iterrows()
    ]
    components.html(
        HERO.replace("__DATA__", json.dumps(rows))
            .replace("__COLORS__", json.dumps(LABEL_COLORS))
            .replace("__BARE__", "true" if background else "false")
            .replace("__BG__", bg_color)
            .replace("__RADIUS__", "0" if background else "18px"),
        height=height,
    )
