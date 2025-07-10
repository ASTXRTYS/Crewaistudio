"""MIRAGE Protocol Implementation - Facial Biometric Analysis"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..base_protocol import AlertLevel, BaseProtocol, ProtocolType


class BiometricScores:
    """Container for facial biometric scores with proper type safety"""

    def __init__(self):
        self.ptosis_score: float = 0.0
        self.inflammation_score: float = 0.0
        self.symmetry_score: float = 0.0
        self.lymphatic_fullness: float = 0.0
        self.skin_clarity: float = 0.0

    def update_score(self, metric: str, value: np.floating) -> None:
        """Safely update biometric scores with type conversion."""
        setattr(self, metric, float(value))

    def to_dict(self) -> Dict:
        return {
            "inflammation": self.inflammation_score,
            "ptosis": self.ptosis_score,
            "symmetry": self.symmetry_score,
            "lymphatic_fullness": self.lymphatic_fullness,
            "skin_clarity": self.skin_clarity,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BiometricScores":
        scores = cls()
        for key, value in data.items():
            if hasattr(scores, key):
                setattr(scores, key, float(value))
        return scores


class MIRAGEProtocol(BaseProtocol):
    """Master Visual Transformation Report - MIRAGE Protocol"""

    def __init__(self):
        super().__init__(ProtocolType.MIRAGE)
        self.ptosis_threshold_yellow = float(os.getenv("PTOSIS_WARNING_THRESHOLD", "6.5"))
        self.ptosis_threshold_red = float(os.getenv("PTOSIS_CRITICAL_THRESHOLD", "7.0"))
        self.inflammation_warning = float(os.getenv("INFLAMMATION_WARNING_THRESHOLD", "3"))

    def create_entry(self, data: Dict) -> Dict:
        """Create MIRAGE entry with biometric analysis"""

        # Extract or calculate scores
        scores = self._analyze_biometrics(data)

        # Create entry
        entry = {
            "id": f"M-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "scores": scores.to_dict(),
            "image_metadata": data.get("image_metadata", {}),
            "lighting_conditions": data.get("lighting", "natural"),
            "camera_angle": data.get("angle", "front"),
            "notes": data.get("notes", ""),
        }

        # Add trend analysis
        entry["trends"] = self._analyze_score_trends(scores)

        # Check for alerts
        self._check_biometric_alerts(scores, entry["trends"])

        self.entries.append(entry)
        return entry

    def _analyze_biometrics(self, data: Dict) -> BiometricScores:
        """Analyze facial biometrics from image data"""

        scores = BiometricScores()

        # If scores are provided directly (manual entry)
        if "scores" in data:
            return BiometricScores.from_dict(data["scores"])

        # Otherwise, perform analysis (placeholder for actual CV analysis)
        # In production, this would use computer vision models

        # For now, simulate analysis based on metadata
        if data.get("post_workout", False):
            scores.inflammation_score += 1.0
            scores.lymphatic_fullness += 1.0

        if data.get("morning", True):
            scores.lymphatic_fullness += 0.5

        # Simulate some variation
        scores.ptosis_score = float(data.get("ptosis_score", 0))
        scores.inflammation_score = min(5.0, float(data.get("inflammation_score", 2)))

        return scores

    def _analyze_score_trends(self, current_scores: BiometricScores) -> Dict:
        """Analyze trends compared to recent entries"""

        recent_entries = self._get_recent_entries(days=7)
        if len(recent_entries) < 2:
            return {"status": "insufficient_data"}

        # Calculate averages
        recent_scores = [BiometricScores.from_dict(e["scores"]) for e in recent_entries]

        trends = {}
        for attr in [
            "inflammation_score",
            "ptosis_score",
            "symmetry_score",
            "lymphatic_fullness",
            "skin_clarity",
        ]:
            recent_values = [getattr(s, attr) for s in recent_scores]
            current_value = getattr(current_scores, attr)

            avg = float(np.mean(recent_values))
            std = float(np.std(recent_values))

            # Determine trend
            if current_value > avg + std:
                trend = "worsening" if attr != "symmetry_score" else "improving"
            elif current_value < avg - std:
                trend = "improving" if attr != "symmetry_score" else "worsening"
            else:
                trend = "stable"

            trends[attr] = {
                "current": current_value,
                "average": round(avg, 2),
                "trend": trend,
                "change": round(current_value - avg, 2),
            }

        return trends

    def _check_biometric_alerts(self, scores: BiometricScores, trends: Dict):
        """Check for protocol-defined alerts"""

        # Ptosis alerts
        if scores.ptosis_score >= self.ptosis_threshold_red:
            ptosis_avg = self._get_ptosis_average(days=3)
            if ptosis_avg >= 6:
                self.add_alert(
                    AlertLevel.CRITICAL,
                    f"RED FLAG: Ptosis {scores.ptosis_score:.1f} (3-day avg: {ptosis_avg:.1f})",
                    "implement_full_recovery_protocol",
                )
        elif scores.ptosis_score >= self.ptosis_threshold_yellow:
            self.add_alert(
                AlertLevel.WARNING,
                f"YELLOW FLAG: Ptosis {scores.ptosis_score:.1f}",
                "add_600kcal_refeed",
            )

        # Inflammation alerts
        if scores.inflammation_score >= self.inflammation_warning:
            self.add_alert(
                AlertLevel.WARNING,
                f"Elevated inflammation: {scores.inflammation_score}/5",
                "anti_inflammatory_protocol",
            )

        # Trend-based alerts
        if trends.get("ptosis_score", {}).get("trend") == "worsening":
            consecutive_days = self._count_consecutive_worsening("ptosis_score")
            if consecutive_days >= 3:
                self.add_alert(
                    AlertLevel.WARNING,
                    f"Ptosis worsening for {consecutive_days} consecutive days",
                    "review_training_volume",
                )

    def _get_recent_entries(self, days: int = 7) -> List[Dict]:
        """Get entries from recent days"""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []

        for entry in reversed(self.entries):
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time > cutoff:
                recent.append(entry)
            else:
                break

        return list(reversed(recent))

    def _get_ptosis_average(self, days: int = 3) -> float:
        """Calculate rolling ptosis average"""
        recent = self._get_recent_entries(days=days)
        if not recent:
            return 0.0

        ptosis_values = [e["scores"]["ptosis"] for e in recent]
        return float(np.mean(ptosis_values))

    def _count_consecutive_worsening(self, metric: str) -> int:
        """Count consecutive days of worsening for a metric"""
        if len(self.entries) < 2:
            return 0

        count = 0
        for i in range(len(self.entries) - 1, 0, -1):
            current = self.entries[i]["scores"][metric]
            previous = self.entries[i - 1]["scores"][metric]

            if metric == "symmetry_score":
                if current < previous:
                    count += 1
                else:
                    break
            else:
                if current > previous:
                    count += 1
                else:
                    break

        return count

    def analyze_trends(self, timeframe: str = "7d") -> Dict:
        """Comprehensive MIRAGE trend analysis"""

        days = int(timeframe.rstrip("d"))
        entries = self._get_recent_entries(days=days)

        if not entries:
            return {"status": "no_data"}

        # Aggregate scores
        all_scores = {
            "inflammation": [],
            "ptosis": [],
            "symmetry": [],
            "lymphatic_fullness": [],
            "skin_clarity": [],
        }

        for entry in entries:
            for metric, values in all_scores.items():
                values.append(entry["scores"][metric])

        # Calculate statistics
        analysis = {"timeframe": timeframe, "entries_analyzed": len(entries), "metrics": {}}

        for metric, values in all_scores.items():
            if values:
                analysis["metrics"][metric] = {
                    "current": values[-1],
                    "average": round(float(np.mean(values)), 2),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": round(float(np.std(values)), 2),
                    "trend": self._determine_trend(values),
                    "improvement": self._calculate_improvement(metric, values),
                }

        # Add alerts summary
        analysis["active_alerts"] = self.get_recent_alerts(hours=days * 24)
        analysis["protocol_status"] = self._determine_protocol_status(analysis)

        return analysis

    def _determine_trend(self, values: List[float]) -> str:
        """Determine overall trend direction"""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear regression
        x = np.arange(len(values))
        slope = float(np.polyfit(x, values, 1)[0])

        if abs(slope) < 0.05:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"

    def _calculate_improvement(self, metric: str, values: List[float]) -> float:
        """Calculate percentage improvement"""
        if len(values) < 2:
            return 0.0

        first, last = values[0], values[-1]

        # For symmetry, higher is better
        if metric == "symmetry":
            change = last - first
        else:
            # For others, lower is better
            change = first - last

        # Calculate percentage
        if first != 0:
            return round((change / first) * 100, 1)
        else:
            return 0.0

    def _determine_protocol_status(self, analysis: Dict) -> str:
        """Determine overall protocol status"""

        critical_alerts = [a for a in analysis["active_alerts"] if a["level"] == "critical"]
        warning_alerts = [a for a in analysis["active_alerts"] if a["level"] == "warning"]

        if critical_alerts:
            return "critical_intervention_required"
        elif warning_alerts:
            return "monitoring_required"
        elif analysis["metrics"].get("ptosis", {}).get("current", 0) < 3:
            return "optimal"
        else:
            return "stable"

    def generate_visual_report(self) -> str:
        """Generate formatted MIRAGE report"""

        analysis = self.analyze_trends("7d")

        report = f"""
