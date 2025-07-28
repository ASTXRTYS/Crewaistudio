#!/usr/bin/env python3
"""
Assert no CrewAI dependencies in runtime environment.
Author: Senior Engineer
Date: January 29, 2025
"""

import importlib.util
import pkg_resources
import sys
import json
import re

def check_crewai():
    """Check for any CrewAI packages in the runtime environment."""
    
    # Check installed packages
    found_pkgs = [
        d.project_name for d in pkg_resources.working_set
        if re.search(r'crew.?ai', d.project_name, re.I)
    ]
    
    # Check if CrewAI is importable
    spec = importlib.util.find_spec("crewai")
    
    if found_pkgs or spec:
        result = {
            "packages": found_pkgs,
            "import_spec": bool(spec)
        }
        print(json.dumps(result, indent=2))
        sys.exit("💥 CrewAI detected in runtime environment")
    
    print("✅ No CrewAI packages found in runtime environment")
    return True

if __name__ == "__main__":
    check_crewai() 