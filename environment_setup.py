"""
Environment setup script for Deriv ML Trading Bot
Helps configure the trading environment for local development and execution
"""
import os
import sys
import argparse
import shutil
import platform
import subprocess
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. Will attempt to install it.")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

def setup_environment():
    """Main environment setup function"""
    parse_args()

    print("\n=== Deriv ML Trading Bot - Environment Setup ===\n")

    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("Created .env file from .env.example")
        else:
            create_default_env_file()
            print("Created default .env file")

    # Load current environment variables
    load_dotenv()

    # Collect environment configuration
    collect_environment_variables()

    # Create necessary directories
    create_directories()

    # Check Python dependencies
    check_dependencies()

    # Create VS Code configuration if requested
    if args.vscode:
        create_vscode_config()

    print("\n=== Environment setup completed ===")
    print_usage_instructions()

def parse_args():
    global args
    parser = argparse.ArgumentParser(description="Setup environment for Deriv ML Trading Bot")
    parser.add_argument('--vscode', action='store_true', help='Create VS Code configuration')
    parser.add_argument('--force', action='store_true', help='Override existing files')
    parser.add_argument('--no-input', action='store_true', help='Don\'t prompt for user input, use defaults')
    args = parser.parse_args()
    return args

def create_default_env_file():
    """Create a default .env file with required variables"""
    default_env = """# Deriv ML Trading Bot Environment Configuration
# Updated by environment_setup.py

# Trading Environment (demo/real)
DERIV_BOT_ENV=demo

# Deriv API Tokens (get from https://app.deriv.com/account/api-token)
# You need tokens with "Read", "Trade", "Payments" and "Admin" permissions
DERIV_API_TOKEN_DEMO=YOUR_DEMO_TOKEN_HERE
DERIV_API_TOKEN_REAL=YOUR_REAL_TOKEN_HERE

# IMPORTANT: Set to "yes" to enable real trading mode (safety measure)
DERIV_REAL_MODE_CONFIRMED=no

# Application ID
APP_ID=1089

# Training Parameters
SEQUENCE_LENGTH=30
TRAINING_EPOCHS=50
MODEL_SAVE_PATH=models
"""

    with open(".env", "w") as f:
        f.write(default_env)

def collect_environment_variables():
    """Collect and save environment variables from user input"""
    if args.no_input:
        print("Skipping user input due to --no-input flag")
        return

    print("\nConfiguring environment variables:")
    print("(Press Enter to keep current value)\n")

    # Helper function to update env vars
    def update_env_var(var_name, prompt, current_value=None, is_secret=False):
        if current_value is None:
            current_value = os.getenv(var_name, "")

        if is_secret and current_value:
            display_value = "*" * 8 + current_value[-4:] if len(current_value) > 4 else "*" * len(current_value)
            new_value = input(f"{prompt} [{display_value}]: ")
        else:
            new_value = input(f"{prompt} [{current_value}]: ")

        if new_value:
            return new_value
        return current_value

    # Environment selection
    env = update_env_var("DERIV_BOT_ENV", "Trading environment (demo/real)")
    if env.lower() not in ["demo", "real"]:
        print("Invalid environment. Using 'demo' as default.")
        env = "demo"

    # API tokens
    demo_token = update_env_var("DERIV_API_TOKEN_DEMO", 
                               "Demo API token (from app.deriv.com/account/api-token)", 
                               is_secret=True)
    real_token = update_env_var("DERIV_API_TOKEN_REAL", 
                               "Real account API token (from app.deriv.com/account/api-token)",
                               is_secret=True)

    # Safety confirmation for real mode
    real_confirmed = "no"
    if env.lower() == "real":
        real_confirmed = update_env_var("DERIV_REAL_MODE_CONFIRMED", 
                                        "Confirm real trading mode (yes/no)", 
                                        current_value="no")
        if real_confirmed.lower() != "yes":
            print("Real mode requires explicit confirmation. Setting DERIV_REAL_MODE_CONFIRMED=no")
            real_confirmed = "no"

    # App ID
    app_id = update_env_var("APP_ID", "App ID", "1089")

    # Training parameters
    sequence_length = update_env_var("SEQUENCE_LENGTH", "Sequence length for training", "30")
    training_epochs = update_env_var("TRAINING_EPOCHS", "Training epochs", "50")
    model_path = update_env_var("MODEL_SAVE_PATH", "Model save path", "models")

    # Update .env file
    update_env_file({
        "DERIV_BOT_ENV": env,
        "DERIV_API_TOKEN_DEMO": demo_token,
        "DERIV_API_TOKEN_REAL": real_token,
        "DERIV_REAL_MODE_CONFIRMED": real_confirmed,
        "APP_ID": app_id,
        "SEQUENCE_LENGTH": sequence_length,
        "TRAINING_EPOCHS": training_epochs,
        "MODEL_SAVE_PATH": model_path
    })

    print("\nEnvironment variables updated successfully!")

