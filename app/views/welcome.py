"""Welcome: the landing screen, with the shop's own customers floating behind it.

The hero is not decoration. It is this shop's customer book in three dimensions -
height is uplift, so the handful of people worth messaging stand above everyone
else - and the messages flying out of the corner go to exactly those people. The
pitch and the product are the same picture.

Overview is untouched; this sits in front of it as the first thing the app shows.
"""

import json

import streamlit as st
import streamlit.components.v1 as components
from lib import LABEL_COLORS, load_customers, summary

HERO = """
<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#0D241E;overflow:hidden;
  font-family:"Source Sans Pro",-apple-system,"Segoe UI",Roboto,sans-serif}
.hero{position:relative;height:100%;border-radius:22px;overflow:hidden;isolation:isolate}
canvas{position:absolute;inset:0;width:100%;height:100%;z-index:0;touch-action:none;cursor:grab}
canvas:active{cursor:grabbing}
.veil{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(130% 100% at 74% 44%,transparent 44%,rgba(13,36,30,.55) 90%),
             linear-gradient(to right,rgba(13,36,30,.94) 0%,rgba(13,36,30,.52) 42%,transparent 66%)}
.inner{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;
  justify-content:center;gap:18px;padding:34px 38px;max-width:36rem;pointer-events:none}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:#D4EF9B}
h1{margin:0;color:#F5FAF4;font-size:clamp(1.9rem,3.6vw,2.9rem);line-height:1.12;
  letter-spacing:-.035em;font-weight:700;text-wrap:balance}
h1 em{font-style:normal;color:#5FE0A4}
p{margin:0;color:#BFCEC5;font-size:15px;line-height:1.7;max-width:34rem}
.pills{display:flex;gap:7px;flex-wrap:wrap}
.pill{border-radius:99px;padding:5px 11px;background:#FFFFFF14;border:1px solid #FFFFFF26;
  color:#D8E8DD;font-size:11px;font-weight:600}
.grab{position:absolute;right:18px;bottom:14px;z-index:2;font-size:11px;color:#7E9C8C;
  pointer-events:none;transition:opacity .5s}
@media (max-width:620px){.inner{padding:24px;max-width:none}.veil{
  background:linear-gradient(to bottom,rgba(13,36,30,.9) 0%,rgba(13,36,30,.6) 60%,rgba(13,36,30,.8) 100%)}}
@media (prefers-reduced-motion:reduce){*{transition-duration:.01ms!important}}
</style></head><body>
<div class="hero">
  <canvas id="cv" aria-hidden="true"></canvas>
  <div class="veil"></div>
  <div class="inner">
    <span class="eyebrow">__EYEBROW__</span>
    <h1>Message the people a message would <em>actually change</em>.</h1>
    <p>__LEDE__</p>
    <div class="pills">__PILLS__</div>
  </div>
  <span class="grab" id="grab">drag the field</span>
</div>
<script>
(function(){
  "use strict";
  var DATA=__DATA__, COLORS=__COLORS__;
  var reduce=window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if(!DATA.length) return;

  function extent(k){ var lo=Infinity,hi=-Infinity;
    DATA.forEach(function(d){ if(d[k]<lo)lo=d[k]; if(d[k]>hi)hi=d[k]; }); return [lo,hi]; }
  var eGap=extent("gap"), eUp=extent("up"), eSpend=extent("spend");
  function span(v,e){ return e[1]===e[0]?0:(v-e[0])/(e[1]-e[0])*2-1; }
  var ZERO=span(0,eUp)*1.05;
  DATA.forEach(function(d){
    d.x=span(d.gap,eGap)*1.05; d.y=span(d.up,eUp)*1.05; d.z=span(d.spend,eSpend)*1.05; });

  var cv=document.getElementById("cv"), ctx=cv.getContext("2d"), grab=document.getElementById("grab");
  var W=0,H=0,k=1,yaw=-0.55,pitch=0.34,dist=4.0,spin=!reduce,beams=[],last=0;

  function size(){
    var r=cv.getBoundingClientRect(); if(!r.width||!r.height) return;
    var dpr=Math.min(window.devicePixelRatio||1,2);
    W=r.width; H=r.height; cv.width=Math.round(W*dpr); cv.height=Math.round(H*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0); k=Math.min(W,H)*0.42;
  }
  function project(x,y,z){
    var cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
    var x1=x*cy-z*sy, z1=x*sy+z*cy, y1=y*cp-z1*sp, z2=y*sp+z1*cp;
    var w=dist/(dist+z2);
    return {sx:W/2+x1*w*k+W*0.16, sy:H/2-y1*w*k, w:w, d:z2};
  }
  function seg(a,b,alpha){
    var p=project(a[0],a[1],a[2]), q=project(b[0],b[1],b[2]);
    ctx.globalAlpha=alpha; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(p.sx,p.sy); ctx.lineTo(q.sx,q.sy); ctx.stroke(); ctx.globalAlpha=1;
  }
  var LIT={};
  function lit(hex){
    if(LIT[hex]) return LIT[hex];
    var m=/^#?([0-9a-f]{6})$/i.exec(hex); if(!m){ LIT[hex]=hex; return hex; }
    var n=parseInt(m[1],16), out="#";
    [(n>>16)&255,(n>>8)&255,n&255].forEach(function(c){
      out+=Math.round(c+(255-c)*0.5).toString(16).padStart(2,"0"); });
    LIT[hex]=out; return out;
  }

  var ORIGIN=[-1.25,ZERO,-1.25];
  var MOVABLE=DATA.filter(function(d){ return d.lab==="Persuadable"; });
  function addBeam(){
    if(!MOVABLE.length) return;
    beams.push({t:MOVABLE[Math.floor(Math.random()*MOVABLE.length)],at:0});
    if(beams.length>5) beams.shift();
  }

  function draw(){
    if(!W){ size(); if(!W) return; }
    ctx.clearRect(0,0,W,H);
    ctx.strokeStyle="#2E5A4C";
    for(var g=-1;g<=1;g+=0.5){
      seg([-1.05,ZERO,g],[1.05,ZERO,g],0.4);
      seg([g,ZERO,-1.05],[g,ZERO,1.05],0.4);
    }
    DATA.forEach(function(d){
      var p=project(d.x,d.y,d.z);
      d.sx=p.sx; d.sy=p.sy; d.depth=p.d; d.sr=Math.max(2.6,9*p.w);
    });
    var o=project(ORIGIN[0],ORIGIN[1],ORIGIN[2]);
    beams.forEach(function(b){
      var e=Math.min(1,b.at), ease=1-Math.pow(1-e,3), t=b.t;
      if(t.sx===undefined) return;
      var px=o.sx+(t.sx-o.sx)*ease, py=o.sy+(t.sy-o.sy)*ease, tail=Math.max(0,ease-0.16);
      ctx.globalAlpha=0.45*(1-e*0.7); ctx.strokeStyle=lit(COLORS["Persuadable"]); ctx.lineWidth=1;
      ctx.beginPath(); ctx.moveTo(o.sx+(t.sx-o.sx)*tail,o.sy+(t.sy-o.sy)*tail);
      ctx.lineTo(px,py); ctx.stroke();
      ctx.globalAlpha=1-e*0.55; ctx.fillStyle=lit(COLORS["Persuadable"]);
      ctx.beginPath(); ctx.arc(px,py,2,0,Math.PI*2); ctx.fill(); ctx.globalAlpha=1;
    });
    DATA.slice().sort(function(a,b){ return b.depth-a.depth; }).forEach(function(d){
      var near=1-Math.min(1,Math.max(0,(d.depth+1.4)/2.9));
      var col=COLORS[d.lab]||"#9CA3AF", r=d.sr;
      var grad=ctx.createRadialGradient(d.sx-r*0.35,d.sy-r*0.4,r*0.1,d.sx,d.sy,r);
      grad.addColorStop(0,lit(col)); grad.addColorStop(0.5,col);
      grad.addColorStop(1,"rgba(0,0,0,0.5)");
      ctx.globalAlpha=0.3+near*0.7; ctx.fillStyle=grad;
      ctx.beginPath(); ctx.arc(d.sx,d.sy,r,0,Math.PI*2); ctx.fill(); ctx.globalAlpha=1;
    });
  }
  function tick(ts){
    if(spin) yaw+=0.0016;
    if(!reduce){
      for(var i=beams.length-1;i>=0;i--){ beams[i].at+=0.016; if(beams[i].at>1.3) beams.splice(i,1); }
      if(ts-last>1000){ addBeam(); last=ts; }
    }
    draw(); requestAnimationFrame(tick);
  }

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

df = load_customers()
movable = int((df.label == "Persuadable").sum())

rows = [
    {
        "lab": r.label,
        "up": round(float(r.uplift) * 100, 1),
        "gap": int(r.days_since_last_visit),
        "spend": round(float(r.avg_spend_sgd), 2),
    }
    for _, r in df.iterrows()
]

pills = ["AI-GNITION 2026 · top ten", "Finals 14 Nov 2026", "Kampung Fresh · demo data"]

components.html(
    HERO.replace("__DATA__", json.dumps(rows))
        .replace("__COLORS__", json.dumps(LABEL_COLORS))
        .replace("__EYEBROW__", "Small messages. Meaningful returns.")
        .replace("__LEDE__",
                 f"Every shop blasts the same promotion to everyone. Nudgely reads your WhatsApp "
                 f"chats, works out which {movable} of your {len(df)} customers are genuinely "
                 f"movable, writes each message from that customer's own history, and proves the "
                 f"lift against a group it deliberately left alone.")
        .replace("__PILLS__", "".join(f'<span class="pill">{p}</span>' for p in pills)),
    height=440,
)
st.caption("That is your own customer book behind the text: height is uplift, and the messages "
           "fly to the customers a nudge would actually move. Drag it.")

a, b, c = st.columns(3)
if a.button("Build a campaign →", type="primary", width="stretch"):
    st.switch_page("views/campaign.py")
if b.button("Explore your customers", width="stretch"):
    st.switch_page("views/customers.py")
if c.button("See the evidence", width="stretch"):
    st.switch_page("views/results.py")

st.markdown('<div class="section-label">How it works</div>', unsafe_allow_html=True)
steps = [
    ("01 · Listen", "Read the chats",
     "Every message a customer sends is tagged as it arrives: a restock they asked for, a "
     "delivery that went wrong, a party coming up. Evidence has to be quoted from something "
     "the customer actually said."),
    ("02 · Score", "Find who is movable",
     "An uplift model predicts the difference a message makes, not whether someone returns. "
     "Someone returning anyway is a wasted discount; someone gone for good is a wasted message."),
    ("03 · Write", "Fill an approved template",
     "WhatsApp forbids free text to open a conversation, so one of six approved sentences is "
     "chosen by the customer's strongest tag and its blanks filled. Invent a price and the "
     "message is thrown away, not patched."),
    ("04 · Prove", "Keep a holdout",
     "Some customers are deliberately not messaged. Without them you cannot tell a good message "
     "from a customer who was returning regardless."),
]
for col, (num, title, body) in zip(st.columns(4), steps):
    col.markdown(f'<div class="feature"><div class="num">{num}</div><h3>{title}</h3>'
                 f'<p>{body}</p></div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Where it stands</div>', unsafe_allow_html=True)
s = summary()
capture = s["top30_capture_share"] if s else None
ci = s.get("top30_capture_ci90") if s else None

f1, f2, f3 = st.columns(3)
with f1, st.container(border=True):
    st.metric("Top 30% captures", f"{capture:.0%}" if capture else "-",
              f"{capture / 0.3:.1f}x vs random" if capture else None)
    st.caption(f"Share of the extra visits, against 30% for picking at random. 90% interval "
               f"{ci[0]:.0%}-{ci[1]:.0%} - the spread is as much the finding as the number."
               if ci else "Share of the extra visits, from the historical Lenta experiment.")
with f2, st.container(border=True):
    st.metric("Tags found", "97%", "86% precision")
    st.caption("Across 32 hand-written test chats. Recall is the one that matters: a missed "
               "complaint becomes a promotion.")
with f3, st.container(border=True):
    st.metric("Columns needed", "3")
    st.caption("Phone, date and amount. Everything the model uses is derived from those three.")

st.markdown('<div class="section-label">Honest state</div>', unsafe_allow_html=True)
good, bad = st.columns(2)
with good, st.container(border=True):
    st.markdown("**Working**")
    st.markdown(
        "- Scoring a real shop from a purchase export\n"
        "- Tagging one message at a time, fast enough for a live webhook\n"
        "- Six approved templates, filled and checked, rejected rather than repaired\n"
        "- A reply bot that answers or hands to a person\n"
        "- Campaign measurement with a holdout and a measured lift")
with bad, st.container(border=True):
    st.markdown("**Not working yet**")
    st.markdown(
        "- **No inbound webhook.** MantaGO's documented API only sends\n"
        "- **No recency feature.** Every lapsed customer scores Lost Cause\n"
        "- **Sarcasm reads as satisfied**, the one tag the test set still misses\n"
        "- **Nothing sent to a real customer** without approved templates on a business number")

st.caption("Fictional identities and chats · Lenta and Hillstrom model scores · "
           "no live campaign has been sent.")
