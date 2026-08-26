"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Eye, Map, ShieldAlert, Target } from "lucide-react";
import { AppNav } from "@/components/app-nav";
import { AnalyzeTargetButton } from "@/components/target-actions";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
type TargetRow = {
  city_id: number;
  name: string;
  x: number;
  y: number;
  target_score: number;
  distance: number;
  reasons: { message: string }[];
};
type Threat = {
  player_id: number;
  name: string;
  score: number;
  level: string;
  nearest_distance: number;
  reasons: { message: string }[];
};
type Overview = {
  player: { name: string; points: number; rank: number; cities_count: number };
  threats: Threat[];
  opportunities: TargetRow[];
  recommendations: { title: string; message: string; category: string }[];
  environment: { nearby_threat_count: number; island_opportunities: number };
  data_freshness: { latest_snapshot_at?: string; reason?: string };
};
type Personal = {
  connected: boolean;
  last_snapshot_at?: string;
  cities: number;
};
const fresh = (value?: string) =>
  value ? new Date(value).toLocaleString("fr-FR") : "Non disponible";
export default function Dashboard() {
  const query = useQuery({
    queryKey: ["overview"],
    queryFn: () => api<Overview>("/api/intelligence/overview"),
  });
  const personal = useQuery({
    queryKey: ["personal-status"],
    queryFn: () => api<Personal>("/api/personal-state/status"),
  });
  const data = query.data;
  return (
    <div className="app-shell">
      <AppNav />
      <main className="workspace">
        <header className="page-heading">
          <div>
            <p className="eyebrow">FR183 · CENTRE DE COMMANDEMENT</p>
            <h1>Bonjour, {data?.player.name ?? "Abator"}</h1>
            <p className="lead">
              Ce qui mérite votre attention, les risques proches et les
              opportunités exploitables.
            </p>
          </div>
          <Link className="secondary-button" href="/map">
            <Map size={15} />
            Ouvrir la carte
          </Link>
        </header>
        {query.isLoading ? (
          <div className="metric-grid">
            {[1, 2, 3, 4].map((item) => (
              <Skeleton className="h-28" key={item} />
            ))}
          </div>
        ) : (
          data && (
            <>
              <section className="freshness-strip">
                <span>
                  Public · {fresh(data.data_freshness.latest_snapshot_at)}
                </span>
                <span>
                  Personnel ·{" "}
                  {personal.data?.connected
                    ? `${personal.data.cities} villes · ${fresh(personal.data.last_snapshot_at)}`
                    : "Companion à synchroniser"}
                </span>
              </section>
              <section className="situation-bar">
                <div>
                  <span>Que se passe-t-il ?</span>
                  <strong>
                    {data.environment.nearby_threat_count} menace(s) active(s) ·{" "}
                    {data.environment.island_opportunities} opportunité(s)
                    insulaire(s)
                  </strong>
                </div>
                <div>
                  <span>Mon empire</span>
                  <strong>
                    {data.player.cities_count} villes · rang #{data.player.rank}
                  </strong>
                </div>
                <div>
                  <span>Prochaine action</span>
                  <strong>
                    {data.recommendations[0]?.title ?? "Sélectionner une cible"}
                  </strong>
                </div>
              </section>
              <section className="dashboard-focus">
                <div>
                  <p className="eyebrow">À FAIRE MAINTENANT</p>
                  <h2>
                    {data.recommendations[0]?.title ??
                      "Aucune alerte prioritaire"}
                  </h2>
                  <p>
                    {data.recommendations[0]?.message ??
                      "Les données publiques sont calmes pour le moment."}
                  </p>
                  {data.opportunities[0] && (
                    <AnalyzeTargetButton
                      cityId={data.opportunities[0].city_id}
                      name={data.opportunities[0].name}
                      coordinates={`${data.opportunities[0].x}|${data.opportunities[0].y}`}
                      source="dashboard"
                    />
                  )}
                </div>
              </section>
              <div className="dashboard-columns">
                <section className="panel">
                  <header className="panel-head">
                    <h2>
                      <ShieldAlert size={16} />
                      Qui surveiller ?
                    </h2>
                    <Link className="table-link" href="/threats">
                      Tout voir <ArrowRight size={14} />
                    </Link>
                  </header>
                  <div className="panel-body">
                    {data.threats.slice(0, 3).map((item) => (
                      <Link
                        className="signal actionable"
                  href={`/threats#threat-${item.player_id}`}
                        key={item.player_id}
                      >
                        <div>
                          <strong>{item.name}</strong>
                          <span>
                            {item.reasons[0]?.message ??
                              `${item.nearest_distance} cases`}
                          </span>
                        </div>
                        <Badge
                          variant={item.score >= 70 ? "destructive" : "outline"}
                        >
                          {item.score}
                        </Badge>
                      </Link>
                    ))}
                  </div>
                </section>
                <section className="panel">
                  <header className="panel-head">
                    <h2>
                      <Target size={16} />
                      Quelles opportunités ?
                    </h2>
                    <Link className="table-link" href="/targets">
                      Tout voir <ArrowRight size={14} />
                    </Link>
                  </header>
                  <div className="panel-body">
                    {data.opportunities.slice(0, 3).map((item) => (
                      <article className="signal actionable" key={item.city_id}>
                        <div>
                          <strong>{item.name}</strong>
                          <span>
                            {item.distance} cases · {item.reasons[0]?.message}
                          </span>
                        </div>
                        <AnalyzeTargetButton
                          cityId={item.city_id}
                          name={item.name}
                          coordinates={`${item.x}|${item.y}`}
                          source="dashboard"
                          compact
                        />
                      </article>
                    ))}
                  </div>
                </section>
              </div>
              <section className="dashboard-question-grid">
                <Link href="/threats">
                  <Eye size={18} />
                  <div>
                    <strong>Qui surveiller ?</strong>
                    <span>Pression, activité et distance.</span>
                  </div>
                </Link>
                <Link href="/targets">
                  <Target size={18} />
                  <div>
                    <strong>Quelle opportunité ?</strong>
                    <span>Cibles filtrées par risque et territoire.</span>
                  </div>
                </Link>
                <Link href="/empire">
                  <Map size={18} />
                  <div>
                    <strong>Que préparer ?</strong>
                    <span>État réel et recommandations de villes.</span>
                  </div>
                </Link>
              </section>
            </>
          )
        )}
      </main>
    </div>
  );
}