■ MIRAGE PROTOCOL REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Protocol Status: {analysis.get('protocol_status', 'unknown').replace('_', ' ').title()}

■■ Current Biometric Scores (Latest Entry)
"""

        if self.entries:
            latest = self.entries[-1]["scores"]
            report += f"""
• Inflammation: {latest['inflammation']}/5
• Ptosis: {latest['ptosis']}/10
• Symmetry: {latest['symmetry']}/5
• Lymphatic Fullness: {latest['lymphatic_fullness']}/5
• Skin Clarity: {latest['skin_clarity']}/5
"""

        report += "\n■■ 7-Day Trends\n"

        for metric, data in analysis.get("metrics", {}).items():
            trend_symbol = (
                "↑"
                if data["trend"] == "increasing"
                else "↓"
                if data["trend"] == "decreasing"
                else "→"
            )
            report += f"• {metric.replace('_', ' ').title()}: {data['current']} {trend_symbol} (avg: {data['average']})\n"

        if analysis.get("active_alerts"):
            report += "\n■■ Active Alerts\n"
            for alert in analysis["active_alerts"]:
                report += f"• [{alert['level'].upper()}] {alert['message']}\n"
                if alert.get("action"):
                    report += f"  → Action: {alert['action'].replace('_', ' ')}\n"

        report += "\n■ End of MIRAGE Report"

        return report
