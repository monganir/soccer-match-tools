from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os
import sys
import json
import argparse
from cryptography.fernet import Fernet
from tabulate import tabulate
from datetime import datetime




def format_date_with_day(date_str):
    # Use current year for parsing
    current_year = datetime.now().year
    full_date_str = f"{date_str} {current_year}"

    try:
        # Parse the full date
        date_obj = datetime.strptime(full_date_str, "%b %d %Y")
        
        # Format: "Wednesday, Sep 18"
        formatted_date = date_obj.strftime("%A, %b %d")
        return formatted_date

    except ValueError:
        return "Invalid date format. Use 'Sep 18' format."
    
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def login(driver, email, password):
    driver.get("https://yorkregionsl.com/team-management/")
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.presence_of_element_located((By.ID, "eml")))
    password_input = driver.find_element(By.ID, "pwd")
    email_input.send_keys(email)
    password_input.send_keys(password)
    driver.find_element(By.CLASS_NAME, "e2e-button").click()
    time.sleep(3)

def select_roster(driver, players):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.form-check")))
    
    player_set = set(
    name.rsplit(" ", 1)[0].strip().lower()
    if name.strip().endswith(" GK") else name.strip().lower()
    for name in players
    )
    
    found_players = set()

    for div in driver.find_elements(By.CSS_SELECTOR, "div.form-check"):
        label = div.find_element(By.TAG_NAME, "label").text.strip().lower()
        if label in player_set:
            found_players.add(label)
            checkbox = div.find_element(By.TAG_NAME, "input")
            if not checkbox.is_selected():
                driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                time.sleep(0.5)
                checkbox.click()
                
                

    missing = player_set - found_players
    if missing:
        raise ValueError(f"❌ Players NOT found on the page: {', '.join(missing)}")
   

def generate_gamesheet(driver):
    wait = WebDriverWait(driver, 10)
    generate_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
    
    # Try standard click first
    try:
        # Scroll the element into view using JavaScript + offsets
        driver.execute_script("""
            arguments[0].scrollIntoView({block: 'center', inline: 'center'});
            window.scrollBy(0, -150); // adjust scroll to account for sticky headers
        """, generate_btn)
        time.sleep(0.5)  # Give time for scroll animation/rendering

        generate_btn.click()
    except Exception as e:
        print(f"⚠️ Standard click failed: {e}")
        print("✅ Retrying using JavaScript click.")
        driver.execute_script("arguments[0].click();", generate_btn)

    print("📄 Gamesheet opened in new tab. Please download manually.")


def generate_schedule_email_html_with_subject(games_list, rosters):
    team_order = list(team_config["team_info"].keys())

    def get_team_code(team_name):
        for code in team_order:
            if code in team_name:
                return code
        return None

    games_by_team = {}
    game_dates = set()
    for game in games_list:
        if "Vaughan" in game['Home']:
            code = get_team_code(game['Home'])
        else:
            code = get_team_code(game['Away'])
        if code:
            games_by_team[code] = game
            game_dates.add(game['Date'])

    sorted_date_str = date_str = ", ".join(sorted(game_dates))
    subject = f"Vaughan SC U9 Boys Game ({sorted_date_str})"

    email = []

     # Coaches
    coaches = team_config["email_contacts"].get("coaches", [])
    coach_text = " or ".join(
        f"{coach['name']} at <a href='mailto:{coach['email']}'>{coach['email']}</a>"
        for coach in coaches
    )

    # Managers
    managers = team_config["email_contacts"].get("managers", [])
    manager_text = " and ".join(
        f"<a href='mailto:{mgr['email']}'>{mgr['email']}</a>"
        for mgr in managers
    )

    email.append(
    f"<p>Please note the rosters for this week's games below. If you are unable to attend, "
    f"please email {coach_text} or you can contact your team managers {manager_text}.</p>"
)
    email.append("<p><b>Arrival Time:</b> Players should be at the field 30 minutes prior to kick-off and bring both sets of jerseys (White and Navy).</p>")

    email.append("<p>Typically the kids will be asked to wear the following depending on if we are the Home or Away Team:</p>")

    email.append("<p><b>Home:</b> " + team_config["uniforms"]["home"] + "<br>")
    email.append("<b>Away:</b> " + team_config["uniforms"]["away"] + "</p>")

    for code in ['T1', 'T2', 'T3', 'T4']:
        game = games_by_team.get(code)
        if not game:
            continue
        roster = rosters.get(code, [])

        email.append(f"<h3 style='text-decoration: underline;'><b>{code} Game and Location</b></h3>")

        email.append("<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
                     "<tr><th>Date</th><th>KO</th><th>Field</th><th>Home</th><th>Away</th></tr>")
        email.append(f"<tr><td>{format_date_with_day(game['Date'])}</td><td>{game['Time']}</td><td><a href='{game['FieldLink']}' target='_blank'>{game['Field']}</a></td><td>{game['Home']}</td><td>{game['Away']}</td></tr>")
        email.append("</table><br>")

        email.append(f"<h4>{code} Roster</h4>")
        email.append("<ul>")
        for player in roster:
            email.append(f"<li>{player}</li>")
        email.append("</ul><br>")

    return subject, "".join(email)



