<!DOCTYPE html>
{{ GENERATED_BANNER }}

<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width,initial-scale=1" name="viewport"/>
<title>DAEE Epistemics — Pipeline Control Wiki</title>
<style>
{{ DESIGN_TOKENS_CSS }}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 18% 0%,rgba(var(--ds-color-info-rgb),.13),transparent 30%),radial-gradient(circle at 82% 0%,rgba(var(--ds-color-success-rgb),.10),transparent 30%),var(--bg);color:var(--ink);font-family:var(--ds-font-body);line-height:var(--ds-type-body-line-height)}
button,input,select{font:inherit} code,pre{font-family:var(--ds-font-monospace)} code{background:var(--ds-color-surface-code);border:1px solid var(--ds-color-border);border-radius:var(--ds-radius-card);padding:1px 5px;color:#e2e8f0} p code,.small code,.subtle code{white-space:normal;overflow-wrap:anywhere} pre{background:#050914;border:1px solid var(--ds-color-border);border-radius:var(--ds-radius-panel);padding:14px;overflow:auto;color:#e5e7eb}
.siteHero{border-bottom:1px solid rgba(38,48,68,.72);background:linear-gradient(180deg,rgba(8,10,16,.96),rgba(8,10,16,.72));text-align:center}.siteHeroInner{max-width:1880px;margin:0 auto;padding:34px 22px 22px}.siteHero h1{font-size:clamp(34px,4vw,58px);letter-spacing:-.07em;line-height:.95;margin:10px 0 8px}.siteHero p{color:var(--muted);max-width:1000px;margin:0 auto}.topbar{position:sticky;top:0;z-index:100;background:rgba(8,10,16,.9);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)} .topbarInner{display:flex;align-items:center;justify-content:space-between;gap:12px;max-width:1880px;margin:0 auto;padding:8px 12px}.tabs{display:flex;gap:4px;min-width:0;overflow:auto}.tab{border:0;background:transparent;color:var(--muted);padding:12px 18px;border-bottom:3px solid transparent;cursor:pointer;font-weight:850;white-space:nowrap} .tab:hover{color:#fff;background:#121a2b} .tab.active{color:var(--green);border-bottom-color:var(--green)}.downloadNavAction{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;border:1px solid rgba(34,197,94,.42);background:linear-gradient(180deg,rgba(34,197,94,.16),rgba(34,197,94,.08));color:#dcfce7;border-radius:999px;padding:9px 14px;font-size:13px;font-weight:900;text-decoration:none;white-space:nowrap;box-shadow:0 8px 20px rgba(0,0,0,.14)}.downloadNavAction:hover{border-color:rgba(34,197,94,.75);background:rgba(34,197,94,.18);color:#fff}.downloadNavAction:focus-visible{outline:3px solid var(--ds-color-focus);outline-offset:3px}
main{max-width:1880px;margin:0 auto;padding:20px 22px 70px} .tabsec{display:none} .tabsec.active{display:block}
.hero{text-align:center;padding:18px 0 20px;border-bottom:1px solid rgba(38,48,68,.55);margin-bottom:18px} .hero h1{font-size:clamp(34px,4vw,58px);letter-spacing:-.07em;line-height:.95;margin:10px 0 8px} .hero p{color:var(--muted);max-width:1000px;margin:0 auto}
.panel{border:1px solid var(--line);background:rgba(15,19,32,.88);border-radius:22px;padding:18px;margin:14px 0;box-shadow:0 10px 30px rgba(0,0,0,.18)} h2{font-size:clamp(24px,2.4vw,38px);letter-spacing:-.055em;margin:20px 0 10px} h3{font-size:20px;letter-spacing:-.035em;margin:18px 0 8px} h4{margin:14px 0 8px;color:#f8fafc} p,li{color:#cbd5e1} .small,.subtle{font-size:13px;color:var(--muted)}
.badges,.chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:14px} .badge,.chip{display:inline-flex;gap:7px;align-items:center;border:1px solid var(--line);background:#0b1020;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:800;color:#dbeafe} .dot{width:8px;height:8px;border-radius:50%;background:var(--blue);display:inline-block}.dot.phase-input{background:var(--stage-d0)}.dot.phase-layer-a{background:var(--stage-psi-n)}.dot.phase-gate{background:var(--stage-dsl-ir)}.dot.phase-owner-delta{background:var(--stage-owner-ttp-delta)}.dot.phase-reread-closure{background:var(--green)}.dot.phase-public-boundary{background:var(--stage-collapse-restoration)} .dot.green{background:var(--green)}.dot.cyan{background:var(--cyan)}.dot.violet{background:var(--violet)}.dot.orange{background:var(--orange)}.dot.red{background:var(--red)}.dot.pink{background:var(--pink)}
.flowline{display:flex;gap:8px;align-items:center;flex-wrap:wrap;background:#080d19;border:1px dashed #334155;border-radius:16px;padding:12px;margin:12px 0} .node{border:1px solid #334155;background:#101827;border-radius:14px;padding:9px 12px;font-weight:900;color:#f8fafc;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace} .arrow{font-weight:900;color:#64748b}
.pipelineGrid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:12px 0} .stageCard{border:2px solid var(--c);border-radius:18px;background:#0c1220;padding:12px;cursor:pointer;min-height:172px;transition:.15s transform,.15s background,.15s box-shadow} .stageCard:hover{transform:translateY(-2px);background:#101827} .stageCard.active{box-shadow:0 0 0 3px color-mix(in srgb,var(--c),transparent 72%);background:#101827} .stageCard h3{font-size:15px;color:var(--c);margin:0 0 8px} .stageNum{width:28px;height:28px;border-radius:50%;background:var(--c);display:inline-grid;place-items:center;color:#fff;font-weight:900;margin-right:6px} .stageCard p{font-size:12px;margin:6px 0;color:#cbd5e1}
.detailGrid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px} .detailBox{border:1px solid #2b3854;background:#0a0f1d;border-radius:14px;padding:10px} .detailBox h4{font-size:12px;color:var(--cyan);text-transform:uppercase;letter-spacing:.06em;margin:0 0 6px} .detailBox ul{padding-left:18px;margin:0} .detailBox li{font-size:12px;margin:4px 0}
.compareGrid{display:grid;grid-template-columns:1fr 1fr;gap:14px} .grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px} .col3{grid-column:span 3} .col4{grid-column:span 4} .col6{grid-column:span 6} .col8{grid-column:span 8} .full{grid-column:1/-1} .card{border:1px solid var(--line);background:#0c1220;border-radius:18px;padding:14px} .card h3,.card h4{margin-top:0}
.regGrid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px} .regCard{border:2px solid var(--c);border-radius:18px;padding:14px;background:#0c1220} .regSym{width:52px;height:52px;border-radius:16px;background:var(--c);color:#fff;display:grid;place-items:center;font-size:28px;font-family:ui-serif,Georgia,serif;font-weight:900;margin-bottom:8px}
table{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:16px;overflow:hidden;margin:10px 0} th,td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;font-size:13px} th{background:#111827;color:#e5e7eb;text-transform:uppercase;letter-spacing:.05em;font-size:11px;text-align:left} tr:last-child td{border-bottom:0} td:first-child{font-weight:800;color:#f8fafc}
.tabsec,.panel,.card,.docviewer,.ownerFamilies,.entityLayout{min-width:0}
.tabsec table{display:block;max-width:100%;overflow-x:auto}
.subtabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0} .subtab{border:1px solid var(--line);background:#0b1020;border-radius:999px;padding:8px 12px;color:#cbd5e1;cursor:pointer;font-weight:800} .subtab.active{color:#bbf7d0;border-color:rgba(34,197,94,.55)} .subpanel{display:none} .subpanel.active{display:block}
.ownerCircuit{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:12px 0} .circuitNode{border:2px solid var(--c);background:#0c1220;border-radius:18px;padding:12px;text-align:center} .circuitNode strong{color:var(--c);display:block;margin-bottom:6px} .circuitNode p{font-size:12px;margin:0}
.ownerFamilies{display:grid;grid-template-columns:330px 1fr;gap:14px} .ownerList{display:grid;gap:8px} .ownerBtn,.conceptBtn{text-align:left;border:1px solid var(--line);background:#0c1220;border-radius:14px;padding:10px;color:#e8edf7;cursor:pointer} .ownerBtn.active,.conceptBtn.active{border-color:var(--green);background:rgba(34,197,94,.09)} .ownerDetail,.conceptDetail{border:1px solid var(--line);background:#0c1220;border-radius:18px;padding:16px}
.entityLayout{display:grid;grid-template-columns:360px 1fr;gap:14px} .conceptList{display:grid;gap:8px;max-height:720px;overflow:auto} .entityType{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em} .relchips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0} .relchips span{border:1px solid #334155;background:#0a0f1d;border-radius:999px;padding:5px 8px;font-size:12px;color:#dbeafe}
.filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0} .filters input,.filters select{background:#0a0f1d;color:#e5e7eb;border:1px solid #334155;border-radius:10px;padding:9px 10px}
.docviewer{display:grid;grid-template-columns:360px 1fr;gap:14px} .doclist{max-height:660px;overflow:auto;display:grid;gap:6px} .docitem{border:1px solid var(--line);background:#0c1220;border-radius:12px;padding:9px;cursor:pointer} .docitem:hover{border-color:var(--cyan)} .docbody{max-height:780px;overflow:auto}
.callout{border-left:4px solid var(--green);background:rgba(34,197,94,.07);border-radius:12px;padding:14px 16px;margin:14px 0} .warn{border-left-color:var(--orange);background:rgba(251,146,60,.08)} .danger{border-left-color:var(--red);background:rgba(248,113,113,.08)}
.procGrid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px} .procStep{border:1px solid #334155;background:#0a0f1d;border-radius:16px;padding:14px} .procStep h3{margin-top:0;color:#dbeafe} .command-block{background:#050914;border:1px solid #243047;border-radius:14px;padding:12px;overflow:auto;font-size:12px}
.auditOnly{border:1px dashed #334155;background:#080d19;border-radius:16px;padding:12px;margin-top:12px} details{margin:10px 0} summary{cursor:pointer;color:#bbf7d0;font-weight:900} details.panel>summary{display:flex;align-items:center;justify-content:space-between;gap:12px;list-style:none} details.panel>summary::-webkit-details-marker{display:none} details.panel>summary::after{content:"+";border:1px solid var(--line);border-radius:999px;width:26px;height:26px;display:grid;place-items:center;color:var(--cyan);flex:0 0 auto} details.panel[open]>summary::after{content:"-"} .proposalAnnex{font-size:14px} .proposalAnnex .shell{display:block;min-height:auto} .proposalAnnex nav{display:none} .proposalAnnex main{padding:0;max-width:none} .proposalAnnex section{border:1px solid var(--line);background:#0c1220;border-radius:18px;padding:16px;margin:12px 0} .proposalAnnex .hero{text-align:left;border:1px solid var(--line);background:#0c1220;border-radius:18px;padding:16px}
.surfaceRoleKicker{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:900;margin-bottom:6px}.surfaceSummaryGrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:10px 0}.surfaceStat{border:1px solid #263044;background:#080d19;border-radius:14px;padding:11px;min-width:0}.surfaceStat strong{display:block;color:#f8fafc;font-size:20px;line-height:1}.surfaceStat span{display:block;color:#93a4bb;font-size:12px;margin-top:4px}.surfaceStat code{white-space:normal;overflow-wrap:anywhere}.sourceBrowser{display:grid;grid-template-columns:360px minmax(0,1fr);gap:14px;align-items:start}.sourceBrowser .doclist{max-height:640px}.docitem{width:100%;text-align:left;color:#e8edf7}.docitem.active,.docitem[aria-selected="true"]{border-color:var(--green);background:rgba(34,197,94,.09)}.docbodyEmpty{border:1px dashed #334155;border-radius:14px;padding:18px;color:var(--muted)}[data-surface-role="focal"]{box-shadow:0 16px 42px rgba(0,0,0,.25)}[data-surface-role="support"],[data-surface-role="provenance"],[data-surface-role="raw-source"]{background:rgba(10,15,29,.82)}[data-surface-role="raw-source"] table,[data-surface-role="provenance"] table{font-size:12px}.ownerWorkspaceIntro{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:12px;margin:10px 0}.ownerSummaryNote{border:1px solid #263044;background:#080d19;border-radius:14px;padding:12px}.theoryFocalGrid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr);gap:14px;align-items:start}.theoryNotationContext{position:sticky;top:86px;max-height:calc(100vh - 120px);overflow:auto}.theoryCardGroups{display:grid;gap:12px;margin-top:14px}.theoryCardGroup{border:1px solid #263044;background:#080d19;border-radius:16px;padding:12px}.theoryCardGroup h3{margin-top:0}.theoryCardGroup .controlOverviewGrid{margin-top:8px}.architectureSupportDisclosure .callout{margin-top:12px}@media(max-width:1100px){.sourceBrowser,.ownerWorkspaceIntro,.theoryFocalGrid{grid-template-columns:1fr}.theoryNotationContext{position:static;max-height:none}.surfaceSummaryGrid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:620px){.surfaceSummaryGrid{grid-template-columns:1fr}}
.bridgeSemantics{border:1px solid var(--line);background:rgba(12,18,32,.92);border-radius:20px;padding:16px;margin:12px 0}.bridgeIntro{max-width:1180px}.bridgeKicker{margin:0 0 4px;color:var(--cyan);font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}.bridgeIntro h2{margin:0 0 8px;font-size:clamp(24px,2vw,34px);letter-spacing:-.04em}.bridgeIntro p{margin:0;color:#cbd5e1}.bridgeFlow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;border:1px dashed #334155;background:#080d19;border-radius:16px;padding:10px;margin:14px 0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-weight:850}.bridgeFlow span{border:1px solid #334155;background:#0c1220;border-radius:10px;padding:6px 8px;color:#e8edf7}.bridgeFlow b{color:#64748b}.bridgeGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.bridgeCard{border:1px solid #334155;background:#0a0f1d;border-radius:16px;padding:12px;min-width:0}.bridgeCard h3{font-size:15px;margin:0 0 8px;color:#dbeafe;letter-spacing:-.02em}.bridgeCard p{margin:7px 0;font-size:13px;line-height:1.48}.bridgeCard dl{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;margin:0}.bridgeCard dt{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#bbf7d0;font-weight:950}.bridgeCard dd{margin:0;color:#cbd5e1;font-size:13px;line-height:1.42}.bridgeNonClaims{border-color:rgba(248,113,113,.45);background:rgba(248,113,113,.055)}.bridgeNonClaims h3{color:#fecaca}.bridgeNonClaims ul{margin:0;padding-left:18px}.bridgeNonClaims li{font-size:13px;line-height:1.45;margin:4px 0}.bridgeExamples{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}.bridgeExamples>div{border:1px solid #334155;background:#080d19;border-radius:14px;padding:10px}.bridgeExamples strong{display:block;color:#bbf7d0;margin-bottom:6px}.bridgeExamples code{display:block;white-space:normal;line-height:1.45}@media(max-width:1100px){.bridgeGrid{grid-template-columns:1fr 1fr}.bridgeExamples{grid-template-columns:1fr}}@media(max-width:760px){.bridgeGrid{grid-template-columns:1fr}.bridgeFlow{display:grid;grid-template-columns:1fr}.bridgeFlow b{display:none}}
@media(max-width:1250px){.pipelineGrid{grid-template-columns:repeat(3,1fr)}.detailGrid{grid-template-columns:1fr 1fr}.compareGrid,.ownerFamilies,.entityLayout,.docviewer{grid-template-columns:1fr}.ownerCircuit{grid-template-columns:1fr 1fr}.regGrid{grid-template-columns:1fr 1fr}.procGrid{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.col3,.col4,.col6,.col8,.full{grid-column:1/-1}}
@media(max-width:760px){main{padding:12px}.pipelineGrid,.detailGrid,.ownerCircuit,.regGrid{grid-template-columns:1fr}.siteHeroInner{padding:26px 12px 18px}.topbarInner{align-items:stretch;flex-wrap:wrap}.tabs{flex:1 1 100%;order:1}.downloadNavAction{order:2;margin-left:auto;padding:8px 12px}.tab{padding:10px 12px}}


.notationBoard{border:1px solid #334155;background:#070b14;border-radius:18px;padding:14px;margin:12px 0;overflow:hidden;max-width:100%}
.notationLine{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin:6px 0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-weight:850;max-width:100%;overflow-wrap:anywhere}
.ntok{--ntok-c:#334155;display:inline-flex;align-items:center;border:1px solid var(--ntok-c);background:color-mix(in srgb,var(--ntok-c),#0c1220 86%);border-radius:10px;padding:5px 8px;color:#dbeafe;transition:.15s all;cursor:pointer;max-width:100%;white-space:normal;overflow-wrap:anywhere;text-align:left;line-height:1.35}
.ntok:hover{border-color:var(--ntok-c);transform:translateY(-1px)}
.ntok.active,
.ntok.is-linked-active,
.ntok[aria-pressed="true"]{border-color:var(--ntok-c);background:color-mix(in srgb,var(--ntok-c),#0c1220 72%);color:#fff;box-shadow:0 0 0 2px color-mix(in srgb,var(--ntok-c),transparent 76%);outline:2px solid rgba(250,204,21,.36);outline-offset:2px}
.ntok.muted{opacity:.34}
.ntok.phase-input,.ntokMini.phase-input{--ntok-c:var(--stage-d0)}
.ntok.phase-layer-a,.ntokMini.phase-layer-a{--ntok-c:var(--stage-psi-n)}
.ntok.phase-gate,.ntokMini.phase-gate{--ntok-c:var(--stage-dsl-ir)}
.ntok.phase-owner-delta,.ntokMini.phase-owner-delta{--ntok-c:var(--stage-owner-ttp-delta)}
.ntok.phase-reread-closure,.ntokMini.phase-reread-closure{--ntok-c:var(--green)}
.ntok.phase-public-boundary,.ntokMini.phase-public-boundary{--ntok-c:var(--stage-collapse-restoration)}
.notationArrow{color:#64748b;font-weight:900}
.notationExplain{border:1px dashed #334155;background:#0a0f1d;border-radius:12px;padding:12px;color:#cbd5e1;font-size:13px;margin-top:10px;overflow:hidden}
.notationContext{display:grid;gap:10px}
.notationContextHeader{display:grid;grid-template-columns:auto 1fr;align-items:center;gap:8px;font-weight:900;color:#f8fafc}
.notationContextHeader .ntokMini{--ntok-c:var(--yellow);border:1px solid var(--ntok-c);background:color-mix(in srgb,var(--ntok-c),#0c1220 82%);border-radius:999px;padding:4px 8px;color:#fff;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.notationContextGrid{display:grid;grid-template-columns:1fr;gap:7px}
.notationContextBlock{border:1px solid #263044;background:#080d19;border-radius:12px;padding:10px;min-width:0}
.notationContextBlock strong{display:block;color:#7dd3fc;text-transform:uppercase;letter-spacing:.06em;font-size:11px;margin-bottom:5px}
.notationContextBlock span{display:block;line-height:1.42}
.notationContextBlock code{white-space:normal;overflow-wrap:anywhere;color:#bbf7d0}
.notationRelated{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.notationRelated span{border:1px solid #334155;background:#0c1220;border-radius:999px;padding:4px 7px;color:#dbeafe;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.notationHighlightList{display:grid;gap:6px;margin-top:4px}
.notationHighlightRow{display:grid;grid-template-columns:minmax(110px,auto) 1fr;gap:8px;align-items:start;border:1px solid #263044;background:#0a0f1d;border-radius:10px;padding:7px}
.notationHighlightRow b{color:#f8fafc;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere}
.notationHighlightRow span{color:#cbd5e1}
.notationLegend{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
.notationLegend .miniCard{border:1px solid #334155;background:#0a0f1d;border-radius:14px;padding:10px;font-size:13px}
.relationLayout{display:grid;grid-template-columns:360px 1fr;gap:14px}.relationList{display:grid;gap:8px;max-height:680px;overflow:auto}.relationBtn{border:1px solid var(--line);background:#0c1220;border-radius:14px;padding:10px;text-align:left;color:#e8edf7;cursor:pointer}.relationBtn.active{border-color:var(--green);background:rgba(34,197,94,.09)}.relationDetail{border:1px solid var(--line);background:#0c1220;border-radius:18px;padding:16px}
.proposalAnnex .grid{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(330px,1fr))!important;gap:14px!important;align-items:stretch!important}
.proposalAnnex .card,.proposalAnnex .card.wide{grid-column:auto!important;min-width:0!important}
.proposalAnnex .card.full{grid-column:1/-1!important}
.proposalAnnex .compare{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(330px,1fr))!important;gap:14px!important}
.proposalAnnex .two{columns:2;column-gap:24px}
.proposalAnnex section{overflow:hidden!important}
.proposalAnnex pre{white-space:pre-wrap}
.proposalAnnex table{display:table;width:100%;table-layout:auto}
.proposalAnnex .shell{display:block!important;min-height:auto!important}
.proposalAnnex nav{display:none!important}
.proposalAnnex main{padding:0!important;max-width:none!important}
.proposalAnnex .hero{text-align:left!important;border:1px solid var(--line)!important;background:#0c1220!important;border-radius:18px!important;padding:16px!important}
.proposalAnnex h1{font-size:clamp(30px,3vw,48px)!important}
@media(max-width:900px){.notationLegend{grid-template-columns:1fr}.relationLayout{grid-template-columns:1fr}.proposalAnnex .two{columns:1}}


.opLayout{display:grid;grid-template-columns:380px 1fr;gap:14px}.opList{display:grid;gap:8px;max-height:720px;overflow:auto}.opBtn{border:1px solid var(--line);background:#0c1220;border-radius:14px;padding:10px;text-align:left;color:#e8edf7;cursor:pointer}.opBtn:hover{border-color:var(--cyan)}.opBtn.active{border-color:var(--green);background:rgba(34,197,94,.09)}.opDetail{border:1px solid var(--line);background:#0c1220;border-radius:18px;padding:16px}.opFamily{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em}.opGraph{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:12px 0}.opGraphNode{border:2px solid var(--c);background:#0c1220;border-radius:18px;padding:12px;text-align:center}.opGraphNode strong{display:block;color:var(--c);margin-bottom:6px}.opChip{border:1px solid #334155;background:#0a0f1d;color:#dbeafe;border-radius:999px;padding:5px 8px;font-size:12px;cursor:pointer;display:inline-flex;align-items:center;margin:2px}.opChip:hover{border-color:var(--green);background:rgba(34,197,94,.1);color:#fff}.opMiniGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0}.opMini{border:1px solid #334155;background:#0a0f1d;border-radius:14px;padding:10px}.opMini h4{font-size:12px;color:var(--cyan);text-transform:uppercase;letter-spacing:.06em;margin:0 0 6px}.opExplainBlock{border:1px solid #334155;background:#080d19;border-radius:14px;padding:12px;margin:8px 0}.opExplain{border-top:1px solid #263044;padding:8px 0}.opExplain:first-of-type{border-top:0}.opExplain p{margin:4px 0}@media(max-width:1100px){.opLayout{grid-template-columns:1fr}.opGraph{grid-template-columns:1fr}.opMiniGrid{grid-template-columns:1fr}}

.opExplainBlock{border:1px solid #334155;background:#080d19;border-radius:14px;padding:12px;margin:10px 0}
.opExplainBlock h3{margin-top:0}
.opExplainRow{display:grid;grid-template-columns:auto 18px 1fr;gap:8px;align-items:start;border-top:1px solid #263044;padding:9px 0}
.opExplainRow:first-of-type{border-top:0}
.opExplainRow .opText{color:#cbd5e1;font-size:13px;line-height:1.45}
.opExplainRow .opText strong{color:#f8fafc}
.opExplainRow .opText em{color:#bbf7d0;font-style:normal;font-weight:800}
.opDash{color:#64748b;font-weight:900}
.opChip{border:1px solid #334155;background:#0a0f1d;color:#dbeafe;border-radius:999px;padding:5px 8px;font-size:12px;cursor:pointer;display:inline-flex;align-items:center;margin:2px;font-weight:800}
.opChip:hover{border-color:var(--green);background:rgba(34,197,94,.1);color:#fff}


.opExplainBlock{border:1px solid #334155;background:#080d19;border-radius:14px;padding:12px;margin:10px 0}
.opExplainBlock h3{margin-top:0}
.opExplainRow{display:grid;grid-template-columns:auto 18px 1fr;gap:8px;align-items:start;border-top:1px solid #263044;padding:9px 0}
.opExplainRow:first-of-type{border-top:0}
.opExplainRow .opText{color:#cbd5e1;font-size:13px;line-height:1.45}
.opExplainRow .opText strong{color:#f8fafc}
.opExplainRow .opText em{color:#bbf7d0;font-style:normal;font-weight:800}
.opDash{color:#64748b;font-weight:900}
.sourceChip{border:1px solid #334155;background:#101827;color:#cbd5e1;border-radius:999px;padding:5px 8px;font-size:12px;cursor:pointer;display:inline-flex;align-items:center;margin:2px}
.sourceChip:hover{border-color:var(--cyan);background:rgba(34,211,238,.10);color:#fff}


.notationChip{border:1px solid #334155;background:#0a0f1d;color:#dbeafe;border-radius:999px;padding:6px 9px;font-size:12px;display:inline-flex;align-items:center;gap:6px;margin:3px}
.notationChip .nsym{font-family:ui-serif,Georgia,serif;font-size:15px;font-weight:900;color:#fff}
.notationChip .nlabel{color:#aebbd1}
.notationChip.activeMeaning{border-color:rgba(250,204,21,.55);background:rgba(250,204,21,.10)}
.notationExplainList{border:1px solid #334155;background:#080d19;border-radius:14px;padding:12px;margin:8px 0}
.notationExplainList h3{margin-top:0}


.readableFieldGrid{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0}
.readableFieldChip{border:1px solid #334155;background:#0a0f1d;color:#dbeafe;border-radius:14px;padding:7px 9px;font-size:12px;display:inline-flex;align-items:center;gap:7px}
.readableFieldChip .fieldSym{font-family:ui-serif,Georgia,serif;font-size:15px;font-weight:900;color:#fff}
.readableFieldChip .fieldMeaning{color:#aebbd1}
.readableFieldChip.clickable{cursor:pointer}
.readableFieldChip.clickable:hover{border-color:var(--cyan);background:rgba(34,211,238,.10)}
.notationChip{border:1px solid #334155;background:#0a0f1d;color:#dbeafe;border-radius:14px;padding:7px 9px;font-size:12px;display:inline-flex;align-items:center;gap:7px;margin:3px}
.notationChip .nsym{font-family:ui-serif,Georgia,serif;font-size:15px;font-weight:900;color:#fff}
.notationChip .nlabel{color:#aebbd1}
.notationChip.activeMeaning{border-color:rgba(250,204,21,.55);background:rgba(250,204,21,.10)}


/* v13 field navigation / left list scroll repair */
.conceptList{max-height:none!important;overflow:visible!important;padding-bottom:32px!important}
.entityLayout{align-items:start!important}
.readableFieldChip.clickable{cursor:pointer}
.readableFieldChip.clickable:hover{border-color:var(--green);background:rgba(34,197,94,.10);color:#fff}
.readableFieldChip .goHint{font-size:10px;color:#64748b;margin-left:2px}
.fieldNavNote{border:1px dashed #334155;background:#080d19;border-radius:12px;padding:9px 10px;color:#cbd5e1;font-size:12px;margin:8px 0}
@media(max-width:1250px){.conceptList{max-height:none!important;overflow:visible!important}}


/* v14: hide self-field chips and make field navigation visually explicit */
.fieldNavNote{border:1px dashed #334155;background:#080d19;border-radius:12px;padding:9px 10px;color:#cbd5e1;font-size:12px;margin:8px 0}
.readableFieldChip.clickable{cursor:pointer}
.readableFieldChip.clickable::after{content:'';font-size:10px;color:#64748b;margin-left:2px}
.readableFieldChip.clickable:hover{border-color:var(--green)!important;background:rgba(34,197,94,.10)!important;color:#fff}


/* v15 SOT field navigation + no-arrow notation chips */
.readableFieldGrid{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0}
.readableFieldChip,.notationChip{border:1px solid #334155;background:#0a0f1d;color:#dbeafe;border-radius:14px;padding:7px 9px;font-size:12px;display:inline-flex;align-items:center;gap:7px;margin:3px}
.readableFieldChip .fieldSym,.notationChip .nsym{font-family:ui-serif,Georgia,serif;font-size:15px;font-weight:900;color:#fff}
.readableFieldChip .fieldMeaning,.notationChip .nlabel{color:#aebbd1}
.readableFieldChip.clickable{cursor:pointer}
.readableFieldChip.clickable:hover{border-color:var(--green)!important;background:rgba(34,197,94,.10)!important;color:#fff}
.notationChip.activeMeaning{border-color:rgba(250,204,21,.55);background:rgba(250,204,21,.10)}
.fieldNavNote{border:1px dashed #334155;background:#080d19;border-radius:12px;padding:9px 10px;color:#cbd5e1;font-size:12px;margin:8px 0}
.conceptList{max-height:none!important;overflow:visible!important;padding-bottom:32px!important}
.entityLayout{align-items:start!important}
.opExplainBlock{border:1px solid #334155;background:#080d19;border-radius:14px;padding:12px;margin:10px 0}
.opExplainBlock h3{margin-top:0}
.opExplainRow{display:grid;grid-template-columns:auto 18px 1fr;gap:8px;align-items:start;border-top:1px solid #263044;padding:9px 0}
.opExplainRow:first-of-type{border-top:0}
.opExplainRow .opText{color:#cbd5e1;font-size:13px;line-height:1.45}
.opExplainRow .opText strong{color:#f8fafc}
.opExplainRow .opText em{color:#bbf7d0;font-style:normal;font-weight:800}
.opDash{color:#64748b;font-weight:900}
.sourceChip{border:1px solid #334155;background:#101827;color:#cbd5e1;border-radius:999px;padding:5px 8px;font-size:12px;cursor:pointer;display:inline-flex;align-items:center;margin:2px}
.sourceChip:hover{border-color:var(--cyan);background:rgba(34,211,238,.10);color:#fff}

/* v16: readable operator rows + owner list no internal cutoff */
.opList{max-height:none!important;overflow:visible!important;padding-bottom:24px!important}
.opLayout{align-items:start!important}
.opExplainRow{grid-template-columns:auto 18px minmax(0,1fr)!important}
.opExplainRow .opText{line-height:1.45}
.opExplainRow .opText .opTitle{color:#f8fafc;font-weight:900}
.opExplainRow .opText .opDesc{color:#cbd5e1}
.opExplainRow .hereLine{display:block;margin-top:5px;color:#cbd5e1}
.opExplainRow .hereLine em{color:#bbf7d0;font-style:normal;font-weight:900}


/* v17: restore bounded scrolling for the operator list without clipping the whole page */
#owners .opLayout{
  grid-template-columns:minmax(300px,420px) minmax(0,1fr)!important;
  align-items:start!important;
}
#owners #operatorGraphList.opList{
  max-height:clamp(520px,72vh,820px)!important;
  overflow-y:auto!important;
  overflow-x:hidden!important;
  padding-right:8px!important;
  padding-bottom:8px!important;
  scrollbar-gutter:stable!important;
  border-right:1px solid rgba(51,65,85,.35);
}
#owners #operatorGraphList.opList .opBtn{
  margin-right:4px;
}
#owners #operatorGraphDetail.opDetail{
  position:sticky;
  top:74px;
  max-height:calc(100vh - 96px);
  overflow-y:auto;
  scrollbar-gutter:stable;
}
#owners .opList::after{
  content:"Scroll for more operators";
  display:block;
  color:#64748b;
  font-size:12px;
  text-align:center;
  padding:10px 0 2px;
}
@media(max-width:1100px){
  #owners .opLayout{grid-template-columns:1fr!important}
  #owners #operatorGraphList.opList{
    max-height:56vh!important;
    border-right:0;
    border-bottom:1px solid rgba(51,65,85,.35);
  }
  #owners #operatorGraphDetail.opDetail{
    position:static;
    max-height:none;
    overflow:visible;
  }
}


/* v18: normalize left-column browser behavior across Owners, Concept Graph, and Relations Map */
#owners .opLayout,
#sub-concepts .entityLayout,
#sub-relations .relationLayout{
  display:grid!important;
  grid-template-columns:minmax(300px,420px) minmax(0,1fr)!important;
  gap:14px!important;
  align-items:start!important;
}
#owners #operatorGraphList.opList,
#sub-concepts #conceptList.conceptList,
#sub-relations .relationList{
  max-height:clamp(520px,72vh,820px)!important;
  overflow-y:auto!important;
  overflow-x:hidden!important;
  padding-right:8px!important;
  padding-bottom:8px!important;
  scrollbar-gutter:stable!important;
  border-right:1px solid rgba(51,65,85,.35)!important;
}
#owners #operatorGraphDetail.opDetail,
#sub-concepts #conceptDetail.conceptDetail,
#sub-relations #relationDetail.relationDetail{
  position:sticky!important;
  top:74px!important;
  max-height:calc(100vh - 96px)!important;
  overflow-y:auto!important;
  scrollbar-gutter:stable!important;
}
#sub-concepts #conceptList.conceptList::after,
#sub-relations .relationList::after{
  content:"Scroll for more nodes";
  display:block;
  color:#64748b;
  font-size:12px;
  text-align:center;
  padding:10px 0 2px;
}
@media(max-width:1100px){
  #owners .opLayout,
  #sub-concepts .entityLayout,
  #sub-relations .relationLayout{
    grid-template-columns:1fr!important;
  }
  #owners #operatorGraphList.opList,
  #sub-concepts #conceptList.conceptList,
  #sub-relations .relationList{
    max-height:56vh!important;
    border-right:0!important;
    border-bottom:1px solid rgba(51,65,85,.35)!important;
  }
  #owners #operatorGraphDetail.opDetail,
  #sub-concepts #conceptDetail.conceptDetail,
  #sub-relations #relationDetail.relationDetail{
    position:static!important;
    max-height:none!important;
    overflow:visible!important;
  }
}
.finalStateChip{border-color:rgba(250,204,21,.55)!important;background:rgba(250,204,21,.10)!important}


/* v62: compact Theory selectors keep the 25-card bank secondary to notation. */
.controlOverviewGrid{
  display:grid;
  grid-template-columns:repeat(5,minmax(150px,1fr));
  gap:8px;
  margin:10px 0 12px;
}
.controlCard{
  text-align:left;
  border:2px solid var(--c);
  background:#0c1220;
  color:var(--ink);
  border-radius:12px;
  padding:8px;
  cursor:pointer;
  min-height:84px;
  transition:.15s transform,.15s background,.15s box-shadow;
}
.controlCard:hover{
  transform:translateY(-1px);
  background:#101827;
  box-shadow:0 0 0 2px color-mix(in srgb,var(--c),transparent 74%);
}
.controlCard:focus-visible{
  outline:2px solid var(--ds-color-focus);
  outline-offset:2px;
}
.controlCard.is-linked-active,
.controlCard[aria-pressed="true"]{
  background:#111c2d;
  box-shadow:0 0 0 2px color-mix(in srgb,var(--c),transparent 58%), inset 0 0 0 1px rgba(255,255,255,.12);
  transform:translateY(-1px);
}
.controlCard.is-linked-active .controlSym,
.controlCard[aria-pressed="true"] .controlSym{
  box-shadow:0 0 0 1px rgba(255,255,255,.34);
}
.controlCard .controlSym{
  min-width:30px;
  height:30px;
  border-radius:9px;
  padding:0 7px;
  display:inline-grid;
  place-items:center;
  background:var(--c);
  color:white;
  font-family:ui-serif,Georgia,serif;
  font-size:16px;
  font-weight:950;
  margin-bottom:5px;
}
.controlCard strong{display:block;font-size:12px;color:#f8fafc;margin-bottom:4px;line-height:1.2}
.controlCard p{margin:0;color:#cbd5e1;font-size:10.5px;line-height:1.28}
.controlCard.phase-input{--c:var(--stage-d0)}
.controlCard.phase-layer-a{--c:var(--stage-psi-n)}
.controlCard.phase-gate{--c:var(--stage-dsl-ir)}
.controlCard.phase-owner-delta{--c:var(--stage-owner-ttp-delta)}
.controlCard.phase-reread-closure{--c:var(--green)}
.controlCard.phase-public-boundary{--c:var(--stage-collapse-restoration)}
.controlCard.final-card .controlSym{font-size:11px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.controlCard.phase-reread-closure .controlSym{font-size:15px}
.controlCard.route-gradient-card .controlSym,
.controlCard.field-diagnostic-card .controlSym,
.controlCard.loopbreak-card .controlSym,
.controlCard.burden-card .controlSym,
.controlCard.delta-card .controlSym,
.controlCard.public-boundary-card .controlSym,
.controlCard.final-card .controlSym{
  max-width:100%;
  height:auto;
  min-height:30px;
  line-height:1.08;
  text-align:center;
  white-space:normal;
  overflow-wrap:anywhere;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:11px;
}
@media(min-width:1500px){.controlOverviewGrid{grid-template-columns:repeat(5,minmax(150px,1fr))}}
@media(max-width:1499px){.controlOverviewGrid{grid-template-columns:repeat(5,minmax(145px,1fr))}}
@media(max-width:900px){.controlOverviewGrid{grid-template-columns:repeat(3,minmax(140px,1fr))}}
@media(max-width:620px){.controlOverviewGrid{grid-template-columns:1fr}}

/* v20: deep pipeline stage cards restoring index9 architecture content */
.pipelineDeepIntro{
  border:1px dashed #334155;
  background:#080d19;
  border-radius:14px;
  padding:12px;
  margin:10px 0 14px;
  color:#cbd5e1;
  font-size:13px;
}
.deepStageGrid{
  display:grid;
  grid-template-columns:repeat(12,1fr);
  gap:12px;
  margin-top:12px;
}
/* v28: .deepCard base moved to v28 CSS block (SOT); keeping positional span modifiers here */
.deepCard.wide{grid-column:span 2}
.deepCard.full{grid-column:1/-1}
.deepCard.wide{grid-column:span 6}
.deepCard.full{grid-column:1/-1}
.deepCard h4{
  margin:0 0 8px;
  color:var(--accent,var(--cyan));
  font-size:13px;
  letter-spacing:.02em;
  text-transform:uppercase;
}
.deepCard p{margin:6px 0;color:#cbd5e1;font-size:13px}
.deepList{display:grid;gap:7px;margin:0;padding:0;list-style:none}
.deepList li{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:8px;
  align-items:start;
  border:1px solid #263044;
  background:#080d19;
  border-radius:11px;
  padding:8px;
  color:#cbd5e1;
  font-size:13px;
}
.deepKey{
  min-width:28px;
  height:24px;
  border:1px solid var(--accent,var(--cyan));
  color:var(--accent,var(--cyan));
  border-radius:8px;
  display:inline-grid;
  place-items:center;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-weight:900;
  font-size:12px;
}
.deepFormula{
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  color:#bbf7d0;
  font-weight:900;
  letter-spacing:-.02em;
  line-height:1.65;
  background:#050914;
  border:1px solid #263044;
  border-radius:12px;
  padding:10px;
  overflow:auto;
}
.deepFlow{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  align-items:center;
}
.deepPill{
  border:1px solid var(--accent,var(--cyan));
  color:#dbeafe;
  background:#080d19;
  border-radius:12px;
  padding:8px 10px;
  font-size:12px;
  font-weight:800;
}
.deepArrow{color:#64748b;font-weight:900}
.decisionMini{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:8px;
}
.decisionMini div{
  border:1px solid currentColor;
  border-radius:12px;
  padding:8px;
  text-align:center;
  font-weight:900;
  background:#080d19;
  font-size:12px;
}
.deepWarn{border-color:rgba(248,113,113,.55);background:rgba(248,113,113,.07)}
.deepGood{border-color:rgba(34,197,94,.55);background:rgba(34,197,94,.07)}
.deepTarget{border-color:rgba(250,204,21,.55);background:rgba(250,204,21,.06)}
@media(max-width:1250px){
  .deepCard,.deepCard.wide{grid-column:1/-1}
  .decisionMini{grid-template-columns:1fr 1fr}
}


/* v21: direct index9-style pipeline diagramming */
.v21-pipeline-panel{overflow:hidden}
.v21-formula{
  text-align:center;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  color:var(--green);
  font-size:clamp(15px,1.6vw,24px);
  font-weight:950;
  letter-spacing:-.03em;
  margin:12px 0 18px;
  padding:10px;
  border:1px solid #263044;
  border-radius:14px;
  background:#070b14;
  overflow:auto;
}
.v21-four-col,.v21-five-col{
  display:grid;
  gap:12px;
  align-items:start;
}
.v21-four-col{grid-template-columns:repeat(4,minmax(260px,1fr))}
.v21-five-col{grid-template-columns:repeat(5,minmax(240px,1fr))}
.v21-stage{
  border:2px solid var(--sc);
  border-radius:20px;
  padding:12px;
  background:rgba(13,17,23,.72);
  min-height:620px;
}
.v21-stage h2{
  margin:0 0 10px;
  color:var(--sc);
  display:flex;
  gap:10px;
  align-items:center;
  font-size:18px;
  letter-spacing:-.03em;
}
.v21-stage h2 span{
  width:28px;
  height:28px;
  border-radius:50%;
  background:var(--sc);
  color:#fff;
  display:grid;
  place-items:center;
  font-weight:900;
  font-size:14px;
}
.v21-s1{--sc:var(--stage-d0)}
.v21-s2{--sc:var(--stage-psi-n)}
.v21-s3{--sc:var(--stage-dsl-ir)}
.v21-s4{--sc:var(--stage-owner-ttp-delta)}
.v21-s5{--sc:var(--stage-collapse-restoration)}
.v21-card{
  background:#0d1117;
  border:1.5px solid #263044;
  border-radius:16px;
  padding:10px;
  margin-bottom:8px;
}
.v21-card h3{
  margin:0 0 7px;
  color:var(--sc);
  font-size:14px;
  font-weight:800;
  letter-spacing:-.02em;
}
.v21-card p{
  margin:0;
  color:#98a2b3;
  font-size:12.5px;
  line-height:1.4;
}
.v21-card ul{
  list-style:none;
  padding:0;
  margin:0;
  display:grid;
  gap:5px;
}
.v21-card li{
  display:flex;
  gap:8px;
  align-items:baseline;
  background:#0b101b;
  border:1px solid #263044;
  border-radius:8px;
  padding:6px 8px;
  font-size:12px;
  line-height:1.35;
  color:#cbd5e1;
}
.v21-card li b{
  min-width:22px;
  color:var(--sc);
  font-weight:900;
}
.v21-warn{border-color:var(--red);background:rgba(239,68,68,.06)}
.v21-warn h3{color:var(--red)}
.v21-purple{--sc:var(--violet);background:rgba(168,85,247,.06)}
.v21-note{
  border:1.5px dashed var(--sc);
  background:rgba(34,197,94,.035);
  border-radius:10px;
  padding:8px 10px;
  font-size:11.5px;
  color:#98a2b3;
  line-height:1.4;
  margin-top:6px;
}
.v21-note b{color:var(--sc)}
.v21-proc-flow{
  display:grid;
  grid-template-columns:repeat(11,auto);
  gap:4px;
  align-items:center;
  text-align:center;
  font-size:11px;
  font-weight:800;
}
.v21-proc-flow.target{grid-template-columns:repeat(15,auto)}
.v21-proc-flow div{
  padding:6px;
  border:1.5px solid rgba(34,197,94,.25);
  border-radius:8px;
  color:var(--green);
  background:rgba(34,197,94,.04);
}
.v21-proc-flow span{color:var(--green);font-weight:900}
.v21-field-grid{
  display:grid;
  grid-template-columns:1fr;
  gap:5px;
}
.v21-field-grid div{
  display:grid;
  grid-template-columns:36px 1fr;
  gap:7px;
  align-items:center;
  border:1px solid rgba(34,197,94,.22);
  background:rgba(34,197,94,.035);
  border-radius:8px;
  padding:6px;
}
.v21-field-grid b{
  width:30px;
  height:30px;
  border-radius:8px;
  border:1.5px solid var(--green);
  color:var(--green);
  display:grid;
  place-items:center;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-weight:900;
}
.v21-field-grid span{font-size:12px;color:#e5e7eb;font-weight:800}
.v21-field-grid small{display:block;font-size:10.5px;color:#98a2b3;line-height:1.25}
.v21-flow-boxes{
  display:grid;
  grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;
  gap:5px;
  margin-top:8px;
}
.v21-flow-boxes div{
  background:#0d1117;
  border:1.5px solid #263044;
  border-radius:12px;
  padding:8px;
  min-height:78px;
}
.v21-flow-boxes h4{margin:0 0 3px;color:var(--green);font-size:11px;font-weight:800}
.v21-flow-boxes p{margin:0;color:#98a2b3;font-size:10.5px;line-height:1.3}
.v21-flow-boxes span{display:grid;place-items:center;color:var(--green);font-weight:900}
.v21-stage-formula{
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  color:var(--green);
  font-weight:900;
  font-size:14px;
  text-align:center;
  padding:8px;
  border-radius:10px;
  background:#070b14;
  border:1px solid #263044;
  margin:8px 0;
  overflow:auto;
}
.v21-dec-grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:5px;
}
.v21-dec-grid div{
  padding:8px 4px;
  border-radius:10px;
  text-align:center;
  font-weight:900;
  font-size:11px;
  border:1.5px solid currentColor;
  background:#0b101b;
}
.v21-dec-grid .stop{color:var(--red)}
.v21-dec-grid .hold{color:var(--orange)}
.v21-dec-grid .recurse{color:var(--green)}
.v21-dec-grid .partial{color:var(--violet)}
.v21-three-col{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:12px;
  margin-top:14px;
}
@media(max-width:1600px){
  .v21-five-col{grid-template-columns:repeat(3,minmax(240px,1fr))}
}
@media(max-width:1250px){
  .v21-four-col,.v21-five-col,.v21-three-col{grid-template-columns:1fr 1fr}
  .v21-stage{min-height:auto}
}
@media(max-width:760px){
  .v21-four-col,.v21-five-col,.v21-three-col{grid-template-columns:1fr}
  .v21-proc-flow,.v21-proc-flow.target{display:flex;flex-wrap:wrap}
  .v21-flow-boxes{grid-template-columns:1fr}
  .v21-flow-boxes span{transform:rotate(90deg)}
}

/* v22: restore landing page material removed in v21 */
.v22-landing-deck{
  border-color:rgba(34,197,94,.32);
  background:linear-gradient(135deg,rgba(34,197,94,.055),rgba(96,165,250,.04));
}
.v22-deck-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(220px,1fr));
  gap:12px;
  margin-top:12px;
}
.v22-deck-card{
  border:1.5px solid var(--c);
  background:#0c1220;
  border-radius:18px;
  padding:14px;
}
.v22-deck-card h3{
  margin:0 0 8px;
  color:var(--c);
  font-size:16px;
}
.v22-deck-card ul{
  margin:0;
  padding-left:18px;
  color:#cbd5e1;
}
.v22-deck-card li{
  margin:6px 0;
  font-size:13px;
}
.v22-deck-card.current{--c:var(--green)}
.v22-deck-card.target{--c:var(--cyan)}
.v22-deck-card.preserve{--c:var(--violet)}
.v22-deck-card.patch{--c:var(--orange)}
.v22-audit-panel,
.v22-implementation-procedure{
  margin-top:18px;
}
.v22-proc-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(260px,1fr));
  gap:12px;
  margin-top:12px;
}
.v22-proc-step{
  border:1px solid #334155;
  background:#0a0f1d;
  border-radius:16px;
  padding:14px;
}
.v22-proc-step h3{
  margin:0 0 8px;
  color:#dbeafe;
}
.v22-proc-step ul{
  margin:0;
  padding-left:18px;
}
.v22-proc-step li{
  margin:6px 0;
  color:#cbd5e1;
  font-size:13px;
}
@media(max-width:1250px){
  .v22-deck-grid{grid-template-columns:repeat(2,minmax(220px,1fr))}
  .v22-proc-grid{grid-template-columns:1fr}
}
@media(max-width:760px){
  .v22-deck-grid{grid-template-columns:1fr}
}

/* v23: restore v19 stage inspector and stabilize architecture formatting */
.v23-inspector{
  border-color:rgba(96,165,250,.35);
  background:linear-gradient(135deg,rgba(96,165,250,.055),rgba(34,197,94,.035));
}
.v23-inspector-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
  margin-top:12px;
  align-items:start;
}
.v23-inspector-side{
  border:1px solid #334155;
  background:#0a0f1d;
  border-radius:18px;
  padding:14px;
  min-width:0;
}
.v23-inspector-side h3{
  margin:0 0 10px;
  color:#dbeafe;
}
.v23-inspector-side .pipelineGrid{
  grid-template-columns:repeat(2,minmax(180px,1fr));
}
.v23-inspector-side .stageCard{
  min-height:132px;
}
.v23-inspector-side .stageCard h3{
  color:var(--c);
  font-size:13px;
}
.v23-stage-detail{
  margin-top:12px!important;
  max-height:520px;
  overflow:auto;
  scrollbar-gutter:stable;
}
.v23-stage-detail .detailGrid{
  grid-template-columns:repeat(2,minmax(220px,1fr));
}
.v23-stage-detail .detailBox:last-child{
  grid-column:1/-1;
}
.v22-landing-deck,
.v21-pipeline-panel,
.v22-audit-panel,
.v22-implementation-procedure{
  max-width:100%;
}
.v22-deck-card ul,
.v22-proc-step ul{
  list-style:disc;
}
@media(max-width:1250px){
  .v23-inspector-grid{grid-template-columns:1fr}
  .v23-inspector-side .pipelineGrid{grid-template-columns:repeat(3,minmax(180px,1fr))}
}
@media(max-width:760px){
  .v23-inspector-side .pipelineGrid{grid-template-columns:1fr}
  .v23-stage-detail .detailGrid{grid-template-columns:1fr}
}

/* v24: remove inspector artifacts and restore index9-like pipeline proportions */
.v23-inspector{display:none!important}
.v21-four-col{
  grid-template-columns:minmax(250px,1fr) minmax(310px,1.25fr) minmax(460px,1.65fr) minmax(310px,1.15fr)!important;
}
.v21-field-grid{
  gap:7px!important;
}
.v21-field-grid div{
  grid-template-columns:42px minmax(0,1fr)!important;
  align-items:start!important;
  padding:8px!important;
}
.v21-field-grid span{
  display:block!important;
  white-space:normal!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  line-height:1.25!important;
}
.v21-field-grid small{
  display:block!important;
  white-space:normal!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  line-height:1.25!important;
}
.v22-deck-grid{
  grid-template-columns:repeat(3,minmax(260px,1fr))!important;
}
@media(max-width:1500px){
  .v21-four-col{grid-template-columns:1fr 1.2fr!important}
}
@media(max-width:900px){
  .v21-four-col{grid-template-columns:1fr!important}
  .v22-deck-grid{grid-template-columns:1fr!important}
}

/* v25: final formatting repair for DSL/IR field cards and 9-step procedure */
.v21-field-grid > div{
  display:grid!important;
  grid-template-columns:44px minmax(0,1fr)!important;
  gap:9px!important;
  align-items:start!important;
  padding:9px!important;
  min-height:auto!important;
}
.v21-field-grid > div > div{
  display:block!important;
  border:0!important;
  background:transparent!important;
  padding:0!important;
  margin:0!important;
  min-height:0!important;
}
.v21-field-grid > div > div span,
.v21-field-grid > div > div small{
  display:block!important;
  white-space:normal!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  line-height:1.35!important;
}
.v21-field-grid > div > div span{
  font-size:12.5px!important;
}
.v21-field-grid > div > div small{
  font-size:11px!important;
}
.v21-five-col{
  grid-template-columns:repeat(auto-fit,minmax(320px,1fr))!important;
}
.v21-five-col .v21-stage{
  min-height:auto!important;
}
.v21-proc-flow.target{
  display:flex!important;
  flex-wrap:wrap!important;
}
.v25-deck-grid{
  grid-template-columns:repeat(4,minmax(240px,1fr))!important;
}
.v25-proc-grid{
  grid-template-columns:repeat(3,minmax(280px,1fr))!important;
}
@media(max-width:1250px){
  .v25-deck-grid{grid-template-columns:repeat(2,minmax(240px,1fr))!important}
  .v25-proc-grid{grid-template-columns:1fr!important}
}
@media(max-width:760px){
  .v25-deck-grid{grid-template-columns:1fr!important}
}

/* v26: fix actual field-card grid placement; keep text in column 2, not under the key */
#architecture .v21-field-grid > div{
  display:grid!important;
  grid-template-columns:44px minmax(0,1fr)!important;
  grid-template-rows:auto auto!important;
  column-gap:10px!important;
  row-gap:2px!important;
  align-items:start!important;
  padding:9px!important;
  min-height:auto!important;
}
#architecture .v21-field-grid > div > b{
  grid-column:1!important;
  grid-row:1 / span 2!important;
  align-self:start!important;
  justify-self:start!important;
  width:30px!important;
  height:30px!important;
  margin:0!important;
}
#architecture .v21-field-grid > div > span{
  grid-column:2!important;
  grid-row:1!important;
  display:block!important;
  white-space:normal!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  line-height:1.25!important;
  min-width:0!important;
}
#architecture .v21-field-grid > div > small{
  grid-column:2!important;
  grid-row:2!important;
  display:block!important;
  white-space:normal!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  line-height:1.25!important;
  min-width:0!important;
}
#architecture .v21-stage-formula{
  white-space:normal!important;
  overflow-wrap:anywhere!important;
  line-height:1.45!important;
}
#architecture .v21-five-col{
  grid-template-columns:repeat(auto-fit,minmax(360px,1fr))!important;
}
#architecture .v26-proc-grid{
  grid-template-columns:repeat(2,minmax(320px,1fr))!important;
}
@media(max-width:1100px){
  #architecture .v26-proc-grid{grid-template-columns:1fr!important}
}

/* v28: restored interactive pipeline panels */
.v28-pipeline-interactive{margin-bottom:14px}
.v28-detail-panel{margin-top:10px;min-height:0;padding:14px}
.v28-detail-panel:empty{display:none}
.pipelineDeepIntro{color:var(--muted);font-size:13px;margin:6px 0 10px;border-left:3px solid var(--cyan);padding-left:10px}
.deepStageGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;margin-top:10px}
.deepCard{border:1.5px solid var(--accent,var(--line));background:#070b14;border-radius:14px;padding:12px;transition:.15s border-color}
.deepCard:hover{border-color:var(--accent,var(--cyan))}
.deepCard.wide{grid-column:span 2}
.deepCard.full{grid-column:1/-1}
.deepCard h4{font-size:13px;color:var(--accent,var(--cyan));margin:0 0 6px;text-transform:uppercase;letter-spacing:.04em}
.deepCard p{font-size:12px;color:var(--muted);margin:4px 0}
.deepFormula{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;color:var(--ink);background:#0c1220;border:1px solid var(--line);border-radius:8px;padding:6px 10px;margin:4px 0}
.deepList{list-style:none;margin:4px 0;padding:0;display:grid;gap:4px}
.deepList li{display:flex;gap:8px;font-size:12px;align-items:baseline}
.deepKey{font-family:ui-monospace,SFMono-Regular,monospace;color:var(--accent,var(--cyan));background:#0c1220;border:1px solid var(--line);border-radius:5px;padding:1px 6px;flex-shrink:0;font-size:11px}
.deepFlow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0}
.deepPill{background:#0c1220;border:1px solid var(--line);border-radius:8px;padding:3px 9px;font-size:12px;color:var(--ink)}
.deepArrow{color:#64748b;font-weight:900}
.deepGood{border-color:rgba(34,197,94,.45)!important}
.deepWarn{border-color:rgba(239,68,68,.4)!important}
.deepTarget{border-color:rgba(167,139,250,.45)!important}
.decisionMini{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;text-align:center;font-size:13px;font-weight:700;margin:6px 0}
.decisionMini div{background:#0c1220;border:1px solid var(--line);border-radius:10px;padding:8px 4px}
@media(max-width:760px){.deepCard.wide,.deepCard.full{grid-column:1/-1}.decisionMini{grid-template-columns:1fr 1fr}}


/* v29: combine interactive inspectors into their static baseline panels */
.v29-integrated-inspector{
  border:1px solid #334155;
  background:linear-gradient(135deg,rgba(96,165,250,.055),rgba(34,197,94,.035));
  border-radius:18px;
  padding:14px;
  margin:14px 0 16px;
}
.v29-inspector-head{
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:12px;
  flex-wrap:wrap;
  margin-bottom:8px;
}
.v29-inspector-head h3{
  margin:0;
  color:#dbeafe;
  font-size:18px;
}
.v29-inspector-head p{
  margin:0;
  color:var(--muted);
  font-size:13px;
  max-width:920px;
}
.v29-flowline{
  margin:8px 0 12px!important;
}
.v29-pipeline-grid{
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr))!important;
}
.v29-pipeline-grid .stageCard{
  min-height:140px!important;
}
.v29-detail-panel{
  margin-top:12px!important;
}
.v29-detail-panel:empty{
  display:none!important;
}
.v29-detail-panel .detailGrid{
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr))!important;
}
/* force schema-light register bridge visual reference to be a single row of five on desktop */
@media(min-width:1180px){
  #architecture .v29-target-panel > .v21-five-col{
    display:grid!important;
    grid-template-columns:repeat(5,minmax(0,1fr))!important;
    gap:12px!important;
    align-items:start!important;
  }
  #architecture .v29-target-panel > .v21-five-col > .v21-stage{
    min-width:0!important;
    min-height:620px!important;
  }
  #architecture .v29-target-panel .v21-stage h2{
    font-size:16px!important;
  }
  #architecture .v29-target-panel .v21-card li{
    font-size:11.5px!important;
  }
  #architecture .v29-target-panel .v21-stage-formula{
    font-size:12px!important;
    white-space:normal!important;
    overflow-wrap:anywhere!important;
  }
  #architecture .v29-target-panel .v21-proc-flow.target{
    display:flex!important;
    flex-wrap:wrap!important;
  }
}
@media(max-width:1179px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:repeat(2,minmax(260px,1fr))!important;
  }
}
@media(max-width:760px){
  .v29-inspector-head{display:block}
  .v29-pipeline-grid{grid-template-columns:1fr!important}
  #architecture .v29-target-panel > .v21-five-col{grid-template-columns:1fr!important}
}

/* v30: DRY pipeline interactivity ported onto the graphics themselves */
#architecture .v29-integrated-inspector,
#architecture #currentPipeline,
#architecture #currentDetail,
#architecture #targetPipeline,
#architecture #targetDetail{
  display:none!important;
}
.v30-click-hint{
  border:1px dashed #334155;
  background:#080d19;
  border-radius:12px;
  padding:9px 11px;
  margin:10px 0 14px;
  color:#cbd5e1;
  font-size:13px;
}
.v30-selectable-stage{
  cursor:pointer;
  position:relative;
  transition:transform .15s ease, box-shadow .15s ease, background .15s ease;
}
.v30-selectable-stage::after{
  content:none;
  position:absolute;
  top:10px;
  right:10px;
  color:#94a3b8;
  font-size:10px;
  text-transform:uppercase;
  letter-spacing:.06em;
  opacity:.55;
}
.v30-selectable-stage:hover{
  transform:translateY(-2px);
  box-shadow:0 0 0 3px color-mix(in srgb,var(--sc),transparent 78%);
}
.v30-selectable-stage.v30-active{
  box-shadow:0 0 0 3px color-mix(in srgb,var(--sc),transparent 62%),0 12px 26px rgba(0,0,0,.18);
  background:color-mix(in srgb,rgba(13,17,23,.72),var(--sc) 7%);
}
.v60-selectable-subcard{
  cursor:pointer;
  position:relative;
  transition:border-color .15s ease, background .15s ease, box-shadow .15s ease, transform .15s ease;
}
.v60-selectable-subcard:hover,
.v60-selectable-subcard:focus-visible{
  border-color:color-mix(in srgb,var(--sc),#fff 18%)!important;
  background:color-mix(in srgb,#0d1117,var(--sc) 10%)!important;
  box-shadow:0 0 0 2px color-mix(in srgb,var(--sc),transparent 78%);
  outline:none;
}
.v60-selectable-subcard.v60-subactive{
  border-color:color-mix(in srgb,var(--sc),#fff 28%)!important;
  box-shadow:0 0 0 2px color-mix(in srgb,var(--sc),transparent 60%);
  background:color-mix(in srgb,#0d1117,var(--sc) 13%)!important;
}
.v60-selectable-subcard::after{
  content:none;
  display:none;
}
.v30-stage-detail{
  margin-top:14px!important;
  border-color:#334155!important;
  background:linear-gradient(135deg,rgba(96,165,250,.055),rgba(34,197,94,.035))!important;
}
.v30-stage-detail:empty{
  display:none!important;
}
.v30-stage-detail h3{
  margin:0 0 8px;
  color:#f8fafc;
}
.v30-detail-subtitle{
  margin:0 0 12px!important;
  color:#98a2b3!important;
  font-size:13px!important;
}
.v30-audit-grid{
  display:grid;
  grid-template-columns:repeat(5,minmax(160px,1fr));
  gap:10px;
}
.v30-audit-box{
  border:1px solid #334155;
  background:#0a0f1d;
  border-radius:14px;
  padding:10px;
  min-width:0;
}
.v30-audit-box h4{
  margin:0 0 6px;
  color:var(--cyan);
  text-transform:uppercase;
  letter-spacing:.06em;
  font-size:11px;
}
.v30-audit-box ul{
  margin:0;
  padding-left:17px;
}
.v30-audit-box li{
  font-size:12px;
  margin:4px 0;
  color:#cbd5e1;
}
.v30-stage-chiprow{
  display:flex;
  flex-wrap:wrap;
  gap:6px;
  margin:8px 0 12px;
}
.v30-stage-chip{
  border:1px solid #334155;
  background:#0b1020;
  border-radius:999px;
  padding:5px 8px;
  font-size:12px;
  color:#dbeafe;
}
/* schema-light register bridge should be one row of five on desktop. */
@media(min-width:1280px){
  #architecture .v29-target-panel > .v21-five-col{
    display:grid!important;
    grid-template-columns:repeat(5,minmax(0,1fr))!important;
    gap:12px!important;
    align-items:start!important;
  }
  #architecture .v29-target-panel > .v21-five-col > .v21-stage{
    min-width:0!important;
    min-height:620px!important;
  }
  #architecture .v29-target-panel .v21-stage h2{
    font-size:16px!important;
  }
  #architecture .v29-target-panel .v21-card li{
    font-size:11.5px!important;
  }
  #architecture .v29-target-panel .v21-stage-formula{
    font-size:12px!important;
    white-space:normal!important;
    overflow-wrap:anywhere!important;
  }
}
@media(max-width:1279px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:repeat(2,minmax(260px,1fr))!important;
  }
}
@media(max-width:900px){
  .v30-audit-grid{grid-template-columns:1fr}
  #architecture .v29-target-panel > .v21-five-col{grid-template-columns:1fr!important}
}

/* v31: DRY click behavior + formatting repair */
.v30-selectable-stage::after{
  content:none!important;
  display:none!important;
}
.v30-selectable-stage{
  cursor:pointer;
}
.v21-card li{
  align-items:flex-start!important;
}
.v21-card li b{
  flex:0 0 auto!important;
  min-width:22px;
  white-space:nowrap!important;
}
.v21-s1 .v21-card li b{
  min-width:8ch!important;
}
.v21-card li{
  word-break:normal!important;
  overflow-wrap:normal!important;
}
.v30-stage-chiprow{
  display:none!important;
}
.v31-stage-kicker{
  display:inline-flex;
  border:1px solid #334155;
  background:#0b1020;
  border-radius:999px;
  padding:5px 9px;
  color:#dbeafe;
  font-size:12px;
  font-weight:850;
  margin-bottom:8px;
}
.v30-detail-subtitle strong{
  color:#e8edf7;
}

/* v32: remove redundant drawer kicker and normalize final release-stage colour */
.v31-stage-kicker{
  display:none!important;
}
.v30-selectable-stage::after{
  content:none!important;
  display:none!important;
}
/* Align schema-light register bridge final Reread/Release stage with retained-spine Burden Cycle/Release shell color. */
#architecture .v29-target-panel .v21-s5{
  --sc:var(--violet)!important;
}
#architecture .v29-target-panel .v21-s5 > h2 span{
  background:var(--violet)!important;
}
#architecture .v29-target-panel .v21-s5 > h2{
  color:var(--violet)!important;
}

/* v34: combine bridge stages 4+5 and harden the preserved ♥ register in schema-light register bridge */
@media(min-width:1280px){
  #architecture .v29-target-panel > .v21-five-col{
    display:grid!important;
    grid-template-columns:repeat(4,minmax(0,1fr))!important;
    gap:12px!important;
    align-items:start!important;
  }
  #architecture .v29-target-panel > .v21-five-col > .v21-stage{
    min-height:620px!important;
  }
}
#architecture .v29-target-panel [data-stage-key="ownerRelease"]{
  --sc:var(--violet)!important;
}
#architecture .v29-target-panel [data-stage-key="ownerRelease"] > h2,
#architecture .v29-target-panel [data-stage-key="ownerRelease"] .v21-card h3{
  color:var(--violet)!important;
}
#architecture .v29-target-panel [data-stage-key="ownerRelease"] > h2 span{
  background:var(--violet)!important;
}
#architecture .v29-target-panel [data-stage-key="ownerRelease"] .v21-stage-formula{
  font-size:12px!important;
  white-space:normal!important;
  overflow-wrap:anywhere!important;
}
@media(max-width:1279px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:repeat(2,minmax(260px,1fr))!important;
  }
}
@media(max-width:760px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:1fr!important;
  }
}

/* v55: compact schema-light register bridge Stage 3 control-flow restoration */
.v48-gate-flow{display:grid;grid-template-columns:1fr;gap:7px;margin-top:8px}
.v48-gate-step{border:1.5px solid #263044;background:#0b101b;border-radius:12px;padding:8px}
.v48-gate-step h4{margin:0 0 3px;color:var(--green);font-size:12px;font-weight:900}
.v48-gate-step p{margin:0;color:#98a2b3;font-size:11px;line-height:1.35}
.v47-gate-arrow{text-align:center;color:var(--green);font-weight:950;font-size:15px;line-height:1}
.v54-ir-essential{border-color:rgba(34,211,238,.45)!important;background:rgba(34,211,238,.045)!important}


/* v55: schema-light register bridge Stage 3 horizontal control-flow restoration */
.v48-gate-flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;gap:6px;align-items:stretch;margin-top:8px}
.v48-gate-step{border:1.5px solid #263044;background:#0b101b;border-radius:12px;padding:8px;min-width:0}
.v48-gate-step h4{margin:0 0 4px;color:var(--green);font-size:12px;font-weight:900}
.v48-gate-step p{margin:0;color:#98a2b3;font-size:10.5px;line-height:1.3}
.v48-gate-step ul{margin:5px 0 0;padding-left:15px}
.v48-gate-step li{font-size:10.5px;line-height:1.28;margin:2px 0;color:#cbd5e1}
.v47-gate-arrow{display:grid;place-items:center;color:var(--green);font-weight:950;font-size:18px;line-height:1}
.v54-ir-essential{border-color:rgba(34,211,238,.45)!important;background:rgba(34,211,238,.045)!important}
@media(max-width:900px){
  .v48-gate-flow{grid-template-columns:1fr}
  .v47-gate-arrow{transform:rotate(90deg);padding:2px}
}


/* v55: readable horizontal schema-light register bridge Stage 3 flow */
@media(min-width:1280px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:minmax(230px,.9fr) minmax(270px,1.05fr) minmax(560px,1.9fr) minmax(310px,1.15fr)!important;
    gap:12px!important;
  }
}
.v48-gate-flow{display:grid;grid-template-columns:repeat(4,minmax(118px,1fr));gap:8px;align-items:stretch;margin-top:8px}
.v48-gate-step{border:1.5px solid #263044;background:#0b101b;border-radius:12px;padding:8px;min-width:0;position:relative}
.v48-gate-step:not(:last-child)::after{content:"→";position:absolute;right:-8px;top:50%;transform:translate(50%,-50%);color:var(--green);font-weight:950;font-size:16px;background:#0d1117;border-radius:999px;padding:0 2px}
.v48-gate-step h4{margin:0 0 4px;color:var(--green);font-size:12px;font-weight:900}
.v48-gate-step p{margin:0;color:#98a2b3;font-size:10.5px;line-height:1.3}
.v48-gate-step .gate-checks{display:block;margin-top:5px;color:#cbd5e1;font-size:10.5px;line-height:1.25}
.v48-gate-step .gate-checks b{color:#e8edf7}
.v54-ir-essential{border-color:rgba(34,211,238,.45)!important;background:rgba(34,211,238,.045)!important}
@media(max-width:1279px){
  .v48-gate-flow{grid-template-columns:repeat(2,minmax(160px,1fr))}
  .v48-gate-step:not(:last-child)::after{display:none}
}
@media(max-width:760px){
  .v48-gate-flow{grid-template-columns:1fr}
}


/* v55: readable schema-light register bridge Stage 3 flow + separate compact gate checks */
.v54-gate-flow{display:grid;grid-template-columns:repeat(4,minmax(125px,1fr));gap:10px;align-items:stretch;margin-top:8px}
.v54-gate-step{border:1.5px solid #263044;background:#0b101b;border-radius:12px;padding:9px;min-width:0}
.v54-gate-step h4{margin:0 0 5px;color:var(--green);font-size:12px;font-weight:900}
.v54-gate-step p{margin:0;color:#cbd5e1;font-size:11px;line-height:1.35}
.v50-flow-arrows{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:4px 0 0}
.v50-flow-arrows span{display:block;text-align:center;color:var(--green);font-weight:950;font-size:16px;line-height:1}
.v50-flow-arrows span:last-child{visibility:hidden}
.v54-gate-check-panel{border:1px solid #263044;background:#080d19;border-radius:14px;padding:10px;margin-top:10px}
.v54-gate-check-panel h4{margin:0 0 7px;color:var(--cyan);font-size:13px;font-weight:900}
.v54-gate-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.v54-gate-check{display:grid;grid-template-columns:46px minmax(0,1fr);gap:8px;align-items:center;border:1px solid #263044;background:#0b101b;border-radius:10px;padding:6px 8px;font-size:11.5px;color:#cbd5e1}
.v54-gate-check b{color:var(--cyan);font-weight:950}
.v54-ir-essential{border-color:rgba(34,211,238,.45)!important;background:rgba(34,211,238,.045)!important}
@media(min-width:1280px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:minmax(230px,.9fr) minmax(270px,1.05fr) minmax(560px,1.75fr) minmax(310px,1.15fr)!important;
    gap:12px!important;
  }
}
@media(max-width:1279px){
  .v54-gate-flow{grid-template-columns:repeat(2,minmax(160px,1fr))}
  .v50-flow-arrows{display:none}
  .v54-gate-checks{grid-template-columns:1fr}
}
@media(max-width:760px){
  .v54-gate-flow{grid-template-columns:1fr}
}


/* v55: readable schema-light register bridge Stage 3 connectors between boxes */
.v54-gate-flow{
  display:grid;
  grid-template-columns:minmax(120px,1fr) 22px minmax(145px,1.1fr) 22px minmax(145px,1.1fr) 22px minmax(125px,1fr);
  gap:6px;
  align-items:stretch;
  margin-top:8px;
}
.v54-gate-step{border:1.5px solid #263044;background:#0b101b;border-radius:12px;padding:9px;min-width:0}
.v54-gate-step h4{margin:0 0 5px;color:var(--green);font-size:12px;font-weight:900}
.v54-gate-step p{margin:0;color:#cbd5e1;font-size:11px;line-height:1.35}
.v54-gate-arrow{display:grid;place-items:center;color:var(--green);font-weight:950;font-size:18px;line-height:1}
.v54-gate-check-panel{border:1px solid #263044;background:#080d19;border-radius:14px;padding:10px;margin-top:10px}
.v54-gate-check-panel h4{margin:0 0 7px;color:var(--cyan);font-size:13px;font-weight:900}
.v54-gate-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.v54-gate-check{display:grid;grid-template-columns:46px minmax(0,1fr);gap:8px;align-items:center;border:1px solid #263044;background:#0b101b;border-radius:10px;padding:6px 8px;font-size:11.5px;color:#cbd5e1}
.v54-gate-check b{color:var(--cyan);font-weight:950}
.v54-ir-essential{border-color:rgba(34,211,238,.45)!important;background:rgba(34,211,238,.045)!important}
@media(min-width:1280px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:minmax(230px,.9fr) minmax(270px,1.05fr) minmax(560px,1.75fr) minmax(310px,1.15fr)!important;
    gap:12px!important;
  }
}
@media(max-width:1279px){
  .v54-gate-flow{grid-template-columns:1fr}
  .v54-gate-arrow{transform:rotate(90deg);padding:1px}
  .v54-gate-checks{grid-template-columns:1fr}
}


/* v55: prevent schema-light register bridge Stage 3 Layer B clipping */
@media(min-width:1280px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:minmax(230px,.9fr) minmax(270px,1.05fr) minmax(560px,1.75fr) minmax(310px,1.15fr)!important;
    gap:12px!important;
  }
}
.v54-gate-flow{
  display:grid;
  grid-template-columns:minmax(118px,.95fr) 20px minmax(150px,1.12fr) 20px minmax(150px,1.12fr) 20px minmax(145px,1.08fr);
  gap:6px;
  align-items:stretch;
  margin-top:8px;
}
.v54-gate-step{border:1.5px solid #263044;background:#0b101b;border-radius:12px;padding:9px;min-width:0;overflow:visible}
.v54-gate-step h4{margin:0 0 5px;color:var(--green);font-size:12px;font-weight:900}
.v54-gate-step p{margin:0;color:#cbd5e1;font-size:10.8px;line-height:1.32;overflow-wrap:normal;word-break:normal}
.v54-gate-arrow{display:grid;place-items:center;color:var(--green);font-weight:950;font-size:17px;line-height:1}
.v54-gate-check-panel{border:1px solid #263044;background:#080d19;border-radius:14px;padding:10px;margin-top:10px}
.v54-gate-check-panel h4{margin:0 0 7px;color:var(--cyan);font-size:13px;font-weight:900}
.v54-gate-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.v54-gate-check{display:grid;grid-template-columns:46px minmax(0,1fr);gap:8px;align-items:center;border:1px solid #263044;background:#0b101b;border-radius:10px;padding:6px 8px;font-size:11.5px;color:#cbd5e1}
.v54-gate-check b{color:var(--cyan);font-weight:950}
.v54-ir-essential{border-color:rgba(34,211,238,.45)!important;background:rgba(34,211,238,.045)!important}
@media(max-width:1279px){
  .v54-gate-flow{grid-template-columns:1fr}
  .v54-gate-arrow{transform:rotate(90deg);padding:1px}
  .v54-gate-checks{grid-template-columns:1fr}
}


/* v55: restore balanced schema-light register bridge width; compact Stage 3 internally */
@media(min-width:1280px){
  #architecture .v29-target-panel > .v21-five-col{
    grid-template-columns:minmax(230px,.9fr) minmax(270px,1.05fr) minmax(560px,1.75fr) minmax(310px,1.15fr)!important;
    gap:12px!important;
  }
}
.v54-gate-flow{
  display:grid;
  grid-template-columns:minmax(94px,.95fr) 14px minmax(118px,1.05fr) 14px minmax(118px,1.05fr) 14px minmax(104px,1fr);
  gap:5px;
  align-items:stretch;
  margin-top:8px;
}
.v54-gate-step{border:1.5px solid #263044;background:#0b101b;border-radius:12px;padding:8px;min-width:0;overflow:hidden}
.v54-gate-step h4{margin:0 0 4px;color:var(--green);font-size:11.5px;font-weight:900}
.v54-gate-step p{margin:0;color:#cbd5e1;font-size:10px;line-height:1.25;overflow-wrap:normal;word-break:normal}
.v54-gate-arrow{display:grid;place-items:center;color:var(--green);font-weight:950;font-size:16px;line-height:1}
.v54-gate-check-panel{border:1px solid #263044;background:#080d19;border-radius:14px;padding:10px;margin-top:10px}
.v54-gate-check-panel h4{margin:0 0 7px;color:var(--cyan);font-size:13px;font-weight:900}
.v54-gate-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.v54-gate-check{display:grid;grid-template-columns:46px minmax(0,1fr);gap:8px;align-items:center;border:1px solid #263044;background:#0b101b;border-radius:10px;padding:6px 8px;font-size:11.5px;color:#cbd5e1}
.v54-gate-check b{color:var(--cyan);font-weight:950}
.v54-ir-essential{border-color:rgba(34,211,238,.45)!important;background:rgba(34,211,238,.045)!important}
@media(max-width:1279px){
  .v54-gate-flow{grid-template-columns:1fr}
  .v54-gate-arrow{transform:rotate(90deg);padding:1px}
  .v54-gate-checks{grid-template-columns:1fr}
}

/* v56: Architecture tab UX repair after section merge. */
#architecture #canonical-architecture-runtime > .v21-five-col{
  display:grid!important;
  grid-template-columns:repeat(5,minmax(340px,1fr))!important;
  gap:14px!important;
  align-items:start!important;
  overflow-x:auto!important;
  overflow-y:visible!important;
  padding:2px 2px 14px!important;
  scroll-snap-type:x proximity!important;
  scrollbar-color:#334155 #080d19!important;
}
#architecture #canonical-architecture-runtime .v21-stage,
#architecture #canonical-architecture-runtime .v21-card,
#architecture #canonical-architecture-runtime .v54-gate-step,
#architecture #canonical-architecture-runtime .v54-gate-check{
  box-sizing:border-box!important;
  min-width:0!important;
  max-width:100%!important;
}
#architecture #canonical-architecture-runtime .v21-stage{
  overflow:visible!important;
  padding:12px!important;
  min-width:340px!important;
  scroll-snap-align:start!important;
}
#architecture #canonical-architecture-runtime [data-stage-key="ownerRelease"]{
  min-width:430px!important;
}
#architecture #canonical-architecture-runtime .v21-stage h2{
  font-size:clamp(14px,1.05vw,17px)!important;
  line-height:1.18!important;
  gap:7px!important;
  justify-content:center!important;
  text-align:center!important;
}
#architecture #canonical-architecture-runtime .v21-stage h2 span{
  width:24px!important;
  height:24px!important;
  font-size:12px!important;
  flex:0 0 auto!important;
}
#architecture #canonical-architecture-runtime .v21-card{
  border-radius:10px!important;
  padding:10px!important;
}
#architecture #canonical-architecture-runtime .v21-card h3{
  font-size:13px!important;
}
#architecture #canonical-architecture-runtime .v21-card p,
#architecture #canonical-architecture-runtime .v21-card li,
#architecture #canonical-architecture-runtime .v21-note{
  font-size:12px!important;
  line-height:1.35!important;
  overflow-wrap:anywhere!important;
}
#architecture #canonical-architecture-runtime .v21-proc-flow.target{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:4px!important;
}
#architecture #canonical-architecture-runtime .v21-proc-flow.target div{
  padding:5px 6px!important;
  font-size:10px!important;
}
#architecture #canonical-architecture-runtime .v21-field-grid > div{
  grid-template-columns:34px minmax(0,1fr)!important;
  padding:7px!important;
  column-gap:7px!important;
}
#architecture #canonical-architecture-runtime .v21-field-grid > div > b{
  width:26px!important;
  height:26px!important;
  font-size:11px!important;
}
#architecture #canonical-architecture-runtime .v21-field-grid > div > span{
  font-size:10.8px!important;
}
#architecture #canonical-architecture-runtime .v21-field-grid > div > small{
  font-size:9.6px!important;
}
#architecture #canonical-architecture-runtime .v54-gate-flow{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:6px!important;
}
#architecture #canonical-architecture-runtime .v54-gate-arrow{
  display:none!important;
}
#architecture #canonical-architecture-runtime .v54-gate-step{
  overflow:hidden!important;
  padding:7px!important;
}
#architecture #canonical-architecture-runtime .v54-gate-step h4{
  font-size:10.6px!important;
}
#architecture #canonical-architecture-runtime .v54-gate-step p{
  font-size:9.8px!important;
  line-height:1.25!important;
  overflow-wrap:anywhere!important;
}
#architecture #canonical-architecture-runtime .v54-gate-checks{
  grid-template-columns:1fr!important;
}
#architecture #canonical-architecture-runtime .v54-gate-check{
  grid-template-columns:82px minmax(0,1fr)!important;
  padding:6px!important;
  font-size:10px!important;
  line-height:1.25!important;
  overflow:hidden!important;
}
#architecture #canonical-architecture-runtime .v54-gate-check span,
#architecture #canonical-architecture-runtime .v54-gate-check b{
  min-width:0!important;
  overflow-wrap:break-word!important;
  word-break:normal!important;
}
#architecture #canonical-architecture-runtime .v21-stage-formula{
  font-size:12px!important;
  overflow-wrap:anywhere!important;
}
#architecture #canonical-architecture-runtime .v21-dec-grid{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
}
#architecture #canonical-architecture-runtime .v56-input{--pipe-rgb:var(--stage-d0-rgb);border-color:rgba(var(--pipe-rgb),.65);background:rgba(var(--pipe-rgb),.10)}
#architecture #canonical-architecture-runtime .v56-ir{--pipe-rgb:var(--stage-psi-n-rgb);border-color:rgba(var(--pipe-rgb),.65);background:rgba(var(--pipe-rgb),.09)}
#architecture #canonical-architecture-runtime .v56-owner{--pipe-rgb:var(--stage-dsl-ir-rgb);border-color:rgba(var(--pipe-rgb),.65);background:rgba(var(--pipe-rgb),.10)}
#architecture #canonical-architecture-runtime .v56-land{--pipe-rgb:var(--stage-owner-ttp-delta-rgb);border-color:rgba(var(--pipe-rgb),.65);background:rgba(var(--pipe-rgb),.10)}
#architecture #canonical-architecture-runtime .v56-reread{--pipe-rgb:var(--ds-color-success-rgb);border-color:rgba(var(--pipe-rgb),.65);background:rgba(var(--pipe-rgb),.10)}
#architecture #canonical-architecture-runtime .v56-decision{--pipe-rgb:var(--stage-collapse-restoration-rgb);border-color:rgba(var(--pipe-rgb),.65);background:rgba(var(--pipe-rgb),.09)}
#architecture #canonical-architecture-runtime .v21-s1{--sc:var(--stage-d0)!important;--sc-rgb:var(--stage-d0-rgb)!important}
#architecture #canonical-architecture-runtime .v21-s2{--sc:var(--stage-psi-n)!important;--sc-rgb:var(--stage-psi-n-rgb)!important}
#architecture #canonical-architecture-runtime .v21-s3{--sc:var(--stage-dsl-ir)!important;--sc-rgb:var(--stage-dsl-ir-rgb)!important}
#architecture #canonical-architecture-runtime .v21-s4{--sc:var(--stage-owner-ttp-delta)!important;--sc-rgb:var(--stage-owner-ttp-delta-rgb)!important}
#architecture #canonical-architecture-runtime .v21-s5{--sc:var(--stage-collapse-restoration)!important;--sc-rgb:var(--stage-collapse-restoration-rgb)!important}
#architecture #canonical-architecture-runtime .v21-stage{
  background:rgba(var(--sc-rgb),.045)!important;
  border-color:rgba(var(--sc-rgb),.92)!important;
}
#architecture #canonical-architecture-runtime .v21-card{
  border-color:rgba(var(--sc-rgb),.32)!important;
  background:rgba(8,13,25,.78)!important;
}
#architecture #canonical-architecture-runtime .v21-note{
  background:rgba(var(--sc-rgb),.045)!important;
}
#architecture #canonical-architecture-runtime .v21-s5 .v21-purple{
  --sc:var(--stage-collapse-restoration)!important;
  --sc-rgb:var(--stage-collapse-restoration-rgb)!important;
  background:rgba(var(--stage-collapse-restoration-rgb),.055)!important;
}
#architecture #canonical-architecture-runtime .v60-reread-label{
  color:var(--green)!important;
  font-style:normal!important;
}
#architecture #canonical-architecture-runtime .v60-reread-phase{
  --sc:var(--ds-color-success)!important;
  --sc-rgb:var(--ds-color-success-rgb)!important;
  border-color:rgba(var(--ds-color-success-rgb),.45)!important;
  background:rgba(var(--ds-color-success-rgb),.045)!important;
}
#architecture #canonical-architecture-runtime .v60-reread-phase h3{
  color:var(--green)!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-stack{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:12px!important;
  margin:12px 0 16px!important;
  max-width:100%!important;
  border:1px solid #263044!important;
  background:rgba(8,13,25,.66)!important;
  border-radius:14px!important;
  padding:12px!important;
  overflow:hidden!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-heading{
  color:#f8fafc!important;
  font-size:14px!important;
  font-weight:950!important;
  letter-spacing:.02em!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-columns{
  display:grid!important;
  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
  gap:18px!important;
  align-items:start!important;
  max-width:100%!important;
  min-width:0!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-panel{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:8px!important;
  min-width:0!important;
  max-width:100%!important;
  align-self:start!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-panel + .v60-pipeline-panel{
  border-left:3px solid var(--green)!important;
  padding-left:18px!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-label{
  color:var(--ds-color-text-muted)!important;
  font-size:11px!important;
  font-weight:950!important;
  letter-spacing:.06em!important;
  text-transform:uppercase!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-list{
  list-style:none!important;
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:8px!important;
  margin:0!important;
  padding:0!important;
  width:100%!important;
  max-width:100%!important;
  min-width:0!important;
  overflow:visible!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-phase-group{
  position:relative!important;
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:5px!important;
  min-width:0!important;
  max-width:100%!important;
  border:1px dashed rgba(var(--pipe-rgb,51,65,85),.32)!important;
  border-radius:12px!important;
  background:rgba(var(--pipe-rgb,51,65,85),.035)!important;
  padding:7px!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-phase-group[data-phase-break="true"]{
  margin-top:8px!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-phase-group[data-phase-break="true"]::before{
  content:"↓"!important;
  position:absolute!important;
  left:12px!important;
  top:-18px!important;
  color:rgba(226,232,240,.76)!important;
  font-size:13px!important;
  font-weight:950!important;
  line-height:1!important;
}
#architecture #canonical-architecture-runtime .v60-phase-flow{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px 7px!important;
  align-items:center!important;
  min-width:0!important;
  max-width:100%!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-step{
  display:inline-grid!important;
  grid-template-columns:26px minmax(0,1fr)!important;
  gap:8px!important;
  align-items:center!important;
  min-width:0!important;
  max-width:min(100%,260px)!important;
  border:1px solid #334155!important;
  border-radius:10px!important;
  padding:6px 8px!important;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace!important;
  font-weight:900!important;
  color:#f8fafc!important;
}
#architecture #canonical-architecture-runtime .v60-formal-pipeline .v60-pipeline-step{
  max-width:min(100%,360px)!important;
}
#architecture #canonical-architecture-runtime .v60-pipeline-arrow{
  display:inline-grid!important;
  place-items:center!important;
  color:rgba(226,232,240,.72)!important;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace!important;
  font-size:14px!important;
  font-weight:950!important;
  align-self:center!important;
}
#architecture #canonical-architecture-runtime .v60-step-number{
  width:22px!important;
  height:22px!important;
  border-radius:999px!important;
  display:inline-grid!important;
  place-items:center!important;
  background:rgba(var(--pipe-rgb,51,65,85),.88)!important;
  color:#fff!important;
  font-size:11px!important;
  font-weight:950!important;
}
#architecture #canonical-architecture-runtime .v60-step-label{
  white-space:normal!important;
  overflow-wrap:anywhere!important;
  word-break:normal!important;
  min-width:0!important;
  font-size:clamp(10px,.72vw,12px)!important;
  line-height:1.32!important;
}
#architecture #canonical-architecture-runtime .v56-formula-flow .v60-step-label{
  font-size:clamp(10px,.68vw,12px)!important;
}
#architecture #canonical-architecture-runtime .v60-formal-trace-copy{
  display:grid!important;
  gap:7px!important;
  min-width:0!important;
  max-width:100%!important;
  border:1px solid rgba(var(--stage-collapse-restoration-rgb),.38)!important;
  background:rgba(3,7,18,.76)!important;
  border-radius:12px!important;
  padding:10px!important;
}
#architecture #canonical-architecture-runtime .v60-formal-trace-copy pre{
  margin:0!important;
  max-width:100%!important;
  overflow:auto!important;
  white-space:pre!important;
  border:1px solid #263044!important;
  background:#050914!important;
  border-radius:10px!important;
  padding:9px 10px!important;
}
#architecture #canonical-architecture-runtime .v60-formal-trace-copy code{
  color:#f8fafc!important;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace!important;
  font-size:12px!important;
  line-height:1.45!important;
}
@media(max-width:920px){
  #architecture #canonical-architecture-runtime .v60-pipeline-columns{
    grid-template-columns:minmax(0,1fr)!important;
  }
  #architecture #canonical-architecture-runtime .v60-pipeline-panel + .v60-pipeline-panel{
    border-left:0!important;
    border-top:3px solid var(--green)!important;
    padding-left:0!important;
    padding-top:12px!important;
  }
}
#architecture #canonical-architecture-runtime .v60-field-diagnostics{
  display:grid!important;
  gap:8px!important;
  margin-top:8px!important;
}
#architecture #canonical-architecture-runtime .v60-diagnostic-card{
  border:1px solid #263044!important;
  background:#0b101b!important;
  border-radius:10px!important;
  padding:7px 8px!important;
  display:grid!important;
  gap:3px!important;
}
#architecture #canonical-architecture-runtime .v60-diagnostic-card b{
  color:var(--orange)!important;
  font-size:11.5px!important;
}
#architecture #canonical-architecture-runtime .v60-diagnostic-card span{
  color:#cbd5e1!important;
  font-size:11px!important;
  line-height:1.32!important;
}
#architecture #canonical-architecture-runtime .v60-field-targets{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  align-items:center!important;
  border:1px solid #263044!important;
  background:#080d19!important;
  border-radius:10px!important;
  padding:7px!important;
}
#architecture #canonical-architecture-runtime .v60-field-heading{
  color:var(--orange)!important;
  font-size:11px!important;
  font-weight:950!important;
  letter-spacing:.04em!important;
  text-transform:uppercase!important;
  flex:0 0 100%!important;
}
#architecture #canonical-architecture-runtime .v60-field-target{
  display:inline-flex!important;
  align-items:center!important;
  white-space:nowrap!important;
  border:1px solid rgba(var(--stage-owner-ttp-delta-rgb),.55)!important;
  background:rgba(var(--stage-owner-ttp-delta-rgb),.10)!important;
  border-radius:999px!important;
  padding:4px 8px!important;
  color:#fff7ed!important;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace!important;
  font-size:12px!important;
  font-weight:900!important;
}
#architecture #canonical-architecture-runtime .v60-field-grammar .v60-field-target{
  border-color:rgba(var(--stage-psi-n-rgb),.62)!important;
  background:rgba(var(--stage-psi-n-rgb),.10)!important;
}
#architecture #canonical-architecture-runtime .v60-loopbreak-form{
  border-color:rgba(var(--stage-owner-ttp-delta-rgb),.75)!important;
  flex:1 1 auto!important;
}
#architecture #canonical-architecture-runtime .v60-field-meaning{
  color:#cbd5e1!important;
  font-size:11px!important;
  line-height:1.32!important;
  min-width:180px!important;
  flex:1 1 180px!important;
}
#architecture #canonical-architecture-runtime .v60-field-wide{
  flex:1 1 100%!important;
}
#architecture #canonical-architecture-runtime .v60-diagnostic-note{
  border:1px dashed rgba(34,197,94,.45)!important;
  background:rgba(34,197,94,.06)!important;
  border-radius:10px!important;
  padding:8px!important;
  color:#d1fae5!important;
  font-size:11px!important;
  line-height:1.35!important;
}
#architecture #canonical-architecture-runtime .v21-dec-grid .complete{
  border-color:rgba(34,197,94,.7)!important;
  color:#bbf7d0!important;
}
@media(max-width:1180px){
  #architecture #canonical-architecture-runtime > .v21-five-col{
    grid-template-columns:repeat(5,minmax(320px,1fr))!important;
  }
}
@media(max-width:760px){
  #architecture #canonical-architecture-runtime > .v21-five-col{
    grid-template-columns:1fr!important;
    overflow-x:visible!important;
  }
  #architecture #canonical-architecture-runtime .v21-stage,
  #architecture #canonical-architecture-runtime [data-stage-key="ownerRelease"]{
    min-width:0!important;
  }
}

.runtimeSourceNote{
  border:1px dashed #334155;
  background:#080d19;
  border-radius:14px;
  padding:10px 12px;
  color:#cbd5e1;
  font-size:13px;
  margin:8px 0 12px;
}
.runtimeSourceNote code{white-space:nowrap}
.compactBridgeFlow{align-items:stretch}
.compactBridgeFlow .notationChip{margin:0}

/* v61: Architecture cards are a selected-primary carousel, not a horizontal rail. */
#architecture #canonical-architecture-runtime .v60-architecture-carousel{
  --v61-carousel-gap:var(--ds-carousel-gap);
  --v61-carousel-primary:var(--ds-carousel-primary-width);
  --v61-carousel-side:var(--ds-carousel-side-width);
  --v61-carousel-far:var(--ds-carousel-far-width);
  display:grid;
  gap:12px;
  margin-top:12px;
}
#architecture #canonical-architecture-runtime .v60-carousel-controls{
  display:flex;
  align-items:center;
  justify-content:center;
  gap:10px;
}
#architecture #canonical-architecture-runtime .v60-carousel-btn{
  width:38px;
  height:38px;
  display:grid;
  place-items:center;
  border:1px solid var(--ds-color-border-strong);
  border-radius:var(--ds-radius-chip);
  background:var(--ds-color-surface-code);
  color:var(--ds-color-text);
  cursor:pointer;
  font-size:24px;
  font-weight:950;
  line-height:1;
}
#architecture #canonical-architecture-runtime .v60-carousel-btn:hover,
#architecture #canonical-architecture-runtime .v60-carousel-btn:focus-visible{
  border-color:var(--ds-color-focus);
  background:rgba(var(--ds-color-focus-rgb),.10);
  outline:none;
}
#architecture #canonical-architecture-runtime .v60-carousel-status{
  min-width:auto;
  display:flex;
  flex-direction:row;
  align-items:center;
  justify-content:center;
  gap:8px;
  text-align:center;
  border:1px solid var(--ds-color-border);
  background:var(--ds-color-surface-deep);
  border-radius:var(--ds-radius-chip);
  padding:5px 9px;
  color:var(--ds-color-text-subtle);
  font-size:13px;
  font-weight:850;
}
#architecture #canonical-architecture-runtime .v60-carousel-status-label{
  position:absolute!important;
  width:1px!important;
  height:1px!important;
  padding:0!important;
  margin:-1px!important;
  overflow:hidden!important;
  clip:rect(0,0,0,0)!important;
  white-space:nowrap!important;
  border:0!important;
}
#architecture #canonical-architecture-runtime > .v60-architecture-carousel > .v60-architecture-rail,
#architecture #canonical-architecture-runtime .v60-architecture-rail{
  display:flex!important;
  grid-template-columns:none!important;
  justify-content:center!important;
  align-items:center!important;
  gap:var(--v61-carousel-gap)!important;
  overflow:hidden!important;
  overflow-x:hidden!important;
  overflow-y:visible!important;
  padding:6px 2px 10px!important;
  scroll-snap-type:none!important;
  scrollbar-width:none!important;
}
#architecture #canonical-architecture-runtime .v60-architecture-rail::-webkit-scrollbar{
  display:none;
}
#architecture #canonical-architecture-runtime .v60-carousel-card{
  flex:0 0 var(--v61-carousel-side)!important;
  min-width:0!important;
  max-width:var(--v61-carousel-side)!important;
  min-height:0!important;
  max-height:none!important;
  padding:12px!important;
  overflow:visible!important;
  opacity:var(--ds-carousel-preview-opacity);
  transform:none;
  transform-origin:center;
  scroll-snap-align:none!important;
  transition:transform var(--ds-motion-duration) var(--ds-motion-easing), opacity var(--ds-motion-duration) var(--ds-motion-easing), flex-basis var(--ds-motion-duration) var(--ds-motion-easing), max-width var(--ds-motion-duration) var(--ds-motion-easing), box-shadow var(--ds-motion-duration) var(--ds-motion-easing), background var(--ds-motion-duration) var(--ds-motion-easing);
}
#architecture #canonical-architecture-runtime .v60-carousel-card h2{
  margin:0!important;
  font-size:clamp(14px,1.05vw,17px)!important;
  line-height:1.18!important;
  justify-content:center!important;
  text-align:center!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card h2 span{
  width:24px!important;
  height:24px!important;
  font-size:12px!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard{
  display:block!important;
  margin-top:8px!important;
  padding:8px!important;
  opacity:1;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard h3,
#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard b{
  font-size:13px!important;
  line-height:1.2!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard p,
#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard li,
#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard span,
#architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard small{
  font-size:12px!important;
  line-height:1.35!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v21-field-grid,
#architecture #canonical-architecture-runtime .v60-carousel-card .v21-dec-grid,
#architecture #canonical-architecture-runtime .v60-carousel-card .v54-gate-checks{
  grid-template-columns:1fr!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v54-gate-flow{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v54-gate-arrow{
  display:none!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-stage-key="psi"]{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  align-content:start!important;
  gap:8px!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-stage-key="psi"] > h2,
#architecture #canonical-architecture-runtime .v60-carousel-card[data-stage-key="psi"] > [data-substage-key="operational-boundary"]{
  grid-column:1 / -1!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-stage-key="psi"] > .v60-selectable-subcard{
  margin-top:0!important;
}
#architecture #canonical-architecture-runtime .v63-two-column-stage-layout{
  display:grid!important;
  grid-template-columns:minmax(0,.94fr) minmax(0,1.06fr)!important;
  gap:10px!important;
  align-items:start!important;
  min-width:0!important;
}
#architecture #canonical-architecture-runtime .v63-stage-stack{
  display:grid!important;
  gap:8px!important;
  align-content:start!important;
  min-width:0!important;
}
#architecture #canonical-architecture-runtime .v63-two-column-stage-layout .v60-selectable-subcard{
  margin-top:0!important;
}
#architecture #canonical-architecture-runtime .v63-owner-release-layout{
  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"]{
  order:3;
  flex-basis:var(--v61-carousel-primary)!important;
  max-width:960px!important;
  min-height:0!important;
  max-height:none!important;
  align-self:stretch!important;
  overflow:visible!important;
  opacity:1;
  transform:none;
  z-index:3;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] h2{
  font-size:clamp(14px,1.05vw,17px)!important;
  line-height:1.18!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] h2 span{
  width:24px!important;
  height:24px!important;
  font-size:12px!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v60-selectable-subcard{
  display:block!important;
  opacity:1;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v60-selectable-subcard h3,
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v60-selectable-subcard b{
  font-size:13px!important;
  line-height:1.2!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v60-selectable-subcard p,
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v60-selectable-subcard li,
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v60-selectable-subcard span,
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v60-selectable-subcard small{
  font-size:12px!important;
  line-height:1.35!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v54-gate-flow{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"] .v54-gate-checks{
  grid-template-columns:1fr!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="prev"]{order:2}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="next"]{order:4}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="far-prev"],
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="far-next"]{
  flex-basis:var(--v61-carousel-far)!important;
  max-width:var(--v61-carousel-far)!important;
  opacity:var(--ds-carousel-preview-far-opacity);
  transform:none;
  max-height:var(--ds-carousel-preview-far-max-height)!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="far-prev"]{order:1}
#architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="far-next"]{order:5}
#architecture #canonical-architecture-runtime .v60-carousel-card:focus-visible{
  outline:2px solid var(--ds-color-focus);
  outline-offset:3px;
}
#architecture #canonical-architecture-runtime .v60-carousel-dots{
  display:flex;
  justify-content:center;
  flex-wrap:wrap;
  gap:6px;
}
#architecture #canonical-architecture-runtime .v60-carousel-dot{
  width:30px;
  height:30px;
  border:1px solid var(--ds-color-border-strong);
  border-radius:var(--ds-radius-chip);
  background:var(--ds-color-surface-code);
  color:var(--ds-color-text-subtle);
  cursor:pointer;
  font-weight:950;
}
#architecture #canonical-architecture-runtime .v60-carousel-dot[aria-current="true"]{
  border-color:var(--ds-color-focus);
  color:#bbf7d0;
  background:rgba(var(--ds-color-focus-rgb),.12);
}
#architecture #canonical-architecture-runtime .v60-carousel-dot:hover,
#architecture #canonical-architecture-runtime .v60-carousel-dot:focus-visible{
  border-color:var(--ds-color-cyan);
  color:#fff;
  outline:none;
}
@media(max-width:1180px){
  #architecture #canonical-architecture-runtime .v60-architecture-carousel{
    --v61-carousel-primary:min(680px,68vw);
    --v61-carousel-side:138px;
    --v61-carousel-far:82px;
  }
}
@media(max-width:760px){
  #architecture #canonical-architecture-runtime .v60-architecture-carousel{
    --v61-carousel-primary:100%;
  }
  #architecture #canonical-architecture-runtime .v60-architecture-rail{
    display:block!important;
    padding:4px 0!important;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-card{
    display:none!important;
    max-width:none!important;
    width:100%!important;
    transform:none!important;
    opacity:1!important;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-card[data-carousel-position="center"]{
    display:block!important;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-status{
    min-width:0;
    flex:1 1 auto;
  }
}
@media(prefers-reduced-motion:reduce){
  #architecture #canonical-architecture-runtime .v60-carousel-card,
  #architecture #canonical-architecture-runtime .v60-carousel-btn,
  #architecture #canonical-architecture-runtime .v60-carousel-dot{
    transition:none!important;
  }
}
@media print{
  #architecture #canonical-architecture-runtime .v60-carousel-controls,
  #architecture #canonical-architecture-runtime .v60-carousel-dots{
    display:none!important;
  }
  #architecture #canonical-architecture-runtime > .v21-five-col,
  #architecture #canonical-architecture-runtime .v60-architecture-rail{
    display:block!important;
    overflow:visible!important;
  }
  #architecture #canonical-architecture-runtime .v21-stage,
  #architecture #canonical-architecture-runtime .v60-carousel-card{
    display:block!important;
    min-width:0!important;
    max-width:none!important;
    max-height:none!important;
    transform:none!important;
    opacity:1!important;
    break-inside:avoid;
    page-break-inside:avoid;
    margin-bottom:12px;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-card .v60-selectable-subcard{
    display:block!important;
  }
}

/* v62: contain card-4 dense notation and make side cards scaled full-card previews. */
#architecture #canonical-architecture-runtime .v60-field-targets{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  align-items:start!important;
  width:100%!important;
  min-width:0!important;
  overflow:hidden!important;
}
#architecture #canonical-architecture-runtime .v60-field-chiprow,
#architecture #canonical-architecture-runtime .v60-grounding-members{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  min-width:0!important;
  max-width:100%!important;
}
#architecture #canonical-architecture-runtime .v60-field-description,
#architecture #canonical-architecture-runtime .v60-field-wide{
  display:block!important;
  min-width:0!important;
  width:100%!important;
  flex:1 1 100%!important;
  overflow-wrap:anywhere!important;
}
#architecture #canonical-architecture-runtime .example-chip-grid{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:6px!important;
  align-items:center!important;
  justify-content:start!important;
  max-width:100%!important;
  overflow:visible!important;
}
#architecture #canonical-architecture-runtime .example-chip-row{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  min-width:0!important;
  max-width:100%!important;
}
#architecture #canonical-architecture-runtime .example-chip-grid .v60-field-target{
  min-width:0!important;
  max-width:100%!important;
  justify-content:center!important;
}
#architecture #canonical-architecture-runtime .example-chip-description{
  display:block!important;
  grid-column:1 / -1!important;
  margin-top:2px!important;
}
#architecture #canonical-architecture-runtime .v60-loopbreak-formula{
  display:grid!important;
  grid-template-columns:auto auto minmax(0,1fr)!important;
  gap:7px!important;
  align-items:start!important;
  min-width:0!important;
  width:100%!important;
  border:1px solid rgba(var(--stage-owner-ttp-delta-rgb),.55)!important;
  background:rgba(var(--stage-owner-ttp-delta-rgb),.10)!important;
  border-radius:var(--ds-radius-card)!important;
  padding:7px!important;
}
#architecture #canonical-architecture-runtime .v60-loopbreak-operands{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:5px!important;
  min-width:0!important;
  max-width:100%!important;
}
#architecture #canonical-architecture-runtime .v60-loopbreak-operand-row{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  align-items:center!important;
  min-width:0!important;
  max-width:100%!important;
}
#architecture #canonical-architecture-runtime .v60-reread-decision-formula{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:6px!important;
  text-align:left!important;
  white-space:normal!important;
  overflow-wrap:anywhere!important;
}
#architecture #canonical-architecture-runtime .v60-reread-signature,
#architecture #canonical-architecture-runtime .v60-reread-outcomes{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  align-items:center!important;
  min-width:0!important;
  max-width:100%!important;
}
#architecture #canonical-architecture-runtime .v60-reread-signature{
  color:#fff7ed!important;
}
#architecture #canonical-architecture-runtime .v60-reread-turnstile,
#architecture #canonical-architecture-runtime .v60-decision-separator{
  color:rgba(var(--stage-owner-ttp-delta-rgb),.8)!important;
  font-weight:950!important;
}
#architecture #canonical-architecture-runtime .v60-decision-outcome{
  display:inline-flex!important;
  align-items:center!important;
  border:1px solid rgba(var(--stage-owner-ttp-delta-rgb),.42)!important;
  background:rgba(var(--stage-owner-ttp-delta-rgb),.08)!important;
  border-radius:var(--ds-radius-chip)!important;
  padding:3px 7px!important;
  color:#fff7ed!important;
  font-weight:900!important;
}
#architecture #canonical-architecture-runtime .v60-loopbreak-head,
#architecture #canonical-architecture-runtime .v60-loopbreak-turnstile,
#architecture #canonical-architecture-runtime .v60-loopbreak-chip,
#architecture #canonical-architecture-runtime .v60-grounding-chip,
#architecture #canonical-architecture-runtime .v60-grounding-label{
  font-family:var(--ds-font-monospace)!important;
  font-weight:900!important;
}
#architecture #canonical-architecture-runtime .v60-loopbreak-head,
#architecture #canonical-architecture-runtime .v60-loopbreak-turnstile{
  color:#fff7ed!important;
  white-space:nowrap!important;
}
#architecture #canonical-architecture-runtime .v60-loopbreak-chip,
#architecture #canonical-architecture-runtime .v60-grounding-chip{
  display:inline-flex!important;
  align-items:center!important;
  border:1px solid rgba(var(--stage-owner-ttp-delta-rgb),.45)!important;
  background:rgba(var(--stage-owner-ttp-delta-rgb),.08)!important;
  border-radius:var(--ds-radius-chip)!important;
  padding:3px 7px!important;
  color:#fff7ed!important;
  white-space:normal!important;
  overflow-wrap:anywhere!important;
}
#architecture #canonical-architecture-runtime .v60-grounding-block{
  display:grid!important;
  grid-template-columns:auto minmax(0,1fr)!important;
  gap:6px!important;
  align-items:start!important;
  min-width:0!important;
  width:100%!important;
  border:1px solid var(--ds-color-border)!important;
  background:var(--ds-color-surface-deep)!important;
  border-radius:var(--ds-radius-card)!important;
  padding:7px!important;
}
#architecture #canonical-architecture-runtime .v60-grounding-label{
  color:var(--ds-color-text-subtle)!important;
}
#architecture #canonical-architecture-runtime > .v60-architecture-carousel > .v60-architecture-rail,
#architecture #canonical-architecture-runtime .v60-architecture-rail{
  align-items:flex-start!important;
  overflow:visible!important;
  overflow-x:visible!important;
  overflow-y:visible!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v62-decision-grid{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:7px!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-card .v62-decision-grid .complete{
  grid-column:1 / -1!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-slot{
  position:relative!important;
  display:grid!important;
  align-items:start!important;
  justify-items:center!important;
  flex:0 0 var(--v61-carousel-side)!important;
  width:var(--v61-carousel-side)!important;
  height:var(--ds-carousel-preview-near-slot-height)!important;
  min-width:0!important;
  overflow:visible!important;
  pointer-events:none!important;
  z-index:1!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="center"]{
  order:3!important;
  flex:0 1 var(--v61-carousel-primary)!important;
  width:var(--v61-carousel-primary)!important;
  height:auto!important;
  align-self:flex-start!important;
  z-index:4!important;
  pointer-events:auto!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="prev"]{order:2!important; z-index:2!important}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="next"]{order:4!important; z-index:2!important}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-prev"],
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-next"]{
  flex-basis:var(--v61-carousel-far)!important;
  width:var(--v61-carousel-far)!important;
  height:var(--ds-carousel-preview-far-slot-height)!important;
  z-index:0!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-prev"]{order:1!important}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-next"]{order:5!important}
#architecture #canonical-architecture-runtime .v60-carousel-slot:not([data-carousel-position="center"]) > .v60-carousel-card{
  position:absolute!important;
  left:50%!important;
  top:0!important;
  flex:none!important;
  width:var(--ds-carousel-preview-source-width)!important;
  max-width:none!important;
  min-width:0!important;
  min-height:auto!important;
  max-height:none!important;
  padding:12px!important;
  overflow:visible!important;
  opacity:var(--ds-carousel-preview-opacity)!important;
  transform:translateX(-50%) scale(var(--ds-carousel-preview-near-scale))!important;
  transform-origin:top center!important;
  pointer-events:auto!important;
  box-shadow:var(--ds-shadow-preview-card)!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-prev"] > .v60-carousel-card,
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-next"] > .v60-carousel-card{
  width:var(--ds-carousel-preview-far-source-width)!important;
  opacity:var(--ds-carousel-preview-far-opacity)!important;
  transform:translateX(-50%) scale(var(--ds-carousel-preview-far-scale))!important;
}
#architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="center"] > .v60-carousel-card{
  flex:none!important;
  width:100%!important;
  max-width:960px!important;
  transform:none!important;
}
@media(max-width:1500px) and (min-width:1181px){
  #architecture #canonical-architecture-runtime .v60-architecture-carousel{
    --ds-carousel-preview-near-scale:.30;
    --ds-carousel-preview-far-scale:.11;
    --ds-carousel-preview-near-slot-height:500px;
    --ds-carousel-preview-far-slot-height:210px;
  }
}
@media(max-width:1180px){
  #architecture #canonical-architecture-runtime .v60-architecture-carousel{
    --ds-carousel-preview-source-width:min(680px,68vw);
    --ds-carousel-preview-near-scale:.18;
    --ds-carousel-preview-near-slot-height:300px;
    --ds-carousel-preview-far-source-width:min(680px,68vw);
    --ds-carousel-preview-far-scale:.075;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-prev"],
  #architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="far-next"]{
    display:none!important;
  }
}
@media(max-width:760px){
  #architecture #canonical-architecture-runtime .v60-carousel-slot{
    display:none!important;
    width:100%!important;
    height:auto!important;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="center"]{
    display:block!important;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-slot[data-carousel-position="center"] > .v60-carousel-card{
    max-width:none!important;
    width:100%!important;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-card[data-stage-key="psi"]{
    grid-template-columns:1fr!important;
  }
  #architecture #canonical-architecture-runtime .v60-carousel-card[data-stage-key="psi"] > h2,
  #architecture #canonical-architecture-runtime .v60-carousel-card[data-stage-key="psi"] > [data-substage-key="operational-boundary"]{
    grid-column:auto!important;
  }
  #architecture #canonical-architecture-runtime .v63-two-column-stage-layout,
  #architecture #canonical-architecture-runtime .v63-owner-release-layout{
    grid-template-columns:1fr!important;
  }
  #architecture #canonical-architecture-runtime .example-chip-grid{
    grid-template-columns:minmax(0,1fr)!important;
  }
}
@media(max-width:620px){
  #architecture #canonical-architecture-runtime .v60-loopbreak-formula,
  #architecture #canonical-architecture-runtime .v60-grounding-block{
    grid-template-columns:1fr!important;
  }
  #architecture #canonical-architecture-runtime .example-chip-grid{
    grid-template-columns:minmax(0,1fr)!important;
  }
}
@media print{
  #architecture #canonical-architecture-runtime .v60-carousel-slot{
    display:block!important;
    width:auto!important;
    height:auto!important;
    overflow:visible!important;
    margin-bottom:12px!important;
  }
}

</style>
</head>
<body>
<header class="siteHero" id="site-hero" aria-label="DAEE Epistemics Control Wiki">
<div class="siteHeroInner">
<h1>DAEE Epistemics Control Wiki</h1>
<p>daee-epistemics is a compact DSL-governed runtime for diagnosing a surface discourse, selecting the live owner-backed operation, landing the burden, rereading state, and releasing only the governed restorative response.</p>
<div class="badges" aria-label="Runtime phase color legend">
<span class="badge" data-masthead-phase="phase-input"><i class="dot phase-input"></i>surface signal</span>
<span class="badge" data-masthead-phase="phase-layer-a"><i class="dot phase-layer-a"></i>noetic signal-state</span>
<span class="badge" data-masthead-phase="phase-gate"><i class="dot phase-gate"></i>DSL/IR + route gate</span>
<span class="badge" data-masthead-phase="phase-owner-delta"><i class="dot phase-owner-delta"></i>owner/TTP + Δ landing</span>
<span class="badge" data-masthead-phase="phase-reread-closure"><i class="dot phase-reread-closure"></i>R(H,Δ) reread</span>
<span class="badge" data-masthead-phase="phase-public-boundary"><i class="dot phase-public-boundary"></i>T_lang public boundary</span>
</div>
</div>
</header>
{{ TOPBAR }}
<main>
{{ SECTIONS }}
</main>
{{ GENERATED_DATA }}
<script>
const CURRENT_STAGES = [{"id": "source", "n": "0", "title": "Source / Runtime Boundary", "color": "blue", "kind": "retained source/runtime boundary", "receives": ["Canonical atomized source under atomics/skill/.", "Generated runtime under skill/.", "Repo/dev harness that is not canonical package content."], "detects": ["Source-of-truth versus generated output.", "Original module IDs versus omnibus bundle containers.", "Package boundary and runtime resolver constraints."], "writes": ["Generated skill/ runtime.", "compiled-module-map.json and build-manifest.json.", "User-facing package root."], "next": ["Edits happen in atomics/skill; generated runtime is rebuilt.", "Bundle co-location is availability, not activation."], "gap": ["schema-light register bridge keeps this boundary and adds fixture-backed registers to the same source/runtime pipeline."]}, {"id": "input", "n": "1", "title": "Input / Surface Discourse", "color": "blue", "kind": "retained compact baseline stage", "receives": ["User claim, doubt, objection, proof packet, slogan, source request, or worldview claim."], "detects": ["Criterion language, source-status cues, testimony posture, discourse register, repeated slogans, visible objection family."], "writes": ["D as input signal and candidate diagnostic features.", "Initial read-status/confidence surface for Layer A."], "next": ["No direct argument-bank response before diagnostic reduction."], "gap": ["The retained baseline has D implicitly; schema-light register bridge makes D₀ → Ψᴺ explicit."]}, {"id": "noetic", "n": "2", "title": "Noetic / Meta-Noetic Read", "color": "green", "kind": "retained compact baseline stage", "receives": ["Surface discourse plus signal features.", "V1 / noetic checklist / deformation / concealment / discourse-orientation surfaces."], "detects": ["N: operative noetic frame.", "m: deformation/concealment/memetic mode.", "Reason role, testimony posture, DO-orient, source-status pressure."], "writes": ["Case-state and compact control features feeding IR(N,m,τ,σ).", "Held/deferred routes where warranted."], "next": ["V1/core axes and triggered passes complete or case is held/partial."], "gap": ["♥/ξ/Ω/μ/κ are implemented as derived/conditional bridge registers, not hard schema fields."]}, {"id": "ir", "n": "3", "title": "IR / Gate / Routing", "color": "cyan", "kind": "retained compact baseline stage", "receives": ["Typed diagnostic state, triggered Phase 2 passes, source-status, claim level, pattern profile, held routes."], "detects": ["IR consistency, suppression rules, routing precedence, P7 stops, source-status non-equivalence."], "writes": ["IR(N,m,τ,σ).", "Current bounded operator / live burden candidate.", "Matched owner source identities."], "next": ["Dispatch only after gate checks and routing precedence authorize the owner/TTP."], "gap": ["schema-light register bridge extends the compact control surface to IR(N,m,τ,σ,♥,ξ,Ω,μ,κ) as derived/conditional structural registers."]}, {"id": "owner", "n": "4", "title": "Owner / TTP Execution", "color": "violet", "kind": "retained compact baseline stage", "receives": ["Validated IR and active live burden B.", "Owner-loadform maps and module source identities."], "detects": ["Which owner is structurally live: V1/V2/FPD/M1/M9/V10/P7/etc.", "Whether owner body is actually loaded or only label-recognized."], "writes": ["Target → operation → result submoves inside B.", "Owner-backed contribution to Land(ⁿB)."], "next": ["Every active owner executes locally, is cleared, held, or marked PARTIAL."], "gap": ["schema-light register bridge normalizes owner submoves as ⁿBᵢ[OP] with Δξ/ΔΩ/Δσ/Δμ/Δκ where live."]}, {"id": "reread", "n": "5", "title": "Land(ⁿB) → R(H,Δ)", "color": "red", "kind": "retained compact baseline stage", "receives": ["Current burden result, held set H, burden-state delta Δ."], "detects": ["Whether another input-anchored burden remains.", "Whether same-burden facets are being mistaken for new burdens.", "STOP/HOLD/RECURSE/PARTIAL decision."], "writes": ["R(H,Δ) reread and terminal/next-burden decision."], "next": ["If recurse, return to diagnostic/routing re-entry; if closure, final restorative response."], "gap": ["schema-light register bridge distinguishes ΔⁿB from ⁿ⁺¹B and adds Δκ/collapse-radius reread."]}];
const TARGET_STAGES = [{"id": "t-input", "n": "1", "title": "Input / Surface Discourse", "color": "blue", "kind": "current bridge stage", "receives": ["D₀: surface claim, objection, slogan, proof packet, source request, or case file."], "detects": ["Source/message/encoding/channel/noise/redundancy signals.", "♥ register: grief, identity, performance, truth-seeking, mixed, or unclear.", "Whether the discourse is a proposition or a carrier of deeper noetic grammar."], "writes": ["D₀ as explicit surface-discourse object.", "Preserved ♥ register for burden sequencing, held material, tone, and release posture.", "Initial features for Ψᴺ reconstruction."], "next": ["Enough signal for diagnostic typing or explicitly marked underdetermined."], "failure": ["Topic-label dispatch before noetic read."]}, {"id": "t-psi", "n": "2", "title": "Encoded Noetic Signal-State", "color": "green", "kind": "current bridge stage", "receives": ["D₀ plus current noetic read features."], "detects": ["N,m,τ,σ plus ♥/ξ/Ω/μ/κ/H where structurally live."], "writes": ["Ψᴺ⟨N,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩."], "next": ["♥ register and structural registers may be held/underdetermined, but not silently omitted when live."], "failure": ["♥ register collapses into noise or μ and meta-noetic memetics remains decorative vocabulary."]}, {"id": "t-ir", "n": "3", "title": "Expanded DSL / IR & Gated Governance", "color": "cyan", "kind": "current bridge stage", "receives": ["Ψᴺ and triggered diagnostic passes."], "detects": ["IR field consistency, suppression rules, source-status non-equivalence, routing precedence, P7 stops, architecture target, and bounded owner eligibility."], "writes": ["IR(N,m,τ,σ,♥,ξ,Ω,μ,κ) as the current derived bridge over the non-optional DSL/IR control surface; fixture/checker evidence keeps the bridge tied to runtime controls."], "next": ["Horizontal Gate → Precedence → Owner Select → Layer B sequence with connector arrows between compact boxes; detailed Gate checks sit in a compact sub-panel under the flow, then dispatch opens, holds, or partials while preserving register-to-release posture."], "failure": ["Treating IR as optional, bypassing gate/precedence, or adding hard schema bloat before smoke/checker stability."]}, {"id": "t-owner", "n": "4", "title": "Owner / TTP Activation", "color": "violet", "kind": "current bridge stage", "receives": ["Validated IR and current ⁿB."], "detects": ["Which owner acts on ♥, ξ, Ω, σ, μ, κ, H, or τ."], "writes": ["ⁿBᵢ[OP] : target → operation → result → ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ."], "next": ["Every active owner locally changes state or is cleared/held/PARTIAL; ΔⁿB/Δκ feed target-explicit ∇·/∇× field diagnostics where closure depends on residual pressure or circularity."], "failure": ["Owner name printed without operation floor."]}, {"id": "t-burden", "n": "5", "title": "Burden Cycle / Layer B", "color": "orange", "kind": "current bridge stage", "receives": ["ⁿB and all material submoves {ⁿB₁...ⁿBₖ}."], "detects": ["Whether Σ submove deltas land the burden."], "writes": ["Land(ⁿB), ΔⁿB/Δκ, and target-explicit ∇·/∇× field-state diagnostics; register-delta notation is fixture-backed where it changes controls."], "next": ["Read ∇·/∇× over explicit live targets where control-relevant, then reread H, Δ♥ where live, and Δκ before closure or next burden."], "failure": ["One paragraph treated as landing without state delta."]}, {"id": "t-decision", "n": "6", "title": "Reread / Collapse Decision", "color": "red", "kind": "current bridge stage", "receives": ["H, Δ♥, ΔⁿB, Δκ, target-explicit ∇·/∇× field diagnostics, changed Ψᴺ′."], "detects": ["What collapsed, what mutated, what remains held, what residual divergence/curl pressure remains, what licenses ⁿ⁺¹B."], "writes": ["R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) names the fixture-backed reread grammar after target-explicit ∇·/∇× diagnostics."], "next": ["Recurse only for distinct τ/ξ/Ω/σ/κ; otherwise hold/partial/close."], "failure": ["Confusing local ΔⁿB with next-burden license."]}];
// Architecture interaction trace maps are parity-checked against docs/index/runtime-architecture.json by tools/check_docs_index_interactions.py.
const ARCHITECTURE_STAGES = [
  {"id":"t-input","n":"1","title":"D₀ / Surface Signal","color":"blue","kind":"canonical architecture stage","receives":["D₀: surface claim, objection, slogan, proof packet, source request, or case file."],"detects":["Source/message/encoding/channel/noise/redundancy signals.","♥ register: grief, identity, performance, truth-seeking, mixed, or unclear.","Whether the discourse is a proposition or a carrier of deeper noetic grammar."],"writes":["D₀ as explicit surface-discourse object.","Preserved ♥ register for burden sequencing, held material, tone, and release posture.","Initial features for Ψᴺ reconstruction."],"next":["Enough signal for diagnostic typing or explicitly marked underdetermined."],"failure":["Topic-label dispatch before noetic read."]},
  {"id":"t-psi","n":"2","title":"Ψᴺ / Noetic Signal-State","color":"cyan","kind":"canonical architecture stage","receives":["D₀ plus current noetic read features."],"detects":["Proper-functional read: F, E, R, T, and Ø.","Structural registers N,m,τ,σ,♥,ξ,Ω,μ,κ,H where live."],"writes":["Ψᴺ⟨N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩ as encoded noetic signal-state.","Live registers may be asserted, held, or marked underdetermined; they are not silently omitted when they govern release."],"next":["Only registers that affect IR, suppression, H, owner choice, Δκ, R, tone, burden sequencing, or release posture govern the next stage."],"failure":["♥/ξ/Ω/μ/κ become decorative notation rather than control-affecting registers."]},
  {"id":"t-ir","n":"3","title":"DSL / IR & Gated Governance","color":"violet","kind":"canonical architecture stage","receives":["Ψᴺ and triggered diagnostic passes."],"detects":["IR field consistency, suppression rules, source-status non-equivalence, routing precedence, P7 stops, architecture target, and bounded owner eligibility."],"writes":["Validated IR(N,m,τ,σ,♥,ξ,Ω,μ,κ) as schema-light register notation over existing IR/control surfaces.","Gate → Precedence → Owner Select → Layer B sequence with register-to-release posture preserved."],"next":["Dispatch opens, holds, or partials only after gate checks and routing precedence authorize the owner/TTP."],"failure":["Treating IR as optional, bypassing gate/precedence, or adding hard schema fields without contract migration."]},
  {"id":"t-owner","n":"4","title":"Owner/TTP + Δ / Field Diagnostics / Reread","color":"orange","kind":"canonical architecture stage","receives":["Validated IR and current ⁿB."],"detects":["Which owner acts on ♥, ξ, Ω, σ, μ, κ, H, or τ.","Whether submoves are same-burden facets or a distinct next-burden candidate."],"writes":["ⁿBᵢ[OP] : target → operation → result → ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ.","Land(ⁿB) only after owner-backed submoves change burden state; then target-explicit ∇·/∇× reads residual field pressure before reread."],"next":["Every active owner locally changes state, is cleared, held, or marked PARTIAL; target-explicit ∇·/∇× field diagnostics feed R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ), then STOP/HOLD/PARTIAL/ⁿ⁺¹B."],"failure":["Owner name printed without operation floor, or same-burden facets treated as a licensed new burden."]},
  {"id":"t-collapse","n":"5","title":"Noetic Collapse / Restoration","color":"red","kind":"canonical architecture stage","receives":["H, ΔⁿB, Δκ, and changed Ψᴺ′ after reread."],"detects":["What collapsed, what mutated, what remains held, what licenses STOP/HOLD/RECURSE/PARTIAL."],"writes":["𝒞(Ψᴺ) as constrained resolution under owner-backed operations and reread.","N_fiṭrī ∧ ʿaql ṣarīḥ only as licensed restoration, not premature synthesis."],"next":["STOP, HOLD, PARTIAL, or ⁿ⁺¹B; recurse only for distinct live τ/ξ/Ω/σ/κ."],"failure":["Restoration printed before the dependency radius, held routes, or noetic state have been reread."]}
];
// Owner/TTP operator and family maps are parity-checked against module-catalogue/frontmatter/source paths by tools/check_docs_index_interactions.py.
const OWNER_FAMILIES = [{"id": "gate", "title": "Gate & Runtime Governance", "color": "cyan", "purpose": "Turns diagnostic state into permissible dispatch and release. This is where meta-noetic memetics becomes operational through IR fields, suppression, held material, routing precedence, and reread.", "owners": ["diagnostic-ir.md", "routing-precedence.md", "recursive-state-transitions.md", "output-release.md", "diagnostic-render-contract.md", "P7-restoration-stops"], "explains": ["Why the model cannot answer from topic alone.", "Why held material is not forgotten.", "Why ⁿ⁺¹B requires R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)."], "audit": "Look for gate checks, source-status discipline, no route-chain bounded operator, and no premature closure."}, {"id": "diagnostics", "title": "Diagnostic Owners", "color": "green", "purpose": "Read the noetic state before response. They identify N, m, reason-role, source-status, discourse orientation, and triggered ♥/ξ/Ω/μ/κ registers.", "owners": ["V1-diagnostic", "M5-deformation-triage", "reason-disambiguation", "foreign-premise-detection", "noetic-reading-checklist"], "explains": ["What is actually live?", "Is the burden epistemic, ontological, source-status, register, or content-level?"], "audit": "Check whether diagnosis is input-grounded and whether thin reads are held rather than overclaimed."}, {"id": "tactics", "title": "Tactics as State Transformers", "color": "violet", "purpose": "Local owner-backed transformations inside a live burden. They operate as ⁿBᵢ[OP] submoves, not as route-list labels.", "owners": ["M1", "M1-P", "M7", "M8", "M9", "R1", "R3", "E1-E4", "F1-F3"], "explains": ["Which rule is being corrected?", "What state delta does the submove produce?"], "audit": "Every active tactic must show target → operation → result → ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ where ♥ is live."}, {"id": "techniques", "title": "Techniques as Burden Tools", "color": "orange", "purpose": "Higher-level methods for reason, transmission, signs, taqlīd, modality, and necessary-knowledge ordering.", "owners": ["V2", "V8", "V9", "V10", "V11", "V12"], "explains": ["How to execute a structurally live burden without collapsing into generic advice."], "audit": "The technique should be loaded/owned and locally applied; bundle availability is not activation."}, {"id": "procedures", "title": "Procedures as Sequencing / Restoration Control", "color": "red", "purpose": "Governs larger arcs: restoration, objection mapping, reason/revelation tension, maieutic follow-through, and stop/hold/recurse discipline.", "owners": ["P1", "P2", "P3", "P4", "P5", "P6", "P7"], "explains": ["When to stop, hold, recurse, partial, or finally release restoration."], "audit": "Restorative response must wait until live burdens are landed, held, or partialed."}];
const OPERATORS = [{"id": "V1-diagnostic", "aliases": ["V1"], "family": "Diagnostic owner", "class": "technique", "label": "V1 — diagnostic technique", "plain": "Runs the opening noetic diagnostic read.", "acts_on": "D₀, N, m, discourse orientation, source-status signals", "activation": "Any substantive theological/philosophical/noetic case.", "operation": "Classifies the case before response: noetic frame, deformation, concealment, discourse orientation, claim level, and source-status pressure.", "delta": "Initial typed noetic state feeding IR.", "reread": "If V1 is skipped, the response is topic-answer cosplay rather than governed execution.", "path": "atomics/skill/references/techniques/V1-diagnostic.md", "symbols": ["D0", "Psi", "N", "m", "IR"], "concepts": ["Noetic structure", "deformation", "discourse orientation", "Layer A"], "example": "Before answering hiddenness or hadith, V1 asks what kind of burden is actually live."}, {"id": "reason-disambiguation", "aliases": ["reason-disambiguation", "reason category"], "family": "Diagnostic pass", "class": "diagnostic", "label": "Reason-disambiguation", "plain": "Determines what kind of 'reason' is being used.", "acts_on": "ξ / reason-role / criterion claims", "activation": "Any intellectual-content case where reason, proof, or evidence is operative.", "operation": "Separates sound reason from corrupted reason, pseudo-neutral tribunals, and inherited criteria.", "delta": "Δξ: the governing epistemic rule is clarified.", "reread": "Can trigger V2, FPD, M1, R1, or HOLD depending on the criterion.", "path": "atomics/skill/references/diagnostics/reason-disambiguation.md", "symbols": ["xi", "IR", "tau"], "concepts": ["ξ epistemic grammar", "tribunal / criterion", "IR gate"], "example": "“I follow reason, not religion” may be sound reason or a pseudo-neutral criterion."}, {"id": "FPD", "aliases": ["FPD", "foreign-premise-detection", "foreign-premise"], "family": "Diagnostic pass", "class": "diagnostic", "label": "FPD — foreign premise detection", "plain": "Exposes an imported criterion or tribunal.", "acts_on": "τ, ξ, σ, μ", "activation": "A standard is being imported as neutral reason, moral authority, source-rule, or proof-method.", "operation": "Shows that the criterion is not neutral, but a live imported tribunal requiring justification.", "delta": "Δξ / Δσ / Δμ: the foreign criterion loses default authority.", "reread": "Downstream claims must be reread once the imported tribunal is no longer governing.", "path": "atomics/skill/references/diagnostics/foreign-premise-detection.md", "symbols": ["tau", "xi", "sigma", "mu", "IR"], "concepts": ["τ tribunal", "ξ epistemic grammar", "μ memetic vector", "source-status σ"], "example": "“Only lab evidence counts” imports a narrow evidential tribunal."}, {"id": "E1-broadening-evidence", "aliases": ["E1"], "family": "Tactic", "class": "tactic", "label": "E1 — broadening evidential scope", "plain": "Broadens what is allowed to count as evidence.", "acts_on": "ξ, evidential scope, testimony/signs", "activation": "When an interlocutor narrows evidence to one artificial kind.", "operation": "Reopens the evidential field so signs, testimony, fitrah, and inference are not excluded by stipulation.", "delta": "Δξ: evidence criterion widened; possible Δκ if dependent objections relied on narrowing.", "reread": "May license E3/V5 or source-status work after the narrow criterion no longer governs.", "path": "atomics/skill/references/tactics/E1-broadening-evidence.md", "symbols": ["xi", "IR", "submoves", "deltaK"], "concepts": ["ξ epistemic grammar", "evidence scope"], "example": "A demand for only laboratory evidence is widened before signs/testimony are discussed."}, {"id": "E2-inferential-criterion", "aliases": ["E2"], "family": "Tactic", "class": "tactic", "label": "E2 — pressing the inferential criterion", "plain": "Presses whether the opponent’s own inference standard is justified.", "acts_on": "ξ, τ, inferential standard", "activation": "When a proof or evidence demand relies on an unstated inferential rule.", "operation": "Asks what justifies the criterion and whether the speaker applies it symmetrically.", "delta": "Δξ/ΔⁿB: inferential rule becomes explicit and accountable.", "reread": "May route to M1/M1-P if the rule self-undermines.", "path": "atomics/skill/references/tactics/E2-inferential-criterion.md", "symbols": ["xi", "tau", "submoves"], "concepts": ["ξ epistemic grammar", "τ criterion"], "example": "A historical skeptic must justify why their standard is the correct one."}, {"id": "E3-cumulative-case", "aliases": ["E3"], "family": "Tactic", "class": "tactic", "label": "E3 — cumulative case construction", "plain": "Builds convergent evidence only after upstream criteria permit it.", "acts_on": "ξ, evidence set, H", "activation": "When reason category is open and evidence can be released.", "operation": "Coordinates multiple signs/evidences without turning into an argument dump.", "delta": "ΔⁿB: evidence burden gains convergent support.", "reread": "Requires reread if one evidence changes the dependency structure.", "path": "atomics/skill/references/tactics/E3-cumulative-case.md", "symbols": ["xi", "H", "submoves"], "concepts": ["evidence", "Layer B"], "example": "After empirical-only restriction is loosened, multiple signs may be presented together."}, {"id": "E4-cross-cultural-check", "aliases": ["E4"], "family": "Tactic", "class": "tactic", "label": "E4 — cross-cultural check", "plain": "Uses widespread human recognition as diagnostic evidence, not mere popularity.", "acts_on": "N, ξ, fitrah, testimony", "activation": "When pluralism/universality or cross-cultural recognition is live.", "operation": "Tests whether recurring recognition reflects fitri deliverability or cultural accident.", "delta": "Δξ/ΔN: cross-cultural signal is properly classified.", "reread": "Can support fitrah/reminder without becoming a popularity fallacy.", "path": "atomics/skill/references/tactics/E4-cross-cultural-check.md", "symbols": ["N", "xi", "Psi"], "concepts": ["fitrah", "testimony"], "example": "A universal religious impulse is read as signal requiring classification."}, {"id": "F1-supra-vs-antirational", "aliases": ["F1"], "family": "Tactic", "class": "tactic", "label": "F1 — supra-rational vs anti-rational", "plain": "Distinguishes what exceeds discursive reason from what contradicts sound reason.", "acts_on": "ξ, reason-role", "activation": "When revelation or doctrine is accused of irrationality.", "operation": "Separates limits of discursive access from actual contradiction.", "delta": "Δξ: reason/revelation relation clarified.", "reread": "May route to P3 if reason-revelation tension is live.", "path": "atomics/skill/references/tactics/F1-supra-vs-antirational.md", "symbols": ["xi", "tau", "submoves"], "concepts": ["reason-role", "revelation"], "example": "A mystery is not automatically a contradiction."}, {"id": "F2-volitional-dimensions", "aliases": ["F2"], "family": "Tactic", "class": "tactic", "label": "F2 — volitional dimensions", "plain": "Foregrounds will, desire, vested interest, and non-intellectual resistance.", "acts_on": "m, μ, discourse orientation", "activation": "When resistance is not primarily evidential but volitional or identity-bound.", "operation": "Shifts response from proof-stacking to will/register-aware engagement.", "delta": "Δm/Δμ: deformation layer is named and content may be held.", "reread": "Often changes κ because downstream objections may be symptoms of the same resistance.", "path": "atomics/skill/references/tactics/F2-volitional-dimensions.md", "symbols": ["m", "mu", "H", "submoves"], "concepts": ["m deformation/mode", "μ memetic vector"], "example": "A repeated objection after answers may indicate vested resistance rather than new doubt."}, {"id": "F3-practice-epistemic-access", "aliases": ["F3"], "family": "Tactic", "class": "tactic", "label": "F3 — practice as epistemic access", "plain": "Shows that some understanding is accessed through practice, not detached spectatorship.", "acts_on": "ξ, practice, epistemic environment", "activation": "When the person demands access while refusing the conditions of access.", "operation": "Identifies practice as part of the epistemic environment for certain recognition.", "delta": "Δξ: access condition corrected.", "reread": "Can route toward P1/P4 rather than abstract proof.", "path": "atomics/skill/references/tactics/F3-practice-epistemic-access.md", "symbols": ["xi", "N", "submoves"], "concepts": ["ξ epistemic grammar", "epistemic environment"], "example": "Some recognitions require worshipful or moral posture, not detached trial."}, {"id": "M1-self-refutation", "aliases": ["M1"], "family": "Tactic", "class": "tactic", "label": "M1 — self-refutation", "plain": "Tests whether a criterion undermines itself.", "acts_on": "τ / ξ", "activation": "A criterion or claim cannot meet its own standard.", "operation": "Applies the standard back to itself and records the resulting collapse or limitation.", "delta": "Δξ / ΔⁿB: criterion no longer governs as stated.", "reread": "Often lands part of an imported tribunal burden with V2/FPD.", "path": "atomics/skill/references/tactics/M1-self-refutation.md", "symbols": ["xi", "tau", "submoves", "deltaB"], "concepts": ["ξ epistemic grammar", "τ tribunal"], "example": "“Only empirically verifiable claims are meaningful” is not itself empirically verified."}, {"id": "M1P-performative-self-refutation", "aliases": ["M1-P", "M1P"], "family": "Tactic", "class": "tactic", "label": "M1-P — performative self-refutation", "plain": "Shows when a position contradicts its own act of asserting or judging.", "acts_on": "τ, ξ, μ", "activation": "The interlocutor’s performance depends on what the claim denies.", "operation": "Compares the spoken criterion with the act/practice needed to make the claim.", "delta": "Δξ / Δμ: the practical veto loses authority.", "reread": "Useful when the discourse posture is a self-authorizing court.", "path": "atomics/skill/references/tactics/M1P-performative-self-refutation.md", "symbols": ["xi", "mu", "tau", "submoves"], "concepts": ["μ memetic vector", "ξ epistemic grammar"], "example": "Using moral condemnation while denying any ground for moral judgment."}, {"id": "M2-prior-probability", "aliases": ["M2"], "family": "Tactic", "class": "tactic", "label": "M2 — prior probability probe", "plain": "Exposes hidden priors that make evidence seem weaker than it is.", "acts_on": "ξ, prior probabilities, evidential frame", "activation": "When evidence is dismissed because a prior framework has already made it implausible.", "operation": "Surfaces and tests the prior rather than endlessly adding evidence.", "delta": "Δξ/Δκ: prior-dependent objections may lose force.", "reread": "Can route to E3 after priors are corrected.", "path": "atomics/skill/references/tactics/M2-prior-probability.md", "symbols": ["xi", "kappa", "submoves"], "concepts": ["ξ epistemic grammar", "κ collapse radius"], "example": "Miracle reports are rejected before evidence because naturalism sets the prior near zero."}, {"id": "M3-orphaned-intuition", "aliases": ["M3"], "family": "Tactic", "class": "tactic", "label": "M3 — orphaned intuition", "plain": "Finds moral or rational intuitions severed from their own grounding source.", "acts_on": "ξ, μ, moral/rational residue", "activation": "When a person uses an intuition their worldview cannot house.", "operation": "Names the intuition and asks what makes it authoritative in that system.", "delta": "Δξ/Δμ: borrowed moral/rational capital becomes visible.", "reread": "Should not replace M1/FPD when a tribunal is live.", "path": "atomics/skill/references/tactics/M3-orphaned-intuition.md", "symbols": ["xi", "mu", "submoves"], "concepts": ["orphaned intuition", "μ memetic vector"], "example": "Condemning divine action with moral realism while denying moral grounding."}, {"id": "M4-grief-register", "aliases": ["M4"], "family": "Tactic", "class": "tactic", "label": "M4 — grief register", "plain": "Detects grief or injury operating as epistemic fog.", "acts_on": "m, discourse orientation, H", "activation": "When pain, betrayal, or trauma is the live register.", "operation": "Holds premature argument and responds to the register appropriately.", "delta": "Δm/H: content may be held while grief is acknowledged.", "reread": "Often blocks direct doctrinal release.", "path": "atomics/skill/references/tactics/M4-grief-register.md", "symbols": ["m", "H", "submoves"], "concepts": ["grief/register", "held set H"], "example": "A problem-of-evil question may be a wound before it is an argument."}, {"id": "M5-deformation-triage", "aliases": ["M5"], "family": "Tactic", "class": "tactic", "label": "M5 — deformation triage", "plain": "Sorts what kind of deformation is operative.", "acts_on": "m / deformation signals", "activation": "Inside V1 or when deformation sorting is live.", "operation": "Distinguishes shubha, hawā, gharaḍ, ʿāda, taqlīd, inherited beliefs, or compound layers.", "delta": "Δm / case-state: identifies what must be addressed first.", "reread": "May suppress doctrinal content until upstream deformation clears.", "path": "atomics/skill/references/tactics/M5-deformation-triage.md", "symbols": ["m", "Psi", "IR"], "concepts": ["m deformation/mode", "noetic structure"], "example": "A polished objection may still be identity-performance or grief-register."}, {"id": "M6-excluded-middle", "aliases": ["M6"], "family": "Tactic", "class": "tactic", "label": "M6 — excluded middle", "plain": "Forces a suppressed binary when equivocation is being preserved.", "acts_on": "τ, σ, semantic status", "activation": "When the response depends on refusing an unstable middle position.", "operation": "Clarifies the options so the live contradiction cannot be hidden.", "delta": "Δσ/ΔⁿB: equivocation reduced.", "reread": "May land a definition or criterion burden.", "path": "atomics/skill/references/tactics/M6-excluded-middle.md", "symbols": ["tau", "sigma", "submoves"], "concepts": ["semantic status", "τ criterion"], "example": "A claim alternates between 'no evidence' and 'not the kind I accept'."}, {"id": "M7-definition-anchor", "aliases": ["M7"], "family": "Tactic", "class": "tactic", "label": "M7 — definition anchor", "plain": "Stops term drift before content is released.", "acts_on": "σ / semantic-status", "activation": "Public/private mismatch, silent redefinition, equivocation, universals/particulars confusion.", "operation": "Stabilizes the term and identifies which definition is doing the work.", "delta": "Δσ: semantic-status corrected.", "reread": "Can HOLD doctrinal content until the term is anchored.", "path": "atomics/skill/references/tactics/M7-definition-anchor.md", "symbols": ["sigma", "IR", "H"], "concepts": ["source-status σ", "semantic status"], "example": "“Evidence” may be narrowed to one kind of evidence without being admitted."}, {"id": "M8-reductio", "aliases": ["M8"], "family": "Tactic", "class": "tactic", "label": "M8 — reductio", "plain": "Traces consequences to expose instability.", "acts_on": "τ, ξ, Ω, κ", "activation": "A position’s implications reveal contradiction or destructive consequence.", "operation": "Carries the claim through its own logic until the disorder is visible.", "delta": "ΔⁿB / Δκ: burden changes and dependent claims may collapse.", "reread": "Reread required because the collapse radius may shift.", "path": "atomics/skill/references/tactics/M8-reductio.md", "symbols": ["tau", "xi", "omega", "kappa", "deltaK", "submoves"], "concepts": ["κ collapse radius", "τ burden-function", "Ω ontology"], "example": "A criterion that defeats testimony may also defeat most historical knowledge."}, {"id": "M9-predication-mode", "aliases": ["M9"], "family": "Tactic", "class": "tactic", "label": "M9 — predication-mode analysis", "plain": "Repairs creaturely/divine predication mistakes.", "acts_on": "Ω / predication rules", "activation": "Creaturely predicate, composition, modality, person-like, embodied, divided, or dependency grammar is imposed on Allah.", "operation": "Separates reception-grounded meaning from creaturely modality and repairs the predicate source.", "delta": "ΔΩ: ontological grammar corrected.", "reread": "If live and skipped, the burden remains PARTIAL.", "path": "atomics/skill/references/tactics/M9-predication-mode.md", "symbols": ["omega", "submoves", "deltaB"], "concepts": ["Ω ontological grammar", "predication"], "example": "“Attributes imply composition” is not answered by generic theology before Ω is repaired."}, {"id": "R1-internalist-criterion", "aliases": ["R1"], "family": "Tactic", "class": "tactic", "label": "R1 — internalist criterion challenge", "plain": "Challenges excessive access requirements for warrant.", "acts_on": "ξ / warrant rule", "activation": "Knowledge is demanded only if the subject can inspect/prove the warrant process reflectively.", "operation": "Shows that warrant can obtain through reliable/proper-function processes without full reflective access.", "delta": "Δξ: internalist over-demand loosened.", "reread": "Can restore prima facie/proper-function warrant and collapse proof-bloat.", "path": "atomics/skill/references/tactics/R1-internalist-criterion.md", "symbols": ["xi", "submoves", "deltaB"], "concepts": ["ξ epistemic grammar", "proper function"], "example": "The demand “prove every basic commitment first” creates regress pressure."}, {"id": "R2-the-reminder", "aliases": ["R2"], "family": "Tactic", "class": "tactic", "label": "R2 — the reminder", "plain": "Elicits recognition already latent in the fitrah.", "acts_on": "N, ξ, fitrah", "activation": "When the case calls for reminder rather than proof construction.", "operation": "Draws attention back to a basic recognition that is being obscured.", "delta": "ΔN/Δξ: suppressed recognition can become live.", "reread": "Often coordinates with P1/P4.", "path": "atomics/skill/references/tactics/R2-the-reminder.md", "symbols": ["N", "xi", "final"], "concepts": ["fitrah", "reminder"], "example": "The response reminds rather than invents a new foundation."}, {"id": "R3-warranted-basic-belief", "aliases": ["R3"], "family": "Tactic", "class": "tactic", "label": "R3 — warranted basic belief", "plain": "Situates basic belief under proper function.", "acts_on": "ξ, fiṭrah, epistemic environment", "activation": "Basic-belief, proper-function, or Reformed/fideist warrant framing is live.", "operation": "Shows how a belief may be warranted as basic when faculties function properly in fitting conditions.", "delta": "Δξ: basic-belief status clarified.", "reread": "May reduce demand for inferential proof where basic warrant is live.", "path": "atomics/skill/references/tactics/R3-warranted-basic-belief.md", "symbols": ["xi", "N", "final"], "concepts": ["ξ epistemic grammar", "fiṭrah/proper function"], "example": "Not all warranted belief is inferred from prior propositions."}, {"id": "doubt-vs-skepticism", "aliases": ["doubt-vs-skepticism"], "family": "Tactic", "class": "tactic", "label": "Doubt vs skepticism", "plain": "Separates ordinary doubt from skepticism that installs evidence as default requirement.", "acts_on": "ξ, m, τ", "activation": "When a demand for evidence may actually be skepticism-as-criterion.", "operation": "Clarifies whether the live burden is a defeater, a doubt, or a criterion demand.", "delta": "Δξ/Δm: evidence-default pressure classified.", "reread": "May route to R1/E1/V2.", "path": "atomics/skill/references/tactics/doubt-vs-skepticism.md", "symbols": ["xi", "m", "tau"], "concepts": ["doubt", "skepticism"], "example": "Not every unargued belief is guilty until proven."}, {"id": "husn-al-nazar-arguments", "aliases": ["husn-al-nazar", "Ḥusn al-Naẓar"], "family": "Tactic", "class": "tactic", "label": "Ḥusn al-Naẓar arguments", "plain": "Uses inferential arguments for impaired fitrah cases.", "acts_on": "N, ξ, impaired fitrah", "activation": "When fitri recognition is impaired and inferential assistance is appropriate.", "operation": "Deploys inferential supports without making inference the foundation itself.", "delta": "Δξ/ΔN: impaired recognition supported through argument.", "reread": "Held if upstream criterion or register blocks release.", "path": "atomics/skill/references/tactics/husn-al-nazar-arguments.md", "symbols": ["N", "xi", "submoves"], "concepts": ["fitrah", "inferential support"], "example": "An impaired fitrah may need inferential reminders."}, {"id": "inductive-fitri-method", "aliases": ["inductive-fitri-method"], "family": "Tactic", "class": "tactic", "label": "Inductive fitri method", "plain": "Identifies fitri deliverables through convergent induction.", "acts_on": "N, ξ, fitri deliverables", "activation": "When a claim concerns what is naturally recognized across cognition.", "operation": "Uses inductive convergence to classify fitri deliverables.", "delta": "Δξ/ΔN: fitri status clarified.", "reread": "Supports E4/R2/P1 where appropriate.", "path": "atomics/skill/references/tactics/inductive-fitri-method.md", "symbols": ["N", "xi"], "concepts": ["fitrah", "induction"], "example": "Recurring basic recognition is analyzed as fitri signal."}, {"id": "symmetric-taqlid-check", "aliases": ["symmetric-taqlid-check", "V7"], "family": "Tactic", "class": "tactic", "label": "Symmetric taqlīd check", "plain": "Applies the anti-taqlid standard symmetrically.", "acts_on": "ξ, μ, inherited criterion", "activation": "When skepticism is inherited while presenting itself as independent reason.", "operation": "Shows that inherited secular skepticism can also be taqlid.", "delta": "Δξ/Δμ: inherited default loses false neutrality.", "reread": "Can coordinate with V7 and V2.", "path": "atomics/skill/references/tactics/symmetric-taqlid-check.md", "symbols": ["xi", "mu", "submoves"], "concepts": ["taqlid", "inherited criterion"], "example": "The demand that religion not be inherited also applies to inherited skepticism."}, {"id": "V2-reconstituting-reason", "aliases": ["V2"], "family": "Technique", "class": "technique", "label": "V2 — reconstituting reason", "plain": "Restores reason to its proper role after false neutrality is named.", "acts_on": "ξ / reason-as-tribunal", "activation": "Reason-category 3/4, pseudo-neutrality, inherited criterion, or foreign tribunal.", "operation": "Names the framework, shows it is not self-grounding, and loosens its authority before evidence is released.", "delta": "Δξ: reason is no longer equated with the imported criterion.", "reread": "May license evidence/sign/testimony response after the upstream criterion burden lands.", "path": "atomics/skill/references/techniques/V2-reconstituting-reason.md", "symbols": ["xi", "IR", "submoves"], "concepts": ["ξ epistemic grammar", "reason-role", "tribunal"], "example": "A scientistic standard is treated as one criterion, not reason itself."}, {"id": "V3-regress-dissolution", "aliases": ["V3"], "family": "Technique", "class": "technique", "label": "V3 — regress dissolution", "plain": "Dissolves infinite regress traps.", "acts_on": "ξ, causal/inferential series", "activation": "When a causal or epistemic series is made impossible by regress demand.", "operation": "Classifies the regress and stops the demand from governing improperly.", "delta": "Δξ/ΔⁿB: regress demand constrained.", "reread": "May connect to necessary foundation or first cause burdens.", "path": "atomics/skill/references/techniques/V3-regress-dissolution.md", "symbols": ["xi", "tau", "submoves"], "concepts": ["regress", "foundation"], "example": "A demand for proof of every proof is stopped as regress."}, {"id": "V4-contamination-identification", "aliases": ["V4"], "family": "Technique", "class": "technique", "label": "V4 — contamination identification", "plain": "Identifies contamination in the reasoning process.", "acts_on": "m, ξ, epistemic environment", "activation": "When a thought process is formally active but polluted by imported assumptions or deformation.", "operation": "Names the contaminant and blocks premature content release.", "delta": "Δm/Δξ: contamination made explicit.", "reread": "Routes to V2/M5/FPD as needed.", "path": "atomics/skill/references/techniques/V4-contamination-identification.md", "symbols": ["m", "xi", "IR"], "concepts": ["deformation", "reason contamination"], "example": "An objection may be polished but built from a contaminated criterion."}, {"id": "V5-directing-attention-signs", "aliases": ["V5"], "family": "Technique", "class": "technique", "label": "V5 — directing attention to signs", "plain": "Directs attention to signs once the gate permits evidence release.", "acts_on": "N, ξ, signs", "activation": "When sound reason is open and signs can be presented.", "operation": "Reorients attention to signs rather than arguing from an imported tribunal.", "delta": "ΔN/Δξ: attention is restored toward evidence/signs.", "reread": "Blocked if upstream criterion or register is unresolved.", "path": "atomics/skill/references/techniques/V5-directing-attention-signs.md", "symbols": ["N", "xi", "submoves"], "concepts": ["signs", "attention"], "example": "After false evidential narrowing clears, signs can be shown."}, {"id": "V6-convergence", "aliases": ["V6"], "family": "Technique", "class": "technique", "label": "V6 — convergence technique", "plain": "Shows coherence/convergence of sound reason, fitrah, and revelation.", "acts_on": "N, ξ, evidence/revelation relation", "activation": "When multiple lines need to be read together without contradiction.", "operation": "Coordinates sources of recognition into convergent order.", "delta": "Δξ/ΔN: source order clarified.", "reread": "May support final restoration.", "path": "atomics/skill/references/techniques/V6-convergence.md", "symbols": ["N", "xi", "sigma"], "concepts": ["convergence", "source-order"], "example": "The point is not isolated proof but ordered convergence."}, {"id": "V7-taqlid-check", "aliases": ["V7"], "family": "Technique", "class": "technique", "label": "V7 — taqlīd check", "plain": "Identifies unexamined imitation.", "acts_on": "ξ, μ, inherited belief", "activation": "When a position is inherited while presenting itself as investigated.", "operation": "Tests whether the speaker is merely repeating their environment.", "delta": "Δξ/Δμ: inherited status is revealed.", "reread": "Pairs with symmetric-taqlid-check.", "path": "atomics/skill/references/techniques/V7-taqlid-check.md", "symbols": ["xi", "mu", "submoves"], "concepts": ["taqlid", "inherited belief"], "example": "Assumed-by-default skepticism may be taqlid."}, {"id": "V8-bila-kayf-anchor", "aliases": ["V8"], "family": "Technique", "class": "technique", "label": "V8 — bilā kayf anchor", "plain": "Holds meaning while refusing creaturely modality.", "acts_on": "Ω, modality, attributes", "activation": "When divine attributes are pressured through 'how' demands.", "operation": "Anchors affirmation without modality transfer.", "delta": "ΔΩ: modality demand constrained.", "reread": "Often pairs with M9/V9.", "path": "atomics/skill/references/techniques/V8-bila-kayf-anchor.md", "symbols": ["omega", "submoves"], "concepts": ["Ω ontological grammar", "modality"], "example": "Attribute language is affirmed without creaturely 'how'."}, {"id": "V9-necessary-knowledge-priority", "aliases": ["V9"], "family": "Technique", "class": "technique", "label": "V9 — necessary knowledge priority", "plain": "Gives foundational/necessary knowledge priority over discursive usurpation.", "acts_on": "ξ, Ω, necessary knowledge", "activation": "When speculative reasoning tries to overturn more basic recognition.", "operation": "Restores order between necessary/basic knowledge and discursive inference.", "delta": "Δξ/ΔΩ: priority order repaired.", "reread": "Often pairs with M9/V8.", "path": "atomics/skill/references/techniques/V9-necessary-knowledge-priority.md", "symbols": ["xi", "omega", "final"], "concepts": ["necessary knowledge", "fitrah"], "example": "A speculative composition argument cannot overthrow clearer foundational knowledge."}, {"id": "V10-transmission-content-vetting", "aliases": ["V10"], "family": "Technique", "class": "technique", "label": "V10 — transmission/content vetting", "plain": "Handles source transmission before doctrinal content.", "acts_on": "σ, ξ, testimony posture", "activation": "Hadith, revelation transmission, canon, textual variants, report reliability, testimony-standard cases.", "operation": "Separates source-status/transmission burden from downstream doctrinal content.", "delta": "Δσ / Δξ: source-status and testimony grammar reclassified.", "reread": "Downstream content remains held until the source-status burden lands.", "path": "atomics/skill/references/techniques/V10-transmission-content-vetting.md", "symbols": ["sigma", "xi", "H", "submoves"], "concepts": ["σ source-status", "ξ testimony/warrant"], "example": "“Hadith are late” must be handled at the transmission layer before broader doctrine."}, {"id": "V11-taqlid-transition", "aliases": ["V11"], "family": "Technique", "class": "technique", "label": "V11 — taqlīd transition", "plain": "Moves from imitation toward investigation/taḥqīq.", "acts_on": "ξ, μ, authority posture", "activation": "When taqlid is recognized and a transition is needed.", "operation": "Guides the shift from inherited repetition to examined commitment.", "delta": "Δξ/Δμ: authority posture changes.", "reread": "Can pair with V7/symmetric-taqlid-check.", "path": "atomics/skill/references/techniques/V11-taqlid-transition.md", "symbols": ["xi", "mu", "submoves"], "concepts": ["taqlid", "authority"], "example": "A person realizes they inherited skepticism and needs a path to inquiry."}, {"id": "V12-tamanuc-exhaustion", "aliases": ["V12"], "family": "Technique", "class": "technique", "label": "V12 — burhān al-tamānuʿ", "plain": "Exhausts independent-divinity plurality.", "acts_on": "Ω, divine plurality, sovereignty", "activation": "When multiple independent lords/divine wills are structurally live.", "operation": "Runs the impossibility of mutually independent absolute wills.", "delta": "ΔΩ/ΔⁿB: divine plurality burden constrained.", "reread": "Specific to divine plurality/independent lordship pressures.", "path": "atomics/skill/references/techniques/V12-tamanuc-exhaustion.md", "symbols": ["omega", "submoves"], "concepts": ["Ω ontological grammar", "divine plurality"], "example": "Two independent absolute gods cannot both govern absolutely."}, {"id": "heuristics", "aliases": ["heuristics"], "family": "Technique", "class": "technique", "label": "Discursive heuristics", "plain": "Governs analyst discipline and use of the framework.", "acts_on": "N, m, τ, σ, release posture", "activation": "When the practitioner needs discipline for how to use the framework.", "operation": "Prevents over-selection, rhetorical overreach, and misuse of categories.", "delta": "governance delta: safer operator selection.", "reread": "Supports all owner execution but is not a topic answer.", "path": "atomics/skill/references/techniques/heuristics.md", "symbols": ["IR", "H"], "concepts": ["analyst discipline", "anti-patterns"], "example": "The framework is used to restore, not to perform superiority."}, {"id": "P1-fitrah-restoration", "aliases": ["P1"], "family": "Procedure", "class": "procedure", "label": "P1 — fiṭrah restoration", "plain": "Governs the restorative arc.", "acts_on": "N, ξ, m", "activation": "Restoration, warning, invitation, or proper-function reorientation is doing actual work.", "operation": "Reorders cognition toward fiṭrah and sound reason after burdens are landed/held/partialed.", "delta": "Toward N_fiṭrī ∧ ʿaql ṣarīḥ.", "reread": "Final restoration cannot be the first place live source architecture appears.", "path": "atomics/skill/references/procedures/P1-fitrah-restoration.md", "symbols": ["N", "xi", "final", "C"], "concepts": ["fiṭrah", "restorative release"], "example": "Restoration follows governed burden traversal, not argument stacking."}, {"id": "P2-objection-mapping", "aliases": ["P2"], "family": "Procedure", "class": "procedure", "label": "P2 — objection mapping", "plain": "Maps objection structure before selecting response path.", "acts_on": "D₀, τ, H", "activation": "When a case contains multiple claims, premises, or burdens.", "operation": "Separates surface claims, hidden premises, held routes, and live burdens.", "delta": "ΔⁿB setup / H organization.", "reread": "Prevents multi-claim prompts from collapsing into one paragraph.", "path": "atomics/skill/references/procedures/P2-objection-mapping.md", "symbols": ["D0", "tau", "H", "IR"], "concepts": ["objection mapping", "held set"], "example": "A compound source request is split into live/held burden order."}, {"id": "P3-reason-revelation-tension", "aliases": ["P3"], "family": "Procedure", "class": "procedure", "label": "P3 — reason/revelation tension", "plain": "Resolves claimed conflict between reason and revelation.", "acts_on": "ξ, σ, proof-status", "activation": "When revelation appears to conflict with reason or proof-family status governs.", "operation": "Classifies proof status and reorders sound reason/revelation relation.", "delta": "Δξ/Δσ: conflict frame corrected.", "reread": "May require proof-method audit before doctrinal release.", "path": "atomics/skill/references/procedures/P3-reason-revelation-tension.md", "symbols": ["xi", "sigma", "IR"], "concepts": ["reason/revelation", "proof status"], "example": "A speculative proof cannot override decisive revelation without proof-status triage."}, {"id": "P4-maieutic", "aliases": ["P4"], "family": "Procedure", "class": "procedure", "label": "P4 — maieutic procedure", "plain": "Draws out latent recognition through guided questioning.", "acts_on": "N, ξ, fitrah", "activation": "When a seam of recognition is visible and direct assertion may not land.", "operation": "Uses questions to elicit what the person already recognizes.", "delta": "ΔN/Δξ: suppressed recognition becomes articulated.", "reread": "Often pairs with R2/P1.", "path": "atomics/skill/references/procedures/P4-maieutic.md", "symbols": ["N", "xi", "submoves"], "concepts": ["maieutic", "fitrah"], "example": "A person is guided to see the standard they already rely on."}, {"id": "P5-already-believing", "aliases": ["P5"], "family": "Procedure", "class": "procedure", "label": "P5 — already-believing", "plain": "Works with a person who already believes but has disorder, fatigue, or confusion.", "acts_on": "N, σ, m, H", "activation": "When the interlocutor is not outside belief but needs reordering.", "operation": "Repairs internal disorder without treating them as a generic skeptic.", "delta": "ΔN/Δσ/Δm: internal posture clarified.", "reread": "May hold public debate-style response.", "path": "atomics/skill/references/procedures/P5-already-believing.md", "symbols": ["N", "sigma", "m", "H"], "concepts": ["already believing", "pastoral hold"], "example": "A believer with authority fatigue needs source-order restoration."}, {"id": "P6-universal-aqidah-principle", "aliases": ["P6"], "family": "Procedure", "class": "procedure", "label": "P6 — universal ʿaqīdah principle", "plain": "Keeps universal creed principles distinct from local case clutter.", "acts_on": "N, Ω, σ", "activation": "When creed universals are at risk of being buried under local controversy.", "operation": "Restates the universal principle at the correct level of generality.", "delta": "ΔΩ/Δσ: principle-status clarified.", "reread": "Prevents overfitting to one sectarian or polemical frame.", "path": "atomics/skill/references/procedures/P6-universal-aqidah-principle.md", "symbols": ["N", "omega", "sigma"], "concepts": ["creed principle", "source-status"], "example": "A local dispute should not redefine universal tawḥīd principles."}, {"id": "P7-restoration-stops", "aliases": ["P7"], "family": "Procedure", "class": "procedure", "label": "P7 — restoration stops", "plain": "Controls STOP/HOLD/PARTIAL/ⁿ⁺¹B.", "acts_on": "H, ΔⁿB, Δκ", "activation": "Every post-burden decision and final release/hold/partial/recursion gate.", "operation": "Determines whether the response closes, holds material, marks partial, or licenses the next burden.", "delta": "Decision-state / Δκ governance.", "reread": "Prevents premature restoration and recursion bloat.", "path": "atomics/skill/references/procedures/P7-restoration-stops.md", "symbols": ["H", "deltaB", "deltaK", "R", "nextB"], "concepts": ["decision states", "κ collapse radius", "held set H"], "example": "R(H, Δ¹B, Δκ) can license ²B only if a distinct next burden remains."}];
const CONCEPTS = [{"id": "noetic", "name": "𝓝 noetic-structure selection space", "type": "ontology/entity", "summary": "The design-time space of possible noetic structures the framework must be able to diagnose, route, constrain, and restore before knowing which one an input will instantiate.", "definition": "𝓝 is not merely the one noetic structure inferred from the current input. It names the engineered selection space of possible noetic structures over which DAEE must be operative. At design time the selected N is unknown, so the framework has to be built to operate for each possible live noetic-structure selection. At runtime, D₀ is decoded into Ψᴺ, the live N is selected or held as underdetermined, and owner/TTP routing acts on that bounded selection.", "runtime": "This is central to the thesis: meta-noetic memetics becomes an engineering control layer because recurring claim-forms, criteria, source-status moves, registers, and stabilizers are represented as state features that let the runtime select among possible noetic structures rather than hard-coding one worldview path. 𝓝 supplies the design-space and D₀ is the current input to be decoded within that space. Selecting 𝓝 highlights only 𝓝 and D₀; N, Ψᴺ, H, and the register set belong to later runtime selection/encoding and should be selected through their own nodes.", "fields": ["Ψᴺ", "N", "m", "τ", "σ", "♥", "ξ", "Ω", "μ", "κ", "H"], "operators": ["V1", "M5", "reason-disambiguation", "FPD", "F1", "F2", "F3", "R1", "R2", "R3", "P1", "P4", "P7", "V7"], "relations": ["designs for → every possible live noetic-structure selection", "runtime selects/holds → N", "is encoded for input as → Ψᴺ", "is made operational by → meta-noetic memetic state features", "is restored through → 𝒞(Ψᴺ)"], "files": ["noetic-reading-checklist.md", "sound-reason-epistemology.md", "diagnostic-ir.md", "routing-precedence.md", "SKILL.md"], "case": "Before a user speaks, DAEE cannot know whether the live structure will be naturalist, inherited-skeptical, grief-register, testimony-demoting, ontology-confused, source-status-confused, or mixed. The architecture solves this by designing the pipeline over the possible 𝓝 selection space, then selecting or holding N at runtime.", "symbols": ["noetic", "D0"]}, {"id": "heart", "name": "♥ affective-discursive register", "type": "diagnostic field", "summary": "Grief, identity, performance, truth-seeking, mixed, or unclear register governing release posture.", "definition": "The ♥ register records how the surface discourse is affectively and socially operating before content is released. It is not reducible to m deformation, μ memetic carrier, or generic noise.", "runtime": "Constrains burden selection, suppression, tone, held material, owner choice, and final release posture.", "fields": ["♥", "m", "μ", "H", "R"], "operators": ["M4", "M5", "F2", "P7", "P2"], "relations": ["constrains → release posture", "can require → HOLD", "is distinct from → μ memetic vector", "is distinct from → m deformation"], "files": ["M4-grief-register.md", "M5-deformation-triage.md", "output-release.md", "diagnostic-render-contract.md"], "case": "A problem-of-evil question may be grief-register, identity-register, performance-register, truth-seeking, or mixed; the same proposition does not license the same release posture.", "symbols": ["heart", "H", "R"]}, {"id": "xi", "name": "ξ epistemic grammar", "type": "diagnostic field", "summary": "Warrant, fiṭrī foundationalism, inference, testimony, reliability, proper function, prima facie status, defeaters.", "definition": "The rule-set by which beliefs are treated as basic, inferred, evidential, testimonial, defeated, reliable, or properly functional.", "runtime": "Prevents warrant/testimony/proof-method cases from being misrouted as generic doctrine or ontology.", "fields": ["ξ", "τ", "σ"], "operators": ["reason-disambiguation", "V2", "FPD", "R1", "R3", "V10"], "relations": ["governs → proof demand", "routes to → R1/R3/V10", "changes as → Δξ"], "files": ["sound-reason-epistemology.md", "reason-disambiguation.md", "R1-internalist-criterion.md"], "case": "“Religious belief needs proof; secular defaults are rational” shows asymmetric ξ.", "symbols": ["xi"]}, {"id": "omega", "name": "Ω ontological grammar", "type": "diagnostic field", "summary": "Being, predication, modality, dependence, causality, universals/particulars, creator/creation boundary.", "definition": "The ontology instantiated or smuggled by discourse. It should not be overloaded with warrant structure.", "runtime": "Routes predication/category/modality/dependence burdens to M9/V8/V9/M8.", "fields": ["Ω", "τ", "σ"], "operators": ["M9", "V8", "V9", "M8"], "relations": ["governs → predication", "changes as → ΔΩ", "constrains → Layer B"], "files": ["M9-predication-mode.md", "metaphysical-architecture.md", "do-attribute-precision.md"], "case": "“Attributes imply composition” carries Ω pressure.", "symbols": ["omega"]}, {"id": "mu", "name": "μ meta-noetic memetic vector", "type": "diagnostic field", "summary": "Carrier, compression, stabilization, defense, reproduction, mutation, identity/prestige role.", "definition": "How noetic and epistemic/ontological grammars are compressed, stabilized, defended, reproduced, and mutated through discourse.", "runtime": "Operational only when it affects IR, suppression, H, owner choice, load-bearing nodes, κ, or R.", "fields": ["μ", "m", "τ", "κ"], "operators": ["FPD", "V2", "M1-P", "P7"], "relations": ["stabilizes → τ", "routes to → FPD/V2", "changes as → Δμ"], "files": ["pattern-profiling.md", "anti-patterns.md", "recursive-state-transitions.md"], "case": "“I just follow reason” can carry a prestige/identity stabilizer.", "symbols": ["mu"]}, {"id": "kappa", "name": "κ collapse radius", "type": "runtime control state", "summary": "Downstream dependency set affected if a burden lands.", "definition": "What must be reread after a load-bearing burden changes state. Not a generic TODO list.", "runtime": "Feeds R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) and helps distinguish same-burden facets from a licensed next burden.", "fields": ["κ", "Δκ", "H"], "operators": ["P7", "M8", "R-gate"], "relations": ["causes re-read of → H", "licenses/blocks → ⁿ⁺¹B", "changes as → Δκ"], "files": ["recursive-state-transitions.md", "output-release.md"], "case": "Hadith reliability affects Sunnah authority, legal practice, and creed-transmission routes.", "symbols": ["kappa", "deltaK", "R"]}, {"id": "sigma", "name": "σ source / semantic / authority status", "type": "runtime control state", "summary": "Whether a source/term/label functions as warrant, context, contrast, genealogy, comparison, or held material.", "definition": "Prevents context or prestige from becoming operative warrant without authorization.", "runtime": "Controls source-use, testimony posture, label discipline, and content hold/release.", "fields": ["σ", "H", "N"], "operators": ["V10", "M7", "P7"], "relations": ["constrains → release", "is held in → H", "routes to → V10"], "files": ["recursive-state-transitions.md", "routing-precedence.md", "V10-transmission-content-vetting.md"], "case": "A school label may be context, not warrant.", "symbols": ["sigma"]}, {"id": "tau", "name": "τ tribunal / noetic function", "type": "runtime control state", "summary": "The live burden-function: criterion, warrant, source, ontology, accountability, register, restoration, etc.", "definition": "Determines what the current burden is actually doing and whether additional content is same-burden facet or distinct next burden.", "runtime": "Selects ⁿB and constrains owner activation.", "fields": ["τ", "ⁿB"], "operators": ["FPD", "V2", "M1", "P7"], "relations": ["selects → ⁿB", "routes to → owner", "same/different governs → ⁿ⁺¹B"], "files": ["diagnostic-ir.md", "routing-precedence.md"], "case": "Imported moral tribunal differs from hiddenness demand.", "symbols": ["tau"]}, {"id": "burden", "name": "ⁿB / ⁿBᵢ burden grammar", "type": "runtime control state", "summary": "Current burden and its local owner-backed submoves.", "definition": "Strict repo convention: burden number before B; subscript after B only for submove number.", "runtime": "Keeps submoves from becoming recursion bloat.", "fields": ["ⁿB", "ⁿBᵢ", "ΔⁿB", "ⁿ⁺¹B"], "operators": ["all active OPs", "P7"], "relations": ["contains → ⁿBᵢ", "lands as → ΔⁿB", "next licensed as → ⁿ⁺¹B"], "files": ["recursive-state-transitions.md", "nomenclature-normalization.md"], "case": "¹B₁[M9] is submove 1 under burden 1.", "symbols": ["burden", "submoves"]}, {"id": "layerA", "name": "Layer A", "type": "output-governance rule", "summary": "Compact diagnostic/control surface.", "definition": "Visible compact state: read status, confidence, claim level, reason category, live burden, held material, source-status, gate decision.", "runtime": "Shows enough control state to prevent clean essay cosplay without dumping full raw IR.", "fields": ["N", "m", "τ", "σ", "H"], "operators": ["diagnostic-render-contract", "P7"], "relations": ["constrains → Layer B", "shows → held routes", "blocks → route dump"], "files": ["diagnostic-render-contract.md", "SKILL.md"], "case": "Layer A names current bounded operator, not a route itinerary.", "symbols": ["IR"]}, {"id": "layerB", "name": "Layer B", "type": "output-governance rule", "summary": "Governed operation/release surface.", "definition": "Where active owners execute target → operation → result submoves under the current burden.", "runtime": "Produces the visible bounded response and supports Land(ⁿB).", "fields": ["ⁿBᵢ", "OP", "ΔⁿB"], "operators": ["all active OPs"], "relations": ["executes → owner", "lands → ⁿB", "cannot leak → held routes"], "files": ["output-release.md", "diagnostic-render-contract.md"], "case": "¹B₂[M1] tests a self-authorizing criterion.", "symbols": ["burden", "submoves"]}, {"id": "decision", "name": "STOP / HOLD / PARTIAL / ⁿ⁺¹B", "type": "output-governance rule", "summary": "Post-reread decision states.", "definition": "The runtime decision after burden landing and state/dependency reread.", "runtime": "Controls closure, held material, incomplete traversal, or next burden.", "fields": ["R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)"], "operators": ["P7"], "relations": ["decides → release", "licenses → ⁿ⁺¹B", "prevents → premature restoration"], "files": ["P7-restoration-stops.md", "recursive-state-transitions.md"], "case": "R(H, Δ¹B, Δκ) ⊢ ²B only if a distinct next burden remains.", "symbols": ["R", "deltaB", "deltaK", "nextB", "H"]}, {"id": "collapse", "name": "𝒞 constrained noetic collapse", "type": "runtime control state", "summary": "Discursive resolution of Ψᴺ after owner-backed operations, burden landing, and reread.", "definition": "𝒞(Ψᴺ) names constrained noetic collapse: the point where a live disorder in the encoded noetic signal-state loses governance under owner-backed operations and reread. Ψᴺ is the encoded state; 𝒞 is the resolution operator/result, so it deserves its own visible card.", "runtime": "Receives the post-reread state after Land(ⁿB), ΔⁿB, and Δκ. It is only licensed when active burdens are landed, held, or partialed; otherwise the system returns to R and possibly ⁿ⁺¹B.", "fields": ["Ψᴺ", "𝒞(Ψᴺ)", "R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)", "ΔⁿB", "Δκ", "N_fiṭrī ∧ ʿaql ṣarīḥ"], "operators": ["all active OPs", "P1", "P7"], "relations": ["resolves → Ψᴺ", "requires → R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)", "terminates in → N_fiṭrī ∧ ʿaql ṣarīḥ", "blocks → premature restoration"], "files": ["recursive-state-transitions.md", "output-release.md", "diagnostic-render-contract.md"], "case": "The imported criterion loses governing role, downstream dependencies are reread, and discourse reorders toward fiṭrah/sound reason only after the relevant burden cycle is governed.", "symbols": ["C", "Psi", "R", "final", "heart", "xi", "omega", "mu"]}, {"id": "D0", "name": "D₀ surface discourse", "type": "runtime control state", "summary": "The initial utterance as a signal object, not merely a topic.", "definition": "D₀ is the visible surface discourse: claim, doubt, slogan, objection, proof-packet, source request, or case input.", "runtime": "Feeds the noetic signal-state Ψᴺ. It is decoded, not directly answered as an argument-bank cue.", "fields": ["D₀"], "operators": ["V1", "reason-disambiguation", "FPD"], "relations": ["encodes → Ψᴺ", "is typed by → IR", "can carry → μ"], "files": ["SKILL.md", "diagnostic-ir.md"], "case": "“Only empirical evidence counts” is D₀ before diagnosis.", "symbols": ["D0"]}, {"id": "Psi", "name": "Ψᴺ encoded noetic signal-state", "type": "runtime control state", "summary": "The unresolved diagnostic field carried by D₀ before operators constrain it.", "definition": "Ψᴺ contains possible N, m, τ, σ, ♥, ξ, Ω, μ, κ, and H as a live noetic signal-state.", "runtime": "Makes meta-noetic memetic analysis visible as a state object acted on by owners.", "fields": ["Ψᴺ", "N", "m", "τ", "σ", "♥", "ξ", "Ω", "μ", "κ", "H", "𝒞(Ψᴺ)"], "operators": ["V1", "FPD", "M1", "M9", "V10", "P7"], "relations": ["receives ← D₀", "formalizes into → IR", "resolves through → 𝒞(Ψᴺ)"], "files": ["preview(3).html proposal", "future recursive-state-transitions.md"], "case": "A slogan may encode ♥, ξ, Ω, μ, and κ before being typed as IR.", "symbols": ["Psi", "N", "m", "tau", "sigma", "heart", "xi", "omega", "mu", "kappa", "H"]}, {"id": "IR", "name": "IR / compact DSL state", "type": "runtime control state", "summary": "Typed control surface that authorizes or suppresses dispatch.", "definition": "IR is the compact formalization of the diagnostic read. schema-light register bridge extends the visible notation from IR(N,m,τ,σ) to IR(N,m,τ,σ,♥,ξ,Ω,μ,κ) as optional registers.", "runtime": "Controls gate checks, routing precedence, owner selection, held material, and release shape.", "fields": ["IR", "N", "m", "τ", "σ", "♥", "ξ", "Ω", "μ", "κ"], "operators": ["diagnostic-ir", "routing-precedence", "P7"], "relations": ["formalizes ← Ψᴺ", "authorizes → owner/TTP", "suppresses → premature release"], "files": ["diagnostic-ir.md", "routing-precedence.md"], "case": "IR marks source-status as held before V10 executes, and preserves ♥ when release posture is live.", "symbols": ["IR", "N", "m", "tau", "sigma", "heart", "xi", "omega", "mu", "kappa"]}, {"id": "N", "name": "N operative noetic frame", "type": "diagnostic field", "summary": "The selected noetic frame governing the burden.", "definition": "N is not a school label by itself. It is the operative frame by which the current burden is read.", "runtime": "Constrains what counts as warrant, source, held material, and restoration target.", "fields": ["N"], "operators": ["V1", "noetic-reading-checklist", "P1"], "relations": ["lives inside → Ψᴺ", "constrains → ξ/σ", "is restored toward → N_fiṭrī"], "files": ["noetic-reading-checklist.md", "SKILL.md"], "case": "N_Naturalist may be operative when empirical access is treated as neutral reason.", "symbols": ["noetic", "N"]}, {"id": "m", "name": "m deformation / memetic mode", "type": "diagnostic field", "summary": "The deformation, concealment, or recurring mode that shapes the discourse.", "definition": "m tracks deformation/concealment/memetic patterning that affects diagnosis and release.", "runtime": "Can suppress content, route to M5/F2/P7, or identify μ as stabilization/reproduction behavior.", "fields": ["m", "μ"], "operators": ["M5", "F2", "P7"], "relations": ["lives inside → Ψᴺ", "can suppress → Layer B", "can stabilize through → μ"], "files": ["seven-deformations.md", "modes-of-concealment.md", "M5-deformation-triage.md"], "case": "Identity-performance may suppress doctrinal release.", "symbols": ["m"]}, {"id": "LandR", "name": "Land(ⁿB) and R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)", "type": "runtime control state", "summary": "Burden landing and reread gate.", "definition": "Land(ⁿB) records local burden-state change. R rereads held material and dependency deltas before STOP/HOLD/PARTIAL/ⁿ⁺¹B.", "runtime": "Prevents premature closure and distinguishes ΔⁿB from next-burden license.", "fields": ["Land(ⁿB)", "ΔⁿB", "R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)", "ⁿ⁺¹B"], "operators": ["P7", "output-release", "recursive-state-transitions"], "relations": ["submoves land → ⁿB", "Δκ feeds → R", "R licenses → ⁿ⁺¹B"], "files": ["recursive-state-transitions.md", "output-release.md", "P7-restoration-stops.md"], "case": "After ¹B lands, R decides whether ²B is licensed or held.", "symbols": ["Land", "R", "deltaB", "deltaK", "H"]}];
const RELATIONS = [{"id": "rel-noetic-design", "label": "𝓝 designs the selection space", "type": "designs-for", "from": "𝓝", "to": "possible live noetic structures", "symbols": ["noetic", "Psi", "N"], "explain": "The framework is engineered before the current input is known, so it must be able to operate for every possible noetic-structure selection that could become live.", "runtime": "Meta-noetic memetics solves this as an engineering problem by representing recurring criteria, source-status moves, registers, stabilizers, and collapse radii as routable control state."}, {"id": "rel-noetic-selects-N", "label": "𝓝 licenses runtime N selection", "type": "selects", "from": "𝓝", "to": "N∈𝓝", "symbols": ["noetic", "N", "Psi"], "explain": "N is not assumed at design time. It is selected, constrained, or held as underdetermined after D₀ is decoded into Ψᴺ.", "runtime": "This prevents the pipeline from hard-coding one worldview path or treating N as a mere label."}, {"id": "rel-D-Psi", "label": "D₀ encodes Ψᴺ", "type": "encodes", "from": "D₀", "to": "Ψᴺ", "symbols": ["D0", "Psi"], "explain": "Surface discourse is treated as an encoded noetic signal-state, not merely a proposition to answer.", "runtime": "This is where Shannon-style signal/compression language becomes useful without replacing noetic theology."}, {"id": "rel-Psi-fields", "label": "Ψᴺ contains N,m,τ,σ,♥,ξ,Ω,μ,κ,H", "type": "contains", "from": "Ψᴺ", "to": "register set", "symbols": ["Psi", "N", "m", "tau", "sigma", "heart", "xi", "omega", "mu", "kappa", "H"], "explain": "The unresolved diagnostic field carries runtime-selected noetic frame, mode, burden-function, source-status, affective-discursive register, epistemic grammar, ontology, memetic carrier, collapse radius, and held material.", "runtime": "Concept selection should highlight the matching register inside the notation."}, {"id": "rel-heart-release", "label": "♥ constrains release posture", "type": "constrains", "from": "♥", "to": "burden / H / tone / release", "symbols": ["heart", "H", "R"], "explain": "The affective-discursive register is not decorative sentiment and is not reducible to μ or m. Grief, identity, performance, truth-seeking, and mixed/unclear registers can license different suppression, hold, burden, and tone decisions.", "runtime": "This is why the same proposition may require different Layer B release depending on register."}, {"id": "rel-Psi-IR", "label": "Ψᴺ formalizes into IR", "type": "formalizes", "from": "Ψᴺ", "to": "IR", "symbols": ["Psi", "IR"], "explain": "Diagnostic reconstruction converts the signal-state into compact DSL/IR control state.", "runtime": "The IR authorizes dispatch; it is not a post-hoc label."}, {"id": "rel-xi-owner", "label": "ξ routes epistemic burdens", "type": "routes to", "from": "ξ", "to": "V2 / R1 / R3 / V10", "symbols": ["xi", "IR", "submoves"], "explain": "Warrant, testimony, proper function, reliability, and defeater structure select epistemic owners.", "runtime": "This blocks routing epistemic objections as mere doctrinal content."}, {"id": "rel-omega-owner", "label": "Ω routes ontological burdens", "type": "routes to", "from": "Ω", "to": "M9 / V8 / V9 / M8", "symbols": ["omega", "IR", "submoves"], "explain": "Predication, modality, dependence, and creator/creation boundaries select ontology-sensitive owners.", "runtime": "This prevents creaturely grammar from governing divine predication unnoticed."}, {"id": "rel-mu-operational", "label": "μ becomes operational through control surfaces", "type": "constrains", "from": "μ", "to": "IR/H/owner/κ/R", "symbols": ["mu", "IR", "H", "submoves", "kappa", "R"], "explain": "Meta-noetic memetics is not decorative vocabulary. It matters only when it changes control state, hold/release, owner choice, collapse radius, or reread.", "runtime": "This is the key structural thesis of schema-light register bridge."}, {"id": "rel-IR-owner", "label": "IR authorizes owner/TTP activation", "type": "authorizes", "from": "IR", "to": "ⁿBᵢ[OP]", "symbols": ["IR", "burden", "submoves"], "explain": "Owners activate only after diagnostic reduction, gate checks, and routing precedence.", "runtime": "No owner label counts without local target → operation → result execution."}, {"id": "rel-op-delta", "label": "ⁿBᵢ[OP] produces ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ", "type": "lands as", "from": "submoves", "to": "deltas", "symbols": ["submoves", "deltaB", "deltaK"], "explain": "Each active operator should produce burden-local and dependency-relevant state change.", "runtime": "The state delta is what makes the operation auditable."}, {"id": "rel-r-next", "label": "R licenses STOP/HOLD/PARTIAL/ⁿ⁺¹B", "type": "licenses release of", "from": "R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)", "to": "decision", "symbols": ["R", "deltaB", "deltaK", "nextB"], "explain": "Reread decides whether the system closes, holds, partials, or recurses to a distinct next burden.", "runtime": "This prevents recursion bloat and premature restoration."}, {"id": "rel-collapse", "label": "R* yields 𝒞(Ψᴺ)", "type": "resolves", "from": "iterated burden cycles", "to": "𝒞(Ψᴺ)", "symbols": ["R", "C", "final"], "explain": "Across landed/held/partial burdens, the encoded noetic signal-state is constrained toward discursive resolution.", "runtime": "The terminal aim is restored fiṭrah and sound reason, not novelty or argument accumulation."}];
{{ REFERENCE_DATA }}
{{ OWNER_SOURCE_RENDERER }}
function esc(value){
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&':'&amp;',
    '<':'&lt;',
    '>':'&gt;',
    '"':'&quot;',
    "'":'&#39;'
  })[ch]);
}
function showTopTab(id, btn){
  const panel=document.getElementById(id);
  if(!panel || !panel.classList.contains('tabsec')) return false;
  document.querySelectorAll('.tabsec').forEach(sec=>{
    const active=sec.id===id;
    sec.classList.toggle('active', active);
    sec.hidden=!active;
  });
  document.querySelectorAll('.topbar .tab[data-tab]').forEach(tab=>{
    const active=(tab===btn) || tab.dataset.tab===id || tab.getAttribute('aria-controls')===id;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', active ? 'true' : 'false');
    tab.tabIndex=active ? 0 : -1;
  });
  if(window.history && window.location && window.location.hash !== '#'+id){
    history.replaceState(null, '', '#'+id);
  }
  return false;
}
function initTopTabs(){
  const tabs=[...document.querySelectorAll('.topbar .tab[data-tab]')];
  if(!tabs.length) return;
  tabs.forEach((tab,index)=>{
    const id=tab.dataset.tab;
    tab.addEventListener('click',()=>showTopTab(id,tab));
    tab.addEventListener('keydown',event=>{
      const keys=['ArrowLeft','ArrowRight','Home','End'];
      if(!keys.includes(event.key)) return;
      event.preventDefault();
      let next=index;
      if(event.key==='ArrowLeft') next=(index-1+tabs.length)%tabs.length;
      if(event.key==='ArrowRight') next=(index+1)%tabs.length;
      if(event.key==='Home') next=0;
      if(event.key==='End') next=tabs.length-1;
      tabs[next].focus();
      showTopTab(tabs[next].dataset.tab,tabs[next]);
    });
  });
  const hash=(window.location.hash||'').slice(1);
  const initial=tabs.find(tab=>tab.dataset.tab===hash) || tabs.find(tab=>tab.classList.contains('active')) || tabs[0];
  showTopTab(initial.dataset.tab, initial);
  if(hash){
    setTimeout(()=>{
      document.documentElement.scrollTop=0;
      document.body.scrollTop=0;
      if(typeof window.scrollTo === 'function') window.scrollTo(0,0);
    },0);
  }
}
function showSub(id,btn){
  document.querySelectorAll('.subpanel').forEach(x=>x.classList.remove('active'));
  document.getElementById('sub-'+id).classList.add('active');
  document.querySelectorAll('.subtab').forEach(x=>x.classList.remove('active'));
  btn.classList.add('active');
  if(id==='concepts'){
    const active=document.querySelector('#conceptList .conceptBtn.active') || document.querySelector('#conceptList .conceptBtn');
    if(active){
      const cid=active.getAttribute('data-cid') || ((active.getAttribute('onclick')||'').match(/selectConcept\('([^']+)'/)||[])[1];
      if(cid) selectConcept(cid, active);
    }
  } else if(id==='relations'){
    const active=document.querySelector('.relationList .relationBtn.active') || document.querySelector('.relationList .relationBtn');
    if(active){
      const rid=active.getAttribute('data-rid') || ((active.getAttribute('onclick')||'').match(/selectRelation\('([^']+)'/)||[])[1];
      if(rid) selectRelation(rid, active);
    }
  } else {
    clearNotation();
  }
}
function box(title,arr){return `<div class="detailBox"><h4>${esc(title)}</h4><ul>${arr.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`;}
function renderPipeline(data, gridId, detailId){const grid=document.getElementById(gridId);grid.innerHTML=data.map((s,i)=>`<div class="stageCard ${i===0?'active':''}" style="--c:${COLORS[s.color]}" onclick="selectStage('${gridId}','${detailId}','${s.id}',this)"><h3><span class="stageNum">${esc(s.n)}</span>${esc(s.title)}</h3><p><strong>${esc(s.kind)}</strong></p><p>${esc(s.writes[0]||s.summary||'')}</p></div>`).join('');selectStage(gridId,detailId,data[0].id,grid.querySelector('.stageCard'));}
function dataFor(gridId){return gridId==='currentPipeline'?CURRENT_STAGES:ARCHITECTURE_STAGES;}
function selectStage(gridId,detailId,id,el){document.querySelectorAll(`#${gridId} .stageCard`).forEach(x=>x.classList.remove('active'));if(el)el.classList.add('active');const s=dataFor(gridId).find(x=>x.id===id);document.getElementById(detailId).innerHTML=`<h3>${esc(s.title)}</h3><div class="detailGrid">${box('Receives',s.receives)}${box('Detects',s.detects)}${box('Writes / constrains',s.writes)}${box('Before next stage',s.next)}${box(gridId==='currentPipeline'?'Bridge overlay on retained spine':'Failure looks like',s.gap||s.failure)}</div>`;}
function renderOwnerFamilies(){const list=document.getElementById('ownerFamilyList');list.innerHTML=OWNER_FAMILIES.map((f,i)=>`<button class="ownerBtn ${i===0?'active':''}" onclick="selectOwnerFamily('${f.id}',this)"><span class="entityType">${esc(f.title)}</span><br><span class="small">${esc(f.purpose).slice(0,120)}...</span></button>`).join('');selectOwnerFamily(OWNER_FAMILIES[0].id,list.querySelector('.ownerBtn'));}
function chips(arr){return `<div class="relchips">${(arr||[]).map(x=>`<span>${esc(x)}</span>`).join('')}</div>`}
function selectOwnerFamily(id,el){document.querySelectorAll('.ownerBtn').forEach(x=>x.classList.remove('active'));if(el)el.classList.add('active');const f=OWNER_FAMILIES.find(x=>x.id===id);document.getElementById('ownerFamilyDetail').innerHTML=`<h2>${esc(f.title)}</h2><p>${esc(f.purpose)}</p><h3>Owners / surfaces</h3>${chips(f.owners)}<h3>What it explains</h3><ul>${f.explains.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Audit question</h3><p>${esc(f.audit)}</p>`;}
function countBy(items,key){return (items||[]).reduce((acc,item)=>{const value=String(item?.[key]||'uncategorized');acc[value]=(acc[value]||0)+1;return acc;},{});}
function statCards(items){return Object.entries(items).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).map(([label,count])=>`<div class="surfaceStat"><strong>${esc(count)}</strong><span>${esc(label)}</span></div>`).join('');}
function renderOwnerSummary(){
  const el=document.getElementById('ownerSummary');
  if(!el) return;
  const modules=window.DOCS_INDEX_MODULE_CATALOGUE||[];
  const operatorFamilies=countBy(OPERATORS,'family');
  const moduleClasses=countBy(modules,'module_class');
  el.innerHTML=`<div class="surfaceRoleKicker">Source-derived summary</div><h2>Owner/TTP map at a glance</h2><p class="subtle">Counts are computed from the generated operator map and <code>atomics/skill/references/diagnostics/module-catalogue.json</code>. Operator graph entries are curated controls; catalogue modules include case-library and noetic-profile material as well as operators.</p><div class="ownerWorkspaceIntro"><div class="ownerSummaryNote"><h3>Operator families</h3><div class="surfaceSummaryGrid">${statCards(operatorFamilies)}</div></div><div class="ownerSummaryNote"><h3>Catalogue module classes</h3><div class="surfaceSummaryGrid">${statCards(moduleClasses)}</div></div></div>`;
}
function renderOperatorMatrix(){
  const target=document.getElementById('operatorMatrix');
  if(!target) return;
  target.innerHTML=`<table><thead><tr><th>Operator</th><th>Family</th><th>Acts on</th><th>Activation</th><th>Operation</th><th>Delta / reread</th></tr></thead><tbody>${OPERATORS.map(o=>`<tr><td><button class="opChip" onclick="goOperator('${esc(o.id)}')">${esc(o.label||o.id)}</button><br><span class="small"><code>${esc(o.path||'')}</code></span></td><td>${esc(o.family||o.class)}</td><td>${esc(o.acts_on||'')}</td><td>${esc(o.activation||'')}</td><td>${esc(o.operation||'')}</td><td>${esc(o.delta||'')}<br><span class="small">${esc(o.reread||'')}</span></td></tr>`).join('')}</tbody></table>`;
}
{{ OWNER_SOURCE_RENDERER }}
function renderConcepts(){const q=(document.getElementById('conceptSearch')?.value||'').toLowerCase();const t=document.getElementById('conceptType')?.value||'';const arr=CONCEPTS.filter(c=>(!t||c.type===t)&&JSON.stringify(c).toLowerCase().includes(q));const list=document.getElementById('conceptList');list.innerHTML=arr.map((c,i)=>`<button class="conceptBtn ${i===0?'active':''}" data-cid="${esc(c.id)}" onclick="selectConcept('${c.id}',this)"><span class="entityType">${esc(c.type)}</span><br><strong>${esc(c.name)}</strong><br><span class="small">${esc(c.summary)}</span></button>`).join('');if(arr[0])selectConcept(arr[0].id,list.querySelector('.conceptBtn'));}
function selectConcept(id,el){document.querySelectorAll('.conceptBtn').forEach(x=>x.classList.remove('active'));if(el)el.classList.add('active');const c=CONCEPTS.find(x=>x.id===id);const registerRows=c.registerRows?`<h3>Register consequences</h3><table><thead><tr><th>♥ register</th><th>Diagnostic meaning</th><th>Release consequence</th></tr></thead><tbody>${c.registerRows.map(r=>`<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td><td>${esc(r[2])}</td></tr>`).join('')}</tbody></table><div class="callout"><strong>Node-local hardening:</strong> this information belongs inside the clickable ♥ concept node, not as a prominent standalone Theory Deep Dive section.</div>`:'';document.getElementById('conceptDetail').innerHTML=`<h2>${esc(c.name)}</h2><span class="chip">${esc(c.type)}</span><h3>Definition</h3><p>${esc(c.definition)}</p><h3>Runtime role</h3><p>${esc(c.runtime)}</p>${registerRows}<h3>Related fields</h3>${chips(c.fields)}<h3>Operators / TTP</h3>${chips(c.operators)}<h3>Relations</h3>${chips(c.relations)}<h3>Owner/source files</h3>${chips(c.files)}<h3>Case example</h3><p>${esc(c.case)}</p>`;}

function renderRelations(){
  const panel=document.getElementById('relationPanel');
  panel.innerHTML=`<div class="relationLayout">
    <div class="relationList">${RELATIONS.map((r,i)=>`<button class="relationBtn ${i===0?'active':''}" data-rid="${esc(r.id)}" onclick="selectRelation('${r.id}',this)"><span class="entityType">${esc(r.type)}</span><br><strong>${esc(r.label)}</strong><br><span class="small">${esc(r.from)} → ${esc(r.to)}</span></button>`).join('')}</div>
    <div id="relationDetail" class="relationDetail"></div>
  </div>`;
  selectRelation(RELATIONS[0].id,panel.querySelector('.relationBtn'));
}
function selectRelation(id,el){
  document.querySelectorAll('.relationBtn').forEach(x=>x.classList.remove('active'));
  if(el) el.classList.add('active');
  const r=RELATIONS.find(x=>x.id===id);
  highlightNotation(r.symbols||[]);
  document.getElementById('relationDetail').innerHTML=`<h2>${esc(r.label)}</h2><span class="chip">${esc(r.type)}</span><h3>Relation</h3><p><strong>${esc(r.from)}</strong> → <strong>${esc(r.to)}</strong></p><h3>Meaning</h3><p>${esc(r.explain)}</p><h3>Runtime operation</h3><p>${esc(r.runtime)}</p><h3>Notation highlighted</h3>${chips(r.symbols||[])}`;
}

function normalizeOpName(name){
  return String(name||'').trim().replace(/^OP:/,'');
}
function getOperatorByName(name){
  const raw=normalizeOpName(name);
  if(!raw || raw==='—') return null;
  const lower=raw.toLowerCase();
  return OPERATORS.find(o =>
    String(o.id).toLowerCase()===lower ||
    (o.aliases||[]).some(a=>String(a).toLowerCase()===lower) ||
    String(o.label||'').toLowerCase()===lower
  ) || null;
}
function chips(arr){
  return `<div class="relchips">${(arr||[]).map(x=>{
    const op=getOperatorByName(x);
    return op ? `<button class="opChip" onclick="goOperator('${esc(op.id)}')">${esc(x)}</button>` : `<span>${esc(x)}</span>`;
  }).join('')}</div>`;
}
function operatorExplainBlock(arr){
  const ops=(arr||[]).map(x=>getOperatorByName(x)).filter(Boolean);
  if(!ops.length) return '';
  return `<div class="opExplainBlock"><h3>What these operators do here</h3>${ops.map(o=>`<div class="opExplain"><button class="opChip" onclick="goOperator('${esc(o.id)}')">${esc(o.aliases?.[0]||o.id)}</button><strong>${esc(o.label)}</strong><p>${esc(o.plain)} ${esc(o.operation)}</p><p class="small"><b>Delta:</b> ${esc(o.delta)}</p></div>`).join('')}</div>`;
}
function relationOperators(r){
  const txt=[r.label,r.from,r.to,r.explain,r.runtime].join(' ');
  return OPERATORS.filter(o => (o.aliases||[o.id]).some(a => new RegExp(`(^|[^A-Za-z0-9-])${a.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}([^A-Za-z0-9-]|$)`).test(txt)));
}
function goOperator(id){
  document.querySelectorAll('.tabsec').forEach(x=>x.classList.remove('active'));
  document.getElementById('owners').classList.add('active');
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  const ownerTab=[...document.querySelectorAll('.tab')].find(t=>t.textContent.includes('Owners'));
  if(ownerTab) ownerTab.classList.add('active');
  renderOperatorGraph();
  const op=getOperatorByName(id);
  if(op){
    const btn=document.querySelector(`#operatorGraphList .opBtn[data-opid="${CSS.escape(op.id)}"]`);
    selectOperator(op.id, btn);
    document.getElementById('owners').scrollIntoView({behavior:'smooth',block:'start'});
    setTimeout(()=>document.getElementById('operatorGraphDetail')?.scrollIntoView({behavior:'smooth',block:'center'}),250);
  }
}
function renderOperatorGraph(){
  const q=(document.getElementById('opSearch')?.value||'').toLowerCase();
  const fam=document.getElementById('opFamily')?.value||'';
  const arr=OPERATORS.filter(o=>(!fam||o.family===fam)&&JSON.stringify(o).toLowerCase().includes(q));
  const list=document.getElementById('operatorGraphList');
  if(!list) return;
  list.innerHTML=arr.map((o,i)=>`<button class="opBtn ${i===0?'active':''}" data-opid="${esc(o.id)}" onclick="selectOperator('${esc(o.id)}',this)"><span class="opFamily">${esc(o.family||o.class)}</span><br><strong>${esc(o.label||o.id)}</strong><br><span class="small">${esc(o.plain||o.operation||'')}</span></button>`).join('');
  if(arr[0]) selectOperator(arr[0].id, list.querySelector('.opBtn'));
}
function selectOperator(id,el){
  document.querySelectorAll('.opBtn').forEach(x=>x.classList.remove('active'));
  if(el) el.classList.add('active');
  const o=getOperatorByName(id);
  if(!o) return;
  if(typeof highlightNotation==='function') highlightNotation(o.symbols||[]);
  const detail=document.getElementById('operatorGraphDetail');
  if(detail){
    detail.innerHTML=`<h2>${esc(o.label||o.id)}</h2>
      <span class="chip">${esc(o.family||o.class)}</span>
      <p>${esc(o.plain||'')}</p>
      <div class="opMiniGrid">
        <div class="opMini"><h4>Acts on</h4><p>${esc(o.acts_on||o.input||'')}</p></div>
        <div class="opMini"><h4>Activation</h4><p>${esc(o.activation||'')}</p></div>
        <div class="opMini"><h4>Operation</h4><p>${esc(o.operation||'')}</p></div>
        <div class="opMini"><h4>Delta</h4><p>${esc(o.delta||'')}</p></div>
        <div class="opMini"><h4>Reread effect</h4><p>${esc(o.reread||'')}</p></div>
        <div class="opMini"><h4>Owner/source</h4><p><code>${esc(o.path||'')}</code></p></div>
      </div>
      <h3>Related concepts</h3>${chips(o.concepts||[])}
      <h3>Notation highlighted</h3>${chips(o.symbols||[])}
      <h3>Example</h3><p>${esc(o.example||'')}</p>`;
  }
}

function renderRefs(){const q=(document.getElementById('refSearch')?.value||'').toLowerCase();const layer=document.getElementById('refLayer')?.value||'';const f=REFS.filter(r=>(!layer||r.layer===layer)&&JSON.stringify(r).toLowerCase().includes(q));document.getElementById('refTable').innerHTML=`<table><thead><tr><th>Path</th><th>Role</th><th>Layer</th><th>Governs</th><th>Operators</th></tr></thead><tbody>${f.map(r=>`<tr><td><code>${esc(r.path)}</code><br><span class="small">${esc(r.lines)} lines</span></td><td>${esc(r.role)}</td><td>${esc(r.layer)}</td><td>${esc(r.governs)}</td><td>${(r.operators||[]).map(esc).join(', ')}</td></tr>`).join('')}</tbody></table><p class="small">${f.length} references shown.</p>`;renderDocList(q);}
function renderDocList(q=''){const arr=DOCS.filter(d=>!q||JSON.stringify(d).toLowerCase().includes(q));document.getElementById('docList').innerHTML=arr.map(d=>`<div class="docitem" onclick="showDoc(${d.id})"><strong>${esc(d.title)}</strong><br><span class="small">${esc(d.rel)} · ${esc(d.lines)} lines</span></div>`).join('');}
function showDoc(id){const d=DOCS.find(x=>x.id==id);if(!d)return;document.getElementById('docBody').innerHTML=`<h2>${esc(d.title)}</h2><p class="small"><code>${esc(d.rel)}</code> · ${esc(d.lines)} lines</p><div>${d.html||'<pre>'+esc(d.content||'')+'</pre>'}</div>`;}

let REFERENCE_SELECTED_ID = null;
function referenceMetaForDoc(doc){
  return REFS.find(r=>r.path===doc.rel) || {};
}
function filteredReferenceRows(q,layer){
  const needle=String(q||'').toLowerCase();
  return REFS.filter(r=>(!layer||r.layer===layer)&&(!needle||JSON.stringify(r).toLowerCase().includes(needle)));
}
function filteredReferenceDocs(q,layer){
  const needle=String(q||'').toLowerCase();
  return DOCS.filter(d=>{
    const ref=referenceMetaForDoc(d);
    if(layer && ref.layer!==layer) return false;
    return !needle || JSON.stringify({...d,ref}).toLowerCase().includes(needle);
  });
}
function renderReferenceSummary(q,layer,refsShown,docsShown){
  const el=document.getElementById('refSummary');
  if(!el) return;
  const summary=(typeof REF_SUMMARY!=='undefined') ? REF_SUMMARY : {};
  const layerStats=statCards(summary.by_layer||{});
  const roleStats=statCards(summary.by_role||{});
  const activeFilter=q||layer ? `<p class="small"><strong>Filtered:</strong> ${esc(refsShown)} source rows and ${esc(docsShown)} document snapshots match the active controls.</p>` : '';
  el.innerHTML=`<div class="surfaceRoleKicker">Source-derived summary</div><h2>Reference library at a glance</h2><p class="subtle">Generated from tracked atomics README/SKILL/reference Markdown. The selected document preview is the human path; the full source map remains available below for audit work.</p><div class="surfaceSummaryGrid"><div class="surfaceStat"><strong>${esc(summary.total_references||REFS.length)}</strong><span>source rows</span></div><div class="surfaceStat"><strong>${esc(summary.total_snapshots||DOCS.length)}</strong><span>document snapshots</span></div><div class="surfaceStat"><strong>${esc(summary.total_lines||REFS.reduce((n,r)=>n+(Number(r.lines)||0),0))}</strong><span>source lines</span></div><div class="surfaceStat"><strong>${esc(Object.keys(summary.by_layer||{}).length)}</strong><span>layers</span></div></div><div class="ownerWorkspaceIntro"><div class="ownerSummaryNote"><h3>Layers</h3><div class="surfaceSummaryGrid">${layerStats}</div></div><div class="ownerSummaryNote"><h3>Roles</h3><div class="surfaceSummaryGrid">${roleStats}</div></div></div>${activeFilter}`;
}
function renderRefs(){
  const q=(document.getElementById('refSearch')?.value||'').trim();
  const layer=document.getElementById('refLayer')?.value||'';
  const refs=filteredReferenceRows(q,layer);
  const docs=filteredReferenceDocs(q,layer);
  const refTable=document.getElementById('refTable');
  if(refTable){
    refTable.innerHTML=`<table><thead><tr><th>Path</th><th>Role</th><th>Layer</th><th>Governs</th><th>Operators</th></tr></thead><tbody>${refs.map(r=>`<tr><td><code>${esc(r.path)}</code><br><span class="small">${esc(r.lines)} lines</span></td><td>${esc(r.role)}</td><td>${esc(r.layer)}</td><td>${esc(r.governs)}</td><td>${(r.operators||[]).map(esc).join(', ')}</td></tr>`).join('')}</tbody></table><p class="small">${refs.length} references shown.</p>`;
  }
  renderReferenceSummary(q,layer,refs.length,docs.length);
  if(docs.length && !docs.some(d=>String(d.id)===String(REFERENCE_SELECTED_ID))) REFERENCE_SELECTED_ID=docs[0].id;
  renderDocList(q,layer);
  if(docs.length) showDoc(REFERENCE_SELECTED_ID||docs[0].id);
  if(!docs.length){
    REFERENCE_SELECTED_ID=null;
    const body=document.getElementById('docBody');
    if(body) body.innerHTML='<div class="docbodyEmpty">No generated source snapshot matches the current filter.</div>';
  }
}
function renderDocList(q='',layer=''){
  const docs=filteredReferenceDocs(q,layer);
  const list=document.getElementById('docList');
  if(!list) return;
  list.setAttribute('role','listbox');
  if(!docs.length){
    list.innerHTML='<div class="docbodyEmpty">No documents match.</div>';
    return;
  }
  if(!docs.some(d=>String(d.id)===String(REFERENCE_SELECTED_ID))) REFERENCE_SELECTED_ID=docs[0].id;
  list.innerHTML=docs.map(d=>{
    const ref=referenceMetaForDoc(d);
    const active=String(d.id)===String(REFERENCE_SELECTED_ID);
    return `<button type="button" class="docitem ${active?'active':''}" role="option" aria-selected="${active?'true':'false'}" data-doc-id="${esc(d.id)}" onclick="showDoc(${Number(d.id)})"><strong>${esc(d.title)}</strong><br><span class="small"><code>${esc(d.rel)}</code></span><br><span class="small">${esc(ref.layer||'reference')} · ${esc(ref.role||'snapshot')} · ${esc(d.lines)} lines</span></button>`;
  }).join('');
}
function showDoc(id){
  const d=DOCS.find(x=>String(x.id)===String(id));
  if(!d) return;
  REFERENCE_SELECTED_ID=d.id;
  document.querySelectorAll('#docList .docitem').forEach(item=>{
    const active=String(item.getAttribute('data-doc-id'))===String(d.id);
    item.classList.toggle('active',active);
    item.setAttribute('aria-selected',active?'true':'false');
  });
  const ref=referenceMetaForDoc(d);
  const body=document.getElementById('docBody');
  if(!body) return;
  body.innerHTML=`<div class="surfaceRoleKicker">Selected generated snapshot</div><h2>${esc(d.title)}</h2><p class="small"><code>${esc(d.rel)}</code> · ${esc(d.lines)} lines</p><div class="relchips"><span>${esc(ref.layer||'reference')}</span><span>${esc(ref.role||'snapshot')}</span><span>${esc(ref.governs||'source')}</span></div><div class="callout"><strong>Source ownership:</strong> this preview is generated from the tracked Markdown source. The raw source-map table is collapsed below for audit parity.</div><div>${d.html||'<pre>'+esc(d.content||'')+'</pre>'}</div>`;
}

function notationMetaFor(key){
  if(!key) return null;
  const el=document.querySelector(`.ntok[data-k="${CSS.escape(key)}"]`);
  if(!el) return null;
  return {
    key,
    symbol:el.textContent.trim(),
    meaning:el.getAttribute('data-meaning')||el.getAttribute('data-label')||key,
    runtimeRole:el.getAttribute('data-runtime-role')||el.getAttribute('data-label')||key,
    sourceOwners:el.getAttribute('data-source-owners')||'docs/index/runtime-architecture.json',
    relatedTargets:(el.getAttribute('data-related-targets')||'').split(/\s+/).filter(Boolean),
    phaseClass:[...el.classList].find(name=>name.startsWith('phase-'))||''
  };
}
function notationTokenLabel(key){
  const el=document.querySelector(`.ntok[data-k="${CSS.escape(key)}"]`);
  return el ? el.textContent.trim() : key;
}
function renderNotationPanel(keys, primaryKey){
  const explain=document.getElementById('notationExplain');
  if(!explain) return;
  const ordered=[...new Set((Array.isArray(keys)?keys:[keys]).filter(Boolean))];
  if(!ordered.length){
    explain.innerHTML='Click a concept or relation to highlight its place in the notation.';
    return;
  }
  const primary=(primaryKey && ordered.includes(primaryKey)) ? primaryKey : ordered[0];
  const meta=notationMetaFor(primary) || {key:primary,symbol:primary,meaning:primary,runtimeRole:'No runtime role metadata found.',sourceOwners:'docs/index/runtime-architecture.json',relatedTargets:[]};
  const related=[...new Set([...(meta.relatedTargets||[]),...ordered.filter(k=>k!==primary)])].filter(k=>k!==primary);
  const ownerChips=String(meta.sourceOwners||'').split(';').map(owner=>owner.trim()).filter(Boolean).map(owner=>`<code>${esc(owner)}</code>`).join('<br>');
  const highlightedRows=ordered.map(key=>{
    const item=notationMetaFor(key) || {symbol:key,meaning:key};
    return `<div class="notationHighlightRow"><b>${esc(item.symbol||key)}</b><span>${esc(item.meaning||key)}</span></div>`;
  }).join('');
  const relatedHtml=related.length
    ? `<div class="notationRelated">${related.map(k=>`<span>${esc(notationTokenLabel(k))}</span>`).join('')}</div>`
    : '<span class="small">No related notation targets declared.</span>';
  explain.innerHTML=`<div class="notationContext">
    <div class="notationContextHeader"><span>Highlighted notation</span><span class="ntokMini ${esc(meta.phaseClass||'')}">${esc(meta.symbol||primary)}</span></div>
    <div class="notationContextGrid">
      <div class="notationContextBlock"><strong>Meaning</strong><span>${esc(meta.meaning||primary)}</span></div>
      <div class="notationContextBlock"><strong>Runtime role</strong><span>${esc(meta.runtimeRole||'')}</span></div>
      <div class="notationContextBlock"><strong>Source owners</strong>${ownerChips||'<code>docs/index/runtime-architecture.json</code>'}</div>
      <div class="notationContextBlock"><strong>Highlighted set</strong><div class="notationHighlightList">${highlightedRows}</div></div>
      <div class="notationContextBlock"><strong>Related</strong>${relatedHtml}</div>
    </div>
  </div>`;
}
function highlightNotation(keys, primaryKey){
  const ordered=[...new Set((Array.isArray(keys)?keys:[keys]).filter(Boolean))];
  const set=new Set(ordered);
  document.querySelectorAll('.ntok').forEach(el=>{
    const key=el.getAttribute('data-k');
    el.classList.toggle('active', set.has(key));
    el.classList.toggle('is-linked-active', set.has(key));
    el.classList.toggle('muted', set.size && !set.has(key));
    el.setAttribute('aria-pressed', set.has(key) ? 'true' : 'false');
  });
  renderNotationPanel(ordered, primaryKey);
}
function clearNotation(){ highlightNotation([]); }
function theoryCardTargetKeys(card){
  if(!card) return [];
  return (card.getAttribute('data-notation-targets')||'')
    .split(/\s+/)
    .map(x=>x.trim())
    .filter(Boolean);
}
function selectTheoryCard(cardOrId){
  const card = typeof cardOrId === 'string'
    ? document.querySelector(`.controlCard[data-theory-card="${CSS.escape(cardOrId)}"]`)
    : cardOrId;
  if(!card) return;
  document.querySelectorAll('.controlCard[data-theory-card]').forEach(el=>{
    const active = el === card;
    el.classList.toggle('is-linked-active', active);
    el.setAttribute('aria-pressed', active ? 'true' : 'false');
  });
  const targets = theoryCardTargetKeys(card);
  if(typeof window.highlightNotation === 'function') window.highlightNotation(targets, targets[0]);
  else highlightNotation(targets, targets[0]);
}
function activateNotationToken(ev, el){
  if(ev && ev.type === 'keydown' && ev.key !== 'Enter' && ev.key !== ' ') return true;
  if(ev) ev.preventDefault();
  if(el && typeof el.click === 'function') el.click();
  return false;
}

function init(){
  const safe=(label,fn)=>{try{fn()}catch(e){console.warn('DAEE wiki init skipped:',label,e)}};

  if(document.getElementById('currentPipeline')) safe('current pipeline',()=>renderPipeline(CURRENT_STAGES,'currentPipeline','currentDetail'));
  if(document.getElementById('targetPipeline')) safe('target pipeline',()=>renderPipeline(TARGET_STAGES,'targetPipeline','targetDetail'));

  safe('owner families',()=>renderOwnerFamilies());
  if(document.getElementById('ownerSummary')) safe('owner summary',()=>renderOwnerSummary());
  if(document.getElementById('operatorGraphList')) safe('operator graph',()=>renderOperatorGraph());
  if(document.getElementById('operatorMatrix')) safe('operator matrix',()=>renderOperatorMatrix());
  if(document.getElementById('ownerSourceTable')) safe('owner source table',()=>renderOwnerSourceTable());
  if(document.getElementById('conceptList')) safe('concepts',()=>renderConcepts());
  if(document.getElementById('relationPanel')) safe('relations',()=>renderRelations());
  if(document.getElementById('refTable')) safe('refs',()=>renderRefs());
  else if(document.getElementById('docList')) safe('doc list',()=>renderDocList());
  const defaultTheoryCard=document.querySelector('.controlCard[data-theory-card][aria-pressed="true"]') || document.querySelector('.controlCard[data-theory-card]');
  if(defaultTheoryCard) safe('theory card default notation',()=>selectTheoryCard(defaultTheoryCard));

}
document.addEventListener('DOMContentLoaded',()=>{ initTopTabs(); init(); });
</script>
<script id="sot-field-navigation-v15">
/* v15 ACID/DRY SOT: one field map, one renderer, one navigation path, one final highlight source. */
(function(){
  const FIELD = {
    D0:{sym:'D₀', label:'surface discourse / initial signal', concept:'D0', key:'D0'},
    'D₀':{sym:'D₀', label:'surface discourse / initial signal', concept:'D0', key:'D0'},
    Psi:{sym:'Ψᴺ', label:'encoded noetic signal-state', concept:'Psi', key:'Psi'},
    'Ψᴺ':{sym:'Ψᴺ', label:'encoded noetic signal-state', concept:'Psi', key:'Psi'},
    noetic:{sym:'𝓝', label:'noetic-structure selection space', concept:'noetic', key:'noetic'},
    '𝓝':{sym:'𝓝', label:'noetic-structure selection space', concept:'noetic', key:'noetic'},
    N:{sym:'N∈𝓝', label:'runtime-selected operative noetic frame from 𝓝', concept:'N', key:'N'},
    m:{sym:'m', label:'deformation / concealment / memetic mode', concept:'m', key:'m'},
    tau:{sym:'τ', label:'tribunal / burden-function / criterion', concept:'tau', key:'tau'},
    'τ':{sym:'τ', label:'tribunal / burden-function / criterion', concept:'tau', key:'tau'},
    sigma:{sym:'σ', label:'source / semantic / authority status', concept:'sigma', key:'sigma'},
    'σ':{sym:'σ', label:'source / semantic / authority status', concept:'sigma', key:'sigma'},
    heart:{sym:'♥', label:'affective-discursive register / release posture', concept:'heart', key:'heart'},
    '♥':{sym:'♥', label:'affective-discursive register / release posture', concept:'heart', key:'heart'},
    xi:{sym:'ξ', label:'epistemic / warrant grammar', concept:'xi', key:'xi'},
    'ξ':{sym:'ξ', label:'epistemic / warrant grammar', concept:'xi', key:'xi'},
    omega:{sym:'Ω', label:'ontological grammar', concept:'omega', key:'omega'},
    'Ω':{sym:'Ω', label:'ontological grammar', concept:'omega', key:'omega'},
    mu:{sym:'μ', label:'meta-noetic memetic vector', concept:'mu', key:'mu'},
    'μ':{sym:'μ', label:'meta-noetic memetic vector', concept:'mu', key:'mu'},
    kappa:{sym:'κ', label:'collapse radius / downstream dependencies', concept:'kappa', key:'kappa'},
    'κ':{sym:'κ', label:'collapse radius / downstream dependencies', concept:'kappa', key:'kappa'},
    H:{sym:'H', label:'held set', concept:'H', key:'H'},
    IR:{sym:'IR', label:'compact DSL/IR control state', concept:'IR', key:'IR'},
    burden:{sym:'ⁿB', label:'current burden n', concept:'burden', key:'burden'},
    'ⁿB':{sym:'ⁿB', label:'current burden n', concept:'burden', key:'burden'},
    submoves:{sym:'ⁿBᵢ[OPᵢ]', label:'owner-backed submoves under burden n', concept:'submoves', key:'submoves'},
    Land:{sym:'Land(ⁿB)', label:'burden landing', concept:'Land', key:'Land'},
    deltaB:{sym:'ΔⁿB', label:'burden-event delta', concept:'deltaB', key:'deltaB'},
    'ΔⁿB':{sym:'ΔⁿB', label:'burden-event delta', concept:'deltaB', key:'deltaB'},
    deltaK:{sym:'Δκ', label:'collapse-radius / dependency delta', concept:'deltaK', key:'deltaK'},
    'Δκ':{sym:'Δκ', label:'collapse-radius / dependency delta', concept:'deltaK', key:'deltaK'},
    nablaDot:{sym:'∇·T', label:'target-explicit post-Delta residual outward pressure diagnostic', concept:'nablaDot', key:'nablaDot'},
    '∇·':{sym:'∇·', label:'target-explicit post-Delta residual outward pressure diagnostic', concept:'nablaDot', key:'nablaDot'},
    nablaCross:{sym:'∇×T', label:'target-explicit post-Delta circular dependency diagnostic', concept:'nablaCross', key:'nablaCross'},
    '∇×':{sym:'∇×', label:'target-explicit post-Delta circular dependency diagnostic', concept:'nablaCross', key:'nablaCross'},
    delDot:{sym:'∇·', label:'∇· / del-dot alias', concept:'delDot', key:'delDot'},
    'del-dot':{sym:'∇·', label:'∇· / del-dot alias', concept:'delDot', key:'delDot'},
    delCross:{sym:'∇×', label:'∇× / del-cross alias', concept:'delCross', key:'delCross'},
    'del-cross':{sym:'∇×', label:'∇× / del-cross alias', concept:'delCross', key:'delCross'},
    fieldDiagnostics:{sym:'∇·T/∇×T', label:'target-explicit post-Delta field diagnostics', concept:'nablaDot', key:'fieldDiagnostics'},
    R:{sym:'R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)', label:'state/noetic reread', concept:'R', key:'R'},
    C:{sym:'𝒞(Ψᴺ)', label:'constrained noetic collapse / discursive resolution', concept:'collapse', key:'C'},
    '𝒞(Ψᴺ)':{sym:'𝒞(Ψᴺ)', label:'constrained noetic collapse / discursive resolution', concept:'collapse', key:'C'},
    final:{sym:'N_fiṭrī ∧ ʿaql ṣarīḥ', label:'restored fiṭrah and sound reason; ♥/ξ/Ω/μ restored or reordered', concept:'collapse', key:'final'},
    'N_fiṭrī ∧ ʿaql ṣarīḥ':{sym:'N_fiṭrī ∧ ʿaql ṣarīḥ', label:'restored fiṭrah and sound reason; ♥/ξ/Ω/μ restored or reordered', concept:'collapse', key:'final'},
    nextB:{sym:'ⁿ⁺¹B', label:'next burden licensed by reread', concept:'decision', key:'nextB'},
    'ⁿ⁺¹B':{sym:'ⁿ⁺¹B', label:'next burden licensed by reread', concept:'decision', key:'nextB'}
  };

  function fInfo(raw){ return FIELD[String(raw||'').trim()] || null; }
  function uniq(xs){ return [...new Set((xs||[]).filter(Boolean))]; }
  function conceptById(id){ return (CONCEPTS||[]).find(c => c.id === id); }
  function extractCallArg(raw, fnName){
    raw = String(raw || '');
    const needle = fnName + "('";
    const start = raw.indexOf(needle);
    if(start < 0) return null;
    const rest = raw.slice(start + needle.length);
    const end = rest.indexOf("'");
    return end >= 0 ? rest.slice(0, end) : null;
  }

  function ensureHeldConcept(){
    if(!Array.isArray(CONCEPTS) || conceptById('H')) return;
    CONCEPTS.push({
      id:'H',
      name:'H held set',
      type:'runtime control state',
      summary:'Live but unreleased material carried through burden cycles.',
      definition:'H is the held set: input-anchored material that remains live but is not yet released because a prior burden, source-status issue, register, or gate condition controls the order.',
      runtime:'H prevents the model from dumping all available content while preserving what must be reread after Land(ⁿB) and Δκ.',
      fields:['R','Δκ','ⁿ⁺¹B'],
      operators:['P7','P2','M4','V10','output-release','recursive-state-transitions'],
      relations:['is reread by → R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)','holds → unreleased routes','prevents → premature Layer B release'],
      files:['output-release.md','recursive-state-transitions.md','diagnostic-render-contract.md'],
      case:'Doctrinal content may be held while a source-status burden is still live.',
      symbols:['H','R','deltaK','nextB']
    });
  }

  function opByName(name){
    const raw=String(name||'').trim();
    if(!raw || raw==='—' || raw==='all active OPs') return null;
    const lower=raw.toLowerCase();
    return (OPERATORS||[]).find(o =>
      String(o.id||'').toLowerCase()===lower ||
      (o.aliases||[]).some(a=>String(a).toLowerCase()===lower) ||
      String(o.label||'').toLowerCase()===lower
    ) || null;
  }
  window.getOperatorByName = opByName;

  function sourceByName(x){
    const q=String(x||'').toLowerCase();
    if(!q) return null;
    return (REFS||[]).find(r => String(r.path||'').toLowerCase().includes(q) || String(r.title||'').toLowerCase().includes(q) || String(r.role||'').toLowerCase().includes(q)) || null;
  }

  function fieldChip(raw, opts={}){
    const info=fInfo(raw);
    if(!info) return `<span class="readableFieldChip"><span class="fieldSym">${esc(raw)}</span></span>`;
    const self = opts.currentId && info.concept === opts.currentId;
    const cls = self ? 'readableFieldChip' : 'readableFieldChip clickable';
    const click = self ? '' : ` onclick="goConceptField('${esc(info.key)}')"`;
    return `<button class="${cls}" data-field-key="${esc(info.key)}" data-concept-id="${esc(info.concept)}"${click}><span class="fieldSym">${esc(info.sym)}</span><span class="fieldMeaning">— ${esc(info.label)}</span></button>`;
  }

  window.fieldChips = function(arr, currentId){
    const clean=uniq(arr).filter(x => {
      const info=fInfo(x);
      return !(info && currentId && info.concept === currentId);
    });
    if(!clean.length) return '<p class="small">No separate related fields; this concept is itself the selected notation field.</p>';
    return `<div class="readableFieldGrid">${clean.map(x=>fieldChip(x,{currentId})).join('')}</div><div class="fieldNavNote">Field chips navigate to their concept node and then highlight that concept’s full notation context.</div>`;
  };

  window.notationChips = function(keys){
    const clean=uniq(keys);
    if(!clean.length) return '<p class="small">No notation token is directly associated.</p>';
    return `<div class="readableFieldGrid">${clean.map(x=>fieldChip(x)).join('')}</div>`;
  };

  window.notationExplanationBlock = function(keys){
    const clean=uniq(keys);
    if(!clean.length) return '';
    return `<div class="notationExplainList"><h3>Notation highlighted</h3>${notationChips(clean)}</div>`;
  };

  window.goReference = function(label){
    document.querySelectorAll('.tabsec').forEach(x=>x.classList.remove('active'));
    document.getElementById('reference')?.classList.add('active');
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    const refTab=[...document.querySelectorAll('.tab')].find(t=>t.textContent.includes('Reference'));
    if(refTab) refTab.classList.add('active');
    const input=document.getElementById('refSearch');
    if(input) input.value=label;
    if(typeof renderRefs==='function') renderRefs();
    const match=sourceByName(label);
    if(match && typeof showDoc==='function' && match.id) showDoc(match.id);
    document.getElementById('reference')?.scrollIntoView({behavior:'smooth',block:'start'});
  };

  window.goOperator = function(id){
    document.querySelectorAll('.tabsec').forEach(x=>x.classList.remove('active'));
    document.getElementById('owners')?.classList.add('active');
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    const ownerTab=[...document.querySelectorAll('.tab')].find(t=>t.textContent.includes('Owners'));
    if(ownerTab) ownerTab.classList.add('active');
    if(typeof renderOperatorGraph==='function') renderOperatorGraph();
    const op=opByName(id);
    if(op && typeof selectOperator==='function'){
      const btn=document.querySelector(`#operatorGraphList .opBtn[data-opid="${CSS.escape(op.id)}"]`);
      selectOperator(op.id, btn);
      document.getElementById('owners')?.scrollIntoView({behavior:'smooth',block:'start'});
      setTimeout(()=>document.getElementById('operatorGraphDetail')?.scrollIntoView({behavior:'smooth',block:'center'}),250);
    }
  };

  window.chips = function(arr){
    return `<div class="relchips">${(arr||[]).map(x=>{
      const info=fInfo(x);
      if(info) return fieldChip(x);
      const op=opByName(x);
      if(op) return `<button class="opChip" onclick="goOperator('${esc(op.id)}')">${esc(x)}</button>`;
      const src=sourceByName(x);
      if(src) return `<button class="sourceChip" onclick="goReference('${esc(x)}')">${esc(x)}</button>`;
      return `<span>${esc(x)}</span>`;
    }).join('')}</div>`;
  };

  function shortOp(o){ return (o && ((o.aliases && o.aliases[0]) || o.id)) || ''; }
  window.operatorExplainBlock = function(arr, context){
    const ops=(arr||[]).map(x=>opByName(x)).filter(Boolean);
    if(!ops.length) return '';
    return `<div class="opExplainBlock"><h3>Operators / TTP explained in this context</h3>${
      ops.map(o=>`<div class="opExplainRow"><button class="opChip" onclick="goOperator('${esc(o.id)}')">${esc(shortOp(o))}</button><span class="opDash">—</span><div class="opText"><strong>${esc(o.label)}</strong>: ${esc(o.plain)} ${esc(o.operation)} <em>Here:</em> in “${esc(context||'this node')}”, it acts on ${esc(o.acts_on)} and should produce ${esc(o.delta)}.</div></div>`).join('')
    }</div>`;
  };

  function relationOps(r){
    const hay=[r?.label,r?.from,r?.to,r?.explain,r?.runtime,(r?.symbols||[]).join(' ')].join(' ');
    return (OPERATORS||[]).filter(o => (o.aliases || [o.id]).some(a => {
      const aa=String(a).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      return new RegExp(`(^|[^A-Za-z0-9-])${aa}([^A-Za-z0-9-]|$)`).test(hay);
    }));
  }

  function enrichConcepts(){
    const byId=Object.fromEntries((CONCEPTS||[]).map(c=>[c.id,c]));
    if(byId.kappa){
      byId.kappa.operators=['P7','M8','FPD','V2','M1','M1-P','M2','M9','V10','R1','R3','P1'];
      byId.kappa.relations=['dependency of → load-bearing node','changed by → any owner that lands a load-bearing burden','causes re-read of → H','licenses/blocks → ⁿ⁺¹B'];
    }
    if(byId.noetic) byId.noetic.operators=['V1','M5','F1','F2','F3','R1','R2','R3','P1','P4','V7'];
    if(byId.xi) byId.xi.operators=['reason-disambiguation','V2','FPD','E1','E2','M1','M1-P','R1','R2','R3','V10','P3'];
    if(byId.omega) byId.omega.operators=['M9','V8','V9','V12','M8','P6'];
    if(byId.mu) byId.mu.operators=['FPD','V2','M1-P','M3','M4','M5','F2','V7','V11','symmetric-taqlid-check','P7'];
    if(byId.IR){ byId.IR.operators=['P7']; byId.IR.files=['diagnostic-ir','routing-precedence','output-release','diagnostic-render-contract']; }
    if(byId.LandR) byId.LandR.operators=['P7','M8','output-release','recursive-state-transitions'];
  }

  window.selectConcept = function(id, el){
    ensureHeldConcept(); enrichConcepts();
    document.querySelectorAll('.conceptBtn').forEach(x=>x.classList.remove('active'));
    if(el) el.classList.add('active');
    const c=conceptById(id);
    if(!c) return;
    if(typeof highlightNotation==='function') highlightNotation(c.symbols || []);
    const detail=document.getElementById('conceptDetail');
    if(detail){
      detail.innerHTML=`<h2>${esc(c.name)}</h2>
        <span class="chip">${esc(c.type)}</span>
        <h3>Definition</h3><p>${esc(c.definition)}</p>
        <h3>Runtime role</h3><p>${esc(c.runtime)}</p>
        <h3>Related fields</h3>${fieldChips(c.fields || [], c.id)}
        ${operatorExplainBlock(c.operators, c.name)}
        <h3>Relations</h3>${chips(c.relations)}
        <h3>Owner/source files</h3>${chips(c.files)}
        <h3>Case example</h3><p>${esc(c.case)}</p>
        ${notationExplanationBlock(c.symbols || [])}`;
    }
  };

  window.goConceptField = function(raw){
    ensureHeldConcept(); enrichConcepts();
    const info=fInfo(raw);
    if(!info) return;
    // Switch to Theory / Concept graph.
    document.querySelectorAll('.tabsec').forEach(x=>x.classList.remove('active'));
    document.getElementById('theory')?.classList.add('active');
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    const theoryTab=[...document.querySelectorAll('.tab')].find(t=>t.textContent.includes('Theory'));
    if(theoryTab) theoryTab.classList.add('active');
    document.querySelectorAll('.subpanel').forEach(x=>x.classList.remove('active'));
    document.getElementById('sub-concepts')?.classList.add('active');
    document.querySelectorAll('.subtab').forEach(x=>x.classList.remove('active'));
    const conceptSub=[...document.querySelectorAll('.subtab')].find(t=>t.textContent.includes('Concept'));
    if(conceptSub) conceptSub.classList.add('active');
    const search=document.getElementById('conceptSearch');
    const type=document.getElementById('conceptType');
    if(search) search.value='';
    if(type) type.value='';
    if(typeof renderConcepts==='function') renderConcepts();
    const btn=[...document.querySelectorAll('#conceptList .conceptBtn')].find(b=>{
      const cid=b.dataset?.cid || extractCallArg(b.getAttribute('onclick'),'selectConcept');
      return cid===info.concept;
    });
    if(btn){
      selectConcept(info.concept, btn); // single SOT for final highlight
      btn.scrollIntoView({behavior:'smooth',block:'center'});
      setTimeout(()=>document.getElementById('conceptDetail')?.scrollIntoView({behavior:'smooth',block:'nearest'}),120);
    }
  };

  window.selectRelation = function(id, el){
    document.querySelectorAll('.relationBtn').forEach(x=>x.classList.remove('active'));
    if(el) el.classList.add('active');
    const r=(RELATIONS||[]).find(x=>x.id===id);
    if(!r) return;
    if(typeof highlightNotation==='function') highlightNotation(r.symbols || []);
    const ops=relationOps(r);
    const detail=document.getElementById('relationDetail');
    if(detail){
      detail.innerHTML=`<h2>${esc(r.label)}</h2>
        <span class="chip">${esc(r.type)}</span>
        <h3>Relation</h3><p><strong>${esc(r.from)}</strong> → <strong>${esc(r.to)}</strong></p>
        <h3>Meaning</h3><p>${esc(r.explain)}</p>
        <h3>Runtime operation</h3><p>${esc(r.runtime)}</p>
        ${operatorExplainBlock(ops.map(shortOp), r.label)}
        ${notationExplanationBlock(r.symbols || [])}`;
    }
  };

  const oldShowSub=window.showSub;
  window.showSub=function(id,btn){
    if(typeof oldShowSub==='function') oldShowSub(id,btn);
    if(id==='concepts'){
      const active=document.querySelector('#conceptList .conceptBtn.active') || document.querySelector('#conceptList .conceptBtn');
      const raw=active?.dataset?.cid || extractCallArg(active?.getAttribute('onclick'),'selectConcept');
      if(raw) selectConcept(raw,active);
    } else if(id==='relations'){
      const active=document.querySelector('.relationList .relationBtn.active') || document.querySelector('.relationList .relationBtn');
      const raw=active?.dataset?.rid || extractCallArg(active?.getAttribute('onclick'),'selectRelation');
      if(raw) selectRelation(raw,active);
    }
  };

  document.addEventListener('DOMContentLoaded', function(){
    ensureHeldConcept(); enrichConcepts();
    setTimeout(function(){
      if(typeof renderConcepts==='function') renderConcepts();
      const active=document.querySelector('#conceptList .conceptBtn.active') || document.querySelector('#conceptList .conceptBtn');
      const raw=active?.dataset?.cid || extractCallArg(active?.getAttribute('onclick'),'selectConcept');
      if(raw) selectConcept(raw,active);
    },0);
  });
})();
</script>
<script id="operator-row-polish-v16">
/* v16: remove duplicated operator labels and put Here: on a new line. */
(function(){
  function opByName(name){
    const raw=String(name||'').trim();
    if(!raw || raw==='—' || raw==='all active OPs') return null;
    const lower=raw.toLowerCase();
    return (OPERATORS||[]).find(o =>
      String(o.id||'').toLowerCase()===lower ||
      (o.aliases||[]).some(a=>String(a).toLowerCase()===lower) ||
      String(o.label||'').toLowerCase()===lower
    ) || null;
  }
  function shortOp(o){ return (o && ((o.aliases && o.aliases[0]) || o.id)) || ''; }
  function cleanTitle(o){
    let title = String((o && (o.label || o.id)) || '');
    const short = shortOp(o);
    if(short){
      const escaped = short.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      title = title.replace(new RegExp('^\\s*' + escaped + '\\s*[—–-]\\s*','i'), '');
      title = title.replace(new RegExp('^\\s*' + escaped + '\\s+','i'), '');
    }
    return title || short || '';
  }
  function sentence(s){
    s = String(s || '').trim();
    if(!s) return '';
    return /[.!?]$/.test(s) ? s : s + '.';
  }
  function opText(o, context){
    const title = cleanTitle(o);
    const desc = [sentence(o.plain), sentence(o.operation)].filter(Boolean).join(' ');
    const here = context ? `<span class="hereLine"><em>Here:</em> in “${esc(context)}”, it acts on ${esc(o.acts_on || o.input || 'the live burden')} and should produce ${esc(o.delta || 'a state delta')}.</span>` : '';
    return `<span class="opTitle">${esc(title)}</span>: <span class="opDesc">${esc(desc)}</span>${here}`;
  }
  window.operatorExplainBlock = function(arr, context){
    const ops=(arr||[]).map(x=>opByName(x)).filter(Boolean);
    if(!ops.length) return '';
    return `<div class="opExplainBlock"><h3>Operators / TTP explained in this context</h3>${
      ops.map(o=>`<div class="opExplainRow"><button class="opChip" onclick="goOperator('${esc(o.id)}')">${esc(shortOp(o))}</button><span class="opDash">—</span><div class="opText">${opText(o, context)}</div></div>`).join('')
    }</div>`;
  };

  // Re-render the active concept/relation so the visible page updates immediately.
  document.addEventListener('DOMContentLoaded', function(){
    setTimeout(function(){
      const activeConcept = document.querySelector('#conceptList .conceptBtn.active');
      const cid = activeConcept?.dataset?.cid || ((activeConcept?.getAttribute('onclick')||'').match(/selectConcept\('([^']+)'/)||[])[1];
      const activeSub = document.querySelector('.subtab.active')?.textContent || '';
      if(activeSub.includes('Concept') && cid && typeof selectConcept === 'function') selectConcept(cid, activeConcept);
      const activeRel = document.querySelector('.relationList .relationBtn.active');
      const rid = activeRel?.dataset?.rid || ((activeRel?.getAttribute('onclick')||'').match(/selectRelation\('([^']+)'/)||[])[1];
      if(activeSub.includes('Relations') && rid && typeof selectRelation === 'function') selectRelation(rid, activeRel);
    }, 25);
  });
})();
</script>
<script id="final-state-and-left-column-sot-v18">
/* v18 ACID pass: final-state concept + shared left-column behavior + field/token navigation. */
(function(){
  const FIELD18 = {
    D0:{concept:'D0', key:'D0'}, 'D₀':{concept:'D0', key:'D0'},
    Psi:{concept:'Psi', key:'Psi'}, 'Ψᴺ':{concept:'Psi', key:'Psi'},
    N:{concept:'N', key:'N'}, m:{concept:'m', key:'m'},
    tau:{concept:'tau', key:'tau'}, 'τ':{concept:'tau', key:'tau'},
    sigma:{concept:'sigma', key:'sigma'}, 'σ':{concept:'sigma', key:'sigma'},
    xi:{concept:'xi', key:'xi'}, 'ξ':{concept:'xi', key:'xi'},
    omega:{concept:'omega', key:'omega'}, 'Ω':{concept:'omega', key:'omega'},
    mu:{concept:'mu', key:'mu'}, 'μ':{concept:'mu', key:'mu'},
    kappa:{concept:'kappa', key:'kappa'}, 'κ':{concept:'kappa', key:'kappa'},
    H:{concept:'H', key:'H'}, IR:{concept:'IR', key:'IR'},
    burden:{concept:'burden', key:'burden'}, 'ⁿB':{concept:'burden', key:'burden'},
    submoves:{concept:'submoves', key:'submoves'},
    Land:{concept:'Land', key:'Land'},
    deltaB:{concept:'deltaB', key:'deltaB'}, 'ΔⁿB':{concept:'deltaB', key:'deltaB'},
    deltaK:{concept:'deltaK', key:'deltaK'}, 'Δκ':{concept:'deltaK', key:'deltaK'},
    nablaDot:{concept:'nablaDot', key:'nablaDot'}, '∇·':{concept:'nablaDot', key:'nablaDot'},
    nablaCross:{concept:'nablaCross', key:'nablaCross'}, '∇×':{concept:'nablaCross', key:'nablaCross'},
    delDot:{concept:'delDot', key:'delDot'}, 'del-dot':{concept:'delDot', key:'delDot'},
    delCross:{concept:'delCross', key:'delCross'}, 'del-cross':{concept:'delCross', key:'delCross'},
    fieldDiagnostics:{concept:'nablaDot', key:'fieldDiagnostics'},
    R:{concept:'R', key:'R'},
    C:{concept:'collapse', key:'C'}, '𝒞(Ψᴺ)':{concept:'collapse', key:'C'},
    final:{concept:'finalState', key:'final'},
    'N_fiṭrī ∧ ʿaql ṣarīḥ':{concept:'finalState', key:'final'},
    nextB:{concept:'decision', key:'nextB'}, 'ⁿ⁺¹B':{concept:'decision', key:'nextB'}
  };
  function extractCallArg(raw, fnName){
    raw = String(raw || '');
    const needle = fnName + "('";
    const start = raw.indexOf(needle);
    if(start < 0) return null;
    const rest = raw.slice(start + needle.length);
    const end = rest.indexOf("'");
    return end >= 0 ? rest.slice(0, end) : null;
  }
  function f(raw){ return FIELD18[String(raw||'').trim()] || null; }

  function ensureConcept(id, obj){
    if(!Array.isArray(CONCEPTS)) return;
    if(!CONCEPTS.some(c => c.id === id)) CONCEPTS.push(obj);
  }
  function ensureFinalConcepts(){
    ensureConcept('H', {
      id:'H',
      name:'H held set',
      type:'runtime control state',
      summary:'Live but unreleased material carried through burden cycles.',
      definition:'H is the held set: input-anchored material that remains live but is not yet released because a prior burden, source-status issue, register, or gate condition controls the order.',
      runtime:'H prevents the model from dumping all available content while preserving what must be reread after Land(ⁿB) and Δκ.',
      fields:['R','Δκ','ⁿ⁺¹B'],
      operators:['P7','P2','M4','V10','output-release','recursive-state-transitions'],
      relations:['is reread by → R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)','holds → unreleased routes','prevents → premature Layer B release'],
      files:['output-release.md','recursive-state-transitions.md','diagnostic-render-contract.md'],
      case:'Doctrinal content may be held while a source-status burden is still live.',
      symbols:['H','R','deltaK','nextB']
    });
    ensureConcept('finalState', {
      id:'finalState',
      name:'N_fiṭrī ∧ ʿaql ṣarīḥ',
      type:'restorative terminal state',
      summary:'Restored fiṭrah and sound reason after governed noetic reread.',
      definition:'The terminal restoration target: the discourse is no longer governed by the deformation, imported criterion, source-status distortion, epistemic-grammar error, ontological-grammar error, or memetic stabilizer.',
      runtime:'This is not an always-printed slogan. It is licensed only after live burdens are landed, held, or marked partial, and after R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) permits restorative closure.',
      fields:['N','ξ','R','𝒞(Ψᴺ)'],
      operators:['P1','P7','R2','R3','V9','V6'],
      relations:['is licensed by → R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)','is endpoint of → 𝒞(Ψᴺ)','restores → fiṭrah / sound reason','is blocked by → live unlanded burdens'],
      files:['P1-fitrah-restoration.md','P7-restoration-stops.md','recursive-state-transitions.md','output-release.md'],
      case:'After the current burden lands and remaining material is stopped, held, or partialed, the response may release restorative closure toward fitrah and sound reason.',
      symbols:['final','C','N','xi','R']
    });
  }

  const previousRenderConcepts = window.renderConcepts;
  window.renderConcepts = function(){
    ensureFinalConcepts();
    if(typeof previousRenderConcepts === 'function') previousRenderConcepts();
  };

  // Patch the notation token for the final state so clicking it navigates, not merely highlights.
  function patchNotationTokenClicks(){
    document.querySelectorAll('.ntok').forEach(tok => {
      const k = tok.getAttribute('data-k') || '';
      if(k === 'final'){
        tok.classList.add('finalStateChip');
        tok.setAttribute('title','Open concept: restored fiṭrah and sound reason');
      }
    });
  }

  const prevGoConceptField = window.goConceptField;
  window.goConceptField = function(raw){
    ensureFinalConcepts();
    const info = f(raw);
    if(!info){
      if(typeof prevGoConceptField === 'function') return prevGoConceptField(raw);
      return;
    }
    // Switch to Theory / Concept graph.
    document.querySelectorAll('.tabsec').forEach(x=>x.classList.remove('active'));
    document.getElementById('theory')?.classList.add('active');
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    const theoryTab=[...document.querySelectorAll('.tab')].find(t=>t.textContent.includes('Theory'));
    if(theoryTab) theoryTab.classList.add('active');
    document.querySelectorAll('.subpanel').forEach(x=>x.classList.remove('active'));
    document.getElementById('sub-concepts')?.classList.add('active');
    document.querySelectorAll('.subtab').forEach(x=>x.classList.remove('active'));
    const conceptSub=[...document.querySelectorAll('.subtab')].find(t=>t.textContent.includes('Concept'));
    if(conceptSub) conceptSub.classList.add('active');
    const search=document.getElementById('conceptSearch');
    const type=document.getElementById('conceptType');
    if(search) search.value='';
    if(type) type.value='';
    if(typeof renderConcepts === 'function') renderConcepts();
    const btn=[...document.querySelectorAll('#conceptList .conceptBtn')].find(b=>{
      const cid=b.dataset?.cid || extractCallArg(b.getAttribute('onclick'), 'selectConcept');
      return cid === info.concept;
    });
    if(btn && typeof selectConcept === 'function'){
      selectConcept(info.concept, btn);
      btn.scrollIntoView({behavior:'smooth',block:'center'});
      setTimeout(()=>document.getElementById('conceptDetail')?.scrollIntoView({behavior:'smooth',block:'nearest'}),120);
    }
  };

  // If user clicks the final token in the notation board, open the final-state concept.
  document.addEventListener('click', function(ev){
    const tok = ev.target.closest && ev.target.closest('.ntok');
    if(tok && tok.getAttribute('data-k') === 'final'){
      ev.preventDefault();
      ev.stopPropagation();
      window.goConceptField('final');
      return;
    }
    const field = ev.target.closest && ev.target.closest('.readableFieldChip.clickable');
    if(field){
      const text = (field.querySelector('.fieldSym')?.textContent || field.querySelector('.nsym')?.textContent || '').trim();
      if(f(text)){
        ev.preventDefault();
        ev.stopPropagation();
        window.goConceptField(text);
      }
    }
  }, true);

  // Normalize left-column browser state after dynamic renders.
  function normalizeBrowsers(){
    ['#operatorGraphList','#conceptList','.relationList'].forEach(sel=>{
      document.querySelectorAll(sel).forEach(el=>{
        el.style.scrollbarGutter='stable';
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    ensureFinalConcepts();
    patchNotationTokenClicks();
    normalizeBrowsers();
    setTimeout(function(){
      ensureFinalConcepts();
      if(typeof renderConcepts === 'function') renderConcepts();
      patchNotationTokenClicks();
      normalizeBrowsers();
      const active=document.querySelector('#conceptList .conceptBtn.active') || document.querySelector('#conceptList .conceptBtn');
      const raw=active?.dataset?.cid || extractCallArg(active?.getAttribute('onclick'), 'selectConcept');
      if(raw && typeof selectConcept === 'function') selectConcept(raw, active);
    }, 0);
  });
})();
</script>
<script id="control-ontology-final-highlight-v19">
/* v19: richer control ontology, D₀ visible, and final state highlights ♥/ξ/Ω/μ/κ as well as N. */
(function(){
  function conceptById(id){ return (CONCEPTS||[]).find(c => c.id === id); }
  function ensureConcept(id, obj){
    if(!Array.isArray(CONCEPTS)) return;
    const existing = conceptById(id);
    if(!existing) CONCEPTS.push(obj);
    else Object.assign(existing, obj);
  }

  function ensureV19Concepts(){
    ensureConcept('D0', {
      id:'D0',
      name:'D₀ surface discourse',
      type:'runtime control state',
      summary:'The initial utterance as a signal object, not merely a topic.',
      definition:'D₀ is the visible surface discourse: claim, doubt, slogan, objection, proof-packet, source request, or case input.',
      runtime:'Feeds the noetic signal-state Ψᴺ. It is decoded, not directly answered as an argument-bank cue.',
      fields:['Ψᴺ','IR','μ','σ','τ'],
      operators:['V1','reason-disambiguation','FPD','P2'],
      relations:['encodes → Ψᴺ','is typed by → IR','can carry → μ','may install → τ/σ'],
      files:['SKILL.md','diagnostic-ir.md','framework-pipeline.md'],
      case:'“Only empirical evidence counts” is D₀ before it is typed as ξ/τ/μ pressure.',
      symbols:['D0','Psi']
    });

    ensureConcept('finalState', {
      id:'finalState',
      name:'N_fiṭrī ∧ ʿaql ṣarīḥ',
      type:'restorative terminal state',
      summary:'Restored fiṭrah and sound reason after governed noetic reread.',
      definition:'The terminal restoration target: the discourse is no longer governed by deformation, imported criterion, source-status distortion, epistemic-grammar error, ontological-grammar error, memetic stabilizer, or unresolved dependency radius.',
      runtime:'Licensed only after live burdens are landed, held, or marked partial, and after R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) permits restorative closure.',
      fields:['N','ξ','Ω','μ','κ','R','𝒞(Ψᴺ)'],
      operators:['P1','P7','R2','R3','V9','V6','M9','FPD'],
      relations:['is licensed by → R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)','is endpoint of → 𝒞(Ψᴺ)','restores → N / ξ / Ω / μ ordering','requires κ → resolved/held/partialed dependencies'],
      files:['P1-fitrah-restoration.md','P7-restoration-stops.md','recursive-state-transitions.md','output-release.md'],
      case:'After ♥, ξ, Ω, μ, and κ disorder are resolved, held, or partialed, the response may release restorative closure toward fiṭrah and sound reason.',
      symbols:['final','C','N','xi','omega','mu','kappa','R']
    });
  }

  const ORDER = ['D0','Psi','IR','N','m','tau','sigma','xi','omega','mu','kappa','H','burden','submoves','Land','deltaB','deltaK','nablaDot','nablaCross','delDot','delCross','R','LandR','decision','collapse','finalState','layerA','layerB'];
  const priorRenderConcepts = window.renderConcepts;
  window.renderConcepts = function(){
    ensureV19Concepts();
    const q=(document.getElementById('conceptSearch')?.value||'').toLowerCase();
    const t=document.getElementById('conceptType')?.value||'';
    const sorted=[...(CONCEPTS||[])].sort((a,b)=>{
      const ai=ORDER.indexOf(a.id), bi=ORDER.indexOf(b.id);
      return (ai===-1?999:ai)-(bi===-1?999:bi) || String(a.name).localeCompare(String(b.name));
    });
    const arr=sorted.filter(c=>(!t||c.type===t)&&JSON.stringify(c).toLowerCase().includes(q));
    const list=document.getElementById('conceptList');
    if(!list) return;
    list.innerHTML=arr.map((c,i)=>`<button class="conceptBtn ${i===0?'active':''}" data-cid="${esc(c.id)}" onclick="selectConcept('${esc(c.id)}',this)"><span class="entityType">${esc(c.type)}</span><br><strong>${esc(c.name)}</strong><br><span class="small">${esc(c.summary)}</span></button>`).join('');
    if(arr[0] && typeof selectConcept === 'function') selectConcept(arr[0].id, list.querySelector('.conceptBtn'));
  };

  const priorGoConceptField = window.goConceptField;
  window.goConceptField = function(raw){
    ensureV19Concepts();
    if(raw === 'final' || raw === 'N_fiṭrī ∧ ʿaql ṣarīḥ'){
      document.querySelectorAll('.tabsec').forEach(x=>x.classList.remove('active'));
      document.getElementById('theory')?.classList.add('active');
      document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
      const theoryTab=[...document.querySelectorAll('.tab')].find(t=>t.textContent.includes('Theory'));
      if(theoryTab) theoryTab.classList.add('active');
      document.querySelectorAll('.subpanel').forEach(x=>x.classList.remove('active'));
      document.getElementById('sub-concepts')?.classList.add('active');
      document.querySelectorAll('.subtab').forEach(x=>x.classList.remove('active'));
      const conceptSub=[...document.querySelectorAll('.subtab')].find(t=>t.textContent.includes('Concept'));
      if(conceptSub) conceptSub.classList.add('active');
      const search=document.getElementById('conceptSearch'); if(search) search.value='';
      const type=document.getElementById('conceptType'); if(type) type.value='';
      renderConcepts();
      const btn=[...document.querySelectorAll('#conceptList .conceptBtn')].find(b=>b.dataset?.cid==='finalState');
      if(btn && typeof selectConcept==='function'){
        selectConcept('finalState', btn);
        btn.scrollIntoView({behavior:'smooth',block:'center'});
      }
      return;
    }
    if(typeof priorGoConceptField === 'function') return priorGoConceptField(raw);
  };

  document.addEventListener('DOMContentLoaded', function(){
    ensureV19Concepts();
    setTimeout(function(){
      if(typeof renderConcepts === 'function') renderConcepts();
    }, 0);
  });
})();
</script>
<script id="pipeline-depth-restoration-v20">
/* v20: ACID/SOT/DRY deep pipeline renderer restoring index9's missing internal sections. */
(function(){
  const PIPELINE_DEEP = {
    current: {
      source: {
        accent:'var(--blue)',
        intro:'Current repo boundary: canonical atomized source compiles into generated runtime. This stage explains what the user runs versus what maintainers patch.',
        cards:[
          {title:'Atomic source / compiled runtime', wide:true, items:[
            ['atomics','canonical source files under atomics/skill/'],
            ['skill/','generated compiled runtime package'],
            ['map','compiled-module-map resolves module IDs to bundled runtime locations'],
            ['guard','bundle availability is not owner activation']
          ]},
          {title:'Current invariant', wide:true, cls:'deepGood', items:[
            ['SOT','edit atomics, regenerate skill/'],
            ['ID','original module IDs remain operative identities'],
            ['scope','repo/dev harness stays outside canonical package']
          ]}
        ]
      },
      input: {
        accent:'var(--blue)',
        intro:'This restores the old index9 Input panel: surface discourse is not yet the target. The system first reads what the utterance is carrying.',
        cards:[
          {title:'Input is not the target yet', wide:true, items:[
            ['“','claims, objections, doubts, questions'],
            ['τ','criteria / tribunals being installed'],
            ['σ','source-status and testimony posture'],
            ['♡','register: grief, identity, performance, truth-seeking'],
            ['↻','recurring slogans or memetic patterns']
          ]},
          {title:'Gate before rebuttal', wide:true, cls:'deepWarn', text:'Direct content release before diagnosis is an architecture failure. The visible proposition may be downstream of a noetic blocker.'}
        ]
      },
      noetic: {
        accent:'var(--green)',
        intro:'This restores the old index9 Noetic / Meta-Noetic Read: proper-function orientation and memetic object-domain are both visible before IR.',
        cards:[
          {title:'Proper-functional noetic structure', wide:true, items:[
            ['F','fiṭrah orientation: sound, impaired, blocked, underdetermined'],
            ['E','epistemic environment: whether faculties operate under fitting conditions'],
            ['R','reason role: sound reason, reason-as-tribunal, pseudo-neutral, inherited'],
            ['T','testimony posture: trusted, demoted, flattened, suspicious, held'],
            ['Ø','defeaters / deformation: what prevents proper recognition or assent']
          ]},
          {title:'Meta-noetic memetics as object-domain', wide:true, items:[
            ['m','memetic node / recurring claim-shape'],
            ['τ','criterion transfer / imported tribunal'],
            ['LB','load-bearing node that regenerates downstream claims'],
            ['CR','collapse radius: what must be re-evaluated if node clears']
          ]},
          {title:'Operational boundary', cls:'deepGood', text:'Meta-noetic memetics does not create a decorative extra pass. It becomes real only through IR fields, suppression, H, owner/TTP choice, collapse radius, or R.'},
          {title:'Design-space invariant', cls:'deepGood', text:'The framework is engineered before the selected noetic structure is known. Each owner family must support possible live structures; runtime selection activates only bounded owners.'}
        ]
      },
      ir: {
        accent:'var(--cyan)',
        intro:'This restores the old DSL/IR & Gated Governance card: diagnostic reduction order, compact control surface, and gate/routing/owner selection.',
        cards:[
          {title:'Diagnostic reduction order', full:true, flow:['core axes','Phase 2','overlays','validated IR','gate checks','routing']},
          {title:'Current DSL / IR control surface', wide:true, formula:'IR(N,m,τ,σ)', items:[
            ['N','operative noetic frame'],
            ['m','memetic claim / node'],
            ['τ','tribunal / criterion'],
            ['σ','source-status'],
            ['LB','load-bearing node'],
            ['CR','collapse radius'],
            ['H','held set'],
            ['B','current live burden']
          ]},
          {title:'Gate → routing → owner → Layer B', wide:true, flow:['Gate: fields, consistency, suppression, P7 stops','Precedence: concealment / DO / deformation / reason / foreign premise / LB','Owner select: active owner only after diagnosis','Layer B: bounded target / operation / result']}
        ]
      },
      owner: {
        accent:'var(--violet)',
        intro:'Current owner execution is already required by the repo, but v19 had it too compressed in the pipeline. This stage shows owner activation as control logic.',
        cards:[
          {title:'Owner activation floor', wide:true, flow:['validated IR','matched owner source','target','operation','result','state delta']},
          {title:'What must be true', items:[
            ['live','owner is structurally live, not just available in a bundle'],
            ['body','owner body / section is actually loaded'],
            ['local','operator performs local work under B'],
            ['delta','work contributes to Land(ⁿB) or is held/partial']
          ]},
          {title:'Failure blocked', cls:'deepWarn', items:[
            ['×','route chain treated as current bounded operator'],
            ['×','bundle co-location treated as activation'],
            ['×','generic prose replacing owner operation']
          ]}
        ]
      },
      reread: {
        accent:'var(--orange)',
        intro:'This restores the old Burden Cycle & Release card: burden cycle, decision, correct recurse, restorative response, and held downstream material.',
        cards:[
          {title:'Burden cycle', wide:true, formula:'B → {s₁...sₙ} → Land(ⁿB) → ΔⁿB/Δκ → ∇·/∇× field state → R(H,Δ)', text:'Submoves are not burden-cycles. A new B is licensed only after burden landing, target-explicit field diagnostics, and state/noetic re-read.'},
          {title:'Decision', wide:true, decision:true},
          {title:'Correct recurse', cls:'deepGood', text:'RECURSE returns to diagnostic/routing re-entry for the next input-anchored live burden. It does not point to Restorative Response.'},
          {title:'Restorative response', wide:true, items:[
            ['F','restored fiṭrah / proper-function orientation'],
            ['⚖','restored criterion order'],
            ['σ','corrected source-status placement'],
            ['Ø','relieved deformation / concealment'],
            ['H','held downstream material named where needed']
          ]}
        ]
      }
    },
    target: {
      't-input': {
        accent:'var(--blue)',
        intro:'schema-light register bridge keeps the input discipline but names the signal object explicitly as D₀.',
        cards:[
          {title:'D₀ input object', wide:true, items:[
            ['D₀','surface discourse as signal object'],
            ['source','origin of claim / authority / semantic default'],
            ['message','claim, slogan, proof-packet, objection'],
            ['encoding','labels, examples, school identity, proof-denominators'],
            ['noise','deformation, equivocation, identity pressure, proof-method narrowing']
          ]},
          {title:'Before next stage', cls:'deepGood', text:'D₀ must be read as encoded signal, not sent directly to an argument-bank response.'}
        ]
      },
      't-psi': {
        accent:'var(--green)',
        intro:'schema-light register bridge upgrades the noetic read into an encoded noetic signal-state Ψᴺ with explicit structural registers.',
        cards:[
          {title:'Ψᴺ signal-state', wide:true, formula:'Ψᴺ⟨N,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩'},
          {title:'Proper-function read retained', wide:true, items:[
            ['F','fiṭrah / proper-function orientation'],
            ['E','epistemic environment'],
            ['R','reason role'],
            ['T','testimony posture'],
            ['Ø','defeater / deformation status']
          ]},
          {title:'New structural registers', wide:true, items:[
            ['ξ','epistemic / warrant grammar'],
            ['Ω','ontological grammar'],
            ['μ','meta-noetic memetic carrier / stabilizer'],
            ['κ','collapse radius / downstream dependency set']
          ]},
          {title:'Operational boundary', cls:'deepTarget', text:'♥/ξ/Ω/μ/κ are not decorative. They matter only when they affect IR, suppression, H, owner choice, Δκ, or R.'}
        ]
      },
      't-ir': {
        accent:'var(--cyan)',
        intro:'schema-light register bridge keeps IR compact but makes optional registers visible when structurally live.',
        cards:[
          {title:'Expanded optional-register IR', full:true, formula:'IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)'},
          {title:'Diagnostic reduction order', full:true, flow:['D₀','Ψᴺ','core axes','Phase 2','overlays','validated IR','gate checks','routing']},
          {title:'Gate checks', wide:true, items:[
            ['fields','required fields and consistency'],
            ['σ','source-status non-equivalence'],
            ['H','held material named and governed'],
            ['P7','stop/hold/recurse/partial controls'],
            ['owner','only bounded owner activation after gate']
          ]}
        ]
      },
      't-owner': {
        accent:'var(--violet)',
        intro:'schema-light register bridge makes the owner/TTP submove shape explicit and auditable.',
        cards:[
          {title:'Operator signature', full:true, formula:'ⁿBᵢ[OP] : target → operation → result → ΔⁿB{♥,ξ,Ω,σ,μ} / Δκ'},
          {title:'Register-to-owner examples', wide:true, items:[
            ['ξ','V2 / FPD / M1 / R1 / R3 / V10'],
            ['Ω','M9 / V8 / V9 / M8 / V12'],
            ['μ','FPD / M1-P / F2 / V7 / V11'],
            ['κ','P7 / M8 / any load-bearing owner that changes dependencies']
          ]},
          {title:'Failure blocked', cls:'deepWarn', text:'A TTP label is not execution. It must perform target → operation → result and produce a traceable register/state/dependency delta.'}
        ]
      },
      't-burden': {
        accent:'var(--orange)',
        intro:'schema-light register bridge normalizes strict burden notation and separates burden landing from next-burden licensing.',
        cards:[
          {title:'Strict burden cycle', full:true, formula:'ⁿB → {ⁿB₁...ⁿBₖ} → Land(ⁿB) → ΔⁿB'},
          {title:'Deltas', wide:true, items:[
            ['ΔⁿB','local burden-state delta'],
            ['Δκ','downstream dependency / collapse-radius delta'],
            ['Δξ','epistemic grammar changed'],
            ['ΔΩ','ontological grammar changed'],
            ['Δμ','memetic carrier/stabilizer changed']
          ]},
          {title:'Layer B release', wide:true, text:'Public answer remains bounded by the current burden. Held material is named, not dumped.'}
        ]
      },
      't-decision': {
        accent:'var(--red)',
        intro:'schema-light register bridge extends the decision gate to R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ), then only licenses next burden or final restoration if warranted.',
        cards:[
          {title:'Reread gate', full:true, formula:'R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) ⊢ STOP | HOLD | PARTIAL | ⁿ⁺¹B'},
          {title:'Decision', wide:true, decision:true},
          {title:'Correct recurse', cls:'deepGood', text:'ⁿ⁺¹B is licensed only if a distinct live τ/ξ/Ω/σ/κ remains. Same-burden facets stay as ⁿBᵢ submoves.'},
          {title:'Noetic collapse / restoration', wide:true, formula:'𝒞(Ψᴺ) → N_fiṭrī ∧ ʿaql ṣarīḥ', items:[
            ['N','restored noetic frame / fitrah orientation'],
            ['ξ','warrant grammar repaired'],
            ['Ω','ontological grammar repaired or held'],
            ['μ','memetic stabilizer broken or reordered'],
            ['κ','dependency radius resolved / held / partialed']
          ]}
        ]
      }
    }
  };

  function deepList(items){
    return `<ul class="deepList">${(items||[]).map(([k,v])=>`<li><span class="deepKey">${esc(k)}</span><span>${esc(v)}</span></li>`).join('')}</ul>`;
  }
  function deepFlow(items){
    return `<div class="deepFlow">${(items||[]).map((x,i)=>`${i?'<span class="deepArrow">→</span>':''}<span class="deepPill">${esc(x)}</span>`).join('')}</div>`;
  }
  function decisionBlock(){
    return `<div class="decisionMini">
      <div style="color:var(--red)">■<br>STOP</div>
      <div style="color:var(--orange)">Ⅱ<br>HOLD</div>
      <div style="color:var(--green)">↺<br>RECURSE</div>
      <div style="color:var(--violet)">◌<br>PARTIAL</div>
    </div>`;
  }
  function deepCard(c, accent){
    const cls = `deepCard ${c.wide?'wide':''} ${c.full?'full':''} ${c.cls||''}`;
    return `<div class="${cls}" style="--accent:${accent}">
      <h4>${esc(c.title)}</h4>
      ${c.formula?`<div class="deepFormula">${esc(c.formula)}</div>`:''}
      ${c.text?`<p>${esc(c.text)}</p>`:''}
      ${c.items?deepList(c.items):''}
      ${c.flow?deepFlow(c.flow):''}
      ${c.decision?decisionBlock():''}
    </div>`;
  }

  const previousSelectStage = window.selectStage;
  window.selectStage = function(gridId, detailId, id, el){
    document.querySelectorAll(`#${gridId} .stageCard`).forEach(x=>x.classList.remove('active'));
    if(el) el.classList.add('active');
    const data = gridId === 'currentPipeline' ? CURRENT_STAGES : TARGET_STAGES;
    const s = data.find(x => x.id === id);
    if(!s) return;
    const group = gridId === 'currentPipeline' ? 'current' : 'target';
    const d = PIPELINE_DEEP[group][id];
    const detail = document.getElementById(detailId);
    if(!detail) return;
    if(!d){
      return previousSelectStage ? previousSelectStage(gridId, detailId, id, el) : null;
    }
    detail.innerHTML = `<h3>${esc(s.title)}</h3>
      <div class="pipelineDeepIntro">${esc(d.intro)}</div>
      <div class="detailGrid">${box('Receives',s.receives)}${box('Detects',s.detects)}${box('Writes / constrains',s.writes)}${box('Before next stage',s.next)}${box(gridId==='currentPipeline'?'Bridge overlay on retained spine':'Failure looks like',s.gap||s.failure)}</div>
      <div class="deepStageGrid">${d.cards.map(c=>deepCard(c,d.accent)).join('')}</div>`;
  };

  document.addEventListener('DOMContentLoaded', function(){
    setTimeout(function(){
      const currentBtn=[...document.querySelectorAll('#currentPipeline .stageCard')].find(b => (b.getAttribute('onclick')||'').includes("'input'")) || document.querySelector('#currentPipeline .stageCard');
      if(currentBtn) selectStage('currentPipeline','currentDetail', (currentBtn.getAttribute('onclick')||'').includes("'input'") ? 'input' : 'source', currentBtn);
      const targetBtn=[...document.querySelectorAll('#targetPipeline .stageCard')].find(b => (b.getAttribute('onclick')||'').includes("'t-input'")) || document.querySelector('#targetPipeline .stageCard');
      if(targetBtn) selectStage('targetPipeline','targetDetail','t-input',targetBtn);
    }, 0);
  });
})();
</script>


<script id="static-pipeline-interactivity-v33">
(function(){
  const STATIC_STAGE_MAP = {
    current: {
      input: {
        title:'Input / Surface Discourse',
        subtitle:'Surface discourse is decoded before rebuttal.',
        ids:['input']
      },
      noetic: {
        title:'Noetic / Meta-Noetic Read',
        subtitle:'Proper-function orientation, memetic node, load-bearing node, and collapse radius are read before IR.',
        ids:['noetic']
      },
      irOwner: {
        title:'DSL / IR & Gated Governance',
        subtitle:'IR/gate/routing and owner activation belong to this visible governance stage.',
        ids:['ir','owner']
      },
      reread: {
        title:'Burden Cycle & Release',
        subtitle:'Burden landing, held material, reread, and STOP/HOLD/RECURSE/PARTIAL decision.',
        ids:['reread']
      }
    },
    target: {
      input: {
        title:'D₀ / Surface Signal',
        subtitle:'The input becomes an explicit surface-discourse signal object.',
        ids:['t-input']
      },
      psi: {
        title:'Ψᴺ / Noetic Signal-State',
        subtitle:'The noetic read becomes Ψᴺ with structural registers where live.',
        ids:['t-psi']
      },
      ir: {
        title:'DSL / IR & Gated Governance',
        subtitle:'Schema-light ♥/ξ/Ω/μ/κ registers enter the compact control surface when live.',
        ids:['t-ir']
      },
      ownerRelease: {
        title:'Owner/TTP + Δ / Field Diagnostics / Reread',
        subtitle:'Owner-backed submoves, strict burden notation, Land(ⁿB), and R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) form the release cycle.',
        ids:['t-owner']
      },
      collapse: {
        title:'Noetic Collapse / Restoration',
        subtitle:'Constrained noetic resolution and restoration occur only after reread consumes the state delta and collapse radius.',
        ids:['t-collapse']
      }
    }
  };

  const SUBSTAGE_MAP = {
    target: {
      input: {
        'encoded-signal': {
          title:'D₀ / Surface Signal — Input as encoded signal',
          subtitle:'The visible discourse is read as signal before any rebuttal is released.',
          receives:['Surface claim, slogan, objection, proof packet, or source request.','Source, message, encoding, channel/noise, and visible register cues.'],
          detects:['Whether the input is a proposition, source-status request, criterion signal, or register-bearing carrier.','♥ pressure such as grief, identity, performance, truth-seeking, mixed posture, or unclear posture.'],
          writes:['D₀ as an explicit surface-discourse object.','Initial source/message/encoding/noise features for Ψᴺ reconstruction.'],
          next:['Pass the encoded signal into Ψᴺ rather than answering the topic directly.'],
          failure:['Topic-label dispatch before the surface signal is decoded.']
        },
        'no-direct-rebuttal': {
          title:'D₀ / Surface Signal — Still no direct rebuttal',
          subtitle:'Content release is blocked until the signal has been decoded into the noetic field.',
          receives:['A tempting content-level answer before diagnostic reduction.','A proposition that may be downstream of criterion, source-status, or register pressure.'],
          detects:['Whether a direct answer would answer the visible claim while missing the governing noetic burden.','Whether the surface wording is carrying hidden tribunal, source, or affective pressure.'],
          writes:['A hold on direct rebuttal.','A requirement to decode D₀ into Ψᴺ before burden release.'],
          next:['Move to Ψᴺ / Noetic Signal-State with the encoded signal preserved.'],
          failure:['Winning a surface proposition while leaving the governing deformation or criterion untouched.']
        }
      },
      psi: {
        'proper-functional-read': {
          title:'Ψᴺ / Noetic Signal-State — Proper-functional read',
          subtitle:'The case is read for fitrah, epistemic environment, reason role, testimony posture, and defeater status.',
          receives:['D₀ plus source/message/register features.','Current noetic-read evidence from discourse, profile, and source-status signals.'],
          detects:['Whether recognition is functioning, occluded, suppressed, or underdetermined.','Whether reason and testimony are playing their sound role or an imported role.'],
          writes:['Proper-function orientation values feeding Ψᴺ.','Initial constraints on tone, hold, and owner eligibility.'],
          next:['Continue to structural registers only where they affect control behavior.'],
          failure:['Treating the case as a topic answer without reading proper-function posture.']
        },
        'structural-registers': {
          title:'Ψᴺ / Noetic Signal-State — Structural registers',
          subtitle:'Live N, m, τ, σ, ♥, ξ, Ω, μ, κ, and H values are asserted, held, or marked underdetermined.',
          receives:['Proper-functional read plus any live source, warrant, ontology, memetic, closure, or held-material signals.'],
          detects:['Which registers govern the current burden and which remain held.','Whether κ/dependency radius or H/held material will affect later reread.'],
          writes:['Ψᴺ⟨N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩ as an encoded noetic signal-state.','Register constraints for IR, suppression, routing, Δκ, R, tone, and release posture.'],
          next:['Form DSL/IR only from registers that are live or explicitly held.'],
          failure:['Decorative register notation that does not change IR, owner choice, hold, reread, or release.']
        },
        'operational-boundary': {
          title:'Ψᴺ / Noetic Signal-State — Operational boundary',
          subtitle:'Registers govern only when they change execution state.',
          receives:['Candidate ♥/ξ/Ω/μ/κ signals from the noetic read.'],
          detects:['Whether a register affects IR, suppression, H, owner choice, Δκ, R, tone, burden sequencing, or release posture.'],
          writes:['Control-affecting registers into the next stage.','Non-governing notation back into explanation or reference status.'],
          next:['Only live or held registers enter DSL/IR and gate behavior.'],
          failure:['Symbol theater: printing registers that do not constrain execution.']
        }
      },
      ir: {
        'diagnostic-reduction-order': {
          title:'DSL / IR & Gated Governance — Diagnostic reduction order',
          subtitle:'The route opens only after D₀, Ψᴺ, core axes, Phase 2, overlays, and validated IR are in order.',
          receives:['Ψᴺ and triggered diagnostic passes.','Core axes, Phase 2 pass results, overlays, and held material.'],
          detects:['Whether diagnostic reduction is complete enough for dispatch.','Whether routing is trying to jump ahead of gate validation.'],
          writes:['A validated diagnostic reduction sequence.','Gate/routing eligibility constraints for the current burden.'],
          next:['Enter the DSL/IR control surface with validated structure.'],
          failure:['Route itinerary formed before diagnostic reduction is complete.']
        },
        'ir-control-surface': {
          title:'DSL / IR & Gated Governance — DSL / IR control surface',
          subtitle:'IR(N,m,τ,σ,♥,ξ,Ω,μ,κ) names control-affecting state, not a decorative schema.',
          receives:['Validated Ψᴺ registers and diagnostic outputs.'],
          detects:['Which N/m/τ/σ/♥/ξ/Ω/μ/κ values actually govern current burden behavior.','Whether source-status, warrant, ontology, register, or collapse-radius pressure is live.'],
          writes:['Validated IR values for gate, precedence, owner selection, and release posture.','Held or underdetermined values that must remain visible to reread.'],
          next:['Run gate checks and routing precedence before owner/TTP activation.'],
          failure:['Treating IR as optional, retrospective, or merely explanatory.']
        },
        'gate-owner-layerb': {
          title:'DSL / IR & Gated Governance — Gate → Precedence → Owner Select → Layer B',
          subtitle:'Gate and routing select one bounded owner-backed operation before Layer B release.',
          receives:['Validated IR, held material, routing precedence, and owner catalogue constraints.'],
          detects:['Whether gate checks pass, what route has highest eligible ∇ pressure, and which owner can act.','Whether source-status or P7 discipline blocks release.'],
          writes:['Current bounded operator and matched owner/TTP identity.','Layer B entry permission or HOLD/PARTIAL/RECURSE gating.'],
          next:['Execute owner-backed submoves under the current ⁿB.'],
          failure:['Owner name printed without gate, precedence, or bounded operation.']
        }
      },
      ownerRelease: {
        'operator-signature': {
          title:'Owner/TTP + Δ / Field Diagnostics / Reread — Operator signature',
          subtitle:'A submove is valid only as target → operation → result → ΔⁿB / Δκ.',
          receives:['Validated IR and the current live ⁿB.','A selected owner/TTP with a bounded target.'],
          detects:['Whether the owner actually performs an operation instead of being name-dropped.','Which register or burden state the operation can change.'],
          writes:['ⁿBᵢ[OP] with target, operation, result, and transition effect.','A contribution to ΔⁿB and possibly Δκ.'],
          next:['Accumulate owner-backed submoves until the current burden can land or be held/partialed.'],
          failure:['TTP label without target, operation, result, or state delta.']
        },
        'strict-burden-cycle': {
          title:'Owner/TTP + Δ / Field Diagnostics / Reread — Strict burden cycle',
          subtitle:'Same-burden submoves land ⁿB before any new ⁿ⁺¹B is licensed.',
          receives:['Current ⁿB and materially necessary submoves {ⁿB₁...ⁿBₖ}.'],
          detects:['Whether submoves are facets of the same burden or a distinct next-burden candidate.','Whether Δκ changes downstream dependency radius.'],
          writes:['Land(ⁿB), ΔⁿB, and Δκ where dependency radius changes.','A blocked route-chain if the same burden is being split cosmetically.'],
          next:['Run target-explicit ∇·/∇× diagnostics over the Δ-produced field state.'],
          failure:['Treating every submove or route leg as a new burden-cycle.']
        },
        'reread-gate': {
          title:'Owner/TTP + Δ / Field Diagnostics / Reread — Reread gate',
          subtitle:'After Δ lands, field diagnostics and R(H,Δ) reread the whole live field.',
          receives:['ΔⁿB, Δκ, H, live registers, and target-explicit ∇·/∇× diagnostics.'],
          detects:['Residual outward pressure, circular dependency, held material, and remaining live burdens.','Whether LoopBreak is needed, null, held, or licensed.'],
          writes:['R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ) as the refreshed field state.','A grounded basis for STOP, HOLD, RECURSE, PARTIAL, or COMPLETE.'],
          next:['Move to decision only after diagnostics are cleared, integrated, held, or carried into RECURSE/PARTIAL.'],
          failure:['Closure by checklist depletion instead of field-state reread.']
        },
        decision: {
          title:'Owner/TTP + Δ / Field Diagnostics / Reread — Decision',
          subtitle:'The decision is a closure/release state, not a decorative label.',
          receives:['Reread output, residual pressure status, held material, and next-burden eligibility.'],
          detects:['Whether STOP, HOLD, RECURSE, PARTIAL, or COMPLETE is licensed.','Whether ⁿ⁺¹B requires a distinct live τ/ξ/Ω/σ/κ.'],
          writes:['The licensed next control state.','A proof that same-burden facets remain inside ⁿB unless a distinct next burden is live.'],
          next:['Either recurse to the next bounded burden or move toward 𝒞(Ψᴺ) and public release.'],
          failure:['Premature COMPLETE, unlicensed RECURSE, or same-burden facets treated as new burdens.']
        }
      },
      collapse: {
        'constrained-resolution': {
          title:'Noetic Collapse / Restoration — Constrained resolution',
          subtitle:'𝒞(Ψᴺ) is positive closure-field condition, not a checklist count.',
          receives:['Reread state with landed, held, partialed, or resolved burdens.','Register and κ/H status after diagnostics.'],
          detects:['Whether N_fiṭrī ∧ ʿaql ṣarīḥ is licensed in the agent execution field.','Whether residual ∇·/∇× pressure blocks final closure.'],
          writes:['𝒞(Ψᴺ) as constrained noetic resolution where licensed.','A restored frame that honors ♥, ξ, Ω, μ, κ, and held material boundaries.'],
          next:['Render a restorative response only after closure or explicit HOLD/PARTIAL discipline.'],
          failure:['Restoration printed before dependency radius, held routes, or noetic state are reread.']
        },
        'coupling-boundary': {
          title:'Noetic Collapse / Restoration — Coupling boundary',
          subtitle:'T_lang: Ψᴺ ⇢ Ψᴵ names public language release, not direct soul access.',
          receives:['A licensed response from the agent execution field Ψᴺ.','Diagnosed interlocutor field Ψᴵ inferred from discourse/profile/register/source-status evidence.'],
          detects:['Whether the public response preserves closure, register, and master deformation diagnosis.','Whether wording overclaims uptake, conversion, guidance, or access to the soul.'],
          writes:['A language-mediated coupling attempt toward Ψᴵ.','Explicit non-claim of guaranteed uptake or interlocutor acceptance.'],
          next:['Public/restorative render with no hidden live pressure and no guaranteed-uptake claim.'],
          failure:['Treating final language as direct rewrite of the interlocutor or proof of conversion.']
        }
      }
    }
  };

  function sourceFor(pipeline){
    return pipeline === 'current' ? CURRENT_STAGES : ARCHITECTURE_STAGES;
  }
  function stageById(pipeline,id){
    return sourceFor(pipeline).find(x => x.id === id);
  }
  function flatten(stages,key){
    const out=[];
    stages.forEach(s => (s[key]||[]).forEach(x => out.push(stages.length > 1 ? `${s.title}: ${x}` : x)));
    return out;
  }
  function list(items){
    if(!items.length) return '<p class="small">No explicit item.</p>';
    return `<ul>${items.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`;
  }
  function auditBox(title, items){
    return `<div class="v30-audit-box"><h4>${esc(title)}</h4>${list(items)}</div>`;
  }
  function renderAuditTrace(panel, config, failureTitle){
    panel.innerHTML = `<h3>${esc(config.title)}</h3>
      <p class="v30-detail-subtitle"><strong>Trace:</strong> ${esc(config.subtitle)}</p>
      <div class="v30-audit-grid">
        ${auditBox('Receives', config.receives || [])}
        ${auditBox('Detects', config.detects || [])}
        ${auditBox('Writes / constrains', config.writes || [])}
        ${auditBox('Before next stage', config.next || [])}
        ${auditBox(failureTitle, config.failure || config.gap || [])}
      </div>`;
  }
  function architectureCarouselStages(){
    return [...document.querySelectorAll('#architecture #canonical-architecture-runtime .v60-architecture-rail .v30-selectable-stage[data-pipeline="target"]')];
  }
  function architectureCarouselKey(){
    const active = document.querySelector('#architecture #canonical-architecture-runtime .v60-architecture-rail .v30-selectable-stage.v30-active[data-pipeline="target"]');
    return active?.getAttribute('data-stage-key') || architectureCarouselStages()[0]?.getAttribute('data-stage-key') || 'input';
  }
  function carouselPosition(index, selectedIndex, total){
    const offset = (index - selectedIndex + total) % total;
    if(offset === 0) return 'center';
    if(offset === 1) return 'next';
    if(offset === 2) return 'far-next';
    if(offset === total - 1) return 'prev';
    if(offset === total - 2) return 'far-prev';
    return 'far';
  }
  function applyArchitectureCarousel(key){
    const stages = architectureCarouselStages();
    if(!stages.length) return;
    const selectedIndex = Math.max(0, stages.findIndex(el => el.getAttribute('data-stage-key') === key));
    const selected = stages[selectedIndex];
    stages.forEach((el,index) => {
      const position = carouselPosition(index, selectedIndex, stages.length);
      const isSelected = position === 'center';
      const slot = el.closest('.v60-carousel-slot');
      el.setAttribute('data-carousel-position', position);
      el.setAttribute('aria-selected', isSelected ? 'true' : 'false');
      el.tabIndex = isSelected ? 0 : -1;
      el.classList.toggle('is-primary', isSelected);
      el.classList.toggle('is-preview', !isSelected);
      if(slot){
        slot.setAttribute('data-carousel-position', position);
        slot.classList.toggle('is-primary', isSelected);
        slot.classList.toggle('is-preview', !isSelected);
      }
      ['prev','next','far-prev','far-next','far'].forEach(name => {
        el.classList.toggle(`is-${name}`, position === name);
        if(slot) slot.classList.toggle(`is-${name}`, position === name);
      });
    });
    document.querySelectorAll('#architecture #canonical-architecture-runtime .v60-carousel-dot').forEach(dot => {
      const isCurrent = dot.getAttribute('data-carousel-target') === key;
      if(isCurrent) dot.setAttribute('aria-current','true');
      else dot.removeAttribute('aria-current');
    });
    const status = document.getElementById('architectureCarouselStatus');
    if(status && selected){
      const label = status.querySelector('.v60-carousel-status-label');
      if(label) label.textContent = `Stage ${selectedIndex + 1} of ${stages.length}`;
    }
  }
  function moveArchitectureCarousel(delta){
    const stages = architectureCarouselStages();
    if(!stages.length) return;
    const currentKey = architectureCarouselKey();
    const currentIndex = Math.max(0, stages.findIndex(el => el.getAttribute('data-stage-key') === currentKey));
    const nextIndex = (currentIndex + delta + stages.length) % stages.length;
    const nextKey = stages[nextIndex].getAttribute('data-stage-key');
    renderStaticStage('target', nextKey);
    stages[nextIndex].focus({preventScroll:true});
  }

  function renderStaticStage(pipeline,key){
    const config = STATIC_STAGE_MAP[pipeline]?.[key];
    if(!config) return;

    const stages = config.ids.map(id => stageById(pipeline,id)).filter(Boolean);
    if(!stages.length) return;

    const panelId = pipeline === 'current' ? 'currentStaticStageDetail' : 'targetStaticStageDetail';
    const panel = document.getElementById(panelId);
    if(!panel) return;

    document.querySelectorAll(`.v30-selectable-stage[data-pipeline="${pipeline}"]`).forEach(el => {
      el.classList.toggle('v30-active', el.getAttribute('data-stage-key') === key);
    });
    if(pipeline === 'target'){
      applyArchitectureCarousel(key);
    }
    document.querySelectorAll(`.v30-selectable-stage[data-pipeline="${pipeline}"] .v60-selectable-subcard`).forEach(el => {
      el.classList.remove('v60-subactive');
    });

    const finalKey = pipeline === 'current' ? 'gap' : 'failure';
    renderAuditTrace(panel, {
      title:config.title,
      subtitle:config.subtitle,
      receives:flatten(stages,'receives'),
      detects:flatten(stages,'detects'),
      writes:flatten(stages,'writes'),
      next:flatten(stages,'next'),
      [finalKey]:flatten(stages,finalKey)
    }, pipeline === 'current' ? 'Bridge overlay on retained spine' : 'Failure looks like');
  }

  function renderStaticSubstage(el){
    const stageEl = el.closest('.v30-selectable-stage');
    if(!stageEl) return;
    const pipeline = stageEl.getAttribute('data-pipeline');
    const stageKey = stageEl.getAttribute('data-stage-key');
    const subKey = el.getAttribute('data-substage-key');
    const config = SUBSTAGE_MAP[pipeline]?.[stageKey]?.[subKey];
    if(!config) return;

    const panelId = pipeline === 'current' ? 'currentStaticStageDetail' : 'targetStaticStageDetail';
    const panel = document.getElementById(panelId);
    if(!panel) return;

    document.querySelectorAll(`.v30-selectable-stage[data-pipeline="${pipeline}"]`).forEach(stage => {
      stage.classList.toggle('v30-active', stage === stageEl);
    });
    if(pipeline === 'target'){
      applyArchitectureCarousel(stageKey);
    }
    document.querySelectorAll(`.v30-selectable-stage[data-pipeline="${pipeline}"] .v60-selectable-subcard`).forEach(card => {
      card.classList.toggle('v60-subactive', card === el);
    });
    renderAuditTrace(panel, config, 'Failure looks like');
  }
  function attachArchitectureCarouselControls(){
    document.querySelectorAll('#architecture #canonical-architecture-runtime [data-carousel-action="prev"]').forEach(btn => {
      btn.addEventListener('click', () => moveArchitectureCarousel(-1));
    });
    document.querySelectorAll('#architecture #canonical-architecture-runtime [data-carousel-action="next"]').forEach(btn => {
      btn.addEventListener('click', () => moveArchitectureCarousel(1));
    });
    document.querySelectorAll('#architecture #canonical-architecture-runtime .v60-carousel-dot').forEach(dot => {
      dot.addEventListener('click', () => renderStaticStage('target', dot.getAttribute('data-carousel-target')));
    });
    document.querySelectorAll('#architecture #canonical-architecture-runtime .v60-architecture-rail').forEach(rail => {
      rail.addEventListener('keydown', ev => {
        if(ev.key === 'ArrowRight'){
          ev.preventDefault();
          moveArchitectureCarousel(1);
        }else if(ev.key === 'ArrowLeft'){
          ev.preventDefault();
          moveArchitectureCarousel(-1);
        }else if(ev.key === 'Home'){
          ev.preventDefault();
          const first = architectureCarouselStages()[0];
          if(first) renderStaticStage('target', first.getAttribute('data-stage-key'));
        }else if(ev.key === 'End'){
          ev.preventDefault();
          const stages = architectureCarouselStages();
          const last = stages[stages.length - 1];
          if(last) renderStaticStage('target', last.getAttribute('data-stage-key'));
        }
      });
    });
  }

  function attachStaticPipelineInteractivity(){
    document.querySelectorAll('.v30-selectable-stage').forEach(el => {
      const pipeline = el.getAttribute('data-pipeline');
      const key = el.getAttribute('data-stage-key');
      const handler = () => renderStaticStage(pipeline,key);
      el.addEventListener('click', handler);
      el.addEventListener('keydown', ev => {
        if(ev.key === 'Enter' || ev.key === ' '){
          ev.preventDefault();
          handler();
        }
      });
    });
    attachArchitectureCarouselControls();
    document.querySelectorAll('.v60-selectable-subcard').forEach(el => {
      const handler = ev => {
        ev.stopPropagation();
        renderStaticSubstage(el);
      };
      el.addEventListener('click', handler);
      el.addEventListener('keydown', ev => {
        if(ev.key === 'Enter' || ev.key === ' '){
          ev.preventDefault();
          ev.stopPropagation();
          renderStaticSubstage(el);
        }
      });
    });
    renderStaticStage('current','input');
    renderStaticStage('target','input');
  }

  document.addEventListener('DOMContentLoaded', attachStaticPipelineInteractivity);
})();
</script>

<script id="v40-theory-ordering">
(function(){
  const CONCEPT_ORDER = [
    'noetic','D0','Psi','N','m','tau','sigma','heart','xi','omega','mu','kappa','H',
    'IR','burden','LandR','decision','collapse','layerA','layerB','final'
  ];
  const RELATION_ORDER = [
    'rel-noetic-design','rel-noetic-selects-N','rel-D-Psi','rel-Psi-fields','rel-heart-release',
    'rel-Psi-IR','rel-xi-owner','rel-omega-owner','rel-mu-operational','rel-IR-owner',
    'rel-op-delta','rel-r-next','rel-collapse'
  ];
  function rank(order,id){ const i=order.indexOf(id); return i < 0 ? 9999 : i; }
  function extractCallArg(raw, fnName){
    raw = String(raw || '');
    const needle = fnName + "('";
    const start = raw.indexOf(needle);
    if(start < 0) return null;
    const rest = raw.slice(start + needle.length);
    const end = rest.indexOf("'");
    return end >= 0 ? rest.slice(0, end) : null;
  }
  window.renderConcepts = function(){
    const q=(document.getElementById('conceptSearch')?.value||'').toLowerCase();
    const t=document.getElementById('conceptType')?.value||'';
    const arr=(CONCEPTS||[])
      .filter(c=>(!t||c.type===t)&&JSON.stringify(c).toLowerCase().includes(q))
      .sort((a,b)=>rank(CONCEPT_ORDER,a.id)-rank(CONCEPT_ORDER,b.id) || String(a.name).localeCompare(String(b.name)));
    const list=document.getElementById('conceptList');
    if(!list) return;
    list.innerHTML=arr.map((c,i)=>`<button class="conceptBtn ${i===0?'active':''}" data-cid="${esc(c.id)}" onclick="selectConcept('${c.id}',this)"><span class="entityType">${esc(c.type)}</span><br><strong>${esc(c.name)}</strong><br><span class="small">${esc(c.summary)}</span></button>`).join('');
    if(arr[0] && typeof selectConcept === 'function') selectConcept(arr[0].id,list.querySelector('.conceptBtn'));
  };
  window.renderRelations = function(){
    const ordered=(RELATIONS||[]).slice().sort((a,b)=>rank(RELATION_ORDER,a.id)-rank(RELATION_ORDER,b.id) || String(a.label).localeCompare(String(b.label)));
    const panel=document.getElementById('relationPanel');
    if(!panel) return;
    panel.innerHTML=`<div class="relationLayout">
      <div class="relationList">${ordered.map((r,i)=>`<button class="relationBtn ${i===0?'active':''}" data-rid="${esc(r.id)}" onclick="selectRelation('${r.id}',this)"><span class="entityType">${esc(r.type)}</span><br><strong>${esc(r.label)}</strong><br><span class="small">${esc(r.from)} → ${esc(r.to)}</span></button>`).join('')}</div>
      <div id="relationDetail" class="relationDetail"></div>
    </div>`;
    if(ordered[0] && typeof selectRelation === 'function') selectRelation(ordered[0].id,panel.querySelector('.relationBtn'));
  };
  document.addEventListener('DOMContentLoaded', function(){
    setTimeout(function(){
      const theoryActive=document.getElementById('theory')?.classList.contains('active');
      if(typeof renderConcepts==='function') renderConcepts();
      if(typeof renderRelations==='function') renderRelations();
      const active=document.querySelector('#conceptList .conceptBtn.active') || document.querySelector('#conceptList .conceptBtn');
      const cid=active?.dataset?.cid || extractCallArg(active?.getAttribute('onclick'),'selectConcept');
      if(cid && typeof selectConcept==='function') selectConcept(cid, active);
    },0);
  });
})();
</script>





<script id="v45-unified-highlight-policy">
(function(){
  const TOKEN_POLICY = {
    noetic:['noetic','D0'],
    D0:['D0'],
    Psi:['Psi','N','m','tau','sigma','heart','xi','omega','mu','kappa','H'],
    N:['noetic','N'],
    m:['m'],
    tau:['tau'],
    sigma:['sigma'],
    heart:['heart','H','R'],
    xi:['xi'],
    omega:['omega'],
    mu:['mu'],
    kappa:['kappa','deltaK','R'],
    IR:['IR','N','m','tau','sigma','heart','xi','omega','mu','kappa'],
    burden:['burden','submoves'],
    submoves:['submoves','burden','deltaB'],
    Land:['Land','deltaB','deltaK'],
    deltaB:['deltaB','Land','nablaDot','nablaCross','R'],
    deltaK:['deltaK','kappa','nablaDot','nablaCross','R'],
    nablaDot:['nablaDot','deltaB','deltaK','R'],
    nablaCross:['nablaCross','deltaB','deltaK','R'],
    delDot:['delDot','nablaDot'],
    delCross:['delCross','nablaCross'],
    fieldDiagnostics:['nablaDot','nablaCross','deltaB','deltaK','R'],
    LandR:['Land','R','deltaB','deltaK','nablaDot','nablaCross','H'],
    R:['R','H','deltaB','deltaK','nablaDot','nablaCross'],
    decision:['R','H','deltaB','deltaK','nablaDot','nablaCross','nextB'],
    C:['C','Psi'],
    collapse:['C','Psi','R','final','heart','xi','omega','mu'],
    final:['final','N','heart','xi','omega','mu'],
    nextB:['nextB','R']
  };
  const oldSelectConcept = window.selectConcept;
  window.selectConcept = function(id, el){
    if(typeof oldSelectConcept === 'function') oldSelectConcept(id, el);
    const chosen = TOKEN_POLICY[id];
    if(chosen && typeof window.highlightNotation === 'function'){
      window.highlightNotation(chosen);
    }
  };
})();
</script>





<script id="field-diagnostics-concept-parity-v60">
  /* v60: first-class Δ / ∇·T / ∇×T concepts with ASCII aliases kept secondary. */
(function(){
  function ensureConcept(id, obj){
    if(!Array.isArray(CONCEPTS)) return;
    const existing = CONCEPTS.find(c => c.id === id);
    if(existing) Object.assign(existing, obj);
    else CONCEPTS.push(obj);
  }
  function ensureRelation(id, obj){
    if(!Array.isArray(RELATIONS)) return;
    const existing = RELATIONS.find(r => r.id === id);
    if(existing) Object.assign(existing, obj);
    else RELATIONS.push(obj);
  }
  function ensureFieldDiagnosticConcepts(){
    ensureConcept('submoves', {id:'submoves', name:'ⁿBᵢ[OPᵢ] submove/operator', type:'runtime control state', summary:'Owner-backed submove executed under the current burden.', definition:'ⁿBᵢ[OPᵢ] names an owner-backed submove: target → operation → result under the bounded current burden ⁿB.', runtime:'Submoves can change the burden field through ΔⁿB, but they do not become new burdens unless R(H,Δ) licenses ⁿ⁺¹B.', fields:['ⁿB','ΔⁿB','Δκ','R'], operators:['owner/TTP','P7','output-release'], relations:['executes within → ⁿB','produces → ΔⁿB','feeds → Land(ⁿB)'], files:['output-release.md','recursive-state-transitions.md','diagnostic-render-contract.md'], case:'A source-status operation may be ⁿB₂[OP₂] while the current burden remains ⁿB.', symbols:['submoves','burden','deltaB']});
    ensureConcept('Land', {id:'Land', name:'Land(ⁿB) burden landing', type:'runtime control state', summary:'The current burden lands only after owner-backed submoves produce governed state change.', definition:'Land(ⁿB) marks burden landing. It is not persuasion theater; it is the point at which the current burden has produced a governed ΔⁿB/Δκ transition or is held/partialed.', runtime:'Land(ⁿB) precedes ∇·/∇× field diagnostics and R(H,Δ) reread. It does not itself license final closure.', fields:['ⁿB','ⁿBᵢ[OPᵢ]','ΔⁿB','Δκ','R'], operators:['P7','recursive-state-transitions','output-release'], relations:['is produced by → ⁿBᵢ[OPᵢ]','precedes → ΔⁿB / Δκ','precedes → ∇· / ∇× diagnostics'], files:['recursive-state-transitions.md','output-release.md'], case:'After the active burden lands, the runtime rereads dependencies rather than continuing by momentum.', symbols:['Land','burden','submoves','deltaB','deltaK']});
    ensureConcept('deltaB', {id:'deltaB', name:'ΔⁿB burden-event delta', type:'runtime control state', summary:'Event-local transition produced by burden/submove landing.', definition:'ΔⁿB is the burden-event delta. It marks the state transition produced by Land(ⁿB) and its owner-backed submoves.', runtime:'ΔⁿB comes before ∇·/∇× field diagnostics and before R(H,Δ). It is not interchangeable with ∇.', fields:['ⁿB','ⁿBᵢ[OPᵢ]','Land(ⁿB)','Δκ','∇·','∇×','R'], operators:['P7','recursive-state-transitions'], relations:['computed by → Land(ⁿB)','precedes → ∇· / ∇× field diagnostics','feeds → R(H,Δ)'], files:['recursive-state-transitions.md','output-release.md','algebraic-notation-and-noetic-formalism.md'], case:'²B landed; Δ²B records what changed in the burden field before field pressure is read.', symbols:['deltaB','burden','submoves','Land','nablaDot','nablaCross','R']});
    ensureConcept('deltaK', {id:'deltaK', name:'Δκ closure-state delta', type:'runtime control state', summary:'Case-collapse / dependency-radius transition after burden-field update.', definition:'Δκ marks dependency-radius or closure-state change produced by the burden cycle. κ is the collapse/closure-state target when rendered as ∇·κ or ∇×κ.', runtime:'Δκ is a transition, not a divergence/curl diagnostic. ∇·κ and ∇×κ may read the κ field after Δκ is produced.', fields:['κ','ΔⁿB','∇·κ','∇×κ','R'], operators:['P7','M8','recursive-state-transitions'], relations:['updates → κ','precedes → ∇·κ / ∇×κ','feeds → R(H,Δ)'], files:['recursive-state-transitions.md','diagnostic-render-contract.md'], case:'If dependency radius expands after a burden lands, Δκ is live and closure remains gated.', symbols:['deltaK','kappa','nablaDot','nablaCross','R']});
    ensureConcept('nablaDot', {id:'nablaDot', name:'∇·T target-explicit field diagnostic', type:'runtime control state', summary:'Post-Delta diagnostic reading divergence-like residual outward pressure in an explicit target field T.', definition:'∇·T reads residual outward pressure in a named target field after Δ has produced a field state. Target grammar: T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}. Examples are owner-valid only when the target is explicit and control-relevant; they are not decorative symbol variants.', runtime:'Detects unresolved outward burden/dependency/register/route pressure after a burden event or field-state update. Positive pressure blocks false closure unless cleared, integrated, discharged, held with reason, or carried into RECURSE/PARTIAL.', fields:['ΔⁿB','Δκ','κ','ⁿB','ξ','Ω','♥','μ','H','route','register','Ψᴺ-slice','R'], operators:['P7','recursive-state-transitions','diagnostic-render-contract'], relations:['post-Delta diagnostic over → explicit target field','not substitute for → Δ','gates → STOP/HOLD/RECURSE/PARTIAL/COMPLETE'], files:['diagnostic-render-contract.md','output-release.md','recursive-state-transitions.md','algebraic-notation-and-noetic-formalism.md'], case:'∇·ⁿB positive over dependent burdens means residual burden-field pressure remains after the last Land(ⁿB).', symbols:['nablaDot','deltaB','deltaK','R']});
    ensureConcept('nablaCross', {id:'nablaCross', name:'∇×T target-explicit field diagnostic', type:'runtime control state', summary:'Post-Delta diagnostic reading curl-like circularity, rotational dependency, or unresolved cyclic pressure in an explicit target field T.', definition:'∇×T reads circularity or rotational dependency in a named target field after Δ has produced a field state. Target grammar: T ∈ {κ, ⁿB, ξ, Ω, ♥, μ, H, route, register, Ψᴺ-slice}. It is a closure diagnostic over relational noetic space, not a graph metaphor or proof-by-symbol.', runtime:'Detects dependency loops, circular burden pressure, recursive closure failure, or route cycles that linear transition alone cannot resolve. Nonzero curl pressure blocks COMPLETE without accounting.', fields:['ΔⁿB','Δκ','κ','ⁿB','ξ','Ω','μ','σ','route','register','R'], operators:['P7','recursive-state-transitions','diagnostic-render-contract'], relations:['post-Delta diagnostic over → explicit target field','not substitute for → Δ','gates → loop-breaking / RECURSE / PARTIAL'], files:['diagnostic-render-contract.md','output-release.md','recursive-state-transitions.md','algebraic-notation-and-noetic-formalism.md'], case:'∇×ξ unresolved means the certainty register contains circular warrant pressure that linear traversal will not resolve.', symbols:['nablaCross','deltaB','deltaK','R']});
    ensureConcept('delDot', {id:'delDot', name:'∇· / del-dot alias', type:'notation alias', summary:'∇· diagnostic with del-dot ASCII alias.', definition:'del-dot is the grep/checker-safe spelling of ∇·. It is not a separate operator and not its own runtime state.', runtime:'Use the ∇· diagnostic as primary notation; use del-dot only where Unicode is impractical while preserving the same target-explicit divergence-like diagnostic contract.', fields:['∇·','ΔⁿB','Δκ','R'], operators:['check_register_formalism_bridge','check_render_modes'], relations:['alias-of → ∇·','not separate from → ∇·'], files:['diagnostic-render-contract.md','algebraic-notation-and-noetic-formalism.md'], case:'del-dot(ⁿB) is the ASCII way to refer to ∇·ⁿB in checker-safe text.', symbols:['delDot','nablaDot']});
    ensureConcept('delCross', {id:'delCross', name:'∇× / del-cross alias', type:'notation alias', summary:'∇× diagnostic with del-cross ASCII alias.', definition:'del-cross is the grep/checker-safe spelling of ∇×. It is not a separate operator and not its own runtime state.', runtime:'Use the ∇× diagnostic as primary notation; use del-cross only where Unicode is impractical while preserving the same target-explicit curl-like diagnostic contract.', fields:['∇×','ΔⁿB','Δκ','R'], operators:['check_register_formalism_bridge','check_render_modes'], relations:['alias-of → ∇×','not separate from → ∇×'], files:['diagnostic-render-contract.md','algebraic-notation-and-noetic-formalism.md'], case:'del-cross(ξ) is the ASCII way to refer to ∇×ξ in checker-safe text.', symbols:['delCross','nablaCross']});
    ensureConcept('R', {id:'R', name:'R(H,Δ) recursive field-state reread', type:'runtime control state', summary:'Rereads the whole live field after burden events and field-state diagnostics.', definition:'R(H,Δ) is the recursive state reread after ΔⁿB/Δκ and target-explicit ∇·/∇× field diagnostics. R(H,Delta) is ASCII fallback only.', runtime:'Rereads selected/held N, live registers, burdens, owner/TTP eligibility, κ/H, alternate routes, residual pressure, and closure state. It licenses STOP/HOLD/RECURSE/PARTIAL/COMPLETE only after accounting.', fields:['H','ΔⁿB','Δκ','∇·','∇×','κ','ⁿB'], operators:['P7','output-release','recursive-state-transitions'], relations:['rereads → whole live field','after → Δ and ∇ diagnostics','licenses → STOP/HOLD/RECURSE/PARTIAL/COMPLETE'], files:['recursive-state-transitions.md','output-release.md','diagnostic-render-contract.md'], case:'After ²B lands, R(H,Δ) must reread dependent burdens and any circular dependency before closure.', symbols:['R','H','deltaB','deltaK','nablaDot','nablaCross']});
    const decision = (CONCEPTS||[]).find(c => c.id === 'decision');
    if(decision){
      decision.name = 'STOP / HOLD / RECURSE / PARTIAL / COMPLETE';
      decision.summary = 'Closure outcomes licensed by R(H,Δ), not by route exhaustion.';
      decision.runtime = 'COMPLETE is licensed only when residual ∇·/∇× pressure is cleared, integrated, discharged, held with reason, or carried into RECURSE/PARTIAL.';
      decision.symbols = ['R','deltaB','deltaK','nablaDot','nablaCross','nextB'];
    }
  }
  function ensureFieldDiagnosticRelations(){
    ensureRelation('rel-submove-land-delta', {id:'rel-submove-land-delta', label:'ⁿBᵢ[OPᵢ] lands into ΔⁿB / Δκ', type:'produces-transition', from:'ⁿBᵢ[OPᵢ]', to:'Land(ⁿB) → ΔⁿB / Δκ', symbols:['submoves','Land','deltaB','deltaK'], explain:'Owner-backed submoves operate inside the selected burden and produce event-local transition when the burden lands.', runtime:'This keeps Δ as transition machinery and prevents ∇ from replacing burden events.'});
    ensureRelation('rel-delta-before-field-diagnostics', {id:'rel-delta-before-field-diagnostics', label:'Δ precedes ∇·T / ∇×T diagnostics', type:'pipeline-order', from:'ΔⁿB / Δκ', to:'∇·T / ∇×T field diagnostics', symbols:['deltaB','deltaK','nablaDot','nablaCross'], explain:'∇·T and ∇×T read the field state that Δ produced. They cannot be applied before a burden lands.', runtime:'This is the operator hierarchy: ∇ ranks eligible route pressure before burden release; Δ computes event-local transition; ∇·T/∇×T diagnose the resulting target-explicit field pressure.'});
    ensureRelation('rel-field-diagnostics-reread', {id:'rel-field-diagnostics-reread', label:'field diagnostics feed R(H,Δ)', type:'closure-gate', from:'∇·T / ∇×T target field state', to:'R(H,Δ)', symbols:['nablaDot','nablaCross','R','H'], explain:'Residual divergence/curl pressure must be accounted for before closure.', runtime:'Nonzero ∇·T or ∇×T with no accounting is false closure.'});
    ensureRelation('rel-del-dot-alias', {id:'rel-del-dot-alias', label:'del-dot is alias-of ∇·', type:'alias-of', from:'del-dot', to:'∇·', symbols:['delDot','nablaDot'], explain:'del-dot is the ASCII alias for ∇·, not a separate operator.', runtime:'Checker-safe spelling preserves the same target-explicit field diagnostic semantics.'});
    ensureRelation('rel-del-cross-alias', {id:'rel-del-cross-alias', label:'del-cross is alias-of ∇×', type:'alias-of', from:'del-cross', to:'∇×', symbols:['delCross','nablaCross'], explain:'del-cross is the ASCII alias for ∇×, not a separate operator.', runtime:'Checker-safe spelling preserves the same target-explicit curl-like diagnostic semantics.'});
    ensureRelation('rel-nabla-not-delta', {id:'rel-nabla-not-delta', label:'∇·T / ∇×T are not substitutes for Δ', type:'anti-conflation', from:'∇·T / ∇×T', to:'ΔⁿB / Δκ', symbols:['nablaDot','nablaCross','deltaB','deltaK'], explain:'∇·T and ∇×T diagnose Δ-produced field state. They do not compute transitions and do not replace Δ.', runtime:'If field diagnostics are used as transition proof or proof-by-symbol, the render/checker must fail.'});
    ensureRelation('rel-reread-whole-live-field', {id:'rel-reread-whole-live-field', label:'R(H,Δ) rereads the whole live field', type:'reconstruction-fidelity', from:'R(H,Δ)', to:'selected/held N, burdens, registers, routes, residual pressure', symbols:['R','H','deltaB','deltaK','nablaDot','nablaCross'], explain:'R rereads more than the selected route. Alternate structures, hidden dependencies, circularities, and residual pressures remain live until accounted for.', runtime:'Closure is not route exhaustion; it is field accounting after reread.'});
    ensureRelation('rel-selected-path-release-order', {id:'rel-selected-path-release-order', label:'selected path is release order over the live field', type:'field-accounting', from:'selected execution path', to:'live noetic/burden/dependency/register/route field', symbols:['noetic','burden','submoves','deltaB','nablaDot','nablaCross','R'], explain:'A selected route is the order of release, not the whole field itself.', runtime:'Multiple valid noetic-structure selections must be integrated, discharged, held, or carried into RECURSE/PARTIAL rather than scalar-collapsed.'});
  }
  ensureFieldDiagnosticConcepts();
  ensureFieldDiagnosticRelations();
  document.addEventListener('DOMContentLoaded', function(){
    ensureFieldDiagnosticConcepts();
    ensureFieldDiagnosticRelations();
    setTimeout(function(){
      if(typeof renderConcepts === 'function') renderConcepts();
      if(typeof renderRelations === 'function') renderRelations();
    }, 0);
  });
})();
</script>

<script id="v45-notation-click-unifier">
(function(){
  const POLICY = {
    noetic:['noetic','D0'],
    D0:['D0'],
    Psi:['Psi','N','m','tau','sigma','heart','xi','omega','mu','kappa','H'],
    N:['noetic','N'],
    m:['m'],
    tau:['tau'],
    sigma:['sigma'],
    heart:['heart','H','R'],
    xi:['xi'],
    omega:['omega'],
    mu:['mu'],
    kappa:['kappa','deltaK','R'],
    IR:['IR','N','m','tau','sigma','heart','xi','omega','mu','kappa'],
    burden:['burden','submoves'],
    Land:['Land','deltaB'],
    LandR:['Land','R','deltaB','deltaK','H'],
    R:['R','H','deltaB','deltaK'],
    decision:['R','H','deltaB','deltaK','nextB'],
    C:['C','Psi'],
    collapse:['C','Psi','R','final','heart','xi','omega','mu'],
    final:['final','N','heart','xi','omega','mu'],
    nextB:['nextB','R']
  };
  const oldHighlight = window.highlightNotation;
  window.highlightNotation = function(keys, primaryKey){
    let raw = Array.isArray(keys) ? keys.slice() : [keys];
    let expanded = [];
    raw.forEach(k => expanded = expanded.concat(POLICY[k] || [k]));
    expanded = [...new Set(expanded.filter(Boolean))];
    if(typeof oldHighlight === 'function') return oldHighlight(expanded, primaryKey || raw[0]);
  };
  const oldSelectConcept = window.selectConcept;
  window.selectConcept = function(id, el){
    if(typeof oldSelectConcept === 'function') oldSelectConcept(id, el);
    const chosen = POLICY[id];
    if(chosen && typeof oldHighlight === 'function') oldHighlight(chosen);
  };
})();
</script>

<script id="field-operator-architecture-v19">
/* v19: route-gradient, loop-breaking, closure-field, and agent/interlocutor coupling concepts. */
(function(){
  const UPGRADE = {
    gradient:{concept:'gradient', key:'gradient'}, '∇':{concept:'gradient', key:'gradient'}, 'route-gradient':{concept:'gradient', key:'gradient'}, routeGradient:{concept:'gradient', key:'gradient'},
    loopBreak:{concept:'loopBreak', key:'loopBreak'}, 'LoopBreak':{concept:'loopBreak', key:'loopBreak'}, 'LoopBreak(∇×T)':{concept:'loopBreak', key:'loopBreak'},
    PsiI:{concept:'PsiI', key:'PsiI'}, 'Ψᴵ':{concept:'PsiI', key:'PsiI'},
    coupling:{concept:'coupling', key:'coupling'}, T_lang:{concept:'coupling', key:'coupling'}, 'T_lang: Ψᴺ ⇢ Ψᴵ':{concept:'coupling', key:'coupling'}
  };
  function ensureConcept(id, obj){
    if(!Array.isArray(CONCEPTS)) return;
    const existing = CONCEPTS.find(c => c.id === id);
    if(existing) Object.assign(existing, obj);
    else CONCEPTS.push(obj);
  }
  function ensureRelation(id, obj){
    if(!Array.isArray(RELATIONS)) return;
    const existing = RELATIONS.find(r => r.id === id);
    if(existing) Object.assign(existing, obj);
    else RELATIONS.push(obj);
  }
  function ensureFieldOperatorArchitecture(){
    ensureConcept('gradient', {
      id:'gradient',
      name:'∇ route-gradient operator',
      type:'runtime control state',
      summary:'Route-gradient pressure over eligible live burdens/routes.',
      definition:'Plain ∇ is the route-gradient read over the live noetic/burden/dependency/register/route field. It indicates the eligible route or burden expected to produce the greatest diagnostic reduction, closure progress, or dependency clarification.',
      runtime:'∇ precedes release-order selection and remains constrained by Diagnostic IR, V1/routing precedence, owner catalogue eligibility, source-status, and held-material gates. It ranks or explains release pressure; it is not truth/warrant, free intuition, Δ, ∇·, ∇×, or deterministic route freezing.',
      fields:['Ψᴺ','IR','ⁿB','routes','H'],
      operators:['V1','routing-precedence','output-release','recursive-state-transitions'],
      relations:['reads pressure over → eligible live field','constrained by → IR/V1/catalogue gates','orders → selected release pressure','not substitute for → Δ / ∇· / ∇×'],
      files:['recursive-state-transitions.md','diagnostic-ir.md','output-release.md','algebraic-notation-and-noetic-formalism.md'],
      case:'If B2 has the greatest live diagnostic yield after gates, ∇ can explain why B2 releases before B3 without treating B2 as the whole field.',
      symbols:['gradient','IR','burden','R']
    });
    ensureConcept('loopBreak', {
      id:'loopBreak',
      name:'LoopBreak(∇×T) loop-breaking submove',
      type:'runtime control state',
      summary:'Owner-grounded submove licensed when nonzero curl remains in an explicit target field.',
      definition:'LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R. It targets a circular dependency in target field T and grounds the loop in an owner-licensed non-circular source.',
      runtime:'G ∈ {fiṭrah, ʿaql ṣarīḥ, necessary knowledge, definition discipline, direct contradiction exposure, source-status correction}. LoopBreak is licensed only with an explicit target loop, owner-licensed grounding source, burden/submove, Δ effect, and post-break reread. If no loop-breaker is licensed, nonzero curl remains held or recursed rather than hidden by closure.',
      fields:['∇×','T','ΔⁿB','Δκ','R'],
      operators:['P1','V2','V3','V9','M1','M7','M8','R1','proof-method-audit'],
      relations:['licensed by → nonzero ∇×T plus owner ground','requires → target loop + G + ⁿBᵢ[OPᵢ] + Δ + R','produces → Δ update','requires → post-break ∇×T reread','not → arbitrary assertion'],
      files:['recursive-state-transitions.md','output-release.md','diagnostic-render-contract.md','algebraic-notation-and-noetic-formalism.md'],
      case:'∇×ⁿB remains nonzero around circular warrant demand; LoopBreak(∇×T) ⊢ target loop + necessary knowledge + ⁿBᵢ[OPᵢ] + Δ + R.',
      symbols:['loopBreak','nablaCross','deltaB','deltaK','R']
    });
    ensureConcept('PsiI', {
      id:'PsiI',
      name:'Ψᴵ diagnosed interlocutor field',
      type:'runtime control state',
      summary:'The interlocutor noetic field as diagnosed from discourse/profile/register evidence.',
      definition:'Ψᴵ is not the agent execution state and not direct access to the soul. It is the diagnosed interlocutor field inferred from public discourse, profile, register, response, and source-status evidence.',
      runtime:'The runtime operates in Ψᴺ and releases through language toward Ψᴵ. Ψᴵ constrains coupling assessment, but it does not authorize claims of guaranteed acceptance, total identity, or agent control of guidance.',
      fields:['D₀','Ψᴺ','profile','registers','source-status'],
      operators:['V1','P2','output-release','diagnostic-render-contract'],
      relations:['diagnosed by → discourse/profile/register evidence','receives → language-mediated coupling attempt','not → access to soul','not → guaranteed uptake'],
      files:['diagnostic-ir.md','recursive-state-transitions.md','output-release.md','algebraic-notation-and-noetic-formalism.md'],
      case:'A response may target the diagnosed proof-method pressure in Ψᴵ without claiming the person has internally accepted the correction.',
      symbols:['PsiI','Psi','coupling']
    });
    ensureConcept('coupling', {
      id:'coupling',
      name:'T_lang: Ψᴺ ⇢ Ψᴵ output boundary',
      type:'output-governance rule',
      summary:'Post-closure public release boundary from the agent execution field toward the diagnosed interlocutor field.',
      definition:'T_lang: Ψᴺ ⇢ Ψᴵ names the language-mediated output boundary after closure, HOLD, PARTIAL, or RECURSE accounting. It is not a burden-loop transition, Δ event, R reread, or claim that the interlocutor has been rewritten.',
      runtime:'The boundary checks that the public response preserves identity, avoids deformation, addresses the live burden state, and releases toward fiṭrah and sound reason without claiming guaranteed uptake, acceptance, or guidance control.',
      fields:['Ψᴺ','Ψᴵ','R','𝒞(Ψᴺ)','Restorative Response'],
      operators:['output-release','diagnostic-render-contract','P1','P7'],
      relations:['post-closure boundary from → Ψᴺ','toward diagnosed → Ψᴵ','not → burden-loop transition','not → guaranteed uptake'],
      files:['recursive-state-transitions.md','diagnostic-ir.md','output-release.md','diagnostic-render-contract.md'],
      case:'T_lang names the public release boundary, not access-to-soul, conversion guarantee, or another runtime state transition.',
      symbols:['coupling','Psi','PsiI','final','C']
    });
    ensureRelation('rel-live-field-gradient', {id:'rel-live-field-gradient', label:'live field feeds ∇ route-gradient', type:'route-pressure', from:'live noetic/burden/dependency/register/route field', to:'∇ route-gradient', symbols:['gradient','Psi','IR','burden'], explain:'Plain ∇ reads route pressure after the field is diagnostically constrained.', runtime:'It explains release order without bypassing IR, routing precedence, or catalogue gates.'});
    ensureRelation('rel-gradient-gate-constrained', {id:'rel-gradient-gate-constrained', label:'IR/V1/catalogue constrain ∇', type:'gate-boundary', from:'IR / V1 / catalogue gates', to:'∇ route-gradient', symbols:['gradient','IR'], explain:'Route-gradient pressure is computed only over eligible routes.', runtime:'∇ cannot authorize arbitrary jumps or replace owner eligibility.'});
    ensureRelation('rel-gradient-selects-release-pressure', {id:'rel-gradient-selects-release-pressure', label:'∇ orders release pressure', type:'release-order', from:'∇ route-gradient', to:'selected live burden / release order', symbols:['gradient','burden'], explain:'The selected execution path is the release order over the live field, not the whole field.', runtime:'Multiple live structures remain accounted through R(H,Δ).'});
    ensureRelation('rel-curl-loopbreak', {id:'rel-curl-loopbreak', label:'nonzero ∇×T checks LoopBreak eligibility', type:'loop-breaking', from:'∇×T nonzero', to:'LoopBreak(∇×T)', symbols:['nablaCross','loopBreak'], explain:'Curl may require a loop-breaking submove rather than indefinite deferral or false closure.', runtime:'LoopBreak(∇×T) ⊢ target loop + G + ⁿBᵢ[OPᵢ] + Δ + R; G must be an owner-licensed grounding source.'});
    ensureRelation('rel-loopbreak-delta-reread', {id:'rel-loopbreak-delta-reread', label:'LoopBreak produces Δ and rereads curl', type:'pipeline-order', from:'LoopBreak(∇×T)', to:'Δ update → ∇×T reread → R(H,Δ)', symbols:['loopBreak','deltaB','nablaCross','R'], explain:'Loop-breaking is operative only when it changes state and triggers reread.', runtime:'It requires target loop, grounding source, burden/submove, Δ effect, and post-break reread; it cannot be arbitrary assertion or proof-by-symbol.'});
    ensureRelation('rel-closure-field-condition', {id:'rel-closure-field-condition', label:'𝒞(Ψᴺ) licenses STOP as positive closure-field condition', type:'closure-field', from:'R(H,Δ) + cleared/bounded residual pressure', to:'𝒞(Ψᴺ)', symbols:['C','R','nablaDot','nablaCross','gradient'], explain:'Closure is target configuration, not checklist exhaustion.', runtime:'It does not guarantee interlocutor conversion.'});
    ensureRelation('rel-agent-interlocutor-coupling', {id:'rel-agent-interlocutor-coupling', label:'Ψᴺ releases through T_lang toward Ψᴵ', type:'output boundary', from:'Ψᴺ agent execution field', to:'Ψᴵ diagnosed interlocutor field', symbols:['Psi','PsiI','coupling','final'], explain:'The public response is a language-mediated output boundary after closure/hold/partial accounting.', runtime:'No access-to-soul, guaranteed uptake, or guidance-control claim is licensed; T_lang is not a burden-loop transition.'});
  }
  const previousGoConceptField = window.goConceptField;
  window.goConceptField = function(raw){
    ensureFieldOperatorArchitecture();
    const info = UPGRADE[String(raw||'').trim()];
    if(!info){
      if(typeof previousGoConceptField === 'function') return previousGoConceptField(raw);
      return;
    }
    document.querySelectorAll('.tabsec').forEach(x=>x.classList.remove('active'));
    document.getElementById('theory')?.classList.add('active');
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    const theoryTab=[...document.querySelectorAll('.tab')].find(t=>t.textContent.includes('Theory'));
    if(theoryTab) theoryTab.classList.add('active');
    document.querySelectorAll('.subpanel').forEach(x=>x.classList.remove('active'));
    document.getElementById('sub-concepts')?.classList.add('active');
    document.querySelectorAll('.subtab').forEach(x=>x.classList.remove('active'));
    const conceptSub=[...document.querySelectorAll('.subtab')].find(t=>t.textContent.includes('Concept'));
    if(conceptSub) conceptSub.classList.add('active');
    const search=document.getElementById('conceptSearch');
    const type=document.getElementById('conceptType');
    if(search) search.value='';
    if(type) type.value='';
    if(typeof renderConcepts === 'function') renderConcepts();
    const btn=[...document.querySelectorAll('#conceptList .conceptBtn')].find(b=>{
      const cid=b.dataset?.cid || ((b.getAttribute('onclick')||'').match(/selectConcept\('([^']+)'/)||[])[1];
      return cid === info.concept;
    });
    if(btn && typeof selectConcept === 'function'){
      selectConcept(info.concept, btn);
      btn.scrollIntoView({behavior:'smooth',block:'center'});
    }
  };
  const previousRenderConcepts = window.renderConcepts;
  window.renderConcepts = function(){
    ensureFieldOperatorArchitecture();
    if(typeof previousRenderConcepts === 'function') previousRenderConcepts();
  };
  const previousRenderRelations = window.renderRelations;
  window.renderRelations = function(){
    ensureFieldOperatorArchitecture();
    if(typeof previousRenderRelations === 'function') previousRenderRelations();
  };
  document.addEventListener('DOMContentLoaded', function(){
    ensureFieldOperatorArchitecture();
    setTimeout(function(){
      if(typeof renderConcepts === 'function') renderConcepts();
      if(typeof renderRelations === 'function') renderRelations();
    }, 0);
  });
})();
</script>

</body>
</html>
