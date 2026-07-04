import pandas as pd
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3

from ..config.logging_config import get_logger


class DataReader:
    """Read location data from various sources"""
    
    def __init__(self):
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def read_csv(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Read data from CSV file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            df = pd.read_csv(file_path, **kwargs)
            self.logger.info(f"Successfully read CSV file: {file_path}, rows: {len(df)}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to read CSV file {file_path}: {str(e)}")
            raise
    
    def read_excel(self, file_path: Union[str, Path], sheet_name: Optional[Union[str, int]] = 0, **kwargs) -> pd.DataFrame:
        """Read data from Excel file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            self.logger.info(f"Successfully read Excel file: {file_path}, sheet: {sheet_name}, rows: {len(df)}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to read Excel file {file_path}: {str(e)}")
            raise
    
    def read_json(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Read data from JSON file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self.logger.info(f"Successfully read JSON file: {file_path}, records: {len(data)}")
                return data
            elif isinstance(data, dict):
                # If it's a single object, wrap it in a list
                self.logger.info(f"Successfully read JSON file: {file_path}, records: 1")
                return [data]
            else:
                raise ValueError(f"Invalid JSON format in {file_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to read JSON file {file_path}: {str(e)}")
            raise
    
    def read_database(self, connection_string: str, query: str) -> pd.DataFrame:
        """Read data from database"""
        try:
            engine = create_engine(connection_string)
            df = pd.read_sql(query, engine)
            self.logger.info(f"Successfully read from database, rows: {len(df)}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to read from database: {str(e)}")
            raise
        finally:
            if 'engine' in locals():
                engine.dispose()
    
    def read_sqlite(self, db_path: Union[str, Path], query: str) -> pd.DataFrame:
        """Read data from SQLite database"""
        db_path = Path(db_path)
        if not db_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(query, conn)
            self.logger.info(f"Successfully read from SQLite database: {db_path}, rows: {len(df)}")
            return df
        except Exception as e:
            self.logger.error(f"Failed to read from SQLite database {db_path}: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def detect_file_format(self, file_path: Union[str, Path]) -> str:
        """Detect file format based on extension"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        format_map = {
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.json': 'json',
            '.db': 'sqlite',
            '.sqlite': 'sqlite',
            '.sqlite3': 'sqlite'
        }
        
        return format_map.get(extension, 'unknown')
    
    def read_file(self, file_path: Union[str, Path], **kwargs) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
        """Automatically detect and read file based on extension"""
        file_path = Path(file_path)
        format_type = self.detect_file_format(file_path)
        
        if format_type == 'csv':
            return self.read_csv(file_path, **kwargs)
        elif format_type == 'excel':
            return self.read_excel(file_path, **kwargs)
        elif format_type == 'json':
            return self.read_json(file_path)
        elif format_type == 'sqlite':
            query = kwargs.pop('query', 'SELECT * FROM locations')
            return self.read_sqlite(file_path, query)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get information about a file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "path": str(file_path.absolute()),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": stat.st_mtime,
            "format": self.detect_file_format(file_path),
            "extension": file_path.suffix
        }
    
    def preview_file(self, file_path: Union[str, Path], rows: int = 5) -> Dict[str, Any]:
        """Preview file contents"""
        file_path = Path(file_path)
        format_type = self.detect_file_format(file_path)
        
        preview_data = {}
        
        try:
            if format_type in ['csv', 'excel']:
                df = self.read_file(file_path)
                preview_data = {
                    "format": format_type,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "preview": df.head(rows).to_dict('records'),
                    "dtypes": df.dtypes.to_dict()
                }
            elif format_type == 'json':
                data = self.read_json(file_path)
                preview_data = {
                    "format": format_type,
                    "rows": len(data),
                    "preview": data[:rows]
                }
            elif format_type == 'sqlite':
                df = self.read_sqlite(file_path, "SELECT * FROM sqlite_master WHERE type='table'")
                preview_data = {
                    "format": format_type,
                    "tables": df['name'].tolist() if not df.empty else [],
                    "preview": df.head(rows).to_dict('records') if not df.empty else []
                }
            
            # Add file info
            preview_data.update(self.get_file_info(file_path))
            
        except Exception as e:
            self.logger.error(f"Failed to preview file {file_path}: {str(e)}")
            raise
        
        return preview_data