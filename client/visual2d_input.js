// Pan and zoom in projected organ coordinates, never changing neural state.
export function attachInput(view){const canvas=view.canvas;let start=null;
  const notify=()=>view.onViewportChange?.();
  canvas.addEventListener('pointerdown',e=>{start={x:e.offsetX,y:e.offsetY,
    px:view.panX,py:view.panY,moved:false};canvas.setPointerCapture(e.pointerId)});
  canvas.addEventListener('pointermove',e=>{
    if(!start)return;const dx=e.offsetX-start.x,dy=e.offsetY-start.y;
    if(Math.abs(dx)+Math.abs(dy)>5)start.moved=true;
    if(start.moved){view.panX=start.px+dx;view.panY=start.py+dy;view.draw()}});
  canvas.addEventListener('pointerup',e=>{
    if(!start)return;if(!start.moved){const n=view.nearest(e.offsetX,e.offsetY);
      view.selected=n?.id||null;view.inspect(n);view.draw()}
    else notify();start=null});
  canvas.addEventListener('pointercancel',()=>{start=null});
  canvas.addEventListener('wheel',e=>{e.preventDefault();
    const before=view.zoom;view.zoom=Math.max(.25,Math.min(90,view.zoom*Math.exp(-e.deltaY*.001)));
    const factor=view.zoom/before;const rect=canvas.getBoundingClientRect();
    const x=e.clientX-rect.left,y=e.clientY-rect.top;
    view.panX=x-(x-view.panX-rect.width/2)*factor-rect.width/2;
    view.panY=y-(y-view.panY-rect.height/2)*factor-rect.height/2;
    view.draw();notify()},{passive:false});
  canvas.addEventListener('dblclick',()=>{view.zoom=1;view.panX=0;view.panY=0;
    view.draw();notify()});
}
