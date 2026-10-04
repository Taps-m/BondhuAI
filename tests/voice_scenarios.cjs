const fs=require('fs'),vm=require('vm'),assert=require('assert');
let now=1000,loud=false,id=0,stops=0,denied=false,pending=false,resolvePending;const timeouts=new Map();const frames=new Map(),events={},els={},sent=[];
const element=()=>({innerText:'',dataset:{},addEventListener(t,f){this[t]=f;}});
const document={body:{dataset:{},scrollHeight:180},documentElement:{},getElementById(k){return els[k]??=element();}};
let marker=false;
class Recorder {constructor(){this.state='inactive';this.mimeType='audio/webm';} start(){this.state='recording';} stop(){this.state='inactive';this.ondataavailable({data:new Blob(['audio'])});this.onstop();}}
class AudioContext {createAnalyser(){return {fftSize:2048,getByteTimeDomainData(a){a.fill(loud?145:128);}};} createMediaStreamSource(){return {connect(){}};} close(){}}
const window={MediaRecorder:Recorder,AudioContext,addEventListener(t,f){events[t]=f;},parent:{postMessage(m){sent.push(m);},document:{getElementById(){return marker?{}:null;}}}};
const ctx=vm.createContext({window,document,MediaRecorder:Recorder,Blob,Uint8Array,console,Date:{now:()=>now},crypto:{randomUUID:()=>String(++id)},navigator:{mediaDevices:{async getUserMedia(){if(denied)throw Error('denied');if(pending)return new Promise(r=>resolvePending=r);return {getTracks:()=>[{stop(){stops++;}}]};}}},FileReader:class{readAsDataURL(){this.result='data:audio/webm;base64,YXVkaW8=';this.onloadend();}},requestAnimationFrame(f){frames.set(++id,f);return id;},cancelAnimationFrame(i){frames.delete(i);},setTimeout(f){timeouts.set(++id,f);return id;},clearTimeout(i){timeouts.delete(i);},setInterval(){return ++id;},clearInterval(){}});
vm.runInContext(fs.readFileSync('master_voice/voice_component/index.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1],ctx);
const read=s=>vm.runInContext(s,ctx);const flush=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
async function tick(ms){now+=ms;const jobs=[...frames.values()];frames.clear();jobs.forEach(f=>f());await flush();}
function render(token){events.message({data:{type:'streamlit:render',args:{language:'bn',answer_ready:token}}});}
const results=[];function check(name,test){assert.ok(test,name);results.push({scenario:name,result:'PASS'});}
(async()=>{
render();await flush();await tick(70000);check('First question waits more than 10 and 60 seconds',read('isRecording && !sessionEnded'));
loud=true;await tick(10);loud=false;await tick(10);await tick(1999);check('Pause shorter than 2 seconds keeps recording',read('isRecording'));await tick(1);check('Two seconds silence submits audio once',sent.filter(m=>m.value?.type==='audio').length===1&&read('waitingForStreamlit'));
render();await tick(100);check('Generic rerender cannot restart microphone',!read('isRecording'));
render('wrong');await tick(100);check('Wrong answer token cannot restart microphone',!read('isRecording'));
const token=read('recordingId');render(token);await tick(100);check('Matching token without display marker waits',!read('isRecording'));
marker=true;await tick(1);await tick(1);check('Waits for paint before restarting',!read('isRecording'));await tick(1);check('Displayed answer starts 10-second window',read('isRecording && nextQuestionDeadline-Date.now()===10000'));
loud=true;await tick(9000);check('Speech cancels follow-up countdown',read('speechDetected && nextQuestionDeadline===null'));await tick(2000);check('Continued speech survives former deadline',read('isRecording'));
loud=false;await tick(1);await tick(2000);check('Follow-up also stops after two seconds silence',sent.filter(m=>m.value?.type==='audio').length===2);
render(read('recordingId'));await tick(1);await tick(1);await tick(1);await tick(10000);check('No follow-up speech ends session and stops tracks',read('sessionEnded && !isRecording')&&stops>=3);
els.restart.click();await flush();check('Restart restores unlimited first-question mode',read('firstQuestion && isRecording'));
els.end.click();check('Manual end does not submit another recording',sent.filter(m=>m.value?.type==='audio').length===2);
denied=true;els.restart.click();await flush();check('Permission denial ends cleanly with error phase',document.body.dataset.phase==='error'&&read('sessionEnded'));
denied=false;pending=true;els.restart.click();await flush();els.end.click();await flush();check('End during pending permission re-enables restart',!els.restart.disabled);
const stoppedBefore=stops;resolvePending({getTracks:()=>[{stop(){stops++;}}]});await flush();check('Late permission stream is stopped after cancel',stops>stoppedBefore&&!read('isRecording'));
els.restart.click();await flush();[...timeouts.values()].forEach(f=>f());await flush();check('Startup timeout reports error and permits retry',document.body.dataset.phase==='error'&&!els.restart.disabled);
pending=false;els.restart.click();await flush();check('Retry succeeds after startup timeout',read('isRecording && firstQuestion'));els.end.click();
fs.writeFileSync('output/voice-scenario-results.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
