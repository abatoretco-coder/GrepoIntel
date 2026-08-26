"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CalendarClock,
  Clock3,
  Eye,
  ShieldAlert,
  Swords,
  Target,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ViewTargetOnMap } from "@/components/target-actions";
import { useTargetContext } from "@/lib/target-context";

type Plan = {
  origin: { name: string; city_id: number };
  distance: number;
  travel_seconds: number;
  unit_speed: number;
  simulation: {
    land: { ratio: number; attack_type: string };
    naval: { ratio: number };
    confidence: number;
  };
  available_units: Record<string, number>;
  recommended_composition: Record<string, number>;
  composition_note: string;
  minimum_margin: string;
  recommended_margin: string;
};
type Unit = { id: string; label: string; domain: string; role: string };
type Advice = {
  recommendation: string;
  confidence: number;
  target: {
    last_spy_hours?: number;
    known_defense?: Record<string, number>;
    observed_at?: string;
  };
  reasons: string[];
  plans: Plan[];
  playbook: { stage: string; status: string; reason: string }[];
};
type City = {
  name: string;
  x: number;
  y: number;
  points: number;
  is_ghost: boolean;
  owner?: { id: number; name: string; alliance_id?: number };
};
type Alliance = { name: string };
type TargetIntel = { city_id: number; target_score: number; risk?: string };
type ThreatIntel = { player_id: number; score: number };
const label: Record<string, string> = {
  SCOUT_FIRST: "Espionner d’abord",
  EVALUATE_ATTACK: "Attaque à évaluer",
  REINFORCE_OR_AVOID: "Renforcer ou éviter",
  RECON: "Reconnaissance",
  NAVAL_CLEAR: "Nettoyage naval",
  LAND_CLEAR: "Nettoyage terrestre",
  RE_CLEAN: "Second passage",
  REVOLT: "Conquête / révolte",
};
const duration = (seconds: number) =>
  seconds >= 3600
    ? `${Math.floor(seconds / 3600)} h ${Math.round((seconds % 3600) / 60)} min`
    : `${Math.round(seconds / 60)} min`;
