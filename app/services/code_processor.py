from typing import Dict, List, Optional, Union
import json
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CodeFileType(str, Enum):
    PYTHON = "py"
    JAVASCRIPT = "js"
    TYPESCRIPT = "ts"
    JSON = "json"
    YAML = "yaml"
    OTHER = "other"

@dataclass
class CodeFile:
    path: str
    content: str
    file_type: CodeFileType
    imports: List[str]
    exports: List[str]
    functions: List[Dict]
    classes: List[Dict]
    size: int
    metadata: Dict

class CodeProcessor:
    def __init__(self):
        self.supported_extensions = {
            ".py": CodeFileType.PYTHON,
            ".js": CodeFileType.JAVASCRIPT,
            ".ts": CodeFileType.TYPESCRIPT,
            ".json": CodeFileType.JSON,
            ".yaml": CodeFileType.YAML,
            ".yml": CodeFileType.YAML
        }

    def process_codebase_json(self, json_content: Union[str, Dict]) -> Dict[str, CodeFile]:
        try:
            if isinstance(json_content, str):
                data = json.loads(json_content)
            else:
                data = json_content

            processed_files = {}
            
            for file in data.get("files", []):
                try:
                    path = file.get("path", "")
                    extension = Path(path).suffix
                    file_type = self.supported_extensions.get(extension, CodeFileType.OTHER)
                    
                    processed_file = CodeFile(
                        path=path,
                        content=file.get("content", ""),
                        file_type=file_type,
                        imports=self.extract_imports(file),
                        exports=self.extract_exports(file),
                        functions=self.extract_functions(file),
                        classes=self.extract_classes(file),
                        size=file.get("size", 0),
                        metadata=self.extract_metadata(file)
                    )
                    
                    processed_files[path] = processed_file
                    logger.info(f"Processed file: {path}")
                    
                except Exception as e:
                    logger.error(f"Error processing file {file.get('path', 'unknown')}: {str(e)}")
                    continue
            
            return processed_files
        except Exception as e:
            logger.error(f"Error processing codebase: {str(e)}")
            raise

    def extract_imports(self, file: Dict) -> List[str]:
        imports = []
        try:
            context = file.get("context", {})
            if isinstance(context.get("imports"), list):
                imports.extend(context["imports"])
        except Exception:
            pass
        return imports

    def extract_exports(self, file: Dict) -> List[str]:
        exports = []
        try:
            context = file.get("context", {})
            if isinstance(context.get("exports"), list):
                exports.extend(context["exports"])
        except Exception:
            pass
        return exports

    def extract_functions(self, file: Dict) -> List[Dict]:
        functions = []
        try:
            context = file.get("context", {})
            elements = context.get("elements", [])
            
            for element in elements:
                if element.get("type") == "functiondef":
                    functions.append({
                        "name": element.get("name", ""),
                        "doc": element.get("doc", ""),
                        "type": "function"
                    })
        except Exception:
            pass
        return functions

    def extract_classes(self, file: Dict) -> List[Dict]:
        classes = []
        try:
            context = file.get("context", {})
            elements = context.get("elements", [])
            
            for element in elements:
                if element.get("type") == "classdef":
                    classes.append({
                        "name": element.get("name", ""),
                        "doc": element.get("doc", ""),
                        "type": "class"
                    })
        except Exception:
            pass
        return classes

    def extract_metadata(self, file: Dict) -> Dict:
        return {
            "size": file.get("size", 0),
            "type": file.get("type", "unknown"),
            "context": file.get("context", {})
        }

    def get_file_content(self, processed_files: Dict[str, CodeFile], path: str) -> Optional[str]:
        if path in processed_files:
            return processed_files[path].content
        return None

    def get_file_structure(self, processed_files: Dict[str, CodeFile]) -> Dict:
        structure = {}
        for path, file in processed_files.items():
            structure[path] = {
                "type": file.file_type,
                "size": file.size,
                "functions": [f["name"] for f in file.functions],
                "classes": [c["name"] for c in file.classes],
                "imports": file.imports,
                "exports": file.exports
            }
        return structure

    def search_codebase(self, processed_files: Dict[str, CodeFile], query: str) -> List[Dict]:
        results = []
        for path, file in processed_files.items():
            if query.lower() in file.content.lower():
                results.append({
                    "path": path,
                    "type": file.file_type,
                    "matches": file.content.lower().count(query.lower()),
                    "preview": self.get_context_preview(file.content, query)
                })
        return results

    def get_context_preview(self, content: str, query: str, context_lines: int = 2) -> str:
        lines = content.split('\n')
        preview_lines = []
        query = query.lower()
        
        for i, line in enumerate(lines):
            if query in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                preview_lines.extend(lines[start:end])
                preview_lines.append('...')
        
        return '\n'.join(preview_lines)