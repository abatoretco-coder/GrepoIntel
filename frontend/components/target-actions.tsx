"use client";

import {useRouter} from "next/navigation";
import {Crosshair, Map} from "lucide-react";
import {useTargetContext} from "@/lib/target-context";

type Props={cityId:number;name:string;coordinates?:string;source:string;compact?:boolean};
export function AnalyzeTargetButton({cityId,name,coordinates,source,compact=false}:Props){
  const router=useRouter(); const setTarget=useTargetContext(state=>state.setTarget);
  return <button className={compact?"table-link action-inline":"action-button"} onClick={()=>{setTarget({cityId,name,coordinates,source});router.push("/simulator")}}><Crosshair size={compact?14:16}/>Analyser{compact?"":" l’attaque"}</button>;
}
export function ViewTargetOnMap({cityId,name,coordinates,source}:Props){
  const router=useRouter(); const setTarget=useTargetContext(state=>state.setTarget);
  return <button className="secondary-button" onClick={()=>{setTarget({cityId,name,coordinates,source});router.push("/map")}}><Map size={15}/>Voir sur la carte</button>;
}
