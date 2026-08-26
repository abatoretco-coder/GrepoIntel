"use client";
import {useQuery} from "@tanstack/react-query";
import {AppNav} from "@/components/app-nav";
import {TargetCard} from "@/components/target-card";
import {Skeleton} from "@/components/ui/skeleton";
import {api} from "@/lib/api";
type Target={city_id:number;name:string;x:number;y:number;points:number;distance:number;target_score:number;owner?:{name:string};alliance?:{name:string};reasons?:{message:string}[]};
export default function TargetsPage(){const query=useQuery({queryKey:["targets"],queryFn:()=>api<{items:Target[]}>("/api/intelligence/targets?limit=30")});return <div className="app-shell"><AppNav/><main className="workspace"><header className="page-heading"><div><p className="eyebrow">RENSEIGNEMENT · OPPORTUNITÉS</p><h1>Cibles à évaluer</h1><p className="lead">Priorisées par proximité, contrôle territorial et risque public. Sélectionnez une cible pour ouvrir directement le conseiller.</p></div></header>{query.isLoading?<div className="target-grid">{[1,2,3,4,5,6].map(item=><Skeleton className="h-52" key={item}/>)}</div>:query.error?<p className="error">{query.error.message}</p>:<div className="target-grid">{query.data?.items.map(item=><TargetCard item={item} key={item.city_id}/>)}</div>}</main></div>}
