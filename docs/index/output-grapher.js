(function(){
  const SUP='⁰¹²³⁴⁵⁶⁷⁸⁹';
  const SUB='₀₁₂₃₄₅₆₇₈₉';
  const supToInt=Object.fromEntries([...SUP].map((c,i)=>[c,String(i)]));
  const subToInt=Object.fromEntries([...SUB].map((c,i)=>[c,String(i)]));
  const intToSup=Object.fromEntries([...SUP].map((c,i)=>[String(i),c]));
  const intToSub=Object.fromEntries([...SUB].map((c,i)=>[String(i),c]));
  let currentModel=null;
  let currentGraphMode='rebuttal';
  let currentDensity='comfortable';

  function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function cleanParsed(s){return String(s??'').replace(/[╔╗╚╝║═]/g,'').replace(/\s+/g,' ').trim();}
  function supNum(raw){return [...String(raw||'')].map(c=>supToInt[c]||'').join('')||'0';}
  function subNum(raw){return [...String(raw||'')].map(c=>subToInt[c]||'').join('')||'0';}
  function burden(n){return [...String(n)].map(c=>intToSup[c]||'').join('')+'B';}
  function submove(b,s){return burden(b)+[...String(s)].map(c=>intToSub[c]||'').join('');}
  function addNode(model,node){if(!model.nodes[node.id]) model.nodes[node.id]=node;}
  function addEdge(model,edge){if(!model.edges.some(e=>e.source===edge.source&&e.target===edge.target&&e.kind===edge.kind)) model.edges.push(edge);}
  function normalizeBurden(raw){const s=String(raw||'').trim(); if(/^[⁰¹²³⁴⁵⁶⁷⁸⁹]+B$/.test(s)) return s; const m=s.match(/^B(\d+)$/); return m?burden(m[1]):s;}
  function warnLegacy(model,lineNo,alias,canonical){if(!model.legacyAliases.includes(alias)){model.legacyAliases.push(alias); model.warnings.push(`line ${lineNo}: parsed legacy alias ${alias}; public canonical notation preferred: ${canonical}`);}}
  function tailSummary(line,end){return String(line).slice(end).replace(/^\s*(?:[-–—]|:)\s*/,'').replace(/\s+/g,' ').trim();}
  function afterColon(line){const i=String(line).indexOf(':'); return i>=0?String(line).slice(i+1).replace(/\s+/g,' ').trim():'';}

  function blankModel(){
    return {nodes:{},edges:[],errors:[],warnings:[],initialBurdens:[],burdens:[],submoves:{},terminals:{},mrp:{},graphEdges:[],generatedBurdens:{},closureComplete:false,hasLayerA:false,hasBanner:false,hasRestoration:false,legacyAliases:[],witnessMismatches:[],inputDigest:'pasted daee-epistemics output',fieldType:'not detected',caseProfile:'not detected',claimType:'not detected',diagnosis:'not detected',held:'not detected',collapse:{},restorationAim:'not detected',restorativeResponse:'',closingFormulation:''};
  }

  function lineBurdens(line,model,lineNo){
    const found=[];
    for(const m of line.matchAll(/([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B(?![₀₁₂₃₄₅₆₇₈₉])/g)){ if(!found.includes(m[0])) found.push(m[0]); }
    for(const m of line.matchAll(/\bB(\d+)\b/g)){
      const t=burden(m[1]); if(!found.includes(t)) found.push(t);
      model.legacyAliases.push(m[0]); model.warnings.push(`line ${lineNo}: parsed legacy alias ${m[0]}; public canonical notation preferred`);
    }
    for(const m of line.matchAll(/\bB([₀₁₂₃₄₅₆₇₈₉]+)\b/g)){
      model.warnings.push(`line ${lineNo}: ${m[0]} looks like subscript burden notation; use superscript-before-B for burdens`);
    }
    return found;
  }

  function ensureMrp(model,b,lineNo){
    const id=`MRP(${b})`;
    if(!model.mrp[b]) model.mrp[b]={id,line:lineNo,routes:[],resultTypes:[],edges:[],pressure:[]};
    addNode(model,{id,kind:'mrp',label:id,line:lineNo,excerpt:''});
    return model.mrp[b];
  }
  function refreshMrpLabel(model,b){
    const data=model.mrp[b]||{}, node=model.nodes[`MRP(${b})`];
    if(!node) return;
    const type=(data.resultTypes||[])[0] || (data.pressure||[]).find(x=>/genuine|partial|stable|churn|held/i.test(x)) || 'reread pressure';
    node.label=`MRP(${b}) — ${String(type).replace(/^Finding:\s*/i,'').slice(0,70)}`;
    node.status=String(type);
  }
  function recordDependency(model,s,t,lineNo,excerpt,currentMrpBurden){
    if(!model.graphEdges.some(e=>e[0]===s&&e[1]===t)) model.graphEdges.push([s,t,lineNo,excerpt]);
    addNode(model,{id:s,kind:'burden',label:s,line:lineNo,excerpt:''}); addNode(model,{id:t,kind:'burden',label:t,line:lineNo,excerpt:''});
    addEdge(model,{source:s,target:t,kind:'dependency',line:lineNo,excerpt});
    if(currentMrpBurden){const m=ensureMrp(model,currentMrpBurden,lineNo); if(!m.edges.some(e=>e[0]===s&&e[1]===t)) m.edges.push([s,t]);}
  }

  function parseOutput(text,witnessText){
    const model=blankModel();
    addNode(model,{id:'input',kind:'input',label:'input',line:0,excerpt:'pasted daee-epistemics output'});
    const sourceText=String(text||'');
    const restorativeMatch=sourceText.match(/Restorative Response\s*\n+([\s\S]*?)(?:\n\s*Closing Formulation\b|$)/i);
    if(restorativeMatch) model.restorativeResponse=cleanParsed(restorativeMatch[1]).slice(0,900);
    const closingMatch=sourceText.match(/Closing Formulation\s*\n+([\s\S]+)$/i);
    if(closingMatch) model.closingFormulation=cleanParsed(closingMatch[1]).slice(0,900);
    const lines=sourceText.split(/\r?\n/);
    let lastBurden='', currentMrpBurden='', pendingMrpBlock=false;
    const routeRecords=[];
    lines.forEach((line,idx)=>{
      const lineNo=idx+1, trimmed=line.trim();
      if(!trimmed) return;
      if(line.includes('NOETIC FIELD EXECUTION') || /governed execution/i.test(line)) model.hasBanner=true;
      if(line.includes('Layer A') || (/DSL/.test(line)&&/IR/.test(line))) model.hasLayerA=true;
      if(/coverage_complete\s*[:=]\s*true/i.test(line)) model.closureComplete=true;
      if(/restoration|T_lang|Ψᴺ ⇢ Ψᴵ/i.test(line)) model.hasRestoration=true;
      const field=line.match(/\bfield:\s*([^|]+)$/i); if(field) model.fieldType=cleanParsed(field[1]);
      const userTask=line.match(/\buser task:\s*(.+)$/i); if(userTask) model.userTask=cleanParsed(userTask[1]);
      const authority=line.match(/\bauthority frame:\s*(.+)$/i); if(authority) model.authorityFrame=cleanParsed(authority[1]);
      const state=line.match(/\bstate:\s*(.+)$/i); if(state) model.runtimeState=cleanParsed(state[1]);
      const readStatus=line.match(/^\s*-\s*read status:\s*(.+)$/i); if(readStatus&&model.inputDigest==='pasted daee-epistemics output'){model.inputDigest=cleanParsed(readStatus[1]); model.diagnosis=cleanParsed(readStatus[1]);}
      const claim=line.match(/^\s*-\s*claim_level:\s*(.+)$/i); if(claim&&model.claimType==='not detected') model.claimType=cleanParsed(claim[1]);
      const pattern=line.match(/^\s*-\s*pattern_profile:\s*(.+)$/i); if(pattern&&!model.patternProfile) model.patternProfile=cleanParsed(pattern[1]);
      const layerCase=line.match(/\bCase:\s*(.*?)\s+Claim:\s*(.*?)\s+Pattern:\s*(.*?)(?:\s+NS:|\s+DO-orient:|$)/i);
      if(layerCase){
        model.caseProfile=cleanParsed(layerCase[1]);
        if(model.claimType==='not detected') model.claimType=cleanParsed(layerCase[2]);
        if(!model.patternProfile) model.patternProfile=cleanParsed(layerCase[3]);
      }
      const held=line.match(/^\s*-\s*held:\s*(.+)$/i); if(held) model.held=cleanParsed(held[1]);
      const live=line.match(/^\s*-\s*live noetic burden:\s*(.+)$/i); if(live) model.liveBurden=cleanParsed(live[1]);
      const div=line.match(/∇·B\s*:\s*([^;\n]+)/i); if(div) model.collapse.divergence=div[1].trim();
      const curl=line.match(/∇×κ\s*:\s*([^;\n]+)/i); if(curl) model.collapse.curl=curl[1].trim();
      const closure=line.match(/𝒞\(Ψᴺ\)\s*:\s*([^;\n]+)/i); if(closure) model.collapse.coverage=closure[1].trim();
      const tLang=line.match(/T_lang\s*:\s*([^\n]+)/i); if(tLang) model.collapse.tLang=tLang[1].trim();
      const restAim=line.match(/Restoration (?:aim|target):\s*(.+)$/i); if(restAim){model.restorationAim=cleanParsed(restAim[1]); model.hasRestoration=true;}
      const burdens=lineBurdens(line,model,lineNo);
      const headingMatch=trimmed.match(/^(?:#+\s*)?Burden\s+(\d+)\b/i);
      const headingBurden=headingMatch?burden(headingMatch[1]):'';
      if(headingMatch){burdens.splice(0,burdens.length,headingBurden,...burdens.filter(b=>b!==headingBurden));}
      const initial=/initial burden|burden inventory|initial set|held\/live burden/i.test(line);
      const heading=/^(#+\s*)?(Burden\s+\d+\b|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\b)/.test(trimmed);
      burdens.forEach(b=>{
        if(!model.burdens.includes(b)) model.burdens.push(b);
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:trimmed.slice(0,220)});
        if(initial&&!model.initialBurdens.includes(b)) model.initialBurdens.push(b);
        if(heading&&b===headingBurden){
          lastBurden=b;
          const title=tailSummary(trimmed, headingMatch?headingMatch[0].length:0);
          if(title && model.nodes[b]) model.nodes[b].label=`${b} — ${title.replace(/\s*\[generated-by:.+?\]\s*/i,'').slice(0,120)}`;
        }
      });
      for(const m of line.matchAll(/([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B([₀₁₂₃₄₅₆₇₈₉]+)(?:\[([^\]\n]+)\])?/g)){
        const b=burden(supNum(m[1])), sm=submove(supNum(m[1]),subNum(m[2])), owner=(m[3]||'').trim();
        const summary=tailSummary(trimmed,m[0].length);
        addNode(model,{id:sm,kind:'submove',label:summary?`${sm}[${owner||'OP'}] — ${summary}`:sm,line:lineNo,excerpt:trimmed.slice(0,220),owner,parent:b,result:summary});
        if(!model.submoves[b]) model.submoves[b]=[];
        if(!model.submoves[b].includes(sm)) model.submoves[b].push(sm);
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:''});
        addEdge(model,{source:b,target:sm,kind:'burden-submove',line:lineNo,excerpt:trimmed.slice(0,220)});
      }
      for(const m of line.matchAll(/\bB(\d+)_(\d+)\s*(?:\[([^\]\n]+)\])?/g)){
        const b=burden(m[1]), sm=submove(m[1],m[2]), owner=(m[3]||'').trim();
        warnLegacy(model,lineNo,m[0],owner?`${sm}[${owner}]`:sm);
        const summary=tailSummary(trimmed,m[0].length);
        if(!model.burdens.includes(b)) model.burdens.push(b);
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:trimmed.slice(0,220)});
        addNode(model,{id:sm,kind:'submove',label:summary?`${sm}[${owner||'OP'}] — ${summary}`:sm,line:lineNo,excerpt:trimmed.slice(0,220),owner,parent:b,result:summary});
        if(!model.submoves[b]) model.submoves[b]=[];
        if(!model.submoves[b].includes(sm)) model.submoves[b].push(sm);
        addEdge(model,{source:b,target:sm,kind:'burden-submove',line:lineNo,excerpt:trimmed.slice(0,220)});
        lastBurden=b;
      }
      const land=line.match(/\b(Land|HOLD)\(([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B\)/i);
      if(land){
        const b=burden(supNum(land[2])), term=land[1].toUpperCase()==='HOLD'?'HOLD':'Land', id=`${term}(${b})`;
        const summary=tailSummary(trimmed,land.index+land[0].length);
        model.terminals[b]=term; addNode(model,{id,kind:term==='Land'?'land':'terminal',label:summary?`${id} — ${summary}`:id,line:lineNo,excerpt:trimmed,status:term,parent:b,result:summary});
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:''}); addEdge(model,{source:b,target:id,kind:'burden-terminal',line:lineNo,excerpt:trimmed}); lastBurden=b;
      }else{
        const legacyLand=line.match(/\b(Land|HOLD)\(B(\d+)\)/i);
        if(legacyLand){
          const b=burden(legacyLand[2]), term=legacyLand[1].toUpperCase()==='HOLD'?'HOLD':'Land', id=`${term}(${b})`;
          const summary=tailSummary(trimmed,legacyLand.index+legacyLand[0].length);
          warnLegacy(model,lineNo,legacyLand[0],id);
          model.terminals[b]=term; addNode(model,{id,kind:term==='Land'?'land':'terminal',label:summary?`${id} — ${summary}`:id,line:lineNo,excerpt:trimmed,status:term,parent:b,result:summary});
          addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:''}); addEdge(model,{source:b,target:id,kind:'burden-terminal',line:lineNo,excerpt:trimmed}); lastBurden=b;
        }
      }
      if(line.includes('R(H,Δ)')||line.includes('R(H,Delta)')){
        if(line.includes('R(H,Delta)')) model.warnings.push(`line ${lineNo}: parsed legacy alias R(H,Delta); use R(H,Δ)`);
        const rereadTarget=line.match(/R\(H,Delta\)\s*B(\d+)\b/i);
        const b=(rereadTarget?burden(rereadTarget[1]):burdens[0]||lastBurden), id=`R(H,Δ)@${b||lineNo}`;
        if(rereadTarget) warnLegacy(model,lineNo,`R(H,Delta) B${rereadTarget[1]}`,`R(H,Δ)@${b}`);
        const summary=tailSummary(trimmed,line.search(/R\(H,(?:Δ|Delta)\)/)+(/R\(H,Delta\)/.test(line)?10:6));
        addNode(model,{id,kind:'reread',label:summary?`R(H,Δ) — ${summary}`:'R(H,Δ)',line:lineNo,excerpt:trimmed,parent:b,result:summary});
        if(b) addEdge(model,{source:`Land(${b})`,target:id,kind:'land-reread',line:lineNo,excerpt:trimmed});
      }
      if(/\[\s*Mid-Reread Pressure\s*\]/i.test(line)){pendingMrpBlock=true; currentMrpBurden='';}
      const target=line.match(/^\s*Target:\s*B(\d+)\b/i);
      if(pendingMrpBlock&&target){const b=burden(target[1]); currentMrpBurden=b; ensureMrp(model,b,lineNo); addEdge(model,{source:`R(H,Δ)@${b}`,target:`MRP(${b})`,kind:'reread-mrp',line:lineNo,excerpt:trimmed}); warnLegacy(model,lineNo,target[0].trim(),`MRP(${b})`);}
      const mrp=line.match(/\bMRP\(([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B\)/);
      if(mrp){const b=burden(supNum(mrp[1])); currentMrpBurden=b; ensureMrp(model,b,lineNo); addEdge(model,{source:`R(H,Δ)@${b}`,target:`MRP(${b})`,kind:'reread-mrp',line:lineNo,excerpt:trimmed});}
      const asciiGenerated=line.match(/\bMRP\(B(\d+)\)/);
      if(line.includes('generated-by')&&burdens[0]&&(mrp||asciiGenerated)){
        model.generatedBurdens[burdens[0]]=mrp?`MRP(${burden(supNum(mrp[1]))})`:`MRP(${burden(asciiGenerated[1])})`;
        if(model.nodes[burdens[0]]) model.nodes[burdens[0]].generatedBy=model.generatedBurdens[burdens[0]];
      }
      const asciiMrpLine=line.match(/^\s*MRP\(B(\d+)\)/i);
      if(asciiMrpLine){const b=burden(asciiMrpLine[1]); currentMrpBurden=b; ensureMrp(model,b,lineNo); warnLegacy(model,lineNo,asciiMrpLine[0].trim(),`MRP(${b})`);}
      const rt=line.match(/\b(held_burden_activation|generated_burden_instantiation|no_new_resultant|loopbreak|hold_partial)\b/);
      if(rt && currentMrpBurden) ensureMrp(model,currentMrpBurden,lineNo).resultTypes.push(rt[1]);
      if(rt && currentMrpBurden) refreshMrpLabel(model,currentMrpBurden);
      const asciiResult=line.match(/\bMRP resultant:\s*B(\d+)\s+licenses\s*(STOP|HOLD|RECURSE|LoopBreak)/i);
      if(asciiResult){
        const b=burden(asciiResult[1]), value=asciiResult[2], id=`Route:${value}@${b}`;
        currentMrpBurden=b; const data=ensureMrp(model,b,lineNo); data.pressure.push(trimmed); if(!data.routes.includes(value)) data.routes.push(value);
        addNode(model,{id,kind:'terminal',label:`Route: ${value} — ${trimmed.replace(/^MRP resultant:\s*/i,'').slice(0,90)}`,line:lineNo,excerpt:trimmed,route:value,parent:b,result:trimmed}); addEdge(model,{source:`MRP(${b})`,target:id,kind:'mrp-route',line:lineNo,excerpt:trimmed});
        refreshMrpLabel(model,b);
      }
      const finding=line.match(/\b(Finding|MRP resultant|Resultant|Result type):\s*([^\n;]+)/i);
      if(finding && currentMrpBurden){ensureMrp(model,currentMrpBurden,lineNo).pressure.push(finding[2].trim()); refreshMrpLabel(model,currentMrpBurden);}
      const route=line.match(/\bRoute:\s*(STOP|HOLD|RECURSE|LoopBreak(?:\(∇×T\))?|LoopBreak)/i);
      if(route){
        const b=currentMrpBurden||burdens[0]||lastBurden, value=route[1], id=`Route:${value}@${b||lineNo}`;
        routeRecords.push({burden:b,route:value,line:lineNo}); addNode(model,{id,kind:'terminal',label:`Route: ${value} — ${tailSummary(trimmed, route.index+route[0].length).slice(0,90)}`,line:lineNo,excerpt:trimmed,route:value,parent:b});
        if(b){ensureMrp(model,b,lineNo).routes.push(value); addEdge(model,{source:`MRP(${b})`,target:id,kind:'mrp-route',line:lineNo,excerpt:trimmed});}
        if(b) refreshMrpLabel(model,b);
      }
      const termRow=line.match(/^\s*B(\d+)\s*:\s*(landed|held|partial|loopbreak|closed|discharged)/i);
      if(termRow){
        const b=burden(termRow[1]), state=termRow[2].toLowerCase(), term=(state==='held'||state==='partial')?'HOLD':'Land', id=`${term}(${b})`;
        warnLegacy(model,lineNo,`B${termRow[1]}:`,`${b}: terminal=${term}`);
        model.terminals[b]=term; addNode(model,{id,kind:term==='Land'?'land':'terminal',label:id,line:lineNo,excerpt:trimmed,status:term});
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:''}); addEdge(model,{source:b,target:id,kind:'burden-terminal',line:lineNo,excerpt:trimmed});
      }
      const isDependencySummary=/Burden dependency graph/i.test(line);
      for(const m of line.matchAll(/([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B\s*→\s*([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B/g)){
        const s=burden(supNum(m[1])), t=burden(supNum(m[2])); recordDependency(model,s,t,lineNo,trimmed,isDependencySummary?'':currentMrpBurden);
      }
      for(const m of line.matchAll(/\bB(\d+)\s*->\s*B(\d+)\b/g)){
        const s=burden(m[1]), t=burden(m[2]); warnLegacy(model,lineNo,m[0],`${s} → ${t}`); recordDependency(model,s,t,lineNo,trimmed,isDependencySummary?'':currentMrpBurden);
      }
      if(isDependencySummary&&line.includes('->')&&!line.includes(';')){
        const chain=[...line.matchAll(/\bB(\d+)\b/g)].map(m=>burden(m[1]));
        for(let i=0;i<chain.length-1;i++) recordDependency(model,chain[i],chain[i+1],lineNo,trimmed,'');
      }
    });
    model.burdens=[...new Set(model.burdens)].sort((a,b)=>Number(supNum(a[0]))-Number(supNum(b[0])));
    validate(model,lines,routeRecords);
    compareWitness(model,witnessText);
    return model;
  }

  function validate(model,lines,routeRecords){
    if(model.closureComplete&&!model.initialBurdens.length) model.errors.push('initial burden set missing while closure claims coverage_complete=true');
    if(model.closureComplete){(model.initialBurdens.length?model.initialBurdens:model.burdens).forEach(b=>{if(!model.terminals[b]) model.errors.push(`${b} lacks terminal Land/HOLD accounting while closure claims complete`);});}
    const known=new Set([...model.burdens,...model.initialBurdens]);
    model.graphEdges.forEach(([s,t,line])=>{if(!known.has(s)) model.errors.push(`line ${line}: dependency edge source ${s} is unknown`); if(!known.has(t)) model.errors.push(`line ${line}: dependency edge target ${t} is unknown`);});
    model.graphEdges.forEach(([s,t,line])=>{if(Object.keys(model.mrp).length&&!Object.values(model.mrp).some(m=>(m.edges||[]).some(e=>e[0]===s&&e[1]===t))) model.errors.push(`line ${line}: dependency edge ${s} → ${t} lacks MRP/resultant backing`);});
    Object.entries(model.mrp).forEach(([b,m])=>{if(!m.routes.length&&!m.resultTypes.length&&!m.pressure.length&&!m.edges.length) model.errors.push(`MRP(${b}) appears as a label with no resultant/route consequence`);});
    const initialSet=new Set(model.initialBurdens);
    Object.entries(model.mrp).forEach(([b,m])=>(m.edges||[]).forEach(([,target])=>{
      if((m.resultTypes||[]).includes('generated_burden_instantiation')&&initialSet.has(target)&&model.generatedBurdens[target]!==`MRP(${b})`){
        model.warnings.push(`MRP(${b}) claims generated_burden_instantiation, but ${target} was already in the initial burden inventory; visually classified as held_burden_activation`);
      }
    }));
    model.burdens.forEach(b=>{if(model.terminals[b]==='Land'&&!(model.submoves[b]||[]).length) model.warnings.push(`${b} lands without visible submoves`);});
    routeRecords.forEach(r=>{if(String(r.route).toUpperCase()==='STOP' && /Layer B|^#+\s*Burden\s+\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\s+\[generated-by/m.test(lines.slice(r.line).join('\n'))) model.errors.push(`line ${r.line}: Route: STOP is followed by later burden / Layer B work`);});
    const text=lines.join('\n');
    const fieldStates=[...text.matchAll(/∇·B\s*:\s*([^;\n]+)/gi)].map(m=>m[1].trim().toLowerCase());
    const curlStates=[...text.matchAll(/∇×κ\s*:\s*([^;\n]+)/gi)].map(m=>m[1].trim().toLowerCase());
    if(model.closureComplete&&fieldStates.some(s=>!s.startsWith('neutral'))&&!/Route:\s*(HOLD|RECURSE)|HOLD\(/i.test(text)) model.errors.push('coverage_complete=true while ∇·B is non-neutral without HOLD/RECURSE explanation');
    if(model.closureComplete&&curlStates.some(s=>!s.startsWith('null')&&!s.includes('resolved'))&&!/LoopBreak|resolved|null/i.test(text)) model.errors.push('coverage_complete=true while ∇×κ is non-null without LoopBreak/resolution');
  }

  function compareWitness(model,witnessText){
    if(!String(witnessText||'').trim()) return;
    try{
      const payload=JSON.parse(witnessText);
      const witnessNodes=new Set((payload.nodes||[]).map(normalizeBurden));
      if(witnessNodes.size){
        const visible=new Set(model.burdens);
        const w=[...witnessNodes].sort().join(', '), v=[...visible].sort().join(', ');
        if(w!==v) model.witnessMismatches.push(`node mismatch visible=[${v}] field_witness=[${w}]`);
      }
    }catch(e){ model.errors.push(`field_witness JSON is invalid: ${e.message}`); }
  }

  function colorFor(node,model){
    if(model.errors.some(e=>e.includes(node.id))) return '#ef4444';
    if(node.kind==='mrp') return '#a855f7';
    if(node.kind==='input') return '#64748b';
    if(node.kind==='closure') return '#16a34a';
    if(node.kind==='burden') return node.generatedBy?'#8b5cf6':'#3b82f6';
    if(node.kind==='submove') return '#38bdf8';
    if(node.kind==='land') return '#22c55e';
    if(node.kind==='reread') return '#f59e0b';
    if(node.kind==='terminal') return /STOP/i.test(node.label)?'#22c55e':'#f59e0b';
    return '#64748b';
  }

  function wrapWords(text,maxChars,maxLines=3){
    const words=String(text||'').replace(/\s+/g,' ').trim().split(' ').filter(Boolean);
    const lines=[]; let cur='';
    words.forEach(w=>{ if((cur+' '+w).trim().length>maxChars && cur){ lines.push(cur); cur=w; } else cur=(cur+' '+w).trim(); });
    if(cur) lines.push(cur);
    if(Number.isFinite(maxLines) && maxLines>0 && lines.length>maxLines){ lines.length=maxLines; lines[maxLines-1]=`${lines[maxLines-1].replace(/\s*$/,'')} (more in inspector)`; }
    return lines.length?lines:[''];
  }
  function svgText(text,x,y,width=180,lineHeight=14,maxLines=3,klass='',fill='#f8fafc',size=12,weight=800){
    return `<text x="${x}" y="${y}" fill="${fill}" font-size="${size}" font-weight="${weight}" ${klass?`class="${klass}"`:''}>${wrapWords(text,Math.max(12,Math.floor(width/7)),maxLines).map((line,i)=>`<tspan x="${x}" dy="${i?lineHeight:0}">${esc(line)}</tspan>`).join('')}</text>`;
  }
  function edgeLabel(kind){
    return ({'input-diagnosis':'read for structure','diagnosis-inventory':'finds problems','inventory-burden':'problem found','burden-submove':'answered by','burden-terminal':'establishes','land-reread':'what remains?','reread-mrp':'follow-up check','mrp-route':'routes','dependency':'depends on'}[kind]||kind);
  }
  function routeResultType(model,b){
    const data=model.mrp[b]||{};
    if((data.edges||[]).some(e=>model.generatedBurdens[e[1]]===`MRP(${b})`)) return 'generated_burden_instantiation';
    if((data.edges||[]).length) return 'held_burden_activation';
    const explicit=(data.resultTypes||[])[0];
    if(explicit) return explicit;
    if((data.routes||[]).some(r=>/HOLD/i.test(r))) return 'hold_partial';
    if((data.routes||[]).some(r=>/LoopBreak/i.test(r))) return 'loopbreak';
    return 'no_new_resultant';
  }
  function publicRouteType(type){
    return ({
      generated_burden_instantiation:'another failure point surfaced',
      held_burden_activation:'known failure point still needs answering',
      no_new_resultant:'no further failure point remained',
      hold_partial:'real failure point remains held',
      loopbreak:'loop/proof-stack blocked'
    })[type]||type;
  }
  function publicTerminalBadge(state){
    const s=String(state||'pending');
    if(/HOLD/i.test(s)) return 'Held';
    if(/PARTIAL|RECURSE/i.test(s)) return 'Partial';
    if(/land/i.test(s)) return 'Failure shown';
    if(/STOP|closed/i.test(s)) return 'Closed';
    return s;
  }
  function publicRouteBadge(routes){
    const r=String(routes||'');
    if(/STOP/i.test(r)) return 'Closed for this reply';
    if(/HOLD/i.test(r)) return 'Held open';
    if(/RECURSE/i.test(r)) return 'Next failure point';
    if(/LoopBreak/i.test(r)) return 'Loop blocked';
    return 'Route';
  }
  function humanize(text){
    return String(text||'')
      .replace(/\s+/g,' ')
      .replace(/\b([a-z]+)-([a-z]+)/gi,(m,a,b)=>`${a} ${b}`)
      .replace(/\bFPD\b/g,'foreign premise detection')
      .replace(/\bM1-P\b/g,'performative contradiction')
      .replace(/\bM1\b/g,'self refutation')
      .replace(/\bM8\b/g,'consequence trace')
      .replace(/\bM9\b/g,'predication repair')
      .trim();
  }
  function stripTechnicalLead(text){
    return humanize(String(text||'')
      .replace(/^Answer move\s+/i,'')
      .replace(/^[⁰¹²³⁴⁵⁶⁷⁸⁹]+B[₀₁₂₃₄₅₆₇₈₉]+(?:\[[^\]]+\])?\s+—\s*/,'')
      .replace(/^Land\([^)]+\)\s+—\s*/i,'')
      .replace(/^HOLD\([^)]+\)\s+—\s*/i,'')
      .replace(/^R\(H,Δ\)\s+—\s*/i,'')
      .replace(/^MRP\([^)]+\)\s*[:—-]?\s*/i,'')
      .replace(/^Route:\s*/i,''));
  }
  function publicNodeLabel(node,model){
    if(node.kind==='input') return node.label;
    if(node.kind==='burden') return node.label.replace(/^([⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s+—\s*/,'Problem $1 — ');
    if(node.kind==='submove') return stripTechnicalLead(node.label);
    if(node.kind==='land'){
      const prefix=/HOLD/i.test(node.id)?'What remains held':'What this answer established';
      return node.label.replace(/^Land\((.+?)\)\s+—\s*/i,`${prefix} — `).replace(/^HOLD\((.+?)\)\s+—\s*/i,`${prefix} — `).replace(/^Land\(.+?\)$/i,prefix).replace(/^HOLD\(.+?\)$/i,prefix);
    }
    if(node.kind==='reread') return node.label.replace(/^R\(H,Δ\)\s+—\s*/,'After this answer, what remains? — ').replace(/^R\(H,Δ\)$/,'After this answer, what remains?');
    if(node.kind==='mrp'){
      const b=node.id.match(/\((.+)\)/)?.[1]||'';
      return `Follow-up pressure check — ${publicRouteType(routeResultType(model,b))}`;
    }
    if(node.kind==='terminal'&&/^Route:/i.test(node.label)){
      if(/RECURSE/i.test(node.label)) return node.label.replace(/^Route:\s*RECURSE/i,'Next issue still needs answering — RECURSE');
      if(/HOLD/i.test(node.label)) return node.label.replace(/^Route:\s*HOLD/i,'Still open — HOLD');
      if(/STOP/i.test(node.label)) return node.label.replace(/^Route:\s*STOP/i,'Final route — STOP');
      if(/LoopBreak/i.test(node.label)) return node.label.replace(/^Route:\s*/i,'Loop blocked — ');
    }
    return node.label;
  }
  function nodeBox(node,x,y,w,h,model,mode){
    const fill=colorFor(node,model), invalid=model.errors.some(e=>e.includes(node.id));
    const stroke=mode==='validation'&&invalid?'#fecaca':'#1f2937';
    const isTop=node.kind==='input';
    const tech=node.kind==='submove'&&node.owner?`TTP / ${node.owner}`:node.kind;
    return `<g class="outputGrapherNode" tabindex="0" data-node-id="${esc(node.id)}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9" fill="${fill}" stroke="${stroke}" stroke-width="1.5" opacity=".92"></rect>${svgText(publicNodeLabel(node,model),x+10,y+20,w-20,isTop?15:14,isTop?4:3,'ogNodeLabel','#f8fafc',isTop?13:12,900)}<text x="${x+10}" y="${y+h-10}" fill="#e2e8f0" font-size="10">${esc(tech)} · ${esc(node.id)}</text><title>${esc(node.excerpt||node.id)}</title></g>`;
  }
  function svgEdge(a,b,kind,labelOverride=''){
    if(!a||!b) return '';
    const midX=(a[0]+b[0])/2, midY=(a[1]+b[1])/2;
    return `<path d="M${a[0]} ${a[1]} C${midX} ${a[1]}, ${midX} ${b[1]}, ${b[0]} ${b[1]}" fill="none" stroke="#64748b" stroke-width="1.4" marker-end="url(#ogArrow)"></path><text class="outputGrapherEdgeLabel" x="${midX-30}" y="${midY-6}" fill="#94a3b8" font-size="10" font-weight="800">${esc(labelOverride||edgeLabel(kind)).slice(0,28)}</text>`;
  }
  function collapseLabel(model){
    if(model.errors.length) return 'invalid / not reconstructible';
    const held=Object.values(model.terminals).some(x=>String(x).toUpperCase()==='HOLD');
    const divergence=String(model.collapse?.divergence||'');
    const curl=String(model.collapse?.curl||'');
    const closureOk=model.closureComplete && !/non-neutral|unresolved|live/i.test(divergence) && !/non-null|unresolved/i.test(curl);
    if(closureOk && /hold|held|separate downstream/i.test(JSON.stringify(model.collapse))) return 'closed for this reply / broader issue held';
    if(closureOk) return 'collapse achieved';
    if(held || /false|non-neutral|hold/i.test(JSON.stringify(model.collapse))) return 'partial / held';
    if(model.closureComplete) return 'collapse achieved';
    return 'reconstructible route';
  }
  function semanticBurdenLabels(model,limit=4){
    return (model.initialBurdens.length?model.initialBurdens:model.burdens)
      .map(b=>`${issueLabel(b)} - ${burdenDescription(model,b)}`.replace(/\s+/g,' '))
      .filter(Boolean)
      .slice(0,limit);
  }
  function splitReadableItems(text){
    return String(text||'')
      .split(/(?<=\.)\s+|;\s+|\s+•\s+/)
      .map(x=>x.trim())
      .filter(Boolean);
  }
  function burdenNumber(b){
    const s=String(b||'');
    const m=s.match(/^B(\d+)/);
    if(m) return m[1];
    const prefix=s.split('B')[0]||'';
    const n=[...prefix].map(c=>supToInt[c]||'').join('');
    return n||s.replace(/B.*/,'')||s;
  }
  function issueLabel(b){return `Failure point ${burdenNumber(b)}`;}
  function issueGraph(a,b){return `${issueLabel(a)} → ${issueLabel(b)}`;}
  function burdenDescription(model,b){
    const raw=String(model.nodes[b]?.label||b).replace(/\s+/g,' ').trim();
    let desc=raw.startsWith(b)?raw.slice(String(b).length):raw;
    desc=desc.replace(/^\s*(?:[-–—]|:)\s*/,'').trim();
    return desc||raw;
  }
  function firstSentence(text){
    return String(text||'').split(/(?<=\.)\s+/)[0] || String(text||'');
  }
  function refutationParties(model){
    const closing=String(model.closingFormulation||'');
    const match=closing.match(/^The\s+(.+?)\s+does\s+not\s+refute\s+(.+?)\./i);
    if(!match) return null;
    return {
      challenged: match[1].trim(),
      defended: match[2].trim()
    };
  }
  function verdictDigest(model){
    const parties=refutationParties(model);
    const closing=conclusionDigest(model);
    if(parties){
      const reason=closing.replace(/^The\s+.+?\s+does\s+not\s+refute\s+.+?\.\s*/i,'').trim();
      const defender=parties.defended.replace(/^the\s+/i,'');
      return {
        headline:`Final answer: the ${parties.challenged} fails`,
        body:`${defender}'s challenge remains standing. The graph is dismantling the ${parties.challenged}, not defending it.${reason?` ${firstSentence(reason)}`:''}`
      };
    }
    return {
      headline:`Verdict: ${collapseLabel(model)}`,
      body:closing
    };
  }
  function readerInputDigest(model){
    const raw=String(model.inputDigest||'').trim();
    if(raw && raw!=='pasted daee-epistemics output' && !/^dominant\b/i.test(raw)) return raw;
    const labels=semanticBurdenLabels(model,2);
    const parties=refutationParties(model);
    const task=/REFUTE/i.test(model.userTask||'')
      ? (parties?`Reply being rejected: the ${parties.challenged} is trying to answer ${parties.defended}. The blue moves below are rebuttal moves against that reply; they show why ${parties.defended}'s challenge remains standing.`:'Claim under review: this map is refuting the surfaced reply, not presenting that reply as the conclusion.')
      : model.userTask?`User task: ${model.userTask}.`:'';
    const casePart=(model.caseProfile&&model.caseProfile!=='not detected')?`Case recognized: ${model.caseProfile}.`:'';
    const targetPart=labels.length?`Failure points tested: ${labels.join('; ')}.`:'';
    const anchored=[task,casePart,targetPart].filter(Boolean).join(' ');
    if(anchored) return anchored;
    if(labels.length) return `Inferred from the burden inventory: ${labels.join('; ')}`;
    if(model.fieldType&&model.fieldType!=='not detected') return `A ${model.fieldType} case processed as ${model.claimType||'a governed claim'}`;
    return 'Pasted daee-epistemics output; original prompt text was not echoed in the output.';
  }
  function diagnosisDigest(model,burdens){
    const parts=[
      `Field diagnosis: ${model.fieldType||'not detected'}`,
      `Case: ${model.caseProfile||'not detected'}`,
      `Claim pattern: ${model.claimType||'not detected'}`,
      `Hidden structure: ${model.patternProfile||model.diagnosis||'not detected'}`,
      `Problems found: ${burdens.length}`
    ];
    if(model.restorationAim&&model.restorationAim!=='not detected') parts.push(`Restoration target: ${model.restorationAim}`);
    return parts.join(' · ');
  }
  function diagnosisItems(model,burdens){
    return [
      `Field diagnosis: ${model.fieldType||'not detected'}`,
      `Case recognized: ${model.caseProfile||'not detected'}`,
      `Claim pattern: ${model.claimType||'not detected'}`,
      `Hidden structure: ${model.patternProfile||model.diagnosis||'not detected'}`,
      `Problems found: ${burdens.length}`,
      model.restorationAim&&model.restorationAim!=='not detected'?`Restoration target: ${model.restorationAim}`:''
    ].filter(Boolean);
  }
  function conclusionDigest(model){
    if(model.closingFormulation) return model.closingFormulation;
    if(model.restorativeResponse) return model.restorativeResponse;
    return collapseLabel(model);
  }
  function renderTopSummary(model){
    const inventory=(model.initialBurdens.length?model.initialBurdens:model.burdens).map(b=>`<li>${esc(model.nodes[b]?.label||b)}</li>`).join('')||'<li>not detected</li>';
    const collapse=model.collapse||{}, pillStatus=model.errors.length?'fail':model.warnings.length?'warn':'ok';
    const verdict=verdictDigest(model);
    return `<div class="outputGrapherTopCards">
      <section class="outputGrapherTopCard"><h3>Final Answer From The Output</h3><p><strong>${esc(verdict.headline)}</strong></p><p>${esc(verdict.body)}</p></section>
      <section class="outputGrapherTopCard"><h3>Reply / Claim Being Rejected</h3><p>${esc(readerInputDigest(model))}</p></section>
      <section class="outputGrapherTopCard"><h3>Why The Reply Fails Structurally</h3><p>field diagnosis: ${esc(model.fieldType||'not detected')}</p><p>case: ${esc(model.caseProfile||'not detected')}</p><p>claim pattern: ${esc(model.claimType||'not detected')}</p><p>hidden structure: ${esc(model.patternProfile||model.diagnosis||'not detected')}</p><p>restoration target: ${esc(model.restorationAim||'not detected')}</p></section>
      <section class="outputGrapherTopCard"><h3>Failure Points In The Reply</h3><ul>${inventory}</ul></section>
      <section class="outputGrapherTopCard"><h3>Collapse / Technical Status</h3><p><strong>${esc(collapseLabel(model))}</strong></p><p>remaining pressure / ∇·B: ${esc(collapse.divergence||'not detected')}</p><p>loop check / ∇×κ: ${esc(collapse.curl||'not detected')}</p><p>all issues accounted for / 𝒞(Ψᴺ): ${esc(collapse.coverage||String(model.closureComplete))}</p><p>T_lang boundary: ${esc(collapse.tLang||'boundary not detected')}</p></section>
    </div><div class="outputGrapherPillRow"><span class="outputGrapherPill ${pillStatus}">Parser verdict: ${model.errors.length?'not reconstructible':'reconstructible'}</span><span class="outputGrapherPill">Burdens: ${model.burdens.length}</span><span class="outputGrapherPill">Submoves: ${Object.values(model.submoves).reduce((a,b)=>a+b.length,0)}</span><span class="outputGrapherPill">MRP resultants: ${Object.keys(model.mrp).length}</span><span class="outputGrapherPill">Terminals: ${Object.keys(model.terminals).length}</span></div>`;
  }

  function restorationBullets(model){
    const burdens=semanticBurdenLabels(model,4);
    const held=Object.entries(model.terminals||{})
      .filter(([,state])=>/HOLD|PARTIAL|RECURSE/i.test(String(state)))
      .map(([b,state])=>`${b}: ${state}`);
    const answered=`The rebuttal accounted for ${Object.keys(model.terminals).length}/${model.burdens.length||0} failure points${burdens.length?`: ${burdens.join('; ')}`:'.'}`;
    const candidateReliance=model.patternProfile||model.diagnosis||model.claimType;
    const reliance=(candidateReliance&&candidateReliance!=='not detected')?candidateReliance:(burdens[0]||'the input relied on a claim structure that the runtime decomposed into burdens.');
    const collapse=collapseLabel(model);
    const route=model.errors.length?'The graph still exposes missing or invalid accounting.':held.length?`The final result remains ${collapse}; live states: ${held.join('; ')}.`:`The final result reaches ${collapse}; no unaccounted terminal problem was detected.`;
    const restored=(model.restorationAim&&model.restorationAim!=='not detected')?model.restorationAim:'The handled field is oriented back toward sound fiṭrah and clear intellect after the visible burden cycle has been accounted for.';
    return [
      model.closingFormulation?`Final answer from the output: ${model.closingFormulation}`:'',
      `The rejected reply relied on: ${reliance}`,
      answered,
      route,
      `Restored synthesis: ${restored}`
    ].filter(Boolean);
  }

  function storyLineChars(width,size){
    return Math.max(18, Math.floor(width/(size*0.50)));
  }
  function storyLineText(lines,x,y,lineHeight,fill,size,weight=800){
    return `<text x="${x}" y="${y}" fill="${fill}" font-size="${size}" font-weight="${weight}" class="ogNodeLabel">${lines.map((line,i)=>`<tspan x="${x}" dy="${i?lineHeight:0}">${esc(line)}</tspan>`).join('')}</text>`;
  }
  function storyListBlock(items,x,y,w,lineHeight,fill,size,weight=800,gap=12){
    let cy=y, svg='';
    (items||[]).filter(Boolean).forEach((item)=>{
      const lines=wrapWords(item, storyLineChars(w-34,size), 0);
      svg+=`<circle cx="${x+7}" cy="${cy-7}" r="5" fill="${fill}"></circle>${storyLineText(lines,x+28,cy,lineHeight,fill,size,weight)}`;
      cy+=lines.length*lineHeight+gap;
    });
    return {svg,height:Math.max(0,cy-y)};
  }
  function storySectionBlock(title,subtitle,x,y,w,options={}){
    const {
      fill='#0b1220',
      stroke='#334155',
      technical='',
      items=null,
      maxLines=0,
      titleSize=18,
      bodySize=16,
      techSize=16,
      lineHeight=24,
      pad=22,
      rail='',
      minHeight=0,
      klass='outputGrapherStoryPanel'
    }=options;
    const listItems=Array.isArray(items)?items.filter(Boolean):null;
    const bodyLines=listItems?[]:wrapWords(subtitle||'not detected', storyLineChars(w-pad*2,bodySize), maxLines);
    const techLines=technical?wrapWords(`Technical: ${technical}`, storyLineChars(w-pad*2,techSize), 2):[];
    const bodyY=y+pad+titleSize+30;
    const listBlock=listItems?storyListBlock(listItems,x+pad,bodyY,w-pad*2,lineHeight,'#e5e7eb',bodySize,800,16):null;
    const bodyHeight=listBlock?listBlock.height:bodyLines.length*lineHeight;
    const techY=bodyY+bodyHeight+24;
    const height=Math.max(minHeight, pad+titleSize+30+bodyHeight+(techLines.length?24+techLines.length*(techSize+5):0)+pad);
    const railSvg=rail?`<rect x="${x}" y="${y}" width="7" height="${height}" rx="7" fill="${rail}"></rect>`:'';
    const techSvg=techLines.length?storyLineText(techLines,x+pad,techY,techSize+5,'#94a3b8',techSize,800):'';
    const bodySvg=listBlock?listBlock.svg:storyLineText(bodyLines,x+pad,bodyY,lineHeight,'#e5e7eb',bodySize,800);
    return {
      height,
      svg:`<g class="${klass}"><rect x="${x}" y="${y}" width="${w}" height="${height}" rx="16" fill="${fill}" stroke="${stroke}" stroke-width="1.4"></rect>${railSvg}<text x="${x+pad}" y="${y+pad+titleSize}" fill="#f8fafc" font-size="${titleSize}" font-weight="900">${esc(title)}</text>${bodySvg}${techSvg}</g>`
    };
  }
  function storySection(title,subtitle,x,y,w,h,fill='#0b1220',stroke='#334155',technical=''){
    return storySectionBlock(title,subtitle,x,y,w,{fill,stroke,technical,minHeight:h,maxLines:3}).svg;
  }
  function renderCollapsePanel(model,x,y,w){
    const collapse=model.collapse||{};
    const bullets=restorationBullets(model);
    const pad=36, titleSize=34, bodySize=22, techSize=18, lineHeight=34;
    const bulletGap=20;
    const bulletHeight=bullets.reduce((height,text)=>height+wrapWords(text, storyLineChars(w-pad*2-24,bodySize), 0).length*lineHeight+bulletGap,0);
    const tech=`Terminal states: ${Object.keys(model.terminals).length}/${model.burdens.length} · ∇·B: ${collapse.divergence||'not detected'} · ∇×κ: ${collapse.curl||'not detected'} · 𝒞(Ψᴺ): ${collapse.coverage||String(model.closureComplete)} · T_lang: ${collapse.tLang||'boundary not detected'}`;
    const techText=`R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) → 𝒞(Ψᴺ) → N_fiṭrī ∧ ʿaql ṣarīḥ · ${tech}`;
    const techLines=wrapWords(techText, storyLineChars(w-pad*2-28,techSize), 0);
    const techH=72+techLines.length*30;
    const height=pad+titleSize+26+bulletHeight+22+techH+pad;
    let cy=y+pad+titleSize+28;
    const bulletSvg=bullets.map(text=>{
      const lines=wrapWords(text, storyLineChars(w-pad*2-24,bodySize), 0);
      const group=`<circle cx="${x+pad+5}" cy="${cy-7}" r="5" fill="#86efac"></circle>${storyLineText(lines,x+pad+24,cy,lineHeight,'#dcfce7',bodySize,800)}`;
      cy+=lines.length*lineHeight+bulletGap;
      return group;
    }).join('');
    const techY=cy+18;
    return {
      height,
      svg:`<g class="outputGrapherProofBlock outputGrapherRestorationSummary"><rect x="${x}" y="${y}" width="${w}" height="${height}" rx="22" fill="#071a12" stroke="#22c55e" stroke-width="1.8"></rect><rect x="${x}" y="${y}" width="8" height="${height}" rx="8" fill="#10b981"></rect><text x="${x+pad}" y="${y+pad+titleSize}" fill="#dcfce7" font-size="${titleSize}" font-weight="900">Restoration Summary: ${esc(collapseLabel(model))}</text>${bulletSvg}<rect x="${x+pad}" y="${techY}" width="${w-pad*2}" height="${techH}" rx="14" fill="#0b1220" stroke="#14532d" stroke-width="1"></rect><text x="${x+pad+16}" y="${techY+32}" fill="#bbf7d0" font-size="20" font-weight="900">Technical proof strip</text>${storyLineText(techLines,x+pad+16,techY+66,30,'#bbf7d0',techSize,800)}</g>`
    };
  }
  function storyBadge(text,x,y,fill='#1f2937',stroke='#475569'){
    return `<g><rect x="${x}" y="${y}" width="${Math.max(126,String(text).length*10+28)}" height="34" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="1.2"></rect><text x="${x+14}" y="${y+23}" fill="#e5e7eb" font-size="16" font-weight="900">${esc(text)}</text></g>`;
  }
  function storyMiniFlow(model,b,x,y,w){
    const steps=[
      ['problem', '#3b82f6', b],
      ['answer moves', '#38bdf8', 'moves'],
      ['established', '#22c55e', `Land(${b})`],
      ['what remains?', '#f59e0b', 'state read'],
      [publicRouteType(routeResultType(model,b)), '#a855f7', 'follow-up'],
      [((model.mrp[b]||{}).routes||[])[0]||'route', '#f59e0b', 'next']
    ];
    const gap=14, sw=(w-gap*(steps.length-1))/steps.length;
    return steps.map((s,i)=>{
      const sx=x+i*(sw+gap);
      const arrow=i<steps.length-1?`<path d="M${sx+sw+2} ${y+24} L${sx+sw+gap-2} ${y+24}" stroke="#64748b" stroke-width="1.4" marker-end="url(#ogArrow)"></path>`:'';
      return `<g><rect x="${sx}" y="${y}" width="${sw}" height="48" rx="10" fill="${s[1]}" stroke="#1f2937" stroke-width="1.2"></rect>${svgText(s[0],sx+8,y+18,sw-16,12,1,'ogNodeLabel','#f8fafc',11,900)}<text x="${sx+8}" y="${y+38}" fill="#e2e8f0" font-size="9" font-weight="800">${esc(s[2])}</text>${arrow}</g>`;
    }).join('');
  }
  function densityConfig(){
    if(currentDensity==='compact') return {font:19,line:29,gap:44,cardPad:36,subMinH:82,subGap:18,panelLines:0};
    if(currentDensity==='expanded') return {font:24,line:37,gap:78,cardPad:54,subMinH:116,subGap:28,panelLines:0};
    return {font:22,line:34,gap:66,cardPad:48,subMinH:104,subGap:24,panelLines:0};
  }
  function renderStorySvg(model){
    const width=1500, margin=46, cardW=width-margin*2;
    const d=densityConfig();
    const burdens=model.burdens.length?model.burdens:Object.values(model.nodes).filter(n=>n.kind==='burden').map(n=>n.id);
    const verdict=verdictDigest(model);
    let y=34;
    const parts=[];
    parts.push(`<text x="${margin}" y="${y+18}" fill="#f8fafc" font-size="38" font-weight="950">OUTPUT GRAPHER - REBUTTAL MAP</text><rect x="${width-420}" y="${y-16}" width="370" height="44" rx="9" fill="#0f172a" stroke="#475569" stroke-width="1.2"></rect><text x="${width-392}" y="${y+12}" fill="#e2e8f0" font-size="19" font-weight="900">Plain-language Rebuttal View</text>`);
    y+=60;
    const verdictCard=storySectionBlock(verdict.headline,verdict.body,margin,y,cardW,{fill:'#071a12',stroke:'#10b981',maxLines:0,titleSize:34,bodySize:23,lineHeight:36,pad:34,rail:'#10b981'});
    parts.push(verdictCard.svg); y+=verdictCard.height+18;
    const claimCard=storySectionBlock('Reply / claim being rejected',readerInputDigest(model),margin,y,cardW,{fill:'#111827',stroke:'#475569',items:splitReadableItems(readerInputDigest(model)),maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34,rail:'#64748b'});
    parts.push(claimCard.svg); y+=claimCard.height+18;
    const diagCard=storySectionBlock('Why the reply fails structurally',diagnosisDigest(model,burdens),margin,y,cardW,{fill:'#0b1220',stroke:'#475569',items:diagnosisItems(model,burdens),maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34,rail:'#64748b'});
    parts.push(diagCard.svg); y+=diagCard.height+18;
    const conclusionCard=storySectionBlock('Why the reply fails',verdict.body,margin,y,cardW,{fill:'#071a12',stroke:'#10b981',maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34,rail:'#10b981'});
    parts.push(conclusionCard.svg); y+=conclusionCard.height+18;
    const invItems=semanticBurdenLabels(model,8);
    const invCard=storySectionBlock('Failure points in the reply',invItems.join('; ')||'not detected',margin,y,cardW,{fill:'#07111f',stroke:'#3b82f6',items:invItems.length?invItems:null,maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34,rail:'#3b82f6'});
    parts.push(invCard.svg); y+=invCard.height+28;
    burdens.forEach((b,index)=>{
      const sms=model.submoves[b]||[];
      const burden=model.nodes[b]||{label:b};
      const land=model.nodes[`Land(${b})`]||model.nodes[`HOLD(${b})`];
      const reread=model.nodes[`R(H,Δ)@${b}`];
      const mrp=model.mrp[b]||{};
      const routes=(mrp.routes||[]).join(', ')||'not detected';
      const result=publicRouteType(routeResultType(model,b));
      const visibleSms=sms.slice(0,currentDensity==='compact'?3:currentDensity==='expanded'?6:4);
      const hiddenCount=Math.max(0,sms.length-visibleSms.length);
      const titleText=`${issueLabel(b)} - ${burdenDescription(model,b)}`;
      const titleLines=wrapWords(titleText, storyLineChars(cardW-68,34), 0);
      const badgeY=y+56+titleLines.length*42+18;
      const problemText='What fails here: '+burdenDescription(model,b);
      const problemLines=wrapWords(problemText, storyLineChars(cardW-68,d.font), 0);
      const problemY=badgeY+76;
      const moveBlocks=visibleSms.map(sm=>{
        const node=model.nodes[sm]||{label:sm};
        const lines=wrapWords(publicNodeLabel(node,model), storyLineChars(cardW-116,d.font), 0);
        return {sm,node,lines,height:Math.max(d.subMinH,lines.length*d.line+30)};
      });
      const moveBlockH=moveBlocks.reduce((sum,block,i)=>sum+block.height+(i?d.subGap:0),0)+(hiddenCount?32:0);
      const movesTitleY=problemY+problemLines.length*d.line+36-y;
      const firstMoveY=movesTitleY+50;
      const panelTop=firstMoveY+moveBlockH+34;
      const fullW=cardW-60, panelGap=24, panelX=margin+30;
      const landBlock=storySectionBlock('What this establishes against the reply',land?stripTechnicalLead(land.label):'No landing result detected in the visible output.',panelX,y+panelTop,fullW,{fill:'#052e16',stroke:'#22c55e',technical:'',maxLines:d.panelLines,titleSize:26,bodySize:22,lineHeight:34,pad:32,rail:'#22c55e'});
      const rereadY=y+panelTop+landBlock.height+panelGap;
      const rereadBlock=storySectionBlock('After this answer, what remains?',reread?stripTechnicalLead(reread.label):'No state reread was detected for this problem.',panelX,rereadY,fullW,{fill:'#451a03',stroke:'#f59e0b',technical:'',maxLines:d.panelLines,titleSize:26,bodySize:22,lineHeight:34,pad:32,rail:'#f59e0b'});
      const mrpY=rereadY+rereadBlock.height+panelGap;
      const edgeText=(mrp.edges||[]).map(e=>issueGraph(e[0],e[1])).join(', ')||'none';
      const mrpBlock=storySectionBlock('Follow-up: does the reply still have pressure?',`${result}. Next link: ${edgeText}`,panelX,mrpY,fullW,{fill:'#2e1065',stroke:'#a855f7',technical:'',maxLines:d.panelLines,titleSize:26,bodySize:22,lineHeight:34,pad:32,rail:'#a855f7'});
      const routeClosed=/STOP/i.test(routes);
      const routeBadgeText=publicRouteBadge(routes);
      const routeY=mrpY+mrpBlock.height+panelGap;
      const routeBlock=storySectionBlock('Next failure point / closure',humanize(routes),panelX,routeY,fullW,{fill:routeClosed?'#052e16':'#451a03',stroke:routeClosed?'#10b981':'#f59e0b',technical:'',maxLines:d.panelLines,titleSize:26,bodySize:22,lineHeight:34,pad:32,rail:routeClosed?'#10b981':'#f59e0b'});
      const cardH=routeY-y+routeBlock.height+86;
      parts.push(`<g class="outputGrapherStoryBurden"><rect x="${margin}" y="${y}" width="${cardW}" height="${cardH}" rx="24" fill="#07111f" stroke="#263044" stroke-width="1.5"></rect><rect x="${margin}" y="${y}" width="10" height="${cardH}" rx="10" fill="#3b82f6"></rect>${storyLineText(titleLines,margin+34,y+56,42,'#f8fafc',34,900)}`);
      parts.push(storyBadge('Failure point',margin+34,badgeY,'#1e3a8a','#3b82f6'));
      parts.push(storyBadge(publicTerminalBadge(model.terminals[b]),margin+260,badgeY,/HOLD|PARTIAL|RECURSE/i.test(model.terminals[b]||'')?'#7c2d12':'#14532d',/HOLD|PARTIAL|RECURSE/i.test(model.terminals[b]||'')?'#f59e0b':'#22c55e'));
      parts.push(storyBadge(routeBadgeText,margin+480,badgeY,routeClosed?'#064e3b':'#7c2d12',routeClosed?'#10b981':'#f59e0b'));
      parts.push(storyLineText(problemLines,margin+34,problemY,d.line,'#cbd5e1',d.font,850));
      parts.push(`<text x="${margin+34}" y="${y+movesTitleY}" fill="#bae6fd" font-size="28" font-weight="900">How the graph rejects this point</text>`);
      let subY=y+firstMoveY;
      moveBlocks.forEach((block)=>{
        parts.push(`<g class="outputGrapherStorySubmove"><rect x="${margin+34}" y="${subY-34}" width="${cardW-68}" height="${block.height}" rx="15" fill="#0e7490" stroke="#38bdf8" stroke-width="1.3"></rect><rect x="${margin+34}" y="${subY-34}" width="8" height="${block.height}" rx="8" fill="#38bdf8"></rect>${storyLineText(block.lines,margin+58,subY,d.line,'#ecfeff',d.font,850)}</g>`);
        subY+=block.height+d.subGap;
      });
      if(hiddenCount) parts.push(`<text x="${margin+46}" y="${subY-16}" fill="#94a3b8" font-size="16" font-weight="900">+ ${hiddenCount} additional move(s) available in technical view / node inspector</text>`);
      parts.push(landBlock.svg);
      parts.push(rereadBlock.svg);
      parts.push(mrpBlock.svg);
      parts.push(routeBlock.svg);
      if(index<burdens.length-1){
        const next=burdens[index+1];
        const rel=(mrp.edges||[]).some(e=>e[1]===next)?publicRouteType(routeResultType(model,b)):'next listed issue';
        parts.push(`<text x="${margin+42}" y="${y+cardH-28}" fill="#94a3b8" font-size="21" font-weight="900">Next failure point: ${esc(issueGraph(b,next))} · ${esc(rel)}</text>`);
      }
      parts.push('</g>');
      y+=cardH+d.gap;
    });
    const collapsePanel=renderCollapsePanel(model,margin,y,cardW);
    parts.push(collapsePanel.svg); y+=collapsePanel.height+52;
    const legend=`<g class="ogSvgLegend" transform="translate(${margin} ${y-10})"><text fill="#e5e7eb" font-size="24" font-weight="900">Legend:</text><circle cx="126" cy="-8" r="8" fill="#3b82f6"/><text x="142" y="0" fill="#cbd5e1" font-size="22">failure point</text><circle cx="342" cy="-8" r="8" fill="#38bdf8"/><text x="358" y="0" fill="#cbd5e1" font-size="22">rebuttal move</text><circle cx="594" cy="-8" r="8" fill="#22c55e"/><text x="610" y="0" fill="#cbd5e1" font-size="22">failure shown</text><circle cx="842" cy="-8" r="8" fill="#a855f7"/><text x="858" y="0" fill="#cbd5e1" font-size="22">follow-up check</text><circle cx="126" cy="38" r="8" fill="#f59e0b"/><text x="142" y="46" fill="#cbd5e1" font-size="22">next failure / HOLD / RECURSE</text><circle cx="514" cy="38" r="8" fill="#10b981"/><text x="530" y="46" fill="#cbd5e1" font-size="22">STOP / closed / restoration</text><circle cx="872" cy="38" r="8" fill="#ef4444"/><text x="888" y="46" fill="#cbd5e1" font-size="22">invalid / missing</text></g>`;
    const height=y+100;
    return `<svg id="ogSvg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Plain-language rebuttal story infographic"><rect x="0" y="0" width="${width}" height="${height}" fill="#050914"/><defs><marker id="ogArrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>${parts.join('')}${legend}</svg>`;
  }

  function renderGraph(model){
    if(currentGraphMode==='rebuttal') return renderStorySvg(model);
    const pos={}, width=1780, nodeH=76, rowH=82, laneGap=56, left=36;
    const burdens=model.burdens.length?model.burdens:Object.values(model.nodes).filter(n=>n.kind==='burden').map(n=>n.id);
    const inputNode={id:'input',kind:'input',label:`What the claim says — ${readerInputDigest(model)}`,excerpt:readerInputDigest(model)};
    const diagNode={id:'diagnosis',kind:'input',label:`What the claim depends on — ${model.fieldType||'field not detected'} / ${model.claimType||'claim not detected'}`,excerpt:model.diagnosis||''};
    const invNode={id:'inventory',kind:'input',label:`Main problems the input creates — ${semanticBurdenLabels(model,3).join('; ')||'not detected'}`,excerpt:model.liveBurden||''};
    const topH=96;
    pos.input=[left,38,350,topH]; pos.diagnosis=[430,38,380,topH]; pos.inventory=[850,38,520,topH];
    let y=194;
    const clusterSvg=[];
    burdens.forEach(b=>{
      const sms=model.submoves[b]||[], laneH=Math.max(190,sms.length*rowH+106), generated=model.generatedBurdens[b];
      clusterSvg.push(`<rect class="outputGrapherBurdenCluster" x="${left}" y="${y-30}" width="${width-72}" height="${laneH}" rx="16" fill="${generated?'#14102a':'#07111f'}" stroke="${generated?'#8b5cf6':'#263044'}" stroke-width="1.4"></rect><text class="outputGrapherClusterTitle" x="${left+16}" y="${y-8}" fill="#f8fafc" font-size="14" font-weight="900">Problem answered ${esc(b)}${generated?' — new issue surfaced by '+esc(generated):''}</text>`);
      pos[b]=[left+18,y+16,260,nodeH];
      sms.forEach((sm,i)=>{pos[sm]=[left+318,y+16+i*rowH,350,nodeH];});
      [`Land(${b})`,`HOLD(${b})`].forEach(id=>{if(model.nodes[id]) pos[id]=[left+710,y+16,300,nodeH];});
      const rr=`R(H,Δ)@${b}`; if(model.nodes[rr]) pos[rr]=[left+1048,y+16,260,nodeH];
      const mrp=`MRP(${b})`; if(model.nodes[mrp]) pos[mrp]=[left+1342,y+16,330,nodeH];
      Object.values(model.nodes).filter(n=>n.id.endsWith(`@${b}`)&&n.kind==='terminal').forEach((n,i)=>{pos[n.id]=[left+1342,y+108+i*rowH,330,nodeH];});
      y+=laneH+laneGap;
    });
    const collapseId='collapseStatus';
    pos[collapseId]=[left,y,width-72,206];
    const height=Math.max(360,y+272);
    const allNodes=[inputNode,diagNode,invNode,...Object.values(model.nodes),{id:collapseId,kind:'closure',label:`Noetic Field Status — ${collapseLabel(model)}`,excerpt:model.restorationAim||''}];
    const renderedNodes=allNodes.filter(n=>pos[n.id]&&n.id!==collapseId).map(n=>{const p=pos[n.id]; return nodeBox(n,p[0],p[1],p[2],p[3],model,currentGraphMode);}).join('');
    const topEdges=svgEdge([pos.input[0]+pos.input[2],pos.input[1]+38],[pos.diagnosis[0],pos.diagnosis[1]+38],'input-diagnosis')+svgEdge([pos.diagnosis[0]+pos.diagnosis[2],pos.diagnosis[1]+38],[pos.inventory[0],pos.inventory[1]+38],'diagnosis-inventory');
    const edgeSvg=model.edges.map(e=>{const s=pos[e.source],t=pos[e.target]; if(!s||!t) return ''; return svgEdge([s[0]+s[2],s[1]+(s[3]/2)],[t[0],t[1]+(t[3]/2)],e.kind);}).join('');
    const initialSet=new Set(model.initialBurdens.length?model.initialBurdens:model.burdens.filter(b=>!model.generatedBurdens[b]));
    const inputBurdenEdges=[...initialSet].map((b,i)=>pos[b]?svgEdge([pos.inventory[0]+pos.inventory[2],pos.inventory[1]+38],[pos[b][0],pos[b][1]+38],'inventory-burden',i?'initial burden':'initial burden'):'').join('');
    const mrpRelationEdges=[];
    Object.entries(model.mrp).forEach(([b,data])=>{
      (data.edges||[]).forEach(([source,target])=>{
        if(!pos[`MRP(${b})`]||!pos[target]) return;
        const generated=model.generatedBurdens[target]===`MRP(${b})`;
        const label=generated?'new problem surfaced':publicRouteType(routeResultType(model,b));
        mrpRelationEdges.push(svgEdge([pos[`MRP(${b})`][0]+pos[`MRP(${b})`][2],pos[`MRP(${b})`][1]+38],[pos[target][0],pos[target][1]+38],'mrp-result',label));
      });
    });
    const routeNodes=Object.values(model.nodes).filter(n=>n.kind==='terminal'&&/^Route:/.test(n.label)); const last=routeNodes[routeNodes.length-1];
    const closureEdge=last&&pos[last.id]?svgEdge([pos[last.id][0]+pos[last.id][2],pos[last.id][1]+38],[pos[collapseId][0],pos[collapseId][1]+62],'closure','closure / restoration'):'';
    const finalPanel=renderCollapsePanel(model,pos[collapseId]);
    const legend=`<g class="ogSvgLegend" transform="translate(36 ${height-36})"><text fill="#e5e7eb" font-size="12" font-weight="800">Legend:</text><circle cx="72" cy="-4" r="5" fill="#3b82f6"/><text x="82" y="0" fill="#cbd5e1" font-size="11">burden</text><circle cx="152" cy="-4" r="5" fill="#38bdf8"/><text x="162" y="0" fill="#cbd5e1" font-size="11">submove/TTP</text><circle cx="252" cy="-4" r="5" fill="#22c55e"/><text x="262" y="0" fill="#cbd5e1" font-size="11">Land/closure</text><circle cx="360" cy="-4" r="5" fill="#a855f7"/><text x="370" y="0" fill="#cbd5e1" font-size="11">MRP</text><circle cx="440" cy="-4" r="5" fill="#f59e0b"/><text x="450" y="0" fill="#cbd5e1" font-size="11">route/HOLD</text><circle cx="548" cy="-4" r="5" fill="#ef4444"/><text x="558" y="0" fill="#cbd5e1" font-size="11">invalid</text></g>`;
    return `<svg id="ogSvg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Noetic field rebuttal infographic"><rect x="0" y="0" width="${width}" height="${height}" fill="#050914"/><defs><marker id="ogArrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>${topEdges}${clusterSvg.join('')}${edgeSvg}${inputBurdenEdges}${mrpRelationEdges.join('')}${closureEdge}${renderedNodes}${finalPanel}${legend}</svg>`;
  }

  function render(model){
    currentModel=model;
    window.outputGrapherModel=model;
    const graph=document.getElementById('ogGraph'), summary=document.getElementById('ogSummary'), errors=document.getElementById('ogErrors'), warnings=document.getElementById('ogWarnings');
    if(!graph) return;
    graph.innerHTML=renderGraph(model);
    summary.innerHTML=renderTopSummary(model);
    errors.innerHTML=(model.errors.length?model.errors:['No hard errors.']).map(x=>`<li class="${model.errors.length?'outputGrapherError':''}">${esc(x)}</li>`).join('');
    warnings.innerHTML=((model.warnings||[]).concat(model.witnessMismatches||[]).length?(model.warnings||[]).concat(model.witnessMismatches||[]):['No warnings.']).map(x=>`<li class="outputGrapherWarn">${esc(x)}</li>`).join('');
    ['ogExportPngBtn','ogExportSvgBtn','ogExportJsonBtn','ogExportMermaidBtn'].forEach(id=>{const b=document.getElementById(id); if(b) b.disabled=false;});
    graph.querySelectorAll('.outputGrapherNode').forEach(el=>el.addEventListener('click',()=>inspectNode(el.dataset.nodeId)));
  }

  function inspectNode(id){
    const node=currentModel?.nodes?.[id], out=document.getElementById('ogInspector'); if(!node||!out) return;
    const notes=(currentModel.errors||[]).concat(currentModel.warnings||[]).filter(x=>x.includes(id));
    const parent=node.parent||Object.keys(currentModel.submoves||{}).find(b=>(currentModel.submoves[b]||[]).includes(node.id))||'not detected';
    const mrp=node.kind==='mrp'?currentModel.mrp[id.match(/\((.+)\)/)?.[1]||'']:{};
    out.innerHTML=`<strong>${esc(node.label)}</strong><p class="subtle">${esc(node.kind)}</p><code>${esc(node.excerpt||'no source excerpt')}</code><p>Burden / parent: ${esc(parent)}</p><p>TTP/operator: ${esc(node.owner||'not detected')}</p><p>Result/delta: ${esc(node.result||node.status||'not detected')}</p><p>Route: ${esc(node.route||mrp?.routes?.join(', ')||'not detected')}</p><p>MRP finding/type: ${esc((mrp?.resultTypes||[]).join(', ')||mrp?.pressure?.[0]||'not detected')}</p><p>Graph delta: ${esc((mrp?.edges||[]).map(e=>e.join(' → ')).join(', ')||'none detected')}</p>${notes.length?`<ul>${notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul>`:''}`;
  }

  function downloadBlob(name,type,content){
    const blob=content instanceof Blob?content:new Blob([content],{type});
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; document.body.appendChild(a); a.click(); setTimeout(()=>{URL.revokeObjectURL(a.href); a.remove();},0);
  }
  function exportSvg(){const svg=document.getElementById('ogSvg'); if(svg) downloadBlob('daee-output-collapse-graph.svg','image/svg+xml;charset=utf-8',new XMLSerializer().serializeToString(svg));}
  function exportJson(){if(currentModel) downloadBlob('daee-output-collapse-graph.json','application/json;charset=utf-8',JSON.stringify(currentModel,null,2));}
  function exportMermaid(){
    if(!currentModel) return;
    const lines=[
      "%%{init: {'flowchart': {'defaultRenderer': 'elk'}} }%%",
      'flowchart LR',
      '  classDef input fill:#64748b,color:#fff,stroke:#334155',
      '  classDef burden fill:#3b82f6,color:#fff,stroke:#334155',
      '  classDef submove fill:#38bdf8,color:#06121f,stroke:#334155',
      '  classDef mrp fill:#a855f7,color:#fff,stroke:#334155',
      '  classDef terminal fill:#f59e0b,color:#111827,stroke:#334155',
      '  classDef invalid fill:#ef4444,color:#fff,stroke:#334155'
    ];
    const nodeName=id=>'n_'+safe(id);
    Object.values(currentModel.nodes).forEach(n=>{
      lines.push(`  ${nodeName(n.id)}["${String(n.label).replace(/"/g,'&quot;')}"]:::${n.kind==='reread'||n.kind==='land'?'terminal':n.kind}`);
    });
    currentModel.edges.forEach(e=>lines.push(`  ${nodeName(e.source)} --> ${nodeName(e.target)}`));
    downloadBlob('daee-output-collapse-graph.mmd','text/plain;charset=utf-8',lines.join('\n'));
  }
  function safe(s){return String(s).replace(/[^a-zA-Z0-9_]/g,'_');}
  function exportPng(){
    const svg=document.getElementById('ogSvg'); if(!svg) return;
    const raw=new XMLSerializer().serializeToString(svg);
    const blob=new Blob([raw],{type:'image/svg+xml;charset=utf-8'});
    const url=URL.createObjectURL(blob), img=new Image();
    img.onload=()=>{const canvas=document.createElement('canvas'); canvas.width=svg.viewBox.baseVal.width||svg.width.baseVal.value; canvas.height=svg.viewBox.baseVal.height||svg.height.baseVal.value; const ctx=canvas.getContext('2d'); ctx.fillStyle='#050914'; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.drawImage(img,0,0); canvas.toBlob(png=>{if(png) downloadBlob('daee-output-collapse-graph.png','image/png',png); URL.revokeObjectURL(url);},'image/png');};
    img.onerror=()=>URL.revokeObjectURL(url); img.src=url;
  }

  function init(){
    const parse=document.getElementById('ogParseBtn');
    if(!parse) return;
    parse.addEventListener('click',()=>render(parseOutput(document.getElementById('ogOutputInput')?.value||'',document.getElementById('ogWitnessInput')?.value||'')));
    document.getElementById('ogExportPngBtn')?.addEventListener('click',exportPng);
    document.getElementById('ogExportSvgBtn')?.addEventListener('click',exportSvg);
    document.getElementById('ogExportJsonBtn')?.addEventListener('click',exportJson);
    document.getElementById('ogExportMermaidBtn')?.addEventListener('click',exportMermaid);
    document.querySelectorAll('[data-og-mode]').forEach(btn=>btn.addEventListener('click',()=>{
      currentGraphMode=btn.dataset.ogMode||'rebuttal';
      document.querySelectorAll('[data-og-mode]').forEach(item=>item.classList.toggle('active',item===btn));
      if(currentModel) render(currentModel);
    }));
    document.querySelectorAll('[data-og-density]').forEach(btn=>btn.addEventListener('click',()=>{
      currentDensity=btn.dataset.ogDensity||'comfortable';
      document.querySelectorAll('[data-og-density]').forEach(item=>item.classList.toggle('active',item===btn));
      if(currentModel) render(currentModel);
    }));
    window.daeeOutputGrapher={parseOutput,renderGraph,exportPng,exportSvg,exportJson};
  }
  document.addEventListener('DOMContentLoaded',init);
})();
