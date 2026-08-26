"use client";

import Link from "next/link";
import { useMemo, useState, type CSSProperties } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  AnalyzeTargetButton,
  PlanTargetButton,
} from "@/components/target-actions";

type City = {
  id: number;
  name: string;
  x: number;
  y: number;
  points: number;
  is_ghost: boolean;
  player_id?: number | null;
  alliance_id?: number | null;
  alliance_name?: string | null;
  player_name?: string | null;
  island_x?: number;
  island_y?: number;
  distance_to_me?: number;
  threat_score?: number;
  target_score?: number;
  relation?: string;
};
type Props = {
  cities: City[];
  referenceCities?: City[];
  onSelect?: (city: City) => void;
  selected?: number;
};
type Focus = { x: number; y: number; zoom: number } | undefined;
const scoreTone = (city: City) =>
  Math.max(city.target_score ?? 0, city.threat_score ?? 0) >= 70
    ? "score-high"
    : Math.max(city.target_score ?? 0, city.threat_score ?? 0) >= 40
      ? "score-mid"
      : "";
export function StrategicMap({
  cities,
  referenceCities,
  onSelect,
  selected,
}: Props) {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<City>();
  const reference = referenceCities?.length ? referenceCities : cities;
  const bounds = useMemo(
    () => {
      const citiesForBounds = reference.length
        ? reference
        : [{ id: 0, name: "", x: 0, y: 0, points: 0, is_ghost: false }];
      return {
        minX: Math.min(...citiesForBounds.map((city) => city.x)),
        maxX: Math.max(...citiesForBounds.map((city) => city.x)),
        minY: Math.min(...citiesForBounds.map((city) => city.y)),
        maxY: Math.max(...citiesForBounds.map((city) => city.y)),
      };
    },
    [reference],
  );
  const point = (city: City) => ({
    x:
      8 +
      (84 * (city.x - bounds.minX)) / Math.max(bounds.maxX - bounds.minX, 1),
    y:
      8 +
      (84 * (city.y - bounds.minY)) / Math.max(bounds.maxY - bounds.minY, 1),
  });
  const target = selected
    ? reference.find((city) => city.id === selected)
    : undefined;
  const empire = reference.filter((city) => city.relation === "SELF");
  const initial = target ? point(target) : undefined;
  const [focus, setFocus] = useState<Focus>(
    initial ? { ...initial, zoom: 1.65 } : undefined,
  );
  const transform = focus
    ? `translate(${(50 - focus.x) / focus.zoom}%, ${(50 - focus.y) / focus.zoom}%) scale(${focus.zoom})`
    : `translate(${offset.x}px,${offset.y}px) scale(${zoom})`;
  const setView = (city?: City, viewZoom = 1.65) => {
    if (!city) {
      setFocus(undefined);
      setZoom(1);
      setOffset({ x: 0, y: 0 });
      return;
    }
    setFocus({ ...point(city), zoom: viewZoom });
  };
  const centerEmpire = () => {
    if (!empire.length) return;
    setFocus({
      x:
        empire.reduce((total, city) => total + point(city).x, 0) /
        empire.length,
      y:
        empire.reduce((total, city) => total + point(city).y, 0) /
        empire.length,
      zoom: 1.45,
    });
  };
  const release = () => setFocus(undefined);
  const select = (city: City) => {
    setActive(city);
    setOpen(true);
    onSelect?.(city);
    setView(city);
  };
  if (!cities.length)
    return <div className="map-empty">Aucune cité dans ce filtre.</div>;
  return (
    <>
      <div className="map-frame">
        <div className="map-controls">
          <button disabled={!target} onClick={() => target && setView(target)}>
            Centrer cible
          </button>
          <button disabled={!empire.length} onClick={centerEmpire}>
            Centrer empire
          </button>
          <button onClick={() => setView()}>Vue globale</button>
          <button
            aria-label="Zoomer"
            onClick={() => {
              release();
              setZoom((value) => Math.min(3, value + 0.25));
            }}
          >
            +
          </button>
          <button
            aria-label="Dézoomer"
            onClick={() => {
              release();
              setZoom((value) => Math.max(0.6, value - 0.25));
            }}
          >
            −
          </button>
        </div>
        <div
          className="strategic-map"
          onWheel={(event) => {
            event.preventDefault();
            release();
            setZoom((value) =>
              Math.max(
                0.6,
                Math.min(3, value + (event.deltaY < 0 ? 0.12 : -0.12)),
              ),
            );
          }}
          onPointerDown={(event) => {
            release();
            const start = { x: event.clientX, y: event.clientY, offset };
            const move = (pointer: PointerEvent) =>
              setOffset({
                x: start.offset.x + pointer.clientX - start.x,
                y: start.offset.y + pointer.clientY - start.y,
              });
            const up = () => {
              window.removeEventListener("pointermove", move);
              window.removeEventListener("pointerup", up);
            };
            window.addEventListener("pointermove", move);
            window.addEventListener("pointerup", up);
          }}
        >
          <div className="map-world" style={{ transform }}>
            {cities.map((city) => {
              const position = point(city);
              const relation = city.is_ghost
                ? "ghost"
                : (city.relation?.toLowerCase() ?? "neutral");
              const score = Math.max(
                city.target_score ?? 0,
                city.threat_score ?? 0,
              );
              const hint = [
                city.name,
                city.player_name ?? "Ville fantôme",
                city.alliance_name,
                city.target_score ? `Cible ${city.target_score}` : "",
                city.threat_score ? `Menace ${city.threat_score}` : "",
              ]
                .filter(Boolean)
                .join(" · ");
              return (
                <button
                  title={hint}
                  onClick={() => select(city)}
                  className={`map-city ${relation} ${scoreTone(city)} ${selected === city.id ? "selected" : ""}`}
                  style={
                    {
                      left: `${position.x}%`,
                      top: `${position.y}%`,
                      "--score": String(score),
                    } as CSSProperties
                  }
                  key={city.id}
                >
                  <span className="map-tooltip">{hint}</span>
                  <span className="sr-only">{city.name}</span>
                </button>
              );
            })}
          </div>
          <div className="map-legend">
            <span className="self">Moi</span>
            <span className="ally">Allié</span>
            <span className="unknown">Autre / inconnu</span>
            <span className="ghost">Fantôme</span>
            <span className="score-high">Score fort</span>
          </div>
          <div className="map-scale">Molette ou glisser pour explorer</div>
        </div>
      </div>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>{active?.name ?? "Ville"}</SheetTitle>
            <SheetDescription>
              {active &&
                `${active.x}|${active.y} · ${active.points.toLocaleString("fr-FR")} points`}
            </SheetDescription>
          </SheetHeader>
          {active && <CityDetails city={active} />}
        </SheetContent>
      </Sheet>
    </>
  );
}
function CityDetails({ city }: { city: City }) {
  return (
    <div className="sheet-city">
      <dl className="key-values">
        <div>
          <span>Île</span>
          <strong>
            {city.island_x !== undefined
              ? `${city.island_x}|${city.island_y}`
              : "Non renseignée"}
          </strong>
        </div>
        <div>
          <span>Menace</span>
          <strong>{city.threat_score ?? "—"}</strong>
        </div>
        <div>
          <span>Cible</span>
          <strong>{city.target_score ?? "—"}</strong>
        </div>
      </dl>
      <section className="sheet-section">
        <span>Joueur</span>
        {city.player_id ? (
          <Link className="table-link" href={`/player/${city.player_id}`}>
            {city.player_name ?? "Voir le joueur"}
          </Link>
        ) : (
          "Fantôme"
        )}
      </section>
      <section className="sheet-section">
        <span>Alliance</span>
        {city.alliance_id ? (
          <Link className="table-link" href={`/alliance/${city.alliance_id}`}>
            {city.alliance_name ?? "Voir l’alliance"}
          </Link>
        ) : (
          "Sans alliance"
        )}
      </section>
      <div className="sheet-actions">
        <Link className="secondary-link" href={`/city/${city.id}`}>
          Voir ville
        </Link>
        <AnalyzeTargetButton
          cityId={city.id}
          name={city.name}
          coordinates={`${city.x}|${city.y}`}
          source="carte"
        />
        <PlanTargetButton
          cityId={city.id}
          name={city.name}
          coordinates={`${city.x}|${city.y}`}
          source="carte"
        />
      </div>
    </div>
  );
}
