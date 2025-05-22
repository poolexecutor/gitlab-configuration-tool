# GitLab Project Configuration Tool

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python script to automate the configuration of GitLab projects within a group. This tool helps standardize branch
protection rules and approval workflows across multiple projects.

## Features

- Multiple project selection with checkboxes (select one, many, or all projects)
- Creates and protects core branches (main, stage, develop)
- Sets up branch protection rules for wildcard patterns (feature/*, bugfix/*, etc.)
- Configures approval rules for protected branches
- Supports multiple configuration files for different branch protection strategies
- Checks if branches and rules already exist before creating them
- Handles API rate limiting and retries

## Requirements

- Python 3.6+
- `requests` library
- `python-dotenv` library
- `loguru` library
- `questionary` library (for interactive menus)
- `python-gitlab` library (for GitLab API integration)
- `pyyaml` library (for YAML configuration)
- `pydantic` library (for configuration validation)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd configure_projects_in_group
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure GitLab connection parameters in the YAML configuration file:

   A template file is provided at `branch_protection_template.yml`. Copy this template to create your
   configuration in the `configs` directory:
   ```
   mkdir -p configs
   cp branch_protection_template.yml configs/branch_protection.yml
   ```

   Then edit the `configs/branch_protection.yml` file and add your GitLab access token and optionally a default group
   ID:
   ```yaml
   # GitLab connection parameters
   gitlab:
     url: https://gitlab.com
     token: your_gitlab_access_token_here
     group_id: your_gitlab_group_id_here  # Optional: can be selected from menu
   ```

   The template includes detailed comments explaining all available configuration options.

   You can create multiple configuration files in the `configs` directory for different branch protection strategies:
   ```
   cp branch_protection_template.yml configs/strict_protection.yml
   cp branch_protection_template.yml configs/relaxed_protection.yml
   ```

   Then customize each configuration file according to your needs.

   Alternatively, you can still use environment variables by creating a `.env` file:
   ```
   cp .env.example .env
   ```

   And editing the `.env` file:
   ```
   GITLAB_URL=https://gitlab.com
   ACCESS_TOKEN=your_gitlab_access_token_here
   GROUP_ID=your_gitlab_group_id_here  # Optional: can be selected from menu
   ```

   Note: Configuration in the YAML file takes precedence over environment variables.

## Usage

Run the script with:

```
python main.py [options]
```

### Command-line Options

- `-v, --verbose`: Enable verbose logging for debugging
- `-c, --config`: Specify which configuration file to use from the configs directory

Examples:

```
# Use the default configuration (branch_protection.yml)
python main.py

# Use a specific configuration file
python main.py --config strict_protection.yml

# Enable verbose logging with a specific configuration
python main.py --verbose --config relaxed_protection.yml
```

The script will:

1. Prompt you to either:
    - Use the group ID from the .env file (if provided)
    - Select a group from an interactive menu with arrow-key navigation
2. Display all available GitLab groups, including nested subgroups
3. After selecting a group, fetch all projects in that group
4. Display an interactive checkbox menu to select multiple projects to configure
    - Navigate with arrow keys
    - Select/deselect projects with space bar
    - Use the "Select All" option to select all projects
    - Confirm your selection with enter
5. For each selected project:
    - Create and protect core branches (main, stage, develop)
    - Add approval rules for main and stage branches
    - Protect wildcard branch patterns
6. Print results for each operation

### Group Selection

When you run the script, you'll see an interactive menu like this:

```
📋 Loading GitLab groups...

📂 Select a GitLab Group:
❯ Group A (group-a)
  Group B (group-b)
  Subgroup B1 (group-b/subgroup-b1)
  Subgroup B2 (group-b/subgroup-b2)
  Nested Subgroup (group-b/subgroup-b2/nested)
  Group C (group-c)
```

Use the up and down arrow keys to navigate through the groups, and press Enter to select the highlighted group.

### Project Selection

After selecting a group, you'll see an interactive checkbox menu for selecting multiple projects:

```
📋 Select Projects to Configure:
Use arrow keys to navigate, space to select, enter to confirm:
❯ ◯ [ Select All ]
  ◯ group-a/project-1
  ◯ group-a/project-2
  ◯ group-a/project-3
```

- Use the up and down arrow keys to navigate through the projects
- Press the space bar to select/deselect a project (selected projects will show a checkmark: ✓)
- Select the "[ Select All ]" option to select all projects at once
- Press Enter to confirm your selection and proceed with configuration

For example, after selecting some projects:

```
📋 Select Projects to Configure:
Use arrow keys to navigate, space to select, enter to confirm:
  ◯ [ Select All ]
  ✓ group-a/project-1
  ◯ group-a/project-2
  ✓ group-a/project-3
```

## Configuration

You can customize the script's behavior by modifying the YAML configuration files in the `configs` directory. By
default, the script uses `configs/branch_protection.yml`, but you can create multiple configuration files for different
scenarios and select them using the `--config` parameter.

```yaml
# Branch Protection Configuration

# GitLab connection parameters
gitlab:
  url: https://gitlab.com
  token: ""  # Your GitLab access token
  group_id: ""  # Your GitLab group ID (optional - can be selected from menu)

# GitLab access levels
access_levels:
  no_access: 0
  developer: 30
  maintainer: 40

# Core branches to create from 'main'
core_branches:
  - name: main
    ref: main
    push_access_level: maintainer
    merge_access_level: maintainer
    approval_required: true
  - name: stage
    ref: main
    push_access_level: maintainer
    merge_access_level: maintainer
    approval_required: true
  - name: develop
    ref: main
    push_access_level: developer
    merge_access_level: developer
    approval_required: false

# Wildcard branch patterns
wildcard_branches:
  - pattern: feature/*
    push_access_level: developer
    merge_access_level: developer
  - pattern: bugfix/*
    push_access_level: developer
    merge_access_level: developer
  - pattern: hotfix/*
    push_access_level: developer
    merge_access_level: developer
  - pattern: release/*
    push_access_level: developer
    merge_access_level: developer
```

This configuration file allows you to:

- Define access levels for branch protection
- Configure core branches with their reference branches, protection levels, and approval requirements
- Set up wildcard branch patterns with their protection levels

### Configuration Validation

The YAML configuration file is validated when loaded to ensure it has the correct structure and values. The validation
checks for:

1. **Required Sections**:
    - `access_levels`: Dictionary of access level names and their numeric values
    - `core_branches`: List of core branches to create and protect
    - `wildcard_branches`: List of wildcard branch patterns to protect

2. **GitLab Connection Parameters** (optional):
    - `gitlab`: Dictionary containing connection parameters
        - `url`: Must be a string (e.g., "https://gitlab.com")
        - `token`: Must be a string
        - `group_id`: Must be a string or integer

3. **Access Levels**:
    - Must include `no_access`, `developer`, and `maintainer` keys
    - Values must be integers

4. **Core Branches**:
    - Each branch must have `name` and `ref` fields
    - Optional fields: `push_access_level`, `merge_access_level`, `approval_required`
    - Access levels must reference valid keys from the `access_levels` section
    - `approval_required` must be a boolean if present

5. **Wildcard Branches**:
    - Each branch must have a `pattern` field
    - Optional fields: `push_access_level`, `merge_access_level`
    - Access levels must reference valid keys from the `access_levels` section

If the configuration file is invalid, an error message will be logged and default values will be used.

Alternatively, you can still customize the script's behavior by modifying the default values in `src/config.py`,
which will be used as fallback if no valid YAML configuration files are found:

## GitLab Permissions

The GitLab access token used must have the following permissions:

- `api` scope
- Maintainer or Owner access to the group

## License

[MIT License](LICENSE)
