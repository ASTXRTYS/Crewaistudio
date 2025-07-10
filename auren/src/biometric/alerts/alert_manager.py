"""Biometric alert management system"""
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of biometric alerts"""

    PTOSIS_WARNING = "ptosis_warning"
    PTOSIS_CRITICAL = "ptosis_critical"
    INFLAMMATION_HIGH = "inflammation_high"
    RAPID_CHANGE = "rapid_change"
    PROTOCOL_VIOLATION = "protocol_violation"
    POSITIVE_MILESTONE = "positive_milestone"


class AlertAction(Enum):
    """Predefined alert actions"""

    REFEED_600 = "add_600kcal_refeed"
    REFEED_1000 = "add_1000kcal_refeed"
    REDUCE_TRAINING = "reduce_training_volume"
    REST_DAY = "implement_rest_day"
    ANTI_INFLAMMATORY = "anti_inflammatory_protocol"
    MEDICAL_REVIEW = "seek_medical_review"
    CELEBRATE = "celebrate_progress"


class Alert:
    """Individual alert instance"""

    def __init__(
        self,
        alert_type: AlertType,
        severity: str,
        message: str,
        action: Optional[AlertAction] = None,
        data: Optional[Dict] = None,
    ):
        self.id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.timestamp = datetime.now()
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.action = action
        self.data = data or {}
        self.acknowledged = False
        self.acknowledged_at = None

    def acknowledge(self):
        """Mark alert as acknowledged"""
        self.acknowledged = True
        self.acknowledged_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.alert_type.value,
            "severity": self.severity,
            "message": self.message,
            "action": self.action.value if self.action else None,
            "data": self.data,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }


class AlertManager:
    """Manages biometric alerts and interventions"""

    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules = self._initialize_rules()
        self.notification_handlers: Dict[str, Callable] = {}

        # Load thresholds from environment
        self.thresholds = {
            "ptosis_warning": float(os.getenv("PTOSIS_WARNING_THRESHOLD", "6.5")),
            "ptosis_critical": float(os.getenv("PTOSIS_CRITICAL_THRESHOLD", "7.0")),
            "inflammation_warning": float(os.getenv("INFLAMMATION_WARNING_THRESHOLD", "3")),
            "inflammation_critical": float(os.getenv("INFLAMMATION_CRITICAL_THRESHOLD", "4")),
        }

    def _initialize_rules(self) -> Dict:
        """Initialize alert rules"""
        return {
            "ptosis_check": self._check_ptosis_alert,
            "inflammation_check": self._check_inflammation_alert,
            "rapid_change_check": self._check_rapid_change,
            "positive_milestone_check": self._check_positive_milestone,
        }

    def check_scores(
        self, scores: Dict, historical_data: Optional[List[Dict]] = None
    ) -> List[Alert]:
        """Check scores against all alert rules"""

        new_alerts = []

        for rule_name, rule_func in self.alert_rules.items():
            alert = rule_func(scores, historical_data)
            if alert:
                new_alerts.append(alert)
                self.alerts.append(alert)

                # Trigger notifications
                self._notify(alert)

        return new_alerts

    def _check_ptosis_alert(
        self, scores: Dict, historical: Optional[List[Dict]]
    ) -> Optional[Alert]:
        """Check for ptosis alerts"""

        ptosis = scores.get("ptosis", 0)

        # Critical alert
        if ptosis >= self.thresholds["ptosis_critical"]:
            # Check if sustained over multiple days
            if historical and len(historical) >= 3:
                recent_ptosis = [h.get("ptosis", 0) for h in historical[-3:]]
                avg_ptosis = sum(recent_ptosis) / len(recent_ptosis)

                if avg_ptosis >= self.thresholds["ptosis_warning"]:
                    return Alert(
                        AlertType.PTOSIS_CRITICAL,
                        "critical",
                        f"CRITICAL: Ptosis score {ptosis:.1f} with 3-day average {avg_ptosis:.1f}",
                        AlertAction.REFEED_1000,
                        {"current_ptosis": ptosis, "average_ptosis": avg_ptosis},
                    )

        # Warning alert
        elif ptosis >= self.thresholds["ptosis_warning"]:
            return Alert(
                AlertType.PTOSIS_WARNING,
                "warning",
                f"Ptosis score elevated: {ptosis:.1f}",
                AlertAction.REFEED_600,
                {"current_ptosis": ptosis},
            )

        return None

    def _check_inflammation_alert(
        self, scores: Dict, historical: Optional[List[Dict]]
    ) -> Optional[Alert]:
        """Check for inflammation alerts"""

        inflammation = scores.get("inflammation", 0)

        if inflammation >= self.thresholds["inflammation_critical"]:
            return Alert(
                AlertType.INFLAMMATION_HIGH,
                "critical",
                f"High inflammation detected: {inflammation}/5",
                AlertAction.ANTI_INFLAMMATORY,
                {"inflammation_score": inflammation},
            )
        elif inflammation >= self.thresholds["inflammation_warning"]:
            return Alert(
                AlertType.INFLAMMATION_HIGH,
                "warning",
                f"Moderate inflammation: {inflammation}/5",
                AlertAction.REDUCE_TRAINING,
                {"inflammation_score": inflammation},
            )

        return None

    def _check_rapid_change(
        self, scores: Dict, historical: Optional[List[Dict]]
    ) -> Optional[Alert]:
        """Check for rapid changes in any metric"""

        if not historical or len(historical) < 2:
            return None

        previous = historical[-1]

        for metric in ["ptosis", "inflammation", "symmetry"]:
            if metric in scores and metric in previous:
                current = scores[metric]
                prev = previous[metric]
                change = abs(current - prev)

                if change > 2.0:  # Significant single-day change
                    direction = "increased" if current > prev else "decreased"

                    return Alert(
                        AlertType.RAPID_CHANGE,
                        "warning",
                        f"Rapid change detected: {metric} {direction} by {change:.1f} points",
                        AlertAction.REST_DAY if direction == "increased" else None,
                        {"metric": metric, "change": change, "direction": direction},
                    )

        return None

    def _check_positive_milestone(
        self, scores: Dict, historical: Optional[List[Dict]]
    ) -> Optional[Alert]:
        """Check for positive achievements"""

        # Check for excellent scores
        if scores.get("ptosis", 10) < 2 and scores.get("inflammation", 5) < 1:
            return Alert(
                AlertType.POSITIVE_MILESTONE,
                "info",
                "Excellent biometric scores! Your protocols are working perfectly.",
                AlertAction.CELEBRATE,
                {"achievement": "optimal_biometrics"},
            )

        # Check for improvement trends
        if historical and len(historical) >= 7:
            recent_ptosis = [h.get("ptosis", 0) for h in historical[-7:]]
            if all(recent_ptosis[i] >= recent_ptosis[i + 1] for i in range(len(recent_ptosis) - 1)):
                return Alert(
                    AlertType.POSITIVE_MILESTONE,
                    "info",
                    "7-day improving trend in ptosis scores!",
                    AlertAction.CELEBRATE,
                    {"achievement": "consistent_improvement"},
                )

        return None

    def register_notification_handler(self, severity: str, handler: Callable):
        """Register a notification handler for specific severity"""
        self.notification_handlers[severity] = handler

    def _notify(self, alert: Alert):
        """Send notifications for alert"""

        if alert.severity in self.notification_handlers:
            try:
                self.notification_handlers[alert.severity](alert)
            except Exception as e:
                logger.error(f"Notification failed: {e}")

    def get_active_alerts(self) -> List[Alert]:
        """Get unacknowledged alerts"""
        return [a for a in self.alerts if not a.acknowledged]

    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alerts if a.timestamp > cutoff]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert by ID"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledge()
                return True
        return False

    def get_alert_summary(self) -> Dict:
        """Get summary of alert status"""

        active = self.get_active_alerts()
        recent = self.get_recent_alerts(24)

        summary = {
            "total_active": len(active),
            "critical_active": len([a for a in active if a.severity == "critical"]),
            "warning_active": len([a for a in active if a.severity == "warning"]),
            "last_24h": len(recent),
            "by_type": {},
        }

        # Count by type
        for alert in active:
            alert_type = alert.alert_type.value
            summary["by_type"][alert_type] = summary["by_type"].get(alert_type, 0) + 1

        return summary

    def generate_intervention_plan(self) -> str:
        """Generate intervention plan based on active alerts"""

        active = self.get_active_alerts()
        if not active:
            return "No active alerts. Continue current protocols."

        plan = f"""
