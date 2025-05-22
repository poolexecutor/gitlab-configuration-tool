import os
import sys
import yaml
from pathlib import Path
from loguru import logger
from typing import Dict
from pydantic import ValidationError

# Import Pydantic models from schemas.py
from src.schemas import (
    BranchProtectionConfig
)

# Path to the configs directory
CONFIGS_DIR = Path("configs")
DEFAULT_CONFIG_NAME = "branch_protection.yml"


def configure_logger(verbose=False, log_file=None):
    """
    Configure the logger with the specified verbosity level and log file.

    Args:
        verbose: Whether to enable verbose logging
        log_file: Path to the log file. If None, no file logging is performed.
    """
    # Remove default handlers
    logger.remove()

    # Set the log level based on verbosity
    console_level = "DEBUG" if verbose else "INFO"

    # Define formats based on verbosity
    if verbose:
        # Detailed format with function name, line, etc. for verbose mode
        console_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
        file_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    else:
        # Simplified format without sensitive data for non-verbose mode
        console_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        file_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"

    # Add console handler
    logger.add(
        sys.stderr,
        format=console_format,
        level=console_level
    )

    # Add file handler only if log_file is provided
    if log_file:
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            format=file_format,
            level="DEBUG"
        )
        logger.info(f"Logging to file: {log_file}")

    if verbose:
        logger.info("Verbose logging enabled")

# Initialize logger with default settings (will be reconfigured in main.py)
# Don't create a log file by default
configure_logger(verbose=False, log_file=None)

def list_available_configs() -> Dict[str, Path]:
    """
    List all available configuration files in the configs directory.

    Returns:
        Dict[str, Path]: Dictionary mapping config names to their file paths
    """
    configs = {}

    # Create configs directory if it doesn't exist
    if not CONFIGS_DIR.exists():
        CONFIGS_DIR.mkdir(parents=True)
        logger.warning(f"Created configs directory: {CONFIGS_DIR}")

    # List all YAML files in the configs directory
    for file_path in CONFIGS_DIR.glob("*.yml"):
        configs[file_path.name] = file_path

    return configs

# Load branch protection configuration
def load_branch_protection_config(config_name=None):
    """
    Load branch protection configuration from YAML file.

    Args:
        config_name (str, optional): Name of the configuration file to load.
            If None, uses the default configuration file.

    Returns:
        BranchProtectionConfig: The validated branch protection configuration
    """
    # If no config name is provided, use the default
    if config_name is None:
        config_name = DEFAULT_CONFIG_NAME

    # Get the full path to the configuration file
    config_path = CONFIGS_DIR / config_name
    template_path = Path("branch_protection_template.yml")

    try:
        if config_path.exists():
            with open(config_path, 'r') as file:
                config_dict = yaml.safe_load(file)

                # Validate the configuration using Pydantic
                try:
                    config = BranchProtectionConfig(**config_dict)
                    logger.info(f"Loaded configuration from {config_path}")
                    return config
                except ValidationError as e:
                    logger.error(f"Invalid branch protection configuration in {config_path}: {e}")
                    # Return default configuration
                    return BranchProtectionConfig(
                        access_levels={"no_access": 0, "guest": 10, "reporter": 20, "developer": 30, "maintainer": 40, "owner": 50},
                        core_branches=[],
                        wildcard_branches=[]
                    )
        else:
            logger.warning(f"Branch protection configuration file not found: {config_path}")

            # Return default configuration
            return BranchProtectionConfig(
                access_levels={"no_access": 0, "guest": 10, "reporter": 20, "developer": 30, "maintainer": 40, "owner": 50},
                core_branches=[],
                wildcard_branches=[]
            )
    except Exception as e:
        logger.error(f"Error loading branch protection configuration: {str(e)}")
        # Return default configuration
        return BranchProtectionConfig(
            access_levels={"no_access": 0, "guest": 10, "reporter": 20, "developer": 30, "maintainer": 40, "owner": 50},
            core_branches=[],
            wildcard_branches=[]
        )

class Config:
    _instance = None  # Singleton instance

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the configuration with default values"""
        self._branch_config = None
        self._gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
        self._access_token = os.getenv("ACCESS_TOKEN", "")
        self._group_id = os.getenv("GROUP_ID", "")
        self._access = {}
        self._core_branches = []
        self._wildcard_branches_config = []
        self._wildcard_branches = []

    def load(self, config_name=None):
        """
        Load configuration from a file.

        Args:
            config_name (str, optional): Name of the configuration file to load.
                If None, uses the default configuration file.
        """
        # Load the configuration
        self._branch_config = load_branch_protection_config(config_name)

        # Update configuration properties
        self._gitlab_url = self._branch_config.gitlab.url or os.getenv("GITLAB_URL", "https://gitlab.com")
        self._access_token = self._branch_config.gitlab.token or os.getenv("ACCESS_TOKEN", "")
        self._group_id = self._branch_config.gitlab.group_id or os.getenv("GROUP_ID", "")

        # GitLab access levels - convert Pydantic model to dict
        self._access = self._branch_config.access_levels.model_dump()

        # Branches to create from 'main' - convert Pydantic models to dicts
        self._core_branches = [branch.model_dump() for branch in self._branch_config.core_branches]

        # Wildcard branch patterns - convert Pydantic models to dicts
        self._wildcard_branches_config = [branch.model_dump() for branch in self._branch_config.wildcard_branches]

        # For backward compatibility, extract just the patterns for WILDCARD_BRANCHES
        self._wildcard_branches = [branch['pattern'] for branch in self._wildcard_branches_config]

    @property
    def branch_config(self):
        """Get the branch protection configuration"""
        return self._branch_config

    @property
    def gitlab_url(self):
        """Get the GitLab URL"""
        return self._gitlab_url

    @property
    def access_token(self):
        """Get the GitLab access token"""
        return self._access_token

    @property
    def group_id(self):
        """Get the GitLab group ID"""
        return self._group_id

    @property
    def access(self):
        """Get the GitLab access levels"""
        return self._access

    @property
    def core_branches(self):
        """Get the core branches configuration"""
        return self._core_branches

    @property
    def wildcard_branches_config(self):
        """Get the wildcard branches configuration"""
        return self._wildcard_branches_config

    @property
    def wildcard_branches(self):
        """Get the wildcard branch patterns"""
        return self._wildcard_branches


# Create a singleton instance of the Config class
config = Config()

# For backward compatibility, provide global variables that reference the config properties
def load_config(config_name=None):
    """
    Load configuration and update global variables.
    This function is kept for backward compatibility.

    Args:
        config_name (str, optional): Name of the configuration file to load.
            If None, uses the default configuration file.
    """
    config.load(config_name)


# Define global variables that reference the config properties for backward compatibility
def __getattr__(name):
    """
    Provide backward compatibility for global variables.
    This function is called when a global variable is not found in this module.
    """
    if name == 'GITLAB_URL':
        return config.gitlab_url
    elif name == 'ACCESS_TOKEN':
        return config.access_token
    elif name == 'GROUP_ID':
        return config.group_id
    elif name == 'ACCESS':
        return config.access
    elif name == 'CORE_BRANCHES':
        return config.core_branches
    elif name == 'WILDCARD_BRANCHES_CONFIG':
        return config.wildcard_branches_config
    elif name == 'WILDCARD_BRANCHES':
        return config.wildcard_branches
    elif name == 'branch_config':
        return config.branch_config
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Initialize the configuration
config.load()
