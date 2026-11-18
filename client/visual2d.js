import {OrganCanvas} from '/client/visual2d_canvas.js';
import {attachInput} from '/client/visual2d_input.js';
const $=id=>document.getElementById(id);
let viewer,ticker,inFlight=false,requestNumber=0,viewSerial=0,pending;
const clamp=n=>Math.max(0,Math.min(1,n));
function viewport(v){const r=v.canvas.getBoundingClientRect();
  const size=Math.max(1,Math.min(r.width,r.height)-50)*v.zoom;
  const x0=clamp(.5+(-r.width/2-v.panX)/size);
  const x1=clamp(.5+(r.width/2-v.panX)/size);
  const y0=clamp(.5+(-r.height/2-v.panY)/size);
  const y1=clamp(.5+(r.height/2-v.panY)/size);
  return x0<x1&&y0<y1?{x0,y0,x1,y1,limit:1200}:null;
}
function meta(graph){const w=graph.window;
  const counts=`${graph.nodes.length} видимых точек / ${graph.edges.length} связей`;
  const note=w?`${w.total_nodes} всего, ${w.partial?'неполная выборка':'вся область'}${
    w.edges_partial?', рёбра частичные':''}`:'';
  $('organMeta').textContent=[graph.projection,graph.coordinate_kind,graph.semantics,
    counts,note].filter(Boolean).join(' · ');
}
export function showVisual(graph,refresh,query){
  if(!graph||graph.schema!=='mikoshi.visual2d.v1')return false;
  const serial=++viewSerial, panel=$('organ2d');panel.hidden=false;
  if(!viewer){viewer=new OrganCanvas($('organCanvas'),node=>{
    $('organPoint').textContent=node?JSON.stringify(node,null,2):'Нейрон не выбран';
  });attachInput(viewer)}
  $('organTitle').textContent=(graph.title||graph.id)+' · '+graph.organ;
  meta(graph);
  $('organPoint').textContent=graph.nodes.length?
    'Колесо: масштаб, перетаскивание: панорама, клик: нейрон, двойной клик: сброс':
    'В выбранной области нет подтверждённых нейронов или наблюдений';
  if(ticker)clearInterval(ticker);ticker=null;
  if(pending)clearTimeout(pending);pending=null;
  viewer.onViewportChange=null;viewer.set(graph);
  if(graph.window&&typeof query==='function'){
    viewer.onViewportChange=()=>{if(pending)clearTimeout(pending);
      const seq=++requestNumber;pending=setTimeout(async()=>{
        const bounds=viewport(viewer);if(!bounds||serial!==viewSerial)return;
        try{const next=await query(bounds);
          if(seq!==requestNumber||serial!==viewSerial||next?.id!==graph.id)return;
          viewer.set(next,true);meta(next);
        }catch(e){if(serial===viewSerial)$('organMeta').textContent='2D-запрос: '+String(e)}
      },140)};
  }
  if(['real_photon_history','live_neural_state','live_retinal_spikes'].includes(graph.source?.kind)&&typeof refresh==='function'){
    ticker=setInterval(async()=>{if(inFlight||document.hidden||serial!==viewSerial)return;
      inFlight=true;try{const next=await refresh();
        if(next?.schema==='mikoshi.visual2d.v1'&&next.id===graph.id){viewer.set(next,true);meta(next)}}
      catch(e){$('organMeta').textContent='Сенсорный поток: '+String(e)}
      finally{inFlight=false}},1500);
  }return true;
}
