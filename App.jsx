import { useState, useEffect, useRef } from "react";

// ── helpers ────────────────────────────────────────────────────────────────
const uid  = () => Math.random().toString(36).slice(2,8);
const ts   = () => new Date().toLocaleTimeString("en-US",{hour12:false});
const $    = v  => (v>=0?"+":"-")+"$"+Math.abs(v).toFixed(2);
const pct  = v  => (v>=0?"+":"")+v.toFixed(3)+"%";
const sma  = (a,n) => { const s=a.slice(-n); return s.reduce((x,y)=>x+y,0)/(s.length||1); };
const sdev = (a,n) => {
  const s=a.slice(-n),m=s.reduce((x,y)=>x+y,0)/(s.length||1);
  return Math.sqrt(s.reduce((x,y)=>x+(y-m)**2,0)/(s.length||1));
};
const fmtP = (inst,p) => inst==="EUR/USD"?p?.toFixed(4):p?.toFixed(2);

// ── market simulator ───────────────────────────────────────────────────────
const INIT_MKT = {
  "EUR/USD":    {price:1.0850, vol:0.00034, trend:0, hist:Array(50).fill(1.0850)},
  "XAU/USD":    {price:2320.0, vol:0.88,   trend:0, hist:Array(50).fill(2320.0)},
  "ES Futures": {price:5200.0, vol:3.75,   trend:0, hist:Array(50).fill(5200.0)},
};
const tickMkt = prev => {
  const next={};
  for(const [k,v] of Object.entries(prev)){
    const trend = Math.random()<0.025 ? (Math.random()-0.5)*4 : v.trend;
    const chg   = (Math.random()-0.47+trend*0.13)*v.vol;
    const price = Math.max(v.price+chg,0.001);
    next[k]={...v,price,trend,hist:[...v.hist.slice(-99),price]};
  }
  return next;
};

// ── initial agents ─────────────────────────────────────────────────────────
const INIT_AGENTS=[
  {
    id:"momentum",name:"MomentumBot",emoji:"⟶",role:"Trend Follower",color:"#f59e0b",
    instruments:["EUR/USD","ES Futures"],
    cfg:{lookback:15,entryThreshold:1.4,stopLoss:0.45,takeProfit:0.90,sizeUSD:10000,maxPos:2},
    stats:{n:0,wins:0,pnl:0},log:[],gen:1,last:null,
  },
  {
    id:"reversion",name:"ReversionBot",emoji:"⟲",role:"Mean Reverter",color:"#34d399",
    instruments:["XAU/USD"],
    cfg:{lookback:20,entryThreshold:1.7,stopLoss:0.55,takeProfit:0.70,sizeUSD:8000,maxPos:1},
    stats:{n:0,wins:0,pnl:0},log:[],gen:1,last:null,
  },
];
const BALANCE=100000;

