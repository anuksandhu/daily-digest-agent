"""
Metrics Collection for Daily Digest
Tracks performance, cost, quality, and reliability metrics
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class Metric:
    """Single metric data point"""
    name: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricsSummary:
    """Summary of all metrics for a digest generation"""
    generation_id: str
    start_time: str
    end_time: str
    total_duration_ms: float
    success: bool
    
    # Performance metrics
    agent_durations: Dict[str, float] = field(default_factory=dict)
    tool_durations: Dict[str, float] = field(default_factory=dict)
    
    # Cost metrics
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    # Quality metrics
    data_freshness_hours: float = 0.0
    source_reliability_score: float = 0.0
    completeness_score: float = 0.0
    
    # Reliability metrics
    tool_errors: int = 0
    retry_attempts: int = 0
    
    # Raw metrics
    all_metrics: List[Metric] = field(default_factory=list)


class MetricsCollector:
    """
    Collects and manages metrics throughout digest generation
    Implements the Metrics pillar of observability
    """
    
    def __init__(self, generation_id: str = None):
        """
        Initialize metrics collector
        
        Args:
            generation_id: Unique identifier for this generation run
        """
        self.generation_id = generation_id or f"digest-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.start_time = datetime.now()
        self.metrics: List[Metric] = []
        self._timers: Dict[str, datetime] = {}
    
    def record(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Record a metric
        
        Args:
            name: Metric name (e.g., 'agent.weather.duration_ms')
            value: Metric value
            tags: Optional tags for filtering/grouping
        """
        metric = Metric(
            name=name,
            value=value,
            tags=tags or {}
        )
        self.metrics.append(metric)
    
    def increment(self, name: str, tags: Dict[str, str] = None):
        """
        Increment a counter metric
        
        Args:
            name: Metric name
            tags: Optional tags
        """
        self.record(name, 1.0, tags)
    
    def start_timer(self, name: str):
        """
        Start a timer for measuring duration
        
        Args:
            name: Timer name
        """
        self._timers[name] = datetime.now()
    
    def stop_timer(self, name: str, tags: Dict[str, str] = None) -> float:
        """
        Stop a timer and record duration
        
        Args:
            name: Timer name
            tags: Optional tags
        
        Returns:
            Duration in milliseconds
        """
        if name not in self._timers:
            raise ValueError(f"Timer '{name}' was not started")
        
        start_time = self._timers.pop(name)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        self.record(f"{name}.duration_ms", duration_ms, tags)
        return duration_ms
    
    def get_metrics(self, name: str = None) -> List[Metric]:
        """
        Get metrics, optionally filtered by name
        
        Args:
            name: Optional metric name to filter by
        
        Returns:
            List of matching metrics
        """
        if name is None:
            return self.metrics
        return [m for m in self.metrics if m.name == name]
    
    def get_average(self, name: str) -> float:
        """
        Get average value for a metric
        
        Args:
            name: Metric name
        
        Returns:
            Average value, or 0.0 if no metrics found
        """
        matching = self.get_metrics(name)
        if not matching:
            return 0.0
        return sum(m.value for m in matching) / len(matching)
    
    def get_total(self, name: str) -> float:
        """
        Get total (sum) value for a metric
        
        Args:
            name: Metric name
        
        Returns:
            Total value
        """
        matching = self.get_metrics(name)
        return sum(m.value for m in matching)
    
    def create_summary(self, success: bool = True) -> MetricsSummary:
        """
        Create a summary of all collected metrics
        
        Args:
            success: Whether the generation was successful
        
        Returns:
            MetricsSummary object
        """
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds() * 1000
        
        # Extract agent durations
        agent_durations = {}
        for metric in self.metrics:
            if metric.name.endswith(".duration_ms") and "agent" in metric.tags.get("type", ""):
                agent_name = metric.tags.get("agent", "unknown")
                agent_durations[agent_name] = metric.value
        
        # Extract tool durations
        tool_durations = {}
        for metric in self.metrics:
            if metric.name.endswith(".duration_ms") and "tool" in metric.tags.get("type", ""):
                tool_name = metric.tags.get("tool", "unknown")
                tool_durations[tool_name] = metric.value
        
        # Extract cost metrics
        total_tokens = int(self.get_total("generation.token_count"))
        estimated_cost = self.get_total("generation.cost_usd")
        
        # Extract quality metrics
        data_freshness = self.get_average("quality.data_freshness.hours")
        source_reliability = self.get_average("quality.source_reliability.score")
        completeness = self.get_average("quality.completeness.score")
        
        # Extract reliability metrics
        tool_errors = int(self.get_total("tool.error"))
        retry_attempts = int(self.get_total("generation.retry"))
        
        return MetricsSummary(
            generation_id=self.generation_id,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration_ms=total_duration,
            success=success,
            agent_durations=agent_durations,
            tool_durations=tool_durations,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
            data_freshness_hours=data_freshness,
            source_reliability_score=source_reliability,
            completeness_score=completeness,
            tool_errors=tool_errors,
            retry_attempts=retry_attempts,
            all_metrics=self.metrics
        )
    
    def save(self, filepath: Path):
        """
        Save metrics to JSON file
        
        Args:
            filepath: Path to save metrics
        """
        summary = self.create_summary()
        
        # Convert to dict
        data = asdict(summary)
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def __str__(self) -> str:
        """String representation of metrics"""
        summary = self.create_summary()
        return (
            f"Metrics Summary for {self.generation_id}:\n"
            f"  Duration: {summary.total_duration_ms:.0f}ms\n"
            f"  Tokens: {summary.total_tokens}\n"
            f"  Cost: ${summary.estimated_cost_usd:.4f}\n"
            f"  Quality Score: {summary.completeness_score:.2f}\n"
            f"  Errors: {summary.tool_errors}"
        )


# Global metrics collector
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def reset_metrics():
    """Reset global metrics collector (for testing or new generation)"""
    global _metrics
    _metrics = MetricsCollector()
