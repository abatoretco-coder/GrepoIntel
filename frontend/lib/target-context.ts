"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type SelectedPlan = {
  originId: number;
  originName: string;
  composition: Record<string, number>;
  unitSpeed: number;
};
export type TargetContext = {
  cityId: number;
  name: string;
  coordinates?: string;
  source: string;
  plan?: SelectedPlan;
};
type TargetStore = {
  target?: TargetContext;
  setTarget: (target: TargetContext) => void;
  selectPlan: (plan: SelectedPlan) => void;
  clearTarget: () => void;
};

export const useTargetContext = create<TargetStore>()(
  persist(
    (set) => ({
      target: undefined,
      setTarget: (target) => set({ target }),
      selectPlan: (plan) =>
        set((state) =>
          state.target ? { target: { ...state.target, plan } } : state,
        ),
      clearTarget: () => set({ target: undefined }),
    }),
    { name: "grepointel-target-context" },
  ),
);
