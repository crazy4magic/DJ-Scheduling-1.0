"""
Folder structure validation utility for DJ Schedule Manager.

This module enforces the project's folder structure and coding standards.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import re

class FolderStructureEnforcer:
    """Enforces project folder structure and coding standards."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.rules = {
            'required_dirs': ['utils', 'config', 'shared', 'tests'],
            'required_files': ['app.py', 'requirements.txt', 'README.md'],
            'import_rules': {
                'module_boundaries': {
                    'utils': 'should not import from app',
                    'config': 'should not import from utils',
                    'shared': 'can import from anywhere'
                }
            }
        }
    
    def validate_structure(self) -> List[str]:
        """Validate the project structure against defined rules."""
        errors = []
        
        # Check required directories
        for dir_name in self.rules['required_dirs']:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                errors.append(f"Missing required directory: {dir_name}")
            elif not dir_path.is_dir():
                errors.append(f"{dir_name} exists but is not a directory")
        
        # Check required files
        for file_name in self.rules['required_files']:
            file_path = self.project_root / file_name
            if not file_path.exists():
                errors.append(f"Missing required file: {file_name}")
            elif not file_path.is_file():
                errors.append(f"{file_name} exists but is not a file")
        
        return errors
    
    def validate_imports(self, file_path: Path) -> List[str]:
        """Validate imports in a Python file."""
        errors = []
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract imports
        imports = re.findall(r'^(?:from|import)\s+(.*?)(?:$|#)', content, re.MULTILINE)
        
        # Check import order
        std_imports = []
        third_party = []
        local = []
        
        for imp in imports:
            if imp.startswith('.'):
                local.append(imp)
            elif any(pkg in imp for pkg in ['streamlit', 'pandas']):
                third_party.append(imp)
            else:
                std_imports.append(imp)
        
        if not (std_imports and not third_party and not local) and \
           not (std_imports and third_party and not local) and \
           not (std_imports and third_party and local):
            errors.append("Imports are not in the correct order")
        
        # Check module boundaries
        module = file_path.parent.name
        if module in self.rules['import_rules']['module_boundaries']:
            for imp in local:
                if not self._check_module_boundary(module, imp):
                    errors.append(f"Import '{imp}' violates module boundary rules")
        
        return errors
    
    def _check_module_boundary(self, module: str, import_stmt: str) -> bool:
        """Check if an import statement follows module boundary rules."""
        rule = self.rules['import_rules']['module_boundaries'].get(module, '')
        
        if 'should not import from' in rule:
            forbidden = rule.split('should not import from')[1].strip()
            return not any(mod in import_stmt for mod in forbidden.split())
        
        return True 