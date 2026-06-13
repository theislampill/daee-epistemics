(function(){
  const SUP='⁰¹²³⁴⁵⁶⁷⁸⁹';
  const SUB='₀₁₂₃₄₅₆₇₈₉';
  const supToInt=Object.fromEntries([...SUP].map((c,i)=>[c,String(i)]));
  const subToInt=Object.fromEntries([...SUB].map((c,i)=>[c,String(i)]));
  const intToSup=Object.fromEntries([...SUP].map((c,i)=>[String(i),c]));
  const intToSub=Object.fromEntries([...SUB].map((c,i)=>[String(i),c]));
  let currentModel=null;
  let currentGraphMode='rebuttal';

  function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function stripMarkdownArtifacts(s){
    return String(s??'')
      .replace(/```/g,'')
      .replace(/\*\*/g,'')
      .replace(/\*/g,'')
      .replace(/(?:^|\s)(?:>\s*){1,}/g,' ');
  }
  function cleanParsed(s){return stripMarkdownArtifacts(String(s??'').replace(/[╔╗╚╝║═]/g,'')).replace(/\s+/g,' ').trim();}
  function escapeRegExp(s){return String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}
  function cleanVisibleProseBlock(s){
    return canonicalizePublicNotation(String(s??'')
      .replace(/[╔╗╚╝║═]/g,'')
      .replace(/```/g,'')
      .replace(/\*\*/g,'')
      .replace(/\*/g,'')
      .replace(/(?:^|\s)(?:>\s*){1,}/g,' ')
      .replace(/\r\n/g,'\n')
      .split('\n')
      .map(line=>line.trim())
      .filter(line=>line && !/^[-–—]{3,}$/.test(line))
      .join('\n')
      .replace(/[ \t]+/g,' ')
      .replace(/\n{3,}/g,'\n\n')
      .trim());
  }
  function extractBodySection(bodyProse, heading, stopHeadings=[]){
    const headingPattern=(label)=>{
      if(/^Restorative Response$/i.test(label)) return String.raw`(?:Final\s+)?Restorative\s+Response(?:\s*(?:—|-)\s*[^*\n#]+)?`;
      if(/^Closing Formulation$/i.test(label)) return String.raw`(?:Final\s+)?Closing\s+Formulation(?:\s*(?:—|-)\s*[^*\n#]+)?`;
      if(/^Closure\/Reconstruction Witness$/i.test(label)) return String.raw`(?:Closure\/Reconstruction\s+Witness|Closure\s+Witness|Reconstruction\s+Witness)`;
      return escapeRegExp(label);
    };
    const marker=(pattern)=>`(?:^|\\n)\\s*(?:#{1,6}\\s*)?(?:\\*{1,2})?${pattern}(?:\\*{1,2})?\\s*:?\\s*(?:\\n|$)`;
    const startRe=new RegExp(marker(headingPattern(heading)),'i');
    const start=String(bodyProse||'').match(startRe);
    if(!start) return '';
    const contentStart=(start.index||0)+start[0].length;
    const rest=bodyProse.slice(contentStart);
    const stops=stopHeadings.length?stopHeadings:[
      'Restorative Response',
      'Closing Formulation',
      'Closure/Reconstruction Witness',
      'Closure Witness',
      'Reconstruction Witness',
      'Closure audit',
      'field_witness'
    ];
    const stopRe=new RegExp(marker(stops.map(headingPattern).join('|')),'i');
    const stop=rest.match(stopRe);
    return cleanVisibleProseBlock(stop?rest.slice(0,stop.index):rest);
  }
  function normalizeSourceHeadingLine(line){
    return String(line||'')
      .replace(/^\s*(?:#{1,6}\s*)?/,'')
      .replace(/^\s*\*{1,2}/,'')
      .replace(/\*{1,2}\s*$/,'')
      .replace(/^\s*\[([^\]]+)\]\s*$/,'$1')
      .replace(/\s+/g,' ')
      .trim();
  }
  function stripSourceHeading(text){
    return cleanVisibleProseBlock(String(text||'').split(/\r?\n/).slice(1).join('\n'));
  }
  function cleanSourceLine(line){
    return canonicalizePublicNotation(String(line||'')
      .replace(/^\s*(?:[-*]\s*)?/,'')
      .replace(/^\s*\*{1,2}/,'')
      .replace(/\*{1,2}\s*$/,'')
      .replace(/```/g,'')
      .replace(/\*\*/g,'')
      .replace(/\*/g,'')
      .replace(/(?:^|\s)(?:>\s*){1,}/g,' ')
      .replace(/\s+/g,' ')
      .trim());
  }
  function sourceBlockLines(text){
    return String(text||'')
      .split(/\r?\n/)
      .map(cleanSourceLine)
      .filter(line=>line && !/^[-–—]{3,}$/.test(line));
  }
  function sourceBurdenToken(raw){
    const token=String(raw||'').trim();
    if(/^\d+$/.test(token)) return burden(token);
    const ascii=token.match(/^B(\d+)$/i);
    if(ascii) return burden(ascii[1]);
    const sup=token.match(/^([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B$/);
    if(sup) return burden(supNum(sup[1]));
    return token;
  }
  function sourceHeadingKind(line){
    const raw=String(line||'');
    const heading=normalizeSourceHeadingLine(line);
    const closureWitnessHeading=/^(?:Closure\s*\/\s*Reconstruction Witness|Closure\/Reconstruction Witness|Closure Witness|Reconstruction Witness)\b/i.test(heading);
    const restorativeHeading=/^(?:Final\s+)?Restorative Response\b/i.test(heading);
    const closingHeading=/^(?:Final\s+)?Closing Formulation\b/i.test(heading);
    const headingLike=/^\s*(?:#{1,6}\s+|\*{1,2}|\[[^\]]+\]\s*$)/.test(raw)
      || /NOETIC FIELD EXECUTION/i.test(raw)
      || closureWitnessHeading
      || restorativeHeading
      || closingHeading;
    let match;
    if(/NOETIC FIELD EXECUTION/i.test(heading)) return {type:'banner',heading};
    if(headingLike&&/^Layer A\b/i.test(heading)&&/Compact\b/i.test(heading)&&/(DSL\/IR|Diagnostic Surface|Header)/i.test(heading)) return {type:'compact_layer_a',heading};
    if((match=heading.match(/^Burden\s+(\d+|B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\b(?:\s*(?::|—|-)\s*(.*))?/i))) return {type:'burden',heading,burden:sourceBurdenToken(match[1])};
    if(headingLike&&(match=heading.match(/^Layer A\b.*\bBurden\s+(\d+)\b/i))) return {type:'burden_setup',heading,burden:burden(match[1])};
    if(headingLike&&/Hidden premises operating/i.test(heading)) return {type:'hidden_premises',heading};
    if((match=heading.match(/^([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B([₀₁₂₃₄₅₆₇₈₉]+)(?:\[([^\]]+)\])?/))) return {type:'submove',heading,burden:burden(supNum(match[1]))};
    if(headingLike&&(match=heading.match(/^(Land|HOLD)\(([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B\)/i))) return {type:'land',heading,burden:burden(supNum(match[2]))};
    if(headingLike&&(match=heading.match(/^(Land|HOLD)\(B(\d+)\)/i))) return {type:'land',heading,burden:burden(match[2])};
    if(headingLike&&/^\[?\s*Mid-Reread Pressure\s*\]?$/i.test(heading)) return {type:'mid_reread_pressure',heading};
    if(closureWitnessHeading) return {type:'closure_witness',heading};
    if(restorativeHeading) return {type:'restorative_response',heading};
    if(closingHeading) return {type:'closing_formulation',heading};
    return null;
  }
  function sourceRenderSection(type,burdenId=''){
    if(type==='banner'||type==='compact_layer_a'||type==='closure_witness'||type==='mid_reread_pressure') return 'formal';
    if(['burden','burden_setup','hidden_premises','submove','land'].includes(type)) return burdenId?`burden:${burdenId}`:'burden';
    if(type==='restorative_response'||type==='closing_formulation') return 'restoration';
    return 'unassigned';
  }
  function sourceRenderLayer(type){
    if(['banner','compact_layer_a','closure_witness','mid_reread_pressure'].includes(type)) return 'technical';
    if(['burden','burden_setup','hidden_premises','submove','land','restorative_response','closing_formulation'].includes(type)) return 'public';
    return 'hidden';
  }
  function publicTitleForSourceSection(section){
    const type=section.type;
    if(type==='banner') return 'Runtime banner preserved in technical details';
    if(type==='compact_layer_a') return 'What structure was detected';
    if(type==='burden') return `Problem ${section.burden||''}`.trim();
    if(type==='burden_setup') return 'Problem setup from the output';
    if(type==='hidden_premises') return 'Hidden premises operating in this problem';
    if(type==='submove') return 'Owner-backed answer move';
    if(type==='land') return 'What this establishes';
    if(type==='mid_reread_pressure') return 'Follow-up pressure check';
    if(type==='closure_witness') return 'Formal reconstruction witness';
    if(type==='restorative_response') return 'Restorative Response';
    if(type==='closing_formulation') return 'Closing Formulation';
    return section.heading||type;
  }
  function technicalGlossForSourceSection(section){
    const type=section.type;
    if(type==='compact_layer_a') return 'Layer A / Compact DSL-IR';
    if(type==='burden_setup') return section.heading||'Layer A burden setup';
    if(type==='mid_reread_pressure') return `MRP(${section.burden||'ⁿB'}) source block`;
    if(type==='closure_witness') return 'Closure/Reconstruction Witness';
    if(type==='land') return `Land(${section.burden||'ⁿB'})`;
    if(type==='submove') return 'ⁿBᵢ[OPᵢ]';
    return section.heading||type;
  }
  function detectSourceSections(sourceText){
    const lines=String(sourceText||'').split(/\r?\n/);
    const markers=[];
    let currentBurden='';
    lines.forEach((line,index)=>{
      const kind=sourceHeadingKind(line);
      if(!kind) return;
      const lineNo=index+1;
      if(kind.type==='burden'&&kind.burden) currentBurden=kind.burden;
      const sectionBurden=kind.burden||currentBurden||'';
      markers.push({
        id:`${kind.type}:${sectionBurden||lineNo}:${lineNo}`,
        type:kind.type,
        heading:kind.heading,
        burden:sectionBurden,
        lineStart:lineNo
      });
    });
    return markers.map((marker,index)=>{
      const next=markers[index+1];
      const lineEnd=(next?next.lineStart-1:lines.length);
      const text=lines.slice(marker.lineStart-1,lineEnd).join('\n');
      const assignedRenderSection=sourceRenderSection(marker.type,marker.burden);
      return {...marker,lineEnd,text,assignedRenderSection,rendered:false,exportFile:'',reason:''};
    }).filter(section=>String(section.text||'').trim());
  }
  function extractBalancedJsonFrom(text,startIndex){
    const source=String(text||'');
    const start=source.slice(startIndex).search(/[\{\[]/);
    if(start<0) return '';
    const jsonStart=startIndex+start;
    const opener=source[jsonStart], closer=opener==='{'?'}':']';
    let depth=0, inString=false, escaped=false;
    for(let i=jsonStart;i<source.length;i++){
      const ch=source[i];
      if(inString){
        if(escaped) escaped=false;
        else if(ch==='\\') escaped=true;
        else if(ch==='"') inString=false;
        continue;
      }
      if(ch==='"'){inString=true; continue;}
      if(ch===opener) depth+=1;
      else if(ch===closer){
        depth-=1;
        if(depth===0) return source.slice(jsonStart,i+1);
      }
    }
    return '';
  }
  function extractEmbeddedFieldWitness(text){
    const source=String(text||'');
    const marker=source.search(/(?:^|\n)\s*(?:#+\s*)?field_witness\b/i);
    if(marker<0) return '';
    return extractBalancedJsonFrom(source,marker);
  }
  function supNum(raw){return [...String(raw||'')].map(c=>supToInt[c]||'').join('')||'0';}
  function subNum(raw){return [...String(raw||'')].map(c=>subToInt[c]||'').join('')||'0';}
  function burden(n){return [...String(n)].map(c=>intToSup[c]||'').join('')+'B';}
  function submove(b,s){return burden(b)+[...String(s)].map(c=>intToSub[c]||'').join('');}
  function canonicalizePublicNotation(text){
    return String(text||'')
      .replace(/\bB(\d+)_(\d+)\s*(?:\[([^\]\n]+)\])?/g,(m,b,s,op)=>`${submove(b,s)}${op?`[${op}]`:''}`)
      .replace(/\b(Land|HOLD)\(B(\d+)\)/gi,(m,op,b)=>`${op}(${burden(b)})`)
      .replace(/\bMRP\(B(\d+)\)/g,(m,b)=>`MRP(${burden(b)})`)
      .replace(/\bR\(H,Delta\)/g,'R(H,Δ)')
      .replace(/\bDelta\s+B(\d+)\b/gi,(m,b)=>`Δ${burden(b)}`)
      .replace(/\bB(\d+)\s*->\s*B(\d+)\b/g,(m,a,b)=>`${burden(a)} → ${burden(b)}`)
      .replace(/\bB(\d+)\b/g,(m,b)=>burden(b));
  }
  function addNode(model,node){if(!model.nodes[node.id]) model.nodes[node.id]=node;}
  function addEdge(model,edge){if(!model.edges.some(e=>e.source===edge.source&&e.target===edge.target&&e.kind===edge.kind)) model.edges.push(edge);}
  function normalizeBurden(raw){const s=String(raw||'').trim(); if(/^[⁰¹²³⁴⁵⁶⁷⁸⁹]+B$/.test(s)) return s; const m=s.match(/^B(\d+)$/); return m?burden(m[1]):s;}
  function warnLegacy(model,lineNo,alias,canonical){if(!model.legacyAliases.includes(alias)){model.legacyAliases.push(alias); model.warnings.push(`line ${lineNo}: parsed legacy alias ${alias}; public canonical notation preferred: ${canonical}`);}}
  function cleanMarkdownLabelLine(line){
    return String(line||'')
      .trim()
      .replace(/^\s*[-•]\s*/,'')
      .replace(/\*\*/g,'')
      .replace(/\s+/g,' ')
      .trim();
  }
  function tailSummary(line,end){
    return String(line).slice(end)
      .replace(/^\s*(?:\*\*)?\s*(?:[-–—]|:)\s*(?:\*\*)?\s*/,'')
      .replace(/^\*{1,2}|\*{1,2}$/g,'')
      .replace(/\s+/g,' ')
      .trim();
  }
  function afterColon(line){const i=String(line).indexOf(':'); return i>=0?String(line).slice(i+1).replace(/\s+/g,' ').trim():'';}
  function splitOutputZones(sourceText){
    const text=String(sourceText||'');
    const sourceSections=detectSourceSections(text);
    const closureMatch=text.match(/\n\s*(?:#+\s*)?(?:Closure\s*\/\s*Reconstruction Witness|Closure\/Reconstruction Witness|Closure Witness|Reconstruction Witness|Closure audit|field_witness)\b/i);
    const closureStart=closureMatch?closureMatch.index+1:text.length;
    const bodyProse=text.slice(0,closureStart);
    const fieldWitnessMatch=text.match(/\n\s*(?:#+\s*)?field_witness\b/i);
    const closureWitness=(fieldWitnessMatch&&fieldWitnessMatch.index+1>closureStart)
      ? text.slice(closureStart,fieldWitnessMatch.index+1)
      : text.slice(closureStart);
    const visibleOutputProse=fieldWitnessMatch?text.slice(0,fieldWitnessMatch.index+1):text;
    const restorativeSection=sourceSections.find(section=>section.type==='restorative_response');
    const closingSection=sourceSections.find(section=>section.type==='closing_formulation');
    const restorativeResponse=restorativeSection?stripSourceHeading(restorativeSection.text):extractBodySection(visibleOutputProse,'Restorative Response',['Closing Formulation','Closure/Reconstruction Witness','Closure Witness','Reconstruction Witness','field_witness']);
    const closingFormulation=closingSection?stripSourceHeading(closingSection.text):extractBodySection(visibleOutputProse,'Closing Formulation',['Closure/Reconstruction Witness','Closure Witness','Reconstruction Witness','field_witness']);
    return {
      bodyProse,
      closureWitness,
      sourceSections,
      bodyLineCount: bodyProse.split(/\r?\n/).length,
      embeddedFieldWitness: extractEmbeddedFieldWitness(text),
      restorativeResponse,
      closingFormulation
    };
  }

  function blankModel(){
    return {nodes:{},edges:[],errors:[],warnings:[],initialBurdens:[],burdens:[],bodyBurdens:[],ledger:{B_LA:[],B_MRP:[],B_total:[]},submoves:{},terminals:{},mrp:{},graphEdges:[],generatedBurdens:{},closureComplete:false,hasLayerA:false,hasBanner:false,hasRestoration:false,legacyAliases:[],witnessMismatches:[],witnessSources:{embedded:false,separate:false},collapseCertificate:{present:false,valid:false,errors:[],fields:{},payload:null},inputDigest:'pasted daee-epistemics output',fieldType:'not detected',caseProfile:'not detected',claimType:'not detected',diagnosis:'not detected',held:'not detected',collapse:{},restorationAim:'not detected',restorativeResponse:'',closingFormulation:'',sourceSections:[],zones:{bodyProse:'',closureWitness:''},bodyExtract:{burdenTitles:{},submoveTexts:{},submoveDetails:{},landTexts:{},rereadTexts:{},mrpTexts:{},mrpSourceTexts:{},burdenSetupTexts:{},burdenSetupHeadings:{},hiddenPremiseTexts:{},hiddenPremiseHeadings:{},compactLayerA:'',compactLayerAHeading:'',bannerText:'',closureWitnessText:''}};
  }

  function parseCollapseCertificate(certificateText){
    const raw=String(certificateText||'').trim();
    const empty={present:false,valid:false,errors:[],fields:{},payload:null};
    if(!raw) return empty;
    let payload;
    try{
      payload=JSON.parse(raw);
    }catch(err){
      return {present:true,valid:false,errors:[`certificate JSON invalid: ${err.message||err}`],fields:{},payload:null};
    }
    if(!payload || typeof payload!=='object' || Array.isArray(payload)){
      return {present:true,valid:false,errors:['certificate root must be a JSON object'],fields:{},payload:null};
    }
    const required=['input_fingerprint','collapse_positive','coverage_complete','diagnostic_completeness','divergence_state','curl_state','max_generation_depth','checker_version'];
    const errors=required.filter(key=>payload[key]===undefined || payload[key]===null || payload[key]==='').map(key=>`certificate missing ${key}`);
    const fields={
      input_fingerprint:String(payload.input_fingerprint||''),
      collapse_positive:payload.collapse_positive,
      coverage_complete:payload.coverage_complete,
      diagnostic_completeness:payload.diagnostic_completeness,
      divergence_state:String(payload.divergence_state||''),
      curl_state:String(payload.curl_state||''),
      max_generation_depth:payload.max_generation_depth,
      restoration_endpoint_reached:payload.restoration_endpoint_reached,
      verified_activations:Array.isArray(payload.verified_activations)?payload.verified_activations.map(String):[],
      checker_version:String(payload.checker_version||'')
    };
    return {present:true,valid:errors.length===0,errors,fields,payload};
  }

  function attachCollapseCertificate(model,certificateText){
    const certificate=parseCollapseCertificate(certificateText);
    model.collapseCertificate=certificate;
    if(!certificate.present) return;
    certificate.errors.forEach(error=>model.errors.push(`collapse certificate sidecar: ${error}`));
    model.warnings.push('browser certificate display is advisory; run the Python certificate-backed Output Grapher checker for B.1/B.2/B.4 agreement');
    const divergence=String(model.collapse?.divergence||model.collapse?.delDot||'').trim();
    const curl=String(model.collapse?.curl||model.collapse?.delCross||'').trim();
    if(certificate.valid && divergence && certificate.fields.divergence_state && !divergence.toLowerCase().includes(certificate.fields.divergence_state.toLowerCase())){
      model.warnings.push(`collapse certificate sidecar divergence_state=${certificate.fields.divergence_state} differs from visible graph divergence=${divergence}`);
    }
    if(certificate.valid && curl && certificate.fields.curl_state && !curl.toLowerCase().includes(certificate.fields.curl_state.toLowerCase())){
      model.warnings.push(`collapse certificate sidecar curl_state=${certificate.fields.curl_state} differs from visible graph curl=${curl}`);
    }
  }

  function lineBurdens(line,model,lineNo){
    const found=[];
    const canonicalIndices=new Set();
    for(const m of line.matchAll(/([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B(?![₀₁₂₃₄₅₆₇₈₉])/g)){
      if(!found.includes(m[0])) found.push(m[0]);
      canonicalIndices.add(String(Number(supNum(m[1]))));
    }
    const formalPairedContext=/^\s*(?:Landed delta|Route-gradient|R\(H,Δ\)|R\(H,Delta\)|Target|Field diagnostics|MRP resultant|LoopBreak)\s*:/i.test(line)
      || /\b(?:Delta\(B\d+\)|B_LA|B_MRP|B_total|field_witness)\b/i.test(line);
    const machinePayloadLine=/^\s*["{[\]},]/.test(line)
      && /"(?:B_LA|B_MRP|B_total|id|source|target|from|to|nodes|edges|terminal_states|owner_activations|coverage_proof|graph|body_ref|loopbreak_target)"\s*:/.test(line);
    for(const m of line.matchAll(/\bB(\d+)\b/g)){
      const t=burden(m[1]); if(!found.includes(t)) found.push(t);
      const isDeltaAlias=new RegExp(`\\\\bDelta\\\\(\\\\s*${m[0]}\\\\s*\\\\)`,'i').test(line);
      const isPaired=canonicalIndices.has(m[1]) || (formalPairedContext && isDeltaAlias);
      if(!isPaired && !machinePayloadLine){
        model.legacyAliases.push(m[0]); model.warnings.push(`line ${lineNo}: parsed legacy alias ${m[0]}; public canonical notation preferred`);
      }
    }
    for(const m of line.matchAll(/\bB([₀₁₂₃₄₅₆₇₈₉]+)\b/g)){
      model.warnings.push(`line ${lineNo}: ${m[0]} looks like subscript burden notation; use superscript-before-B for burdens`);
    }
    return found;
  }
  function cleanVisibleLedgerSegment(segment){
    return String(segment||'')
      .replace(/\[generated-by:\s*MRP\([^\)]*\)\]/ig,'')
      .replace(/\bMRP\([^\)]*\)/ig,'')
      .replace(/\b(?:B_|𝔅_)(?:LA|MRP|total)\b/ig,'');
  }

  function ensureMrp(model,b,lineNo){
    const id=`MRP(${b})`;
    if(!model.mrp[b]) model.mrp[b]={id,line:lineNo,routes:[],resultTypes:[],edges:[],pressure:[],routeGradient:'',divergence:'',curl:''};
    addNode(model,{id,kind:'mrp',label:id,line:lineNo,excerpt:''});
    return model.mrp[b];
  }
  function pushBodyMrp(model,b,line){
    if(!b) return;
    if(!model.bodyExtract.mrpTexts[b]) model.bodyExtract.mrpTexts[b]=[];
    const cleaned=cleanParsed(line);
    if(cleaned && !model.bodyExtract.mrpTexts[b].includes(cleaned)) model.bodyExtract.mrpTexts[b].push(cleaned);
  }
  function pushSubmoveDetail(model,sm,key,line){
    if(!sm||!key) return;
    if(!model.bodyExtract.submoveDetails[sm]) model.bodyExtract.submoveDetails[sm]={};
    const cleaned=canonicalizePublicNotation(cleanParsed(line));
    if(!cleaned) return;
    if(key==='body'){
      const existing=model.bodyExtract.submoveDetails[sm][key]||'';
      if(!existing.includes(cleaned)){
        model.bodyExtract.submoveDetails[sm][key]=existing?`${existing}\n${cleaned}`:cleaned;
      }
      return;
    }
    model.bodyExtract.submoveDetails[sm][key]=cleaned;
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

  function parseOutput(text,witnessText,certificateText){
    const model=blankModel();
    addNode(model,{id:'input',kind:'input',label:'input',line:0,excerpt:'pasted daee-epistemics output'});
    const sourceText=String(text||'');
    const zones=splitOutputZones(sourceText);
    model.zones={bodyProse:zones.bodyProse,closureWitness:zones.closureWitness};
    model.sourceSections=zones.sourceSections||[];
    model.witnessSources={embedded:Boolean(zones.embeddedFieldWitness),separate:Boolean(String(witnessText||'').trim())};
    model.restorativeResponse=zones.restorativeResponse;
    model.closingFormulation=zones.closingFormulation;
    const fieldWitnessStart=sourceText.search(/(?:^|\n)\s*(?:#+\s*)?field_witness\b/i);
    const fieldWitnessLine=fieldWitnessStart>=0?sourceText.slice(0,fieldWitnessStart).split('\n').length+1:Infinity;
    (model.sourceSections||[]).forEach(section=>{
      const body=stripSourceHeading(section.text);
      if(section.type==='banner') model.bodyExtract.bannerText=body||cleanVisibleProseBlock(section.text);
      if(section.type==='compact_layer_a'){model.bodyExtract.compactLayerA=body; model.bodyExtract.compactLayerAHeading=section.heading;}
      if(section.type==='burden_setup'&&section.burden){model.bodyExtract.burdenSetupTexts[section.burden]=body; model.bodyExtract.burdenSetupHeadings[section.burden]=section.heading;}
      if(section.type==='hidden_premises'&&section.burden){model.bodyExtract.hiddenPremiseTexts[section.burden]=body; model.bodyExtract.hiddenPremiseHeadings[section.burden]=section.heading;}
      if(section.type==='mid_reread_pressure'&&section.burden) model.bodyExtract.mrpSourceTexts[section.burden]=body;
      if(section.type==='closure_witness') model.bodyExtract.closureWitnessText=body;
    });
    if(!model.bodyExtract.closureWitnessText&&zones.closureWitness){
      model.bodyExtract.closureWitnessText=stripSourceHeading(zones.closureWitness);
    }
    const lines=sourceText.split(/\r?\n/);
    let lastBurden='', currentMrpBurden='', pendingMrpBlock=false, currentSubmove='';
    const routeRecords=[];
    lines.forEach((line,idx)=>{
      const lineNo=idx+1, trimmed=line.trim();
      if(lineNo>=fieldWitnessLine) return;
      const inBody=lineNo<=zones.bodyLineCount;
      if(!trimmed) return;
      if(/^(?:#{1,6}\s*)?(?:Restorative Response|Closing Formulation|Closure\/Reconstruction Witness|Closure Witness|Reconstruction Witness)\b/i.test(trimmed)){
        pendingMrpBlock=false;
        currentMrpBurden='';
      }
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
      const routeGradient=line.match(/Route-gradient\s*:\s*([^;\n]+)/i); if(routeGradient) model.collapse.routeGradient=routeGradient[1].trim();
      const delDot=line.match(/(?:del-dot(?:\s*\(?T\)?)?|∇·T|∇·B)\s*:\s*([^;\n]+)/i); if(delDot) model.collapse.delDot=delDot[1].trim();
      const delCross=line.match(/(?:del-cross(?:\s*\(?T\)?)?|∇×T|∇×κ)\s*:\s*([^;\n]+)/i); if(delCross) model.collapse.delCross=delCross[1].trim();
      const closure=line.match(/𝒞\(Ψᴺ\)\s*:\s*([^;\n]+)/i); if(closure) model.collapse.coverage=closure[1].trim();
      const tLang=line.match(/T_lang\s*:\s*([^\n]+)/i); if(tLang) model.collapse.tLang=tLang[1].trim();
      const restAim=line.match(/Restoration (?:aim|target):\s*(.+)$/i); if(restAim){model.restorationAim=cleanParsed(restAim[1]); model.hasRestoration=true;}
      const burdens=lineBurdens(line,model,lineNo);
      const ledgerLine=line.match(/^\s*(?:[-*]\s*)?(?:B_|𝔅_)(LA|MRP|total)\b(?:\s*\(\s*(?:B_|𝔅_)(?:LA|MRP|total)\s*\))?\s*(?:=|:)\s*(.*)$/i);
      if(ledgerLine){
        const key=ledgerLine[1].toLowerCase()==='la'?'B_LA':ledgerLine[1].toLowerCase()==='mrp'?'B_MRP':'B_total';
        let ledgerSegment=ledgerLine[2]||'';
        const nextLedger=ledgerSegment.search(/\b(?:B_|𝔅_)(?:LA|MRP|total)\b/i);
        if(nextLedger>0) ledgerSegment=ledgerSegment.slice(0,nextLedger);
        ledgerSegment=cleanVisibleLedgerSegment(ledgerSegment);
        const ledgerBurdens=lineBurdens(ledgerSegment,model,lineNo);
        ledgerBurdens.forEach(b=>{if(!model.ledger[key].includes(b)) model.ledger[key].push(b);});
        if(key==='B_LA') ledgerBurdens.forEach(b=>{if(!model.initialBurdens.includes(b)) model.initialBurdens.push(b);});
      }
      const headingMatch=trimmed.match(/^(?:#+\s*)?Burden\s+(\d+|B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\b/i);
      const headingBurden=headingMatch?sourceBurdenToken(headingMatch[1]):'';
      if(headingMatch){burdens.splice(0,burdens.length,headingBurden,...burdens.filter(b=>b!==headingBurden));}
      const initial=/^\s*(?:[-*]\s*)?(?:Initial burden set|initial burden inventory|initial burdens?|burden inventory|initial set|held\/live burden)\s*[:=]/i.test(line);
      const heading=/^(#+\s*)?(Burden\s+(?:\d+|B\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\b|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\b)/.test(trimmed);
      const mrp=line.match(/\bMRP\(([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B\)/);
      const asciiGenerated=line.match(/\bMRP\(B(\d+)\)/);
      const generatedProvenance=line.includes('generated-by')&&(mrp||asciiGenerated);
      burdens.forEach(b=>{
        if(!model.burdens.includes(b)) model.burdens.push(b);
        if(inBody&&!model.bodyBurdens.includes(b)) model.bodyBurdens.push(b);
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:trimmed.slice(0,220)});
        if(initial&&!generatedProvenance&&!model.initialBurdens.includes(b)) model.initialBurdens.push(b);
        if(heading&&b===headingBurden){
          lastBurden=b;
          currentSubmove='';
          const title=tailSummary(trimmed, headingMatch?headingMatch[0].length:0);
          if(title && model.nodes[b]) model.nodes[b].label=`${b} — ${title.replace(/\s*\[generated-by:.+?\]\s*/i,'').slice(0,120)}`;
          if(inBody && title) model.bodyExtract.burdenTitles[b]=cleanParsed(title.replace(/\s*\[generated-by:.+?\]\s*/i,''));
        }
      });
      for(const m of line.matchAll(/([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B([₀₁₂₃₄₅₆₇₈₉]+)(?:\[([^\]\n]+)\])?/g)){
        const b=burden(supNum(m[1])), sm=submove(supNum(m[1]),subNum(m[2])), owner=(m[3]||'').trim();
        const summary=tailSummary(trimmed,m[0].length);
        addNode(model,{id:sm,kind:'submove',label:summary?`${sm}[${owner||'OP'}] — ${summary}`:sm,line:lineNo,excerpt:trimmed.slice(0,220),owner,parent:b,result:summary});
        if(inBody && summary) model.bodyExtract.submoveTexts[sm]=cleanParsed(summary);
        if(inBody) pushSubmoveDetail(model,sm,'heading',summary||trimmed);
        if(!model.submoves[b]) model.submoves[b]=[];
        if(!model.submoves[b].includes(sm)) model.submoves[b].push(sm);
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:''});
        addEdge(model,{source:b,target:sm,kind:'burden-submove',line:lineNo,excerpt:trimmed.slice(0,220)});
        currentSubmove=sm;
      }
      for(const m of line.matchAll(/\bB(\d+)_(\d+)\s*(?:\[([^\]\n]+)\])?/g)){
        const b=burden(m[1]), sm=submove(m[1],m[2]), owner=(m[3]||'').trim();
        warnLegacy(model,lineNo,m[0],owner?`${sm}[${owner}]`:sm);
        const summary=tailSummary(trimmed,m[0].length);
        if(!model.burdens.includes(b)) model.burdens.push(b);
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:trimmed.slice(0,220)});
        addNode(model,{id:sm,kind:'submove',label:summary?`${sm}[${owner||'OP'}] — ${summary}`:sm,line:lineNo,excerpt:trimmed.slice(0,220),owner,parent:b,result:summary});
        if(inBody && summary) model.bodyExtract.submoveTexts[sm]=cleanParsed(summary);
        if(inBody) pushSubmoveDetail(model,sm,'heading',summary||trimmed);
        if(!model.submoves[b]) model.submoves[b]=[];
        if(!model.submoves[b].includes(sm)) model.submoves[b].push(sm);
        addEdge(model,{source:b,target:sm,kind:'burden-submove',line:lineNo,excerpt:trimmed.slice(0,220)});
        lastBurden=b;
        currentSubmove=sm;
      }
      if(inBody&&currentSubmove){
        const detailLine=cleanMarkdownLabelLine(trimmed);
        const targetDetail=detailLine.match(/^Target:\s*(.+)$/i);
        const operationDetail=detailLine.match(/^(?:Operation|What it does):\s*(.+)$/i);
        const resultDetail=detailLine.match(/^(?:Result\/state-change|Result):\s*(.+)$/i);
        const contributionDetail=detailLine.match(/^Contribution-to-Land\([^)]+\):\s*(.+)$/i);
        if(targetDetail) pushSubmoveDetail(model,currentSubmove,'target',targetDetail[1]);
        if(operationDetail) pushSubmoveDetail(model,currentSubmove,'operation',operationDetail[1]);
        if(resultDetail) pushSubmoveDetail(model,currentSubmove,'result',resultDetail[1]);
        if(contributionDetail) pushSubmoveDetail(model,currentSubmove,'contribution',contributionDetail[1]);
        const isDetailLine=targetDetail||operationDetail||resultDetail||contributionDetail;
        const isSubmoveHeading=/^\s*(?:#{1,6}\s*)?(?:[-*]\s*)?(?:B\d+_\d+|[^\s]+B[^\s]*\[[^\]]+\])/.test(trimmed);
        const isStructuralLine=/^\s*(?:#{1,6}\s*)?(?:Burden\b|Layer\b|Land\(|HOLD\(|\[Mid-Reread Pressure\]|R\(H,|MRP\(|Route:|Closure\/Reconstruction Witness|Final Restorative Response|Restorative Response|Closing Formulation|field_witness\b|Initial burden set|Terminal states|Burden dependency graph|MRP resultants|Graph delta:|Field diagnostics:|Finding:|Pressure activations:|Boundary:)/i.test(trimmed);
        if(!isDetailLine && !isSubmoveHeading && !isStructuralLine && trimmed){
          pushSubmoveDetail(model,currentSubmove,'body',trimmed);
        }
      }
      const terminalLandLine=cleanMarkdownLabelLine(trimmed).match(/^\s*(?:[-*]\s*)?(?:\*\*)?(Land|HOLD)\(([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B\)/i);
      const land=terminalLandLine;
      if(land){
        currentSubmove='';
        const b=burden(supNum(land[2])), term=land[1].toUpperCase()==='HOLD'?'HOLD':'Land', id=`${term}(${b})`;
        const summary=tailSummary(trimmed,land.index+land[0].length);
        if(inBody && summary) model.bodyExtract.landTexts[b]=cleanParsed(summary);
        model.terminals[b]=term; addNode(model,{id,kind:term==='Land'?'land':'terminal',label:summary?`${id} — ${summary}`:id,line:lineNo,excerpt:trimmed,status:term,parent:b,result:summary});
        addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:''}); addEdge(model,{source:b,target:id,kind:'burden-terminal',line:lineNo,excerpt:trimmed}); lastBurden=b;
      }else{
        const legacyLand=cleanMarkdownLabelLine(trimmed).match(/^\s*(?:[-*]\s*)?(?:\*\*)?(Land|HOLD)\(B(\d+)\)/i);
        if(legacyLand){
          currentSubmove='';
          const b=burden(legacyLand[2]), term=legacyLand[1].toUpperCase()==='HOLD'?'HOLD':'Land', id=`${term}(${b})`;
          const summary=tailSummary(trimmed,legacyLand.index+legacyLand[0].length);
          if(inBody && summary) model.bodyExtract.landTexts[b]=cleanParsed(summary);
          warnLegacy(model,lineNo,legacyLand[0],id);
          model.terminals[b]=term; addNode(model,{id,kind:term==='Land'?'land':'terminal',label:summary?`${id} — ${summary}`:id,line:lineNo,excerpt:trimmed,status:term,parent:b,result:summary});
          addNode(model,{id:b,kind:'burden',label:b,line:lineNo,excerpt:''}); addEdge(model,{source:b,target:id,kind:'burden-terminal',line:lineNo,excerpt:trimmed}); lastBurden=b;
        }
      }
      if((line.includes('R(H,Δ)')||line.includes('R(H,Delta)')) && !/^\s*Reread:\s*/i.test(line)){
        currentSubmove='';
        if(line.includes('R(H,Delta)')) model.warnings.push(`line ${lineNo}: parsed legacy alias R(H,Delta); use R(H,Δ)`);
        const rereadTarget=line.match(/R\(H,Delta\)\s*B(\d+)\b/i);
        const b=(rereadTarget?burden(rereadTarget[1]):burdens[0]||lastBurden), id=`R(H,Δ)@${b||lineNo}`;
        if(rereadTarget) warnLegacy(model,lineNo,`R(H,Delta) B${rereadTarget[1]}`,`R(H,Δ)@${b}`);
        const summary=tailSummary(trimmed,line.search(/R\(H,(?:Δ|Delta)\)/)+(/R\(H,Delta\)/.test(line)?10:6));
        if(inBody && summary && b) model.bodyExtract.rereadTexts[b]=cleanParsed(summary);
        addNode(model,{id,kind:'reread',label:summary?`R(H,Δ) — ${summary}`:'R(H,Δ)',line:lineNo,excerpt:trimmed,parent:b,result:summary});
        if(b) addEdge(model,{source:`Land(${b})`,target:id,kind:'land-reread',line:lineNo,excerpt:trimmed});
      }
      if(/\[\s*Mid-Reread Pressure\s*\]/i.test(line)){pendingMrpBlock=true; currentMrpBurden=''; currentSubmove='';}
      const targetLine=cleanMarkdownLabelLine(trimmed);
      const target=targetLine.match(/^Target:\s*(?:B(\d+)|([⁰¹²³⁴⁵⁶⁷⁸⁹]+)B)\b/i);
      if(pendingMrpBlock&&target){const b=target[1]?burden(target[1]):burden(supNum(target[2])); currentMrpBurden=b; ensureMrp(model,b,lineNo); if(inBody) pushBodyMrp(model,b,trimmed); addEdge(model,{source:`R(H,Δ)@${b}`,target:`MRP(${b})`,kind:'reread-mrp',line:lineNo,excerpt:trimmed}); if(target[1]) warnLegacy(model,lineNo,target[0].trim(),`MRP(${b})`);}
      if(mrp&&!line.includes('generated-by')){const b=burden(supNum(mrp[1])); currentMrpBurden=b; ensureMrp(model,b,lineNo); if(inBody) pushBodyMrp(model,b,trimmed); addEdge(model,{source:`R(H,Δ)@${b}`,target:`MRP(${b})`,kind:'reread-mrp',line:lineNo,excerpt:trimmed});}
      if(line.includes('generated-by')&&(mrp||asciiGenerated)){
        const sourceBurden=mrp?burden(supNum(mrp[1])):burden(asciiGenerated[1]);
        const generatedTarget=headingBurden || (lastBurden&&lastBurden!==sourceBurden?lastBurden:'') || burdens.find(b=>b!==sourceBurden);
        if(generatedTarget){
          model.generatedBurdens[generatedTarget]=`MRP(${sourceBurden})`;
          if(model.nodes[generatedTarget]) model.nodes[generatedTarget].generatedBy=model.generatedBurdens[generatedTarget];
        }
      }
      const asciiMrpLine=line.match(/^\s*MRP\(B(\d+)\)/i);
      if(asciiMrpLine){const b=burden(asciiMrpLine[1]); currentMrpBurden=b; ensureMrp(model,b,lineNo); if(inBody) pushBodyMrp(model,b,trimmed); warnLegacy(model,lineNo,asciiMrpLine[0].trim(),`MRP(${b})`);}
      if(pendingMrpBlock&&!currentMrpBurden&&lastBurden&&/\b(Result|What remained|Why it matters|Route-gradient|Finding|MRP route result type|MRP resultant|Graph movement|Graph delta|Field diagnostics|R\(H,|Route:)/i.test(line)){
        currentMrpBurden=lastBurden;
        ensureMrp(model,currentMrpBurden,lineNo);
        addEdge(model,{source:`R(H,Δ)@${currentMrpBurden}`,target:`MRP(${currentMrpBurden})`,kind:'reread-mrp',line:lineNo,excerpt:trimmed});
      }
      if(pendingMrpBlock&&currentMrpBurden&&/^\s*(?:Result|What remained|Why it matters|Graph movement|Graph delta|Field diagnostics)\s*:/i.test(cleanMarkdownLabelLine(trimmed))){
        pushBodyMrp(model,currentMrpBurden,trimmed);
      }
      const rt=line.match(/\b(held_burden_activation|generated_burden_instantiation|no_new_resultant|loopbreak|hold_partial)\b/);
      if(rt && currentMrpBurden){ ensureMrp(model,currentMrpBurden,lineNo).resultTypes.push(rt[1]); if(inBody) pushBodyMrp(model,currentMrpBurden,trimmed); }
      if(rt && currentMrpBurden) refreshMrpLabel(model,currentMrpBurden);
      const asciiResult=line.match(/\bMRP resultant:\s*B(\d+)\s+licenses\s*(STOP|HOLD|RECURSE|LoopBreak)/i);
      if(asciiResult){
        const b=burden(asciiResult[1]), value=asciiResult[2], id=`Route:${value}@${b}`;
        currentMrpBurden=b; const data=ensureMrp(model,b,lineNo); data.pressure.push(trimmed); if(inBody) pushBodyMrp(model,b,trimmed); if(!data.routes.includes(value)) data.routes.push(value);
        addNode(model,{id,kind:'terminal',label:`Route: ${value} — ${trimmed.replace(/^MRP resultant:\s*/i,'').slice(0,90)}`,line:lineNo,excerpt:trimmed,route:value,parent:b,result:trimmed}); addEdge(model,{source:`MRP(${b})`,target:id,kind:'mrp-route',line:lineNo,excerpt:trimmed});
        refreshMrpLabel(model,b);
      }
      const finding=line.match(/\b(Finding|MRP resultant|Resultant|Result type):\s*([^\n;]+)/i);
      if(finding && currentMrpBurden){ensureMrp(model,currentMrpBurden,lineNo).pressure.push(finding[2].trim()); if(inBody) pushBodyMrp(model,currentMrpBurden,trimmed); refreshMrpLabel(model,currentMrpBurden);}
      const activeMrp=currentMrpBurden || (pendingMrpBlock&&lastBurden?lastBurden:'');
      if(activeMrp&&pendingMrpBlock){
        const rg=line.match(/^\s*Route-gradient\s*:\s*(.+)$/i);
        const div=line.match(/(?:\u2207\u00b7[BT]|del[- ]dot\s*[BT])\s*:\s*([^;\n]+)/i);
        const curl=line.match(/(?:\u2207(?:\u00d7|x)(?:\u03ba|kappa|T)|del[- ]cross\s*(?:kappa|T))\s*:\s*([^;\n]+)/i);
        if(rg){currentMrpBurden=activeMrp; ensureMrp(model,activeMrp,lineNo).routeGradient=rg[1].trim();}
        if(div){currentMrpBurden=activeMrp; ensureMrp(model,activeMrp,lineNo).divergence=String(div[1]||'').split(/[\/;,]/)[0].trim();}
        if(curl){currentMrpBurden=activeMrp; ensureMrp(model,activeMrp,lineNo).curl=String(curl[1]||'').split(/[\/;,]/)[0].trim();}
      }
      const route=line.match(/\bRoute(?:\*\*)?\s*:\s*(?:\*\*)?\s*(STOP|HOLD|RECURSE|LoopBreak(?:\(∇×T\))?|LoopBreak)/i);
      if(route){
        const b=currentMrpBurden||burdens[0]||lastBurden, value=route[1], id=`Route:${value}@${b||lineNo}`;
        routeRecords.push({burden:b,route:value,line:lineNo}); if(inBody && b) pushBodyMrp(model,b,trimmed); addNode(model,{id,kind:'terminal',label:`Route: ${value} — ${tailSummary(trimmed, route.index+route[0].length).slice(0,90)}`,line:lineNo,excerpt:trimmed,route:value,parent:b});
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
        const s=burden(supNum(m[1])), t=burden(supNum(m[2])); recordDependency(model,s,t,lineNo,trimmed,(isDependencySummary||!inBody)?'':currentMrpBurden);
      }
      for(const m of line.matchAll(/\bB(\d+)\s*->\s*B(\d+)\b/g)){
        const s=burden(m[1]), t=burden(m[2]); warnLegacy(model,lineNo,m[0],`${s} → ${t}`); recordDependency(model,s,t,lineNo,trimmed,(isDependencySummary||!inBody)?'':currentMrpBurden);
      }
      if(isDependencySummary&&line.includes('->')&&!line.includes(';')){
        const chain=[...line.matchAll(/\bB(\d+)\b/g)].map(m=>burden(m[1]));
        for(let i=0;i<chain.length-1;i++) recordDependency(model,chain[i],chain[i+1],lineNo,trimmed,'');
      }
    });
    model.burdens=[...new Set(model.burdens)].sort((a,b)=>Number(supNum(a[0]))-Number(supNum(b[0])));
    validate(model,lines,routeRecords);
    if(zones.embeddedFieldWitness) compareWitness(model,zones.embeddedFieldWitness,'embedded field_witness');
    if(String(witnessText||'').trim()) compareWitness(model,witnessText,'separate field_witness');
    compareEmbeddedAndSeparateWitness(model,zones.embeddedFieldWitness,witnessText);
    attachCollapseCertificate(model,certificateText);
    return model;
  }

  const HIGH_LEVERAGE_HELD_ROUTE_RE=/(?:independent lordship|canon[- ]wide|textual criticism|epistemology of canon|full Christology|source\/proof-stack|source authority|proof[- ]stack|mystery shield|worldview recoil|moral tribunal shift|authority-order|predication|source-worldview|Christology|theology|hiddenness|metaphysics|epistemology|identity\/worldview|historical\/transmission|transmission|source-authority|analogy[- ]stack|shubha|shakk|rayb|moral protest|secular moral|source[- ]order|criterion)/i;
  const UNROUTED_HELD_ROUTE_RE=/(?:not released|unreleased|held beyond|beyond prompt|beyond bounded claim|held outside scope|not worked)/i;
  const TERMINAL_CLOSURE_RE=/(?:STOP|closure|complete|collapse achieved|no remaining live problem)/i;
  const ROUTING_OR_BOUNDARY_PROOF_RE=/(?:held_burden_activation|generated_burden_instantiation|HOLD|PARTIAL|coverage_complete\s*=\s*false|non[- ]load[- ]bearing|not load[- ]bearing|not needed for (?:this|the) (?:scoped|bounded|local) claim|scope gate|local closure only|partial closure)/i;
  const HIGH_MASS_GENERATED_RE=/(?:source[- ]worldview|worldview|proof[- ]stack|textual|canon|Christology|independent lordship|hidden premise|dependency radius|source authority|authority-order|predication|category|moral tribunal|worship[- ]worthiness|hiddenness|coercive guidance|accountability|mystery shield|immunity|recoil|epistemology|framework|bounded-answer)/i;
  const OPERATION_MECHANISM_RE=/(?:hidden premise|escape route|smuggl|burden shift|proof[- ]stack|source[- ]order|source authority|authority frame|scope gate|bounded claim|local claim|total[- ]system|whole[- ]system|exhaust|reopen|would require|unworked held route|non[- ]load[- ]bearing|predicate|predication|category|dependency|criterion|immunity|recoil|framework|broader material|held material|state change|delta)/i;
  const OPERATION_SCOPE_RE=/(?:original (?:local )?claim|local (?:claim|argument|reply|refutation|closure)|specific (?:reply|argument|claim)|bounded (?:claim|refutation|closure|answer)|scoped (?:claim|closure)|total[- ]system|whole[- ]system|entire doctrine|every (?:text|possible route|doctrine)|broader (?:system|framework|doctrine|material))/i;
  const OPERATION_TEST_RE=/(?:hidden premise|new premise|unargued|unstated|must be (?:stated|tested|carried)|would require|requires (?:a )?(?:new burden|fixed|stable|criterion)|reopen(?:ed|ing)?|reopen condition|admissible only if|cannot be smuggled|smuggled)/i;
  const OPERATION_FAILURE_RE=/(?:cannot (?:rescue|repair|retroactively|function)|not a rescue|does not (?:establish|license|derive)|burden shift|burden shifting|proof[- ]carousel|evasion|not evidence|barred|blocked|fails because)/i;
  const OPERATION_ACTION_RE=/(?:expose|distinguish|block|repair|trace|ground|test|separate|prevent|audit|apply|identify|reclassify|refuse|sequence|show why|demonstrate|bar|route|bind|isolate|restore|reorient|re-home|honor|define|vet|reconstruct|dissolve|triage|clarify|prioritize|anchor|map|bound|shifts?|smuggl|reopen|supplies|explains|cannot retroactively|does not mean|answered according)/i;
  const STATE_CHANGE_RE=/(?:blocked|blocks|bounded|boundary[- ]bounded|removed|removes|separated|separates|held|released|routed|licensed|licenses|license|closed|restored|reoriented|scoped STOP|STOP[- ]eligible|HOLD\/PARTIAL|reopen conditions|future distinct burdens|admissible|barred|prevents|cannot rescue|cannot act as hidden support|must be stated as (?:a )?new burden|requires a new burden|becomes a new burden|new burden and tested|exposed|demoted|invalidated|withheld|narrowed|converted|classified|refused|denied|self[- ]undercut|loses|loss|severed|separated from|non[- ]load[- ]bearing|not load[- ]bearing|lands|landed|cleared|state change|state delta|delta)/i;
  const OWNER_OPERATION_SHAPES=[
    {owner:/\bFPD\b|foreign[- ]premise|imported[- ]premise/i, work:/(?:hidden|foreign|imported|unstated|smuggled|impossible).{0,120}(?:premise|criterion|court|tribunal|support|route)/i},
    {owner:/source[- ]status|authority[- ]order|\bV10\b|transmission|testimony/i, work:/(?:source|authority|transmission|content|support|override|govern|ledger|hidden support|source[- ]order|source-use|source function|source-prestige|source accumulation|proof[- ]text|citation|cited|held material)/i},
    {owner:/\bP7\b|boundedness|stop/i, work:/(?:STOP|HOLD|PARTIAL|bounded|scoped|closure|reopen|proof[- ]carousel|stop condition|held[- ]route|boundary)/i},
    {owner:/\bM8\b|reductio|consequence/i, work:/(?:trace|consequence|if .* then|if allowed|self[- ]undermin|evasion|unacceptable|what follows|proof[- ]carousel)/i},
    {owner:/\bM9\b|predication|predicate|category/i, work:/(?:predicate|predication|category|referent|semantic|identity|transfer|mode|sense|level)/i},
    {owner:/do[- ]attribute[- ]precision|attribute[- ]precision/i, work:/(?:person\/nature|attribute|multiplicity|model identification|composition|dependence|category confusion|person-level|nature-level)/i},
    {owner:/do[- ]christian[- ]extensions|Christian theological pressure|Trinitarian/i, work:/(?:Christian theological pressure|Trinitarian model|Trinity model|model identification|model-shift|identity-style|social Trinitarian|relative identity|mystery|person\/nature|DO-1[1-4]|canon authority|coherence burden|Christian overlay)/i},
    {owner:/do[- ]second[- ]loop/i, work:/(?:DO[- ]second[- ]loop|hujjah|á¸¥ujjah|warning|record|prophetic authority|moral protest|Great Pumpkin|cognitive science|CSR|HADD|necessary-knowledge|accountability|guidance architecture|family-local load floor)/i},
    {owner:/doubt[- ]vs[- ]skepticism|skepticism/i, work:/(?:doubt[- ]vs[- ]skepticism|normal doubt|skepticism as (?:ideology|methodology)|skeptical methodology|evidence demand|absence of evidence|modal veto|bare imagined possibility|alternative description|anomaly|background commitments|burden[- ]of[- ]proof inversion|total possibility[- ]exhaustion|doubt function)/i},
    {owner:/proof[- ]method[- ]audit|method[- ]audit/i, work:/(?:proof[- ]method|proof grammar|proof family|formal derivation|logic tree|inferential standard|what the proof establishes|premise strength|invalid inference)/i},
    {owner:/\bM7\b|definition/i, work:/(?:define|definition|term|meaning|anchor|equivocation|relation|category)/i},
    {owner:/\bM1-P\b|performative/i, work:/(?:performative|act of making|presupposes|cannot ground|denies|self[- ]refutation)/i},
    {owner:/\bM1\b|self[- ]refutation/i, work:/(?:self[- ]refut|contradiction|own standard|internal standard|inconsistent)/i},
    {owner:/\bM3\b|orphaned[- ]intuition|moral intuition/i, work:/(?:orphaned intuition|ungrounded intuition|intuition without|moral intuition|orphaned moral|ground is orphaned|intuition has a home|moral deliverance|moral recognition|recognition remains honored|retained while its ground)/i},
    {owner:/\bV2\b|reason reconstruction/i, work:/(?:reason|rationality|governing conception|faculty|truth|sovereign|criterion|type reason|reason as (?:access|recognition|recognizer)|epistemic role|order of discovery|order of reality)/i},
    {owner:/\bV3\b|regress/i, work:/(?:regress|infinite|foundation|ground|terminates|dissolve)/i},
    {owner:/\bV7\b|\bV11\b|taqlid|taḥqīq|taqlīd/i, work:/(?:taqlid|taqlīd|blind following|inherited|transition|taḥqīq|verification)/i},
    {owner:/\bV8\b|bilā kayf|attribute/i, work:/(?:attribute|bilā kayf|mystery|modality|without asking how|anti[- ]rational)/i},
    {owner:/\bV9\b|necessary[- ]knowledge|fitri|fiṭr/i, work:/(?:necessary knowledge|fiṭr|fitr|priority|lower[- ]order|destabilization|hujjah|clarity)/i},
    {owner:/\bV12\b|tamānuʿ|tamanu/i, work:/(?:divine plurality|lordship|independent|tamānu|exhaustion|mutual prevention)/i},
    {owner:/\bE[1-4]\b|evidence|inferential|cumulative|cross[- ]cultural/i, work:/(?:evidence|inferential|criterion|cumulative|cross[- ]cultural|case|support|rule)/i},
    {owner:/\bF[1-3]\b|supra[- ]rational|volitional|practice/i, work:/(?:supra[- ]rational|anti[- ]rational|volitional|practice|access|orientation|will)/i},
    {owner:/\bR[1-3]\b|internalist|reminder|warranted/i, work:/(?:internalist|criterion|reminder|warrant|basic belief|recognition|fitr)/i},
    {owner:/\bP1\b|restoration|fiṭrah|fitrah/i, work:/(?:restore|restored|restoration|positive orientation|fiṭr|fitr|tawḥīd|tawhid|da.?ee|mercy|justice|sound orientation|capacity, access|access, clarity|clear warning|honest (?:engagement|inquiry)|humane criterion)/i},
    {owner:/\bP2\b|objection mapping/i, work:/(?:map|objection|pressure|route|structure|premise|burden)/i},
    {owner:/\bP3\b|reason.*revelation|revelation.*reason/i, work:/(?:reason|revelation|tension|source order|authority|scripture)/i},
    {owner:/\bP4\b|maieutic/i, work:/(?:question|elicit|maieutic|draw out|admission|already sees)/i},
    {owner:/\bP5\b|already[- ]believing/i, work:/(?:already[- ]believing|internal repair|implicit|commitment|presupposes)/i},
    {owner:/\bP6\b|ʿaqīdah|aqidah/i, work:/(?:universal|aqidah|ʿaqīdah|principle|doctrine|norm)/i},
  ];
  const GENERIC_OWNER_ACTIVATION_RE=/(?:validated state|operation mechanism|state change|mechanism|criterion|ground|source|authority|predicate|definition|consequence|reconstruct|dissolve|vet|triage|restore|route|bound|test|separate|block|trace|repair|anchor|map|clarify|transition|priority|warrant|evidence|orientation|result follows)/i;
  function ownerSpecificOperationActivated(ownerText,combined){
    const matched=OWNER_OPERATION_SHAPES.filter(shape=>shape.owner.test(ownerText));
    if(matched.length) return matched.some(shape=>shape.work.test(combined));
    return GENERIC_OWNER_ACTIVATION_RE.test(combined);
  }
  function splitMrpSourceBlocks(lines){
    const blocks=[];
    for(let i=0;i<lines.length;i++){
      if(!/^\s*\[Mid-Reread Pressure\]\s*$/i.test(lines[i])) continue;
      const start=i+1;
      let end=lines.length;
      for(let j=start;j<lines.length;j++){
        if(/^\s*(?:#{1,6}\s*)?(?:Burden\s+\d+|Restorative Response|Closing Formulation|Closure\/Reconstruction Witness|field_witness)\b/i.test(lines[j])){end=j; break;}
      }
      blocks.push(lines.slice(start,end).join('\n'));
    }
    return blocks;
  }
  function validateHeldRouteClosure(model,lines){
    const text=lines.join('\n');
    const rLines=[...text.matchAll(/^\s*(?:[-*]\s*)?R\(H,\s*(?:Δ|Delta)\)\s*:\s*(.+)$/gim)].map(m=>m[1]);
    const closureIndex=lines.findIndex(line=>/^\s*(?:#{1,6}\s*)?Closure\/Reconstruction Witness\b/i.test(line));
    const closureTail=closureIndex>=0?lines.slice(closureIndex).join('\n'):'';
    const candidates=[...rLines,...splitMrpSourceBlocks(lines),closureTail].filter(Boolean);
    if(candidates.some(candidate=>
      HIGH_LEVERAGE_HELD_ROUTE_RE.test(candidate)
      && UNROUTED_HELD_ROUTE_RE.test(candidate)
      && TERMINAL_CLOSURE_RE.test(candidate)
      && !ROUTING_OR_BOUNDARY_PROOF_RE.test(candidate)
    )){
      model.errors.push('R(H,Δ) detected a pertinent high-leverage held route, but output claimed STOP/collapse without working, generating, HOLD/PARTIAL-routing, or proving non-load-bearing status');
    }
  }

  function witnessStringParts(value,parts=[]){
    if(value==null) return parts;
    if(typeof value==='string'){parts.push(value); return parts;}
    if(Array.isArray(value)){value.forEach(item=>witnessStringParts(item,parts)); return parts;}
    if(typeof value==='object'){
      Object.entries(value).forEach(([key,item])=>{
        parts.push(String(key));
        witnessStringParts(item,parts);
      });
    }
    return parts;
  }
  function validateWitnessHeldRouteClosure(model,body,label){
    if(!body||typeof body!=='object') return;
    const coverage=body.coverage_proof&&typeof body.coverage_proof==='object'?body.coverage_proof:{};
    const closure=body.closure&&typeof body.closure==='object'?body.closure:{};
    const candidate=witnessStringParts(body).join('\n');
    const claimsClosure=TERMINAL_CLOSURE_RE.test(candidate)
      || body.coverage_complete===true
      || coverage.coverage_complete===true
      || /complete|collapse achieved|STOP/i.test(String(closure.status||closure.verdict||''));
    if(claimsClosure
      && HIGH_LEVERAGE_HELD_ROUTE_RE.test(candidate)
      && UNROUTED_HELD_ROUTE_RE.test(candidate)
      && !ROUTING_OR_BOUNDARY_PROOF_RE.test(candidate)
    ){
      model.errors.push(`${label}: unresolved high-leverage held route is still load-bearing, but closure is marked complete/collapse achieved`);
    }
  }

  function validate(model,lines,routeRecords){
    if(lines.some(line=>/^\s*(?:#{1,6}\s*)?(?:[\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079]+B|B\d+)(?:[\u2080-\u2089]+|[_\.]\d+)\s*\[OP(?:[\u1d62i])?\](?:\s*\[[^\]]+\])?/i.test(line))){
      model.errors.push('submove heading uses [OP] placeholder or second owner bracket; render one concrete source-owned owner bracket such as [M9]');
    }
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
    Object.keys(model.generatedBurdens||{}).forEach(b=>{
      const sms=model.submoves[b]||[];
      const highMassText=[bodyBurdenDescription(model,b),...sms.map(sm=>{
        const d=model.bodyExtract?.submoveDetails?.[sm]||{};
        return [d.heading,d.target,d.operation,d.body,d.result,d.contribution].join(' ');
      })].join(' ');
      if(!HIGH_MASS_GENERATED_RE.test(highMassText)) return;
      const bad=sms.filter(sm=>{
        const d=model.bodyExtract?.submoveDetails?.[sm]||{};
        const ownerText=[model.nodes?.[sm]?.owner,d.heading].filter(Boolean).join(' ');
        const operationBody=[d.operation,d.body].filter(Boolean).join(' ');
        const combined=[d.target,d.operation,d.body,d.result,d.contribution].join(' ');
        if(!(d.target&&d.operation&&d.result&&d.contribution&&d.body)) return true;
        const ownerActivated=ownerSpecificOperationActivated(ownerText,combined);
        if(!OPERATION_MECHANISM_RE.test(combined)&&!ownerActivated) return true;
        const semanticCategories=[OPERATION_SCOPE_RE,OPERATION_TEST_RE,OPERATION_FAILURE_RE].filter(re=>re.test(combined)).length;
        if(semanticCategories<2&&!ownerActivated) return true;
        if(!OPERATION_ACTION_RE.test(`${d.heading||''} ${operationBody}`)&&!ownerActivated) return true;
        if(!STATE_CHANGE_RE.test(`${d.result} ${d.contribution}`)) return true;
        const opWords=(String(operationBody).match(/\b[\w'-]{4,}\b/g)||[]).length;
        const bodyWords=(String(d.body).match(/\b[\w'-]{4,}\b/g)||[]).length;
        const opSentences=String(operationBody).split(/(?<=[.!?])\s+/).filter(Boolean).length;
        const minOpWords=ownerActivated?55:70;
        return opSentences<=2||opWords<minOpWords||bodyWords<45;
      });
      if(bad.length){
        model.errors.push(`${b} generated burden Layer B treatment is mass-insufficient: owner labels and fields are present, but submoves are conclusion-shaped rather than operation-shaped`);
      }
    });
    routeRecords.forEach(r=>{
      if(String(r.route).toUpperCase()!=='STOP') return;
      const tailLines=lines.slice(r.line);
      const closureIdx=tailLines.findIndex(line=>/^\s*(?:#{1,6}\s*)?Closure\/Reconstruction Witness\b/i.test(line));
      const tail=(closureIdx>=0?tailLines.slice(0,closureIdx):tailLines).join('\n');
      if(/Layer B|^#+\s*Burden\s+\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\s+\[generated-by/m.test(tail)) model.errors.push(`line ${r.line}: Route: STOP is followed by later burden / Layer B work`);
    });
    const text=lines.join('\n');
    validateHeldRouteClosure(model,lines);
    const fieldStates=[...text.matchAll(/∇·B\s*:\s*([^;\n]+)/gi)].map(m=>m[1].trim().toLowerCase());
    const curlStates=[...text.matchAll(/∇×κ\s*:\s*([^;\n]+)/gi)].map(m=>m[1].trim().toLowerCase());
    if(model.closureComplete&&fieldStates.some(s=>!s.startsWith('neutral'))&&!/Route:\s*(HOLD|RECURSE)|HOLD\(/i.test(text)) model.errors.push('coverage_complete=true while ∇·B is non-neutral without HOLD/RECURSE explanation');
    if(model.closureComplete&&curlStates.some(s=>!s.startsWith('null')&&!s.includes('resolved'))&&!/LoopBreak|resolved|null/i.test(text)) model.errors.push('coverage_complete=true while ∇×κ is non-null without LoopBreak/resolution');
  }

  function parseWitnessPayload(witnessText,label,model){
    if(!String(witnessText||'').trim()) return;
    try{
      return JSON.parse(witnessText);
    }catch(e){
      model.errors.push(`${label} JSON is invalid: ${e.message}`);
      return null;
    }
  }
  function canonicalJson(value){
    if(Array.isArray(value)) return value.map(canonicalJson);
    if(value&&typeof value==='object') return Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonicalJson(value[k])]));
    return value;
  }
  function normalizeWitnessGraph(value){
    const raw=String(value||'').trim();
    if(!raw || /\b(?:none|no edge|no new graph edge|no-edge)\b/i.test(raw)) return 'none';
    return canonicalizePublicNotation(raw).replace(/\s*→\s*/g,'->').replace(/\s+/g,'');
  }
  function firstState(value){
    return String(value||'').trim().split(/[\/;,]/)[0].trim();
  }
  function compareFormalRereadStates(model,body,visibleMrpEntries,label){
    const raw=body.formal_reread_states;
    if(raw===undefined || raw===null) return;
    if(!Array.isArray(raw)){
      model.errors.push(`${label}: field_witness.formal_reread_states must be a list`);
      return;
    }
    const visible=Object.fromEntries(visibleMrpEntries);
    const seen=new Set();
    if(raw.length!==visibleMrpEntries.length){
      model.errors.push(`${label}: formal_reread_states count ${raw.length} does not match visible MRP count ${visibleMrpEntries.length}`);
    }
    raw.forEach((state,index)=>{
      const stateLabel=`${label}: formal_reread_states[${index+1}]`;
      if(!state || typeof state!=='object'){
        model.errors.push(`${stateLabel}: state must be an object`);
        return;
      }
      const source=normalizeBurden(state.source_burden||state.source||'');
      if(!source){
        model.errors.push(`${stateLabel}: missing source_burden`);
        return;
      }
      if(seen.has(source)) model.errors.push(`${stateLabel}: duplicate source_burden ${source}`);
      seen.add(source);
      const data=visible[source];
      if(!data){
        model.errors.push(`${stateLabel}: source_burden ${source} has no visible MRP block`);
        return;
      }
      const visibleType=(data.resultTypes||[]).slice(-1)[0]||'';
      const visibleRoute=(data.routes||[]).slice(-1)[0]||'';
      if(state.route_result_type&&visibleType&&state.route_result_type!==visibleType){
        model.errors.push(`${stateLabel}: route_result_type mismatch visible=${visibleType} field_witness=${state.route_result_type}`);
      }
      if(state.route&&visibleRoute&&String(state.route).toUpperCase()!==visibleRoute.toUpperCase()){
        model.errors.push(`${stateLabel}: route mismatch visible=${visibleRoute} field_witness=${state.route}`);
      }
      const visibleGraphs=new Set((data.edges||[]).map(e=>`${e[0]}->${e[1]}`));
      const stateGraph=normalizeWitnessGraph(state.graph_delta||state.graph||'');
      if(visibleGraphs.size && !visibleGraphs.has(stateGraph)){
        model.errors.push(`${stateLabel}: graph_delta mismatch visible=[${[...visibleGraphs].sort().join(', ')}] field_witness=${stateGraph}`);
      }else if(!visibleGraphs.size && stateGraph && stateGraph!=='none'){
        model.errors.push(`${stateLabel}: graph_delta must be none when visible MRP has no graph edge`);
      }
      const visibleDivergence=firstState(data.divergence);
      const visibleCurl=firstState(data.curl);
      const stateDivergence=firstState(state.divergence_state);
      const stateCurl=firstState(state.curl_state);
      const terminalStopProjection=(state.route_result_type==='no_new_resultant'||String(state.route||'').toUpperCase()==='STOP');
      const divergenceDisplayProjection=(
        terminalStopProjection&&
        stateDivergence==='neutral'&&
        (visibleDivergence==='settled'||visibleDivergence==='bounded'||visibleDivergence==='non-neutral')
      );
      const curlDisplayProjection=(
        terminalStopProjection&&
        stateCurl==='null'&&
        visibleCurl==='resolved'
      );
      if(visibleDivergence&&stateDivergence&&visibleDivergence!==stateDivergence&&!divergenceDisplayProjection){
        model.errors.push(`${stateLabel}: divergence_state mismatch visible=${visibleDivergence} field_witness=${stateDivergence}`);
      }
      if(visibleCurl&&stateCurl&&visibleCurl!==stateCurl&&!curlDisplayProjection){
        model.errors.push(`${stateLabel}: curl_state mismatch visible=${visibleCurl} field_witness=${stateCurl}`);
      }
    });
    visibleMrpEntries.forEach(([burden])=>{
      if(!seen.has(burden)) model.errors.push(`${label}: formal_reread_states missing visible MRP source ${burden}`);
    });
    [...seen].filter(b=>!visible[b]).forEach(b=>model.errors.push(`${label}: formal_reread_states names non-visible MRP source ${b}`));
  }
  function compareWitness(model,witnessText,label='field_witness'){
    const payload=parseWitnessPayload(witnessText,label,model);
    if(!payload) return;
    const body=payload.field_witness&&typeof payload.field_witness==='object'?payload.field_witness:payload;
    const coverage=body.coverage_proof&&typeof body.coverage_proof==='object'?body.coverage_proof:{};
    const graph=coverage.dependency_graph&&typeof coverage.dependency_graph==='object'?coverage.dependency_graph:{};
    validateWitnessHeldRouteClosure(model,body,label);
    const rawNodes=Array.isArray(graph.nodes)?graph.nodes:(Array.isArray(body.nodes)?body.nodes:[]);
    const witnessNodes=new Set(rawNodes.map(item=>{
      if(item&&typeof item==='object'){
        const token=normalizeBurden(item.id||'');
        return item.type==='burden'||/^[⁰¹²³⁴⁵⁶⁷⁸⁹]+B$/.test(token)?token:'';
      }
      return normalizeBurden(item);
    }).filter(token=>/^[⁰¹²³⁴⁵⁶⁷⁸⁹]+B$/.test(token)));
    if(witnessNodes.size){
      const visible=new Set(model.bodyBurdens.length?model.bodyBurdens:model.burdens);
      const w=[...witnessNodes].sort().join(', '), v=[...visible].sort().join(', ');
      if(w!==v) model.errors.push(`${label}: node mismatch visible=[${v}] field_witness=[${w}]`);
    }
    const rawEdges=Array.isArray(graph.edges)?graph.edges:(Array.isArray(body.edges)?body.edges:[]);
    const witnessEdges=new Set(rawEdges.map(edge=>{
      if(Array.isArray(edge)&&edge.length>=2) return `${normalizeBurden(edge[0])}->${normalizeBurden(edge[1])}`;
      if(edge&&typeof edge==='object') return `${normalizeBurden(edge.source||edge.from||'')}->${normalizeBurden(edge.target||edge.to||'')}`;
      return '';
    }).filter(edge=>edge&&edge!=='->'));
    if(witnessEdges.size){
      const visibleEdges=new Set((model.graphEdges||[]).map(edge=>`${edge[0]}->${edge[1]}`));
      const w=[...witnessEdges].sort().join(', '), v=[...visibleEdges].sort().join(', ');
      if(w!==v) model.errors.push(`${label}: edge mismatch visible=[${v}] field_witness=[${w}]`);
    }
    const ledgerSource=body.ledger&&typeof body.ledger==='object'?body.ledger:body;
    const ledger={
      B_LA:Array.isArray(ledgerSource.B_LA)?ledgerSource.B_LA.map(normalizeBurden):[],
      B_MRP:Array.isArray(ledgerSource.B_MRP)?ledgerSource.B_MRP.map(normalizeBurden):[],
      B_total:Array.isArray(ledgerSource.B_total)?ledgerSource.B_total.map(normalizeBurden):[]
    };
    if(!ledger.B_MRP.length&&body.generated_burdens&&typeof body.generated_burdens==='object'){
      ledger.B_MRP=Array.isArray(body.generated_burdens)?body.generated_burdens.map(normalizeBurden):Object.keys(body.generated_burdens).map(normalizeBurden);
    }
    const visibleLa=(model.ledger.B_LA.length?model.ledger.B_LA:model.initialBurdens).map(normalizeBurden);
    const visibleMrp=(model.ledger.B_MRP.length?model.ledger.B_MRP:Object.keys(model.generatedBurdens||{})).map(normalizeBurden);
    const visibleTotal=(model.ledger.B_total.length?model.ledger.B_total:model.burdens).map(normalizeBurden);
    const sameSet=(a,b)=>[...new Set(a)].sort().join(', ')===[...new Set(b)].sort().join(', ');
    ledger.B_MRP.forEach(generated=>{
      if(ledger.B_LA.includes(generated)) model.errors.push(`${label}: field_witness marks baseline burden ${generated} as generated`);
    });
    if(Object.keys(model.generatedBurdens||{}).length&&!ledger.B_MRP.length){
      model.errors.push(`${label}: visible generated B_MRP appears in prose but field_witness omits B_MRP`);
    }
    if(ledger.B_LA.length&&visibleLa.length&&!sameSet(ledger.B_LA,visibleLa)){
      model.errors.push(`${label}: B_LA mismatch visible=[${visibleLa.join(', ')}] field_witness=[${ledger.B_LA.join(', ')}]`);
    }
    if(ledger.B_MRP.length&&visibleMrp.length&&!sameSet(ledger.B_MRP,visibleMrp)){
      model.errors.push(`${label}: B_MRP mismatch visible=[${visibleMrp.join(', ')}] field_witness=[${ledger.B_MRP.join(', ')}]`);
    }
    if(ledger.B_total.length&&visibleTotal.length&&!sameSet(ledger.B_total,visibleTotal)){
      model.errors.push(`${label}: B_total mismatch visible=[${visibleTotal.join(', ')}] field_witness=[${ledger.B_total.join(', ')}]`);
    }
    let rawMrp=body.mrp_resultants;
    if(!Array.isArray(rawMrp)&&!(rawMrp&&typeof rawMrp==='object')) rawMrp=body.reread_pressure;
    if(!Array.isArray(rawMrp)&&!(rawMrp&&typeof rawMrp==='object')) rawMrp=[];
    if(!rawMrp.length&&body.mrp_resultants&&typeof body.mrp_resultants==='object'){
      rawMrp=Object.entries(body.mrp_resultants).map(([source,item])=>(
        item&&typeof item==='object'?{source,...item}:{source,type:String(item||'')}
      ));
    }
    if(!rawMrp.length&&body.reread_pressure&&typeof body.reread_pressure==='object'){
      rawMrp=Object.entries(body.reread_pressure).map(([source,item])=>(
        item&&typeof item==='object'?{source,...item}:{source,type:String(item||'')}
      ));
    }
    const witnessMrp={};
    rawMrp.forEach(item=>{
      if(!item||typeof item!=='object') return;
      const source=normalizeBurden(String(item.source||item.burden||item.target||item.id||'').replace(/^MRP\(/,'').replace(/\)$/,''));
      if(!source) return;
      witnessMrp[source]={type:String(item.type||item.result_type||item.resultant||''),route:String(item.route||item.next_route||''),graph:item.graph};
    });
    const visibleMrpEntries=Object.entries(model.mrp||{}).filter(([_,data])=>(data.resultTypes||[]).length||(data.routes||[]).length||(data.edges||[]).length);
    if(visibleMrpEntries.length&&!Object.keys(witnessMrp).length){
      model.errors.push(`${label}: visible MRP resultants appear in prose but field_witness omits mrp_resultants`);
    }
    visibleMrpEntries.forEach(([burden,data])=>{
      const witness=witnessMrp[burden];
      if(!witness){model.errors.push(`${label}: missing MRP resultant for visible MRP(${burden})`); return;}
      const visibleType=(data.resultTypes||[]).slice(-1)[0]||'';
      const visibleRoute=(data.routes||[]).slice(-1)[0]||'';
      if(visibleType&&witness.type&&visibleType!==witness.type) model.errors.push(`${label}: MRP(${burden}) type mismatch visible=${visibleType} field_witness=${witness.type}`);
      if(visibleRoute&&witness.route&&visibleRoute.toUpperCase()!==witness.route.toUpperCase()) model.errors.push(`${label}: MRP(${burden}) route mismatch visible=${visibleRoute} field_witness=${witness.route}`);
    });
    compareFormalRereadStates(model,body,visibleMrpEntries,label);
    function normalizeTerminalSource(source){
      const terminals={};
      const add=(burden,value)=>{
        const token=normalizeBurden(burden);
        const state=value&&typeof value==='object'?String(value.state||value.terminal||''):String(value||'');
        if(token&&state) terminals[token]=state.toLowerCase();
      };
      if(Array.isArray(source)){
        source.forEach(value=>{
          if(value&&typeof value==='object') add(value.id||value.notation||value.burden||'',value);
          else add(value,value);
        });
      }else if(source&&typeof source==='object'){
        Object.entries(source).forEach(([burden,value])=>add(burden,value));
      }
      return terminals;
    }
    let witnessTerminals=normalizeTerminalSource(body.terminal_states);
    if(!Object.keys(witnessTerminals).length) witnessTerminals=normalizeTerminalSource(coverage.terminal_states);
    if(!Object.keys(witnessTerminals).length&&body.burdens&&typeof body.burdens==='object'){
      witnessTerminals=normalizeTerminalSource(Object.fromEntries(Object.entries(body.burdens).map(([burden,value])=>[
        burden,
        value&&typeof value==='object'?{state:value.terminal_state||value.terminal||value.state||''}:value
      ])));
    }
    Object.entries(witnessTerminals).forEach(([burden,value])=>{
      const token=normalizeBurden(burden);
      const state=String(value||'');
      if(token&&state) witnessTerminals[token]=state.toLowerCase();
    });
    const visibleTerminals=Object.entries(model.terminals||{});
    if(visibleTerminals.length&&!Object.keys(witnessTerminals).length){
      model.errors.push(`${label}: visible terminal states appear in prose but field_witness omits terminal_states`);
    }
    visibleTerminals.forEach(([burden,state])=>{
      const witness=witnessTerminals[burden]||'';
      if(!witness){model.errors.push(`${label}: missing terminal state for visible ${burden}`); return;}
      if(state==='Land'&&!/(landed|cleared|discharged|held-with-reason)/i.test(witness)) model.errors.push(`${label}: terminal mismatch for ${burden}: visible Land but field_witness state=${witness}`);
      if(state==='HOLD'&&!/(hold|held|partial|carried)/i.test(witness)) model.errors.push(`${label}: terminal mismatch for ${burden}: visible HOLD but field_witness state=${witness}`);
    });
  }
  function compareEmbeddedAndSeparateWitness(model,embedded,separate){
    if(!String(embedded||'').trim() || !String(separate||'').trim()) return;
    const a=parseWitnessPayload(embedded,'embedded field_witness',model);
    const b=parseWitnessPayload(separate,'separate field_witness',model);
    if(!a||!b) return;
    if(JSON.stringify(canonicalJson(a))!==JSON.stringify(canonicalJson(b))){
      model.errors.push('embedded field_witness and separate field_witness disagree');
    }
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
    return lines.length?lines:[''];
  }
  let svgMeasureCanvas=null;
  function browserSvgTextWidth(text,size,weight=500){
    try{
      if(typeof document==='undefined'||!document.createElement) return null;
      svgMeasureCanvas=svgMeasureCanvas||document.createElement('canvas');
      const ctx=svgMeasureCanvas.getContext&&svgMeasureCanvas.getContext('2d');
      if(!ctx) return null;
      ctx.font=`${Math.round(Number(weight)||500)} ${size}px Segoe UI, Arial, sans-serif`;
      return ctx.measureText(String(text||'')).width;
    }catch(_error){
      return null;
    }
  }
  function estimateSvgTextWidth(text,size,weight=500){
    const measured=browserSvgTextWidth(text,size,weight);
    if(Number.isFinite(measured)) return measured;
    const heavy=Number(weight)>=700?1.04:1;
    let units=0;
    for(const ch of String(text||'')){
      if(ch===' ') units+=0.34;
      else if(/[ilI\.,:;'`|!]/.test(ch)) units+=0.30;
      else if(/[fjrt\[\]\(\)]/.test(ch)) units+=0.42;
      else if(/[MW@#%&]/.test(ch)) units+=0.86;
      else if(/[A-Z]/.test(ch)) units+=0.66;
      else if(/[0-9]/.test(ch)) units+=0.56;
      else if(/[—–→∇×κΨᴺᴵ𝒞]/.test(ch)) units+=0.70;
      else units+=0.52;
    }
    return units*size*heavy;
  }
  function wrapSvgText(text,width,size,weight=500,maxLines=0){
    const words=String(text||'').replace(/\s+/g,' ').trim().split(' ').filter(Boolean);
    const lines=[]; let cur='';
    words.forEach(word=>{
      const test=(cur+' '+word).trim();
      if(cur && estimateSvgTextWidth(test,size,weight)>width){lines.push(cur); cur=word;}
      else cur=test;
    });
    if(cur) lines.push(cur);
    if(Number.isFinite(maxLines)&&maxLines>0&&lines.length>maxLines) lines.length=maxLines;
    return lines.length?lines:[''];
  }
  function storyWrap(text,width,size,weight=500,maxLines=0){
    return wrapSvgText(text,width,size,weight,maxLines);
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
      generated_burden_instantiation:'generated_burden_instantiation',
      held_burden_activation:'held_burden_activation',
      no_new_resultant:'no_new_resultant',
      hold_partial:'hold_partial',
      loopbreak:'loopbreak'
    })[type]||type;
  }
  function publicTerminalBadge(state){
    const s=String(state||'pending');
    if(/HOLD/i.test(s)) return 'Held';
    if(/PARTIAL|RECURSE/i.test(s)) return 'Partial';
    if(/land/i.test(s)) return 'Landed';
    if(/STOP|closed/i.test(s)) return 'Closed';
    return s;
  }
  function publicRouteBadge(routes){
    const r=String(routes||'');
    if(/STOP/i.test(r)) return 'Closed for this reply';
    if(/HOLD/i.test(r)) return 'Held open';
    if(/RECURSE/i.test(r)) return 'RECURSE';
    if(/LoopBreak/i.test(r)) return 'Loop blocked';
    return 'Route';
  }
  function humanize(text){
    return canonicalizePublicNotation(String(text||'')
      .replace(/\s+/g,' ')
      .replace(/\bPF[-_ ]?definition[-_ ]?shift\b/gi,'definition shift')
      .replace(/\bDO-\d+\s*\/\s*/gi,'')
      .replace(/\b([a-z]+)-([a-z]+)/gi,(m,a,b)=>`${a} ${b}`)
      .replace(/\bFPD\b/g,'foreign premise detection')
      .replace(/\bM1-P\b/g,'performative contradiction')
      .replace(/\bM1\b/g,'self refutation')
      .replace(/\bM8\b/g,'consequence trace')
      .replace(/\bM9\b/g,'predication repair')
      .trim());
  }
  function stripTechnicalLead(text){
    return publicizeInsiderReference(humanize(canonicalizePublicNotation(String(text||'')
      .replace(/^Answer move\s+/i,'')
      .replace(/^[⁰¹²³⁴⁵⁶⁷⁸⁹]+B[₀₁₂₃₄₅₆₇₈₉]+(?:\[[^\]]+\])?\s+—\s*/,'')
      .replace(/^Land\([^)]+\)\s+—\s*/i,'')
      .replace(/^HOLD\([^)]+\)\s+—\s*/i,'')
      .replace(/^R\(H,Δ\)\s+—\s*/i,'')
      .replace(/^MRP\([^)]+\)\s*[:—-]?\s*/i,'')
      .replace(/^Route:\s*/i,''))));
  }
  function publicizeInsiderReference(text){
    return stripMarkdownArtifacts(String(text||''))
      .replace(/\bProceed to Closure\s*\/\s*Reconstruction Witness\.?/gi,'Proceed to formal closure accounting.')
      .replace(/\bClosure\s*\/\s*Reconstruction Witness\b/gi,'formal closure witness')
      .replace(/\bMRP resultants\b/gi,'follow-up pressure results')
      .replace(/\bField diagnostics\s*:/gi,'Field state:')
      .replace(/∇·B\s*:/g,'field pressure:')
      .replace(/∇×κ\s*:/g,'dependency curl:')
      .replace(/𝒞\(Ψᴺ\)\s*:/g,'closure field:')
      .trim();
  }
  function publicNodeLabel(node,model){
    if(node.kind==='input') return canonicalizePublicNotation(node.label);
    if(node.kind==='burden') return canonicalizePublicNotation(node.label).replace(/^([⁰¹²³⁴⁵⁶⁷⁸⁹]+B)\s+—\s*/,'Problem $1 — ');
    if(node.kind==='submove') return stripTechnicalLead(node.label);
    if(node.kind==='land'){
      const prefix=/HOLD/i.test(node.id)?'What remains held':'What this answer established';
      return canonicalizePublicNotation(node.label).replace(/^Land\((.+?)\)\s+—\s*/i,`${prefix} — `).replace(/^HOLD\((.+?)\)\s+—\s*/i,`${prefix} — `).replace(/^Land\(.+?\)$/i,prefix).replace(/^HOLD\(.+?\)$/i,prefix);
    }
    if(node.kind==='reread') return canonicalizePublicNotation(node.label).replace(/^R\(H,Δ\)\s+—\s*/,'After this, what remains? — ').replace(/^R\(H,Δ\)$/,'After this, what remains?');
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
    return canonicalizePublicNotation(node.label);
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
      .map(b=>`${issueLabel(b)} — ${bodyBurdenDescription(model,b)}`.replace(/\s+/g,' '))
      .filter(Boolean)
      .slice(0,limit);
  }
  function baselineBurdenIds(model){
    const baseline=model.ledger.B_LA.length?model.ledger.B_LA:model.initialBurdens;
    return baseline.map(normalizeBurden).filter(Boolean);
  }
  function generatedBurdenIds(model){
    const generated=model.ledger.B_MRP.length?model.ledger.B_MRP:Object.keys(model.generatedBurdens||{});
    return generated.map(normalizeBurden).filter(Boolean);
  }
  function burdenLabelItems(model,ids,limit=20){
    return ids
      .map(b=>`${issueLabel(b)} — ${bodyBurdenDescription(model,b)}`.replace(/\s+/g,' '))
      .filter(Boolean)
      .slice(0,limit);
  }
  function baselineBurdenLabels(model,limit=8){
    return burdenLabelItems(model,baselineBurdenIds(model),limit);
  }
  function generatedBurdenLabels(model,limit=8){
    return burdenLabelItems(model,generatedBurdenIds(model),limit).map(item=>{
      const b=(item.match(/^Problem\s+(\S+)/)||[])[1]||'';
      const provenance=b&&model.generatedBurdens[b]?` [generated-by: ${model.generatedBurdens[b]}]`:' [generated]';
      return `${item}${provenance}`;
    });
  }
  function uniqueBurdenIds(ids){
    const seen=new Set(), out=[];
    (ids||[]).map(normalizeBurden).filter(Boolean).forEach(id=>{
      if(!seen.has(id)){seen.add(id); out.push(id);}
    });
    return out;
  }
  function accountedBurdenIds(model){
    const total=uniqueBurdenIds(model.ledger.B_total.length?model.ledger.B_total:model.burdens);
    if(total.length) return total;
    return uniqueBurdenIds([...baselineBurdenIds(model),...generatedBurdenIds(model)]);
  }
  function accountedBurdenLabels(model,limit=50){
    const generatedSet=new Set(generatedBurdenIds(model));
    return burdenLabelItems(model,accountedBurdenIds(model),limit).map(item=>{
      const b=(item.match(/^Problem\s+(\S+)/)||[])[1]||'';
      if(generatedSet.has(b)){
        const provenance=model.generatedBurdens[b]?` [generated-by: ${model.generatedBurdens[b]}]`:' [generated]';
        return `${item}${provenance}`;
      }
      return item;
    });
  }
  function splitReadableItems(text){
    return String(text||'')
      .split(/(?<=\.)\s+|;\s+|\s+•\s+/)
      .map(x=>x.trim())
      .filter(Boolean);
  }
  function splitListLikeItems(text){
    const raw=String(text||'').replace(/\s+/g,' ').trim();
    if(!raw) return null;
    const cleaned=raw
      .replace(/^After this(?: answer)?, what remains\?\s*[—:-]?\s*/i,'')
      .replace(/^R\(H,Δ\)\s*[—:-]?\s*/i,'')
      .replace(/^Follow-up(?: pressure check)?:\s*/i,'');
    const pieces=cleaned.split(/\s*(?:;|\|)\s+|\s+•\s+|\s+(?=(?:Failure point|Known failure|Next link|What remained|Why it matters|Field diagnostics|Field state|Field pressure|Dependency curl|MRP result(?:ant)?|Graph|Route|Target|Finding|Resultant)\b)/i)
      .map(x=>x.trim().replace(/^\s*[-–—]\s*/,''))
      .filter(x=>x.length>2);
    if(pieces.length>1) return pieces;
    const burdenPieces=cleaned.split(/\s+(?=(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+B|B\d+)\s*[—:-])/).map(x=>x.trim()).filter(Boolean);
    return burdenPieces.length>1?burdenPieces:null;
  }
  function technicalDiagnosis(model){
    const parts=[
      `field=${model.fieldType||'not detected'}`,
      `case=${model.caseProfile||'not detected'}`,
      `claim=${model.claimType||'not detected'}`,
      `pattern=${model.patternProfile||model.diagnosis||'not detected'}`
    ];
    if(model.restorationAim&&model.restorationAim!=='not detected') parts.push(`restoration=${model.restorationAim}`);
    return parts.join(' · ');
  }
  function publicTechnicalGloss(model){
    const parts=['Layer A / Compact DSL-IR detected'];
    if(model.fieldType&&model.fieldType!=='not detected') parts.push(`field=${model.fieldType}`);
    if(model.claimType&&model.claimType!=='not detected') parts.push(`claim=${model.claimType}`);
    if(model.patternProfile||model.diagnosis) parts.push(`pattern=${model.patternProfile||model.diagnosis}`);
    return parts.join(' · ');
  }
  function bodyBackedStructuralSummary(model){
    const candidates=[
      model.liveBurden,
      model.inputDigest && model.inputDigest!=='pasted daee-epistemics output' ? model.inputDigest : '',
      model.diagnosis,
      model.patternProfile,
      semanticBurdenLabels(model,1)[0]
    ].filter(x=>x&&x!=='not detected');
    if(candidates.length) return humanize(candidates[0]);
    const first=semanticBurdenLabels(model,1)[0];
    return first?first.replace(/^Problem\s+[⁰¹²³⁴⁵⁶⁷⁸⁹]+B\s*—\s*/,''):'not detected in visible body';
  }
  function publicStructureDigest(model,burdens){
    const context=visibleClaimContext(model);
    const structural=bodyBackedStructuralSummary(model);
    const burdenCount=burdens.length||model.burdens.length||0;
    const burdenLine=burdenCount?`It treats the output as carrying ${burdenCount} live problem${burdenCount===1?'':'s'} that must be answered in order.`:'It looks for the live problems that have to be answered before closure is licensed.';
    if(context){
      return `${context} The map reads the reply by its noetic pressure, not by raw parser labels. ${burdenLine}`;
    }
    return `The output detects a structured noetic pressure: ${structural}. ${burdenLine}`;
  }
  function publicStructureItems(model,burdens){
    const items=[];
    const structural=bodyBackedStructuralSummary(model);
    if(structural&&structural!=='not detected in visible body') items.push(`Noetic pressure detected: ${structural}`);
    if(burdens.length) items.push(`Live burdens found: ${burdens.length}`);
    const firstProblems=semanticBurdenLabels(model,3).map(item=>item.replace(/^Problem\s+\S+\s+—\s*/,''));
    if(firstProblems.length) items.push(`First problems named by the output: ${firstProblems.join('; ')}`);
    const aim=model.restorationAim&&model.restorationAim!=='not detected'?model.restorationAim:'the reply is returned to a restored reading after the burdens land';
    items.push(`Restoration aim: ${aim}`);
    return items;
  }
  function burdenNumber(b){
    const s=String(b||'');
    const m=s.match(/^B(\d+)/);
    if(m) return m[1];
    const prefix=s.split('B')[0]||'';
    const n=[...prefix].map(c=>supToInt[c]||'').join('');
    return n||s.replace(/B.*/,'')||s;
  }
  function issueLabel(b){return `Problem ${normalizeBurden(b)}`;}
  function issueGraph(a,b){return `${normalizeBurden(a)} → ${normalizeBurden(b)}`;}
  function burdenDescription(model,b){
    const raw=String(model.nodes[b]?.label||normalizeBurden(b)).replace(/\s+/g,' ').trim();
    let desc=raw.startsWith(b)?raw.slice(String(b).length):raw;
    desc=desc.replace(/^\s*(?:[-–—]|:)\s*/,'').trim();
    return desc||raw;
  }
  function bodyBurdenDescription(model,b){
    const body=model.bodyExtract?.burdenTitles?.[b];
    return (body?stripTechnicalLead(body):stripTechnicalLead(burdenDescription(model,b))).replace(/^\s*(?:[-–—]|:)\s*/,'').trim();
  }
  function bodySubmoveLabel(model,sm,node){
    const body=model.bodyExtract?.submoveTexts?.[sm];
    const details=model.bodyExtract?.submoveDetails?.[sm]||{};
    const heading=body?stripTechnicalLead(body):publicNodeLabel(node,model);
    const owner=node?.owner?`[${node.owner}]`:'';
    const prefix=`${sm}${owner} — `;
    const detail=details.result||details.contribution||details.operation||details.target||'';
    if(detail){
      const cleaned=stripTechnicalLead(detail);
      if(cleaned && !heading.includes(cleaned.slice(0,40))) return `${prefix}${heading}. ${cleaned}`;
    }
    return `${prefix}${heading}`;
  }
  function bodySubmoveSections(model,sm,node){
    const details=model.bodyExtract?.submoveDetails?.[sm]||{};
    const owner=node?.owner?`[${node.owner}]`:'';
    const heading=stripTechnicalLead(model.bodyExtract?.submoveTexts?.[sm]||node?.result||node?.label||sm);
    const sections=[{kind:'heading',label:'',text:`${sm}${owner} — ${heading}`}];
    [
      ['Target', details.target],
      ['What it does', details.operation],
      ['TTP operation body', details.body],
      ['Result', details.result],
      ['Contribution-to-Land', details.contribution]
    ].forEach(([label,value])=>{
      const cleaned=stripTechnicalLead(value||'');
      if(cleaned) sections.push({kind:'detail',label,text:storyFieldText(cleaned,label)});
    });
    return sections;
  }
  function storyFieldText(text,label=''){
    const cleaned=stripTechnicalLead(text||'');
    return cleaned;
  }
  function bodyLandText(model,b,land){
    const body=model.bodyExtract?.landTexts?.[b];
    return body?stripTechnicalLead(body):(land?stripTechnicalLead(land.label):'No landing result detected in the visible output.');
  }
  function mrpRereadFallbackText(model,b){
    const body=(model.bodyExtract?.mrpTexts?.[b]||[])
      .map(line=>canonicalizePublicNotation(cleanParsed(line)))
      .filter(Boolean);
    if(!body.length) return '';
    const pick=(patterns)=>patterns.flatMap(pattern=>body.filter(line=>pattern.test(line)))[0]||'';
    const result=pick([/^Result\s*:/i,/^MRP result(?:ant)?\s*:/i,/^Resultant\s*:/i]);
    const target=pick([/^What remained\s*:/i,/^Target\s*:/i]);
    const diagnostics=pick([/^Field diagnostics\s*:/i,/∇·|∇×|del[- ]dot|del[- ]cross/i]);
    const graph=pick([/^Graph (?:movement|delta)\s*:/i]);
    const route=pick([/^Route\s*:/i]);
    return [result,target,diagnostics,graph,route]
      .filter(Boolean)
      .map(stripTechnicalLead)
      .filter(Boolean)
      .join('; ');
  }
  function bodyRereadText(model,b,reread){
    const body=model.bodyExtract?.rereadTexts?.[b];
    if(body) return stripTechnicalLead(body);
    if(reread) return stripTechnicalLead(reread.label);
    const mrpFallback=mrpRereadFallbackText(model,b);
    return mrpFallback||'No state reread was detected for this problem.';
  }
  function bodyBurdenSetupText(model,b){
    return model.bodyExtract?.hiddenPremiseTexts?.[b] || model.bodyExtract?.burdenSetupTexts?.[b] || '';
  }
  function bodyMrpSourceText(model,b){
    return model.bodyExtract?.mrpSourceTexts?.[b] || '';
  }
  function bodyClosureWitnessText(model){
    return model.bodyExtract?.closureWitnessText || '';
  }
  function sourceSectionTitle(model,b){
    return model.bodyExtract?.hiddenPremiseHeadings?.[b] || model.bodyExtract?.burdenSetupHeadings?.[b] || 'Source setup from the output';
  }
  function publicSourceSetupTitle(model,b){
    if(model.bodyExtract?.hiddenPremiseTexts?.[b]) return 'Hidden premises operating in this problem';
    if(model.bodyExtract?.burdenSetupTexts?.[b]) return 'Problem setup from the output';
    return 'Problem setup from the output';
  }
  function bodyMrpItems(model,b,result,edgeText){
    const body=(model.bodyExtract?.mrpTexts?.[b]||[]).map(stripTechnicalLead).filter(Boolean);
    const bodyItems=(splitListLikeItems(body.join('; '))||[])
      .map(x=>x.replace(/^\s*(?:Resultant|MRP resultant)\s*:\s*/i,'Result: ').trim())
      .filter(x=>!/^(?:MRP|resultant:?|pressure activations:?|target:?|reread:?)$/i.test(x));
    if(bodyItems&&bodyItems.length) return bodyItems;
    return [`Follow-up result: ${result}.`, `Next link: ${canonicalizePublicNotation(edgeText)}.`];
  }
  function pickMrpLine(model,b,patterns,fallback='not detected'){
    const body=(model.bodyExtract?.mrpTexts?.[b]||[]).map(x=>canonicalizePublicNotation(cleanParsed(x))).filter(Boolean);
    for(const pattern of patterns){
      const found=body.find(line=>pattern.test(line));
      if(found) return stripTechnicalLead(found);
    }
    return fallback;
  }
  function mrpPanelRows(model,b,result,edgeText,routes,rereadText){
    const route=routes||'not detected';
    const graph=edgeText&&edgeText!=='none'?canonicalizePublicNotation(edgeText):'none';
    const routeType=routeResultType(model,b);
    const mrp=model.mrp[b]||{};
    const edgeTarget=(mrp.edges||[])[0]?.[1]||'';
    const targetGenerated=edgeTarget&&model.generatedBurdens[edgeTarget]===`MRP(${b})`;
    const targetBaseline=edgeTarget&&(baselineBurdenIds(model).includes(edgeTarget)||model.initialBurdens.includes(edgeTarget));
    const remained=pickMrpLine(model,b,[/∇·T\s*:/i,/Target:\s*/i,/Reread:\s*/i],rereadText);
    const why=pickMrpLine(model,b,[/MRP resultant\s*:/i,/Resultant\s*:/i,/finding .* routes/i,/no new pressure/i],route&&/STOP/i.test(route)?'No additional live pressure remained after this follow-up check.':'The previous answer landed, but the follow-up check found pressure that still had to be handled.');
    const rows=[
      ['Result', result],
      ['What remained', remained],
      ['Why it matters', why],
      ['Graph movement', graph],
      ['Route', route],
    ];
    if(routeType==='generated_burden_instantiation'){
      rows.push(['Generated burden', edgeTarget?`${edgeTarget} [generated-by: MRP(${b})]`:'generated burden detected']);
      rows.push(['Ledger effect', edgeTarget?`${edgeTarget} was absent from B_LA and added to B_MRP.`:'A new non-baseline pressure was added to B_MRP.']);
      rows.push(['Next step', edgeTarget?`RECURSE into generated ${edgeTarget}.`:'RECURSE into the generated burden.']);
    }else if(routeType==='held_burden_activation'){
      rows.push(['Ledger effect', edgeTarget&&targetBaseline?`${edgeTarget} was already in B_LA; no ledger expansion.`:'Known baseline pressure was activated; no ledger expansion.']);
      rows.push(['Next step', edgeTarget?`RECURSE to existing ${edgeTarget}.`:'RECURSE to the existing held burden.']);
    }else if(routeType==='no_new_resultant'){
      rows.push(['Ledger effect', 'No new burden was added to B_MRP.']);
      rows.push(['Next step', /STOP/i.test(route)?'STOP / closure as licensed.':'No graph movement unless HOLD or closure is licensed.']);
    }else if(routeType==='hold_partial'){
      rows.push(['Ledger effect', 'No ledger expansion; real pressure remains held.']);
      rows.push(['Next step', 'HOLD / PARTIAL as licensed.']);
    }else if(routeType==='loopbreak'){
      rows.push(['Ledger effect', 'No ledger expansion; cyclic pressure is blocked.']);
      rows.push(['Next step', 'LoopBreak rather than proof-stack expansion.']);
    }
    rows.push(['Technical', `MRP(${b}); type=${routeType}; graph=${graph}; route=${route}`]);
    return rows;
  }
  function routePanelItems(model,b,nextBurden,routes,result){
    const route=String(routes||'').toUpperCase();
    const mrp=model.mrp[b]||{};
    const edgeTarget=(mrp.edges||[])[0]?.[1] || nextBurden || '';
    const nextTitle=edgeTarget?`${edgeTarget} — ${bodyBurdenDescription(model,edgeTarget)}`:'no next problem detected';
    const reread=bodyRereadText(model,b,model.nodes[`R(H,Δ)@${b}`]);
    const relation=result||publicRouteType(routeResultType(model,b));
    if(/RECURSE/.test(route)){
      return [
        `Move to next identified problem: ${nextTitle}.`,
        `Why closure is withheld: ${reread}`,
      relation==='generated_burden_instantiation'
          ? `Route type: MRP generated an additional problem from the reread.`
          : `Route type: MRP activated a remaining problem that still had to be answered.`
      ];
    }
    if(/HOLD/.test(route)){
      return [
        `Hold instead of closing: ${reread}`,
        `Why this is held: the output records real pressure that is not expanded in this pass.`
      ];
    }
    if(/LOOPBREAK/.test(route)){
      return [
        `LoopBreak: repeated proof-demand or circular pressure was detected.`,
        `Why expansion stops: further proof-stacking is not licensed by this route.`
      ];
    }
    if(/STOP/.test(route)){
      return [
        `Stop for this reply: no additional live problem remains after ${b}.`,
        `Closure is licensed because the follow-up check records no new graph edge.`
      ];
    }
    return [
      edgeTarget?`Next problem available: ${nextTitle}.`:`No explicit next route was detected.`,
      `Route evidence: ${canonicalizePublicNotation(routes||'not detected')}.`
    ];
  }
  function firstSentence(text){
    return String(text||'').split(/(?<=\.)\s+/)[0] || String(text||'');
  }
  function visibleClaimContext(model){
    const labels=semanticBurdenLabels(model,6).map(item=>item.replace(/^Problem\s+\S+\s+—\s*/,'').trim()).filter(Boolean);
    const joined=[...labels,model.closingFormulation||'',model.restorationAim||''].join(' ');
    if(/proof-?text|local grammar|remote text|cross-text|only true God/i.test(joined)){
      const proofTexts=[...new Set((joined.match(/\b(?:[1-3]\s+)?[A-Z][a-z]+\s+\d+:\d+/g)||[]).map(x=>x.replace(/\s+/g,' ')))];
      const textList=proofTexts.length?` around ${proofTexts.slice(0,4).join(', ')}`:'';
      return `A prooftext or source-reading reply${textList}: the output tests whether local grammar, remote-text appeals, and imported doctrinal or framework pressure have been routed as distinct burdens.`;
    }
    if(/secular/i.test(joined) && /neutral/i.test(joined)){
      return `A secular-public-reason reply: it claims neutrality while the output tests whether that neutrality hides an authority rule or admissibility filter.`;
    }
    if(/eternal lake of fire|non-belief|worship|moral tribunal|divine judgment/i.test(joined)){
      return `A moral-protest reply about divine judgment and worship-worthiness: it challenges whether the objection's moral criterion and worldview frame can carry the burden it places on God.`;
    }
    if(labels.length){
      const shown=labels.slice(0,3).join('; ');
      const remaining=labels.length>3?`; plus ${labels.length-3} more listed problem${labels.length-3===1?'':'s'}`:'';
      return `The output is refuting a reply built around: ${shown}${remaining}.`;
    }
    return '';
  }
  function storyCaseHeadline(model){
    const context=visibleClaimContext(model);
    if(/prooftext or source-reading reply/i.test(context)){
      return {
        title:'CASE: prooftext / source-reading reply',
        subtitle:'Question under test: does the output distinguish local grammar, remote source appeals, imported frameworks, and generated post-land pressure?'
      };
    }
    if(/secular-public-reason/i.test(context)){
      return {
        title:'CASE: secular public-reason neutrality claim',
        subtitle:'Question under test: does the appeal to neutral shared reason hide an authority rule or admissibility filter?'
      };
    }
    if(/moral-protest reply/i.test(context)){
      return {
        title:'CASE: moral protest against divine judgment',
        subtitle:'Question under test: can the objection’s moral criterion and worldview frame carry the burden it places on God?'
      };
    }
    return {
      title:'CASE: pasted daee-epistemics output',
      subtitle:context||readerInputDigest(model)
    };
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
    const status=collapseLabel(model);
    const accounted=accountedBurdenIds(model);
    const burdenCount=accounted.length||model.burdens.length||0;
    const terminalCount=accounted.length?accounted.filter(b=>model.terminals[b]).length:Object.keys(model.terminals||{}).length;
    const closed=/collapse achieved|closed/i.test(status);
    const routeLine=closed
      ? `The final pressure-check stops because no additional input-anchored burden remains live.`
      : `The final state is ${status}; the map shows which pressure remains held or unresolved.`;
    if(parties){
      const defender=parties.defended.replace(/^the\s+/i,'');
      return {
        headline:`Final answer: the ${parties.challenged} fails`,
        body:`${defender}'s challenge remains standing. The map accounts for ${terminalCount}/${burdenCount||terminalCount} live problem${(burdenCount||terminalCount)===1?'':'s'} and keeps the detailed closing formulation in its own final card. ${routeLine}`
      };
    }
    return {
      headline:`Verdict: ${status}`,
      body:`The map accounts for ${terminalCount}/${burdenCount||terminalCount} live problem${(burdenCount||terminalCount)===1?'':'s'} from the output. ${routeLine}`
    };
  }
  function readerInputDigest(model){
    const raw=String(model.inputDigest||'').trim();
    if(raw && raw!=='pasted daee-epistemics output' && !/^dominant\b/i.test(raw)) return raw;
    const visibleContext=visibleClaimContext(model);
    if(visibleContext) return visibleContext;
    const parties=refutationParties(model);
    const task=/REFUTE/i.test(model.userTask||'')
      ? (parties?`Reply being rejected: the ${parties.challenged} is trying to answer ${parties.defended}.`:'Task stated in the output: REFUTE.')
      : model.userTask?`User task: ${model.userTask}.`:'';
    const anchored=[task].filter(Boolean).join(' ');
    if(anchored) return anchored;
    const labels=semanticBurdenLabels(model,1);
    if(labels.length) return `Inferred from the burden inventory: ${labels.join('; ')}`;
    if(model.fieldType&&model.fieldType!=='not detected') return `A ${model.fieldType} case processed as ${model.claimType||'a governed claim'}`;
    return 'Pasted daee-epistemics output; original prompt text was not echoed in the output.';
  }
  function diagnosisDigest(model,burdens){
    const parts=diagnosisItems(model,burdens);
    return parts.join(' · ');
  }
  function diagnosisItems(model,burdens){
    const visibleContext=visibleClaimContext(model);
    return [
      visibleContext?`What kind of reply this is: ${visibleContext}`:(model.userTask?`Task stated in the output: ${humanize(model.userTask)}`:''),
      `Structural pressure from the visible output: ${bodyBackedStructuralSummary(model)}`,
      `Problems found in the output: ${burdens.length}`,
      model.restorationAim&&model.restorationAim!=='not detected'?`Restoration aim from the output: ${model.restorationAim}`:''
    ].filter(Boolean);
  }
  function conclusionDigest(model){
    if(model.closingFormulation) return model.closingFormulation;
    if(model.restorativeResponse) return model.restorativeResponse;
    if(model.restorationAim&&model.restorationAim!=='not detected') return `Restoration aim from output: ${model.restorationAim}`;
    return collapseLabel(model);
  }
  function certificateStatusLabel(model){
    const cert=model.collapseCertificate||{};
    if(!cert.present) return '';
    if(!cert.valid) return 'certificate sidecar invalid';
    return cert.fields?.collapse_positive===true?'certificate collapse_positive=true':'certificate displayed';
  }
  function renderCertificateSummary(model){
    const cert=model.collapseCertificate||{};
    if(!cert.present) return '';
    const fields=cert.fields||{};
    const status=cert.valid?'accepted for display':'invalid sidecar';
    const fingerprint=fields.input_fingerprint?`${fields.input_fingerprint.slice(0,24)}...`:'missing';
    const rows=[
      `collapse_positive=${String(fields.collapse_positive)}`,
      `coverage_complete=${String(fields.coverage_complete)}`,
      `diagnostic_completeness=${String(fields.diagnostic_completeness)}`,
      `field pressure=${fields.divergence_state||'missing'}`,
      `dependency curl=${fields.curl_state||'missing'}`,
      `max_generation_depth=${String(fields.max_generation_depth??'missing')}`,
      `input_fingerprint=${fingerprint}`
    ];
    const errors=(cert.errors||[]).map(error=>`<li>${esc(error)}</li>`).join('');
    return `<section class="outputGrapherTopCard outputGrapherCertificateCard"><h3>Collapse Certificate</h3><p><strong>${esc(status)}</strong></p><ul>${rows.map(row=>`<li>${esc(row)}</li>`).join('')}</ul>${errors?`<p class="outputGrapherError">Certificate sidecar problems:</p><ul>${errors}</ul>`:''}<p class="outputGrapherTechMeta">Browser display is advisory; proof-mode agreement still belongs to the Python certificate-backed checker.</p></section>`;
  }
  function renderTopSummary(model){
    const inventory=baselineBurdenLabels(model,20).map(item=>`<li>${esc(item)}</li>`).join('')||'<li>not detected</li>';
    const generatedFollowup=generatedBurdenLabels(model,20).map(item=>`<li>${esc(item)}</li>`).join('');
    const collapse=model.collapse||{}, pillStatus=model.errors.length?'fail':model.warnings.length?'warn':'ok';
    const verdict=verdictDigest(model);
    const diagnosisList=diagnosisItems(model,model.burdens).map(x=>`<li>${esc(x)}</li>`).join('');
    const baseline=(model.ledger.B_LA.length?model.ledger.B_LA:model.initialBurdens).map(normalizeBurden).join(', ')||'not detected';
    const generated=(model.ledger.B_MRP.length?model.ledger.B_MRP:Object.keys(model.generatedBurdens||{})).map(normalizeBurden).join(', ')||'none';
    const total=(model.ledger.B_total.length?model.ledger.B_total:model.burdens).map(normalizeBurden).join(', ')||'not detected';
    return `<div class="outputGrapherTopCards">
      <section class="outputGrapherTopCard"><h3>Final Answer From The Output</h3><p><strong>${esc(verdict.headline)}</strong></p><p>${esc(verdict.body)}</p></section>
      <section class="outputGrapherTopCard"><h3>Reply / Claim Being Rejected</h3><p>${esc(readerInputDigest(model))}</p></section>
      <section class="outputGrapherTopCard"><h3>What The Reply Depends On</h3><ul>${diagnosisList}</ul><p class="outputGrapherTechMeta">Technical reading: ${esc(technicalDiagnosis(model))}</p></section>
      <section class="outputGrapherTopCard"><h3>Main Problems In The Reply</h3><ul>${inventory}</ul><p class="outputGrapherTechMeta">Baseline only: this section lists B_LA. Ledger: B_LA=${esc(baseline)}; B_MRP=${esc(generated)}; B_total=${esc(total)}; B_total = B_LA ∪ B_MRP when generated pressure is present.</p></section>
      ${generatedFollowup?`<section class="outputGrapherTopCard"><h3>Preempted Problems Surfaced By Reread</h3><ul>${generatedFollowup}</ul><p class="outputGrapherTechMeta">Technical: B_MRP. Generated burdens are shown separately from Main Problems and must carry generated-by MRP provenance.</p></section>`:''}
      <section class="outputGrapherTopCard"><h3>Closure / Restoration Status</h3><p><strong>${esc(collapseLabel(model))}</strong></p><p>The map shows whether the reply is closed, held, partial, or still live after the final pressure-check.</p><p class="outputGrapherTechMeta">Technical reading: route-gradient=${esc(collapse.routeGradient||'not detected')}; del-dot=${esc(collapse.delDot||collapse.divergence||'not detected')}; del-cross=${esc(collapse.delCross||collapse.curl||'not detected')}; T_lang=${esc(collapse.tLang||'boundary not detected')}</p></section>
      ${renderCertificateSummary(model)}
    </div><div class="outputGrapherPillRow"><span class="outputGrapherPill ${pillStatus}">Parser verdict: ${model.errors.length?'not reconstructible':'reconstructible'}</span><span class="outputGrapherPill">Problems: ${model.burdens.length}</span><span class="outputGrapherPill">TTP moves: ${Object.values(model.submoves).reduce((a,b)=>a+b.length,0)}</span><span class="outputGrapherPill">Follow-up checks: ${Object.keys(model.mrp).length}</span><span class="outputGrapherPill">Terminal states: ${Object.keys(model.terminals).length}</span></div>`;
  }

  function restorationBullets(model){
    const burdens=accountedBurdenLabels(model,50);
    const burdenIds=accountedBurdenIds(model);
    const renderedCount=burdens.length;
    const terminalCount=burdenIds.length?burdenIds.filter(b=>model.terminals[b]).length:Object.keys(model.terminals||{}).length;
    const held=Object.entries(model.terminals||{})
      .filter(([,state])=>/HOLD|PARTIAL|RECURSE/i.test(String(state)))
      .map(([b,state])=>`${normalizeBurden(b)}: ${state}`);
    const answered=`The rebuttal accounted for ${terminalCount}/${renderedCount||terminalCount} problems.`;
    const collapse=collapseLabel(model);
    const route=model.errors.length?'The graph still exposes missing or invalid accounting.':held.length?`The final result remains ${collapse}; live states: ${held.join('; ')}.`:`The final result reaches ${collapse}; no unaccounted terminal problem was detected.`;
    const restored=(model.restorationAim&&model.restorationAim!=='not detected')?model.restorationAim:'The handled field is oriented back toward sound fiṭrah and clear intellect after the visible burden cycle has been accounted for.';
    return [
      answered,
      ...burdens.map(item=>`Accounted for: ${item}`),
      route,
      `Restored synthesis: ${restored}`
    ].filter(Boolean);
  }

  function storyLineText(lines,x,y,lineHeight,fill,size,weight=800){
    return `<text x="${x}" y="${y}" fill="${fill}" font-size="${size}" font-weight="${weight}" class="ogNodeLabel">${lines.map((line,i)=>`<tspan x="${x}" dy="${i?lineHeight:0}">${esc(line)}</tspan>`).join('')}</text>`;
  }
  function storyTextHeight(lines,lineHeight,size){
    const count=(lines||[]).length;
    if(!count) return 0;
    return Math.max(Math.ceil(size*1.22), (count-1)*lineHeight+Math.ceil(size*1.22));
  }
  function storyBottomPad(pad){
    return Math.max(8,Math.round(pad*.38));
  }
  function normalizeHeaderBadges(badges){
    const items=(badges||[]).filter(Boolean).map(item=>{
      const label=typeof item==='string'?item:item.label;
      const color=typeof item==='string'?'#334155':(item.color||'#334155');
      return {label:String(label||'').trim(), color};
    }).filter(item=>item.label);
    return items.map(item=>({...item,width:Math.max(92,Math.min(190,estimateSvgTextWidth(item.label,14,650)+28))}));
  }
  function renderHeaderBadges(badges,x,y,w,align='left'){
    const items=normalizeHeaderBadges(badges);
    if(!items.length) return {svg:'',height:0};
    let rowH=30, gap=8, svg='';
    let cx=align==='right'?x+w:x;
    items.forEach((item)=>{
      const bw=Math.min(w,item.width);
      const bx=align==='right'?(cx-bw):cx;
      svg+=`<rect x="${bx}" y="${y}" width="${bw}" height="${rowH}" rx="7" fill="${item.color}" stroke="rgba(255,255,255,.18)" stroke-width="1"></rect><text x="${bx+13}" y="${y+20}" fill="#f8fafc" font-size="14" font-weight="650">${esc(item.label)}</text>`;
      cx+=align==='right'?-(bw+gap):(bw+gap);
    });
    return {svg,height:rowH,width:items.reduce((sum,item,i)=>sum+item.width+(i?gap:0),0)};
  }
  function renderCardHeader({x,y,width,title,subtitle='',badges=[],type='',color='#64748b',titleSize=24,subtitleSize=16,pad=24,titleFill='#f8fafc',subtitleFill='#cbd5e1',titleWeight=700}){
    const titleLine=Math.round(titleSize*1.32);
    const subtitleLine=Math.round(subtitleSize*1.45);
    const contentW=width-pad*2;
    const badgeItems=normalizeHeaderBadges(badges);
    const badgeW=badgeItems.length?Math.min(contentW*.42,badgeItems.reduce((sum,item,i)=>sum+item.width+(i?8:0),0)):0;
    const titleW=badgeW?Math.max(300,contentW-badgeW-24):contentW;
    const titleText=title||type||'Untitled';
    const titleLines=storyWrap(titleText, titleW, titleSize, titleWeight, 0);
    let svg='';
    const titleY=y+pad+titleSize;
    if(badgeItems.length){
      const badgeY=y+pad-4;
      svg+=renderHeaderBadges(badgeItems,x+pad,badgeY,contentW,'right').svg;
    }
    svg+=storyLineText(titleLines,x+pad,titleY,titleLine,titleFill,titleSize,titleWeight);
    const titleBottom=titleY+Math.max(0,titleLines.length-1)*titleLine+12;
    const badgeBottom=badgeItems.length?y+pad-4+30+16:0;
    let cy=Math.max(titleBottom,badgeBottom);
    const subtitleLines=subtitle?storyWrap(subtitle, contentW, subtitleSize, 440, 0):[];
    if(subtitleLines.length){
      cy+=subtitleSize;
      svg+=storyLineText(subtitleLines,x+pad,cy,subtitleLine,subtitleFill,subtitleSize,440);
      cy+=Math.max(0,subtitleLines.length-1)*subtitleLine+10;
    }
    const headerHeight=Math.max(78,cy-y+10);
    return {svg,height:headerHeight,bodyY:y+headerHeight+24,color};
  }
  function splitLeadingLabel(text){
    const match=String(text||'').match(/^([^:]{3,54}):\s+(.+)$/);
    if(!match) return null;
    return {label:match[1].trim(), value:match[2].trim()};
  }
  function measureSubmoveSections(sections,w,d){
    const headingSize=Math.max(22,d.font+1);
    const labelSize=Math.max(21,d.font);
    const bodySize=Math.max(22,d.font);
    const bodyLine=Math.max(36,d.line+2);
    const heading=sections.find(section=>section.kind==='heading')?.text||'Answer move';
    const header=renderCardHeader({x:0,y:0,width:w,title:heading,color:'#38bdf8',titleSize:headingSize,pad:24,titleWeight:720,titleFill:'#ecfeff'});
    let height=header.height+6;
    const detailSections=sections.filter(section=>section.kind!=='heading');
    const measured=detailSections.map((section,index)=>{
      const isLast=index===detailSections.length-1;
      const textW=w-48;
      const labelLines=storyWrap(`${section.label}:`, textW, labelSize, 690, 1);
      const bodyLines=storyWrap(section.text, textW, bodySize, 500, 0);
      height+=(index?22:14)+labelLines.length*(labelSize+6)+12+bodyLines.length*bodyLine+(isLast?4:14);
      return {...section,labelLines,bodyLines,labelSize,bodySize,bodyLine};
    });
    return {title:heading,sections:measured,height:Math.max(d.subMinH,height+8)};
  }
  function renderSubmoveSections(block,x,y,w){
    const header=renderCardHeader({x,y,width:w,title:block.title,color:'#38bdf8',titleSize:Math.max(20,block.sections[0]?.bodySize||20),pad:24,titleWeight:720,titleFill:'#ecfeff'});
    let cy=header.bodyY;
    const bodySvg=block.sections.map((section,index)=>{
      cy+=index?22:14;
      const labelSvg=storyLineText(section.labelLines,x+24,cy,section.labelSize+6,'#bae6fd',section.labelSize,690);
      cy+=section.labelLines.length*(section.labelSize+6)+12;
      const bodySvg=storyLineText(section.bodyLines,x+24,cy,section.bodyLine,'#dff7ff',section.bodySize,500);
      cy+=section.bodyLines.length*section.bodyLine+(index===block.sections.length-1?4:14);
      return `${labelSvg}${bodySvg}`;
    }).join('');
    return `${header.svg}${bodySvg}`;
  }
  function storyListBlock(items,x,y,w,lineHeight,fill,size,weight=540,gap=16,labelWeight=700){
    let cy=y, svg='';
    const rows=(items||[]).filter(Boolean);
    rows.forEach((item,index)=>{
      const isLast=index===rows.length-1;
      const split=splitLeadingLabel(item);
      svg+=`<circle cx="${x+7}" cy="${cy-7}" r="5" fill="${fill}"></circle>`;
      if(split){
        const textW=w-34;
        const labelLines=storyWrap(`${split.label}:`, textW, size, labelWeight, 1);
        const valueLines=storyWrap(split.value, textW, size, weight, 0);
        svg+=storyLineText(labelLines,x+28,cy,lineHeight,fill,size,labelWeight);
        cy+=storyTextHeight(labelLines,lineHeight,size)+8;
        svg+=storyLineText(valueLines,x+28,cy,lineHeight,fill,size,weight);
        cy+=storyTextHeight(valueLines,lineHeight,size)+(isLast?0:gap+4);
      }else{
        const lines=storyWrap(item, w-34, size, weight, 0);
        svg+=storyLineText(lines,x+28,cy,lineHeight,fill,size,weight);
        cy+=storyTextHeight(lines,lineHeight,size)+(isLast?0:gap);
      }
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
      badges=[],
      color=stroke,
      minHeight=0,
      klass='outputGrapherStoryPanel'
    }=options;
    const listItems=Array.isArray(items)?items.filter(Boolean):null;
    const innerW=w-pad*2;
    const bodyLines=listItems?[]:storyWrap(subtitle||'not detected', innerW, bodySize, 540, maxLines);
    const techLines=technical?storyWrap(`Technical: ${technical}`, innerW, techSize, 500, 2):[];
    const header=renderCardHeader({x,y,width:w,title,badges,color,titleSize,pad,titleWeight:720});
    const bodyY=header.bodyY;
    const listBlock=listItems?storyListBlock(listItems,x+pad,bodyY,w-pad*2,lineHeight,'#e5e7eb',bodySize,540,16,700):null;
    const bodyHeight=listBlock?listBlock.height:storyTextHeight(bodyLines,lineHeight,bodySize);
    const techY=bodyY+bodyHeight+24;
    const bottomPad=storyBottomPad(pad);
    const visualTrim=techLines.length?Math.ceil(Math.min(bodySize,techSize)*.45):Math.ceil(bodySize*.75);
    const height=Math.max(minHeight, (bodyY-y)+bodyHeight+(techLines.length?24+techLines.length*(techSize+5):0)+bottomPad-visualTrim);
    const techSvg=techLines.length?storyLineText(techLines,x+pad,techY,techSize+5,'#94a3b8',techSize,500):'';
    const bodySvg=listBlock?listBlock.svg:storyLineText(bodyLines,x+pad,bodyY,lineHeight,'#e5e7eb',bodySize,540);
    return {
      height,
      svg:`<g class="${klass}" data-panel-width="${w}" data-inner-text-width="${innerW}" data-left-padding="${pad}" data-right-padding="${pad}" data-text-x="${x+pad}"><rect x="${x}" y="${y}" width="${w}" height="${height}" rx="16" fill="${fill}" stroke="${stroke}" stroke-width="1.4"></rect>${header.svg}${bodySvg}${techSvg}</g>`
    };
  }
  function storyKeyValueBlock(title,rows,x,y,w,options={}){
    const {
      fill='#0b1220',
      stroke='#334155',
      titleSize=18,
      bodySize=16,
      labelSize=16,
      lineHeight=24,
      pad=22,
      badges=[],
      color=stroke,
      klass='outputGrapherStoryPanel outputGrapherKeyValuePanel'
    }=options;
    const labelW=Math.min(260,Math.max(170,Math.floor(w*.2)));
    const header=renderCardHeader({x,y,width:w,title,badges,color,titleSize,pad,titleWeight:720});
    let cy=header.bodyY+10;
    const rowGap=22;
    const rowPad=14;
    const rowData=(rows||[]).filter(row=>row&&row[1]).map(([label,value])=>{
      const lines=storyWrap(value, w-pad*2-labelW-28, bodySize, 500, 0);
      const height=Math.max(lineHeight+rowPad*2, storyTextHeight(lines,lineHeight,bodySize)+rowPad*2);
      return {label,value,lines,height};
    });
    const rowsSvg=rowData.map(row=>{
      const textY=cy+rowPad+labelSize;
      const labelSvg=`<text x="${x+pad}" y="${textY}" fill="#c4b5fd" font-size="${labelSize}" font-weight="700">${esc(row.label)}:</text>`;
      const bodyWeight=/^Technical$/i.test(row.label)?480:500;
      const bodyFill=/^Technical$/i.test(row.label)?'#ddd6fe':'#ede9fe';
      const bodySvg=storyLineText(row.lines,x+pad+labelW,textY,lineHeight,bodyFill,bodySize,bodyWeight);
      const sep=`<line x1="${x+pad}" y1="${cy+row.height+6}" x2="${x+w-pad}" y2="${cy+row.height+6}" stroke="${stroke}" stroke-width=".8" opacity=".45"></line>`;
      cy+=row.height+rowGap;
      return `${labelSvg}${bodySvg}${sep}`;
    }).join('');
    const height=Math.max(96,cy-y+storyBottomPad(pad)-rowGap);
    return {
      height,
      svg:`<g class="${klass}" data-panel-width="${w}" data-value-text-width="${w-pad*2-labelW-28}" data-left-padding="${pad}" data-right-padding="${pad}" data-label-width="${labelW}"><rect x="${x}" y="${y}" width="${w}" height="${height}" rx="16" fill="${fill}" stroke="${stroke}" stroke-width="1.4"></rect>${header.svg}${rowsSvg}</g>`
    };
  }
  function renderRouteRow(title,items,routes,x,y,w,options={}){
    const route=String(routes||'not detected');
    const closed=/STOP/i.test(route);
    const held=/HOLD/i.test(route);
    const loop=/LoopBreak/i.test(route);
    const stroke=closed?'#10b981':loop?'#ef4444':'#f59e0b';
    const fill=closed?'#052e16':loop?'#3b0a0a':'#451a03';
    const badgeFill=closed?'#064e3b':held?'#7c2d12':loop?'#7f1d1d':'#7c2d12';
    const pad=options.pad||24, titleSize=options.titleSize||24, bodySize=options.bodySize||21, lineHeight=options.lineHeight||32;
    const routeLabel=/STOP/i.test(route)?'STOP':/HOLD/i.test(route)?'HOLD':/RECURSE/i.test(route)?'RECURSE':/LoopBreak/i.test(route)?'LoopBreak':'Route';
    const bodyItems=(items||[]).filter(Boolean);
    const main=bodyItems[0]||'No explicit next-step explanation was detected.';
    const detail=bodyItems.slice(1);
    const badgeW=Math.max(92,Math.min(190,estimateSvgTextWidth(routeLabel,14,650)+28));
    const textX=x+pad;
    const textW=w-pad*2;
    const mainLines=storyWrap(main,textW,bodySize,500,0);
    const detailLines=detail.flatMap(item=>storyWrap(`- ${item}`,textW,bodySize-1,480,0));
    const header=renderCardHeader({x,y,width:w,title,badges:[{label:routeLabel,color:badgeFill}],color:stroke,titleSize,pad,titleWeight:720,titleFill:'#fed7aa'});
    const bodyH=storyTextHeight(mainLines,lineHeight,bodySize)+(detailLines.length?16+storyTextHeight(detailLines,lineHeight-2,bodySize-1):0);
    const height=Math.max(96,(header.bodyY-y)+bodyH+storyBottomPad(pad)-Math.ceil(bodySize*.75));
    let cy=header.bodyY;
    let svg=`<g class="outputGrapherRouteRow" data-panel-width="${w}" data-route-badge-width="${badgeW}" data-route-badge-position="top-right" data-inner-text-width="${textW}" data-left-padding="${pad}" data-right-padding="${pad}" data-text-x="${textX}"><rect x="${x}" y="${y}" width="${w}" height="${height}" rx="16" fill="${fill}" stroke="${stroke}" stroke-width="1.4"></rect>${header.svg}`;
    svg+=storyLineText(mainLines,textX,cy,lineHeight,'#ffedd5',bodySize,500);
    cy+=storyTextHeight(mainLines,lineHeight,bodySize)+16;
    if(detailLines.length) svg+=storyLineText(detailLines,textX,cy,lineHeight-2,'#fed7aa',bodySize-1,480);
    svg+=`</g>`;
    return {height,svg};
  }
  function storySection(title,subtitle,x,y,w,h,fill='#0b1220',stroke='#334155',technical=''){
    return storySectionBlock(title,subtitle,x,y,w,{fill,stroke,technical,minHeight:h,maxLines:3}).svg;
  }
  function renderCollapsePanel(model,x,y,w){
    const collapse=model.collapse||{};
    const bullets=restorationBullets(model);
    const pad=36, titleSize=34, bodySize=22, lineHeight=34;
    const bulletGap=20;
    const bulletHeight=bullets.reduce((height,text,index)=>{
      const lines=storyWrap(text, w-pad*2-24, bodySize, 540, 0);
      return height+storyTextHeight(lines,lineHeight,bodySize)+(index===bullets.length-1?0:bulletGap);
    },0);
    const header=renderCardHeader({x,y,width:w,title:`Restoration Summary: ${collapseLabel(model)}`,color:'#22c55e',titleSize,pad,titleFill:'#dcfce7',titleWeight:720});
    const height=header.height+bulletHeight+storyBottomPad(pad);
    let cy=header.bodyY;
    const bulletSvg=bullets.map((text,index)=>{
      const lines=storyWrap(text, w-pad*2-24, bodySize, 540, 0);
      const group=`<circle cx="${x+pad+5}" cy="${cy-7}" r="5" fill="#86efac"></circle>${storyLineText(lines,x+pad+24,cy,lineHeight,'#dcfce7',bodySize,540)}`;
      cy+=storyTextHeight(lines,lineHeight,bodySize)+(index===bullets.length-1?0:bulletGap);
      return group;
    }).join('');
    return {
      height,
      svg:`<g class="outputGrapherProofBlock outputGrapherRestorationSummary"><rect x="${x}" y="${y}" width="${w}" height="${height}" rx="22" fill="#071a12" stroke="#22c55e" stroke-width="1.8"></rect>${header.svg}${bulletSvg}</g>`
    };
  }
  function renderFormalCaseFill(model,x,y,w){
    const collapse=model.collapse||{};
    const terminalStates=Object.entries(model.terminals||{})
      .map(([b,state])=>`${normalizeBurden(b)}=${canonicalizePublicNotation(state)}`)
      .join('; ') || 'not detected';
    const mrpLedger=Object.entries(model.mrp||{})
      .map(([b,data])=>{
        const graph=(data.edges||[]).map(edge=>issueGraph(edge[0],edge[1])).join(', ') || 'none';
        const route=(data.routes||[]).join(', ') || 'not detected';
        const result=(data.resultTypes||[]).join(', ') || publicRouteType(routeResultType(model,b));
        return `MRP(${normalizeBurden(b)}): finding=${result}; graph=${graph}; route=${route}`;
      })
      .join('; ') || 'none';
    const rows=[
      ['Formal reading', 'R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) → 𝒞(Ψᴺ) → N_fiṭrī ∧ ʿaql ṣarīḥ'],
      ['Burden ledger', `B_LA=${(model.ledger.B_LA.length?model.ledger.B_LA:model.initialBurdens).map(normalizeBurden).join(', ')||'not detected'}; B_MRP=${(model.ledger.B_MRP.length?model.ledger.B_MRP:Object.keys(model.generatedBurdens||{})).map(normalizeBurden).join(', ')||'none'}; B_total=${(model.ledger.B_total.length?model.ledger.B_total:model.burdens).map(normalizeBurden).join(', ')||'not detected'}`],
      ['Terminal states', `${Object.keys(model.terminals||{}).length}/${model.burdens.length||0}; ${terminalStates}`],
      ['MRP/resultant ledger', mrpLedger],
      ['Formal field proof', `Route-gradient: ${collapse.routeGradient||'not detected'}; del-dot: ${collapse.delDot||collapse.divergence||'not detected'}; del-cross: ${collapse.delCross||collapse.curl||'not detected'}; 𝒞(Ψᴺ): ${collapse.coverage||String(model.closureComplete)}`],
      ['Language boundary', `T_lang: ${collapse.tLang||'boundary not detected'}`],
      ['field_witness fill', model.witnessMismatches?.length?`visible output / field_witness mismatches: ${model.witnessMismatches.length}`:'visible output and supplied field_witness have no reported mismatch']
    ];
    const block=storyKeyValueBlock('Formal Case Fill',rows,x,y,w,{fill:'#0b1220',stroke:'#64748b',titleSize:30,bodySize:20,labelSize:20,lineHeight:31,pad:30,badges:[{label:'Technical appendix',color:'#334155'}],klass:'outputGrapherStoryPanel outputGrapherKeyValuePanel outputGrapherFormalCaseFill'});
    return block;
  }
  function renderFinalProseCard(title,text,x,y,w,options={}){
    const cleaned=cleanVisibleProseBlock(text);
    if(!cleaned) return {height:0,svg:''};
    const {
      klass='outputGrapherFinalBodyProse',
      fill='#0b1220',
      stroke='#10b981',
      color=stroke,
      titleSize=34,
      bodySize=23,
      lineHeight=36,
      pad=36
    }=options;
    const paragraphs=cleaned.split(/\n{2,}/).map(item=>item.trim()).filter(Boolean);
    const innerW=w-pad*2;
    const header=renderCardHeader({x,y,width:w,title,color,titleSize,pad,titleFill:'#f8fafc',titleWeight:720});
    let cy=header.bodyY;
    const paraGap=22;
    const bodySvg=paragraphs.map(paragraph=>{
      const lines=storyWrap(paragraph,innerW,bodySize,500,0);
      const svg=storyLineText(lines,x+pad,cy,lineHeight,'#e5e7eb',bodySize,500);
      cy+=storyTextHeight(lines,lineHeight,bodySize)+paraGap;
      return svg;
    }).join('');
    const height=Math.max(header.height+storyBottomPad(pad),cy-y+storyBottomPad(pad)-paraGap-Math.ceil(bodySize*.85));
    return {
      height,
      svg:`<g class="${klass}" data-panel-width="${w}" data-inner-text-width="${innerW}" data-left-padding="${pad}" data-right-padding="${pad}" data-text-x="${x+pad}"><rect x="${x}" y="${y}" width="${w}" height="${height}" rx="22" fill="${fill}" stroke="${stroke}" stroke-width="1.8"></rect>${header.svg}${bodySvg}</g>`
    };
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
  function storyLayoutConfig(){
    return {font:22,line:34,gap:54,cardPad:42,subMinH:82,subGap:20,panelLines:0,panelPad:26};
  }
  function renderTechnicalSourceAppendix(model,x,y,w){
    const sections=model.sourceSections||[];
    const technicalOnly=sections.filter(section=>['compact_layer_a','closure_witness'].includes(section.type));
    const mrpCount=sections.filter(section=>section.type==='mid_reread_pressure').length;
    const rows=[
      ['Source preservation', `${sections.length} source section${sections.length===1?'':'s'} detected and assigned to public or technical render layers.`],
      ['Technical-only sections', technicalOnly.map(section=>section.heading).join('; ') || 'none detected'],
      ['MRP source blocks', `${mrpCount} pressure-check source block${mrpCount===1?'':'s'} preserved in the parser model and manifest.`],
      ['Public boundary', 'The default Restorative Noetic Map shows public prose first; raw witness and formal notation remain in this appendix / JSON manifest.']
    ];
    return storyKeyValueBlock('Source Preservation / Coverage',rows,x,y,w,{fill:'#0b1220',stroke:'#64748b',titleSize:30,bodySize:20,labelSize:20,lineHeight:31,pad:30,badges:[{label:'Technical appendix',color:'#334155'}],klass:'outputGrapherStoryPanel outputGrapherKeyValuePanel outputGrapherSourceCoverageAppendix'});
  }
  function renderStoryLegend(margin,y){
    return `<g class="ogSvgLegend" transform="translate(${margin} ${y-10})"><text fill="#e5e7eb" font-size="24" font-weight="900">Legend:</text><circle cx="126" cy="-8" r="8" fill="#3b82f6"/><text x="142" y="0" fill="#cbd5e1" font-size="22">B_LA baseline burden</text><circle cx="430" cy="-8" r="8" fill="#8b5cf6"/><text x="446" y="0" fill="#cbd5e1" font-size="22">B_MRP generated burden</text><circle cx="796" cy="-8" r="8" fill="#38bdf8"/><text x="812" y="0" fill="#cbd5e1" font-size="22">owner-backed move</text><circle cx="126" cy="38" r="8" fill="#22c55e"/><text x="142" y="46" fill="#cbd5e1" font-size="22">Land / closure</text><circle cx="384" cy="38" r="8" fill="#a855f7"/><text x="400" y="46" fill="#cbd5e1" font-size="22">MRP / generated route</text><circle cx="718" cy="38" r="8" fill="#f59e0b"/><text x="734" y="46" fill="#cbd5e1" font-size="22">STOP / HOLD / LoopBreak</text><circle cx="1104" cy="38" r="8" fill="#ef4444"/><text x="1120" y="46" fill="#cbd5e1" font-size="22">invalid / missing</text></g>`;
  }
  function renderStorySvg(model,options={}){
    const includeTechnicalAppendix=Boolean(options.includeTechnicalAppendix);
    const width=1800, margin=56, cardW=width-margin*2;
    const d=storyLayoutConfig();
    const burdens=model.burdens.length?model.burdens:Object.values(model.nodes).filter(n=>n.kind==='burden').map(n=>n.id);
    const verdict=verdictDigest(model);
    const caseHead=storyCaseHeadline(model);
    let y=34;
    const parts=[], introParts=[];
    introParts.push(`<text x="${margin}" y="${y+18}" fill="#f8fafc" font-size="38" font-weight="760">Output grapher — Restorative Noetic Map</text><rect x="${width-444}" y="${y-16}" width="394" height="44" rx="9" fill="#0f172a" stroke="#475569" stroke-width="1.2"></rect><text x="${width-416}" y="${y+12}" fill="#e2e8f0" font-size="19" font-weight="700">Restorative Noetic Map View</text>`);
    y+=58;
    const caseCard=storySectionBlock(caseHead.title,caseHead.subtitle,margin,y,cardW,{fill:'#0a1020',stroke:'#38bdf8',maxLines:0,titleSize:42,bodySize:27,lineHeight:40,pad:36,badges:[{label:'What this map is about',color:'#0e7490'}]});
    introParts.push(caseCard.svg); y+=caseCard.height+20;
    const verdictCard=storySectionBlock(verdict.headline,verdict.body,margin,y,cardW,{fill:'#071a12',stroke:'#10b981',maxLines:0,titleSize:38,bodySize:25,lineHeight:38,pad:34});
    introParts.push(verdictCard.svg); y+=verdictCard.height+18;
    if(model.collapseCertificate?.present){
      const cert=model.collapseCertificate, fields=cert.fields||{};
      const certItems=[
        `collapse_positive=${String(fields.collapse_positive)}`,
        `coverage_complete=${String(fields.coverage_complete)}`,
        `diagnostic_completeness=${String(fields.diagnostic_completeness)}`,
        `input_fingerprint=${fields.input_fingerprint?String(fields.input_fingerprint).slice(0,32):'missing'}`,
        `field pressure=${fields.divergence_state||'missing'}; dependency curl=${fields.curl_state||'missing'}`
      ];
      const certCard=storySectionBlock('Collapse Certificate',certificateStatusLabel(model),margin,y,cardW,{fill:'#07130c',stroke:cert.valid?'#22c55e':'#ef4444',items:certItems,technical:'Browser certificate display is advisory; proof-mode agreement still belongs to the Python certificate-backed checker.',maxLines:0,titleSize:30,bodySize:21,lineHeight:32,pad:32,badges:[{label:cert.valid?'certificate sidecar':'invalid certificate sidecar',color:cert.valid?'#166534':'#991b1b'}],klass:'outputGrapherStoryPanel outputGrapherKeyValuePanel outputGrapherCertificateDisplay'});
      introParts.push(certCard.svg); y+=certCard.height+18;
    }
    const claimCard=storySectionBlock('Reply / claim being rejected',readerInputDigest(model),margin,y,cardW,{fill:'#111827',stroke:'#475569',maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34});
    introParts.push(claimCard.svg); y+=claimCard.height+18;
    const diagCard=storySectionBlock('What the reply depends on',diagnosisDigest(model,burdens),margin,y,cardW,{fill:'#0b1220',stroke:'#475569',items:diagnosisItems(model,burdens),technical:technicalDiagnosis(model),maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34});
    introParts.push(diagCard.svg); y+=diagCard.height+18;
    if(model.bodyExtract?.bannerText||model.bodyExtract?.compactLayerA||model.hasLayerA){
      const structureIntro=storySectionBlock('What structure was detected',publicStructureDigest(model,burdens),margin,y,cardW,{fill:'#0b1220',stroke:'#64748b',items:publicStructureItems(model,burdens),technical:publicTechnicalGloss(model),maxLines:0,titleSize:28,bodySize:21,lineHeight:33,pad:32,klass:'outputGrapherStoryPanel outputGrapherStructureDigest'});
      introParts.push(structureIntro.svg); y+=structureIntro.height+18;
    }
    const invItems=baselineBurdenLabels(model,12);
    const invCard=storySectionBlock('Main problems in the reply',invItems.join('; ')||'not detected',margin,y,cardW,{fill:'#07111f',stroke:'#3b82f6',items:invItems.length?invItems:null,technical:'B_LA only; generated B_MRP burdens are not backfilled into this baseline list.',maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34});
    introParts.push(invCard.svg); y+=invCard.height+28;
    const generatedItems=generatedBurdenLabels(model,12);
    if(generatedItems.length){
      const generatedCard=storySectionBlock('Preempted problems surfaced by reread',generatedItems.join('; '),margin,y,cardW,{fill:'#14102a',stroke:'#8b5cf6',items:generatedItems,technical:'B_MRP; generated by MRP after a burden landed and absent from B_LA.',maxLines:0,titleSize:30,bodySize:22,lineHeight:34,pad:34,badges:[{label:'B_MRP',color:'#6d28d9'}]});
      introParts.push(generatedCard.svg); y+=generatedCard.height+28;
    }
    parts.push(`<g class="outputGrapherStorySection outputGrapherIntroSection" data-og-section="intro">${introParts.join('')}</g>`);
    burdens.forEach((b,index)=>{
      const sms=model.submoves[b]||[];
      const burden=model.nodes[b]||{label:b};
      const land=model.nodes[`Land(${b})`]||model.nodes[`HOLD(${b})`];
      const reread=model.nodes[`R(H,Δ)@${b}`];
      const mrp=model.mrp[b]||{};
      const routes=(mrp.routes||[]).join(', ')||'not detected';
      const result=publicRouteType(routeResultType(model,b));
      const generatedBy=model.generatedBurdens[b];
      const burdenColor=generatedBy?'#8b5cf6':'#3b82f6';
      const burdenFill=generatedBy?'#14102a':'#07111f';
      const burdenStroke=generatedBy?'#8b5cf6':'#263044';
      const titleText=`${issueLabel(b)} — ${bodyBurdenDescription(model,b)}`;
      const problemText=(generatedBy?`Generated by ${generatedBy}. Technical: ${b} ∈ B_MRP, absent from B_LA. `:'Baseline Layer-A burden. Technical: B_LA. ')+'Problem from the visible output: '+bodyBurdenDescription(model,b);
      const burdenHeader=renderCardHeader({
        x:margin,
        y,
        width:cardW,
        title:titleText,
        subtitle:problemText,
        color:burdenColor,
        titleSize:34,
        subtitleSize:22,
        pad:34,
        titleWeight:720
      });
      const moveBlocks=sms.map(sm=>{
        const node=model.nodes[sm]||{label:sm};
        const sections=bodySubmoveSections(model,sm,node);
        const measured=measureSubmoveSections(sections,cardW-68,d);
        return {sm,node,...measured};
      });
      const moveBlockH=moveBlocks.reduce((sum,block,i)=>sum+block.height+(i?d.subGap:0),0);
      const setupText=bodyBurdenSetupText(model,b);
      const setupBlock=setupText?storySectionBlock(publicSourceSetupTitle(model,b),setupText,margin+34,burdenHeader.bodyY+18,cardW-68,{fill:'#0b1220',stroke:'#64748b',items:sourceBlockLines(setupText),technical:sourceSectionTitle(model,b),maxLines:0,titleSize:24,bodySize:20,lineHeight:31,pad:26,klass:'outputGrapherStoryPanel outputGrapherSourceSetup'}):{height:0,svg:''};
      const movesTitleY=(setupBlock.svg?burdenHeader.bodyY+18+setupBlock.height+34:burdenHeader.bodyY+18)-y;
      const firstMoveY=movesTitleY+50;
      const panelTop=firstMoveY+moveBlockH+34;
      const fullW=cardW-60, panelGap=24, panelX=margin+30;
      const landText=bodyLandText(model,b,land);
      const landBlock=storySectionBlock('What this establishes',landText,panelX,y+panelTop,fullW,{fill:'#052e16',stroke:'#22c55e',items:splitListLikeItems(landText),maxLines:d.panelLines,titleSize:26,bodySize:22,lineHeight:34,pad:d.panelPad,badges:[{label:`Land(${b})`,color:'#14532d'}]});
      const rereadY=y+panelTop+landBlock.height+panelGap;
      const rereadText=bodyRereadText(model,b,reread);
      const rereadBlock=storySectionBlock('After this, what remains?',rereadText,panelX,rereadY,fullW,{fill:'#451a03',stroke:'#f59e0b',items:splitListLikeItems(rereadText),maxLines:d.panelLines,titleSize:26,bodySize:22,lineHeight:34,pad:d.panelPad,badges:[{label:'R(H,Δ)',color:'#7c2d12'}]});
      const bottomPanelY=rereadY+rereadBlock.height+panelGap;
      const edgeText=(mrp.edges||[]).map(e=>issueGraph(e[0],e[1])).join(', ')||'none';
      const mrpRows=mrpPanelRows(model,b,result,edgeText,routes,rereadText);
      const mrpBlock=storyKeyValueBlock('Follow-up: pressure-check',mrpRows,panelX,bottomPanelY,fullW,{fill:'#2e1065',stroke:'#a855f7',titleSize:26,bodySize:21,lineHeight:32,pad:d.panelPad,badges:[{label:`MRP(${b})`,color:'#581c87'}]});
      const mrpSourceY=bottomPanelY+mrpBlock.height+18;
      const mrpSourceBlock={height:0,svg:''};
      const nextBurden=burdens[index+1]||'';
      const routeItems=routePanelItems(model,b,nextBurden,routes,result);
      const routeY=mrpSourceY+(mrpSourceBlock.svg?mrpSourceBlock.height+18:0);
      const routeBlock=renderRouteRow('Next step',routeItems,routes,panelX,routeY,fullW,{titleSize:24,bodySize:21,lineHeight:32,pad:d.panelPad});
      const bottomRowH=mrpBlock.height+18+(mrpSourceBlock.svg?mrpSourceBlock.height+18:0)+routeBlock.height;
      const cardH=bottomPanelY-y+bottomRowH+38;
      parts.push(`<g class="outputGrapherStorySection outputGrapherStoryBurden" data-og-section="burden" data-burden="${esc(b)}"><rect x="${margin}" y="${y}" width="${cardW}" height="${cardH}" rx="24" fill="${burdenFill}" stroke="${burdenStroke}" stroke-width="${generatedBy?'2.4':'1.5'}"></rect>${burdenHeader.svg}`);
      if(setupBlock.svg) parts.push(setupBlock.svg);
      parts.push(`<text x="${margin+34}" y="${y+movesTitleY}" fill="#bae6fd" font-size="28" font-weight="900">How this problem is answered</text>`);
      let subY=y+firstMoveY;
      moveBlocks.forEach((block)=>{
        parts.push(`<g class="outputGrapherStorySubmove outputGrapherSingleColumnPanel" data-panel-width="${cardW-68}" data-inner-text-width="${cardW-68-48}" data-left-padding="24" data-right-padding="24" data-text-x="${margin+58}"><rect x="${margin+34}" y="${subY-34}" width="${cardW-68}" height="${block.height}" rx="15" fill="#0b3142" stroke="#38bdf8" stroke-width="1.3"></rect>${renderSubmoveSections(block,margin+34,subY-34,cardW-68)}</g>`);
        subY+=block.height+d.subGap;
      });
      parts.push(landBlock.svg);
      parts.push(rereadBlock.svg);
      parts.push(mrpBlock.svg);
      if(mrpSourceBlock.svg) parts.push(mrpSourceBlock.svg);
      parts.push(routeBlock.svg);
      parts.push('</g>');
      y+=cardH+d.gap;
    });
    const restorationParts=[];
    const collapsePanel=renderCollapsePanel(model,margin,y,cardW);
    restorationParts.push(collapsePanel.svg); y+=collapsePanel.height+52;
    const restorativeCard=renderFinalProseCard('Restorative Response',model.restorativeResponse,margin,y,cardW,{klass:'outputGrapherFinalBodyProse outputGrapherRestorativeResponse',fill:'#071a12',stroke:'#10b981',color:'#22c55e'});
    if(restorativeCard.svg){restorationParts.push(restorativeCard.svg); y+=restorativeCard.height+34;}
    const closingCard=renderFinalProseCard('Closing Formulation',model.closingFormulation,margin,y,cardW,{klass:'outputGrapherFinalBodyProse outputGrapherClosingFormulation',fill:'#111827',stroke:'#38bdf8',color:'#38bdf8'});
    if(closingCard.svg){restorationParts.push(closingCard.svg); y+=closingCard.height+52;}
    parts.push(`<g class="outputGrapherStorySection outputGrapherRestorationSection" data-og-section="restoration">${restorationParts.join('')}</g>`);
    if(includeTechnicalAppendix){
      const formalParts=[];
      const closureWitnessText=bodyClosureWitnessText(model);
      if(closureWitnessText){
        const closureWitnessCard=storySectionBlock('Closure/Reconstruction Witness',closureWitnessText,margin,y,cardW,{fill:'#0b1220',stroke:'#64748b',items:sourceBlockLines(closureWitnessText),maxLines:0,titleSize:30,bodySize:20,lineHeight:31,pad:30,klass:'outputGrapherStoryPanel outputGrapherClosureWitnessSource'});
        formalParts.push(closureWitnessCard.svg); y+=closureWitnessCard.height+34;
      }
      const formalCaseFill=renderFormalCaseFill(model,margin,y,cardW);
      formalParts.push(formalCaseFill.svg); y+=formalCaseFill.height+34;
      const sourceCoverage=renderTechnicalSourceAppendix(model,margin,y,cardW);
      formalParts.push(sourceCoverage.svg); y+=sourceCoverage.height+44;
      formalParts.push(renderStoryLegend(margin,y));
      parts.push(`<g class="outputGrapherStorySection outputGrapherFormalSection" data-og-section="formal">${formalParts.join('')}</g>`);
    }else{
      parts.push(renderStoryLegend(margin,y));
    }
    const height=y+78;
    return `<svg id="ogSvg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" font-family="Segoe UI, Arial, sans-serif" role="img" aria-label="Restorative noetic map infographic"><rect x="0" y="0" width="${width}" height="${height}" fill="#050914"/><defs><marker id="ogArrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>${parts.join('')}</svg>`;
  }

  function renderGraph(model){
    currentModel=model;
    if(currentGraphMode==='rebuttal') return renderStorySvg(model,{includeTechnicalAppendix:true});
    const pos={}, width=1780, nodeH=76, rowH=82, laneGap=56, left=36;
    const burdens=model.burdens.length?model.burdens:Object.values(model.nodes).filter(n=>n.kind==='burden').map(n=>n.id);
    const inputNode={id:'input',kind:'input',label:`What the claim says — ${readerInputDigest(model)}`,excerpt:readerInputDigest(model)};
    const diagNode={id:'diagnosis',kind:'input',label:`What the claim depends on — ${model.fieldType||'field not detected'} / ${model.claimType||'claim not detected'}`,excerpt:model.diagnosis||''};
    const ledgerLabel=`B_LA=${(model.ledger.B_LA.length?model.ledger.B_LA:model.initialBurdens).map(normalizeBurden).join(', ')||'not detected'}; B_MRP=${(model.ledger.B_MRP.length?model.ledger.B_MRP:Object.keys(model.generatedBurdens||{})).map(normalizeBurden).join(', ')||'none'}`;
    const invNode={id:'inventory',kind:'input',label:`Main problems the input creates — ${ledgerLabel}`,excerpt:model.liveBurden||''};
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
    const legend=`<g class="ogSvgLegend" transform="translate(36 ${height-36})"><text fill="#e5e7eb" font-size="12" font-weight="800">Legend:</text><circle cx="72" cy="-4" r="5" fill="#3b82f6"/><text x="82" y="0" fill="#cbd5e1" font-size="11">B_LA burden</text><circle cx="174" cy="-4" r="5" fill="#8b5cf6"/><text x="184" y="0" fill="#cbd5e1" font-size="11">B_MRP generated</text><circle cx="306" cy="-4" r="5" fill="#38bdf8"/><text x="316" y="0" fill="#cbd5e1" font-size="11">submove/TTP</text><circle cx="418" cy="-4" r="5" fill="#22c55e"/><text x="428" y="0" fill="#cbd5e1" font-size="11">Land/closure</text><circle cx="538" cy="-4" r="5" fill="#a855f7"/><text x="548" y="0" fill="#cbd5e1" font-size="11">MRP</text><circle cx="618" cy="-4" r="5" fill="#f59e0b"/><text x="628" y="0" fill="#cbd5e1" font-size="11">route/HOLD</text><circle cx="736" cy="-4" r="5" fill="#ef4444"/><text x="746" y="0" fill="#cbd5e1" font-size="11">invalid</text></g>`;
    return `<svg id="ogSvg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" font-family="Segoe UI, Arial, sans-serif" role="img" aria-label="Noetic field rebuttal infographic"><rect x="0" y="0" width="${width}" height="${height}" fill="#050914"/><defs><marker id="ogArrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#64748b"/></marker></defs>${topEdges}${clusterSvg.join('')}${edgeSvg}${inputBurdenEdges}${mrpRelationEdges.join('')}${closureEdge}${renderedNodes}${finalPanel}${legend}</svg>`;
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
    ['ogExportPngBtn','ogExportPngSectionsBtn','ogExportSvgBtn','ogExportJsonBtn','ogExportMermaidBtn'].forEach(id=>{const b=document.getElementById(id); if(b) b.disabled=false;});
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
  function cloneSvgForExport(svg,padding=56){
    const clone=svg.cloneNode(true);
    const vb=svg.viewBox.baseVal;
    const width=vb.width||svg.width.baseVal.value;
    const height=vb.height||svg.height.baseVal.value;
    clone.setAttribute('viewBox',`${-padding} ${-padding} ${width+padding*2} ${height+padding*2}`);
    clone.setAttribute('width',String(width+padding*2));
    clone.setAttribute('height',String(height+padding*2));
    const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
    bg.setAttribute('x',String(-padding));
    bg.setAttribute('y',String(-padding));
    bg.setAttribute('width',String(width+padding*2));
    bg.setAttribute('height',String(height+padding*2));
    bg.setAttribute('fill','#050914');
    clone.insertBefore(bg,clone.firstChild);
    return clone;
  }
  function svgGeometry(svg){
    const vb=svg.viewBox.baseVal;
    return {
      x:vb.x||0,
      y:vb.y||0,
      width:vb.width||svg.width.baseVal.value,
      height:vb.height||svg.height.baseVal.value
    };
  }
  function svgElementBounds(el){
    if(!el||!el.getBBox) return null;
    const box=el.getBBox();
    const matrix=el.getCTM&&el.getCTM();
    const svg=el.ownerSVGElement||el;
    if(!matrix||!svg.createSVGPoint){
      return {x:box.x,y:box.y,width:box.width,height:box.height};
    }
    const point=svg.createSVGPoint();
    const corners=[
      [box.x,box.y],
      [box.x+box.width,box.y],
      [box.x,box.y+box.height],
      [box.x+box.width,box.y+box.height]
    ].map(([x,y])=>{
      point.x=x; point.y=y;
      return point.matrixTransform(matrix);
    });
    const xs=corners.map(p=>p.x), ys=corners.map(p=>p.y);
    const x=Math.min(...xs), y=Math.min(...ys);
    return {x,y,width:Math.max(...xs)-x,height:Math.max(...ys)-y};
  }
  function buildSectionExportSvg(){
    const visible=document.getElementById('ogSvg');
    if(!currentModel) return {svg:visible,cleanup:()=>{}};
    const host=document.createElement('div');
    host.setAttribute('data-output-grapher-export-host','true');
    host.style.position='absolute';
    host.style.left='-100000px';
    host.style.top='0';
    host.style.width='1800px';
    host.style.pointerEvents='none';
    host.style.opacity='0';
    host.innerHTML=renderStorySvg(currentModel,{includeTechnicalAppendix:true});
    document.body.appendChild(host);
    return {svg:host.querySelector('svg'),cleanup:()=>host.remove()};
  }
  function cropSvgForExport(svg,crop,padding=56){
    const clone=svg.cloneNode(true);
    const x=Number.isFinite(crop.viewX)?crop.viewX:Math.max(0,crop.x-padding);
    const y=Number.isFinite(crop.viewY)?crop.viewY:Math.max(0,crop.y-padding);
    const width=Number.isFinite(crop.viewWidth)?crop.viewWidth:crop.width+padding*2;
    const height=Number.isFinite(crop.viewHeight)?crop.viewHeight:crop.height+padding*2;
    clone.setAttribute('viewBox',`${x} ${y} ${width} ${height}`);
    clone.setAttribute('width',String(width));
    clone.setAttribute('height',String(height));
    const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
    bg.setAttribute('x',String(x));
    bg.setAttribute('y',String(y));
    bg.setAttribute('width',String(width));
    bg.setAttribute('height',String(height));
    bg.setAttribute('fill','#050914');
    clone.insertBefore(bg,clone.firstChild);
    return clone;
  }
  function exportCoverageReport(){
    const svg=document.getElementById('ogSvg');
    if(!svg) return null;
    const exportBuild=buildSectionExportSvg();
    const exportSvg=exportBuild.svg||svg;
    const geom=svgGeometry(svg);
    const burdenCards=[...svg.querySelectorAll('.outputGrapherStoryBurden')].map(svgElementBounds).filter(Boolean);
    const restoration=svgElementBounds(svg.querySelector('.outputGrapherRestorationSummary'));
    const restorativeResponse=svgElementBounds(svg.querySelector('.outputGrapherRestorativeResponse'));
    const closingFormulation=svgElementBounds(svg.querySelector('.outputGrapherClosingFormulation'));
    const formalCaseFill=svgElementBounds(exportSvg.querySelector('.outputGrapherFormalCaseFill'));
    const legend=svgElementBounds(svg.querySelector('.ogSvgLegend'));
    const finalBurden=burdenCards[burdenCards.length-1]||null;
    const terminalBottom=Math.max(
      restoration?restoration.y+restoration.height:0,
      restorativeResponse?restorativeResponse.y+restorativeResponse.height:0,
      closingFormulation?closingFormulation.y+closingFormulation.height:0
    );
    const bottom=Math.max(
      finalBurden?finalBurden.y+finalBurden.height:0,
      terminalBottom,
      legend?legend.y+legend.height:0
    );
    const cfg=pngExportConfig();
    const exportPadding=56;
    const paddedHeight=geom.height+exportPadding*2;
    const paddedWidth=geom.width+exportPadding*2;
    const scale=cfg.width/paddedWidth;
    const oneShotCanvasSafe=canvasSafetyForDimensions(paddedWidth*scale,paddedHeight*scale);
    const sectionCrops=storySectionCrops(exportSvg);
    const sectionedCanvasSafe=sectionCrops.length>0&&sectionCrops.every(section=>section.canvasSafe);
    const bottomPadding=Math.round(geom.height-bottom);
    const report={
      contentHeight:geom.height,
      contentWidth:geom.width,
      paddedExportHeight:paddedHeight,
      paddedExportWidth:paddedWidth,
      pngWidth:Math.round(paddedWidth*scale),
      pngHeight:Math.round(paddedHeight*scale),
      hasFinalBurden:Boolean(finalBurden),
      hasRestorationSummary:Boolean(restoration),
      hasRestorativeResponse:Boolean(restorativeResponse),
      hasClosingFormulation:Boolean(closingFormulation),
      hasFormalCaseFill:Boolean(formalCaseFill),
      hasLegend:Boolean(legend),
      bottomContentY:Math.round(bottom),
      bottomPadding,
      postTerminalCardBottomPadding:Math.round(geom.height-terminalBottom),
      postLegendBottomPadding:legend?Math.round(geom.height-(legend.y+legend.height)):null,
      legendGapAfterTerminal:legend&&terminalBottom?Math.round(legend.y-terminalBottom):null,
      exportPadding,
      exportedBottomPadding:bottomPadding+exportPadding,
      burdenCardCount:burdenCards.length,
      exportedBurdenCardCount:burdenCards.length,
      sectionedExportType:'zip',
      sectionedExportCount:sectionCrops.length,
      hasSectionManifest:true,
      oneShotCanvasSafe,
      sectionedCanvasSafe,
      canvasSafe:oneShotCanvasSafe||sectionedCanvasSafe
    };
    exportBuild.cleanup();
    return report;
  }
  function exportSvg(){const svg=document.getElementById('ogSvg'); if(svg) downloadBlob('daee-output-collapse-graph.svg','image/svg+xml;charset=utf-8',new XMLSerializer().serializeToString(cloneSvgForExport(svg)));}
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
  function pngExportConfig(){
    const mode=document.getElementById('ogExportWidthMode')?.value||'poster';
    const widths={compact:1500,desktop:1800,poster:2200};
    return {mode,width:widths[mode]||widths.desktop};
  }
  function exportPng(){
    const svg=document.getElementById('ogSvg'); if(!svg) return;
    const exportSvgNode=cloneSvgForExport(svg);
    const naturalW=exportSvgNode.viewBox.baseVal.width||exportSvgNode.width.baseVal.value;
    const naturalH=exportSvgNode.viewBox.baseVal.height||exportSvgNode.height.baseVal.value;
    const cfg=pngExportConfig();
    const scale=cfg.width/naturalW;
    if(!canvasSafetyForDimensions(naturalW*scale,naturalH*scale)){
      exportPngSections();
      return;
    }
    renderPngBlobFromSvgNode(exportSvgNode,cfg.width).then(png=>{
      if(png) downloadBlob(`daee-output-collapse-graph-${cfg.mode}.png`,'image/png',png);
    });
  }
  function nextAnimationFrame(){
    return new Promise(resolve=>requestAnimationFrame(()=>resolve()));
  }
  async function waitForExportLayout(){
    if(document.fonts?.ready){
      try{await document.fonts.ready;}catch(err){}
    }
    if(typeof requestAnimationFrame==='function'){
      await nextAnimationFrame();
      await nextAnimationFrame();
    }
  }
  const BROWSER_CANVAS_SIDE_LIMIT=30000;
  const BROWSER_CANVAS_PIXEL_LIMIT=240000000;
  const EXPORT_CANVAS_SIDE_TARGET=28000;
  const EXPORT_CANVAS_PIXEL_TARGET=220000000;
  function canvasSafetyForDimensions(width,height){
    return width>0&&height>0&&width<BROWSER_CANVAS_SIDE_LIMIT&&height<BROWSER_CANVAS_SIDE_LIMIT&&width*height<BROWSER_CANVAS_PIXEL_LIMIT;
  }
  function safePngTargetWidthForDimensions(naturalW,naturalH,preferredWidth){
    if(!naturalW||!naturalH) return preferredWidth;
    let safeWidth=preferredWidth;
    safeWidth=Math.min(safeWidth,Math.floor((EXPORT_CANVAS_SIDE_TARGET*naturalW)/naturalH));
    safeWidth=Math.min(safeWidth,Math.floor(Math.sqrt((EXPORT_CANVAS_PIXEL_TARGET*naturalW)/naturalH)));
    return Math.max(480,Math.min(preferredWidth,safeWidth||preferredWidth));
  }
  function plannedPngDimensionsForCrop(width,height,preferredWidth){
    const targetWidth=safePngTargetWidthForDimensions(width,height,preferredWidth);
    const scale=targetWidth/width;
    const pngWidth=Math.round(width*scale);
    const pngHeight=Math.round(height*scale);
    return {width:pngWidth,height:pngHeight,targetWidth,canvasSafe:canvasSafetyForDimensions(pngWidth,pngHeight)};
  }
  function sectionBoundsPayload(bounds){
    if(!bounds) return null;
    return {
      x:bounds.x,
      y:bounds.y,
      width:bounds.width,
      height:bounds.height,
      top:bounds.y,
      bottom:bounds.y+bounds.height
    };
  }
  function storySemanticSections(svg){
    return [...svg.querySelectorAll('[data-og-section]')]
      .map((el,index)=>({
        el,
        index,
        type:el.getAttribute('data-og-section')||'unknown',
        burden:el.getAttribute('data-burden')||'',
        bounds:svgElementBounds(el)
      }))
      .filter(section=>section.bounds&&section.bounds.height>0)
      .sort((a,b)=>(a.bounds.y-b.bounds.y)||(a.index-b.index));
  }
  function boundedSectionCrop(section,index,sections,geom,name,title,order){
    const semantic=sectionBoundsPayload(section.bounds);
    const prev=sections[index-1]?sectionBoundsPayload(sections[index-1].bounds):null;
    const next=sections[index+1]?sectionBoundsPayload(sections[index+1].bounds):null;
    const horizontalPad=56;
    const verticalBleed=24;
    const sectionTop=semantic.top;
    const sectionBottom=semantic.bottom;
    const previousBottom=prev?prev.bottom:null;
    const nextTop=next?next.top:null;
    const topGap=previousBottom===null?sectionTop:Math.max(0,sectionTop-previousBottom);
    const bottomGap=nextTop===null?Math.max(0,geom.height-sectionBottom):Math.max(0,nextTop-sectionBottom);
    const topBleed=section.type==='intro'?0:Math.min(verticalBleed,Math.max(0,topGap-1));
    const bottomBleed=Math.min(verticalBleed,Math.max(0,bottomGap-1));
    const viewY=Math.floor(Math.max(0,sectionTop-topBleed));
    const maxBottom=nextTop===null?geom.height:Math.max(sectionBottom,nextTop-1);
    const viewBottom=Math.ceil(Math.min(geom.height,maxBottom,sectionBottom+bottomBleed));
    const viewHeight=Math.max(1,viewBottom-viewY);
    const viewX=-horizontalPad;
    const viewWidth=geom.width+horizontalPad*2;
    const sourceCrop={x:viewX,y:viewY,width:viewWidth,height:viewHeight};
    const foreignSectionOverlap=Boolean(
      (previousBottom!==null&&viewY<previousBottom-0.25)||
      (nextTop!==null&&viewY+viewHeight>nextTop+0.25)
    );
    const sourceCanvasSafe=canvasSafetyForDimensions(viewWidth,viewHeight);
    const plannedPng=plannedPngDimensionsForCrop(viewWidth,viewHeight,pngExportConfig().width);
    const canvasSafe=plannedPng.canvasSafe;
    return {
      name,
      title,
      type:section.type,
      order,
      burden:section.burden,
      x:viewX,
      y:viewY,
      width:viewWidth,
      height:viewHeight,
      viewX,
      viewY,
      viewWidth,
      viewHeight,
      semanticBounds:semantic,
      sourceCrop,
      previousSectionBottom:previousBottom,
      nextSectionTop:nextTop,
      foreignSectionOverlap,
      sourceCanvasSafe,
      plannedPng,
      canvasSafe
    };
  }
  function storySectionCrops(svg){
    const geom=svgGeometry(svg);
    const semanticSections=storySemanticSections(svg);
    if(semanticSections.length){
      let burdenCount=0;
      return semanticSections.map((section,index)=>{
        if(section.type==='intro'){
          return boundedSectionCrop(section,index,semanticSections,geom,'01-intro-case-and-verdict.png','Intro, case, verdict, reply, dependencies, and live burdens',1);
        }
        if(section.type==='burden'){
          burdenCount+=1;
          return boundedSectionCrop(section,index,semanticSections,geom,`${String(burdenCount+1).padStart(2,'0')}-burden-${burdenCount}.png`,`Burden ${burdenCount}`,burdenCount+1);
        }
        if(section.type==='restoration'){
          return boundedSectionCrop(section,index,semanticSections,geom,`${String(burdenCount+2).padStart(2,'0')}-restoration-summary.png`,'Restoration Summary, Restorative Response, and Closing Formulation',burdenCount+2);
        }
        if(section.type==='formal'){
          return boundedSectionCrop(section,index,semanticSections,geom,`${String(burdenCount+3).padStart(2,'0')}-formal-reconstruction.png`,'Formal Reconstruction and technical appendix',burdenCount+3);
        }
        return boundedSectionCrop(section,index,semanticSections,geom,`${String(index+1).padStart(2,'0')}-${safe(section.type)}.png`,section.type,index+1);
      }).filter(section=>section.height>80);
    }
    const burdenGroups=[...svg.querySelectorAll('.outputGrapherStoryBurden')].map(svgElementBounds).filter(Boolean);
    const crops=[];
    const addCrop=(name,title,type,y,height)=>{
      const top=Math.max(0,Math.floor(y));
      const bottom=Math.min(geom.height,Math.ceil(y+height));
      if(bottom-top>80) crops.push({name,title,type,x:0,y:top,width:geom.width,height:bottom-top});
    };
    if(burdenGroups.length){
      const first=burdenGroups[0];
      addCrop('01-intro-case-and-verdict.png','Intro, case, verdict, reply, dependencies, and live burdens','intro',0,first.y);
      burdenGroups.forEach((box,i)=>addCrop(`${String(i+2).padStart(2,'0')}-burden-${i+1}.png`,`Burden ${i+1}`,'burden',box.y,box.height));
      const restorationEls=[
        svg.querySelector('.outputGrapherRestorationSummary'),
        svg.querySelector('.outputGrapherRestorativeResponse'),
        svg.querySelector('.outputGrapherClosingFormulation')
      ].map(svgElementBounds).filter(Boolean);
      const formalBox=svgElementBounds(svg.querySelector('.outputGrapherFormalCaseFill'));
      const legendBox=svgElementBounds(svg.querySelector('.ogSvgLegend'));
      if(restorationEls.length){
        const top=Math.min(...restorationEls.map(box=>box.y));
        const bottom=Math.max(...restorationEls.map(box=>box.y+box.height));
        addCrop(`${String(burdenGroups.length+2).padStart(2,'0')}-restoration-summary.png`,'Restoration Summary, Restorative Response, and Closing Formulation','restoration',top,bottom-top);
      }
      if(formalBox){
        const top=formalBox.y;
        const bottom=Math.max(formalBox.y+formalBox.height,legendBox?legendBox.y+legendBox.height:0);
        addCrop(`${String(burdenGroups.length+3).padStart(2,'0')}-formal-reconstruction.png`,'Formal Reconstruction and technical appendix','formal',top,bottom-top);
      }else if(legendBox){
        addCrop(`${String(burdenGroups.length+3).padStart(2,'0')}-formal-reconstruction.png`,'Legend and technical appendix','formal',legendBox.y,legendBox.height);
      }
    }else{
      addCrop('01-restorative-noetic-map.png','Restorative Noetic Map','full',0,geom.height);
    }
    return crops;
  }
  function sectionExportPlan(){
    const build=buildSectionExportSvg();
    const plan=build.svg?storySectionCrops(build.svg):[];
    build.cleanup();
    return plan;
  }
  function renderPngBlobFromSvgNode(svgNode,targetWidth){
    return new Promise(resolve=>{
    const raw=new XMLSerializer().serializeToString(svgNode);
    const blob=new Blob([raw],{type:'image/svg+xml;charset=utf-8'});
    const url=URL.createObjectURL(blob), img=new Image();
    img.onload=()=>{
      const naturalW=svgNode.viewBox.baseVal.width||svgNode.width.baseVal.value;
      const naturalH=svgNode.viewBox.baseVal.height||svgNode.height.baseVal.value;
      const scale=targetWidth/naturalW;
      const canvas=document.createElement('canvas');
      canvas.width=Math.round(naturalW*scale);
      canvas.height=Math.round(naturalH*scale);
      const ctx=canvas.getContext('2d');
      ctx.fillStyle='#050914';
      ctx.fillRect(0,0,canvas.width,canvas.height);
      ctx.drawImage(img,0,0,canvas.width,canvas.height);
      canvas.toBlob(png=>{URL.revokeObjectURL(url); resolve(png);},'image/png');
    };
    img.onerror=()=>{URL.revokeObjectURL(url); resolve(null);}; img.src=url;
    });
  }
  function safePngTargetWidthForSection(svgNode,preferredWidth){
    const naturalW=svgNode.viewBox.baseVal.width||svgNode.width.baseVal.value;
    const naturalH=svgNode.viewBox.baseVal.height||svgNode.height.baseVal.value;
    return safePngTargetWidthForDimensions(naturalW,naturalH,preferredWidth);
  }
  function zipCrc32(bytes){
    if(!zipCrc32.table){
      zipCrc32.table=Array.from({length:256},(_,n)=>{
        let c=n;
        for(let k=0;k<8;k++) c=(c&1)?(0xedb88320^(c>>>1)):(c>>>1);
        return c>>>0;
      });
    }
    let crc=0xffffffff;
    for(let i=0;i<bytes.length;i++) crc=zipCrc32.table[(crc^bytes[i])&0xff]^(crc>>>8);
    return (crc^0xffffffff)>>>0;
  }
  function zipDosDateTime(date=new Date()){
    const time=(date.getHours()<<11)|(date.getMinutes()<<5)|Math.floor(date.getSeconds()/2);
    const dosDate=((date.getFullYear()-1980)<<9)|((date.getMonth()+1)<<5)|date.getDate();
    return {time,dosDate};
  }
  async function createZipBlob(files){
    const enc=new TextEncoder();
    const chunks=[], central=[];
    let offset=0;
    const {time,dosDate}=zipDosDateTime();
    for(const file of files){
      const nameBytes=enc.encode(file.name);
      const data=new Uint8Array(await file.blob.arrayBuffer());
      const crc=zipCrc32(data);
      const local=new ArrayBuffer(30+nameBytes.length);
      const view=new DataView(local);
      view.setUint32(0,0x04034b50,true);
      view.setUint16(4,20,true);
      view.setUint16(6,0,true);
      view.setUint16(8,0,true);
      view.setUint16(10,time,true);
      view.setUint16(12,dosDate,true);
      view.setUint32(14,crc,true);
      view.setUint32(18,data.length,true);
      view.setUint32(22,data.length,true);
      view.setUint16(26,nameBytes.length,true);
      view.setUint16(28,0,true);
      const localBytes=new Uint8Array(local);
      localBytes.set(nameBytes,30);
      chunks.push(localBytes,data);
      const centralHeader=new ArrayBuffer(46+nameBytes.length);
      const cv=new DataView(centralHeader);
      cv.setUint32(0,0x02014b50,true);
      cv.setUint16(4,20,true);
      cv.setUint16(6,20,true);
      cv.setUint16(8,0,true);
      cv.setUint16(10,0,true);
      cv.setUint16(12,time,true);
      cv.setUint16(14,dosDate,true);
      cv.setUint32(16,crc,true);
      cv.setUint32(20,data.length,true);
      cv.setUint32(24,data.length,true);
      cv.setUint16(28,nameBytes.length,true);
      cv.setUint16(30,0,true);
      cv.setUint16(32,0,true);
      cv.setUint16(34,0,true);
      cv.setUint16(36,0,true);
      cv.setUint32(38,0,true);
      cv.setUint32(42,offset,true);
      const centralBytes=new Uint8Array(centralHeader);
      centralBytes.set(nameBytes,46);
      central.push(centralBytes);
      offset+=localBytes.length+data.length;
    }
    const centralOffset=offset;
    const centralSize=central.reduce((sum,item)=>sum+item.length,0);
    chunks.push(...central);
    const end=new ArrayBuffer(22);
    const ev=new DataView(end);
    ev.setUint32(0,0x06054b50,true);
    ev.setUint16(4,0,true);
    ev.setUint16(6,0,true);
    ev.setUint16(8,files.length,true);
    ev.setUint16(10,files.length,true);
    ev.setUint32(12,centralSize,true);
    ev.setUint32(16,centralOffset,true);
    ev.setUint16(20,0,true);
    chunks.push(new Uint8Array(end));
    return new Blob(chunks,{type:'application/zip'});
  }
  function sourceCoverageManifest(model,sections){
    const cropFor=(sourceSection)=>{
      const assigned=sourceSection.assignedRenderSection||'unassigned';
      if(assigned==='intro') return sections.find(section=>section.type==='intro');
      if(assigned==='restoration') return sections.find(section=>section.type==='restoration');
      if(assigned==='formal') return sections.find(section=>section.type==='formal');
      const burdenMatch=assigned.match(/^burden:(.+)$/);
      if(burdenMatch) return sections.find(section=>section.type==='burden'&&section.burden===burdenMatch[1]);
      return null;
    };
    const isRendered=(section)=>{
      const b=section.burden;
      if(section.type==='banner') return Boolean(model.bodyExtract?.bannerText);
      if(section.type==='compact_layer_a') return Boolean(model.bodyExtract?.compactLayerA);
      if(section.type==='burden') return Boolean(b&&model.burdens?.includes(b));
      if(section.type==='burden_setup') return Boolean(b&&model.bodyExtract?.burdenSetupTexts?.[b]);
      if(section.type==='hidden_premises') return Boolean(b&&model.bodyExtract?.hiddenPremiseTexts?.[b]);
      if(section.type==='submove') return true;
      if(section.type==='land') return Boolean(b&&model.bodyExtract?.landTexts?.[b]);
      if(section.type==='mid_reread_pressure') return Boolean(b&&model.bodyExtract?.mrpSourceTexts?.[b]);
      if(section.type==='closure_witness') return Boolean(model.bodyExtract?.closureWitnessText);
      if(section.type==='restorative_response') return Boolean(model.restorativeResponse);
      if(section.type==='closing_formulation') return Boolean(model.closingFormulation);
      return false;
    };
    const reasonFor=(section,rendered)=>{
      if(!rendered) return 'detected source section was not rendered';
      if(sourceRenderLayer(section.type)==='technical') return 'preserved in the parser model and technical appendix/export manifest; public view uses a transformed digest';
      if(section.type==='submove') return 'rendered as owner-backed answer move with source-derived fields';
      if(section.type==='land') return 'rendered in the burden landing panel';
      if(section.type==='burden') return 'rendered as the burden/problem card header';
      return 'rendered as a source-preserving card or final prose card';
    };
    return (model.sourceSections||[]).map(section=>{
      const crop=cropFor(section);
      const rendered=isRendered(section);
      return {
        id:section.id,
        type:section.type,
        sourceSectionKind:section.type,
        heading:section.heading,
        burden:section.burden||null,
        lineStart:section.lineStart,
        lineEnd:section.lineEnd,
        renderLayer:sourceRenderLayer(section.type),
        publicTitle:publicTitleForSourceSection(section),
        technicalGloss:technicalGlossForSourceSection(section),
        sourcePreserved:true,
        defaultVisible:sourceRenderLayer(section.type)==='public',
        assignedRenderSection:section.assignedRenderSection,
        rendered,
        exportFile:crop?.name||null,
        reason:reasonFor(section,rendered)
      };
    });
  }
  function sectionExportManifest(sections,renderedFiles){
    const coverage=exportCoverageReport()||{};
    const model=currentModel||blankModel();
    const verdict=verdictDigest(model);
    return {
      title:'Restorative Noetic Map section export',
      case:storyCaseHeadline(model).title,
      verdict:verdict.headline,
      sourceOutputDigest:readerInputDigest(model),
      exportedAt:new Date().toISOString(),
      parserVerdict:{
        reconstructible:!(model.errors||[]).length,
        closureComplete:Boolean(model.closureComplete),
        burdenCount:(model.burdens||[]).length,
        errors:model.errors||[],
        warnings:[...(model.warnings||[]),...(model.witnessMismatches||[])]
      },
      fieldWitness:{
        embedded:Boolean(model.witnessSources?.embedded),
        separate:Boolean(model.witnessSources?.separate),
        mismatchCount:(model.witnessMismatches||[]).length
      },
      dimensions:coverage,
      sourceCoverage:sourceCoverageManifest(model,sections),
      sections:sections.map((section,index)=>({
        order:index+1,
        file:section.name,
        title:section.title,
        type:section.type,
        semanticBounds:section.semanticBounds?{
          x:Math.round(section.semanticBounds.x),
          y:Math.round(section.semanticBounds.y),
          width:Math.round(section.semanticBounds.width),
          height:Math.round(section.semanticBounds.height),
          top:Math.round(section.semanticBounds.top),
          bottom:Math.round(section.semanticBounds.bottom)
        }:null,
        sourceCrop:{
          x:Math.round(section.sourceCrop?.x??section.x),
          y:Math.round(section.sourceCrop?.y??section.y),
          width:Math.round(section.sourceCrop?.width??section.width),
          height:Math.round(section.sourceCrop?.height??section.height)
        },
        previousSectionBottom:Number.isFinite(section.previousSectionBottom)?Math.round(section.previousSectionBottom):null,
        nextSectionTop:Number.isFinite(section.nextSectionTop)?Math.round(section.nextSectionTop):null,
        foreignSectionOverlap:Boolean(section.foreignSectionOverlap),
        sourceCanvasSafe:Boolean(section.sourceCanvasSafe??section.canvasSafe),
        plannedPng:section.plannedPng||null,
        canvasSafe:Boolean(section.canvasSafe||(renderedFiles[index]?.dimensions&&canvasSafetyForDimensions(renderedFiles[index].dimensions.width,renderedFiles[index].dimensions.height))),
        png:renderedFiles[index]?.dimensions||null
      }))
    };
  }
  async function exportPngSections(){
    if(!document.getElementById('ogSvg')) return;
    const build=buildSectionExportSvg();
    const svg=build.svg;
    if(!svg){build.cleanup(); return;}
    await waitForExportLayout();
    const cfg=pngExportConfig();
    const sections=storySectionCrops(svg);
    const files=[], renderedFiles=[];
    for(const section of sections){
      const sectionSvg=cropSvgForExport(svg,section,56);
      const targetWidth=safePngTargetWidthForSection(sectionSvg,cfg.width);
      const png=await renderPngBlobFromSvgNode(sectionSvg,targetWidth);
      if(!png) continue;
      const naturalW=sectionSvg.viewBox.baseVal.width||sectionSvg.width.baseVal.value;
      const naturalH=sectionSvg.viewBox.baseVal.height||sectionSvg.height.baseVal.value;
      const scale=targetWidth/naturalW;
      renderedFiles.push({name:section.name,dimensions:{width:Math.round(naturalW*scale),height:Math.round(naturalH*scale)}});
      files.push({name:section.name,blob:png});
    }
    const manifest=sectionExportManifest(sections,renderedFiles);
    files.push({name:'manifest.json',blob:new Blob([JSON.stringify(manifest,null,2)],{type:'application/json;charset=utf-8'})});
    const zip=await createZipBlob(files);
    build.cleanup();
    downloadBlob('daee-output-grapher-sections.zip','application/zip',zip);
  }

  function init(){
    const parse=document.getElementById('ogParseBtn');
    if(!parse) return;
    parse.addEventListener('click',()=>render(parseOutput(
      document.getElementById('ogOutputInput')?.value||'',
      document.getElementById('ogWitnessInput')?.value||'',
      document.getElementById('ogCertificateInput')?.value||''
    )));
    document.getElementById('ogExportPngBtn')?.addEventListener('click',exportPng);
    document.getElementById('ogExportPngSectionsBtn')?.addEventListener('click',exportPngSections);
    document.getElementById('ogExportSvgBtn')?.addEventListener('click',exportSvg);
    document.getElementById('ogExportJsonBtn')?.addEventListener('click',exportJson);
    document.getElementById('ogExportMermaidBtn')?.addEventListener('click',exportMermaid);
  }
  window.daeeOutputGrapher={parseOutput,renderGraph,exportPng,exportPngSections,exportSvg,exportJson,exportCoverageReport,sectionExportPlan,sourceRenderLayer,parseCollapseCertificate};
  document.addEventListener('DOMContentLoaded',init);
})();
