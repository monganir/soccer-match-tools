# ⚽ Soccer Game Management

A utility for managing soccer team logistics, including retrieving league schedules (e.g., YRSL), generating game sheets, and creating email communications for team rosters.

This tool uses Selenium to log in to league websites, scrape and parse schedules, and automate match-day preparation for coaches, managers, and referees.

---

## 🚀 Features

- 🔍 Fetches team schedules from the league website
- 📨 Generates HTML email summaries for upcoming matches
- 📄 Automates login and game sheet generation per team
- 🔒 Uses encrypted credentials for secure access
- 💼 Supports multiple teams and divisions via config files

---

## 🧰 Requirements

- Python 3.7+
- Google Chrome installed
- ChromeDriver (automatically managed via `webdriver_manager`)

Install dependencies:


pip install -r requirements.txt

## Setup Secrets

In order to generate game sheets you will need to setup your local secrets to login to yrsl team manager site. Open file `generate_secret.py` and modify the teams dictionary with your login and password information for each team. Run the python script and two files will be created within your local directory. 

```bash
python generate_secret.py
```

You now have the encrypted configuration set.

# Setup your team configuration file
Create a new team config file from a copy of `team-config.sample.json` and fill out the missing pieces of information.

# Creating a Roster File
A roster file is required when running the tool in mode generate-email or generate-gamesheet. Create a new roster file from a copy of the `roster-example.sample.json` file and fill out of the names of the team members. Goal keepers should be denoted by a suffix GK.

> ⚠️ **IMPORTANT:** The names of the players must match what has been entered within the YRSL website team management page (https://yorkregionsl.com/team-management/?pg=gs).


## 🧰 Run the tool


| Flag              | Required? | Accepted Values                                              | Description                                                                     |
| ----------------- | --------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| `--mode` / `-m`   | ✅         | `generate-game-list`, `generate-email`, `generate-gamesheet` | Operation mode (controls what the tool does)                                    |
| `--config` / `-c` | ✅         | Path to JSON file                                            | Team configuration file (includes divisions, teams, contacts, uniforms)         |
| `--roster` / `-r` | ✅\*       | Path to JSON file                                            | Player roster per team (required for `generate-email` and `generate-gamesheet`) |

| Mode                 | Description                                                                  |
| -------------------- | ---------------------------------------------------------------------------- |
| `generate-game-list` | Fetches upcoming games from the league schedule for all teams in the config. |
| `generate-email`     | Generates an HTML email with game schedules and player rosters.              |
| `generate-gamesheet` | Logs into each team’s account and opens the official gamesheet page.         |

Run the script with the required mode and configuration:

```bash
python game-generator.py --mode MODE --config CONFIG_PATH [--roster ROSTER_PATH]

```
## 📌 Example Commands
```bash
# Generate a game list for all teams
python game-generator.py --mode generate-game-list --config team_config.json

# Generate an HTML email with game info and rosters
python game-generator.py --mode generate-email --config team_config.json --roster roster.json

# Generate gamesheets (requires encrypted credentials and secret.key)
python game-generator.py --mode generate-gamesheet --config team_config.json --roster roster.json
```
