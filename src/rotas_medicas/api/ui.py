"""Interface web autocontida servida pela aplicação FastAPI."""

# ruff: noqa: E501

INDEX_HTML = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rotas Médicas</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{--ink:#172033;--muted:#64748b;--brand:#4f46e5;--bg:#f4f7fb;--card:#fff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:Inter,system-ui,sans-serif}header{padding:24px 30px;color:#fff;
background:linear-gradient(120deg,#172554,#4f46e5)}header h1{margin:0;font-size:25px}
header p{margin:6px 0 0;color:#dbeafe}.layout{display:grid;
grid-template-columns:360px 1fr;min-height:calc(100vh - 100px)}aside{padding:22px;
background:#fff;border-right:1px solid #e2e8f0}main{padding:22px;min-width:0}
label{display:block;margin:13px 0 5px;font-size:12px;font-weight:700;color:var(--muted)}
input,select,textarea,button{width:100%;padding:10px;border:1px solid #cbd5e1;
border-radius:7px;font:inherit}button{margin-top:14px;border:0;background:var(--brand);
color:#fff;font-weight:700;cursor:pointer}button.secondary{background:#e0e7ff;color:#3730a3}
button:disabled{opacity:.55;cursor:wait}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.button-content{display:inline-flex;align-items:center;justify-content:center;gap:9px}
.spinner{width:18px;height:18px;border:3px solid #ffffff66;border-top-color:#fff;
border-radius:50%;animation:spin .75s linear infinite}.secondary .spinner{
border-color:#a5b4fc;border-top-color:#3730a3}.loading{position:fixed;inset:0;
z-index:2000;display:grid;place-items:center;background:#0f172a80;backdrop-filter:blur(2px)}
.loading-card{width:min(420px,calc(100% - 32px));padding:26px;text-align:center;
background:#fff;border-radius:14px;box-shadow:0 20px 50px #0f172a4d}.loading-card .spinner{
width:42px;height:42px;margin:0 auto 15px;border-width:5px;border-color:#c7d2fe;
border-top-color:var(--brand)}.loading-card strong{display:block;font-size:18px}
.loading-card p{margin:8px 0 0;color:var(--muted);font-size:13px;line-height:1.5}
@keyframes spin{to{transform:rotate(360deg)}}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
.card,.panel{background:var(--card);border-radius:10px;box-shadow:0 2px 14px #0f172a0d}
.card{padding:15px}.card span{display:block;font-size:11px;color:var(--muted)}
.card strong{display:block;margin-top:5px;font-size:20px}.panel{padding:16px;margin-top:16px}
#map{height:480px;border-radius:10px;background:#e2e8f0}.route{padding:10px 0;
border-bottom:1px solid #e2e8f0}.route:last-child{border:0}.route h3{margin:0 0 4px}
.bar{height:7px;background:#e2e8f0;border-radius:5px;overflow:hidden}.bar i{display:block;
height:100%;background:#4f46e5}.muted{color:var(--muted);font-size:12px}
pre{white-space:pre-wrap;max-height:420px;overflow:auto;background:#0f172a;color:#e2e8f0;
padding:14px;border-radius:8px;font-size:12px}.error{color:#b91c1c;font-weight:650}
.hidden{display:none}@media(max-width:900px){.layout{grid-template-columns:1fr}
aside{border-right:0}.cards{grid-template-columns:1fr 1fr}#map{height:380px}}
</style></head><body><header><h1>Otimização de Rotas Médicas</h1>
<p>Algoritmo genético, restrições operacionais e assistência por LLM</p></header>
<div class="layout"><aside><h2>Configuração</h2><label>Cenário</label>
<select id="scenario"></select><div class="grid2"><div><label>População</label>
<input id="population" type="number" value="60" min="10" max="300"></div>
<div><label>Gerações</label><input id="generations" type="number" value="120"
min="1" max="1000"></div><div><label>Mutação</label>
<input id="mutation" type="number" value="0.25" min="0" max="1" step="0.05"></div>
<div><label>Seed</label><input id="seed" type="number" value="101"></div></div>
<button id="optimize">Otimizar rotas</button><p id="status" class="muted"></p>
<section id="llm" class="hidden"><h2>Assistente</h2>
<button class="secondary" id="instructions">Gerar instruções</button>
<button class="secondary" id="report">Gerar relatório</button>
<label>Pergunta sobre as rotas</label><textarea id="question" rows="3"
placeholder="Quais veículos atendem entregas críticas?"></textarea>
<button class="secondary" id="ask">Perguntar</button></section></aside>
<main><div id="empty" class="panel">Configure um cenário e execute a otimização.</div>
<section id="result" class="hidden"><div class="cards" id="cards"></div>
<div id="map"></div><div class="panel"><h2>Rotas</h2><div id="routes"></div></div>
<div class="panel hidden" id="assistantPanel"><h2>Resposta do assistente</h2>
<pre id="assistantOutput"></pre></div></section></main></div>
<div id="optimizationLoading" class="loading hidden" role="status" aria-live="assertive"
aria-label="Otimização em andamento"><div class="loading-card"><div class="spinner"></div>
<strong id="loadingTitle">Otimizando as rotas</strong>
<p id="loadingDetail">Executando o algoritmo genético…</p>
</div></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
let solutionId=null,map=null,routeLayer=null;const $=id=>document.getElementById(id);
async function api(path,options={}){const response=await fetch(path,{headers:{
'Content-Type':'application/json'},...options});const data=await response.json();
if(!response.ok)throw new Error(data.detail?.message||data.detail||'Erro na operação');return data}
async function loadScenarios(){const items=await api('/api/scenarios');$('scenario').innerHTML=
items.map(s=>`<option value="${s.id}" ${s.detected_issues.length?'disabled':''}>`+
`${s.name} · ${s.deliveries} entregas${s.detected_issues.length?' (inviável)':''}</option>`).join('')}
function renderMap(data){if(map)map.remove();map=L.map('map');L.tileLayer(
'https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,
attribution:'&copy; OpenStreetMap contributors'}).addTo(map);routeLayer=L.geoJSON(data,{
style:f=>({color:f.properties.color,weight:4}),pointToLayer:(f,ll)=>L.circleMarker(ll,
{radius:f.properties.feature_type==='deposito'?10:7,color:f.properties.color||'#111827',
fillColor:f.properties.priority_color||'#facc15',fillOpacity:1,weight:3}),
onEachFeature:(f,l)=>f.properties.popup&&l.bindPopup(f.properties.popup)}).addTo(map);
map.fitBounds(routeLayer.getBounds().pad(.12))}
function render(data){solutionId=data.solution_id;$('empty').classList.add('hidden');
$('result').classList.remove('hidden');$('llm').classList.remove('hidden');const m=data.metrics;
$('cards').innerHTML=[['Fitness',m.total_cost.toFixed(4)],['Distância',m.distance_km.toFixed(2)+' km'],
['Custo',m.operating_cost.toFixed(2)],['Veículos',m.vehicles_used]].map(x=>
`<div class="card"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join('');
$('routes').innerHTML=data.routes.filter(r=>r.stops.length).map(r=>`<div class="route"><h3>${r.vehicle}</h3>`+
`<div class="muted">${r.stops.length} entregas · ${r.distance_km.toFixed(2)} km · `+
`carga ${r.load}/${r.capacity}</div><div class="bar"><i style="width:${Math.min(100,r.load_usage_percent)}%"></i></div></div>`).join('');
renderMap(data.geojson)}
function setOptimizing(active){const button=$('optimize'),controls=['scenario','population',
'generations','mutation','seed'];controls.forEach(id=>$(id).disabled=active);button.disabled=active;
$('optimizationLoading').classList.toggle('hidden',!active);button.innerHTML=active?
'<span class="button-content"><span class="spinner"></span>Otimizando…</span>':'Otimizar rotas';
if(active){$('loadingTitle').textContent='Otimizando as rotas';
$('optimizationLoading').setAttribute('aria-label','Otimização em andamento');
$('loadingDetail').textContent=`População ${$('population').value} · até `+
`${$('generations').value} gerações. Aguarde a melhor solução viável.`}}
async function optimize(){setOptimizing(true);$('status').textContent='Executando algoritmo genético…';
try{const data=await api('/api/optimize',{method:'POST',body:JSON.stringify({scenario_id:$('scenario').value,
population_size:+$('population').value,max_generations:+$('generations').value,
mutation_rate:+$('mutation').value,seed:+$('seed').value})});render(data);$('status').textContent=
`Concluído em ${data.metrics.generations_executed} gerações.`}catch(e){$('status').innerHTML=
`<span class="error">${e.message}</span>`}finally{setOptimizing(false)}}
const assistantActions={instructions:{button:'instructions',idle:'Gerar instruções',busy:'Gerando…',
title:'Gerando instruções',detail:'O Ollama está preparando orientações para motoristas e equipes de entrega.'},
report:{button:'report',idle:'Gerar relatório',busy:'Gerando…',title:'Gerando relatório',
detail:'O Ollama está analisando as métricas e preparando o relatório de eficiência.'},
question:{button:'ask',idle:'Perguntar',busy:'Respondendo…',title:'Consultando as rotas',
detail:'O Ollama está preparando uma resposta fundamentada nos dados da solução.'}};
function setAssistantLoading(active,path){const action=assistantActions[path];
Object.values(assistantActions).forEach(item=>$(item.button).disabled=active);
$('optimizationLoading').classList.toggle('hidden',!active);const button=$(action.button);
button.innerHTML=active?`<span class="button-content"><span class="spinner"></span>`+
`${action.busy}</span>`:action.idle;if(active){$('loadingTitle').textContent=action.title;
$('loadingDetail').textContent=action.detail;
$('optimizationLoading').setAttribute('aria-label',`${action.title} em andamento`)}}
async function llmAction(path,body){if(!solutionId)return;setAssistantLoading(true,path);try{const data=await api(
`/api/solutions/${solutionId}/${path}`,{method:'POST',body:JSON.stringify(body)});
$('assistantPanel').classList.remove('hidden');$('assistantOutput').textContent=JSON.stringify(data,null,2)
}catch(e){$('assistantPanel').classList.remove('hidden');$('assistantOutput').textContent=e.message
}finally{setAssistantLoading(false,path)}}
$('optimize').onclick=optimize;$('instructions').onclick=()=>llmAction('instructions',{});
$('report').onclick=()=>llmAction('report',{period:'diario'});$('ask').onclick=()=>
llmAction('question',{question:$('question').value});loadScenarios().catch(e=>$('status').textContent=e.message);
</script></body></html>"""
