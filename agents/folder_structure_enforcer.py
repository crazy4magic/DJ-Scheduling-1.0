"""
Folder Structure Enforcer Agent

This agent ensures all folders and files follow the modular architecture
as defined in PROJECT_STRUCTURE.md. It validates and suggests corrections
based on the folder and import rules.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

class FolderStructureEnforcer:
    def __init__(self, project_root: str):
        """
        Initialize the folder structure enforcer.
        
        Args:
            project_root (str): Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.structure_file = self.project_root / "PROJECT_STRUCTURE.md"
        self.rules = self._load_rules()
        
    def _load_rules(self) -> Dict:
        """
        Load rules from PROJECT_STRUCTURE.md.
        
        Returns:
            Dict: Parsed rules and requirements
        """
        if not self.structure_file.exists():
            raise FileNotFoundError("PROJECT_STRUCTURE.md not found")
            
        with open(self.structure_file, 'r') as f:
            content = f.read()
            
        return {
            'import_rules': self._parse_import_rules(content),
            'naming_conventions': self._parse_naming_conventions(content),
            'documentation': self._parse_documentation_rules(content)
        }
    
    def _parse_import_rules(self, content: str) -> Dict:
        """Parse import rules from the structure file."""
        import_rules = {
            'allowed_imports': [],
            'import_order': [],
            'module_boundaries': {}
        }
        
        # Extract import rules
        import_section = re.search(r'## Import Rules(.*?)(?=##|$)', content, re.DOTALL)
        if import_section:
            # Parse allowed imports
            allowed = re.search(r'Files can only import from:(.*?)(?=\d\.|$)', 
                              import_section.group(1), re.DOTALL)
            if allowed:
                import_rules['allowed_imports'] = [
                    line.strip('- ').strip()
                    for line in allowed.group(1).split('\n')
                    if line.strip().startswith('-')
                ]
            
            # Parse module boundaries
            boundaries = re.search(r'Module Boundaries(.*?)(?=\d\.|$)', 
                                 import_section.group(1), re.DOTALL)
            if boundaries:
                for line in boundaries.group(1).split('\n'):
                    if '→' in line or '->' in line:
                        module, rule = line.split(':', 1)
                        import_rules['module_boundaries'][module.strip()] = rule.strip()
        
        return import_rules
    
    def _parse_naming_conventions(self, content: str) -> Dict:
        """Parse naming conventions from the structure file."""
        naming_rules = {
            'python_files': [],
            'config_files': [],
            'function_types': {}
        }
        
        # Extract naming conventions
        naming_section = re.search(r'## File Naming Conventions(.*?)(?=##|$)', 
                                 content, re.DOTALL)
        if naming_section:
            # Parse Python file rules
            python_files = re.search(r'Python Files(.*?)(?=\d\.|$)', 
                                   naming_section.group(1), re.DOTALL)
            if python_files:
                naming_rules['python_files'] = [
                    line.strip('- ').strip()
                    for line in python_files.group(1).split('\n')
                    if line.strip().startswith('-')
                ]
            
            # Parse function naming rules
            function_section = re.search(r'## Function Naming Conventions(.*?)(?=##|$)', 
                                       content, re.DOTALL)
            if function_section:
                for line in function_section.group(1).split('\n'):
                    if line.strip().startswith('-'):
                        parts = line.split('with')
                        if len(parts) == 2:
                            func_type = parts[0].strip('- ').strip()
                            prefix = parts[1].strip().strip('`')
                            naming_rules['function_types'][func_type] = prefix
        
        return naming_rules
    
    def _parse_documentation_rules(self, content: str) -> Dict:
        """Parse documentation requirements from the structure file."""
        doc_rules = {
            'file_headers': '',
            'function_docs': ''
        }
        
        # Extract documentation rules
        doc_section = re.search(r'## Documentation Requirements(.*?)(?=##|$)', 
                              content, re.DOTALL)
        if doc_section:
            # Parse file header template
            headers = re.search(r'File Headers(.*?)(?=\d\.|$)', 
                              doc_section.group(1), re.DOTALL)
            if headers:
                doc_rules['file_headers'] = headers.group(1).strip()
            
            # Parse function documentation template
            func_docs = re.search(r'Function Documentation(.*?)(?=\d\.|$)', 
                                doc_section.group(1), re.DOTALL)
            if func_docs:
                doc_rules['function_docs'] = func_docs.group(1).strip()
        
        return doc_rules
    
    def validate_file(self, file_path: str) -> List[str]:
        """
        Validate a file against the project structure rules.
        
        Args:
            file_path (str): Path to the file to validate
            
        Returns:
            List[str]: List of validation errors/warnings
        """
        errors = []
        file_path = Path(file_path)
        
        # Check file naming convention
        if file_path.suffix == '.py':
            if not self._validate_python_filename(file_path.name):
                errors.append(f"File name '{file_path.name}' does not follow naming convention")
        
        # Check imports
        if file_path.suffix == '.py':
            import_errors = self._validate_imports(file_path)
            errors.extend(import_errors)
        
        # Check documentation
        if file_path.suffix == '.py':
            doc_errors = self._validate_documentation(file_path)
            errors.extend(doc_errors)
        
        return errors
    
    def _validate_python_filename(self, filename: str) -> bool:
        """Validate Python filename against naming conventions."""
        # Check if it follows snake_case
        if not re.match(r'^[a-z][a-z0-9_]*\.py$', filename):
            return False
        
        # Check if it's a config file
        if filename.endswith('_config.py'):
            return filename in self.rules['naming_conventions']['config_files']
        
        return True
    
    def _validate_imports(self, file_path: Path) -> List[str]:
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
    
    def _validate_documentation(self, file_path: Path) -> List[str]:
        """Validate documentation in a Python file."""
        errors = []
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check file header
        if not content.startswith('"""'):
            errors.append("Missing file header docstring")
        
        # Check function documentation
        functions = re.finditer(r'def\s+(\w+)\s*\(', content)
        for func in functions:
            func_name = func.group(1)
            func_def = func.group(0)
            func_start = content.find(func_def)
            
            # Look for docstring after function definition
            doc_start = content.find('"""', func_start)
            if doc_start == -1 or doc_start > content.find('\n', func_start) + 1:
                errors.append(f"Function '{func_name}' is missing docstring")
        
        return errors
    
    def suggest_corrections(self, file_path: str) -> List[str]:
        """
        Suggest corrections for a file based on validation results.
        
        Args:
            file_path (str): Path to the file to analyze
            
        Returns:
            List[str]: List of suggested corrections
        """
        suggestions = []
        file_path = Path(file_path)
        
        # Get validation errors
        errors = self.validate_file(file_path)
        
        # Generate suggestions based on errors
        for error in errors:
            if "does not follow naming convention" in error:
                suggestions.append(
                    f"Rename '{file_path.name}' to follow snake_case convention"
                )
            elif "Imports are not in the correct order" in error:
                suggestions.append(
                    "Reorder imports: 1) Standard library, 2) Third-party, 3) Local"
                )
            elif "violates module boundary rules" in error:
                suggestions.append(
                    "Move shared code to the shared directory or restructure imports"
                )
            elif "Missing file header docstring" in error:
                suggestions.append(
                    "Add a file header docstring describing the module's purpose"
                )
            elif "is missing docstring" in error:
                suggestions.append(
                    "Add a docstring to the function following the template in PROJECT_STRUCTURE.md"
                )
        
        return suggestions 