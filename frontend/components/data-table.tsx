import Link from "next/link";

type Row = Record<string, unknown>;
type Kind = "player" | "alliance" | "city" | "threat" | "target" | "event";
const number = (value: unknown) => typeof value === "number" ? value.toLocaleString("fr-FR") : "—";
const scoreClass = (score: unknown) => Number(score) >= 70 ? "high" : Number(score) >= 40 ? "medium" : "low";

export function DataTable({ rows, kind }: { rows: Row[]; kind: Kind }) {
  if (!rows.length) return <p className="empty">Aucune donnée ne correspond encore à cette vue.</p>;
  if (kind === "event") return <div>{rows.map((row, index) => <div className="alert" key={index}><i className="alert-marker"/><div><strong>{row.type === "conquest" ? "Conquête détectée" : "Changement d’alliance détecté"}</strong><span>{new Date(String(row.timestamp)).toLocaleString("fr-FR")} · Identifiant concerné : {String(row.city_id ?? row.player_id ?? "—")}</span></div></div>)}</div>;
  const headers = kind === "player" ? ["Joueur", "Alliance", "Points", "Rang", "Villes", "Fiche"] : kind === "alliance" ? ["Alliance", "Points", "Rang", "Membres", "Villes", "Fiche"] : kind === "city" ? ["Ville", "Coordonnées", "Points", "État", "Fiche"] : kind === "threat" ? ["Joueur", "Distance", "Niveau", "Score", "Signaux", "Fiche"] : ["Ville", "Distance", "Points", "Niveau", "Signaux", "Fiche"];
  return <div className="table-wrap"><table className="intel-table"><thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => {
    const id = Number(row.id ?? row.player_id ?? row.city_id); const entity = kind === "alliance" ? "alliance" : kind === "city" || kind === "target" ? "city" : "player";
    if (kind === "player") return <tr key={id || index}><td className="primary-cell">{String(row.name)}</td><td>{String(row.alliance_name ?? "Sans alliance")}</td><td>{number(row.points)}</td><td>#{number(row.rank)}</td><td>{number(row.cities_count)}</td><td><Link className="table-link" href={`/player/${id}`}>Analyser →</Link></td></tr>;
    if (kind === "alliance") return <tr key={id || index}><td className="primary-cell">{String(row.name)}</td><td>{number(row.points)}</td><td>#{number(row.rank)}</td><td>{number(row.members_count)}</td><td>{number(row.cities_count)}</td><td><Link className="table-link" href={`/alliance/${id}`}>Analyser →</Link></td></tr>;
    if (kind === "city") return <tr key={id || index}><td className="primary-cell">{String(row.name)}</td><td>{String(row.x ?? "—")} · {String(row.y ?? "—")}</td><td>{number(row.points)}</td><td><span className={`score ${Boolean(row.is_ghost) ? "medium" : "low"}`}>{Boolean(row.is_ghost) ? "Fantôme" : "Occupée"}</span></td><td><Link className="table-link" href={`/city/${id}`}>Analyser →</Link></td></tr>;
    const score = row.score ?? row.target_score;
    return <tr key={id || index}><td className="primary-cell">{String(row.name)}</td><td>{number(row.distance ?? row.nearest_distance)} cases</td><td>{number(row.points)}</td><td><span className={`score ${scoreClass(score)}`}>{number(score)}</span></td><td><div className="reason-list">{(Array.isArray(row.reasons) ? row.reasons : []).slice(0, 2).map((reason) => <span className="reason" key={String(reason)}>{typeof reason === "object" && reason ? String((reason as {message?:string}).message ?? "Signal") : String(reason)}</span>)}</div></td><td><Link className="table-link" href={`/${entity}/${id}`}>Analyser →</Link></td></tr>;
  })}</tbody></table></div>;
}
