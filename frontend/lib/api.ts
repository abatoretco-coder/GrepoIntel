export const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:18000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "La requête API a échoué.");
  }
  return response.json() as Promise<T>;
}
