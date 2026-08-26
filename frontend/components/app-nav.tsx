"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Crosshair, LayoutDashboard, Map, ShieldAlert, Swords, Users, Settings, CalendarClock, FlaskConical, Castle } from "lucide-react";

const items = [
  ["Dashboard", "/dashboard", LayoutDashboard], ["Carte tactique", "/map", Map], ["Joueurs", "/players", Users], ["Alliances", "/alliances", Users],
  ["Cibles", "/targets", Crosshair], ["Menaces", "/threats", ShieldAlert], ["Événements", "/events", Bell], ["Empire", "/empire", Castle], ["Planificateur", "/planner", CalendarClock], ["Simulateur", "/simulator", FlaskConical], ["Réglages", "/settings", Settings],
] as const;
export function AppNav() { const pathname = usePathname(); return <nav className="app-nav"><Link className="brand" href="/dashboard"><span className="brand-mark"><Swords/></span>GREPO<span>INTEL</span></Link><p className="nav-label">INTELLIGENCE</p>{items.map(([label, href, Icon]) => <Link key={href} href={href} className={`nav-link ${pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`)) ? "active" : ""}`}><Icon/>{label}</Link>)}<div className="nav-footer"><span className="online-dot"/>Système opérationnel<br/><small>FR183 · lecture seule</small></div></nav>; }
