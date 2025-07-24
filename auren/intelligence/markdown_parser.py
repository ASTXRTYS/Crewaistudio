"""
Advanced Markdown Parser for Clinical Knowledge Base
This replaces the simple YAML loader with sophisticated parsing for clinical protocols
"""

import re
import yaml
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedSection:
    """Represents a parsed section of clinical knowledge"""
    title: str
    content: str
    metadata: Dict[str, Any]
    confidence_score: float
    evidence_level: str
    section_type: str

class ClinicalMarkdownParser:
    """
    Advanced parser for clinical knowledge in Markdown format.
    
    This parser handles:
    - Confidence scoring from evidence levels
    - Cross-reference resolution
    - Emergency protocol detection
    - Statistical validation requirements
    - Multi-specialist consensus building
    """
    
    def __init__(self):
        self.confidence_weights = {
            "definitive": 0.95,
            "strong": 0.85,
            "moderate": 0.75,
            "weak": 0.65,
            "emerging": 0.55,
            "clinical_experience": 0.70,
            "research_validated": 0.90,
            "peer_reviewed": 0.88,
            "expert_consensus": 0.92
        }
        
        self.emergency_indicators = [
            "emergency", "urgent", "critical", "red zone", "immediate",
            "life-threatening", "severe", "acute", "crisis"
        ]
        
        self.section_patterns = {
            "protocol": r'^#{1,3}\s*(?:Protocol|Procedure|Method)\s*:?\s*(.+)$',
            "evidence": r'^#{1,3}\s*(?:Evidence|Research|Studies)\s*:?\s*(.+)$',
            "confidence": r'^#{1,3}\s*(?:Confidence|Reliability)\s*:?\s*(.+)$',
            "emergency": r'^#{1,3}\s*(?:Emergency|Urgent)\s*:?\s*(.+)$',
            "validation": r'^#{1,3}\s*(?:Validation|Testing)\s*:?\s*(.+)$',
            "cross_reference": r'^#{1,3}\s*(?:Related|Cross-reference|See also)\s*:?\s*(.+)$'
        }
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a complete clinical knowledge file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_content(content, file_path.stem)
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return {}
    
    def parse_content(self, content: str, source_name: str = "unknown") -> Dict[str, Any]:
        """Parse markdown content into structured clinical knowledge"""
        
        # Split into sections
        sections = self._split_into_sections(content)
        
        # Parse frontmatter if present
        frontmatter, body = self._extract_frontmatter(content)
        
        # Parse each section
        parsed_sections = []
        for section_title, section_content in sections.items():
            parsed_section = self._parse_section(section_title, section_content)
            parsed_sections.append(parsed_section)
        
        # Extract metadata
        metadata = self._extract_metadata(frontmatter, body)
        
        # Build knowledge structure
        knowledge = {
            "source": source_name,
            "title": metadata.get("title", source_name),
            "description": metadata.get("description", ""),
            "domain": metadata.get("domain", "general"),
            "sections": parsed_sections,
            "metadata": metadata,
            "confidence_score": self._calculate_overall_confidence(parsed_sections),
            "emergency_protocols": self._detect_emergency_protocols(parsed_sections),
            "cross_references": self._extract_cross_references(body),
            "validation_requirements": self._extract_validation_requirements(body),
            "evidence_levels": self._extract_evidence_levels(parsed_sections)
        }
        
        return knowledge
    
    def _extract_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter from markdown"""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                body = match.group(2)
                return frontmatter or {}, body
            except yaml.YAMLError as e:
                logger.warning(f"Error parsing frontmatter: {e}")
                return {}, content
        
        return {}, content
    
    def _split_into_sections(self, content: str) -> Dict[str, str]:
        """Split content into sections based on headers"""
        sections = {}
        current_section = "introduction"
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for section headers
            header_match = re.match(r'^(#{1,6})\s*(.+)$', line.strip())
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save final section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _parse_section(self, title: str, content: str) -> ParsedSection:
        """Parse a single section into structured data"""
        
        # Determine section type
        section_type = self._determine_section_type(title)
        
        # Extract metadata from section
        metadata = self._extract_section_metadata(content)
        
        # Calculate confidence for this section
        confidence_score = self._calculate_section_confidence(title, content, metadata)
        
        # Determine evidence level
        evidence_level = self._determine_evidence_level(content, metadata)
        
        # Check for emergency indicators
        is_emergency = self._check_emergency_indicators(content)
        
        # Extract cross-references
        cross_refs = self._extract_section_cross_references(content)
        
        # Build parsed section
        parsed_section = ParsedSection(
            title=title,
            content=content,
            metadata={
                **metadata,
                "section_type": section_type,
                "is_emergency": is_emergency,
                "cross_references": cross_refs,
                "validation_required": "validation" in content.lower()
            },
            confidence_score=confidence_score,
            evidence_level=evidence_level,
            section_type=section_type
        )
        
        return parsed_section
    
    def _determine_section_type(self, title: str) -> str:
        """Determine the type of section based on title"""
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ["protocol", "procedure", "method"]):
            return "protocol"
        elif any(keyword in title_lower for keyword in ["evidence", "research", "study"]):
            return "evidence"
        elif any(keyword in title_lower for keyword in ["emergency", "urgent", "critical"]):
            return "emergency"
        elif any(keyword in title_lower for keyword in ["validation", "testing", "verification"]):
            return "validation"
        elif any(keyword in title_lower for keyword in ["confidence", "reliability", "accuracy"]):
            return "confidence"
        else:
            return "general"
    
    def _extract_section_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from section content"""
        metadata = {}
        
        # Extract YAML blocks
        yaml_blocks = re.findall(r'```yaml\s*\n(.*?)\n```', content, re.DOTALL)
        for yaml_block in yaml_blocks:
            try:
                parsed_yaml = yaml.safe_load(yaml_block)
                if isinstance(parsed_yaml, dict):
                    metadata.update(parsed_yaml)
            except yaml.YAMLError:
                pass
        
        # Extract key-value pairs
        key_value_pattern = r'^([A-Za-z_]+)\s*:\s*(.+)$'
        for line in content.split('\n'):
            match = re.match(key_value_pattern, line.strip())
            if match:
                key, value = match.groups()
                try:
                    # Try to parse as YAML
                    parsed_value = yaml.safe_load(value)
                    metadata[key.lower()] = parsed_value
                except:
                    metadata[key.lower()] = value
        
        return metadata
    
    def _calculate_section_confidence(self, title: str, content: str, metadata: Dict[str, Any]) -> float:
        """Calculate confidence score for a section"""
        
        # Start with base confidence
        confidence = 0.5
        
        # Boost based on evidence level
        evidence_level = metadata.get("evidence_level", "").lower()
        if evidence_level in self.confidence_weights:
            confidence = max(confidence, self.confidence_weights[evidence_level])
        
        # Boost based on validation status
        validation_status = metadata.get("validation_status", "").lower()
        if validation_status in ["validated", "confirmed", "verified"]:
            confidence = max(confidence, 0.85)
        
        # Boost based on source quality
        source_quality = metadata.get("source_quality", "").lower()
        if source_quality in self.confidence_weights:
            confidence = max(confidence, self.confidence_weights[source_quality])
        
        # Penalty for uncertainty indicators
        uncertainty_indicators = ["may", "might", "could", "possibly", "potentially"]
        content_lower = content.lower()
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in content_lower)
        confidence -= uncertainty_count * 0.05
        
        # Ensure confidence stays within bounds
        return max(0.1, min(1.0, confidence))
    
    def _determine_evidence_level(self, content: str, metadata: Dict[str, Any]) -> str:
        """Determine the evidence level from content and metadata"""
        
        # Check metadata first
        evidence_level = metadata.get("evidence_level", "").lower()
        if evidence_level:
            return evidence_level
        
        # Check content for evidence indicators
        content_lower = content.lower()
        
        if any(indicator in content_lower for indicator in ["randomized controlled trial", "meta-analysis", "systematic review"]):
            return "definitive"
        elif any(indicator in content_lower for indicator in ["cohort study", "case-control", "prospective"]):
            return "strong"
        elif any(indicator in content_lower for indicator in ["case series", "observational", "cross-sectional"]):
            return "moderate"
        elif any(indicator in content_lower for indicator in ["expert opinion", "clinical experience", "consensus"]):
            return "clinical_experience"
        else:
            return "emerging"
    
    def _check_emergency_indicators(self, content: str) -> bool:
        """Check if content contains emergency indicators"""
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in self.emergency_indicators)
    
    def _extract_cross_references(self, content: str) -> List[str]:
        """Extract cross-references to other knowledge"""
        cross_refs = []
        
        # Look for markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        for title, url in links:
            cross_refs.append({"type": "link", "title": title, "url": url})
        
        # Look for "see also" references
        see_also_pattern = r'(?:see also|related|cross-reference)[:\s]+([^\n]+)'
        matches = re.findall(see_also_pattern, content, re.IGNORECASE)
        for match in matches:
            cross_refs.append({"type": "text", "content": match.strip()})
        
        return cross_refs
    
    def _extract_validation_requirements(self, content: str) -> Dict[str, Any]:
        """Extract validation requirements from content"""
        requirements = {
            "required_data_points": 0,
            "minimum_duration": 0,
            "statistical_tests": [],
            "confidence_threshold": 0.0
        }
        
        # Extract data point requirements
        data_point_match = re.search(r'(\d+)\s+(?:data points?|observations?|samples?)', content, re.IGNORECASE)
        if data_point_match:
            requirements["required_data_points"] = int(data_point_match.group(1))
        
        # Extract duration requirements
        duration_match = re.search(r'(\d+)\s+(?:days?|weeks?|months?)', content, re.IGNORECASE)
        if duration_match:
            requirements["minimum_duration"] = int(duration_match.group(1))
        
        # Extract statistical tests
        stat_tests = ["t-test", "anova", "regression", "correlation", "chi-square"]
        for test in stat_tests:
            if test.lower() in content.lower():
                requirements["statistical_tests"].append(test)
        
        # Extract confidence threshold
        confidence_match = re.search(r'(\d+(?:\.\d+)?)%?\s+(?:confidence|significance)', content, re.IGNORECASE)
        if confidence_match:
            requirements["confidence_threshold"] = float(confidence_match.group(1)) / 100
        
        return requirements
    
    def _calculate_overall_confidence(self, sections: List[ParsedSection]) -> float:
        """Calculate overall confidence score for the entire knowledge"""
        if not sections:
            return 0.5
        
        # Weight sections by importance
        weights = {
            "protocol": 1.5,
            "evidence": 1.3,
            "validation": 1.2,
            "emergency": 1.4,
            "confidence": 1.1,
            "general": 1.0
        }
        
        total_weight = 0
        weighted_confidence = 0
        
        for section in sections:
            weight = weights.get(section.section_type, 1.0)
            weighted_confidence += section.confidence_score * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.5
    
    def _detect_emergency_protocols(self, sections: List[ParsedSection]) -> List[Dict[str, Any]]:
        """Detect emergency protocols in the knowledge"""
        emergency_protocols = []
        
        for section in sections:
            if section.section_type == "emergency" or section.metadata.get("is_emergency"):
                emergency_protocols.append({
                    "title": section.title,
                    "confidence": section.confidence_score,
                    "urgency_level": "high" if section.confidence_score > 0.9 else "medium",
                    "content": section.content[:200] + "..." if len(section.content) > 200 else section.content
                })
        
        return emergency_protocols
    
    def _extract_evidence_levels(self, sections: List[ParsedSection]) -> Dict[str, int]:
        """Count evidence levels across all sections"""
        evidence_counts = {
            "definitive": 0,
            "strong": 0,
            "moderate": 0,
            "weak": 0,
            "emerging": 0,
            "clinical_experience": 0
        }
        
        for section in sections:
            level = section.evidence_level
            if level in evidence_counts:
                evidence_counts[level] += 1
        
        return evidence_counts
    
    def _extract_section_cross_references(self, content: str) -> List[str]:
        """Extract cross-references within a section"""
        cross_refs = []
        
        # Look for markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        for title, url in links:
            cross_refs.append(f"{title} ({url})")
        
        # Look for section references
        section_ref_pattern = r'(?:see|refer to|check)\s+(?:the\s+)?(?:section|protocol)\s+["\']([^"\']+)["\']'
        matches = re.findall(section_ref_pattern, content, re.IGNORECASE)
        cross_refs.extend(matches)
        
        return cross_refs
    
    def _extract_metadata(self, frontmatter: Dict[str, Any], body: str) -> Dict[str, Any]:
        """Extract comprehensive metadata"""
        metadata = {
            **frontmatter,
            "source_type": "clinical_markdown",
            "parsing_version": "2.0",
            "confidence_indicators": self._extract_confidence_indicators(body),
            "validation_flags": self._extract_validation_flags(body),
            "emergency_flags": self._extract_emergency_flags(body)
        }
        
        return metadata
    
    def _extract_confidence_indicators(self, content: str) -> List[str]:
        """Extract confidence indicators from content"""
        indicators = []
        
        confidence_patterns = {
            "high": ["definitive", "strong evidence", "validated", "confirmed", "peer-reviewed"],
            "medium": ["moderate evidence", "some evidence", "likely", "probable"],
            "low": ["limited evidence", "preliminary", "suggests", "may indicate"]
        }
        
        content_lower = content.lower()
        for level, patterns in confidence_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    indicators.append(f"{level}:{pattern}")
        
        return indicators
    
    def _extract_validation_flags(self, content: str) -> List[str]:
        """Extract validation-related flags"""
        flags = []
        
        validation_keywords = [
            "validated", "tested", "verified", "confirmed", "statistical",
            "significant", "p-value", "confidence interval", "effect size"
        ]
        
        content_lower = content.lower()
        for keyword in validation_keywords:
            if keyword in content_lower:
                flags.append(keyword)
        
        return flags
    
    def _extract_emergency_flags(self, content: str) -> List[str]:
        """Extract emergency-related flags"""
        flags = []
        
        content_lower = content.lower()
        for indicator in self.emergency_indicators:
            if indicator in content_lower:
                flags.append(indicator)
        
        return flags
    
    def validate_knowledge_structure(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the parsed knowledge structure"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "confidence_score": knowledge.get("confidence_score", 0.5),
            "sections_count": len(knowledge.get("sections", [])),
            "emergency_protocols": len(knowledge.get("emergency_protocols", [])),
            "cross_references": len(knowledge.get("cross_references", []))
        }
        
        # Check for required sections
        required_sections = ["protocol", "evidence"]
        section_types = [s.section_type for s in knowledge.get("sections", [])]
        
        for required in required_sections:
            if required not in section_types:
                validation["warnings"].append(f"Missing {required} section")
        
        # Check confidence thresholds
        if knowledge.get("confidence_score", 0) < 0.5:
            validation["warnings"].append("Low overall confidence")
        
        # Check for emergency protocols
        if knowledge.get("emergency_protocols"):
            validation["warnings"].append("Contains emergency protocols - requires immediate validation")
        
        # Check for sufficient evidence
        evidence_levels = knowledge.get("evidence_levels", {})
        if evidence_levels.get("definitive", 0) + evidence_levels.get("strong", 0) < 1:
            validation["warnings"].append("Limited high-quality evidence")
        
        return validation
    
    def extract_hypothesis_candidates(self, knowledge: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract potential hypotheses from knowledge"""
        candidates = []
        
        for section in knowledge.get("sections", []):
            if section.section_type == "protocol":
                # Extract protocol as hypothesis
                hypothesis = {
                    "description": section.title,
                    "prediction": {
                        "protocol_effectiveness": "high",
                        "expected_outcome": "positive"
                    },
                    "evidence_criteria": [
                        {
                            "metric_types": ["outcome_score", "effectiveness_rating"],
                            "time_window_days": 30,
                            "min_data_points": 5
                        }
                    ],
                    "confidence": section.confidence_score,
                    "domain": knowledge.get("domain", "general")
                }
                candidates.append(hypothesis)
        
        return candidates
    
    def generate_knowledge_summary(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the knowledge"""
        return {
            "title": knowledge.get("title", "Unknown"),
            "domain": knowledge.get("domain", "general"),
            "confidence": knowledge.get("confidence_score", 0.5),
            "sections": len(knowledge.get("sections", [])),
            "emergency_protocols": len(knowledge.get("emergency_protocols", [])),
            "evidence_summary": knowledge.get("evidence_levels", {}),
            "validation_ready": knowledge.get("confidence_score", 0) > 0.7,
            "key_insights": self._extract_key_insights(knowledge)
        }
    
    def _extract_key_insights(self, knowledge: Dict[str, Any]) -> List[str]:
        """Extract key insights from knowledge"""
        insights = []
        
        for section in knowledge.get("sections", []):
            if section.confidence_score > 0.8:
                insights.append(f"{section.title} (confidence: {section.confidence_score:.2f})")
        
        return insights

# Usage example and testing
if __name__ == "__main__":
    parser = ClinicalMarkdownParser()
    
    # Example clinical knowledge
    example_content = """
---
title: "HRV-Based Training Optimization"
domain: "neuroscience"
confidence: 0.87
evidence_level: "strong"
---

# Protocol: HRV-Guided Training Intensity

## Overview
This protocol uses heart rate variability (HRV) to optimize training intensity and prevent overtraining.

## Evidence
Based on randomized controlled trials with 200+ participants showing 23% improvement in performance.

```yaml
evidence_level: "definitive"
studies: 5
participants: 247
confidence: 0.92
```

## Implementation
1. Measure HRV daily upon waking
2. Adjust training intensity based on HRV score
3. Reduce intensity when HRV drops >10% from baseline

## Validation Requirements
- Minimum 30 days of data
- Statistical significance p < 0.05
- Effect size > 0.3

## Emergency Protocols
If HRV drops >30% and symptoms of overtraining appear:
- Immediate rest day
- Consult healthcare provider
- Monitor for 48 hours

## Cross-References
- [Sleep Recovery Protocol](./sleep_recovery.md)
- [Stress Management](./stress_management.md)
"""
    
    parsed = parser.parse_content(example_content, "hrv_training")
    print("Parsed Knowledge:")
    print(f"Title: {parsed['title']}")
    print(f"Confidence: {parsed['confidence_score']}")
    print(f"Emergency Protocols: {len(parsed['emergency_protocols'])}")
    print(f"Sections: {len(parsed['sections'])}")
    
    # Validate structure
    validation = parser.validate_knowledge_structure(parsed)
    print(f"\nValidation: {validation}")
    
    # Extract hypotheses
    hypotheses = parser.extract_hypothesis_candidates(parsed)
    print(f"\nHypothesis Candidates: {len(hypotheses)}")
