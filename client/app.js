// Mechanicus client: only the live API graph can create actions and tabs.
import {render} from '/client/board.js';
import {runEditor} from '/client/editor.js';
import {showVisual} from '/client/visual2d.js';
const $ = id => document.getElementById(id);
const state = {token:'', graph:{nodes:[], edges:[], placements:[]}, caps:[], selected:null};
export const current = () => state;
export const actionNode = id => state.graph.nodes.find(n => n.id === id);
export const tabs = () => state.graph.nodes.filter(n => n.type==='tab')
  .sort((a,b)=>a.order-b.order || a.title.localeCompare(b.title));
export async function api(path, data){
  if(!state.token) throw Error('Нет API-соединения');
  const options={headers:{Authorization:'Bearer '+state.token}};
  if(data!==undefined){options.method='POST';options.headers['Content-Type']='application/json';
    options.body=JSON.stringify(data)}
  const response=await fetch(path,options), value=await response.json();
  if(!response.ok||value.ok===false)throw Error(value.error||`HTTP ${response.status}`);
  return value;
}
export function report(value){$('result').textContent=JSON.stringify(value,null,2)}
export async function execute(action,args){
  const result=await api('/api/v1/action',{action,args});
  report(result); showVisual(result.result, async()=>{
    const next=await api('/api/v1/action',{action,args});return next.result;
  }, result.result?.window?async bounds=>{
    const next=await api('/api/v1/action',{
      action:'visual2d.query.'+result.result.id,args:bounds});
    return next.result;
  }:null); if(action.startsWith('layout.')||action.startsWith('components.')) await refresh(); return result.result;
}
export async function refresh(){
  state.graph=await api('/api/v1/graph');
  state.caps=(await api('/api/v1/capabilities')).capabilities;
  if(!tabs().some(t=>t.id===state.selected)) state.selected=tabs()[0]?.id||null;
  $('status').textContent=`${state.caps.length} активных API-действий`;
  render();
}
export const select = id => {state.selected=id;render()};
export async function run(id, preset={}){
  const capability=state.caps.find(c=>c.id===id);
  if(!capability) throw Error('Действие недоступно');
  const args=capability.fields?.length?await runEditor(capability,preset):preset;
  if(args!==null) return execute(id,args);
}
export async function place(item,tab,area){
  if(!tab) throw Error('Создайте вкладку');
  const p=state.graph.placements.find(p=>p.id===item);
  if(p) return execute('layout.move',{placement:p.id,tab,area,order:0});
  if(state.caps.some(c=>c.id===item))
    return execute('layout.place',{action:item,tab,area,order:0});
  throw Error('Недействительный узел графа');
}
$('connect').onclick=async()=>{
  state.token=$('token').value;$('token').value='';
  try{await refresh()}catch(e){state.token='';$('status').textContent='Нет соединения';report({error:String(e)})}
};
$('editor').addEventListener('close',()=>{$('editorFields').replaceChildren()});

$('cancelEditor').onclick=()=>{$('editor').close()};
