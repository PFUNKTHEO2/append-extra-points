"""
NEPSAC Roster Scraper
=====================
Scrapes remaining team rosters from Neutral Zone website using Selenium.
"""

import os
import csv
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Team URLs - remaining teams to scrape
TEAM_URLS = {
    "Holderness": "https://neutralzone.com/prep-boys/team/holderness-66",
    "Hotchkiss School": "https://neutralzone.com/prep-boys/team/hotchkiss-school-34",
    "Kents Hill": "https://neutralzone.com/prep-boys/team/kents-hill-68",
    "Loomis Chaffee": "https://neutralzone.com/prep-boys/team/loomis-chaffee-35",
    "Middlesex": "https://neutralzone.com/prep-boys/team/middlesex-15",
    "Millbrook": "https://neutralzone.com/prep-boys/team/millbrook-50",
    "Milton Academy": "https://neutralzone.com/prep-boys/team/milton-academy-57",
    "Moses Brown": "https://neutralzone.com/prep-boys/team/moses-brown-27",
    "Mount St. Charles": "https://neutralzone.com/prep-boys/team/mount-st.-charles-155",
    "New Hampton": "https://neutralzone.com/prep-boys/team/new-hampton-67",
    "Nichols": "https://neutralzone.com/prep-boys/team/nichols-11",
    "NMH": "https://neutralzone.com/prep-boys/team/nmh-41",
    "Noble & Greenough": "https://neutralzone.com/prep-boys/team/noble-&-greenough-62",
    "Northwood School": "https://neutralzone.com/prep-boys/team/northwood-school-139",
    "North Yarmouth": "https://neutralzone.com/prep-boys/team/north-yarmouth-52",
    "Pingree": "https://neutralzone.com/prep-boys/team/pingree-20",
    "Pomfret": "https://neutralzone.com/prep-boys/team/pomfret-45",
    "Portsmouth Abbey": "https://neutralzone.com/prep-boys/team/portsmouth-abbey-28",
    "Princeton Day School": "https://neutralzone.com/prep-boys/team/princeton-day-school-10",
    "Proctor Academy": "https://neutralzone.com/prep-boys/team/proctor-academy-65",
    "Ridley College": "https://neutralzone.com/prep-boys/team/ridley-college-(on)-158",
    "Rivers School": "https://neutralzone.com/prep-boys/team/rivers-school-19",
    "Roxbury Latin": "https://neutralzone.com/prep-boys/team/roxbury-latin-21",
    "Salisbury School": "https://neutralzone.com/prep-boys/team/salisbury-school-47",
    "St. Andrews": "https://neutralzone.com/prep-boys/team/st.-andrews-9",
    "Stanstead College": "https://neutralzone.com/prep-boys/team/stanstead-college-12",
    "St. Georges": "https://neutralzone.com/prep-boys/team/st.-georges-29",
    "St. Marks": "https://neutralzone.com/prep-boys/team/st.-marks-18",
    "St. Paul's School": "https://neutralzone.com/prep-boys/team/st.-paul's-school-42",
    "St. Sebastian's": "https://neutralzone.com/prep-boys/team/st.-sebastian's-60",
    "Tabor": "https://neutralzone.com/prep-boys/team/tabor-59",
    "Taft": "https://neutralzone.com/prep-boys/team/taft-31",
    "Thayer Academy": "https://neutralzone.com/prep-boys/team/thayer-academy-61",
    "The Hill School": "https://neutralzone.com/prep-boys/team/the-hill-school-73",
    "Tilton": "https://neutralzone.com/prep-boys/team/tilton-69",
    "Trinity-Pawling": "https://neutralzone.com/prep-boys/team/trinity-pawling-74",
    "Vermont Academy": "https://neutralzone.com/prep-boys/team/vermont-academy-71",
    "Westminster": "https://neutralzone.com/prep-boys/team/westminster-32",
    "Wilbraham & Monson": "https://neutralzone.com/prep-boys/team/wilbraham-&-monson-168",
    "Williston-Northampton": "https://neutralzone.com/prep-boys/team/williston-northampton-43",
    "Winchendon": "https://neutralzone.com/prep-boys/team/winchendon-48",
    "Worcester Academy": "https://neutralzone.com/prep-boys/team/worcester-academy-54",
    "Wyoming Seminary": "https://neutralzone.com/prep-boys/team/wyoming-seminary-79"
}

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_ROSTER_FILE = os.path.join(OUTPUT_DIR, "nepsac_scraped_rosters.csv")
NEW_COACHES_FILE = os.path.join(OUTPUT_DIR, "nepsac_scraped_coaches.csv")


def log(message, level="INFO"):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")