■ INTERVENTION PLAN
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Active Alerts: {len(active)}

■■ Immediate Actions Required:
"""

        # Group by severity
        critical = [a for a in active if a.severity == "critical"]
        warning = [a for a in active if a.severity == "warning"]

        if critical:
            plan += "\n⚠️  CRITICAL INTERVENTIONS:\n"
            for alert in critical:
                plan += f"  • {alert.message}\n"
                if alert.action:
                    plan += f"    → {alert.action.value.replace('_', ' ').upper()}\n"

        if warning:
            plan += "\n⚡ WARNING INTERVENTIONS:\n"
            for alert in warning:
                plan += f"  • {alert.message}\n"
                if alert.action:
                    plan += f"    → {alert.action.value.replace('_', ' ').title()}\n"

        # Add specific protocols
        if any(a.action == AlertAction.REFEED_600 for a in active):
            plan += """
■■ 600 Calorie Refeed Protocol:
  • Add 150g white rice (cooked weight)
  • Consume with regular meals
  • Prioritize post-workout window
  • Monitor next day's biometrics
"""

        if any(a.action == AlertAction.ANTI_INFLAMMATORY for a in active):
            plan += """
■■ Anti-Inflammatory Protocol:
  • 10-minute facial ice therapy
  • Increase water to 4L today
  • Add turmeric/ginger to meals
  • Consider lymphatic massage
  • Elevate head during sleep
"""

        plan += "\n■ Monitor closely and reassess in 24 hours."

        return plan