def get_yrsl_games(division,team,filter):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://yorkregionsl.com/schedule/")
    time.sleep(0.5)  # Wait for full page load

    # Select the division
    select_div = Select(driver.find_element("id", "e2e-divisionid"))
    select_div.select_by_visible_text(division)
    time.sleep(0.5)  # Wait for JS schedule refresh

    # Select the team
    select_team = Select(driver.find_element("id", "e2e-teamid"))
    select_team.select_by_visible_text(team)
    time.sleep(0.5)  # Wait for schedule refresh

    # Select Filter "This Week"
    select_filter = Select(driver.find_element("id", "e2e-filter"))
    select_filter.select_by_visible_text(filter)
    time.sleep(0.5)

    # Parse updated HTML with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Find the table with class "e2e-table"
    table = soup.find('table', class_='e2e-table')
    schedule = []

    for row in table.find_all('tr')[1:]:  # Skip header row
        tds = row.find_all('td')
        if len(tds) >= 8:
            # Field is at index 5, get text and href if available
            field_td = tds[5]
            field_name = field_td.get_text(strip=True)
            field_link_tag = field_td.find('a')
            field_link = field_link_tag['href'] if field_link_tag else None

            schedule.append({
                'Date': tds[3].get_text(strip=True),
                'Time': tds[4].get_text(strip=True),
                'Field': field_name,
                'FieldLink': field_link,
                'Home': tds[6].get_text(strip=True),
                'Away': tds[7].get_text(strip=True),
            })
    return schedule

#Check arguments
parser = argparse.ArgumentParser(description="Help msg",    
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-m','--mode', choices=['generate-email', 'generate-gamesheet', 'generate-game-list'], required=True, help='Operation mode')

parser.add_argument("-r", "--roster", help="roster json file location")

parser.add_argument("-c", "--config", required=True, help="Team configuration file")

args = parser.parse_args()

if ((args.mode == 'generate-email' or args.mode == 'generate-gamesheet') and not args.roster):
    parser.error("--roster is required when --mode is 'generate-email' or 'generate-gamesheet'")

if not os.path.isfile(args.config):
        print(f"Error: The file '{args.config}' does not exist.")
        sys.exit(1)

with open(args.config, "r") as f:
    team_config = json.load(f)

if args.roster:
    if not os.path.isfile(args.roster):
        print(f"Error: The file '{args.roster}' does not exist.")
        sys.exit(1)

    try:
        with open(args.roster, 'r') as f:
            rosters = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file.\n{e}")
        sys.exit(1)

    print("Roster loaded successfully.")

    print(json.dumps(rosters, indent=4, sort_keys=True))


if args.mode == 'generate-game-list' or args.mode == 'generate-email':

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")

    games_list = []

    for team_code, info in team_config["team_info"].items():
        games_list += get_yrsl_games(
            division=info["division"],
            team=info["team"],
            filter=team_config["filter"]
    )

if args.mode == 'generate-game-list':
    # Prepare rows with link text
    output = "📅 *Match Schedule*\n\n"
    for game in games_list:
        output += (
            f"*Date:* {game['Date']}\n"
            f"*Time:* {game['Time']}\n"
            f"*Field:* {game['Field']}\n"
            f"*Map:* {game['FieldLink']}\n"
            f"*Home:* {game['Home']}\n"
            f"*Away:* {game['Away']}\n"
            f"{'-'*30}\n"
        )

    print(output)


if args.mode == 'generate-email':

    subject, html_body = generate_schedule_email_html_with_subject(games_list, rosters)
    
    print("Subject:", subject)
    print("HTML body:\n", html_body)
    


if args.mode == 'generate-gamesheet':

    # Load secret key
    with open("secret.key", "rb") as f:
        key = f.read()

    fernet = Fernet(key)

    # Load encrypted config
    with open("secure_config.json") as f:
        encrypted_config = json.load(f)

    # Decrypt passwords into credentials
    team_credentials = {}
    for team, data in encrypted_config.items():
        decrypted_password = fernet.decrypt(data["password"].encode()).decode()
        team_credentials[team] = {
            "email": data["email"],
            "password": decrypted_password
        }

    # Main loop
    for team, players in rosters.items():
        if not players:
            print(f"⚠️ Skipping {team}: no players.")
            continue
                
        creds = team_credentials.get(team)
        if not creds:
            print(f"⚠️ Skipping {team}: no credentials.")
            continue

        email = creds["email"]
        password = creds["password"]

        print(f"\n=== Processing {team} ===")
        driver = create_driver()
        
        try:
            login(driver, email, password)
            if players:
                select_roster(driver, players)
            generate_gamesheet(driver)
            input(f"⏸️  {team}: Press Enter after you download the gamesheet...")
        except Exception as e:
            print(f"❌ Error processing {team}: {e}")
        finally:
            driver.quit()












    








