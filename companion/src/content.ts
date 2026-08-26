const source="grepointel-companion";
if(!document.getElementById("grepointel-runtime-bridge")){
  const script=document.createElement("script");
  script.id="grepointel-runtime-bridge";
  script.type="module";
  script.src=chrome.runtime.getURL("dist/injected/page.js");
  (document.head||document.documentElement).append(script);
}
chrome.runtime.onMessage.addListener((message,_,sendResponse)=>{if(message?.type!=="CAPTURE")return;const nonce=crypto.randomUUID();const timer=setTimeout(()=>sendResponse({error:"capture_timeout"}),5000);const handler=(event:MessageEvent)=>{if(event.source!==window||event.data?.source!==source||event.data?.type!=="CAPTURE_RESULT"||event.data?.nonce!==nonce)return;clearTimeout(timer);window.removeEventListener("message",handler);sendResponse(event.data)};window.addEventListener("message",handler);window.postMessage({source,type:"CAPTURE_REQUEST",nonce},window.location.origin);return true;});
chrome.storage.local.get({mode:"PERIODIC"}).then(config=>{if(config.mode!=="MANUAL")chrome.runtime.sendMessage({type:"SYNC"})});
