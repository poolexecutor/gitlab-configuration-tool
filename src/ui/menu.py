import sys
import questionary
from typing import List, Dict

from src.config import logger
from src.api.groups import get_groups, build_group_tree

def display_group_menu(group_tree: Dict, indent: int = 0, path: List[int] = None) -> List[Dict]:
    """
    Display a hierarchical menu of groups and return a flattened list with their paths.

    Args:
        group_tree: Dictionary representing the group hierarchy
        indent: Current indentation level
        path: Current path in the hierarchy

    Returns:
        List of dictionaries with group information and their menu paths
    """
    if path is None:
        path = []

    menu_items = []

    for i, group in enumerate(group_tree['subgroups']):
        current_path = path + [i]
        prefix = "  " * indent
        logger.info(f"{prefix}{len(menu_items) + 1}. {group['name']} ({group['full_path']})")

        menu_items.append({
            'id': group['id'],
            'name': group['name'],
            'full_path': group['full_path'],
            'path': current_path
        })

        if group['subgroups']:
            sub_items = display_group_menu({'subgroups': group['subgroups']}, indent + 1, current_path)
            menu_items.extend(sub_items)

    return menu_items

def select_group_from_menu() -> str:
    """
    Display an interactive menu of available groups and let the user select one.

    Returns:
        The ID of the selected group
    """
    logger.info("\n📋 Loading GitLab groups...")

    try:
        # Get all groups (including subgroups)
        all_groups = get_groups()

        if not all_groups:
            logger.error("❌ No groups found. Please check your GitLab access token permissions.")
            sys.exit(1)

        # Build the group tree
        group_tree = build_group_tree(all_groups)

        # Display groups in a flat list for the interactive menu
        menu_items = display_group_menu(group_tree)

        # Create choices for questionary select
        choices = [
            {
                'name': f"{group['name']} ({group['full_path']})",
                'value': group['id']
            }
            for group in menu_items
        ]

        logger.info("\n📂 Select a GitLab Group:")

        # Display interactive select menu
        selected_group_id = questionary.select(
            "Use arrow keys to navigate, enter to select:",
            choices=choices,
        ).ask()

        # Check if user cancelled the selection
        if selected_group_id is None:
            logger.info("\nSelection cancelled by user. Exiting...")
            sys.exit(0)

        # Find the selected group to log its details
        selected_group = next((group for group in menu_items if group['id'] == selected_group_id), None)
        if selected_group:
            logger.info(f"\n✅ Selected group: {selected_group['name']} ({selected_group['full_path']})")

        return selected_group_id

    except Exception as e:
        logger.error(f"❌ Error fetching groups: {str(e)}")
        sys.exit(1)

def select_project_from_menu(projects: List[Dict]) -> Dict:
    """
    Display a menu of available projects and let the user select one.

    Args:
        projects: List of project dictionaries

    Returns:
        The selected project dictionary
    """
    logger.info("\n📋 Available Projects:")
    logger.info("---------------------------")

    for i, project in enumerate(projects, 1):
        logger.info(f"{i}. {project['path_with_namespace']}")

    logger.info("---------------------------")
    logger.info("0. Exit")

    while True:
        try:
            choice = int(input("\nSelect a project (enter number, or 0 to exit): "))
            if choice == 0:
                logger.info("Exiting...")
                sys.exit(0)
            elif 1 <= choice <= len(projects):
                selected_project = projects[choice - 1]
                logger.info(f"\n✅ Selected project: {selected_project['path_with_namespace']}")
                return selected_project
            else:
                logger.warning("❌ Invalid choice. Please try again.")
        except ValueError:
            logger.warning("❌ Please enter a number.")

def select_multiple_projects_from_menu(projects: List[Dict]) -> List[Dict]:
    """
    Display an interactive menu of available projects and let the user select multiple projects.

    Args:
        projects: List of project dictionaries

    Returns:
        List of selected project dictionaries
    """
    logger.info("\n📋 Select Projects to Configure:")

    # Create choices for questionary checkbox
    choices = [
        {
            'name': project['path_with_namespace'],
            'value': project,
            'checked': False
        }
        for project in projects
    ]

    # Add "Select All" option at the top
    select_all_option = {
        'name': '[ Select All ]',
        'value': 'all',
        'checked': False
    }
    choices.insert(0, select_all_option)

    # Display interactive checkbox menu
    result = questionary.checkbox(
        "Use arrow keys to navigate, space to select, enter to confirm:",
        choices=choices,
    ).ask()

    # Check if user cancelled the selection
    if result is None:
        logger.info("Selection cancelled by user. Exiting...")
        sys.exit(0)

    # Handle "Select All" option
    if 'all' in result:
        selected_projects = projects
    else:
        selected_projects = result

    # Log selected projects
    if selected_projects:
        logger.info(f"\n✅ Selected {len(selected_projects)} projects:")
        for project in selected_projects:
            logger.info(f" → {project['path_with_namespace']}")
    else:
        logger.warning("❌ No projects selected. Exiting...")
        sys.exit(0)

    return selected_projects
