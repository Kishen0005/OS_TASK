"""Shared helpers: thread-safe event recorder, trace verifier, HTML generator.
Every simulation HTML is built ONLY from the events recorded by the running threads."""
import argparse, json, os, threading, time

class TraceRecorder:
    """Collects timestamped state-change events from many threads (lock keeps a total order)."""
    def __init__(self, title, kind, approach, actors, initial, notes=""):
        self.meta = dict(title=title, kind=kind, approach=approach, actors=actors,
                         initial=initial, notes=notes)
        self.events, self._lock, self._t0 = [], threading.Lock(), time.perf_counter()

    def log(self, actor, state, detail=""):
        with self._lock:
            self.events.append({"t": round(time.perf_counter() - self._t0, 4),
                                "actor": actor, "state": state, "detail": str(detail)})

    def trace(self):
        d = dict(self.meta); d["events"] = self.events; return d

def verify(trace):
    """Replay the trace and check the safety properties; returns list of violations."""
    st = dict(trace["initial"]); owner = {}; bad = []
    for e in trace["events"]:
        a, s, d = e["actor"], e["state"], e["detail"]
        if trace["kind"] == "dp" and a.startswith("F"):
            if s == "held":
                if owner.get(a): bad.append(f"{a} held by two philosophers at t={e['t']}")
                owner[a] = d
            else: owner[a] = None
        st[a] = s
        if trace["kind"] == "rw":
            rd = [x for x in st if x[0] == "R" and st[x] == "reading"]
            wr = [x for x in st if x[0] == "W" and st[x] == "writing"]
            if len(wr) > 1 or (wr and rd): bad.append(f"mutual exclusion broken at t={e['t']}: {rd+wr}")
        else:
            n = len([x for x in st if x[0] == "P"])
            for i in range(n):
                if st[f"P{i}"] == "eating" and st[f"P{(i+1)%n}"] == "eating":
                    bad.append(f"neighbours P{i},P{(i+1)%n} eating together at t={e['t']}")
    return bad

def rw_args():
    p = argparse.ArgumentParser()
    p.add_argument("--readers", type=int, default=4); p.add_argument("--writers", type=int, default=2)
    p.add_argument("--rounds", type=int, default=3); p.add_argument("--delay", type=float, default=0.3)
    p.add_argument("--out", default="generated_html"); return p.parse_args()

def dp_args():
    p = argparse.ArgumentParser()
    p.add_argument("--meals", type=int, default=3); p.add_argument("--delay", type=float, default=0.3)
    p.add_argument("--out", default="generated_html"); return p.parse_args()

def finish(rec, out_dir, name):
    tr = rec.trace(); bad = verify(tr)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, name + ".json"), "w") as f: json.dump(tr, f, indent=1)
    with open(os.path.join(out_dir, name + ".html"), "w", encoding="utf-8") as f:
        f.write(HTML.replace("__TITLE__", tr["title"]).replace("__TRACE__", json.dumps(tr)))
    print(f"{len(tr['events'])} events -> {out_dir}/{name}.html |",
          "trace verified: no violations" if not bad else f"VIOLATIONS: {bad[:3]}")

