"use client";
import { useParams } from "next/navigation";
import { EntityDetail } from "@/components/entity-detail";
export default function PlayerPage() { const { id } = useParams<{ id: string }>(); return <EntityDetail title="Joueur" id={id} endpoint={`/api/players/${id}`}/>; }
