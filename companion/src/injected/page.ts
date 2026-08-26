import {GrepolisClientAdapter} from "../adapters/grepolis/adapter.js";

const source="grepointel-companion";
window.addEventListener("message",event=>{
  if(event.origin!==window.location.origin||event.data?.source!==source||event.data?.type!=="CAPTURE_REQUEST")return;
  try{
    const snapshot=new GrepolisClientAdapter(window as unknown as Record<string,unknown>).capture();
    window.postMessage({source,type:"CAPTURE_RESULT",nonce:event.data.nonce,snapshot},window.location.origin);
  }catch{
    window.postMessage({source,type:"CAPTURE_RESULT",nonce:event.data.nonce,error:"runtime_capture_failed"},window.location.origin);
  }
});
window.postMessage({source,type:"RUNTIME_READY"},window.location.origin);
