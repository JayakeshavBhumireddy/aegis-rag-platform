$ErrorActionPreference = "Stop"

python "$PSScriptRoot\validate_configs.py"
python "$PSScriptRoot\check_repo_hygiene.py"

