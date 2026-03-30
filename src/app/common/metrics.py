from prometheus_client import Counter, Histogram

# HTTP Metrics

HTTP_REQUESTS_TOTAL = Counter(
    name="http_requests_total",
    documentation="Total number of HTTP requests received.",
    labelnames=["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request duration in seconds.",
    labelnames=["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Pipeline Metrics

PIPELINE_JOBS_TOTAL = Counter(
    name="pipeline_jobs_total",
    documentation="Total number of pipeline jobs processed.",
    labelnames=["status"],  # "success" or "failure"
)