def update_env_file(new_vars):
    """Update .env file with new variables"""
    # Read current content
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
    else:
        content = ""

    # Parse current variables
    lines = content.split("\n")
    env_vars = {}

    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip()

    # Update with new values
    env_vars.update(new_vars)

    # Write back to file
    new_content = []

    # Add header
    new_content.append("# Deriv ML Trading Bot Environment Configuration")
    new_content.append("# Updated by environment_setup.py on " + get_timestamp())
    new_content.append("")

    # Trading environment
    new_content.append("# Trading Environment (demo/real)")
    new_content.append(f"DERIV_BOT_ENV={env_vars['DERIV_BOT_ENV']}")
    new_content.append("")

    # API tokens
    new_content.append("# Deriv API Tokens (get from https://app.deriv.com/account/api-token)")
    new_content.append("# You need tokens with \"Read\", \"Trade\", \"Payments\" and \"Admin\" permissions")
    new_content.append(f"DERIV_API_TOKEN_DEMO={env_vars['DERIV_API_TOKEN_DEMO']}")
    new_content.append(f"DERIV_API_TOKEN_REAL={env_vars['DERIV_API_TOKEN_REAL']}")
    new_content.append("")

    # Safety confirmation
    new_content.append("# IMPORTANT: Set to \"yes\" to enable real trading mode (safety measure)")
    new_content.append(f"DERIV_REAL_MODE_CONFIRMED={env_vars['DERIV_REAL_MODE_CONFIRMED']}")
    new_content.append("")

    # Application ID
    new_content.append("# Application ID")
    new_content.append(f"APP_ID={env_vars['APP_ID']}")
    new_content.append("")

    # Training parameters
    new_content.append("# Training Parameters")
    new_content.append(f"SEQUENCE_LENGTH={env_vars['SEQUENCE_LENGTH']}")
    new_content.append(f"TRAINING_EPOCHS={env_vars['TRAINING_EPOCHS']}")
    new_content.append(f"MODEL_SAVE_PATH={env_vars['MODEL_SAVE_PATH']}")

    # Write to file
    with open(".env", "w") as f:
        f.write("\n".join(new_content))

def get_timestamp():
    """Get current timestamp in string format"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_directories():
    """Create necessary directories for the project"""
    directories = ["models", "model_archive", "logs", "data"]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Verified directory: {directory}")

def check_dependencies():
    """Check and report on required Python dependencies"""
    try:
        import importlib

        # Check for required packages
        required_packages = [
            "pandas",
            "numpy", 
            "tensorflow",
            "websockets",
            "matplotlib",
            "sklearn",
            "python-deriv-api"
        ]

        missing_packages = []
        installed_packages = []

        for package in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                installed_packages.append(package)
            except ImportError:
                missing_packages.append(package)

        if installed_packages:
            print("\nInstalled dependencies:")
            for package in installed_packages:
                print(f"- {package}")

        if missing_packages:
            print("\nMissing dependencies:")
            for package in missing_packages:
                print(f"- {package}")

            print("\nTo install missing dependencies, run:")
            print("pip install -r requirements.txt")

            if not args.no_input:
                install = input("\nWould you like to install missing dependencies now? (y/n): ")
                if install.lower() == 'y':
                    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
                    print("Dependencies installed successfully!")
        else:
            print("\nAll required Python dependencies are installed!")
    except Exception as e:
        print(f"\nError checking dependencies: {str(e)}")
        print("Please install required dependencies manually:")
        print("pip install -r requirements.txt")

def create_vscode_config():
    """Create VS Code configuration files"""
    vscode_dir = Path(".vscode")
    os.makedirs(vscode_dir, exist_ok=True)

    # Create launch.json for debugging
    launch_file = vscode_dir / "launch.json"
    if not launch_file.exists() or args.force:
        launch_config = """{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Check API Connection",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/test_api_connectivity.py",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Run Demo Mode",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--env", "demo"],
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Run Real Mode",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--env", "real"],
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Train Only",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--train-only"],
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Clean Models",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/clean_models.py",
            "args": ["--action", "both"],
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}"""
        with open(launch_file, "w") as f:
            f.write(launch_config)
        print(f"Created VS Code launch configuration: {launch_file}")
    else:
        print(f"VS Code launch configuration already exists: {launch_file}")

    # Create settings.json for Python configuration
    settings_file = vscode_dir / "settings.json"
    if not settings_file.exists() or args.force:
        settings_config = """{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "autopep8",
    "python.formatting.autopep8Args": ["--max-line-length", "100"],
    "editor.formatOnSave": true,
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ]
}"""
        with open(settings_file, "w") as f:
            f.write(settings_config)
        print(f"Created VS Code settings configuration: {settings_file}")
    else:
        print(f"VS Code settings configuration already exists: {settings_file}")

def print_usage_instructions():
    """Print usage instructions for the trading bot"""
    print("\nYou can now run the trading bot using the following commands:")

    print("\n=== Checking API Connectivity ===")
    print("python test_api_connectivity.py")

    print("\n=== Training Models ===")
    print("python main.py --train-only")

    print("\n=== Running in Demo Mode ===")
    print("python main.py --env demo")

    print("\n=== Running in Real Mode ===")
    print("1. First set DERIV_REAL_MODE_CONFIRMED=yes in .env file")
    print("2. Then run: python main.py --env real")

    print("\n=== Managing Model Files ===")
    print("python clean_models.py --action both  # Archive old and clean expired")
    print("python clean_models.py --action stats  # Show storage statistics")

    if args.vscode:
        print("\n=== VS Code Integration ===")
        print("Open the project in VS Code:")
        print("code .")
        print("\nUse the Run and Debug tab to select and launch configurations")

if __name__ == "__main__":
    setup_environment()