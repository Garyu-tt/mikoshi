// Canvas renderer consumes only real 2D graph nodes and edges from the API.
export class OrganCanvas {
  constructor(canvas, inspect) {
    this.canvas=canvas;this.inspect=inspect;this.zoom=1;this.panX=0;this.panY=0;
    this.graph=null;this.viewport=null;this.selected=null;
    this.attach();new ResizeObserver(()=>this.draw()).observe(canvas);
  }
  set(graph,preserve=false){this.graph=graph;
    if(!preserve){this.zoom=1;this.panX=0;this.panY=0;this.selected=null}
    this.draw()}
  size(){const box=this.canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1;
    this.canvas.width=Math.max(1,Math.round(box.width*dpr));
    this.canvas.height=Math.max(1,Math.round(box.height*dpr));
    return {w:box.width,h:box.height,dpr}}
  transform(p){const v=this.viewport;return {x:v.x+(p.x-.5)*v.size,y:v.y+(p.y-.5)*v.size}}
  draw(){const g=this.graph;if(!g)return;
    const {w,h,dpr}=this.size(),ctx=this.canvas.getContext('2d');
    ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
    const scale=Math.max(1,Math.min(w,h)-50)*this.zoom;
    this.viewport={x:w/2+this.panX,y:h/2+this.panY,size:scale};
    const nodes=new Map(g.nodes.map(n=>[n.id,n]));
    ctx.lineWidth=.7;ctx.strokeStyle='GrayText';ctx.globalAlpha=.32;
    ctx.beginPath();for(const e of g.edges){const a=nodes.get(e.source),b=nodes.get(e.target);
      if(!a||!b)continue;const p=this.transform(a),q=this.transform(b);
      ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y)}ctx.stroke();ctx.globalAlpha=1;
    for(const n of g.nodes){const p=this.transform(n),r=n.id===this.selected?5:2.3;
      if(p.x<0||p.y<0||p.x>w||p.y>h)continue;
      ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);
      ctx.fillStyle=n.id===this.selected?'AccentColor':
        (n.fresh_now===true?'AccentColor':
         (typeof n.activity==='number'&&n.activity>.5?'CanvasText':'GrayText'));
      ctx.fill()}
  }
  nearest(x,y){if(!this.graph)return null;let best=null,dist=100;
    for(const n of this.graph.nodes){const p=this.transform(n);
      const d=(p.x-x)**2+(p.y-y)**2;if(d<dist){dist=d;best=n}}
    return best}
}
