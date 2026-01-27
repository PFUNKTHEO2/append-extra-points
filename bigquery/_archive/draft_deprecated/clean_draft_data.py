#!/usr/bin/env python3
"""
Junior Hockey Draft Data Cleaner
Consolidates and cleans junior hockey draft data from multiple leagues and formats
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def clean_ushl_data(df, phase, year='2025'):
    """Clean USHL Phase I and II data (structured format)"""
    print(f"Cleaning USHL {phase} data...")
    
    # Define column names
    columns = ['round', 'pick', 'team', 'player', 'height', 'weight', 'birth_date', 'position', 'location', 'previous_team']
    
    # Assign column names
    df.columns = columns[:len(df.columns)]
    
    # Remove rows where player is 'Tender' or empty
    df = df[~df['player'].isin(['Tender', '']) & df['player'].notna()]
    
    # Remove rows that contain trade information (e.g., "from Omaha")
    df = df[~df['team'].str.contains('from ', na=False)]
    
    # Clean birth dates
    df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Add identifiers
    df['league'] = 'USHL'
    df['draft_year'] = year
    df['phase'] = phase
    
    # Clean height format (convert to inches if needed)
    df['height_inches'] = df['height'].apply(convert_height_to_inches)
    
    return df

def clean_ohl_data(df, year='2025'):
    """Clean OHL draft data (pick#, team, player(position) format)"""
    print("Cleaning OHL data...")
    
    # Filter rows that start with #
    df = df[df.iloc[:, 0].astype(str).str.contains('#', na=False)]
    
    cleaned_data = []
    for _, row in df.iterrows():
        pick_str = str(row.iloc[0]).replace('#', '')
        try:
            pick = int(pick_str)
            round_num = ((pick - 1) // 30) + 1  # Assuming 30 picks per round
        except:
            continue
            
        team = str(row.iloc[2]) if len(row) > 2 else ''
        player_with_pos = str(row.iloc[3]) if len(row) > 3 else ''
        
        # Extract position from parentheses
        position_match = re.search(r'\(([^)]+)\)$', player_with_pos)
        position = position_match.group(1) if position_match else ''
        player = re.sub(r'\s*\([^)]+\)$', '', player_with_pos).strip()
        
        cleaned_data.append({
            'round': round_num,
            'pick': pick,
            'team': team,
            'player': player,
            'position': position,
            'league': 'OHL',
            'draft_year': year
        })
    
    return pd.DataFrame(cleaned_data)

def clean_single_column_data(df, league, year='2025'):
    """Clean QMJHL/WHL single column format data"""
    print(f"Cleaning {league} data...")
    
    # Get all non-empty values from first column
    data = df.iloc[:, 0].dropna().astype(str).tolist()
    data = [item for item in data if item.strip() != '']
    
    cleaned_data = []
    i = 0
    
    while i < len(data):
        try:
            # Look for round number (should be 1-15)
            if data[i].isdigit() and 1 <= int(data[i]) <= 15:
                round_num = int(data[i])
                i += 1
                
                # Next should be pick number
                if i < len(data) and data[i].isdigit():
                    pick = int(data[i])
                    i += 1
                    
                    # Next should be team name
                    team = ''
                    if i < len(data):
                        team = data[i]
                        i += 1
                        
                        # Skip trade info lines
                        if i < len(data) and 'from ' in data[i].lower():
                            i += 1
                    
                    # Next should be player name (Last, First format usually)
                    player = ''
                    if i < len(data):
                        player = data[i]
                        i += 1
                    
                    # Next should be position
                    position = ''
                    if i < len(data):
                        position = data[i]
                        i += 1
                    
                    # Next might be height
                    height = ''
                    if i < len(data) and (data[i].replace('.', '').replace("'", '').replace('"', '').replace(' ', '').isdigit() or 
                                        re.match(r'^\d+\.\d+$', data[i]) or re.match(r'^\d+\'\d+\"?$', data[i])):
                        height = data[i]
                        i += 1
                    
                    # Next might be weight
                    weight = ''
                    if i < len(data) and data[i].isdigit():
                        weight = int(data[i])
                        i += 1
                    
                    # Next might be location
                    location = ''
                    if i < len(data) and not data[i].isdigit():
                        location = data[i]
                        i += 1
                    
                    # Next might be previous team
                    previous_team = ''
                    if i < len(data) and not data[i].isdigit():
                        previous_team = data[i]
                        i += 1
                    
                    # Only add if we have essential info
                    if player and team:
                        cleaned_data.append({
                            'round': round_num,
                            'pick': pick,
                            'team': team,
                            'player': player,
                            'position': position,
                            'height': height,
                            'weight': weight,
                            'location': location,
                            'previous_team': previous_team,
                            'league': league,
                            'draft_year': year
                        })
                else:
                    i += 1
            else:
                i += 1
                
        except Exception as e:
            i += 1
            continue
    
    return pd.DataFrame(cleaned_data)

def convert_height_to_inches(height_str):
    """Convert various height formats to inches"""
    if pd.isna(height_str) or height_str == '':
        return None
    
    height_str = str(height_str).strip()
    
    # Handle feet'inches" format
    if "'" in height_str or '"' in height_str:
        try:
            feet_inches = re.findall(r'\d+', height_str)
            if len(feet_inches) >= 2:
                return int(feet_inches[0]) * 12 + int(feet_inches[1])
            elif len(feet_inches) == 1:
                return int(feet_inches[0]) * 12
        except:
            pass
    
    # Handle decimal format (assume feet.inches)
    if '.' in height_str:
        try:
            parts = height_str.split('.')
            feet = int(parts[0])
            inches = int(parts[1]) if len(parts[1]) <= 2 else int(parts[1][:2])
            return feet * 12 + inches
        except:
            pass
    
    # Handle just inches
    try:
        return int(float(height_str))
    except:
        return None

def standardize_columns(df):
    """Standardize column names and add missing columns"""
    standard_columns = [
        'round', 'pick', 'team', 'player', 'position', 'height', 'weight', 
        'birth_date', 'location', 'previous_team', 'league', 'draft_year', 'phase'
    ]
    
    # Add missing columns
    for col in standard_columns:
        if col not in df.columns:
            df[col] = ''
    
    # Reorder columns
    df = df[standard_columns]
    
    return df

def main():
    """Main function to clean all junior hockey draft data"""
    print("=== Junior Hockey Draft Data Cleaner ===\n")
    
    # Read the Excel file
    file_path = "Junior League Draft Results.xlsx"
    
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"Found {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}\n")
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}")
        print("Please make sure the Excel file is in the same directory as this script.")
        return
    
    all_data = []
    
    # Clean each sheet
    for sheet_name in excel_file.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            if sheet_name == "USHL Draft  Phase I 2025":
                cleaned_df = clean_ushl_data(df, "Phase I", "2025")
            elif sheet_name == "USHL Draft  Phase II 2025":
                cleaned_df = clean_ushl_data(df, "Phase II", "2025")
            elif sheet_name == "OHL Draft":
                cleaned_df = clean_ohl_data(df, "2025")
            elif sheet_name == "QMJHL Draft 20251":
                cleaned_df = clean_single_column_data(df, "QMJHL", "2025")
            elif sheet_name == "QMJHL 2024":
                cleaned_df = clean_single_column_data(df, "QMJHL", "2024")
            elif sheet_name == "WHL Draft 2025":
                cleaned_df = clean_single_column_data(df, "WHL", "2025")
            elif sheet_name == "WHL Draft US 2025":
                cleaned_df = clean_single_column_data(df, "WHL-US", "2025")
            elif sheet_name == "League Tiers":
                print("Skipping League Tiers sheet (reference only)")
                continue
            else:
                print(f"Unknown sheet format: {sheet_name}")
                continue
            
            if not cleaned_df.empty:
                cleaned_df = standardize_columns(cleaned_df)
                all_data.append(cleaned_df)
                print(f"✓ Processed {len(cleaned_df)} records from {sheet_name}")
            else:
                print(f"⚠ No data extracted from {sheet_name}")
                
        except Exception as e:
            print(f"✗ Error processing {sheet_name}: {str(e)}")
        
        print()
    
    # Combine all data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Final cleaning
        combined_df = combined_df[combined_df['player'].str.strip() != '']
        combined_df = combined_df.sort_values(['league', 'draft_year', 'round', 'pick'])
        
        # Save to CSV
        output_file = "junior_hockey_draft_consolidated.csv"
        combined_df.to_csv(output_file, index=False)
        
        print("=== CLEANING COMPLETE ===")
        print(f"Total records processed: {len(combined_df)}")
        print(f"Output saved to: {output_file}")
        
        # Print summary by league
        print("\nSummary by League:")
        summary = combined_df.groupby(['league', 'draft_year']).size().reset_index(name='count')
        for _, row in summary.iterrows():
            print(f"  {row['league']} {row['draft_year']}: {row['count']} players")
        
        # Show sample of cleaned data
        print("\nSample of cleaned data:")
        print(combined_df[['league', 'draft_year', 'round', 'pick', 'team', 'player', 'position']].head(10))
        
    else:
        print("No data was successfully processed.")

if __name__ == "__main__":
    main()