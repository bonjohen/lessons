"""Prometheus metrics for Lessons Hub backend.

Guarded behind try/except so the backend runs without prometheus_client installed.
"""

from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram

    METRICS_AVAILABLE = True

    requests_total = Counter(
        "requests_total",
        "Total HTTP requests",
        labelnames=["method", "path", "status"],
    )

    request_duration_seconds = Histogram(
        "request_duration_seconds",
        "HTTP request duration in seconds",
        labelnames=["method", "path"],
    )

    gap_detections_total = Counter(
        "gap_detections_total",
        "Total gap detections triggered",
    )

    cache_hits_total = Counter(
        "cache_hits_total",
        "Total cache hits (retriever + generator)",
        labelnames=["component"],
    )

except ImportError:
    METRICS_AVAILABLE = False
    requests_total = None
    request_duration_seconds = None
    gap_detections_total = None
    cache_hits_total = None
