"""AAS015-016 — 系統維運監控。

提供：線上人數、請求/錯誤計數、登入失敗次數、伺服器負載(CPU/記憶體)、異常警示。
請求與錯誤由 main.py 的中介層收集；指標由 ADMIN 透過 /api/aas/monitoring/metrics 查詢。
psutil 為選用相依：未安裝時 server_load 回傳 None，其餘指標仍可用。
"""
import threading
import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.aas.models import User

# 異常警示門檻
ERROR_RATE_ALERT = 0.2          # 錯誤率 >= 20%
ERROR_RATE_MIN_SAMPLES = 20     # 樣本數足夠才判斷錯誤率
LOGIN_FAILURE_ALERT = 5         # 登入失敗累計 >= 5 次
CPU_ALERT = 90.0                # CPU >= 90%
MEMORY_ALERT = 90.0             # 記憶體 >= 90%


class MetricsCollector:
    """行程內的即時指標收集器（執行緒安全）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.started_at = time.time()
        self.requests_total = 0
        self.errors_total = 0
        self.login_failures_total = 0

    def reset(self) -> None:
        with self._lock:
            self.started_at = time.time()
            self.requests_total = 0
            self.errors_total = 0
            self.login_failures_total = 0

    def record_request(self, status_code: int) -> None:
        with self._lock:
            self.requests_total += 1
            if status_code >= 500:
                self.errors_total += 1

    def record_login_failure(self) -> None:
        with self._lock:
            self.login_failures_total += 1

    def uptime_seconds(self) -> float:
        return time.time() - self.started_at


# 全域單例：中介層與服務層共用
metrics = MetricsCollector()


def _server_load() -> dict | None:
    """伺服器 CPU / 記憶體負載；psutil 未安裝時回傳 None。"""
    try:
        import psutil
    except ImportError:
        return None
    vm = psutil.virtual_memory()
    return {
        "cpu_percent": float(psutil.cpu_percent(interval=None)),
        "memory_percent": float(vm.percent),
        "memory_used_mb": round(vm.used / 1024 / 1024, 1),
        "memory_total_mb": round(vm.total / 1024 / 1024, 1),
    }


def _evaluate_alerts(error_rate: float, requests_total: int, login_failures: int, load: dict | None) -> list[dict]:
    alerts: list[dict] = []
    if requests_total >= ERROR_RATE_MIN_SAMPLES and error_rate >= ERROR_RATE_ALERT:
        alerts.append({"level": "CRITICAL", "code": "HIGH_ERROR_RATE",
                       "message": f"伺服器錯誤率偏高（{round(error_rate * 100, 1)}%）"})
    if login_failures >= LOGIN_FAILURE_ALERT:
        alerts.append({"level": "WARNING", "code": "LOGIN_FAILURE_SPIKE",
                       "message": f"登入失敗次數異常（累計 {login_failures} 次）"})
    if load is not None:
        if load["cpu_percent"] >= CPU_ALERT:
            alerts.append({"level": "WARNING", "code": "HIGH_CPU",
                           "message": f"CPU 負載過高（{load['cpu_percent']}%）"})
        if load["memory_percent"] >= MEMORY_ALERT:
            alerts.append({"level": "WARNING", "code": "HIGH_MEMORY",
                           "message": f"記憶體使用率過高（{load['memory_percent']}%）"})
    return alerts


def build_metrics(db: Session) -> dict:
    """組裝完整維運指標（AAS015 線上人數/負載 + AAS016 異常警示）。"""
    from app.modules.aas import service

    online_users = service.count_online_users(db)
    total_users = int(db.scalar(select(func.count(User.user_id))) or 0)

    requests_total = metrics.requests_total
    errors_total = metrics.errors_total
    login_failures = metrics.login_failures_total
    error_rate = round(errors_total / requests_total, 4) if requests_total else 0.0
    load = _server_load()

    return {
        "online_users": online_users,
        "total_users": total_users,
        "uptime_seconds": round(metrics.uptime_seconds(), 1),
        "requests_total": requests_total,
        "errors_total": errors_total,
        "error_rate": error_rate,
        "login_failures_total": login_failures,
        "server_load": load,
        "alerts": _evaluate_alerts(error_rate, requests_total, login_failures, load),
    }
