import os
import time
from typing import Dict, List, Union
import gitlab
from gitlab.exceptions import GitlabError

from src.config import logger

class GitLabClient:
    """
    A client for interacting with the GitLab API using python-gitlab.
    """

    def __init__(self, url: str, token: str):
        """
        Initialize the GitLab client.

        Args:
            url: The GitLab URL
            token: The GitLab API token
        """
        self.url = url
        self.token = token
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "1"))

        # Initialize the GitLab client
        logger.debug(f"Initializing GitLab client with URL: {url}")
        self.gl = gitlab.Gitlab(url=url, private_token=token)

    def get_groups(self) -> List[Dict]:
        """
        Get all groups accessible by the authenticated user.

        Returns:
            List of group dictionaries
        """
        logger.debug("Fetching all groups")
        return self._with_retries(lambda: [group.asdict() for group in self.gl.groups.list(all=True)])

    def get_subgroups(self, group_id: Union[int, str]) -> List[Dict]:
        """
        Get all subgroups of a group.

        Args:
            group_id: The ID of the parent group

        Returns:
            List of subgroup dictionaries
        """
        logger.debug(f"Fetching subgroups for group {group_id}")
        return self._with_retries(lambda: [group.asdict() for group in self.gl.groups.get(group_id).subgroups.list(all=True)])

    def get_projects(self, group_id: Union[int, str]) -> List[Dict]:
        """
        Get all projects in a group.

        Args:
            group_id: The ID of the group

        Returns:
            List of project dictionaries
        """
        logger.debug(f"Fetching projects for group {group_id}")
        return self._with_retries(lambda: [project.asdict() for project in self.gl.groups.get(group_id).projects.list(all=True)])

    def branch_exists(self, project_id: Union[int, str], branch_name: str) -> bool:
        """
        Check if a branch exists in a project.

        Args:
            project_id: The ID of the project
            branch_name: The name of the branch

        Returns:
            True if the branch exists, False otherwise
        """
        logger.debug(f"Checking if branch {branch_name} exists in project {project_id}")
        try:
            self._with_retries(lambda: self.gl.projects.get(project_id).branches.get(branch_name))
            return True
        except gitlab.exceptions.GitlabGetError:
            return False

    def create_branch(self, project_id: Union[int, str], branch_name: str, ref: str) -> Dict:
        """
        Create a branch in a project.

        Args:
            project_id: The ID of the project
            branch_name: The name of the branch to create
            ref: The reference branch to create from

        Returns:
            Dictionary with status information
        """
        logger.debug(f"Creating branch {branch_name} in project {project_id} from {ref}")
        try:
            if self.branch_exists(project_id, branch_name):
                return {"status": "already_exists", "message": "Branch already exists"}

            self._with_retries(lambda: self.gl.projects.get(project_id).branches.create({
                'branch': branch_name,
                'ref': ref
            }))
            return {"status": "created", "message": "Branch created successfully"}
        except gitlab.exceptions.GitlabCreateError as e:
            if "already exists" in str(e):
                return {"status": "already_exists", "message": "Branch already exists"}
            return {"status": "error", "message": str(e)}

    def is_branch_protected(self, project_id: Union[int, str], branch_name: str) -> bool:
        """
        Check if a branch is protected in a project.

        Args:
            project_id: The ID of the project
            branch_name: The name of the branch

        Returns:
            True if the branch is protected, False otherwise
        """
        logger.debug(f"Checking if branch {branch_name} is protected in project {project_id}")
        protected_branches = self._with_retries(lambda: self.gl.projects.get(project_id).protectedbranches.list())
        return any(branch.name == branch_name for branch in protected_branches)

    def protect_branch(self, project_id: Union[int, str], branch_name: str, 
                      push_access_level: int, merge_access_level: int, 
                      unprotect_access_level: int = 40, 
                      allow_force_push: bool = False,
                      code_owner_approval_required: bool = False,
                      wildcard: bool = False) -> Dict:
        """
        Protect a branch in a project.

        Args:
            project_id: The ID of the project
            branch_name: The name of the branch to protect
            push_access_level: Access level required to push to the branch
            merge_access_level: Access level required to merge into the branch
            unprotect_access_level: Access level required to unprotect the branch
            allow_force_push: Whether to allow force push to the branch
            code_owner_approval_required: Whether code owner approval is required
            wildcard: Whether the branch name is a wildcard pattern

        Returns:
            Dictionary with status information
        """
        logger.debug(f"Protecting branch {branch_name} in project {project_id}")
        try:
            # Check if branch is already protected (only for non-wildcard branches)
            if not wildcard and self.is_branch_protected(project_id, branch_name):
                return {"status": "already_protected", "message": "Branch is already protected"}

            self._with_retries(lambda: self.gl.projects.get(project_id).protectedbranches.create({
                'name': branch_name,
                'push_access_level': push_access_level,
                'merge_access_level': merge_access_level,
                'unprotect_access_level': unprotect_access_level,
                'allow_force_push': allow_force_push,
                'code_owner_approval_required': code_owner_approval_required
            }))
            return {"status": "protected", "message": "Branch protected successfully"}
        except gitlab.exceptions.GitlabCreateError as e:
            if "already been protected" in str(e):
                return {"status": "already_protected", "message": "Branch is already protected"}
            return {"status": "error", "message": str(e)}

    def approval_rule_exists(self, project_id: Union[int, str], rule_name: str) -> bool:
        """
        Check if an approval rule exists in a project.

        Args:
            project_id: The ID of the project
            rule_name: The name of the approval rule

        Returns:
            True if the rule exists, False otherwise
        """
        logger.debug(f"Checking if approval rule {rule_name} exists in project {project_id}")
        approval_rules = self._with_retries(lambda: self.gl.projects.get(project_id).approvalrules.list())
        return any(rule.name == rule_name for rule in approval_rules)

    def add_approval_rule(self, project_id: Union[int, str], branch_name: str, 
                         group_id: Union[int, str], rule_name: str = "Maintainers Approval") -> Dict:
        """
        Add an approval rule to a project.

        Args:
            project_id: The ID of the project
            branch_name: The name of the branch to add the rule for
            group_id: The ID of the group to add as approvers
            rule_name: The name of the approval rule

        Returns:
            Dictionary with status information
        """
        logger.debug(f"Adding approval rule {rule_name} for branch {branch_name} in project {project_id}")
        try:
            if self.approval_rule_exists(project_id, rule_name):
                return {"status": "already_exists", "message": f"Approval rule already exists for '{branch_name}'"}

            self._with_retries(lambda: self.gl.projects.get(project_id).approvalrules.create({
                'name': rule_name,
                'approvals_required': 1,
                'group_ids': [group_id],
                'applies_to_all_protected_branches': False,
                'protected_branch_ids': [],
                'rule_type': 'regular',
                'contains_hidden_groups': True
            }))
            return {"status": "created", "message": f"Approval rule added for '{branch_name}'"}
        except gitlab.exceptions.GitlabCreateError as e:
            if "has already been taken" in str(e):
                return {"status": "already_exists", "message": f"Approval rule already exists for '{branch_name}'"}
            return {"status": "error", "message": str(e)}

    def _with_retries(self, operation, max_retries=None, retry_delay=None):
        """
        Execute an operation with retries.

        Args:
            operation: The operation to execute
            max_retries: Maximum number of retries (defaults to self.max_retries)
            retry_delay: Delay between retries in seconds (defaults to self.retry_delay)

        Returns:
            The result of the operation

        Raises:
            GitlabError: If the operation fails after all retries
        """
        if max_retries is None:
            max_retries = self.max_retries
        if retry_delay is None:
            retry_delay = self.retry_delay

        retries = 0
        while retries < max_retries:
            try:
                return operation()
            except GitlabError as e:
                status_code = getattr(e, 'response_code', 500)

                # For server errors, retry with exponential backoff
                if 500 <= status_code < 600:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries reached for server error: {str(e)}")
                        raise

                    # Exponential backoff for server errors
                    sleep_time = retry_delay * (2 ** (retries - 1))
                    logger.warning(f"Server error {status_code}, retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    # For 4xx client errors, don't retry as they indicate client-side issues
                    if 400 <= status_code < 500:
                        # Log 409 conflicts at DEBUG level, other client errors at INFO level
                        if status_code == 409:
                            logger.debug(f"{status_code} client error detected, not retrying: {str(e)}")
                        else:
                            logger.info(f"{status_code} client error detected, not retrying: {str(e)}")
                        raise

                    # For other errors, use normal retry logic
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries reached for non-server error: {str(e)}")
                        raise

                    logger.warning(f"Non-server error, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)

        logger.error("Max retries exceeded for all error types")
        raise GitlabError("Max retries exceeded")

# Create a function to get a GitLab client instance for backward compatibility
def get_gitlab_client(url: str, token: str) -> GitLabClient:
    """
    Get a GitLab client instance.

    Args:
        url: The GitLab URL
        token: The GitLab API token

    Returns:
        A GitLabClient instance
    """
    return GitLabClient(url, token)
