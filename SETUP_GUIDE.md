# Deriv ML Trading Bot - Local Setup Guide

This guide provides comprehensive instructions for setting up the Deriv ML Trading Bot project on your local machine using Visual Studio Code.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Environment Configuration](#environment-configuration)
4. [VS Code Setup](#vs-code-setup)
5. [Running the Bot](#running-the-bot)
6. [Debugging](#debugging)
7. [Common Issues & Troubleshooting](#common-issues--troubleshooting)

## System Requirements

- **Python 3.11 or higher** - Required for compatibility with TensorFlow and other dependencies
- **Visual Studio Code** - Recommended IDE with Python extension
- **Git** - For cloning the repository
- **Deriv.com Account** - You'll need API tokens for demo and real accounts
- **Minimum 4GB RAM** - For model training and execution
- **Internet Connection** - For API communication with Deriv servers

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd deriv-ml-trading-bot
```

### 2. Set Up Python Environment

#### Option A: Using the Automated Setup Script (Recommended)

```bash
python environment_setup.py --vscode
```

This script will:
- Verify Python dependencies
- Create necessary directories
- Set up VS Code configuration
- Guide you through creating the `.env` file

#### Option B: Manual Setup

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install matplotlib==3.10.0 numpy==1.24.3 pandas==2.0.3 python-deriv-api>=0.1.6 python-dotenv>=1.0.1 scikit-learn>=1.6.1 tensorflow>=2.14.0 websockets>=10.3
```

> **Note**: The specific package versions listed above are known to work together without conflicts. Deviating from these versions may cause compatibility issues.

## Environment Configuration

### Creating the .env File

Create a file named `.env` in the project root with the following content:

```
# Trading Environment (demo/real)
DERIV_BOT_ENV=demo

# Deriv API Tokens (get from https://app.deriv.com/account/api-token)
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
```

### Obtaining Deriv API Tokens

1. Login to your [Deriv.com](https://app.deriv.com/) account
2. Navigate to Account Settings → Security and Limits → API Token
3. Create a token with the following permissions:
   - Read
   - Trade
   - Payments
   - Admin
   - Trading information
4. Create separate tokens for both Demo and Real accounts

## VS Code Setup

### Recommended Extensions

Install these VS Code extensions for the best development experience:

- **Python** - For Python language support
- **Pylance** - For improved type checking and IntelliSense
- **Python Debugger** - For debugging capabilities

### Configuring Python Path

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
3. Type "Python: Select Interpreter" and select your Python 3.11+ interpreter

### Launch Configurations

The setup script creates the necessary VS Code configuration files in the `.vscode` directory. These include:

- **launch.json** - Configurations for running different aspects of the bot
- **settings.json** - Python-specific settings and path configurations

For detailed VS Code-specific setup instructions, refer to [VSCODE_SETUP_EN.md](VSCODE_SETUP_EN.md).

## Running the Bot

### Verify API Connection

Before running the trading bot, verify your API connection:

```bash
python test_api_connectivity.py
```

You should see a successful connection message and account details.

### Training Models

Train the machine learning models before running the bot:

```bash
python main.py --train-only
```

Optional training parameters:
- `--model-types` - Specify model types to train (e.g., "short_term", "medium_term")
- `--data-source` - Choose data source ("api", "file", or "both")
- `--save-data` - Save fetched data for future use
- `--sequence-length` - Set the input sequence length (default: 30)
- `--epochs` - Number of training epochs (default: 50)

### Run in Demo Mode

Always start with demo mode to test your setup:

```bash
python main.py --env demo
```

Additional options:
- `--symbol` - Trading symbol (e.g., "frxEURUSD")
- `--stake-amount` - Amount to stake per trade
- `--debug` - Enable verbose logging
- `--dry-run` - Run without executing actual trades

### Run in Real Mode

**IMPORTANT**: Real mode uses real funds. Use with caution.

1. First, edit your `.env` file and set:
   ```
   DERIV_REAL_MODE_CONFIRMED=yes
   ```

2. Then run:
   ```bash
   python main.py --env real
   ```

## Debugging

### Using VS Code Debugger

1. Set breakpoints by clicking in the margin next to line numbers
2. Select the appropriate launch configuration from the Run and Debug panel
3. Press F5 or click the green play button to start debugging

### Enhanced Logging

To enable detailed logging:

```bash
python main.py --env demo --debug
```

Logs are saved in the `logs` directory.

## Common Issues & Troubleshooting

### ImportError: No module named 'numpy' or 'tensorflow'

**Problem**: Dependencies not properly installed.

**Solution**:
```bash
pip install numpy==1.24.3 tensorflow>=2.14.0
```

### ModuleNotFoundError: No module named 'deriv_bot'

**Problem**: Python cannot find the project module.

**Solution**:
Ensure you're running commands from the project root directory, or add the project directory to PYTHONPATH:

```bash
# Windows
set PYTHONPATH=%PYTHONPATH%;%CD%

# macOS/Linux
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### TensorFlow Warnings about CUDA

**Problem**: Warnings about CUDA not being available.

**Solution**: These are normal if you don't have a GPU. The bot will function correctly using CPU for training and predictions.

### Connection Error with Deriv API

**Problem**: Cannot connect to Deriv API.

**Solution**:
1. Verify your API tokens in the `.env` file
2. Check your internet connection
3. Ensure your Deriv account is active

### Intel MKL or libiomp5md.dll Conflicts

**Problem**: Numpy/TensorFlow conflicts on Windows.

**Solution**:
```bash
pip uninstall numpy
pip install numpy==1.24.3
```

### Model-Related Errors

**Problem**: Errors when loading or using models.

**Solution**:
1. Ensure models are trained first: `python main.py --train-only`
2. Check that the `models` directory exists and contains model files
3. If errors persist, delete existing models and retrain

## Additional Resources

- [Deriv API Documentation](https://api.deriv.com/)
- [TensorFlow Documentation](https://www.tensorflow.org/api_docs)
- [Python-Deriv-API Documentation](https://pypi.org/project/python-deriv-api/)

## Support

If you encounter any issues not covered in this guide, please check the project repository issues section or create a new issue with detailed information about your problem.