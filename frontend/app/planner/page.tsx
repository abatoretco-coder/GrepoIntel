"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CalendarClock, MapPin } from "lucide-react";
import { AppNav } from "@/components/app-nav";
import { api } from "@/lib/api";
import { useTargetContext } from "@/lib/target-context";
type City = { id: number; name: string; x: number; y: number; points: number };
type Travel = {
  distance: number;
  estimated_travel_seconds: number;
  suggested_departure?: string;
};
type Unit = { id: string; label: string };
const label = (city: City) => `${city.name} · ${city.x}|${city.y}`;
const duration = (value: number) =>
  `${Math.floor(value / 3600)} h ${Math.round((value % 3600) / 60)} min`;
export default function PlannerPage() {
  const target = useTargetContext((state) => state.target);
  const cities = useQuery({
    queryKey: ["my-cities"],
    queryFn: () => api<City[]>("/api/me/cities"),
  });
  const catalogue = useQuery({
    queryKey: ["unit-catalogue"],
    queryFn: () => api<{ items: Unit[] }>("/api/game-data/units"),
  });
  const [origin, setOrigin] = useState("");
  const [arrival, setArrival] = useState("");
  const [result, setResult] = useState<Travel>();
  const [error, setError] = useState("");
  const selectedOrigin = useMemo(
    () =>
      cities.data?.find(
        (city) =>
          String(city.id) === (origin || String(target?.plan?.originId ?? "")),
      ) || cities.data?.[0],
    [cities.data, origin, target?.plan?.originId],
  );
  const plan = target?.plan;
  const names = new Map(
    (catalogue.data?.items ?? []).map((unit) => [unit.id, unit.label]),
  );
  async function calculate(event: FormEvent) {
    event.preventDefault();
    setError("");
    setResult(undefined);
    if (!selectedOrigin || !target) {
      setError(
        "Choisissez une cible depuis la carte ou les cibles avant de planifier.",
      );
      return;
    }
    if (!plan) {
      setError(
        "Choisissez d’abord un plan dans le conseiller : sa vitesse et sa composition seront reprises ici.",
      );
      return;
    }
    try {
      setResult(
        await api<Travel>("/api/planner/travel", {
          method: "POST",
          body: JSON.stringify({
            origin_city_id: selectedOrigin.id,
            target_city_id: target.cityId,
            unit_speed: plan.unitSpeed,
            desired_arrival: arrival || null,
          }),
        }),
      );
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Calcul indisponible",
      );
    }
  }
  return (
    <div className="app-shell">
      <AppNav />
      <main className="workspace">
        <header className="page-heading">
          <div>
            <p className="eyebrow">OPÉRATION · PLANIFICATION</p>
            <h1>Préparer une arrivée</h1>
            <p className="lead">
              Calcul informatif uniquement. La cible active et le plan choisi
              sont conservés depuis le conseiller.
            </p>
          </div>
        </header>
        <form className="panel operation-form" onSubmit={calculate}>
          <div className="panel-body">
            <div className="detail-grid">
              <label className="field">
                Ville de départ
                <select
                  value={selectedOrigin ? String(selectedOrigin.id) : ""}
                  onChange={(event) => setOrigin(event.target.value)}
                >
                  {(cities.data ?? []).map((city) => (
                    <option value={city.id} key={city.id}>
                      {label(city)}
                    </option>
                  ))}
                </select>
              </label>
              <section className="target-lock">
                <span>Cible sélectionnée</span>
                {target ? (
                  <>
                    <strong>
                      <MapPin size={15} />
                      {target.name}
                      {target.coordinates ? ` · ${target.coordinates}` : ""}
                    </strong>
                    <Link href="/map">Changer sur la carte</Link>
                  </>
                ) : (
                  <>
                    <strong>Aucune cible active</strong>
                    <Link href="/targets">Choisir une cible</Link>
                  </>
                )}
              </section>
              <label className="field">
                Arrivée souhaitée{" "}
                <input
                  type="datetime-local"
                  value={arrival}
                  onChange={(event) => setArrival(event.target.value)}
                />
              </label>
            </div>
            {plan ? (
              <section className="selected-plan">
                <span>Plan repris</span>
                <strong>
                  {plan.originName} · vitesse {plan.unitSpeed}
                </strong>
                <p>
                  {Object.entries(plan.composition)
                    .filter(([, amount]) => amount > 0)
                    .map(
                      ([unit, amount]) =>
                        `${amount} ${names.get(unit) ?? unit}`,
                    )
                    .join(" · ")}
                </p>
              </section>
            ) : (
              <p className="freshness-note">
                Aucun plan sélectionné : ouvrez le conseiller et utilisez «
                Planifier ce plan ».
              </p>
            )}
            <button
              className="action-button"
              disabled={!target || !selectedOrigin || !plan}
            >
              <CalendarClock size={16} />
              Calculer le trajet
            </button>
            {error && <p className="error">{error}</p>}
            {result && (
              <section className="planner-result">
                <article>
                  <span>Distance</span>
                  <strong>{result.distance} cases</strong>
                </article>
                <article>
                  <span>Durée estimée</span>
                  <strong>{duration(result.estimated_travel_seconds)}</strong>
                </article>
                <article>
                  <span>Départ conseillé</span>
                  <strong>
                    {result.suggested_departure
                      ? new Date(result.suggested_departure).toLocaleString(
                          "fr-FR",
                        )
                      : "Choisissez une arrivée"}
                  </strong>
                </article>
              </section>
            )}
          </div>
        </form>
      </main>
    </div>
  );
}
