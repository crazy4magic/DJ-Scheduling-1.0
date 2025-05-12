"""
Test script for the Folder Structure Enforcer agent.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.folder_structure_enforcer import FolderStructureEnforcer

def test_folder_structure_enforcer():
    """Test the Folder Structure Enforcer functionality."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Initialize the enforcer
    enforcer = FolderStructureEnforcer(str(project_root))
    
    # Test validation on app.py
    app_path = project_root / "app.py"
    if app_path.exists():
        print("\nValidating app.py:")
        errors = enforcer.validate_file(str(app_path))
        if errors:
            print("Found issues:")
            for error in errors:
                print(f"- {error}")
            
            print("\nSuggested corrections:")
            suggestions = enforcer.suggest_corrections(str(app_path))
            for suggestion in suggestions:
                print(f"- {suggestion}")
        else:
            print("No issues found!")
    
    # Test validation on a test file
    print("\nValidating test file:")
    errors = enforcer.validate_file(__file__)
    if errors:
        print("Found issues:")
        for error in errors:
            print(f"- {error}")
        
        print("\nSuggested corrections:")
        suggestions = enforcer.suggest_corrections(__file__)
        for suggestion in suggestions:
            print(f"- {suggestion}")
    else:
        print("No issues found!")

if __name__ == "__main__":
    test_folder_structure_enforcer() 