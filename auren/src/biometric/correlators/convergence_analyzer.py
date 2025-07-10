"""Convergence analysis across protocols"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class ConvergenceAnalyzer:
    """Analyzes correlations between visual, peptide, and lifestyle data"""

    def __init__(self):
        self.data_sources = {"journal": [], "mirage": [], "visor": [], "lifestyle": []}

    def add_data(self, source: str, data: Dict):
        """Add data from a protocol source"""
        if source in self.data_sources:
            self.data_sources[source].append(
                {"timestamp": datetime.now().isoformat(), "data": data}
            )

    def analyze_peptide_visual_correlation(self, timeframe_days: int = 14) -> Dict:
        """Analyze correlation between peptide changes and visual markers"""

        logger.info(f"Analyzing peptide-visual correlations over {timeframe_days} days")

        # Get data within timeframe
        cutoff = datetime.now() - timedelta(days=timeframe_days)

        # Extract peptide events
        peptide_events = []
        for entry in self.data_sources["journal"]:
            if datetime.fromisoformat(entry["timestamp"]) > cutoff:
                if entry["data"].get("type") == "peptide_dose":
                    peptide_events.append(entry)

        # Extract visual scores
        visual_scores = []
        for entry in self.data_sources["mirage"]:
            if datetime.fromisoformat(entry["timestamp"]) > cutoff:
                visual_scores.append(entry)

        if not peptide_events or not visual_scores:
            return {"status": "insufficient_data"}

        # Analyze correlations
        correlations = {}

        for peptide in peptide_events:
            compound = peptide["data"]["compound"]
            dose_time = datetime.fromisoformat(peptide["timestamp"])

            # Find visual changes within 7 days
            post_dose_visuals = [
                v
                for v in visual_scores
                if dose_time
                < datetime.fromisoformat(v["timestamp"])
                < dose_time + timedelta(days=7)
            ]

            if post_dose_visuals:
                # Calculate average changes
                changes = self._calculate_visual_changes(
                    visual_scores[-1] if visual_scores else None, post_dose_visuals
                )

                correlations[compound] = {
                    "dose": peptide["data"]["dose"],
                    "visual_changes": changes,
                    "confidence": self._calculate_confidence(len(post_dose_visuals)),
                }

        return {
            "timeframe_days": timeframe_days,
            "correlations": correlations,
            "summary": self._summarize_correlations(correlations),
        }

    def _calculate_visual_changes(self, baseline: Optional[Dict], post_entries: List[Dict]) -> Dict:
        """Calculate changes in visual markers"""

        if not post_entries:
            return {}

        # Get baseline scores
        if baseline and "data" in baseline and "scores" in baseline["data"]:
            baseline_scores = baseline["data"]["scores"]
        else:
            baseline_scores = {
                "inflammation": 2.5,
                "ptosis": 5.0,
                "symmetry": 3.0,
                "lymphatic_fullness": 2.5,
                "skin_clarity": 3.0,
            }

        # Calculate average post scores
        post_scores = {metric: [] for metric in baseline_scores}

        for entry in post_entries:
            if "data" in entry and "scores" in entry["data"]:
                for metric, value in entry["data"]["scores"].items():
                    if metric in post_scores:
                        post_scores[metric].append(value)

        # Calculate changes
        changes = {}
        for metric, values in post_scores.items():
            if values:
                avg_post = np.mean(values)
                change = avg_post - baseline_scores[metric]
                changes[metric] = {
                    "baseline": baseline_scores[metric],
                    "post_average": round(avg_post, 2),
                    "change": round(change, 2),
                    "percent_change": round((change / baseline_scores[metric] * 100), 1)
                    if baseline_scores[metric] > 0
                    else 0,
                }

        return changes

    def _calculate_confidence(self, sample_size: int) -> float:
        """Calculate confidence score based on sample size"""
        # Simple confidence calculation
        return min(0.95, 0.5 + (sample_size * 0.1))

    def _summarize_correlations(self, correlations: Dict) -> Dict:
        """Summarize correlation findings"""

        summary = {
            "strongest_positive": None,
            "strongest_negative": None,
            "overall_trend": "neutral",
        }

        if not correlations:
            return summary

        # Find strongest effects
        max_improvement = 0
        max_decline = 0

        for compound, data in correlations.items():
            changes = data.get("visual_changes", {})

            # Calculate overall effect (lower is better for most metrics)
            overall_change = 0
            for metric, change_data in changes.items():
                if metric == "symmetry" or metric == "skin_clarity":
                    # Higher is better
                    overall_change += change_data.get("change", 0)
                else:
                    # Lower is better
                    overall_change -= change_data.get("change", 0)

            if overall_change > max_improvement:
                max_improvement = overall_change
                summary["strongest_positive"] = compound
            elif overall_change < max_decline:
                max_decline = overall_change
                summary["strongest_negative"] = compound

        # Determine overall trend
        if max_improvement > abs(max_decline):
            summary["overall_trend"] = "improving"
        elif abs(max_decline) > max_improvement:
            summary["overall_trend"] = "declining"

        return summary

    def analyze_lifestyle_impact(self) -> Dict:
        """Analyze impact of lifestyle factors on biometrics"""

        analysis = {
            "sleep_impact": self._analyze_sleep_correlation(),
            "training_impact": self._analyze_training_correlation(),
            "nutrition_impact": self._analyze_nutrition_correlation(),
            "recommendations": [],
        }

        # Generate recommendations based on analysis
        if analysis["sleep_impact"].get("correlation", 0) < -0.3:
            analysis["recommendations"].append(
                "Poor sleep strongly correlated with increased ptosis. Prioritize 7-9 hours."
            )

        if analysis["training_impact"].get("high_volume_days", 0) > 3:
            analysis["recommendations"].append(
                "High training volume affecting recovery markers. Consider deload week."
            )

        return analysis

    def _analyze_sleep_correlation(self) -> Dict:
        """Analyze sleep quality impact on visual markers"""

        # Extract sleep data from lifestyle entries
        sleep_data = []
        visual_data = []

        for entry in self.data_sources["lifestyle"]:
            if "sleep_hours" in entry["data"]:
                sleep_data.append(
                    {
                        "timestamp": entry["timestamp"],
                        "hours": entry["data"]["sleep_hours"],
                        "quality": entry["data"].get("sleep_quality", 5),
                    }
                )

        for entry in self.data_sources["mirage"]:
            if "scores" in entry["data"]:
                visual_data.append(
                    {
                        "timestamp": entry["timestamp"],
                        "ptosis": entry["data"]["scores"].get("ptosis", 0),
                        "inflammation": entry["data"]["scores"].get("inflammation", 0),
                    }
                )

        if len(sleep_data) < 5 or len(visual_data) < 5:
            return {"status": "insufficient_data"}

        # Simple correlation analysis
        # In production, use more sophisticated time-series analysis
        sleep_hours = [s["hours"] for s in sleep_data[-10:]]
        ptosis_scores = [v["ptosis"] for v in visual_data[-10:]]

        if len(sleep_hours) == len(ptosis_scores):
            correlation = np.corrcoef(sleep_hours, ptosis_scores)[0, 1]

            return {
                "correlation": round(correlation, 3),
                "interpretation": "negative"
                if correlation < -0.3
                else "positive"
                if correlation > 0.3
                else "neutral",
                "average_sleep": round(np.mean(sleep_hours), 1),
                "recommendation": "Increase sleep"
                if np.mean(sleep_hours) < 7
                else "Maintain current sleep",
            }

        return {"status": "data_mismatch"}

    def _analyze_training_correlation(self) -> Dict:
        """Analyze training volume impact"""

        # Placeholder implementation
        return {
            "high_volume_days": 2,
            "recovery_score": 0.75,
            "recommendation": "Current training volume is sustainable",
        }

    def _analyze_nutrition_correlation(self) -> Dict:
        """Analyze nutrition impact on visual markers"""

        # Extract macro data
        macro_data = []
        for entry in self.data_sources["journal"]:
            if entry["data"].get("type") == "macro_log":
                macro_data.append(entry["data"])

        if not macro_data:
            return {"status": "no_nutrition_data"}

        # Calculate averages
        avg_calories = np.mean([m.get("calories", 0) for m in macro_data])
        avg_protein = np.mean([m.get("protein", 0) for m in macro_data])

        return {
            "average_calories": round(avg_calories),
            "average_protein": round(avg_protein),
            "protein_per_kg": round(avg_protein / 85, 1),  # Assuming 85kg bodyweight
            "recommendation": "Increase protein" if avg_protein < 170 else "Protein intake optimal",
        }

    def generate_convergence_report(self) -> str:
        """Generate comprehensive convergence analysis report"""

        peptide_visual = self.analyze_peptide_visual_correlation()
        lifestyle = self.analyze_lifestyle_impact()

        report = f"""
