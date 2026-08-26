"use client";

import {create} from "zustand";
import {persist} from "zustand/middleware";

export type TargetContext={cityId:number;name:string;coordinates?:string;source:string};
type TargetStore={target?:TargetContext;setTarget:(target:TargetContext)=>void;clearTarget:()=>void};

export const useTargetContext=create<TargetStore>()(persist((set)=>({
  target:undefined,
  setTarget:(target)=>set({target}),
  clearTarget:()=>set({target:undefined}),
}),{name:"grepointel-target-context"}));
