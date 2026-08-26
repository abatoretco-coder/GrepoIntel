"use client";

import { useEffect, useRef } from "react";

type City = { id: number; name: string; x: number; y: number; points: number; is_ghost: boolean; player_id?: number | null };
export function StrategicMap({ cities }: { cities: City[] }) {
  const node = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!node.current || !cities.length) return;
    let map: import("maplibre-gl").Map | undefined;
    let cancelled = false;
    import("maplibre-gl").then((module) => {
      if (cancelled || !node.current) return;
      const maplibregl = module.default;
      const points = cities.map((city) => [city.x, city.y] as [number, number]);
      map = new maplibregl.Map({ container: node.current, style: { version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#111827" } }] }, center: points[0], zoom: 4, attributionControl: false });
      map.on("load", () => { map?.addSource("cities", { type: "geojson", cluster: true, clusterRadius: 42, clusterMaxZoom: 7, data: { type: "FeatureCollection", features: cities.map((city) => ({ type: "Feature", properties: city, geometry: { type: "Point", coordinates: [city.x, city.y] } })) } }); map?.addLayer({ id:"clusters",type:"circle",source:"cities",filter:["has","point_count"],paint:{"circle-color":"#236aa6","circle-radius":["step",["get","point_count"],16,30,22,100,29],"circle-stroke-color":"#a5e7ff","circle-stroke-width":1}}); map?.addLayer({id:"cluster-count",type:"symbol",source:"cities",filter:["has","point_count"],layout:{"text-field":["get","point_count_abbreviated"],"text-size":12},paint:{"text-color":"#eff9ff"}}); map?.addLayer({ id: "cities", type: "circle", source: "cities",filter:["!",["has","point_count"]], paint: { "circle-radius": ["interpolate", ["linear"], ["get", "points"], 0, 4, 50000, 10], "circle-color": ["case", ["get", "is_ghost"], "#b56cff", "#4e9cff"], "circle-stroke-color": "#d9edff", "circle-stroke-width": 1 } }); map?.on("click", "clusters", (event) => { const feature=map?.queryRenderedFeatures(event.point,{layers:["clusters"]})[0]; const clusterId=Number(feature?.properties?.cluster_id); const source=map?.getSource("cities") as import("maplibre-gl").GeoJSONSource; source?.getClusterExpansionZoom(clusterId).then(zoom=>map?.easeTo({center:event.lngLat,zoom})); }); map?.on("click", "cities", (event) => { const feature = event.features?.[0]; if (!feature) return; const p = feature.properties as City & {city_id?:number}; new maplibregl.Popup().setLngLat(event.lngLat).setHTML(`<strong>${p.name}</strong><br>${Number(p.points).toLocaleString("fr-FR")} points<br><a href="/city/${p.id ?? p.city_id}">Ouvrir la fiche</a>`).addTo(map!); }); if (points.length > 1) map?.fitBounds(points.reduce((bounds, point) => bounds.extend(point), new maplibregl.LngLatBounds(points[0], points[0])), { padding: 48, maxZoom: 7 }); });
    });
    return () => { cancelled = true; map?.remove(); };
  }, [cities]);
  return <div className="strategic-map" ref={node}/>;
}