def setup_driver():
    """Setup Selenium Chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def extract_coaches(soup, team_name):
    """Extract coach info from page."""
    coaches = []

    try:
        page_text = soup.get_text()

        # Find Head Coach section
        head_coach_match = re.search(r'Head Coach\s*\n\s*([^\n]+)', page_text)
        if head_coach_match:
            coach_name = head_coach_match.group(1).strip()

            # Find email near head coach
            email = ''
            email_links = soup.find_all('a', href=re.compile(r'mailto:'))
            for link in email_links:
                href = link.get('href', '')
                if '@' in href:
                    email = href.replace('mailto:', '').strip()
                    break

            # Find phone
            phone = ''
            phone_match = re.search(r'(\d{3}[-.]?\d{3}[-.]?\d{4})', page_text)
            if phone_match:
                phone = phone_match.group(1)

            coaches.append({
                'team': team_name,
                'role': 'Head Coach',
                'name': coach_name,
                'email': email,
                'phone': phone
            })

        # Find Assistant Coaches
        asst_match = re.search(r'Assistant Coach(?:es)?\s*\n(.+?)(?:School Information|$)', page_text, re.DOTALL)
        if asst_match:
            asst_section = asst_match.group(1)
            # Look for names and emails
            asst_emails = re.findall(r'([A-Za-z\s]+)\s*\n?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+)', asst_section)
            for name, email in asst_emails:
                name = name.strip()
                if name and len(name) > 2:
                    coaches.append({
                        'team': team_name,
                        'role': 'Assistant',
                        'name': name,
                        'email': email.strip(),
                        'phone': ''
                    })

    except Exception as e:
        log(f"Error extracting coaches for {team_name}: {e}", "WARN")

    return coaches


def extract_roster(soup, team_name):
    """Extract roster from page - look for table with 'No. Name Position Ht Wt'."""
    players = []

    try:
        tables = soup.find_all('table')

        # Find the right roster table
        roster_table = None
        for table in tables:
            headers = table.find_all('th')
            header_text = ' '.join([h.get_text().strip() for h in headers])

            # Look for table with No. Name Position Ht Wt
            if 'No.' in header_text and 'Name' in header_text and 'Position' in header_text:
                roster_table = table
                break

        if not roster_table:
            log(f"Could not find roster table for {team_name}", "WARN")
            return players

        # Map headers to indices
        headers = roster_table.find_all('th')
        header_map = {}
        for i, th in enumerate(headers):
            text = th.get_text().strip().lower()
            if text == 'no.' or text == '#':
                header_map['number'] = i
            elif text == 'name':
                header_map['name'] = i
            elif 'position' in text or text == 'pos':
                header_map['position'] = i
            elif text == 'ht' or 'height' in text:
                header_map['height'] = i
            elif text == 'wt' or 'weight' in text:
                header_map['weight'] = i
            elif text == 'shot':
                header_map['shot'] = i
            elif 'grad' in text:
                header_map['grad_year'] = i
            elif 'hometown' in text:
                header_map['hometown'] = i
            elif 'dob' in text or 'birth' in text:
                header_map['dob'] = i

        # Extract rows
        rows = roster_table.find_all('tr')[1:]
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            player = {
                'team': team_name,
                'number': '',
                'name': '',
                'position': '',
                'height': '',
                'weight': '',
                'shot': '',
                'grad_year': '',
                'hometown': '',
                'dob': ''
            }

            for field, idx in header_map.items():
                if idx < len(cells):
                    value = cells[idx].get_text().strip()
                    player[field] = value

            if player['name']:
                players.append(player)

    except Exception as e:
        log(f"Error extracting roster for {team_name}: {e}", "ERROR")

    return players


def scrape_team(driver, team_name, url):
    """Scrape a single team."""
    try:
        driver.get(url)
        time.sleep(2)  # Let page render

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract roster
        players = extract_roster(soup, team_name)

        # Extract coaches
        coaches = extract_coaches(soup, team_name)

        log(f"{team_name}: {len(players)} players, {len(coaches)} coaches")

        return players, coaches

    except Exception as e:
        log(f"Error scraping {team_name}: {e}", "ERROR")
        return [], []


def main():
    print("=" * 60)
    print("NEPSAC ROSTER SCRAPER")
    print("=" * 60)

    driver = setup_driver()
    all_players = []
    all_coaches = []

    try:
        total = len(TEAM_URLS)
        for i, (team_name, url) in enumerate(TEAM_URLS.items(), 1):
            log(f"Scraping {team_name}... ({i}/{total})")

            players, coaches = scrape_team(driver, team_name, url)
            all_players.extend(players)
            all_coaches.extend(coaches)

            # Rate limiting
            time.sleep(0.75)

        # Save rosters
        log(f"Saving {len(all_players)} players to {NEW_ROSTER_FILE}")
        with open(NEW_ROSTER_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'team', 'number', 'name', 'position', 'height', 'weight',
                'shot', 'grad_year', 'hometown', 'dob'
            ])
            writer.writeheader()
            writer.writerows(all_players)

        # Save coaches
        log(f"Saving {len(all_coaches)} coaches to {NEW_COACHES_FILE}")
        with open(NEW_COACHES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'team', 'role', 'name', 'email', 'phone'
            ])
            writer.writeheader()
            writer.writerows(all_coaches)

        print("\n" + "=" * 60)
        print("SCRAPING COMPLETE!")
        print(f"  Total players: {len(all_players)}")
        print(f"  Total coaches: {len(all_coaches)}")
        print("=" * 60)

    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
