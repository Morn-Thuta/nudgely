"""The customer field: the whole book of customers as one rotatable 3D picture.

The bar charts on the Results page say how well the model separates customers in
general. This says what it decided about *these* customers - where the movable
people sit relative to everyone else, and how much of the book is not worth
messaging at all. A table cannot show that, because the thing you are looking for
is a cluster.

Three axes, all from the customer file the rest of the app already uses: days
since their last visit, uplift, and what they usually spend. Height is the only
one the model produces; the other two are context, so you can see whether the
movable customers are the recent ones, the big spenders, or neither.
"""

import json

import streamlit as st
import streamlit.components.v1 as components
from lib import LABEL_COLORS, LABEL_HELP

PAGE = """
<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#153F36;
  font-family:"Source Sans Pro",-apple-system,"Segoe UI",Roboto,sans-serif;color:#EAF3ED}
.shell{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(0,1fr);height:100%;
  border-radius:22px;overflow:hidden}
/* Streamlit's sidebar eats most of a laptop's width, so the two columns have to
   survive further down than a normal page would need. */
@media (max-width:600px){.shell{grid-template-columns:1fr;grid-template-rows:minmax(290px,1fr) auto}}
.stage{position:relative;min-width:0;touch-action:none;cursor:grab}
.stage:active{cursor:grabbing}
.stage:focus-visible{outline:2px solid #3FD79A;outline-offset:-3px}
canvas{display:block;width:100%;height:100%}
.hint{position:absolute;left:16px;bottom:13px;font-size:11px;color:#8FA99B;
  pointer-events:none;transition:opacity .45s;letter-spacing:.02em}
.side{background:#11352E;border-left:1px solid #27544A;padding:18px;min-width:0;
  display:flex;flex-direction:column;gap:13px;overflow:auto}
@media (max-width:600px){.side{border-left:0;border-top:1px solid #27544A}}
.legend{display:flex;flex-direction:column;gap:7px}
.key{display:flex;align-items:center;gap:9px;font-size:13px;color:#9EB6A8}
.key i{width:10px;height:10px;border-radius:50%;flex:none}
.key b{color:#EAF3ED;font-weight:650}
.card{border:1px solid #27544A;border-radius:14px;padding:14px;background:#0E2E27;
  display:flex;flex-direction:column;gap:9px;min-height:188px}
.who{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.who b{font-size:15px;font-weight:650}
.who small{color:#8FA99B;font-weight:400;font-size:11px;display:block}
.tag{font-size:11px;padding:3px 9px;border-radius:99px;flex:none;font-weight:600}
.rows{display:flex;flex-direction:column;gap:5px;font-size:12.5px}
.row{display:flex;justify-content:space-between;gap:10px;color:#9EB6A8}
.row span:last-child{color:#EAF3ED;font-variant-numeric:tabular-nums;font-weight:600}
.say{font-size:12.5px;line-height:1.45;color:#CFE0D6}
.empty{color:#9EB6A8;font-size:13px;line-height:1.55}
.btns{display:flex;gap:8px;flex-wrap:wrap}
button{font:inherit;font-size:13px;font-weight:650;padding:9px 14px;border-radius:10px;
  border:1px solid #27544A;background:#0E2E27;color:#EAF3ED;cursor:pointer}
button:hover{border-color:#3FD79A}
button:focus-visible{outline:2px solid #3FD79A;outline-offset:2px}
button.on{background:#0E9F6E;border-color:#0E9F6E;color:#06231A}
.axes{font-size:11.5px;color:#8FA99B;line-height:1.75;margin-top:auto}
.axes b{color:#CFE0D6}
@media (prefers-reduced-motion:reduce){*{transition-duration:.01ms!important}}
</style></head><body>
<div class="shell">
  <div class="stage" id="stage" tabindex="0" role="application"
       aria-label="Rotatable 3D field of customers. Arrow keys rotate, Enter steps through them.">
    <canvas id="cv"></canvas>
    <div class="hint" id="hint">drag to rotate · click a customer</div>
  </div>
  <div class="side">
    <div class="legend" id="legend"></div>
    <div class="card" id="card"></div>
    <div class="btns">
      <button id="top">Show the top 30%</button>
      <button id="reset">Reset</button>
    </div>
    <div class="axes">
      <b>x</b> days since last visit<br>
      <b>y</b> uplift — what a message changes<br>
      <b>z</b> average basket
    </div>
  </div>
</div>
<script>
(function(){
  "use strict";
  var DATA = __DATA__, COLORS = __COLORS__;
  var SAY = __SAY__;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function extent(key){
    var lo=Infinity, hi=-Infinity;
    DATA.forEach(function(d){ if(d[key]<lo)lo=d[key]; if(d[key]>hi)hi=d[key]; });
    return [lo,hi];
  }
  var eGap=extent("gap"), eUp=extent("up"), eSpend=extent("spend");
  function span(v,e){ return e[1]===e[0] ? 0 : (v-e[0])/(e[1]-e[0])*2-1; }
  var ZERO = span(0,eUp)*1.05;

  DATA.forEach(function(d){
    d.x=span(d.gap,eGap)*1.05; d.y=span(d.up,eUp)*1.05; d.z=span(d.spend,eSpend)*1.05;
  });
  var ranked = DATA.slice().sort(function(a,b){ return b.up-a.up; });
  var cut = Math.round(DATA.length*0.3);
  ranked.forEach(function(d,i){ d.top = i<cut; });

  var stage=document.getElementById("stage"), cv=document.getElementById("cv"),
      ctx=cv.getContext("2d"), hint=document.getElementById("hint");
  var W=0,H=0,k=1, yaw=-0.72, pitch=0.42, dist=4.0;
  var spin=!reduce, selected=null, hover=null, onlyTop=false, pulse=0, running=false;

  function size(){
    var r=stage.getBoundingClientRect();
    if(!r.width||!r.height) return;
    var dpr=Math.min(window.devicePixelRatio||1,2);
    W=r.width; H=r.height;
    cv.width=Math.round(W*dpr); cv.height=Math.round(H*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    k=Math.min(W,H)*0.33;
  }
  function project(x,y,z){
    var cy=Math.cos(yaw), sy=Math.sin(yaw), cp=Math.cos(pitch), sp=Math.sin(pitch);
    var x1=x*cy-z*sy, z1=x*sy+z*cy, y1=y*cp-z1*sp, z2=y*sp+z1*cp;
    var w=dist/(dist+z2);
    return {sx:W/2+x1*w*k, sy:H/2-y1*w*k, w:w, d:z2};
  }
  function seg(a,b,alpha,width){
    var p=project(a[0],a[1],a[2]), q=project(b[0],b[1],b[2]);
    ctx.globalAlpha=alpha; ctx.lineWidth=width||1;
    ctx.beginPath(); ctx.moveTo(p.sx,p.sy); ctx.lineTo(q.sx,q.sy); ctx.stroke();
    ctx.globalAlpha=1;
  }
  function label(text,x,y,z){
    var p=project(x,y,z), pad=9, half=ctx.measureText(text).width/2;
    ctx.fillText(text, Math.min(Math.max(p.sx,pad+half),W-pad-half),
                       Math.min(Math.max(p.sy,pad+6),H-pad-6));
  }

  function draw(){
    if(!W){ size(); if(!W) return; }
    ctx.clearRect(0,0,W,H);
    ctx.strokeStyle="#27544A";
    for(var g=-1;g<=1;g+=0.5){
      seg([-1.05,ZERO,g],[1.05,ZERO,g],0.55);
      seg([g,ZERO,-1.05],[g,ZERO,1.05],0.55);
    }
    ctx.strokeStyle="#8FA99B";
    seg([-1.05,ZERO,-1.05],[1.05,ZERO,-1.05],0.5,1.4);
    seg([-1.05,ZERO,-1.05],[-1.05,ZERO,1.05],0.5,1.4);
    seg([-1.05,ZERO,-1.05],[-1.05,1.1,-1.05],0.5,1.4);
    ctx.font='600 10px -apple-system,"Segoe UI",sans-serif';
    ctx.fillStyle="#8FA99B"; ctx.textAlign="center"; ctx.textBaseline="middle";
    label(eGap[1]+" days since visit", 1.16, ZERO, -1.05);
    label("$"+Math.round(eSpend[1])+" basket", -1.05, ZERO, 1.18);
    label("+"+eUp[1].toFixed(0)+" pts uplift", -1.05, 1.2, -1.05);

    DATA.forEach(function(d){
      var p=project(d.x,d.y,d.z);
      d.sx=p.sx; d.sy=p.sy; d.depth=p.d; d.sr=Math.max(2.6, 8*p.w);
    });
    var order=DATA.slice().sort(function(a,b){ return b.depth-a.depth; });
    order.forEach(function(d,i){
      var dim = onlyTop && !d.top;
      var near = 1-Math.min(1,Math.max(0,(d.depth+1.4)/2.9));
      var a = (0.32+near*0.68)*(dim?0.18:1);
      var r = d.sr*(d===selected?1.7 : d===hover?1.3 : 1);
      if(onlyTop && d.top && !reduce) r *= 1+0.16*Math.sin(pulse+i*0.4);
      var col=COLORS[d.lab]||"#9CA3AF";
      var grad=ctx.createRadialGradient(d.sx-r*0.35,d.sy-r*0.4,r*0.1,d.sx,d.sy,r);
      grad.addColorStop(0,lit(col)); grad.addColorStop(0.5,col);
      grad.addColorStop(1,"rgba(0,0,0,0.5)");
      ctx.globalAlpha=a; ctx.fillStyle=grad;
      ctx.beginPath(); ctx.arc(d.sx,d.sy,r,0,Math.PI*2); ctx.fill();
      if(d===selected||d===hover){
        ctx.globalAlpha=1; ctx.strokeStyle=col; ctx.lineWidth=1.5;
        ctx.beginPath(); ctx.arc(d.sx,d.sy,r+3.5,0,Math.PI*2); ctx.stroke();
      }
      ctx.globalAlpha=1;
    });
  }
  function tick(){
    running=false;
    if(spin) yaw += 0.0022;
    if(onlyTop && !reduce) pulse += 0.055;
    draw();
    if(spin || (onlyTop && !reduce)) start();
  }
  function start(){ if(!running){ running=true; requestAnimationFrame(tick); } }

  // The app's label colours were picked for white cards. On the dark panel the
  // brand green sinks into the background, so each sphere gets a lit core in a
  // paler version of its own colour rather than a different colour.
  var LIT={};
  function lit(hex){
    if(LIT[hex]) return LIT[hex];
    var m=/^#?([0-9a-f]{6})$/i.exec(hex);
    if(!m){ LIT[hex]=hex; return hex; }
    var n=parseInt(m[1],16), out="#";
    [(n>>16)&255,(n>>8)&255,n&255].forEach(function(c){
      out += Math.round(c+(255-c)*0.5).toString(16).padStart(2,"0");
    });
    LIT[hex]=out;
    return out;
  }

  function at(mx,my){
    var best=null, bd=Infinity;
    DATA.forEach(function(d){
      var dx=d.sx-mx, dy=d.sy-my, d2=dx*dx+dy*dy, reach=Math.max(14,d.sr+9);
      if(d2<reach*reach && d2<bd){ bd=d2; best=d; }
    });
    return best;
  }

  var card=document.getElementById("card");
  function esc(s){ return String(s).replace(/[&<>]/g,function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c]; }); }
  function show(d){
    if(!d){
      card.innerHTML='<p class="empty">Click any customer to see what the model decided about '
        +'them.<br><br>Height is uplift. The flat grid is zero — below it, a message makes '
        +'things slightly worse.</p>';
      return;
    }
    var col=COLORS[d.lab]||"#9CA3AF";
    card.innerHTML =
      '<div class="who"><b>'+esc(d.name)+'<small>'+esc(d.id)+'</small></b>'
      +'<span class="tag" style="background:'+col+'26;color:'+col+'">'+esc(d.lab)+'</span></div>'
      +'<div class="rows">'
      +'<div class="row"><span>Returns if messaged</span><span>'+d.pm.toFixed(1)+'%</span></div>'
      +'<div class="row"><span>Returns if left alone</span><span>'+d.pn.toFixed(1)+'%</span></div>'
      +'<div class="row"><span>Uplift</span><span>'+(d.up>0?"+":"")+d.up.toFixed(1)+' pts</span></div>'
      +'<div class="row"><span>Visits a month</span><span>'+d.visits+'</span></div>'
      +'<div class="row"><span>Average basket</span><span>$'+d.spend.toFixed(2)+'</span></div>'
      +'<div class="row"><span>Days since last visit</span><span>'+d.gap+'</span></div>'
      +'</div><p class="say">'+esc(SAY[d.lab]||"")+'</p>';
  }
  show(null);

  var counts={};
  DATA.forEach(function(d){ counts[d.lab]=(counts[d.lab]||0)+1; });
  document.getElementById("legend").innerHTML =
    ["Persuadable","Sure Thing","Lost Cause"].filter(function(l){ return counts[l]; })
    .map(function(l){
      return '<div class="key"><i style="background:'+COLORS[l]+'"></i><b>'+counts[l]+'</b> '+l+'</div>';
    }).join("");

  var drag=false,lx=0,ly=0,moved=0;
  stage.addEventListener("pointerdown",function(e){
    drag=true; moved=0; lx=e.clientX; ly=e.clientY;
    stage.setPointerCapture(e.pointerId);
    if(spin){ spin=false; hint.style.opacity=0; }
    start();
  });
  stage.addEventListener("pointermove",function(e){
    var r=cv.getBoundingClientRect(), mx=e.clientX-r.left, my=e.clientY-r.top;
    if(drag){
      var dx=e.clientX-lx, dy=e.clientY-ly;
      moved+=Math.abs(dx)+Math.abs(dy);
      yaw -= dx*0.008;                      // the near face follows the hand
      pitch=Math.max(-1.25,Math.min(1.25,pitch+dy*0.006));
      lx=e.clientX; ly=e.clientY; draw();
    } else {
      var h=at(mx,my);
      if(h!==hover){ hover=h; stage.style.cursor=h?"pointer":"grab"; draw(); }
    }
  });
  stage.addEventListener("pointerup",function(e){
    drag=false;
    if(moved<7){
      var r=cv.getBoundingClientRect();
      var hit=at(e.clientX-r.left,e.clientY-r.top);
      selected=(hit===selected)?null:hit;
      show(selected); draw();
    }
  });
  stage.addEventListener("pointerleave",function(){ if(hover){ hover=null; draw(); } });
  stage.addEventListener("keydown",function(e){
    var step=0.12, used=true;
    if(e.key==="ArrowLeft") yaw+=step;
    else if(e.key==="ArrowRight") yaw-=step;
    else if(e.key==="ArrowUp") pitch=Math.min(1.25,pitch+step);
    else if(e.key==="ArrowDown") pitch=Math.max(-1.25,pitch-step);
    else if(e.key==="Enter"||e.key===" "){
      var i = selected ? (ranked.indexOf(selected)+1)%ranked.length : 0;
      selected=ranked[i]; show(selected);
    } else used=false;
    if(used){ e.preventDefault(); spin=false; hint.style.opacity=0; draw(); }
  });

  var topBtn=document.getElementById("top");
  topBtn.addEventListener("click",function(){
    onlyTop=!onlyTop;
    topBtn.classList.toggle("on",onlyTop);
    topBtn.textContent = onlyTop ? "Show everyone" : "Show the top 30%";
    start(); draw();
  });
  document.getElementById("reset").addEventListener("click",function(){
    yaw=-0.72; pitch=0.42; selected=null; hover=null; onlyTop=false;
    topBtn.classList.remove("on"); topBtn.textContent="Show the top 30%";
    show(null); draw();
  });

  if(window.ResizeObserver) new ResizeObserver(function(){ size(); draw(); }).observe(stage);
  else window.addEventListener("resize",function(){ size(); draw(); });
  size(); draw(); start();
})();
</script></body></html>
"""

