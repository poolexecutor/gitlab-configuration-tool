from typing import Union

from src.config import config, logger
from src.api.client import get_gitlab_client

def branch_exists(project_id: Union[int, str], branch_name: str) -> bool:
    """
    Check if a branch exists in a GitLab project using the GitLab SDK.

    Args:
        project_id: The GitLab project ID
        branch_name: The name of the branch to check

    Returns:
        True if the branch exists, False otherwise
    """
    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Check if branch exists
        return client.branch_exists(project_id, branch_name)
    except Exception as e:
        logger.error(f"Error checking if branch {branch_name} exists in project {project_id}: {str(e)}")
        return False

def create_branch(project_id: Union[int, str], branch: str, ref: str) -> str:
    """
    Create a new branch in a GitLab project using the GitLab SDK.

    Args:
        project_id: The GitLab project ID
        branch: The name of the branch to create
        ref: The reference branch to create from

    Returns:
        Status message indicating success or failure
    """
    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Create branch
        result = client.create_branch(project_id, branch, ref)

        if result["status"] == "created":
            return "✅ Created"
        elif result["status"] == "already_exists":
            return "⚠️ Already exists"
        else:
            return f"❌ Error: {result['message']}"
    except Exception as e:
        logger.error(f"Error creating branch {branch} in project {project_id}: {str(e)}")
        return f"❌ Error: {str(e)}"

def is_branch_protected(project_id: Union[int, str], branch: str) -> bool:
    """
    Check if a branch is already protected in a GitLab project using the GitLab SDK.

    Args:
        project_id: The GitLab project ID
        branch: The name of the branch to check

    Returns:
        True if the branch is protected, False otherwise
    """
    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Check if branch is protected
        return client.is_branch_protected(project_id, branch)
    except Exception as e:
        logger.error(f"Error checking if branch {branch} is protected in project {project_id}: {str(e)}")
        return False

def protect_branch(project_id: Union[int, str], branch: str, push_level: int, merge_level: int, wildcard: bool = False) -> str:
    """
    Protect a branch in a GitLab project using the GitLab SDK.

    Args:
        project_id: The GitLab project ID
        branch: The name of the branch to protect
        push_level: Access level required to push to the branch
        merge_level: Access level required to merge into the branch
        wildcard: Whether the branch name is a wildcard pattern

    Returns:
        Status message indicating success or failure
    """
    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Protect branch
        result = client.protect_branch(
            project_id, 
            branch, 
            push_level, 
            merge_level, 
            config.access["maintainer"],  # unprotect_access_level
            False,  # allow_force_push
            False,  # code_owner_approval_required
            wildcard
        )

        if result["status"] == "protected":
            return "🔒 Protected"
        elif result["status"] == "already_protected":
            return "🔒 Already protected"
        else:
            return f"❌ Protect error: {result['message']}"
    except Exception as e:
        logger.error(f"Error protecting branch {branch} in project {project_id}: {str(e)}")
        return f"❌ Protect error: {str(e)}"
