"use client";

import {useEffect,useMemo,useState} from "react";
import {Clipboard,RefreshCw,ShieldCheck} from "lucide-react";
import {AppNav} from "@/components/app-nav";
import {api} from "@/lib/api";

type Status={connected:boolean;paired:boolean;player:string;world:string;last_snapshot_at:string|null;cities:number;diagnostics?:Record<string,string>};
const labels:Record<string,string>={resources:"Ressources",population:"Population",buildings:"Bâtiments",researches:"Recherches",units:"Unités",heroes:"Héros",towns:"Villes",god:"Dieu",queues:"Files"};
const errorLabels:Record<string,string>={pairing_required:"Pairing invalide",capture_timeout:"Capture impossible",runtime_not_ready:"Runtime Grepolis non chargé",runtime_script_load_failed:"Script Grepolis non chargé",runtime_capture_failed:"Capture impossible",import_failed:"Import impossible"};

export default function Companion(){
  const [status,setStatus]=useState<Status>(); const [sync,setSync]=useState("Prêt"); const [advanced,setAdvanced]=useState(false);
  async function refresh(){try{setStatus(await api<Status>("/api/personal-state/status"))}catch{setSync("Backend indisponible")}}
  useEffect(()=>{void refresh();const listener=(event:MessageEvent)=>{if(event.data?.source!=="grepointel-companion")return;if(event.data.type==="SYNC_STATUS")setSync(event.data.status);if(event.data.type==="SYNC_RESULT"){const error=event.data.result?.error;setSync(errorLabels[error]??error??(event.data.result?.created?"Synchronisé":"Aucun changement"));void refresh()}};window.addEventListener("message",listener);return()=>window.removeEventListener("message",listener)},[]);
  const diagnostic=useMemo(()=>Object.entries(status?.diagnostics??{}).map(([key,value])=>`${labels[key]??key}: ${value}`).join("\n")||"Aucun snapshot personnel reçu.",[status]);
  function request(){setSync("Companion détecté…");window.postMessage({source:"grepointel-web",type:"SYNC_REQUEST"},window.location.origin)}
  return <div className="app-shell"><AppNav/><main className="workspace"><header className="page-heading"><div><p className="eyebrow">FIREFOX COMPANION</p><h1>Synchronisation locale</h1><p className="lead">Lecture passive de l’onglet Grepolis déjà ouvert dans Firefox. Le token reste dans l’extension.</p></div></header><section className="panel"><header className="panel-head"><div><h2>Firefox Companion <span className="status-ok">{status?.paired?"CONNECTÉ":"À VÉRIFIER"}</span></h2><p className="panel-subtitle">{sync}</p></div><ShieldCheck/></header><div className="panel-body"><div className="metric-grid"><Metric label="Grepolis" value={status?.connected?"OUVERT":"EN ATTENTE"}/><Metric label="Profil" value={status?.player??"—"}/><Metric label="Monde" value={status?.world??"—"}/><Metric label="Villes" value={status?.cities??0}/></div><p className="sync-freshness">Dernière synchro : {status?.last_snapshot_at?new Date(status.last_snapshot_at).toLocaleString("fr-FR"):"jamais"}</p><div className="extractor-grid">{Object.entries(labels).slice(0,7).map(([key,label])=><div className="extractor" key={key}><span>{label}</span><strong>{status?.diagnostics?.[key]??"—"}</strong></div>)}</div><div className="import-actions"><button className="action-button" onClick={request}><RefreshCw size={16}/>Synchroniser maintenant</button><button className="secondary-button" onClick={()=>navigator.clipboard.writeText(diagnostic)}><Clipboard size={16}/>Copier diagnostic</button><button className="secondary-button" onClick={()=>setAdvanced(value=>!value)}>Avancé</button></div>{advanced&&<p className="result">Réappairage et régénération du token sont réservés au dépannage. Le token ne s’affiche jamais dans GrepoIntel.</p>}</div></section></main></div>;
}
function Metric({label,value}:{label:string;value:string|number}){return <article className="metric"><span className="metric-label">{label}</span><strong className="metric-value">{value}</strong></article>}
