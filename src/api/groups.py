from typing import List, Dict, Union

from src.config import config, logger
from src.api.client import get_gitlab_client

def get_groups() -> List[Dict]:
    """
    Fetch all available groups from GitLab API using the GitLab SDK.

    Returns:
        List of group dictionaries

    Raises:
        Exception: If there's an error fetching groups
    """
    logger.info("🔍 Fetching groups...")

    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Fetch groups using the client
        groups = client.get_groups()

        logger.info(f"Successfully fetched {len(groups)} groups")
        return groups
    except Exception as e:
        logger.error(f"Failed to fetch groups: {str(e)}")
        raise

def get_subgroups(parent_id: Union[str, int]) -> List[Dict]:
    """
    Fetch all subgroups of a specific group from GitLab API using the GitLab SDK.

    Args:
        parent_id: The parent group ID

    Returns:
        List of subgroup dictionaries

    Raises:
        Exception: If there's an error fetching subgroups
    """
    logger.debug(f"Fetching subgroups for group {parent_id}...")

    try:
        # Get GitLab client
        client = get_gitlab_client(config.gitlab_url, config.access_token)

        # Fetch subgroups using the client
        subgroups = client.get_subgroups(parent_id)

        logger.debug(f"Successfully fetched {len(subgroups)} subgroups for group {parent_id}")
        return subgroups
    except Exception as e:
        logger.error(f"Failed to fetch subgroups for group {parent_id}: {str(e)}")
        raise

def build_group_tree(groups: List[Dict]) -> Dict:
    """
    Build a hierarchical tree of groups and their subgroups.

    Args:
        groups: List of group dictionaries from GitLab API

    Returns:
        Dictionary representing the group hierarchy
    """
    # First, create a mapping of group IDs to their data
    group_map = {str(group['id']): {
        'id': str(group['id']),
        'name': group['name'],
        'full_path': group['full_path'],
        'parent_id': str(group['parent_id']) if group.get('parent_id') else None,
        'subgroups': []
    } for group in groups}

    # Build the tree structure
    root_groups = []
    for group_id, group_data in group_map.items():
        parent_id = group_data['parent_id']
        if parent_id and parent_id in group_map:
            group_map[parent_id]['subgroups'].append(group_data)
        else:
            root_groups.append(group_data)

    return {'subgroups': root_groups}
