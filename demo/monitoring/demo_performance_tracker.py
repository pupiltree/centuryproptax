"""
Demo Performance Tracker
Real-time monitoring and metrics collection for demo environment performance
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric record"""
    timestamp: datetime
    metric_type: str
    value: float
    session_id: str
    scenario_id: Optional[str] = None
    user_persona: Optional[str] = None

@dataclass
class ConversationMetrics:
    """Metrics for a single conversation session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    scenario_id: Optional[str]
    user_persona: Optional[str]
    total_turns: int
    response_times: List[float]
    accuracy_scores: List[float]
    user_satisfaction: Optional[float]
    escalation_occurred: bool
    completion_status: str  # "completed", "abandoned", "escalated"

class DemoPerformanceTracker:
    """Tracks and analyzes demo performance metrics in real-time"""

    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.metrics_history: deque = deque(maxlen=max_history_size)
        self.active_sessions: Dict[str, ConversationMetrics] = {}
        self.performance_targets = {
            "response_time_ms": 200,
            "accuracy_percent": 95.0,
            "resolution_rate_percent": 85.0,
            "user_satisfaction": 4.5
        }
        self.real_time_metrics = {
            "current_response_time": 0,
            "current_accuracy": 0,
            "current_resolution_rate": 0,
            "active_sessions": 0,
            "total_conversations": 0
        }

    def start_conversation_session(self, session_id: str, scenario_id: Optional[str] = None, user_persona: Optional[str] = None) -> ConversationMetrics:
        """Start tracking a new conversation session"""
        conversation_metrics = ConversationMetrics(
            session_id=session_id,
            start_time=datetime.now(),
            end_time=None,
            scenario_id=scenario_id,
            user_persona=user_persona,
            total_turns=0,
            response_times=[],
            accuracy_scores=[],
            user_satisfaction=None,
            escalation_occurred=False,
            completion_status="active"
        )

        self.active_sessions[session_id] = conversation_metrics
        self.real_time_metrics["active_sessions"] = len(self.active_sessions)

        logger.info(f"Started tracking conversation session: {session_id}")
        return conversation_metrics

    def record_response_time(self, session_id: str, response_time_ms: float):
        """Record response time for a conversation turn"""
        if session_id not in self.active_sessions:
            logger.warning(f"Recording response time for unknown session: {session_id}")
            return

        session = self.active_sessions[session_id]
        session.response_times.append(response_time_ms)
        session.total_turns += 1

        # Record as metric
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_type="response_time",
            value=response_time_ms,
            session_id=session_id,
            scenario_id=session.scenario_id,
            user_persona=session.user_persona
        )
        self.metrics_history.append(metric)

        # Update real-time metrics
        self._update_real_time_metrics()

    def record_accuracy_score(self, session_id: str, accuracy_percent: float):
        """Record accuracy score for a response"""
        if session_id not in self.active_sessions:
            logger.warning(f"Recording accuracy for unknown session: {session_id}")
            return

        session = self.active_sessions[session_id]
        session.accuracy_scores.append(accuracy_percent)

        # Record as metric
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_type="accuracy",
            value=accuracy_percent,
            session_id=session_id,
            scenario_id=session.scenario_id,
            user_persona=session.user_persona
        )
        self.metrics_history.append(metric)

        # Update real-time metrics
        self._update_real_time_metrics()

    def record_escalation(self, session_id: str, escalation_reason: str):
        """Record that a conversation was escalated to human agent"""
        if session_id not in self.active_sessions:
            logger.warning(f"Recording escalation for unknown session: {session_id}")
            return

        session = self.active_sessions[session_id]
        session.escalation_occurred = True
        session.completion_status = "escalated"

        # Record as metric
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_type="escalation",
            value=1.0,
            session_id=session_id,
            scenario_id=session.scenario_id,
            user_persona=session.user_persona
        )
        self.metrics_history.append(metric)

        logger.info(f"Escalation recorded for session {session_id}: {escalation_reason}")

    def record_user_satisfaction(self, session_id: str, satisfaction_score: float):
        """Record user satisfaction score (1-5 scale)"""
        if session_id not in self.active_sessions:
            logger.warning(f"Recording satisfaction for unknown session: {session_id}")
            return

        session = self.active_sessions[session_id]
        session.user_satisfaction = satisfaction_score

        # Record as metric
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_type="satisfaction",
            value=satisfaction_score,
            session_id=session_id,
            scenario_id=session.scenario_id,
            user_persona=session.user_persona
        )
        self.metrics_history.append(metric)

    def end_conversation_session(self, session_id: str, completion_status: str = "completed"):
        """End tracking for a conversation session"""
        if session_id not in self.active_sessions:
            logger.warning(f"Ending unknown session: {session_id}")
            return

        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        session.completion_status = completion_status

        # Move to completed sessions (could be stored in database)
        del self.active_sessions[session_id]
        self.real_time_metrics["active_sessions"] = len(self.active_sessions)
        self.real_time_metrics["total_conversations"] += 1

        logger.info(f"Ended conversation session: {session_id} with status: {completion_status}")

    def _update_real_time_metrics(self):
        """Update real-time performance metrics"""
        recent_metrics = self._get_recent_metrics(minutes=5)

        # Calculate average response time
        response_times = [m.value for m in recent_metrics if m.metric_type == "response_time"]
        if response_times:
            self.real_time_metrics["current_response_time"] = sum(response_times) / len(response_times)

        # Calculate average accuracy
        accuracy_scores = [m.value for m in recent_metrics if m.metric_type == "accuracy"]
        if accuracy_scores:
            self.real_time_metrics["current_accuracy"] = sum(accuracy_scores) / len(accuracy_scores)

        # Calculate resolution rate
        self.real_time_metrics["current_resolution_rate"] = self._calculate_resolution_rate()

    def _get_recent_metrics(self, minutes: int = 5) -> List[PerformanceMetric]:
        """Get metrics from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def _calculate_resolution_rate(self) -> float:
        """Calculate current resolution rate (non-escalated conversations)"""
        total_sessions = self.real_time_metrics["total_conversations"]
        if total_sessions == 0:
            return 100.0

        escalated_count = len([m for m in self.metrics_history if m.metric_type == "escalation"])
        resolution_rate = ((total_sessions - escalated_count) / total_sessions) * 100
        return max(0, min(100, resolution_rate))

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time performance metrics"""
        return {
            **self.real_time_metrics,
            "last_updated": datetime.now().isoformat(),
            "targets": self.performance_targets,
            "status": self._get_performance_status()
        }

    def _get_performance_status(self) -> Dict[str, str]:
        """Get performance status compared to targets"""
        status = {}

        # Response time status
        current_rt = self.real_time_metrics["current_response_time"]
        target_rt = self.performance_targets["response_time_ms"]
        if current_rt <= target_rt:
            status["response_time"] = "excellent"
        elif current_rt <= target_rt * 1.5:
            status["response_time"] = "good"
        elif current_rt <= target_rt * 2:
            status["response_time"] = "fair"
        else:
            status["response_time"] = "poor"

        # Accuracy status
        current_acc = self.real_time_metrics["current_accuracy"]
        target_acc = self.performance_targets["accuracy_percent"]
        if current_acc >= target_acc:
            status["accuracy"] = "excellent"
        elif current_acc >= target_acc * 0.9:
            status["accuracy"] = "good"
        elif current_acc >= target_acc * 0.8:
            status["accuracy"] = "fair"
        else:
            status["accuracy"] = "poor"

        # Resolution rate status
        current_res = self.real_time_metrics["current_resolution_rate"]
        target_res = self.performance_targets["resolution_rate_percent"]
        if current_res >= target_res:
            status["resolution_rate"] = "excellent"
        elif current_res >= target_res * 0.9:
            status["resolution_rate"] = "good"
        elif current_res >= target_res * 0.8:
            status["resolution_rate"] = "fair"
        else:
            status["resolution_rate"] = "poor"

        return status

    def get_performance_analytics(self, time_period: str = "1h") -> Dict[str, Any]:
        """Get detailed performance analytics for a time period"""
        if time_period == "1h":
            cutoff = datetime.now() - timedelta(hours=1)
        elif time_period == "24h":
            cutoff = datetime.now() - timedelta(hours=24)
        elif time_period == "7d":
            cutoff = datetime.now() - timedelta(days=7)
        else:
            cutoff = datetime.now() - timedelta(hours=1)

        relevant_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff]

        analytics = {
            "time_period": time_period,
            "total_metrics": len(relevant_metrics),
            "response_time_analytics": self._analyze_response_times(relevant_metrics),
            "accuracy_analytics": self._analyze_accuracy(relevant_metrics),
            "escalation_analytics": self._analyze_escalations(relevant_metrics),
            "scenario_performance": self._analyze_by_scenario(relevant_metrics),
            "persona_performance": self._analyze_by_persona(relevant_metrics)
        }

        return analytics

    def _analyze_response_times(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze response time metrics"""
        response_times = [m.value for m in metrics if m.metric_type == "response_time"]

        if not response_times:
            return {"count": 0}

        return {
            "count": len(response_times),
            "average": sum(response_times) / len(response_times),
            "min": min(response_times),
            "max": max(response_times),
            "median": sorted(response_times)[len(response_times) // 2],
            "under_target_percent": (len([rt for rt in response_times if rt <= self.performance_targets["response_time_ms"]]) / len(response_times)) * 100
        }

    def _analyze_accuracy(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze accuracy metrics"""
        accuracy_scores = [m.value for m in metrics if m.metric_type == "accuracy"]

        if not accuracy_scores:
            return {"count": 0}

        return {
            "count": len(accuracy_scores),
            "average": sum(accuracy_scores) / len(accuracy_scores),
            "min": min(accuracy_scores),
            "max": max(accuracy_scores),
            "above_target_percent": (len([acc for acc in accuracy_scores if acc >= self.performance_targets["accuracy_percent"]]) / len(accuracy_scores)) * 100
        }

    def _analyze_escalations(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze escalation patterns"""
        escalations = [m for m in metrics if m.metric_type == "escalation"]
        total_sessions = len(set(m.session_id for m in metrics))

        return {
            "total_escalations": len(escalations),
            "total_sessions": total_sessions,
            "escalation_rate_percent": (len(escalations) / total_sessions * 100) if total_sessions > 0 else 0,
            "escalations_by_scenario": self._count_by_attribute(escalations, "scenario_id"),
            "escalations_by_persona": self._count_by_attribute(escalations, "user_persona")
        }

    def _analyze_by_scenario(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze performance by scenario"""
        scenario_metrics = defaultdict(list)
        for metric in metrics:
            if metric.scenario_id:
                scenario_metrics[metric.scenario_id].append(metric)

        scenario_analysis = {}
        for scenario_id, scenario_metrics_list in scenario_metrics.items():
            response_times = [m.value for m in scenario_metrics_list if m.metric_type == "response_time"]
            accuracy_scores = [m.value for m in scenario_metrics_list if m.metric_type == "accuracy"]

            scenario_analysis[scenario_id] = {
                "total_interactions": len(scenario_metrics_list),
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "avg_accuracy": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0,
                "escalation_count": len([m for m in scenario_metrics_list if m.metric_type == "escalation"])
            }

        return scenario_analysis

    def _analyze_by_persona(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze performance by user persona"""
        persona_metrics = defaultdict(list)
        for metric in metrics:
            if metric.user_persona:
                persona_metrics[metric.user_persona].append(metric)

        persona_analysis = {}
        for persona, persona_metrics_list in persona_metrics.items():
            response_times = [m.value for m in persona_metrics_list if m.metric_type == "response_time"]
            accuracy_scores = [m.value for m in persona_metrics_list if m.metric_type == "accuracy"]

            persona_analysis[persona] = {
                "total_interactions": len(persona_metrics_list),
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "avg_accuracy": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0,
                "escalation_count": len([m for m in persona_metrics_list if m.metric_type == "escalation"])
            }

        return persona_analysis

    def _count_by_attribute(self, metrics: List[PerformanceMetric], attribute: str) -> Dict[str, int]:
        """Count metrics by a specific attribute"""
        counts = defaultdict(int)
        for metric in metrics:
            value = getattr(metric, attribute, "unknown")
            if value:
                counts[value] += 1
        return dict(counts)

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics data in specified format"""
        if format == "json":
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "performance_targets": self.performance_targets,
                "real_time_metrics": self.real_time_metrics,
                "metrics_history": [asdict(metric) for metric in self.metrics_history],
                "active_sessions": {sid: asdict(session) for sid, session in self.active_sessions.items()}
            }
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def reset_metrics(self):
        """Reset all performance metrics (for demo resets)"""
        self.metrics_history.clear()
        self.active_sessions.clear()
        self.real_time_metrics = {
            "current_response_time": 0,
            "current_accuracy": 0,
            "current_resolution_rate": 0,
            "active_sessions": 0,
            "total_conversations": 0
        }
        logger.info("Performance metrics reset")

# Global performance tracker instance
demo_performance_tracker = DemoPerformanceTracker()