HTML = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
body{font-family:system-ui,sans-serif;margin:16px;background:#f6f7f9;color:#1f2933}
h1{font-size:20px;margin:0 0 4px}.sub{color:#52606d;font-size:13px;margin-bottom:10px}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0}
button,select{padding:6px 12px;border:1px solid #b6c0cb;border-radius:6px;background:#fff;cursor:pointer}
.main{display:flex;gap:16px;flex-wrap:wrap}.panel{background:#fff;border:1px solid #d9e0e7;border-radius:8px;padding:12px}
.box{display:inline-block;min-width:92px;padding:8px;margin:4px;border-radius:8px;color:#fff;text-align:center;font-size:13px}
#log{height:380px;overflow:auto;font-size:12px;width:430px}#log div{padding:2px 4px;cursor:pointer;border-bottom:1px solid #eef1f4}
#log .cur{background:#fff3c4}.legend span{display:inline-block;margin-right:8px;font-size:12px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:3px}
</style></head><body>
<h1>__TITLE__</h1><div class="sub" id="sub"></div>
<div class="bar"><button id="start">Start</button><button id="pause">Pause</button><button id="reset">Reset</button>
Speed <select id="speed"><option value="1">1x</option><option value="2" selected>2x</option><option value="5">5x</option><option value="10">10x</option></select>
<input type="range" id="slider" min="0" value="0" style="width:260px"><span id="cnt"></span></div>
<div class="main"><div class="panel" style="flex:1;min-width:480px"><div id="view"></div><div class="legend" id="legend"></div></div>
<div class="panel"><b>Event timeline (recorded by program)</b><div id="log"></div></div></div>
<script>
const T=__TRACE__;const N=T.events.length;let idx=0,timer=null;
const COL={idle:"#9aa5b1",waiting:"#f5a623",reading:"#2e9e5b",writing:"#d9433f",done:"#6b7280",thinking:"#5b8fd6",hungry:"#f5a623",acquiring:"#9b5fd1",eating:"#2e9e5b",releasing:"#e08a5a",free:"#cfd6dd",held:"#d9433f"};
document.getElementById("sub").textContent=T.approach+" | "+T.notes;
const used=[...new Set([...Object.values(T.initial),...T.events.map(e=>e.state)])];
document.getElementById("legend").innerHTML=used.map(s=>`<span><i class="dot" style="background:${COL[s]||"#444"}"></i>${s}</span>`).join("");
const sl=document.getElementById("slider");sl.max=N;
document.getElementById("log").innerHTML=T.events.map((e,i)=>`<div id="e${i}" onclick="go(${i+1})">[${e.t.toFixed(2)}s] <b>${e.actor}</b> &rarr; ${e.state} ${e.detail}</div>`).join("");
function compute(n){const s={};T.actors.forEach(a=>s[a]={state:T.initial[a],detail:""});
 for(let i=0;i<n;i++){const e=T.events[i];s[e.actor]={state:e.state,detail:e.detail};}return s;}
function box(a,s){return `<div class="box" style="background:${COL[s[a].state]}"><b>${a}</b><br>${s[a].state}<br><small>${s[a].detail}</small></div>`;}
function renderRW(s){const R=T.actors.filter(a=>a[0]=="R"),W=T.actors.filter(a=>a[0]=="W");
 const rd=R.filter(a=>s[a].state=="reading"),wr=W.filter(a=>s[a].state=="writing"),wt=T.actors.filter(a=>s[a].state=="waiting");
 const res=wr.length?"LOCKED for writing by "+wr[0]:rd.length?"OPEN: "+rd.length+" reader(s) inside ("+rd.join(", ")+")":"FREE";
 document.getElementById("view").innerHTML=`<h3>Readers</h3>${R.map(a=>box(a,s)).join("")}<h3>Writers</h3>${W.map(a=>box(a,s)).join("")}
 <h3>Shared resource (critical section)</h3><div class="box" style="background:${wr.length?COL.writing:rd.length?COL.reading:COL.idle};width:90%">${res}</div>
 <p>Waiting queue: <b>${wt.join(", ")||"none"}</b></p>`;}
function renderDP(s){const n=T.actors.filter(a=>a[0]=="P").length,C=240;let g=`<svg width="480" height="480">`;
 const pos=(i,r,off)=>{const a=(-90+i*360/n+off)*Math.PI/180;return [C+r*Math.cos(a),C+r*Math.sin(a)];};
 g+=`<circle cx="${C}" cy="${C}" r="105" fill="#f0e6d2" stroke="#c9b48a"/>`;
 for(let i=0;i<n;i++){const f="F"+i,[fx,fy]=pos(i,95,360/n/2),[px,py]=pos(i,185,0);
  if(s[f].state=="held"){const o=+s[f].detail.slice(1),[ox,oy]=pos(o,185,0);g+=`<line x1="${fx}" y1="${fy}" x2="${ox}" y2="${oy}" stroke="#d9433f" stroke-width="4"/>`;}}
 for(let i=0;i<n;i++){const f="F"+i,[fx,fy]=pos(i,95,360/n/2);
  g+=`<circle cx="${fx}" cy="${fy}" r="17" fill="${COL[s[f].state]}" stroke="#333"/><text x="${fx}" y="${fy+4}" text-anchor="middle" font-size="11">${f}</text>`;}
 for(let i=0;i<n;i++){const p="P"+i,[px,py]=pos(i,185,0);
  g+=`<circle cx="${px}" cy="${py}" r="42" fill="${COL[s[p].state]}"/><text x="${px}" y="${py-2}" text-anchor="middle" fill="#fff" font-weight="bold">${p}</text><text x="${px}" y="${py+14}" text-anchor="middle" fill="#fff" font-size="11">${s[p].state}</text>`;}
 g+="</svg>";const ft=T.actors.filter(a=>a[0]=="F").map(a=>`${a}: ${s[a].state=="held"?"held by "+s[a].detail:"available"}`).join(" | ");
 document.getElementById("view").innerHTML=g+`<p>${ft}</p>`;}
function render(){const s=compute(idx);T.kind=="rw"?renderRW(s):renderDP(s);
 sl.value=idx;document.getElementById("cnt").textContent=idx+" / "+N;
 document.querySelectorAll("#log .cur").forEach(x=>x.classList.remove("cur"));
 if(idx>0){const el=document.getElementById("e"+(idx-1));el.classList.add("cur");el.scrollIntoView({block:"nearest"});}}
function go(i){idx=i;render();}
function stop(){clearInterval(timer);timer=null;}
function play(){stop();if(idx>=N)idx=0;const sp=+document.getElementById("speed").value;
 timer=setInterval(()=>{if(idx>=N){stop();return;}idx++;render();},500/sp);}
document.getElementById("start").onclick=play;document.getElementById("pause").onclick=stop;
document.getElementById("reset").onclick=()=>{stop();go(0);};
document.getElementById("speed").onchange=()=>{if(timer)play();};
sl.oninput=()=>{stop();go(+sl.value);};render();
</script></body></html>"""
