# Setting Up and Using the Trading Bot in VS Code

This document provides detailed instructions for setting up and running the ML Trading Bot for Deriv.com in Visual Studio Code.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [VS Code Configuration](#vs-code-configuration)
4. [Running the Bot](#running-the-bot)
5. [Debugging](#debugging)
6. [Recommended Workflow](#recommended-workflow)
7. [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Prerequisites

Before you begin, make sure you have the following installed:

- [Python 3.11](https://www.python.org/downloads/) or higher
- [Visual Studio Code](https://code.visualstudio.com/download)
- Python Extension for VS Code
- Account on [Deriv.com](https://deriv.com) with API tokens (demo and real)

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/deriv-ml-trading-bot.git
cd deriv-ml-trading-bot
```

### 2. Set Up the Environment

#### 2.1 Automatic Setup
Run the setup script:

```bash
python environment_setup.py --vscode
```

#### 2.2 Manual Development Environment Setup

1. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```
   DERIV_API_TOKEN_DEMO=YourDemoToken
   DERIV_API_TOKEN_REAL=YourRealToken
   DERIV_BOT_ENV=demo
   APP_ID=1089
   ```

2. **Configure the Python Interpreter**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Type "Python: Select Interpreter"
   - Select Python 3.11 interpreter

3. **Verify Extensions**:
   Make sure you have the following installed:
   - Python
   - Pylance
   - Python Debugger

4. **Verify Configuration**:
   - Run `python test_api_connectivity.py --mode demo`
   - Confirm successful connection
   - Repeat with `--mode real` if you plan to use real mode

The automatic setup command:
- Creates/updates the `.env` file with your configurations
- Verifies Python dependencies
- Creates configuration files for VS Code
- Sets up necessary folders

Alternatively, you can manually configure each component:

#### Manual Environment Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file**:
   - Copy `.env.example` to `.env`
   - Edit the file to include your Deriv API tokens

## VS Code Configuration

### 1. Open the Project

```bash
code .
```

### 2. Select the Python Interpreter

1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. Type "Python: Select Interpreter"
3. Select Python 3.11 or higher interpreter

### 3. Launch Configuration

If you ran `environment_setup.py --vscode`, the configuration files should already be created. Otherwise, manually create the following files:

#### .vscode/launch.json
```json
{
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
}
```

#### .vscode/settings.json
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "autopep8",
    "python.formatting.autopep8Args": ["--max-line-length", "100"],
    "editor.formatOnSave": true,
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ]
}
```

## Running the Bot

### Verify API Connection

Before running the full bot, it's recommended to verify the API connection:

1. In VS Code, open the "Run and Debug" tab (Ctrl+Shift+D)
2. Select the "Check API Connection" configuration
3. Press the play button (F5)

You should see a confirmation message if the connection is successful.

### Training Models

To train models without trading:

1. Select the "Train Only" configuration
2. Press the play button (F5)

#### Additional Training Options

If you want to customize training, you can modify the launch configuration by adding additional arguments:

```json
"args": [
    "--train-only",
    "--model-types", "short_term", "medium_term",
    "--data-source", "both",
    "--save-data",
    "--sequence-length", "40",
    "--epochs", "100"
],
```

### Running in Demo Mode

To run the bot in demo mode (without using real funds):

1. Select the "Run Demo Mode" configuration
2. Press the play button (F5)

### Running in Real Mode

**IMPORTANT**: Real mode uses real funds. Make sure you understand the risks.

1. First, edit the `.env` file and set:
   ```
   DERIV_REAL_MODE_CONFIRMED=yes
   ```

2. Select the "Run Real Mode" configuration
3. Press the play button (F5)

### Cleaning Model Files

To manage model files:

1. Select the "Clean Models" configuration
2. Press the play button (F5)

## Debugging

VS Code makes debugging the bot easy. You can:

1. Set breakpoints by clicking on the left margin next to line numbers
2. Inspect variables in the debug window
3. View output in the integrated console

### Advanced Debugging

For more detailed logs, add `--debug` to the arguments:

```json
"args": ["--env", "demo", "--debug"],
```

## Recommended Workflow

For efficient development and operation, the following workflow is recommended:

1. **Initial**:
   - Verify API connection
   - Train models in "train-only" mode
   - Verify generated model files

2. **Development**:
   - Make code changes
   - Test functionality in demo mode
   - Use breakpoints to debug issues

3. **Operation**:
   - Run in demo mode until satisfied with performance
   - Enable real mode with small amounts initially
   - Regularly monitor logs and performance

4. **Maintenance**:
   - Periodically clean model files
   - Retrain models with new data
   - Update configurations as needed

## Troubleshooting Common Issues

### Module `deriv_bot` Not Found

**Problem**: VS Code cannot find the `deriv_bot` module.

**Solution**:
1. Verify that the setting `python.analysis.extraPaths` includes `"${workspaceFolder}"`
2. Restart VS Code
3. If the problem persists, make sure you're running from the project root folder

### Error Connecting to the API

**Problem**: Cannot connect to the Deriv API.

**Solution**:
1. Verify that your API tokens in the `.env` file are correct
2. Check your internet connection
3. Make sure the account associated with the token is not blocked

### Errors During Training

**Problem**: Model training fails.

**Solution**:
1. Increase log level with `--debug`
2. Verify you have sufficient historical data
3. Check memory requirements for training
4. Try reducing model size or data amount

### Bot Not Trading

**Problem**: The bot runs but doesn't execute trades.

**Solution**:
1. Check logs for predictions
2. Verify if predictions are below the minimum threshold
3. Review risk management settings
4. Make sure the account has sufficient funds
