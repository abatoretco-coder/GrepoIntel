"use client";

import {MapPin, Shield, Target} from "lucide-react";
import {AnalyzeTargetButton,ViewTargetOnMap} from "@/components/target-actions";
import {Badge} from "@/components/ui/badge";
type Item={city_id:number;name:string;x:number;y:number;points:number;distance:number;target_score:number;owner?:{name:string};alliance?:{name:string};reasons?:{message:string}[];level?:string};
export function TargetCard({item,source="cibles"}:{item:Item;source?:string}){const coordinates=`${item.x}|${item.y}`;return <article className="target-card"><header><div><p className="eyebrow">CIBLE · {coordinates}</p><h2>{item.name}</h2><p>{item.owner?.name??"Ville fantôme"}{item.alliance?` · ${item.alliance.name}`:" · sans alliance"}</p></div><Badge variant="outline" className="score-badge"><Target size={13}/>Score {item.target_score}</Badge></header><div className="target-facts"><span><MapPin size={14}/>{item.distance} cases</span><span><Shield size={14}/>{item.points.toLocaleString("fr-FR")} points</span></div><p className="target-reason">{item.reasons?.[0]?.message??"À analyser"}</p><footer><AnalyzeTargetButton cityId={item.city_id} name={item.name} coordinates={coordinates} source={source}/><ViewTargetOnMap cityId={item.city_id} name={item.name} coordinates={coordinates} source={source}/></footer></article>}
