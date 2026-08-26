// Firefox MV3 currently runs background.scripts as classic scripts. Keep this
// file import-free so TypeScript does not emit `export {}` into background.js.
type Snapshot={cities?:unknown[];[key:string]:unknown};
type CompanionSettings={apiUrl:string;pairingToken:string;mode:"MANUAL"|"ON_PAGE_LOAD"|"PERIODIC";periodMinutes:number};
const defaults:CompanionSettings={apiUrl:"http://localhost:18000",pairingToken:"",mode:"PERIODIC",periodMinutes:5};
async function settings(){return {...defaults,...await chrome.storage.local.get(defaults)}}
async function pairedSettings(){
  const config=await settings();
  if(config.pairingToken)return config;
  const response=await fetch(`${config.apiUrl}/api/personal-state/pairing`,{method:"POST"});
  const result=await response.json().catch(()=>null) as {token?:string}|null;
  if(!response.ok||!result?.token)throw new Error("pairing_setup_failed");
  await chrome.storage.local.set({pairingToken:result.token});
  return {...config,pairingToken:result.token};
}
async function submit(snapshot:Snapshot){try{const config=await pairedSettings();const response=await fetch(`${config.apiUrl}/api/personal-state/import`,{method:"POST",headers:{"Content-Type":"application/json","X-GrepoIntel-Pairing":config.pairingToken},body:JSON.stringify(snapshot)});const result=await response.json();if(!response.ok)return {error:result.detail??"import_failed"};await chrome.storage.local.set({lastSync:new Date().toISOString(),lastResult:result});return result;}catch(error){return {error:error instanceof Error?error.message:"pairing_setup_failed"}}}
async function sync(tabId:number){
  const steps=["Onglet Grepolis détecté","Lecture passive du runtime Grepolis…"];
  const capture=await chrome.tabs.sendMessage(tabId,{type:"CAPTURE"});
  if(capture.error)return {...capture,steps};
  const cityCount=Array.isArray(capture.snapshot?.cities)?capture.snapshot.cities.length:0;
  steps.push(`${cityCount} ville${cityCount>1?"s":""} capturée${cityCount>1?"s":""}`,"Import sécurisé vers GrepoIntel…");
  const result=await submit(capture.snapshot as Snapshot);
  return {...result,steps:[...steps,result.error?"Synchronisation interrompue":"État personnel actualisé"]};
}
async function grepolisTab(){return (await chrome.tabs.query({url:["*://*.grepolis.com/*","*://*.grepolis.fr/*"]}))[0]}
chrome.runtime.onMessage.addListener((message,sender,respond)=>{if(message?.type==="IMPORT") {submit(message.snapshot as Snapshot).then(respond).catch(error=>respond({error:String(error)}));return true}if(message?.type==="SYNC_FROM_WEB"){grepolisTab().then(tab=>tab?.id?sync(tab.id):({error:"Aucun onglet Grepolis ouvert"})).then(respond).catch(error=>respond({error:String(error)}));return true}if(message?.type!=="SYNC"||!sender.tab?.id)return;sync(sender.tab.id).then(respond).catch(error=>respond({error:String(error)}));return true});
chrome.alarms.onAlarm.addListener(async()=>{const config=await settings();if(config.mode!=="PERIODIC")return;for(const tab of await chrome.tabs.query({url:["*://*.grepolis.com/*","*://*.grepolis.fr/*"]}))if(tab.id)await sync(tab.id)});
chrome.storage.onChanged.addListener(async changes=>{if(changes.mode||changes.periodMinutes){const config=await settings();await chrome.alarms.clear("periodic-sync");if(config.mode==="PERIODIC")chrome.alarms.create("periodic-sync",{periodInMinutes:Math.max(5,config.periodMinutes)})}});
async function ensureAutomaticSync(){const stored=await chrome.storage.local.get({mode:undefined,periodMinutes:5,syncPolicyVersion:0});if(stored.syncPolicyVersion<2)await chrome.storage.local.set({mode:"PERIODIC",periodMinutes:5,syncPolicyVersion:2});else if(!stored.mode)await chrome.storage.local.set({mode:"PERIODIC",periodMinutes:5});const config=await settings();await chrome.alarms.clear("periodic-sync");if(config.mode==="PERIODIC")chrome.alarms.create("periodic-sync",{periodInMinutes:Math.max(5,config.periodMinutes)})}
chrome.runtime.onInstalled.addListener(()=>{void ensureAutomaticSync()});chrome.runtime.onStartup.addListener(()=>{void ensureAutomaticSync()});void ensureAutomaticSync();