function UnitGroups({
  units,
  catalogue,
}: {
  units: Record<string, number>;
  catalogue: Unit[];
}) {
  const lookup = new Map(catalogue.map((unit) => [unit.id, unit]));
  const groups: { name: string; domains: string[] }[] = [
    { name: "Terrestre", domains: ["land"] },
    { name: "Naval", domains: ["naval"] },
    { name: "Transport", domains: ["naval"] },
    { name: "Mythique", domains: ["mythic_land", "mythic_naval"] },
  ];
  return (
    <div className="unit-groups">
      {groups.map((group) => {
        const entries = Object.entries(units).filter(
          ([id, amount]) =>
            amount > 0 &&
            lookup.get(id)?.domain &&
            group.domains.includes(lookup.get(id)!.domain) &&
            !(
              group.name === "Transport" && lookup.get(id)?.role !== "TRANSPORT"
            ) &&
            !(group.name === "Naval" && lookup.get(id)?.role === "TRANSPORT"),
        );
        return entries.length ? (
          <div key={group.name}>
            <span>{group.name}</span>
            <strong>
              {entries
                .map(
                  ([id, amount]) => `${amount} ${lookup.get(id)?.label ?? id}`,
                )
                .join(" · ")}
            </strong>
          </div>
        ) : null;
      })}
    </div>
  );
}
function Dossier({
  cityId,
  advice,
  catalogue,
}: {
  cityId: number;
  advice: Advice;
  catalogue: Unit[];
}) {
  const city = useQuery({
    queryKey: ["target-city", cityId],
    queryFn: () => api<City>(`/api/cities/${cityId}`),
  });
  const allianceId = city.data?.owner?.alliance_id;
  const alliance = useQuery({
    queryKey: ["target-alliance", allianceId],
    queryFn: () => api<Alliance>(`/api/alliances/${allianceId}`),
    enabled: !!allianceId,
  });
  const targets = useQuery({
    queryKey: ["target-intelligence"],
    queryFn: () =>
      api<{ items: TargetIntel[] }>("/api/intelligence/targets?limit=100"),
  });
  const threats = useQuery({
    queryKey: ["threat-intelligence"],
    queryFn: () =>
      api<{ items: ThreatIntel[] }>("/api/intelligence/threats?limit=100"),
  });
  if (city.isLoading)
    return (
      <section className="target-dossier">
        <Skeleton className="h-24 w-full" />
      </section>
    );
  const data = city.data;
  const targetIntel = targets.data?.items.find((item) => item.city_id === cityId);
  const threatIntel = threats.data?.items.find(
    (item) => item.player_id === data?.owner?.id,
  );
  return (
    <section className="target-dossier">
      <header>
        <div>
          <p className="eyebrow">DOSSIER CIBLE</p>
          <h3>{data?.name ?? "Cible"}</h3>
        </div>
        {data?.is_ghost ? (
          <Badge variant="outline">Ville fantôme</Badge>
        ) : (
          <Badge variant="outline">
            {targetIntel?.risk ?? "Risque géopolitique à confirmer"}
          </Badge>
        )}
      </header>
      <div className="dossier-grid">
        <article>
          <span>Joueur</span>
          <strong>{data?.owner?.name ?? "Aucun propriétaire"}</strong>
        </article>
        <article>
          <span>Alliance</span>
          <strong>
            {alliance.data?.name ??
              (allianceId ? "Alliance identifiée" : "Sans alliance")}
          </strong>
        </article>
        <article>
          <span>Points</span>
          <strong>{data?.points?.toLocaleString("fr-FR") ?? "Inconnus"}</strong>
        </article>
        <article>
          <span>Renseignement</span>
          <strong>
            {advice.target.last_spy_hours === undefined
              ? "Absent"
              : `${advice.target.last_spy_hours} h`}
          </strong>
        </article>
        <article>
          <span>Opportunité</span>
          <strong>{targetIntel?.target_score ?? "À évaluer"}</strong>
        </article>
        <article>
          <span>Menace</span>
          <strong>{threatIntel?.score ?? "Non signalée"}</strong>
        </article>
        <article className="wide">
          <span>Défense connue</span>
          <UnitGroups
            units={advice.target.known_defense ?? {}}
            catalogue={catalogue}
          />
        </article>
      </div>
      {data && (
        <ViewTargetOnMap
          cityId={cityId}
          name={data.name}
          coordinates={`${data.x}|${data.y}`}
          source="conseiller"
        />
      )}
    </section>
  );
}
export function CombatAdvice({ cityId }: { cityId: number }) {
  const query = useQuery({
    queryKey: ["combat-advice", cityId],
    queryFn: () =>
      api<Advice>("/api/combat/advice", {
        method: "POST",
        body: JSON.stringify({ target_city_id: cityId }),
      }),
  });
  const catalogue = useQuery({
    queryKey: ["unit-catalogue"],
    queryFn: () => api<{ items: Unit[] }>("/api/game-data/units"),
  });
  const router = useRouter();
  const selectPlan = useTargetContext((state) => state.selectPlan);
  if (query.isLoading)
    return (
      <section className="panel">
        <div className="panel-body">
          <Skeleton className="h-8 w-52" />
          <Skeleton className="mt-4 h-24 w-full" />
        </div>
      </section>
    );
  if (query.error)
    return (
      <p className="error">Analyse indisponible : {query.error.message}</p>
    );
  const advice = query.data!;
  const units = catalogue.data?.items ?? [];
  const best = advice.plans[0];
  return (
    <section className="advice-stack">
      <Dossier cityId={cityId} advice={advice} catalogue={units} />
      <header className="advice-hero">
        <div>
          <p className="eyebrow">CONSEILLER D’ATTAQUE · LECTURE SEULE</p>
          <h2>{label[advice.recommendation] ?? advice.recommendation}</h2>
          <p>
            {advice.reasons[0] ??
              "Aucune conclusion sans renseignement récent."}
          </p>
        </div>
        <strong className="confidence">
          <ShieldAlert size={16} />
          {advice.confidence}% confiance
        </strong>
      </header>
      {best && (
        <div className="plan-summary">
          <article>
            <span>Meilleure origine</span>
            <strong>{best.origin.name}</strong>
          </article>
          <article>
            <span>Distance</span>
            <strong>{best.distance} cases</strong>
          </article>
          <article>
            <span>Durée estimée</span>
            <strong>
              <Clock3 size={15} />
              {duration(best.travel_seconds)}
            </strong>
          </article>
          <article>
            <span>Ratio terrestre</span>
            <strong>{best.simulation.land.ratio}×</strong>
          </article>
        </div>
      )}
      <section>
        <p className="eyebrow">PLANS D’ATTAQUE COMPARÉS</p>
        <div className="attack-plan-grid">
          {advice.plans.length ? (
            advice.plans.map((plan, index) => (
              <article className="attack-plan-card" key={plan.origin.name}>
                <header>
                  <div>
                    <span>
                      PLAN {index + 1}
                      {index === 0 ? " · RECOMMANDÉ" : ""}
                    </span>
                    <h3>{plan.origin.name}</h3>
                  </div>
                  <Badge variant={index === 0 ? "default" : "outline"}>
                    {plan.simulation.confidence}% confiance
                  </Badge>
                </header>
                <dl>
                  <div>
                    <span>Unités disponibles</span>
                    <UnitGroups
                      units={plan.available_units}
                      catalogue={units}
                    />
                  </div>
                  <div>
                    <span>Composition conseillée</span>
                    <UnitGroups
                      units={plan.recommended_composition}
                      catalogue={units}
                    />
                    <em>{plan.composition_note}</em>
                  </div>
                  <div className="plan-facts">
                    <span>
                      <Clock3 size={14} />
                      {duration(plan.travel_seconds)}
                    </span>
                    <span>
                      <Target size={14} />
                      {plan.distance} cases
                    </span>
                    <span>
                      <Swords size={14} />
                      Sol {plan.simulation.land.ratio}×
                    </span>
                    <span>Naval {plan.simulation.naval.ratio}×</span>
                  </div>
                </dl>
                <footer>
                  <span>Minimum : {plan.minimum_margin}</span>
                  <button
                    className="secondary-button"
                    onClick={() => {
                      selectPlan({
                        originId: plan.origin.city_id,
                        originName: plan.origin.name,
                        composition: plan.recommended_composition,
                        unitSpeed: plan.unit_speed,
                      });
                      router.push("/planner");
                    }}
                  >
                    <CalendarClock size={15} />
                    Planifier ce plan
                  </button>
                </footer>
              </article>
            ))
          ) : (
            <p className="empty">Aucune armée personnelle synchronisée.</p>
          )}
        </div>
      </section>
      <div className="advice-grid">
        <section>
          <p className="eyebrow">SÉQUENCE CONSEILLÉE</p>
          {advice.playbook.map((step) => (
            <article
              className={`playbook-step ${step.status}`}
              key={step.stage}
            >
              <div>
                <strong>{label[step.stage] ?? step.stage}</strong>
                <p>{step.reason}</p>
              </div>
              <Eye size={16} />
            </article>
          ))}
        </section>
        <section className="advice-guidance">
          <p className="eyebrow">COMMENT LIRE CE CONSEIL</p>
          <p>
            La proposition n’envoie rien. Elle part des unités actuellement
            disponibles, affiche la marge de sécurité et écarte tout bonus non
            observé.
          </p>
          <Swords size={18} />
        </section>
      </div>
      {advice.target.last_spy_hours !== undefined && (
        <p className="freshness-note">
          Renseignement observé il y a {advice.target.last_spy_hours} h. Les
          paramètres non observés restent exclus du verdict.
        </p>
      )}
    </section>
  );
}
