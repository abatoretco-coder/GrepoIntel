"use client";
import { useParams } from "next/navigation";
import { EntityDetail } from "@/components/entity-detail";
export default function CityPage() { const { id } = useParams<{ id: string }>(); return <EntityDetail title="Ville" id={id} endpoint={`/api/cities/${id}`}/>; }
