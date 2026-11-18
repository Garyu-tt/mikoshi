import {current,actionNode,tabs,run,place,select,report} from '/client/app.js';
const $=id=>document.getElementById(id);
const child=(name,cls='',content='')=>{
  const e=document.createElement(name);e.className=cls;e.textContent=content;return e;
};
const areas=()=>current().graph.areas||[];
function draggable(node,id){
  node.draggable=true;
  node.ondragstart=e=>e.dataTransfer.setData('text/x-mikoshi-graph',id);
}
function target(element,tab,area){
  element.classList.add('drop-target');
  element.ondragover=e=>{e.preventDefault();element.classList.add('dragover')};
  element.ondragleave=()=>element.classList.remove('dragover');
  element.ondrop=async e=>{
    e.preventDefault();element.classList.remove('dragover');
    const id=e.dataTransfer.getData('text/x-mikoshi-graph');if(!id)return;
    try{await place(id,tab,area)}catch(err){report({error:String(err)})}
  };
}
function renderTabs(){
  const container=$('tabs');container.replaceChildren();
  const ts=tabs(), ids=new Set(ts.map(t=>t.id));
  for(const t of ts){
    const parent=ids.has(t.parent)?ts.find(n=>n.id===t.parent):null;
    let depth=0,walk=parent,seen=new Set([t.id]);
    while(walk&&!seen.has(walk.id)){
      depth++;seen.add(walk.id);walk=ts.find(n=>n.id===walk.parent);
    }
    const b=child('button','tab'+(current().selected===t.id?' selected':''),t.title);
    b.style.paddingLeft=`${10+depth*14}px`;
    b.onclick=()=>select(t.id);
    b.ondblclick=()=>run('layout.tab_edit',{tab:t.id,title:t.title}).catch(e=>report({error:String(e)}));
    target(b,t.id,'sidebar');container.appendChild(b);
  }
}
function buttonOf(p){
  const a=actionNode(p.source), b=child('button','placed',a?.title||p.source);
  b.title=`${p.id} · ${p.source} · ${p.area}`;
  draggable(b,p.id);
  b.onclick=()=>run(p.source).catch(e=>report({error:String(e)}));
  const wrapper=child('div','button-item');wrapper.appendChild(b);
  const remove=child('button','remove','×');remove.title='Убрать размещение';
  remove.onclick=()=>run('layout.remove',{placement:p.id}).catch(e=>report({error:String(e)}));
  wrapper.appendChild(remove);return wrapper;
}
function renderPalette(){
  const pal=$('palette');pal.replaceChildren();
  const placed=new Set(current().graph.placements.map(p=>p.source));
  for(const a of current().graph.nodes.filter(n=>n.type==='action')){
    const div=child('div','action');div.appendChild(child('b','',a.title));
    div.appendChild(child('small','',a.id+(placed.has(a.id)?' · на сцене':'')));
    draggable(div,a.id);div.ondblclick=()=>run(a.id).catch(e=>report({error:String(e)}));
    pal.appendChild(div);
  }
}
function renderAreas(){
  const graph=current().graph, selected=current().selected;
  $('current').textContent=actionNode(selected)?.title||'Сначала создайте вкладку';
  const side=$('sidebarButtons');side.replaceChildren();
  target(side,selected,'sidebar');
  for(const p of graph.placements.filter(p=>p.target===selected&&p.area==='sidebar'))
    side.appendChild(buttonOf(p));
  const grid=$('areas');grid.replaceChildren();
  for(const area of areas().filter(a=>a!=='sidebar')){
    const zone=child('section','zone');zone.appendChild(child('h3','',area));
    target(zone,selected,area);
    const items=graph.placements.filter(p=>p.target===selected&&p.area===area)
      .sort((a,b)=>a.order-b.order||a.row-b.row||a.column-b.column);
    for(const p of items)zone.appendChild(buttonOf(p));
    grid.appendChild(zone);
  }
}
export function render(){renderTabs();renderPalette();renderAreas()}
