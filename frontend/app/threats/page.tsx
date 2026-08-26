"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ChevronDown, Crosshair, Eye, ShieldAlert } from "lucide-react";
import { AppNav } from "@/components/app-nav";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useTargetContext } from "@/lib/target-context";
type City = { id: number; name: string; x: number; y: number; points: number };
type Threat = {
  player_id: number;
  name: string;
  alliance?: { name: string };
  score: number;
  level: string;
  nearest_distance: number;
  nearby_city_count: number;
  reasons: { message: string }[];
};
type Player = { cities: City[] };
const distance = (a: City, b: City) => Math.hypot(a.x - b.x, a.y - b.y);
function ThreatRow({ item, ownCities }: { item: Threat; ownCities: City[] }) {
  const details = useQuery({
    queryKey: ["threat-player", item.player_id],
    queryFn: () => api<Player>(`/api/players/${item.player_id}`),
  });
  const router = useRouter();
  const setTarget = useTargetContext((state) => state.setTarget);
  const ranked = useMemo(
    () =>
      [...(details.data?.cities ?? [])].sort(
        (a, b) =>
          Math.min(...ownCities.map((own) => distance(a, own))) -
          Math.min(...ownCities.map((own) => distance(b, own))),
      ),
    [details.data, ownCities],
  );
  const [selected, setSelected] = useState("");
  const city =
    ranked.find((value) => String(value.id) === selected) ?? ranked[0];
  function analyse() {
    if (!city) return;
    setTarget({
      cityId: city.id,
      name: city.name,
      coordinates: `${city.x}|${city.y}`,
      source: "menaces",
    });
    router.push("/simulator");
  }
  return (
    <article id={`threat-${item.player_id}`} className="threat-card">
      <div className="threat-score">
        <strong>{item.score}</strong>
        <span>score</span>
      </div>
      <div className="threat-copy">
        <p className="eyebrow">{item.level}</p>
        <h2>{item.name}</h2>
        <p>
          {item.alliance?.name ?? "Sans alliance"} · {item.nearest_distance}{" "}
          cases · {item.nearby_city_count} ville(s) proche(s)
        </p>
        <span>{item.reasons[0]?.message ?? "Signal à confirmer"}</span>
      </div>
      <Badge variant={item.score >= 70 ? "destructive" : "outline"}>
        <ShieldAlert size={13} />
        {item.level}
      </Badge>
      <div className="threat-actions">
        {details.isLoading ? (
          <span className="muted">Recherche des villes…</span>
        ) : city ? (
          <label className="city-choice">
            <span>Ville à analyser</span>
            <select
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
            >
              {ranked.map((value, index) => (
                <option key={value.id} value={index === 0 ? "" : value.id}>
                  {value.name} · {value.x}|{value.y}
                  {index === 0 ? " · la plus proche" : ""}
                </option>
              ))}
            </select>
            <ChevronDown size={14} />
          </label>
        ) : (
          <span className="muted">Aucune ville publique</span>
        )}
        <button className="action-button" disabled={!city} onClick={analyse}>
          <Crosshair size={16} />
          Analyser
        </button>
        <button
          className="secondary-button"
          onClick={() => router.push(`/player/${item.player_id}`)}
        >
          <Eye size={15} />
          Fiche
        </button>
      </div>
    </article>
  );
}
export default function ThreatsPage() {
  const query = useQuery({
    queryKey: ["threats"],
    queryFn: () =>
      api<{ items: Threat[] }>("/api/intelligence/threats?limit=30"),
  });
  const own = useQuery({
    queryKey: ["my-cities"],
    queryFn: () => api<City[]>("/api/me/cities"),
  });
  return (
    <div className="app-shell">
      <AppNav />
      <main className="workspace">
        <header className="page-heading">
          <div>
            <p className="eyebrow">RENSEIGNEMENT · PRESSION</p>
            <h1>Menaces à surveiller</h1>
            <p className="lead">
              La ville proposée est maintenant celle qui est la plus proche de
              votre empire. Vous pouvez choisir n’importe quelle autre ville
              connue avant d’ouvrir le conseiller.
            </p>
          </div>
        </header>
        {query.error && <p className="error">{query.error.message}</p>}
        <div className="threat-list">
          {query.data?.items.map((item) => (
            <ThreatRow
              item={item}
              ownCities={own.data ?? []}
              key={item.player_id}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
