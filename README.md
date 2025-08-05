# Project Chimera: An Advanced AI Agent Simulation Environment

## Overview

Project Chimera is a sophisticated simulation environment designed to study the behavior of autonomous AI agents in a collaborative software development setting. The primary focus of this project is to develop and test advanced AI safety and oversight mechanisms, specifically the "Hierarchical Monitor Agent," which is tasked with detecting and mitigating malicious activities (sabotage) from other AI agents.

This environment facilitates an "arms race" between saboteur agents attempting to introduce bugs and vulnerabilities, and a multi-layered monitoring system designed to identify and neutralize these threats. The simulation is built to be highly configurable, allowing for the exploration of various scenarios and deception techniques.

## Key Features

*   **Realistic Multi-Agent Simulation:** Simulates a team of AI agents working on software development tasks.
*   **Diverse Agent Types:**
    *   **Collaborative Agents:** Honest agents that work towards completing tasks correctly.
    *   **Stealth Saboteur Agents:** Malicious agents that attempt to introduce subtle bugs and vulnerabilities.
    *   **Coordination Saboteur Agents:** Multiple malicious agents that coordinate their sabotage efforts to be more effective and harder to detect.
*   **Hierarchical Monitoring System (TAO - Tiered Agentic Oversight):** A sophisticated, multi-layered monitoring system designed to detect malicious behavior.
    *   **Tier 1 Monitors:** Perform initial analysis of agent behavior.
    *   **Tier 2 Supervisor:** Aggregates signals from Tier 1 monitors to identify more complex threat patterns.
*   **Adversarial "Arms Race" Scenarios:** The environment is designed to test the limits of the monitoring system by providing saboteur agents with knowledge of the monitor's detection strategies, allowing them to evolve their evasion tactics.
*   **Configurable Scenarios:** Easily define and run different simulation scenarios to test various hypotheses.
*   **Detailed Logging and Analysis:** The simulation generates detailed logs and forensic data for in-depth analysis of agent behavior and monitor performance.

## Getting Started

### Prerequisites

*   Python 3.9+
*   Docker and Docker Compose (for running certain models or environments)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd project_chimera
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Simulation

The main simulation script is `run_hierarchical_simulation.py`. You can run a simulation with the following command:

```bash
python3 run_hierarchical_simulation.py --steps <number_of_steps> --scenario "<scenario_name>"
```

**Example:**

```bash
python3 run_hierarchical_simulation.py --steps 20 --scenario 'Refactor and add sabotage with evasion'
```

## Project Structure

```
.
├── README.md                   # This file
├── Research_Summary.md         # Summary of research findings
├── analysis/                   # Scripts for analyzing simulation data
├── configs/                    # Configuration files for simulations and models
├── docker/                     # Docker-related files
├── docker-compose.yml          # Docker Compose configuration
├── example_project/            # An example project that the agents might work on
├── pyproject.toml              # Project metadata and dependencies
├── run_hierarchical_simulation.py # Main script to run the hierarchical simulation
├── run_simulation.py           # A simpler simulation script
├── scripts/                    # Helper scripts
├── src/                        # Source code for agents, the monitor, and the simulation engine
├── test_api_keys.py            # Script for testing API key setups
├── test_enhanced_monitor.py    # Tests for the enhanced monitor
├── test_hierarchical_monitor.py # Tests for the hierarchical monitor
└── venv/                       # Virtual environment
```

## How it Works

The simulation proceeds in discrete steps. In each step, every agent (collaborative and saboteur) is given a task to work on. The agents generate "thoughts" about how they will approach the task, and then "actions" that represent their work.

The Hierarchical Monitor Agent observes the thoughts and actions of all other agents. It uses a multi-tiered approach to analyze this data for signs of malicious intent, deception, and coordinated sabotage.

### The Agents

*   **`CollaborativeAgent`:** A baseline agent that performs tasks honestly and to the best of its ability.
*   **`StealthSaboteurAgent`:** A misaligned agent that tries to introduce subtle bugs. It is designed to be difficult to detect.
*   **`CoordinationSaboteurAgent`:** A more advanced misaligned agent that can coordinate with other saboteurs to carry out more complex attacks.

### The Hierarchical Monitor

The monitor is the core of the AI safety research in this project. It is composed of multiple layers:

1.  **Enhanced Monitor (Tier 1):** This is the first line of defense. It analyzes the "thought" processes of each agent to detect suspicious reasoning.
2.  **Hierarchical Supervisor (Tier 2):** This layer aggregates the outputs of the Tier 1 monitors. It looks for patterns of suspicious behavior over time and across multiple agents to detect coordinated attacks and more subtle threats.

The monitor's effectiveness is tested by running simulations with and without "evasion" tactics enabled for the saboteur agents.

## Contributing

Contributions are welcome! If you have ideas for new features, scenarios, or improvements to the monitoring system, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