■ CONVERGENCE ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

■■ Peptide-Visual Correlations
"""

        if peptide_visual.get("correlations"):
            for compound, data in peptide_visual["correlations"].items():
                report += f"\n{compound} ({data['dose']})\n"

                changes = data.get("visual_changes", {})
                for metric, change_data in changes.items():
                    if change_data["change"] != 0:
                        direction = "↑" if change_data["change"] > 0 else "↓"
                        report += (
                            f"  • {metric}: {direction} {abs(change_data['percent_change'])}%\n"
                        )
        else:
            report += "  Insufficient data for analysis\n"

        report += f"""
■■ Lifestyle Impact Analysis

Sleep Correlation: {lifestyle['sleep_impact'].get('interpretation', 'unknown')}
Training Impact: {lifestyle['training_impact'].get('recovery_score', 0) * 100:.0f}% recovery efficiency
Nutrition Status: {lifestyle['nutrition_impact'].get('recommendation', 'unknown')}

■■ Key Recommendations
"""

        for rec in lifestyle.get("recommendations", []):
            report += f"  • {rec}\n"

        summary = peptide_visual.get("summary", {})
        if summary.get("strongest_positive"):
            report += (
                f"  • {summary['strongest_positive']} showing best results for visual improvement\n"
            )

        report += "\n■ End of Convergence Report"

        return report

    def export_for_visualization(self) -> Dict:
        """Export data formatted for visualization tools"""

        # Create time-aligned dataframes
        data = {
            "timestamps": [],
            "ptosis": [],
            "inflammation": [],
            "peptide_events": [],
            "sleep_hours": [],
            "training_load": [],
        }

        # This would be expanded to create properly aligned time series
        # data for visualization in tools like Plotly or Matplotlib

        return data