// ── component ──────────────────────────────────────────────────────────────
export default function App(){
  const [running,  setRunning] = useState(false);
  const [mkt,      setMkt]     = useState(INIT_MKT);
  const [agents,   setAgents]  = useState(INIT_AGENTS);
  const [positions,setPos]     = useState([]);
  const [history,  setHist]    = useState([]);
  const [julesLog, setJLog]    = useState([]);
  const [thoughtLogs, setTLogs] = useState([]);
  const [portfolio,setPort]    = useState(BALANCE);
  const [tab,      setTab]     = useState("positions");
  const [busy,     setBusy]    = useState({});
  const [prevP,    setPrevP]   = useState({});
  const [tick,     setTick]    = useState(0);

  const mktR  = useRef(INIT_MKT);
  const agR   = useRef(INIT_AGENTS);
  const posR  = useRef([]);
  const histR = useRef([]);
  const tLogsR= useRef([]);
  const portR = useRef(BALANCE);
  const runR  = useRef(false);
  const dIdx  = useRef(0);
  const tickR = useRef(0);

  useEffect(()=>{mktR.current=mkt;},  [mkt]);
  useEffect(()=>{agR.current=agents;}, [agents]);
  useEffect(()=>{posR.current=positions;},[positions]);
  useEffect(()=>{histR.current=history;},[history]);
  useEffect(()=>{tLogsR.current=thoughtLogs;},[thoughtLogs]);
  useEffect(()=>{portR.current=portfolio;},[portfolio]);
  useEffect(()=>{runR.current=running;}, [running]);

  // ── market tick ──────────────────────────────────────────────────────────
  useEffect(()=>{
    if(!running)return;
    const id=setInterval(()=>{
      tickR.current+=1;
      setTick(t=>t+1);

      const prevPrices={};
      for(const [k,v] of Object.entries(mktR.current)) prevPrices[k]=v.price;
      const next=tickMkt(mktR.current);
      mktR.current=next;
      setMkt(next);
      setPrevP({...prevPrices});

      // SL / TP check
      if(!posR.current.length)return;
      const keep=[],close=[];
      for(const pos of posR.current){
        const p=next[pos.instrument]?.price;
        if(!p){keep.push(pos);continue;}
        const pp=pos.dir==="long"
          ?(p-pos.entry)/pos.entry*100
          :(pos.entry-p)/pos.entry*100;
        if(pp<=-pos.sl) close.push({...pos,exit:p,exitPnl:pp/100*pos.size,why:"Stop Loss",   t2:ts()});
        else if(pp>=pos.tp) close.push({...pos,exit:p,exitPnl:pp/100*pos.size,why:"Take Profit",t2:ts()});
        else keep.push({...pos,cur:p,pnl:pp/100*pos.size,pnlPct:pp});
      }
      posR.current=keep;
      setPos([...keep]);
      if(close.length){
        const h=[...histR.current,...close];
        histR.current=h;
        setHist(h);
        const gain=close.reduce((s,c)=>s+c.exitPnl,0);
        portR.current+=gain;
        setPort(portR.current);
        setAgents(prev=>prev.map(a=>{
          const mine=close.filter(c=>c.agId===a.id);
          if(!mine.length)return a;
          return{...a,stats:{n:a.stats.n+mine.length,wins:a.stats.wins+mine.filter(c=>c.exitPnl>0).length,pnl:a.stats.pnl+mine.reduce((s,c)=>s+c.exitPnl,0)}};
        }));
      }
    },1000);
    return()=>clearInterval(id);
  },[running]);

  // ── agent decision loop ──────────────────────────────────────────────────
  useEffect(()=>{
    if(!running)return;
    const t1=setTimeout(()=>decide(agR.current[0]),800);
    const t2=setTimeout(()=>decide(agR.current[1]),3500);
    const id=setInterval(()=>{
      const i=dIdx.current%2;
      dIdx.current++;
      decide(agR.current[i]);
    },24000);
    return()=>{clearTimeout(t1);clearTimeout(t2);clearInterval(id);};
  },[running]); // eslint-disable-line

  // ── jules improvement trigger ────────────────────────────────────────────
  useEffect(()=>{
    const n=histR.current.length;
    if(n>0&&n%10===0) jules();
  },[history.length]); // eslint-disable-line

  // ── decide (agent API call) ──────────────────────────────────────────────
  const decide=async(agent)=>{
    if(!agent||!runR.current)return;
    setBusy(b=>({...b,[agent.id]:true}));
    const m=mktR.current;
    const myPos=posR.current.filter(p=>p.agId===agent.id);
    const mdata=agent.instruments.map(inst=>{
      const h=m[inst]?.hist||[];
      const price=m[inst]?.price||0;
      return{inst,price:+price.toFixed(5),ma20:+sma(h,20).toFixed(5),std15:+sdev(h,15).toFixed(6),chg10:h.length>=10?+((price-h[h.length-10])/h[h.length-10]*100).toFixed(3):0};
    });
    const isMom=agent.id==="momentum";
    const sys=isMom
      ?`You are MomentumBot, a trend-following agent. Trade EUR/USD and ES Futures. Go long on strong uptrend (chg10 > ${(agent.cfg.entryThreshold*0.2).toFixed(2)}%), short on strong downtrend (chg10 < -${(agent.cfg.entryThreshold*0.2).toFixed(2)}%). Max ${agent.cfg.maxPos} positions. SL=${agent.cfg.stopLoss}% TP=${agent.cfg.takeProfit}%.
Stats: ${agent.stats.n} trades, WR:${agent.stats.n>0?(agent.stats.wins/agent.stats.n*100).toFixed(0):0}%, PnL:$${agent.stats.pnl.toFixed(0)}
Reply ONLY valid JSON: {"action":"buy"|"sell"|"close"|"wait","instrument":"EUR/USD"|"ES Futures"|null,"posId":null,"reason":"≤10 words"}`
      :`You are ReversionBot, a mean-reversion agent. Trade XAU/USD only. Buy when price far BELOW ma20 (deviation/${agent.cfg.entryThreshold} std), sell when far ABOVE. Max ${agent.cfg.maxPos} positions. SL=${agent.cfg.stopLoss}% TP=${agent.cfg.takeProfit}%.
Stats: ${agent.stats.n} trades, WR:${agent.stats.n>0?(agent.stats.wins/agent.stats.n*100).toFixed(0):0}%, PnL:$${agent.stats.pnl.toFixed(0)}
Reply ONLY valid JSON: {"action":"buy"|"sell"|"close"|"wait","instrument":"XAU/USD"|null,"posId":null,"reason":"≤10 words"}`;
    const addTLog = (msg) => {
      const entry = { id: uid(), t: ts(), agId: agent.id, agName: agent.name, color: agent.color, msg };
      const nxt = [entry, ...tLogsR.current].slice(0, 100);
      tLogsR.current = nxt;
      setTLogs(nxt);
    };

    addTLog(`Analyzing market... EUR/USD:${mdata.find(d=>d.inst==="EUR/USD")?.price||"—"} XAU/USD:${mdata.find(d=>d.inst==="XAU/USD")?.price||"—"}`);

    try{
      const res=await fetch("https://api.anthropic.com/v1/messages",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          model:"claude-sonnet-4-20250514",max_tokens:120,system:sys,
          messages:[{role:"user",content:`Market:${JSON.stringify(mdata)}\nMy positions:${JSON.stringify(myPos.map(p=>({id:p.id,inst:p.instrument,dir:p.dir,entry:p.entry,pnlPct:p.pnlPct?.toFixed(2)})))}`}],
        }),
      });
      const d=await res.json();
      const raw=d.content?.[0]?.text||'{"action":"wait"}';
      const dec=JSON.parse(raw.replace(/```json?|```/g,"").trim());

      let logMsg = `Decided to ${dec.action.toUpperCase()}`;
      if(dec.instrument) logMsg += ` on ${dec.instrument}`;
      if(dec.reason) logMsg += `. Reason: ${dec.reason}`;
      addTLog(logMsg);

      if((dec.action==="buy"||dec.action==="sell")&&dec.instrument&&agent.instruments.includes(dec.instrument)&&myPos.length<agent.cfg.maxPos){
        const price=m[dec.instrument]?.price||0;
        const pos={
          id:uid(),agId:agent.id,agName:agent.name,agEmoji:agent.emoji,agColor:agent.color,
          instrument:dec.instrument,dir:dec.action==="buy"?"long":"short",
          entry:price,cur:price,size:agent.cfg.sizeUSD,sl:agent.cfg.stopLoss,tp:agent.cfg.takeProfit,
          pnl:0,pnlPct:0,t1:ts(),reason:dec.reason,
        };

        let riskPassed = true;
        let riskReason = "";

        if (!pos.sl || pos.sl <= 0) {
          riskPassed = false;
          riskReason = "Stop Loss required";
        } else if (pos.size > 50000) {
          riskPassed = false;
          riskReason = "Position exceeds maximum size";
        } else if (portR.current < BALANCE * 0.99) {
          riskPassed = false;
          riskReason = "Exceeds Max Daily Risk (1%)";
        }

        if (riskPassed) {
          const rmLog = { id: uid(), t: ts(), agId: "risk", agName: "Risk Manager", color: "#f87171", msg: "[Risk Manager]: Trade approved." };
          tLogsR.current = [rmLog, ...tLogsR.current].slice(0, 100);
          setTLogs(tLogsR.current);

          const nxt=[...posR.current,pos];
          posR.current=nxt;setPos(nxt);
        } else {
          const rmLog = { id: uid(), t: ts(), agId: "risk", agName: "Risk Manager", color: "#f87171", msg: `[Risk Manager REJECTED]: Position exceeds maximum risk parameters (${riskReason}).` };
          tLogsR.current = [rmLog, ...tLogsR.current].slice(0, 100);
          setTLogs(tLogsR.current);
        }
      }else if(dec.action==="close"&&dec.posId){
        const pos=posR.current.find(p=>p.id===dec.posId&&p.agId===agent.id);
        if(pos){
          const price=m[pos.instrument]?.price||pos.entry;
          const pp=pos.dir==="long"?(price-pos.entry)/pos.entry*100:(pos.entry-price)/pos.entry*100;
          const exitPnl=pp/100*pos.size;
          const closed={...pos,exit:price,exitPnl,why:"Agent Close",t2:ts()};
          const nxt=posR.current.filter(p=>p.id!==pos.id);
          posR.current=nxt;setPos(nxt);
          const h=[...histR.current,closed];histR.current=h;setHist(h);
          portR.current+=exitPnl;setPort(portR.current);
          setAgents(prev=>prev.map(a=>a.id!==agent.id?a:{...a,stats:{n:a.stats.n+1,wins:a.stats.wins+(exitPnl>0?1:0),pnl:a.stats.pnl+exitPnl}}));
        }
      }
      const entry={t:ts(),action:dec.action,inst:dec.instrument,reason:dec.reason};
      setAgents(prev=>prev.map(a=>a.id!==agent.id?a:{...a,log:[entry,...a.log.slice(0,5)],last:entry}));
    }catch(e){console.error("decide",e);}
    setBusy(b=>({...b,[agent.id]:false}));
  };

  // ── jules improvement ────────────────────────────────────────────────────
  const jules=async()=>{
    if(busy.jules)return;
    setBusy(b=>({...b,jules:true}));
    const trades=histR.current.slice(-20);
    const summary=agR.current.map(a=>({
      id:a.id,cfg:a.cfg,n:a.stats.n,
      wr:a.stats.n>0?+(a.stats.wins/a.stats.n*100).toFixed(1):null,
      pnl:+a.stats.pnl.toFixed(2),gen:a.gen,
    }));
    try{
      const res=await fetch("https://api.anthropic.com/v1/messages",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          model:"claude-sonnet-4-20250514",max_tokens:350,
          system:`You are Jules, a meta-optimizer AI. Improve trading agent configs based on performance. Focus on the weaker agent. Change 1-3 params.
Params: lookback(5-50 int), entryThreshold(0.5-3.0 float), stopLoss(0.2-2.0 float), takeProfit(0.3-3.0 float), sizeUSD(3000-20000 int).
Reply ONLY JSON: {"agentId":"momentum"|"reversion","changes":{},"reasoning":"≤25 words","expected":"≤12 words"}`,
          messages:[{role:"user",content:`Agents:${JSON.stringify(summary)}\nTrades(last20):${JSON.stringify(trades.map(t=>({ag:t.agId,inst:t.instrument,dir:t.dir,pnl:+t.exitPnl?.toFixed(2),why:t.why})))}`}],
        }),
      });
      const d=await res.json();
      const raw=d.content?.[0]?.text||"";
      const imp=JSON.parse(raw.replace(/```json?|```/g,"").trim());
      setAgents(prev=>prev.map(a=>a.id!==imp.agentId?a:{...a,cfg:{...a.cfg,...imp.changes},gen:a.gen+1}));
      setJLog(prev=>[{t:ts(),agentId:imp.agentId,changes:imp.changes,reasoning:imp.reasoning,expected:imp.expected,n:histR.current.length},...prev]);
    }catch(e){console.error("jules",e);}
    setBusy(b=>({...b,jules:false}));
  };

  // ── derived ──────────────────────────────────────────────────────────────
  const realized=portfolio-BALANCE;
  const openPnl=positions.reduce((s,p)=>s+(p.pnl||0),0);

  const priceColor=inst=>{
    const c=mkt[inst]?.price,p=prevP[inst];
    if(!p||c===p)return"#6b7280";
    return c>p?"#22c55e":"#ef4444";
  };

  // ── render ───────────────────────────────────────────────────────────────
  return(
    <div style={{background:"#060a10",minHeight:"100vh",color:"#c9d1d9",fontFamily:"'Courier New',Courier,monospace",padding:"12px 14px",fontSize:12}}>

      <style>{`
        @keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
        @keyframes scanline{0%{transform:translateY(-100%)}100%{transform:translateY(100vh)}}
        @keyframes fadein{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
        .row-in{animation:fadein .25s ease forwards}
        .blink{animation:blink 1s step-start infinite}
        ::-webkit-scrollbar{width:4px}
        ::-webkit-scrollbar-track{background:#0a0f18}
        ::-webkit-scrollbar-thumb{background:#1e2d40;border-radius:2px}
        button:hover{filter:brightness(1.2)}
        button:active{filter:brightness(0.9)}
      `}</style>

      {/* scanline overlay */}
      <div style={{position:"fixed",inset:0,pointerEvents:"none",background:"repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.06) 2px,rgba(0,0,0,.06) 4px)",zIndex:9999}}/>

      {/* ── HEADER ── */}
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",borderBottom:"1px solid #1a2535",paddingBottom:10,marginBottom:10}}>
        <div>
          <div style={{fontSize:15,fontWeight:"bold",letterSpacing:3,color:"#f0b429",marginBottom:2}}>
            ◈ MULTI-AGENT TRADING SYSTEM
          </div>
          <div style={{fontSize:9,color:"#3d5166",letterSpacing:2}}>
            FUTURES · FOREX · {running?<span style={{color:"#22c55e"}}>● LIVE</span>:<span style={{color:"#ef4444"}}>■ STOPPED</span>} · TICK #{tick}
          </div>
        </div>
        <div style={{display:"flex",gap:18,alignItems:"flex-end"}}>
          <div>
            <div style={{fontSize:8,color:"#3d5166",letterSpacing:2}}>EQUITY</div>
            <div style={{fontSize:20,fontWeight:"bold",color:"#f0b429",letterSpacing:1}}>${portfolio.toLocaleString("en",{minimumFractionDigits:2,maximumFractionDigits:2})}</div>
          </div>
          <div>
            <div style={{fontSize:8,color:"#3d5166",letterSpacing:2}}>REALIZED</div>
            <div style={{fontSize:15,fontWeight:"bold",color:realized>=0?"#22c55e":"#ef4444"}}>{$(realized)}</div>
          </div>
          <div>
            <div style={{fontSize:8,color:"#3d5166",letterSpacing:2}}>FLOATING</div>
            <div style={{fontSize:13,color:openPnl>=0?"#4ade80":"#f87171"}}>{$(openPnl)}</div>
          </div>
          <button onClick={()=>setRunning(r=>!r)} style={{padding:"7px 16px",background:running?"#3b1219":"#0f2d1a",color:running?"#fca5a5":"#86efac",border:`1px solid ${running?"#7f1d1d":"#14532d"}`,borderRadius:3,cursor:"pointer",fontWeight:"bold",fontSize:11,fontFamily:"monospace",letterSpacing:2}}>
            {running?"■ STOP":"▶ START"}
          </button>
        </div>
      </div>

      {/* ── PRICE TICKER ── */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:6,marginBottom:10}}>
        {Object.entries(mkt).map(([inst,v])=>{
          const p=prevP[inst];
          const chg=p?(v.price-p):0;
          const col=priceColor(inst);
          const myPos=positions.filter(pos=>pos.instrument===inst);
          return(
            <div key={inst} style={{background:"#0a0f18",border:"1px solid #1a2535",borderRadius:4,padding:"8px 10px",position:"relative",overflow:"hidden"}}>
              <div style={{position:"absolute",top:0,left:0,right:0,height:2,background:col==="#22c55e"?"#22c55e22":col==="#ef4444"?"#ef444422":"transparent"}}/>
              <div style={{fontSize:8,color:"#3d5166",letterSpacing:2,marginBottom:1}}>{inst}</div>
              <div style={{fontSize:22,fontWeight:"bold",color:col,fontFamily:"monospace",letterSpacing:1}}>{fmtP(inst,v.price)}</div>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginTop:2}}>
                <div style={{fontSize:9,color:chg>=0?"#22c55e":"#ef4444"}}>{chg>=0?"▲":"▼"} {Math.abs(chg).toFixed(inst==="EUR/USD"?5:2)}</div>
                {myPos.length>0&&<div style={{fontSize:8,color:"#f0b429"}}>{myPos.length} pos</div>}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── AGENT CARDS ── */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6,marginBottom:10}}>
        {agents.map(ag=>{
          const wr=ag.stats.n>0?(ag.stats.wins/ag.stats.n*100).toFixed(0)+"%":"—";
          const myPos=positions.filter(p=>p.agId===ag.id);
          return(
            <div key={ag.id} style={{background:"#0a0f18",border:`1px solid ${ag.color}33`,borderRadius:4,padding:"9px 10px"}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:6}}>
                <div>
                  <div style={{fontWeight:"bold",fontSize:13,color:ag.color,letterSpacing:1}}>{ag.emoji} {ag.name}</div>
                  <div style={{fontSize:8,color:"#3d5166",letterSpacing:1}}>{ag.role.toUpperCase()} · GEN {ag.gen}</div>
                </div>
                <div style={{display:"flex",gap:4,alignItems:"center"}}>
                  {busy[ag.id]&&<span className="blink" style={{fontSize:8,color:"#f0b429"}}>THINKING</span>}
                  {myPos.length>0&&<span style={{fontSize:8,color:ag.color}}>● {myPos.length}</span>}
                  <button onClick={()=>decide(ag)} disabled={busy[ag.id]} style={{fontSize:8,padding:"2px 5px",background:"#111827",color:"#6b7280",border:"1px solid #1e293b",borderRadius:2,cursor:"pointer",fontFamily:"monospace"}}>RUN</button>
                </div>
              </div>

              <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:3,marginBottom:6}}>
                {[["N",ag.stats.n],["WIN",wr],["PNL",$(ag.stats.pnl)],["SIZE","$"+ag.cfg.sizeUSD.toLocaleString()]].map(([l,val])=>(
                  <div key={l} style={{background:"#060a10",borderRadius:3,padding:"3px 4px"}}>
                    <div style={{fontSize:7,color:"#3d5166",letterSpacing:1}}>{l}</div>
                    <div style={{fontSize:10,fontWeight:"bold",color:l==="PNL"?(ag.stats.pnl>=0?"#22c55e":"#ef4444"):l==="WIN"?"#f0b429":"#94a3b8"}}>{val}</div>
                  </div>
                ))}
              </div>

              <div style={{fontSize:8,color:"#3d5166",marginBottom:4,letterSpacing:1}}>
                SL:{ag.cfg.stopLoss}% · TP:{ag.cfg.takeProfit}% · THRESHOLD:{ag.cfg.entryThreshold} · LB:{ag.cfg.lookback}
              </div>

              {ag.last&&(
                <div style={{background:"#060a10",borderRadius:3,padding:"3px 6px",fontSize:8,borderLeft:`2px solid ${ag.last.action==="buy"?"#22c55e":ag.last.action==="sell"?"#ef4444":ag.last.action==="close"?"#f59e0b":"#3d5166"}`}}>
                  <span style={{color:"#3d5166"}}>{ag.last.t} </span>
                  <span style={{fontWeight:"bold",color:ag.last.action==="buy"?"#22c55e":ag.last.action==="sell"?"#ef4444":ag.last.action==="close"?"#f59e0b":"#4b5563"}}>{ag.last.action?.toUpperCase()} </span>
                  {ag.last.inst&&<span style={{color:"#94a3b8"}}>{ag.last.inst} · </span>}
                  <span style={{color:"#4b5563"}}>{ag.last.reason}</span>
                </div>
              )}

              {ag.log.length>1&&(
                <div style={{marginTop:4}}>
                  {ag.log.slice(1,3).map((l,i)=>(
                    <div key={i} style={{fontSize:8,color:"#2d3d50",padding:"1px 0"}}>{l.t} {l.action?.toUpperCase()} {l.inst||""} {l.reason}</div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── JULES META-AGENT ── */}
      <div style={{background:"#0a0f18",border:"1px solid #4c1d9533",borderRadius:4,padding:"8px 10px",marginBottom:10}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div>
            <span style={{fontWeight:"bold",color:"#a78bfa",fontSize:12,letterSpacing:1}}>✦ JULES</span>
            <span style={{fontSize:8,color:"#3d5166",marginLeft:6,letterSpacing:1}}>META-OPTIMIZER · SELF-IMPROVES AGENTS EVERY 10 TRADES</span>
          </div>
          <div style={{display:"flex",gap:6,alignItems:"center"}}>
            {busy.jules&&<span className="blink" style={{fontSize:8,color:"#a78bfa"}}>ANALYZING</span>}
            <span style={{fontSize:8,color:"#3d5166"}}>{history.length<10?`${10-history.length} trades until next →`:`Last after trade #${julesLog[0]?.n||"—"}`}</span>
            <button onClick={jules} disabled={busy.jules||history.length<2} style={{fontSize:8,padding:"2px 7px",background:"#1e1b4b",color:"#818cf8",border:"1px solid #312e81",borderRadius:2,cursor:"pointer",fontFamily:"monospace",letterSpacing:1}}>⚡ RUN JULES</button>
          </div>
        </div>
        {julesLog[0]&&(
          <div className="row-in" style={{marginTop:6,background:"#060a10",borderRadius:3,padding:"5px 8px",borderLeft:"2px solid #7c3aed",fontSize:9}}>
            <span style={{color:"#a78bfa",fontWeight:"bold"}}>Jules → {julesLog[0].agentId==="momentum"?"⟶ MomentumBot":"⟲ ReversionBot"} </span>
            <span style={{color:"#3d5166"}}>after #{julesLog[0].n} · {julesLog[0].t} · </span>
            <span style={{color:"#94a3b8"}}>{julesLog[0].reasoning} </span>
            <span style={{color:"#3d5166"}}>→ expected: {julesLog[0].expected}</span>
            <div style={{marginTop:3,display:"flex",gap:3,flexWrap:"wrap"}}>
              {Object.entries(julesLog[0].changes).map(([k,v])=>(
                <span key={k} style={{fontSize:8,padding:"1px 5px",background:"#1e1b4b",color:"#818cf8",borderRadius:2,letterSpacing:1}}>{k}:{v}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── TABS ── */}
      <div style={{display:"flex",gap:0,borderBottom:"1px solid #1a2535",marginBottom:6}}>
        {[["positions",`POSITIONS (${positions.length})`],["history",`HISTORY (${history.length})`],["juleslog",`JULES LOG (${julesLog.length})`],["thoughtlogs",`THOUGHT LOGS`]].map(([id,label])=>(
          <button key={id} onClick={()=>setTab(id)} style={{padding:"5px 14px",background:tab===id?"#0e1a2a":"transparent",color:tab===id?"#f0b429":"#3d5166",border:"none",borderBottom:tab===id?"2px solid #f0b429":"2px solid transparent",cursor:"pointer",fontSize:9,fontFamily:"monospace",letterSpacing:2}}>
            {label}
          </button>
        ))}
      </div>

      {/* ── TAB CONTENT ── */}
      <div style={{background:"#0a0f18",border:"1px solid #1a2535",borderRadius:4,padding:8,minHeight:170}}>

        {tab==="positions"&&(
          positions.length===0
            ?<div style={{color:"#2d3d50",textAlign:"center",paddingTop:55,fontSize:11,letterSpacing:1}}>{running?"AGENTS ANALYZING MARKETS...":"PRESS START TO BEGIN"}</div>
            :positions.map(p=>(
              <div key={p.id} className="row-in" style={{display:"flex",justifyContent:"space-between",alignItems:"center",background:"#060a10",borderRadius:3,padding:"6px 8px",marginBottom:4,borderLeft:`3px solid ${p.dir==="long"?"#22c55e":"#ef4444"}`}}>
                <div>
                  <div style={{fontWeight:"bold",fontSize:11}}><span style={{color:p.agColor}}>{p.agEmoji}</span> {p.instrument} <span style={{color:p.dir==="long"?"#22c55e":"#ef4444",fontSize:9}}>{p.dir.toUpperCase()}</span></div>
                  <div style={{fontSize:8,color:"#3d5166"}}>{p.agName} · ENTRY {fmtP(p.instrument,p.entry)} · {p.t1}</div>
                  <div style={{fontSize:8,color:"#2d3d50",marginTop:1}}>{p.reason}</div>
                </div>
                <div style={{textAlign:"right"}}>
                  <div style={{fontSize:14,fontWeight:"bold",color:p.pnl>=0?"#22c55e":"#ef4444"}}>{$(p.pnl)}</div>
                  <div style={{fontSize:8,color:"#3d5166"}}>{pct(p.pnlPct||0)}</div>
                  <div style={{fontSize:8,color:"#2d3d50"}}>SL {p.sl}% · TP {p.tp}%</div>
                </div>
              </div>
            ))
        )}

        {tab==="history"&&(
          history.length===0
            ?<div style={{color:"#2d3d50",textAlign:"center",paddingTop:55,fontSize:11,letterSpacing:1}}>NO CLOSED TRADES YET</div>
            :[...history].reverse().slice(0,40).map((t,i)=>(
              <div key={i} className="row-in" style={{display:"flex",justifyContent:"space-between",background:"#060a10",borderRadius:3,padding:"4px 8px",marginBottom:3}}>
                <div>
                  <span style={{fontWeight:"bold",fontSize:10}}>{t.instrument}</span>
                  <span style={{fontSize:8,color:"#3d5166",marginLeft:5}}>{t.dir?.toUpperCase()} · {t.why}</span>
                  <div style={{fontSize:8,color:"#2d3d50"}}>{t.agName} · {t.t1}→{t.t2}</div>
                </div>
                <div style={{textAlign:"right"}}>
                  <div style={{fontWeight:"bold",fontSize:11,color:t.exitPnl>=0?"#22c55e":"#ef4444"}}>{$(t.exitPnl)}</div>
                  <div style={{fontSize:8,color:"#3d5166"}}>{fmtP(t.instrument,t.entry)} → {fmtP(t.instrument,t.exit)}</div>
                </div>
              </div>
            ))
        )}

        {tab==="juleslog"&&(
          julesLog.length===0
            ?<div style={{color:"#2d3d50",textAlign:"center",paddingTop:45,fontSize:11,letterSpacing:1}}>JULES MONITORING... FIRST IMPROVEMENT AFTER 10 TRADES<br/><span style={{fontSize:9,marginTop:4,display:"block"}}>OR PRESS "RUN JULES" AFTER 2+ TRADES</span></div>
            :julesLog.map((j,i)=>(
              <div key={i} className="row-in" style={{background:"#060a10",borderRadius:3,padding:"7px 8px",marginBottom:5,borderLeft:"2px solid #7c3aed"}}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                  <div style={{fontWeight:"bold",color:"#a78bfa",fontSize:10,letterSpacing:1}}>
                    Jules → {j.agentId==="momentum"?"⟶ MomentumBot":"⟲ ReversionBot"} (Gen {(agR.current.find(a=>a.id===j.agentId)?.gen)||"?"})
                  </div>
                  <div style={{fontSize:8,color:"#3d5166"}}>trade #{j.n} · {j.t}</div>
                </div>
                <div style={{fontSize:9,color:"#94a3b8",marginBottom:2}}>{j.reasoning}</div>
                <div style={{fontSize:8,color:"#3d5166",marginBottom:4}}>Expected → {j.expected}</div>
                <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>
                  {Object.entries(j.changes).map(([k,v])=>(
                    <span key={k} style={{fontSize:8,padding:"1px 6px",background:"#1e1b4b",color:"#818cf8",borderRadius:2,letterSpacing:1}}>{k}: {v}</span>
                  ))}
                </div>
              </div>
            ))
        )}

        {tab==="thoughtlogs"&&(
          <div style={{height:154,overflowY:"auto",paddingRight:4,display:"flex",flexDirection:"column-reverse"}}>
            {thoughtLogs.length===0
              ?<div style={{color:"#2d3d50",textAlign:"center",paddingTop:55,fontSize:11,letterSpacing:1}}>WAITING FOR AGENT THOUGHTS...</div>
              :thoughtLogs.map(l=>(
                <div key={l.id} className="row-in" style={{fontFamily:"monospace",fontSize:10,marginBottom:4,lineHeight:1.4}}>
                  <span style={{color:"#3d5166"}}>[{l.t}] </span>
                  <span style={{color:l.color,fontWeight:"bold"}}>{l.agName}: </span>
                  <span style={{color:"#c9d1d9"}}>{l.msg}</span>
                </div>
              ))
            }
          </div>
        )}
      </div>

      <div style={{marginTop:8,fontSize:8,color:"#1e2d3d",textAlign:"center",letterSpacing:1}}>
        SIMULATION · NOT FINANCIAL ADVICE · AGENTS POWERED BY CLAUDE SONNET · AUTO-IMPROVE EVERY 10 TRADES
      </div>
    </div>
  );
}