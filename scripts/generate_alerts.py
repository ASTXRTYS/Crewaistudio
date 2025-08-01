#!/usr/bin/env python3
"""
Generate Prometheus alert rules from KPI Registry
"""
import yaml
import sys
from pathlib import Path
from typing import Dict, List

def parse_condition(condition: str) -> tuple:
    """Parse a condition string like '< 20' or '> 100'"""
    if '<' in condition:
        return '<', float(condition.split('<')[1].strip())
    elif '>' in condition:
        return '>', float(condition.split('>')[1].strip())
    else:
        return None, None

def generate_alert_rules(kpi_registry_path: str) -> Dict:
    """Generate Prometheus alert rules from KPI thresholds"""
    
    with open(kpi_registry_path) as f:
        registry = yaml.safe_load(f)
    
    rules = []
    
    for kpi in registry['kpis']:
        if 'risk_thresholds' not in kpi:
            continue
            
        base_metric = kpi['prometheus_metric']
        kpi_name = kpi['name']
        
        # Generate critical alerts
        if 'critical' in kpi['risk_thresholds']:
            threshold = kpi['risk_thresholds']['critical']
            operator, value = parse_condition(threshold['condition'])
            
            if operator and value is not None:
                rules.append({
                    'alert': f'{kpi_name}_critical',
                    'expr': f'{base_metric} {operator} {value}',
                    'for': '5m',
                    'labels': {
                        'severity': 'critical',
                        'category': kpi.get('category', 'general'),
                        'kpi': kpi_name
                    },
                    'annotations': {
                        'summary': f'Critical: {kpi["description"]} {operator} {value}{kpi["unit"]}',
                        'description': f'{{{{ $labels.user_id }}}} has {kpi["description"]} {{{{ $value }}}}{kpi["unit"]} (threshold: {operator} {value})',
                        'action': threshold.get('action', 'Immediate attention required')
                    }
                })
        
        # Generate warning alerts
        if 'warning' in kpi['risk_thresholds']:
            threshold = kpi['risk_thresholds']['warning']
            operator, value = parse_condition(threshold['condition'])
            
            if operator and value is not None:
                rules.append({
                    'alert': f'{kpi_name}_warning',
                    'expr': f'{base_metric} {operator} {value}',
                    'for': '10m',
                    'labels': {
                        'severity': 'warning',
                        'category': kpi.get('category', 'general'),
                        'kpi': kpi_name
                    },
                    'annotations': {
                        'summary': f'Warning: {kpi["description"]} {operator} {value}{kpi["unit"]}',
                        'description': f'{{{{ $labels.user_id }}}} has {kpi["description"]} {{{{ $value }}}}{kpi["unit"]} (threshold: {operator} {value})',
                        'action': threshold.get('action', 'Attention required')
                    }
                })
        
        # Generate elevated alerts
        if 'elevated' in kpi['risk_thresholds']:
            threshold = kpi['risk_thresholds']['elevated']
            operator, value = parse_condition(threshold['condition'])
            
            if operator and value is not None:
                rules.append({
                    'alert': f'{kpi_name}_elevated',
                    'expr': f'{base_metric} {operator} {value}',
                    'for': '15m',
                    'labels': {
                        'severity': 'info',
                        'category': kpi.get('category', 'general'),
                        'kpi': kpi_name
                    },
                    'annotations': {
                        'summary': f'Elevated: {kpi["description"]} {operator} {value}{kpi["unit"]}',
                        'description': f'{{{{ $labels.user_id }}}} has {kpi["description"]} {{{{ $value }}}}{kpi["unit"]} (threshold: {operator} {value})',
                        'action': threshold.get('action', 'Monitor closely')
                    }
                })
    
    # Add system-level alerts
    rules.extend(generate_system_alerts())
    
    return {
        'groups': [{
            'name': 'auren_kpi_alerts',
            'interval': '30s',
            'rules': rules
        }]
    }

def generate_system_alerts() -> List[Dict]:
    """Generate system-level alerts"""
    return [
        {
            'alert': 'AurenHighErrorRate',
            'expr': 'rate(auren_errors_total[5m]) > 0.05',
            'for': '5m',
            'labels': {
                'severity': 'warning',
                'category': 'system'
            },
            'annotations': {
                'summary': 'High error rate detected in AUREN system',
                'description': 'Error rate is {{ $value }} errors/sec (threshold: 0.05)'
            }
        },
        {
            'alert': 'AurenNoData',
            'expr': 'up{job="neuros"} == 0',
            'for': '5m',
            'labels': {
                'severity': 'critical',
                'category': 'system'
            },
            'annotations': {
                'summary': 'NEUROS service is down',
                'description': 'NEUROS has been unreachable for 5 minutes'
            }
        },
        {
            'alert': 'AurenLowUserEngagement',
            'expr': 'auren:user_engagement_score < 0.1',
            'for': '1h',
            'labels': {
                'severity': 'info',
                'category': 'business'
            },
            'annotations': {
                'summary': 'Low user engagement detected',
                'description': 'Less than 10% of users are actively using the system'
            }
        }
    ]

def validate_alerts(alerts_config: Dict) -> bool:
    """Validate the generated alerts"""
    try:
        # Check basic structure
        if 'groups' not in alerts_config:
            print("❌ Missing 'groups' key")
            return False
        
        for group in alerts_config['groups']:
            if 'name' not in group or 'rules' not in group:
                print("❌ Missing required keys in group")
                return False
            
            for rule in group['rules']:
                if 'alert' not in rule or 'expr' not in rule:
                    print(f"❌ Missing required keys in alert: {rule}")
                    return False
                
                if 'labels' not in rule or 'severity' not in rule['labels']:
                    print(f"❌ Missing severity label in alert: {rule['alert']}")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Prometheus alert rules from KPI registry')
    parser.add_argument('--input', required=True, help='Path to KPI registry YAML')
    parser.add_argument('--output', required=True, help='Output path for alert rules YAML')
    
    args = parser.parse_args()
    
    try:
        alerts = generate_alert_rules(args.input)
        
        if not validate_alerts(alerts):
            print("❌ Generated alerts failed validation")
            sys.exit(1)
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(alerts, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Generated alert rules: {output_path}")
        print(f"   Alerts: {len(alerts['groups'][0]['rules'])}")
        
    except Exception as e:
        print(f"❌ Error generating alerts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()