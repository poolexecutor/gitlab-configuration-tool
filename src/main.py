import time
import typer

from src.config import (
    config, logger, configure_logger, list_available_configs, 
    load_config, DEFAULT_CONFIG_NAME
)
from src.api.projects import get_projects
from src.api.branches import create_branch, protect_branch
from src.api.approvals import add_approval_rule
from src.ui.menu import select_group_from_menu, select_multiple_projects_from_menu

# Create a Typer app instance
app = typer.Typer(help="Configure GitLab projects in a group")

@app.command()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    config_file: str = typer.Option(DEFAULT_CONFIG_NAME, "--config", "-c", help="Configuration file to use (from configs directory)"),
    log_file: str = typer.Option(None, "--log-file", "-l", help="Path to log file. If not provided, no file logging is performed.")
) -> None:
    """
    Configure GitLab projects in a group.
    """
    # Configure logger based on verbosity and log file path
    configure_logger(verbose, log_file)

    # Validate config choice
    available_configs = list_available_configs()
    config_choices = list(available_configs.keys())

    if not config_choices:
        logger.warning("No configuration files found in configs directory. Using default configuration.")
        return
    elif config_file not in config_choices:
        logger.warning(f"Configuration '{config_file}' not found. Available configs: {', '.join(config_choices)}")
        logger.warning(f"Using default configuration: {DEFAULT_CONFIG_NAME}")
        config_file = DEFAULT_CONFIG_NAME

    # Load the selected configuration
    logger.info(f"Using configuration file: {config_file}")
    load_config(config_file)

    # Validate configuration
    if not config.access_token:
        logger.error("❌ Error: ACCESS_TOKEN is not set in .env file")
        return

    try:
        # Let the user select a group from the menu
        selected_group_id = config.group_id

        # If GROUP_ID is not set in .env or user wants to select a different group
        if not config.group_id or input("\nUse group from .env file? (y/n): ").lower() != 'y':
            selected_group_id = select_group_from_menu()

        # Get all projects in the selected group
        all_projects = get_projects(selected_group_id)
        logger.info(f"📊 Found {len(all_projects)} projects in group {selected_group_id}")

        # Ask user to select projects using interactive menu
        projects_to_process = select_multiple_projects_from_menu(all_projects)
        logger.info(f"Configuring {len(projects_to_process)} selected projects...")

        for project in projects_to_process:
            project_id = project['id']
            project_name = project['path_with_namespace']
            logger.info(f"\n📘 Processing project: {project_name}")
            results = []

            # Create and protect core branches
            for branch in config.core_branches:
                b_name = branch["name"]
                ref = branch["ref"]
                status = create_branch(project_id, b_name, ref)
                logger.debug(f"Branch '{b_name}' creation status: {status}")

                # Get protection levels from branch configuration
                push_access_level = branch.get("push_access_level", "maintainer")
                merge_access_level = branch.get("merge_access_level", "maintainer")

                protection = protect_branch(
                    project_id, b_name,
                    push_level=config.access[push_access_level],
                    merge_level=config.access[merge_access_level]
                )
                logger.debug(f"Branch '{b_name}' protection status: {protection}")

                results.append((b_name, status, protection))

                # Add approval rules based on configuration
                approval_required = branch.get("approval_required", False)
                if approval_required:
                    approval_status = add_approval_rule(project_id, b_name, selected_group_id)
                    logger.debug(f"Branch '{b_name}' approval rule status: {approval_status}")
                    results.append((f"{b_name} approval", "—", approval_status))

                # Avoid rate limiting
                time.sleep(0.5)

            # Protect wildcard branches
            for branch_config in config.wildcard_branches_config:
                pattern = branch_config["pattern"]
                push_access_level = branch_config.get("push_access_level", "developer")
                merge_access_level = branch_config.get("merge_access_level", "developer")

                protection = protect_branch(
                    project_id, pattern,
                    push_level=config.access[push_access_level],
                    merge_level=config.access[merge_access_level],
                    wildcard=True
                )
                logger.debug(f"Wildcard pattern '{pattern}' protection status: {protection}")
                results.append((pattern, "—", protection))
                time.sleep(0.5)

            # Audit results
            for name, status, protection in results:
                logger.info(f" → Branch '{name}': {status} | {protection}")

        logger.success("✅ All projects processed successfully!")

    except Exception as e:
        logger.error(f"❌ Error: \n{str(e)}")
        logger.exception("Exception details:")

if __name__ == "__main__":
    app()
