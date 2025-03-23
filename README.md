# PFM-Hackathon

This repository contains a multi-agent application designed to provide financial advisory services through specialized agents. The system uses synthetic data and a collection of prompt files to support various financial planning and analysis tasks.

## Table of Contents
- [PFM-Hackathon](#pfm-hackathon)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Directory Structure](#directory-structure)
  - [Set Up Enenvironment](#set-up-enenvironment)
  - [Usage](#usage)

## Overview

This application leverages multiple agents, each specialized in a particular area of financial advisory:
- **Asset Allocation Agent**: Helps manage and optimize asset distributions.
- **Education Agent**: Provides educational content and guidance.
- **Financial Advisor Agent**: Offers overall financial planning recommendations (Orchestration agent).
- **Goal Planning Agent**: Assists in setting and planning financial goals.
- **Transaction Analysis Agent**: Analyzes transactions to provide insights.

The agents are supported by dedicated prompt files to guide their interactions, and the system uses synthetic data for testing and demonstration purposes.

## Features

- **Modular Agent Design**: Each agent is implemented as a separate module, allowing for easy expansion and maintenance.
- **Prompt Driven Interaction**: Custom prompt files for each agent help define their behavior and responses.
- **Synthetic Data**: Includes CSV files for asset allocation, budget, financial goals, risk profiles, and more for simulation and testing.
- **Utility Functions**: Contains several utilities for context management, goal data management, and handling LLM responses.
- **Main Application**: The `app.py` file ties together the various components for seamless execution.

## Directory Structure

```plaintext
.
├── app.py                         # Main application entry point
├── financial_data_generator.py    # Initiallize synthetic data                  
├── requirements.txt               # Python dependencies
├── agents/                        # Agent modules
│   ├── asset_allocation_agent.py
│   ├── education_agent.py
│   ├── financial_advisor_agent.py
│   ├── goal_planning_agent.py
│   ├── transaction_analysis_agent.py
│   └── __init__.py
├── prompts/                       # Prompt definitions for agents
│   ├── asset_allocation_agent_prompts.py
│   ├── education_agent_prompts.py
│   ├── financial_advisor_agent_prompts.py
│   ├── goal_planning_agent_prompts.py
│   └── transaction_agent_prompts.py
├── synthetic_data/                # Synthetic CSV data files
│   ├── asset_allocation_matrix.csv
│   ├── budget_data.csv
│   ├── current_asset_allocation.csv
│   ├── enhanced_goal_data.csv
│   ├── expanded_risk_profiles.csv
│   ├── financial_goals_data.csv
│   ├── goal_specific_allocations.csv
│   ├── subscription_data.csv
│   ├── transactions_data.csv
│   └── user_profile_data.csv
└── utils/                         # Utility modules
    ├── context_management.py
    ├── goal_data_manager.py
    ├── llm_response.py
    └── __init__.py
```

## Set Up Enenvironment

- **Clone Git Repo**
  
  git clone <repository_url>
  
  cd <repository_directory>


- **Create Virtual Env**:
  
  python -m venv venv
  
  source venv/bin/activate  # On Windows: venv\Scripts\activate

- **Install Requirements**:
  
  pip install -r requirements.txt

- **Set Up .ENV File**
  
  Create .env file in your project directory and add following lines

  DEKA_LLM_API_URL=https://dekallm.cloudeka.ai/v1/chat/completions
  DEKA_LLM_API_KEY=<Your_DEKA_LLM_API_KEY>
  DEKA_LLM_MODEL_NAME=meta/llama-3.3-70b-instruct
  DEKA_EMBEDDING_API_URL=https://dekallm.cloudeka.ai/v1/embeddings
  DEKA_EMBEDDING_MODEL_NAME=baai/bge-multilingual-gemma2

- **Initiallize Synthetic Data**:
  
  create synthetic_data directory in your project folder and then run following command.

  python financial_data_generator.py

## Usage

  Run the main application with:

  python app.py
