"""Journal Protocol Implementation - Peptide Recomposition Tracking"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..base_protocol import AlertLevel, BaseProtocol, ProtocolType


class JournalEntry:
    """Represents a single journal entry"""

    def __init__(self, entry_type: str, data: Dict):
        self.id = f"J-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.timestamp = datetime.now().isoformat()
        self.entry_type = entry_type
        self.data = data

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "entry_type": self.entry_type,
            "data": self.data,
        }


class JournalProtocol(BaseProtocol):
    """Master Peptide Recomposition Journal"""

    def __init__(self):
        super().__init__(ProtocolType.JOURNAL)
        self.peptide_phases = []
        self.current_phase = None
        self.metrics_history = []

    def create_entry(self, data: Dict) -> Dict:
        """Create a journal entry with validation"""

        entry_type = data.get("type", "general")

        # Validate based on entry type
        if entry_type == "weight_log":
            self._validate_weight_log(data)
        elif entry_type == "peptide_dose":
            self._validate_peptide_dose(data)
        elif entry_type == "macro_log":
            self._validate_macro_log(data)

        # Create entry
        entry = JournalEntry(entry_type, data)
        self.entries.append(entry.to_dict())

        # Check for alerts
        self._check_for_alerts(entry)

        return entry.to_dict()

    def _validate_weight_log(self, data: Dict):
        """Validate weight log data"""
        required = ["weight", "unit", "time_of_day"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Convert weight to consistent unit (kg)
        if data["unit"] == "lbs":
            data["weight_kg"] = data["weight"] * 0.453592
        else:
            data["weight_kg"] = data["weight"]

    def _validate_peptide_dose(self, data: Dict):
        """Validate peptide dosing data"""
        required = ["compound", "dose", "unit", "route"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Add to peptide phases
        phase_entry = {
            "compound": data["compound"],
            "dose": data["dose"],
            "unit": data["unit"],
            "started": datetime.now().isoformat(),
            "active": True,
        }

        # Deactivate previous phase of same compound
        for phase in self.peptide_phases:
            if phase["compound"] == data["compound"] and phase["active"]:
                phase["active"] = False
                phase["ended"] = datetime.now().isoformat()

        self.peptide_phases.append(phase_entry)
        self.current_phase = phase_entry

    def _validate_macro_log(self, data: Dict):
        """Validate macronutrient log"""
        required = ["calories", "protein", "carbs", "fats"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def _check_for_alerts(self, entry: JournalEntry):
        """Check if entry triggers any alerts"""

        if entry.entry_type == "weight_log":
            # Check for rapid weight changes
            recent_weights = self._get_recent_weights(days=7)
            if len(recent_weights) >= 3:
                weight_change = recent_weights[0] - recent_weights[-1]
                change_rate = abs(weight_change) / len(recent_weights)

                if change_rate > 0.5:  # More than 0.5kg/day average
                    self.add_alert(
                        AlertLevel.WARNING,
                        f"Rapid weight change detected: {weight_change:.1f}kg in {len(recent_weights)} days",
                        "review_protocol",
                    )

        elif entry.entry_type == "side_effect":
            severity = entry.data.get("severity", 0)
            if severity >= 7:
                self.add_alert(
                    AlertLevel.CRITICAL,
                    f"High severity side effect reported: {entry.data.get('description')}",
                    "medical_review",
                )

    def _get_recent_weights(self, days: int = 7) -> List[float]:
        """Get weight measurements from recent days"""
        cutoff = datetime.now() - timedelta(days=days)
        weights = []

        for entry in reversed(self.entries):
            if entry["entry_type"] == "weight_log":
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time > cutoff:
                    weights.append(entry["data"]["weight_kg"])
                else:
                    break

        return weights

    def analyze_trends(self, timeframe: str = "7d") -> Dict:
        """Analyze journal trends"""

        # Parse timeframe
        days = int(timeframe.rstrip("d"))
        cutoff = datetime.now() - timedelta(days=days)

        # Collect metrics
        weights = []
        macros = {"calories": [], "protein": [], "carbs": [], "fats": []}
        peptide_changes = []

        for entry in self.entries:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time > cutoff:
                if entry["entry_type"] == "weight_log":
                    weights.append(entry["data"]["weight_kg"])
                elif entry["entry_type"] == "macro_log":
                    for key in macros:
                        macros[key].append(entry["data"][key])
                elif entry["entry_type"] == "peptide_dose":
                    peptide_changes.append(entry["data"])

        # Calculate trends
        analysis = {
            "timeframe": timeframe,
            "weight_trend": self._calculate_trend(weights),
            "average_macros": {
                key: sum(values) / len(values) if values else 0 for key, values in macros.items()
            },
            "peptide_changes": peptide_changes,
            "active_compounds": [p for p in self.peptide_phases if p["active"]],
            "alerts": self.get_recent_alerts(hours=days * 24),
        }

        return analysis

    def _calculate_trend(self, values: List[float]) -> Dict:
        """Calculate trend statistics"""
        if not values:
            return {"direction": "stable", "change": 0}

        change = values[-1] - values[0] if len(values) > 1 else 0
        direction = "increasing" if change > 0.1 else "decreasing" if change < -0.1 else "stable"

        return {
            "direction": direction,
            "change": change,
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "data_points": len(values),
        }

    def get_current_protocol_summary(self) -> Dict:
        """Get current protocol status"""
        return {
            "active_compounds": [p for p in self.peptide_phases if p["active"]],
            "recent_weight": self._get_recent_weights(days=1)[0]
            if self._get_recent_weights(days=1)
            else None,
            "weekly_trend": self.analyze_trends("7d"),
            "active_alerts": [a for a in self.alerts if a["level"] != "info"],
            "last_entry": self.entries[-1] if self.entries else None,
        }
