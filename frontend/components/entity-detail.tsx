"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Activity, Building2, MapPin, Shield } from "lucide-react";
import { AppNav } from "@/components/app-nav";
import { DataTable } from "@/components/data-table";
import { GrowthChart } from "@/components/growth-chart";
import { api } from "@/lib/api";
import {AnalyzeTargetButton, ViewTargetOnMap} from "@/components/target-actions";

const kindFor = (title:string) => title === "Alliance" ? "alliance" : title === "Ville" ? "city" : "player";
export function EntityDetail({ endpoint, title, id }: { endpoint:string; title:string; id:string }) {
  const query = useQuery({queryKey:[endpoint],queryFn:()=>api<Record<string,unknown>>(endpoint)}); const data = query.data;
  const related = Array.isArray(data?.cities) ? data.cities as Record<string,unknown>[] : Array.isArray(data?.nearby_cities) ? data.nearby_cities as Record<string,unknown>[] : Array.isArray(data?.top_players) ? data.top_players as Record<string,unknown>[] : [];
  const history = Array.isArray(data?.history) ? data.history as Record<string,unknown>[] : [];
  const back = title === "Alliance" ? "/alliances" : title === "Ville" ? "/map" : "/players";
  const metrics = Object.entries(data ?? {}).filter(([key,value]) => ["string","number","boolean"].includes(typeof value) && !["id","world_id","name","player_id"].includes(key)).slice(0,4);
  const isCity=title==="Ville"; const coordinates=isCity?`${String(data?.x??"—")}|${String(data?.y??"—")}`:undefined;
  return <div className="app-shell"><AppNav/><main className="workspace"><Link className="back" href={back}>← Retour au renseignement</Link><header className="page-heading"><div><p className="eyebrow">FICHE {title.toUpperCase()}</p><h1 className="detail-title">{String(data?.name ?? "Chargement…")}</h1><p className="lead">Vue consolidée des informations publiques, de l’historique observé et du contexte local.</p></div>{isCity&&data?<div className="context-actions"><AnalyzeTargetButton cityId={Number(id)} name={String(data.name)} coordinates={coordinates} source="fiche-ville"/><ViewTargetOnMap cityId={Number(id)} name={String(data.name)} coordinates={coordinates} source="fiche-ville"/></div>:<span className="read-only"><i className="online-dot"/>DONNÉES PUBLIQUES</span>}</header>{query.error && <p className="error">{query.error.message}</p>}{query.isLoading && <div className="loading"><i className="loading-block"/><i className="loading-block"/><i className="loading-block"/><i className="loading-block"/></div>}{data && <><section className="metric-grid">{metrics.map(([key,value],index) => { const Icon = [Activity,Shield,Building2,MapPin][index]; return <article className="metric" key={key}><Icon color="#55d6ff" size={18}/><span className="metric-label">{key.replaceAll("_"," ")}</span><strong className="metric-value">{typeof value === "number" ? value.toLocaleString("fr-FR") : String(value)}</strong></article>; })}</section>{history.length > 0 && <section className="panel"><header className="panel-head"><div><h2 className="panel-title">Évolution observée</h2><p className="panel-subtitle">Les snapshots publics disponibles pour cette fiche.</p></div></header><div className="panel-body"><GrowthChart history={history as {timestamp:string;points:number}[]}/></div></section>}<section className="panel"><header className="panel-head"><div><h2 className="panel-title">{title === "Alliance" ? "Joueurs principaux" : "Contexte géographique"}</h2><p className="panel-subtitle">Relations et positions associées à cette entité.</p></div></header><div className="panel-body"><DataTable rows={related} kind={title === "Alliance" ? "player" : "city"}/></div></section></>}</main></div>;
}
