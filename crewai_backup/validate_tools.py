#!/usr/bin/env python3
"""
CrewAI Studio Tool Validation Script
Checks for common issues that cause startup failures
"""

import os
import sys
import importlib.util
import inspect
from typing import Type
from pathlib import Path

def check_pydantic_compatibility(tool_class):
    """Check if a tool class is Pydantic V2 compatible"""
    issues = []
    
    # Check if args_schema has proper type annotation
    if hasattr(tool_class, 'args_schema'):
        # Get the annotation for args_schema
        annotations = getattr(tool_class, '__annotations__', {})
        if 'args_schema' not in annotations:
            issues.append(f"Missing type annotation for args_schema")
        else:
            # Check if the annotation includes Type[BaseModel]
            annotation = annotations['args_schema']
            if 'Type[BaseModel]' not in str(annotation) and 'type[BaseModel]' not in str(annotation):
                issues.append(f"args_schema should be typed as Type[BaseModel]")
    
    # Check for proper class attribute typing
    class_attrs = ['name', 'description']
    annotations = getattr(tool_class, '__annotations__', {})
    
    for attr in class_attrs:
        if hasattr(tool_class, attr) and attr not in annotations:
            issues.append(f"Missing type annotation for {attr} (should be: {attr}: str)")
    
    return issues

def validate_tool_file(file_path):
    """Validate a single tool file"""
    print(f"\n🔍 Validating {file_path}...")
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("temp_module", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find tool classes
        tool_classes = []
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                hasattr(obj, '_run') and 
                name.endswith('Tool')):
                tool_classes.append((name, obj))
        
        if not tool_classes:
            print(f"  ⚠️  No tool classes found in {file_path}")
            return False
        
        all_valid = True
        for class_name, tool_class in tool_classes:
            print(f"  📋 Checking {class_name}...")
            issues = check_pydantic_compatibility(tool_class)
            
            if issues:
                all_valid = False
                print(f"    ❌ Issues found:")
                for issue in issues:
                    print(f"      - {issue}")
            else:
                print(f"    ✅ {class_name} is valid")
        
        return all_valid
        
    except Exception as e:
        print(f"  ❌ Error loading {file_path}: {e}")
        return False

def main():
    """Main validation function"""
    print("🔧 CrewAI Studio Tool Validation")
    print("=" * 40)
    
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Find all tool files
    tools_dir = project_root / "app" / "tools"
    if not tools_dir.exists():
        print(f"❌ Tools directory not found: {tools_dir}")
        return False
    
    tool_files = list(tools_dir.glob("*.py"))
    tool_files = [f for f in tool_files if not f.name.startswith("__")]
    
    if not tool_files:
        print("❌ No tool files found!")
        return False
    
    print(f"📁 Found {len(tool_files)} tool files")
    
    all_valid = True
    for tool_file in tool_files:
        if not validate_tool_file(tool_file):
            all_valid = False
    
    print("\n" + "=" * 40)
    if all_valid:
        print("🎉 All tools are valid!")
        return True
    else:
        print("❌ Some tools have issues that need fixing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 