def customer_field(df, height=560):
    """Draw the scored customer book as a rotatable 3D field.

    `df` is the customers table as `lib.load_customers` returns it.
    """
    rows = [
        {
            "id": r.customer_id,
            "name": r["name"],
            "lab": r.label,
            "up": round(float(r.uplift) * 100, 1),
            "pm": round(float(r.p_msg) * 100, 1),
            "pn": round(float(r.p_no_msg) * 100, 1),
            "gap": int(r.days_since_last_visit),
            "spend": round(float(r.avg_spend_sgd), 2),
            "visits": round(float(r.visits_per_month), 1),
        }
        for _, r in df.iterrows()
    ]

    components.html(
        PAGE.replace("__DATA__", json.dumps(rows))
            .replace("__COLORS__", json.dumps(LABEL_COLORS))
            .replace("__SAY__", json.dumps(LABEL_HELP)),
        height=height,
    )

    st.caption(
        "Drag to turn the field, click a customer to see their scores. Height is the model's "
        "estimate; days since last visit and average basket are shown for context and are not "
        "model inputs. Fictional identities, Lenta model scores."
    )

    with st.expander("How to read it"):
        st.markdown(
            "**Look along the uplift axis.** Most customers sit in a flat band near zero. The "
            "handful standing well above it are the whole return on a campaign, and a table of "
            "30 rows hides how few of them there are.\n\n"
            "**Look along the recency axis.** The customers who have not visited in months "
            "cluster low. The model has no recency feature, so it cannot tell a lapsed customer "
            "from a quiet one, and a win-back tool that refuses to message anyone who left is a "
            "problem worth knowing about before the pitch.\n\n"
            "**Some customers sit below the grid.** Their uplift is negative: the model expects "
            "a message to make them slightly *less* likely to return. Those are the ones a "
            "blanket promotion costs you."
        )
