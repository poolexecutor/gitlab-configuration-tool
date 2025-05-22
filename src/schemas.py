from typing import List, Optional, Union
from pydantic import BaseModel, Field, model_validator

# Define Pydantic models for configuration validation
class GitLabConfig(BaseModel):
    """GitLab connection configuration."""
    url: str = "https://gitlab.com"
    token: str = ""
    group_id: Optional[Union[str, int]] = ""

class AccessLevels(BaseModel):
    """GitLab access levels configuration."""
    no_access: int
    guest: int
    reporter: int
    developer: int
    maintainer: int
    owner: int

    # Allow additional access levels
    class Config:
        extra = "allow"

class CoreBranch(BaseModel):
    """Core branch configuration."""
    name: str
    ref: str
    push_access_level: Optional[str] = "maintainer"
    merge_access_level: Optional[str] = "maintainer"
    approval_required: Optional[bool] = False

    @model_validator(mode='after')
    def validate_access_levels(self):
        """Validate that access levels are valid."""
        # This validation will be performed after the model is created
        # The actual validation logic is in BranchProtectionConfig.validate_branch_access_levels
        return self

class WildcardBranch(BaseModel):
    """Wildcard branch pattern configuration."""
    pattern: str
    push_access_level: Optional[str] = "developer"
    merge_access_level: Optional[str] = "developer"

    @model_validator(mode='after')
    def validate_access_levels(self):
        """Validate that access levels are valid."""
        # This validation will be performed after the model is created
        # The actual validation logic is in BranchProtectionConfig.validate_branch_access_levels
        return self

class BranchProtectionConfig(BaseModel):
    """Complete branch protection configuration."""
    gitlab: Optional[GitLabConfig] = Field(default_factory=GitLabConfig)
    access_levels: AccessLevels
    core_branches: List[CoreBranch]
    wildcard_branches: List[WildcardBranch]

    @model_validator(mode='after')
    def validate_branch_access_levels(self):
        """Validate that branch access levels reference valid access level names."""
        valid_access_levels = list(self.access_levels.model_dump().keys())

        # Validate core branches
        for branch in self.core_branches:
            if branch.push_access_level and branch.push_access_level not in valid_access_levels:
                raise ValueError(f"Invalid push_access_level: {branch.push_access_level}. Must be one of {valid_access_levels}")
            if branch.merge_access_level and branch.merge_access_level not in valid_access_levels:
                raise ValueError(f"Invalid merge_access_level: {branch.merge_access_level}. Must be one of {valid_access_levels}")

        # Validate wildcard branches
        for branch in self.wildcard_branches:
            if branch.push_access_level and branch.push_access_level not in valid_access_levels:
                raise ValueError(f"Invalid push_access_level: {branch.push_access_level}. Must be one of {valid_access_levels}")
            if branch.merge_access_level and branch.merge_access_level not in valid_access_levels:
                raise ValueError(f"Invalid merge_access_level: {branch.merge_access_level}. Must be one of {valid_access_levels}")

        return self