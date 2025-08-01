#!/usr/bin/env python3
"""
Generate Prometheus recording rules from KPI Registry
"""
import yaml
import sys
from pathlib import Path
from typing import Dict, List

def generate_recording_rules(kpi_registry_path: str) -> Dict:
    """Generate Prometheus recording rules for KPI aggregations"""
    
    with open(kpi_registry_path) as f:
        registry = yaml.safe_load(f)
    
    rules = []
    
    for kpi in registry['kpis']:
        base_metric = kpi['prometheus_metric']
        
        # Generate 5m rate rule for all metrics
        rules.append({
            'record': f'{base_metric}:rate5m',
            'expr': f'rate({base_metric}[5m])'
        })
        
        # Generate 1h average
        rules.append({
            'record': f'{base_metric}:avg1h',
            'expr': f'avg_over_time({base_metric}[1h])'
        })
        
        # Generate daily aggregations
        rules.append({
            'record': f'{base_metric}:avg24h',
            'expr': f'avg_over_time({base_metric}[24h])'
        })
        
        # Generate user-specific aggregations
        rules.append({
            'record': f'{base_metric}:by_user',
            'expr': f'avg by (user_id) ({base_metric})'
        })
        
        # Add specific rules based on metric type
        if kpi['unit'] in ['milliseconds', 'ms']:
            # Add percentile calculations for latency metrics
            rules.append({
                'record': f'{base_metric}:p95',
                'expr': f'quantile(0.95, {base_metric})'
            })
            rules.append({
                'record': f'{base_metric}:p99',
                'expr': f'quantile(0.99, {base_metric})'
            })
        
        # Add threshold-based rules
        if 'risk_thresholds' in kpi:
            if 'critical' in kpi['risk_thresholds']:
                condition = kpi['risk_thresholds']['critical']['condition']
                if '<' in condition:
                    threshold = float(condition.split('<')[1].strip())
                    rules.append({
                        'record': f'{base_metric}:critical_low',
                        'expr': f'{base_metric} < {threshold}'
                    })
                elif '>' in condition:
                    threshold = float(condition.split('>')[1].strip())
                    rules.append({
                        'record': f'{base_metric}:critical_high',
                        'expr': f'{base_metric} > {threshold}'
                    })
    
    # Add composite rules
    rules.extend(generate_composite_rules(registry['kpis']))
    
    return {
        'groups': [{
            'name': 'auren_kpi_aggregations',
            'interval': '30s',
            'rules': rules
        }]
    }

def generate_composite_rules(kpis: List[Dict]) -> List[Dict]:
    """Generate composite metric rules"""
    rules = []
    
    # Overall system health score (example composite metric)
    kpi_metrics = [kpi['prometheus_metric'] for kpi in kpis]
    
    if len(kpi_metrics) >= 3:
        # Create a normalized health score
        rules.append({
            'record': 'auren:system_health_score',
            'expr': f'''
                (
                    (clamp_max(auren_recovery_score / 100, 1)) * 0.4 +
                    (clamp_max((100 - auren_sleep_debt_hours * 10) / 100, 1)) * 0.3 +
                    (clamp_max(auren_hrv_rmssd_ms / 100, 1)) * 0.3
                ) * 100
            '''
        })
    
    # User engagement score
    rules.append({
        'record': 'auren:user_engagement_score',
        'expr': 'count by (user_id) (rate(auren_hrv_rmssd_ms[5m]) > 0)'
    })
    
    return rules

def validate_rules(rules_config: Dict) -> bool:
    """Validate the generated rules"""
    try:
        # Check basic structure
        if 'groups' not in rules_config:
            print("❌ Missing 'groups' key")
            return False
        
        for group in rules_config['groups']:
            if 'name' not in group or 'rules' not in group:
                print("❌ Missing required keys in group")
                return False
            
            for rule in group['rules']:
                if 'record' not in rule or 'expr' not in rule:
                    print(f"❌ Missing required keys in rule: {rule}")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Prometheus recording rules from KPI registry')
    parser.add_argument('--input', required=True, help='Path to KPI registry YAML')
    parser.add_argument('--output', required=True, help='Output path for recording rules YAML')
    
    args = parser.parse_args()
    
    try:
        rules = generate_recording_rules(args.input)
        
        if not validate_rules(rules):
            print("❌ Generated rules failed validation")
            sys.exit(1)
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(rules, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Generated recording rules: {output_path}")
        print(f"   Rules: {len(rules['groups'][0]['rules'])}")
        
    except Exception as e:
        print(f"❌ Error generating rules: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()