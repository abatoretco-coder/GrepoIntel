const source="grepointel-companion";
let runtimeReady=false;
let runtimeError:string|undefined;
const readyWaiters=new Set<() => void>();

window.addEventListener("message",event=>{
  if(event.origin!==window.location.origin||event.data?.source!==source)return;
  if(event.data.type==="RUNTIME_READY"){
    runtimeReady=true;
    for(const resolve of readyWaiters)resolve();
    readyWaiters.clear();
  }
});

document.getElementById("grepointel-runtime-bridge")?.remove();
const script=document.createElement("script");
script.id="grepointel-runtime-bridge";
script.type="module";
script.src=chrome.runtime.getURL("dist/injected/page.js");
script.onerror=()=>{runtimeError="runtime_script_load_failed";for(const resolve of readyWaiters)resolve();readyWaiters.clear()};
(document.head||document.documentElement).append(script);

function waitForRuntime(){
  if(runtimeReady||runtimeError)return Promise.resolve();
  return new Promise<void>(resolve=>{readyWaiters.add(resolve);window.setTimeout(()=>{readyWaiters.delete(resolve);resolve()},10_000)});
}

chrome.runtime.onMessage.addListener((message,_,sendResponse)=>{
  if(message?.type!=="CAPTURE")return;
  void (async()=>{
    await waitForRuntime();
    if(runtimeError)return sendResponse({error:runtimeError});
    if(!runtimeReady)return sendResponse({error:"runtime_not_ready"});
    const nonce=crypto.randomUUID();
    const timer=window.setTimeout(()=>finish({error:"capture_timeout"}),15_000);
    const handler=(event:MessageEvent)=>{
      if(event.origin!==window.location.origin||event.data?.source!==source||event.data?.type!=="CAPTURE_RESULT"||event.data?.nonce!==nonce)return;
      finish(event.data);
    };
    const finish=(result:unknown)=>{window.clearTimeout(timer);window.removeEventListener("message",handler);sendResponse(result)};
    window.addEventListener("message",handler);
    window.postMessage({source,type:"CAPTURE_REQUEST",nonce},window.location.origin);
  })();
  return true;
});

chrome.storage.local.get({mode:"PERIODIC"}).then(config=>{if(config.mode!=="MANUAL")chrome.runtime.sendMessage({type:"SYNC"})});
