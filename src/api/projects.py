from typing import List, Dict, Union

from src.config import config, logger
from src.api.client import get_gitlab_client

def get_projects(group_id: Union[str, int]) -> List[Dict]:
    """
    Fetch all projects in a GitLab group using the GitLab SDK.

    Args:
        group_id: The GitLab group ID

    Returns:
        List of project dictionaries

    Raises:
        Exception: If there's an error fetching projects
    """
    logger.info(f"🔍 Fetching projects for group {group_id}...")

    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Fetch projects using the client
        projects = client.get_projects(group_id)

        logger.info(f"Successfully fetched {len(projects)} projects for group {group_id}")
        return projects
    except Exception as e:
        logger.error(f"Failed to fetch projects for group {group_id}: {str(e)}")
        raise
