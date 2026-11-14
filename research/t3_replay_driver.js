async function(kind){
const closing=kind==="closing", role=closing?"closing":"receiver", base="research/"+(closing?"closing-runs":"memory-runs");
if(load(kind+"_current")){
const c=load(kind+"_current");await eval("("+load("recorder")+")")({folder:base+"/"+c.name,role,send:c.send,prompt:c.prompt,controls:{experiment:kind,weights_updated:false}});
if(!closing){const r=await tools.exec_command({cmd:"python research/memory_replay.py score --run "+base+"/"+c.name,max_output_tokens:1000});if(r.exit_code!==0)throw Error(r.output);text({scored:c.name,...JSON.parse(r.output)});}
}
const c=await tools.exec_command({cmd:"python -c \"import json;from pathlib import Path;b=Path('"+base+"');s=json.loads((b/'schedule.json').read_text())['order'];print(json.dumps([n for n in s if not (b/n/'"+(closing?"closing-reply.txt":"outcome.json")+"').exists()]))\"",max_output_tokens:1500});
const q=JSON.parse(c.output);if(!q.length){store(kind+"_current",null);text({done:kind});return;}
const name=q[0],r=await tools.exec_command({cmd:"Get-Content -Raw "+base+"/"+name+"/"+role+"-input.json",max_output_tokens:3000});
const s=await tools.mcp__t3_code__t3_thread_send({threadId:load(closing?"a":"b"),freshContext:true,mode:"auto",message:r.output.trim()});
const current={name,prompt:r.output.trim(),send:s.structuredContent};store(kind+"_current",current);
text(await tools.apply_patch("*** Begin Patch\n*** Add File: "+base+"/"+name+"/dispatch.json\n+"+JSON.stringify(current).split("\n").join("\n+")+"\n*** End Patch"));
text({kind,name,remaining:q.length-1,runId:s.structuredContent.runId});
}
