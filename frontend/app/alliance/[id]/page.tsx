"use client";
import { useParams } from "next/navigation";
import { EntityDetail } from "@/components/entity-detail";
export default function AlliancePage() { const { id } = useParams<{ id: string }>(); return <EntityDetail title="Alliance" id={id} endpoint={`/api/alliances/${id}`}/>; }
