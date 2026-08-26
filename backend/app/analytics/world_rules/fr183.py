from datetime import datetime, timedelta
from app.analytics.config import ANTI_TIMING_SECONDS, SAFE_OPERATION_MARGIN_SECONDS

REVOLT_PREPARATION_HOURS = 12
REVOLT_ACTIVE_HOURS = 12
NIGHT_BONUS_START = "00:00"
NIGHT_BONUS_END = "08:00"

def calculate_revolt_window(activation_time: datetime) -> dict[str, datetime]:
    return {"preparation_start": activation_time - timedelta(hours=REVOLT_PREPARATION_HOURS), "active_start": activation_time, "active_end": activation_time + timedelta(hours=REVOLT_ACTIVE_HOURS)}
