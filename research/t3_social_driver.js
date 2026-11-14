/* T3 functions.exec orchestration helper. Requires the configured subject thread metadata and state in store/load. No model training. */
const recordSubject = async function({folder,role,send,prompt,controls={}}){
 const r=await tools.mcp__t3_code__t3_thread_read({threadId:send.threadId,view:"activity",limit:50,maxCharsPerItem:12000});
 const d=r.structuredContent, current=d.items.filter(x=>x.runId===send.runId&&x.type!=="reasoning");
 const reply=current.filter(x=>x.type==="assistant_message").at(-1)?.text;
 if(!reply||d.thread.status!=="completed")throw Error("Subject result not terminal or unavailable");
 const files={[role+"-reply.txt"]:reply,[role+"-prompt.json"]:JSON.stringify(JSON.parse(prompt),null,2),
 [role+"-metadata.json"]:JSON.stringify({send,controls:{freshContext:true,weights_updated:false,...controls},activity:current,run:d.recentRuns.find(x=>x.runId===send.runId)},null,2)};
 let patch="*** Begin Patch\n";for(const [name,value]of Object.entries(files))patch+="*** Add File: "+folder+"/"+name+"\n+"+value.split("\n").join("\n+")+"\n";
 text(await tools.apply_patch(patch+"*** End Patch"));return reply;
};
const advanceSocial = async function(){
 const record=eval("("+load("subject_recorder")+")");
 const run=load("social_run"), role=load("social_role"), mode=load("social_mode")||"pass", base="research/social-runs/"+run, prior=load("social_memory_root");
 await record({folder:base,role,send:load("social_send"),prompt:load("social_prompt"),controls:{mode,memory_source:prior,within_episode_self_message_present:role==="closing"}});
 const command=async cmd=>{const r=await tools.exec_command({cmd,max_output_tokens:2600});if(r.exit_code!==0)throw Error(r.output);return r.output;};
 const start=async(nextRole,prompt,threadId)=>{store("social_role",nextRole);store("social_prompt",prompt);const r=await tools.mcp__t3_code__t3_thread_send({threadId,freshContext:true,mode:"auto",message:prompt});store("social_send",r.structuredContent);text(r.structuredContent);};
 const peerNext=async side=>{
   text(await command("python social_experiment.py deliver --run "+base+" --side "+side+" --mode "+mode+(["light","strong"].includes(mode)?" --reply "+base+"/editor-"+side+"-reply.txt":"")));
   const relay=await tools.exec_command({cmd:"wsl -d kali-linux -- sh -c 'cd /home/pratz/guardianai-pilot && python3 paired_relay.py --run /mnt/c/Users/sayal/.t3/projects/guardianai/"+base+" --direction "+side+" --sensor /home/pratz/guardianai-tools/unpacked/usr/bin/strace'",max_output_tokens:700,yield_time_ms:1000});
   if(relay.session_id)throw Error("Relay command still running; resume its exec session before advancing");
   if(relay.exit_code!==0)throw Error(relay.output);
   text(relay.output);
   const nextRole=side==="a"?"receiver":"closing";
   const memory=prior?" --memory-file "+prior+"/"+(nextRole==="receiver"?"receiver":"closing")+"-reply.txt --feedback-file "+prior+"/outcome.json":"";
   const p=await command("python social_experiment.py prompt --run "+base+" --role "+nextRole+memory);
   await start(nextRole,p,side==="a"?load("pair_receiver_task").childThreadId:load("pair_sender_task").childThreadId);
 };
 if(role==="sender"||role==="receiver"){
   text(await command("python social_experiment.py observe --run "+base+" --role "+role+" --reply "+base+"/"+role+"-reply.txt"));
   const side=role==="sender"?"a":"b";
   if(mode==="light"||mode==="strong"){
     const p=await command("python social_experiment.py edit-prompt --run "+base+" --side "+side+" --strength "+mode);
     await start("editor-"+side,p,load("pair_receiver_task").childThreadId);
   }else await peerNext(side);
 }else if(role.startsWith("editor-")){
   await peerNext(role.slice(-1));
 }else if(role==="closing"){
   text(await command("python social_experiment.py score --run "+base));
   const queue=load("social_queue")||[];
   if(!queue.length){store("social_done",true);text({block:"complete",last_run:run});return;}
   const next=queue.shift();store("social_queue",queue);store("social_run",next.run);store("social_mode",next.mode);store("social_memory_root",next.prior||null);
   text(await command("python social_experiment.py init --run research/social-runs/"+next.run+" --seed "+next.seed));
   const memory=next.prior?" --memory-file "+next.prior+"/closing-reply.txt --feedback-file "+next.prior+"/outcome.json":"";
   const p=await command("python social_experiment.py prompt --run research/social-runs/"+next.run+" --role sender"+memory);
   await start("sender",p,load("pair_sender_task").childThreadId);
 }
};
