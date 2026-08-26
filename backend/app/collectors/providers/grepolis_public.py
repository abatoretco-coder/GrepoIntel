"""Read-only, rate-limited adapter for official public Grepolis world exports."""
import csv
import gzip
import io
import logging
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PublicWorldData:
    players: list[dict[str, str]]
    alliances: list[dict[str, str]]
    towns: list[dict[str, str]]
    player_kills_attack: list[dict[str, str]]
    player_kills_defense: list[dict[str, str]]

class GrepolisPublicProvider:
    """Only downloads public exports once per requested import; never contacts game UI."""
    user_agent = "GrepoIntel/0.1 (read-only public data collector)"

    def __init__(self, world_code: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = f"https://{world_code.lower()}.grepolis.com/data"
        self.timeout = httpx.Timeout(timeout_seconds)

    async def _download_rows(self, client: httpx.AsyncClient, filename: str, fields: tuple[str, ...]) -> list[dict[str, str]]:
        response = await client.get(f"{self.base_url}/{filename}.txt.gz")
        response.raise_for_status()
        decoded = gzip.decompress(response.content).decode("utf-8", errors="replace")
        return [dict(zip(fields, row)) for row in csv.reader(io.StringIO(decoded)) if len(row) >= len(fields)]

    async def fetch(self) -> PublicWorldData:
        logger.info("collector.start", extra={"world": self.base_url})
        headers = {"User-Agent": self.user_agent, "Accept": "application/gzip"}
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
            players = await self._download_rows(client, "players", ("external_id", "name", "alliance_external_id", "points", "rank", "cities_count"))
            alliances = await self._download_rows(client, "alliances", ("external_id", "name", "points", "cities_count", "members_count", "rank"))
            towns = await self._download_rows(client, "towns", ("external_id", "player_external_id", "name", "island_x", "island_y", "number_on_island", "points"))
            attack = await self._download_rows(client, "player_kills_att", ("rank", "player_external_id", "points"))
            defense = await self._download_rows(client, "player_kills_def", ("rank", "player_external_id", "points"))
        logger.info("collector.success", extra={"players": len(players), "towns": len(towns)})
        return PublicWorldData(players, alliances, towns, attack, defense)
