from typing import Union

from src.config import config, logger
from src.api.client import get_gitlab_client

def approval_rule_exists(project_id: Union[int, str], rule_name: str) -> bool:
    """
    Check if an approval rule already exists in a GitLab project using the GitLab SDK.

    Args:
        project_id: The GitLab project ID
        rule_name: The name of the approval rule to check

    Returns:
        True if the rule exists, False otherwise
    """
    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Check if approval rule exists
        return client.approval_rule_exists(project_id, rule_name)
    except Exception as e:
        logger.error(f"Error checking if approval rule {rule_name} exists in project {project_id}: {str(e)}")
        return False

def add_approval_rule(project_id: Union[int, str], branch_name: str, group_id: Union[int, str], rule_name: str = "Maintainers Approval") -> str:
    """
    Add an approval rule to a GitLab project using the GitLab SDK.

    Args:
        project_id: The GitLab project ID
        branch_name: The name of the branch to add the rule for
        group_id: The GitLab group ID
        rule_name: The name of the approval rule

    Returns:
        Status message indicating success or failure
    """
    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Add approval rule
        result = client.add_approval_rule(project_id, branch_name, group_id, rule_name)

        if result["status"] == "created":
            return f"✅ Approval rule added for '{branch_name}'"
        elif result["status"] == "already_exists":
            return f"⚠️ Approval rule already exists for '{branch_name}'"
        else:
            return f"❌ Approval rule error for '{branch_name}': {result['message']}"
    except Exception as e:
        logger.error(f"Error adding approval rule for branch {branch_name} in project {project_id}: {str(e)}")
        return f"❌ Approval rule error for '{branch_name}': {str(e)}"
