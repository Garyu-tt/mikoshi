// Capability field contracts supply the form, without manual action screens.
const $=id=>document.getElementById(id);
export function runEditor(capability,preset={}){
  return new Promise(resolve=>{
    const dialog=$('editor'), fields=$('editorFields'), form=$('editorForm');
    $('editorTitle').textContent=capability.title+' · '+capability.id;
    fields.replaceChildren();
    const inputs=[];
    for(const spec of capability.fields||[]){
      const label=document.createElement('label');label.className='field';
      const text=document.createElement('span');text.textContent=spec.label||spec.name;
      const input=spec.type==='json'?document.createElement('textarea'):
                    document.createElement('input');
      input.name=spec.name;input.type=['number','fraction'].includes(spec.type)?'number':'text';
      input.required=!spec.optional;input.autocomplete='off';
      if(spec.type==='number')input.step='1';
      if(spec.type==='fraction'){input.step='any';input.min='0';input.max='1'}
      input.value=preset[spec.name]===undefined?'':String(preset[spec.name]);
      label.append(text,input);fields.appendChild(label);inputs.push([spec,input]);
    }
    let finished=false;
    const settle=result=>{if(finished)return;finished=true;
      form.removeEventListener('submit',submit);
      dialog.removeEventListener('close',close);
      if(dialog.open)dialog.close();resolve(result)};
    const submit=e=>{e.preventDefault();try{
      const args={};for(const [spec,input] of inputs){
        const value=input.value.trim();if(spec.optional&&!value)continue;
        if(spec.type==='number'){
          if(!/^(0|[1-9][0-9]*)$/.test(value))throw Error('Требуется целое число без потери точности');
          args[spec.name]=value;
        }else if(spec.type==='fraction'){
          if(!/^(?:0(?:\.[0-9]+)?|1(?:\.0+)?)$/.test(value))
            throw Error('Координата должна находиться в диапазоне 0..1');
          args[spec.name]=Number(value);
        }else if(spec.type==='json')args[spec.name]=JSON.parse(value);
        else args[spec.name]=value;
      }settle(args);
    }catch(e){$('editorError').textContent=String(e)}};
    const close=()=>settle(null);
    $('editorError').textContent='';
    form.addEventListener('submit',submit);dialog.addEventListener('close',close);
    dialog.showModal();
  });
}
