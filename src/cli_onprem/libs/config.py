"""Configuration management utilities."""

import os
import pathlib
from typing import Any, Dict

import yaml


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class ConfigManager:
    """Unified configuration management for all commands."""
    
    def __init__(self, config_name: str = "config.yaml"):
        """Initialize configuration manager.
        
        Args:
            config_name: Name of the configuration file
        """
        self.config_dir = pathlib.Path.home() / ".cli-onprem"
        self.config_path = self.config_dir / config_name
    
    def ensure_config_dir(self) -> None:
        """Ensure configuration directory exists with proper permissions."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # Set directory permissions to 700 (rwx------)
        os.chmod(self.config_dir, 0o700)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dictionary containing configuration data
            
        Raises:
            ConfigError: If configuration cannot be loaded
        """
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"설정 파일 로드 실패: {e}") from e
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
            
        Raises:
            ConfigError: If configuration cannot be saved
        """
        self.ensure_config_dir()
        
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            # Set file permissions to 600 (rw-------)
            os.chmod(self.config_path, 0o600)
        except Exception as e:
            raise ConfigError(f"설정 파일 저장 실패: {e}") from e
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.load_config()
        
        # Support dot notation for nested keys
        keys = key.split(".")
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        config = self.load_config()
        
        # Support dot notation for nested keys
        keys = key.split(".")
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self.save_config(config)
    
    def delete(self, key: str) -> bool:
        """Delete configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            
        Returns:
            True if key was deleted, False if key didn't exist
        """
        config = self.load_config()
        
        # Support dot notation for nested keys
        keys = key.split(".")
        current = config
        
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False
        
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            self.save_config(config)
            return True
        
        return False
    
    def exists(self) -> bool:
        """Check if configuration file exists.
        
        Returns:
            True if configuration file exists
        """
        return self.config_path.exists()