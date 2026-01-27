# Quick fix for the null draft_league issue
# Replace the _process_draft_data method in your script with this version:

def _process_draft_data(self, df, draft_league_name):
    """Process draft data and match players"""
    
    logger.info(f"Processing {len(df)} {draft_league_name} draft records")
    
    # Create standardized dataframe
    processed_df = pd.DataFrame()
    
    # Map columns from CSV to BigQuery schema - ENSURE NO NULLS
    processed_df['draft_league'] = draft_league_name  # This should never be null since we pass it in
    processed_df['draft_year'] = pd.to_numeric(df['Draft Year'], errors='coerce').fillna(0).astype(int)
    processed_df['draft_round'] = pd.to_numeric(df['Round'], errors='coerce').fillna(0).astype(int)
    processed_df['overall_pick'] = pd.to_numeric(df['Pick'], errors='coerce').fillna(0).astype(int)
    processed_df['team_name'] = df['Team'].fillna('').astype(str)  # Ensure string type
    processed_df['player_name'] = df['Player Name'].fillna('').astype(str)  # Ensure string type
    
    # Extract position from player name if it exists (like "John Doe (F)")
    processed_df['player_position'] = df['Player Name'].apply(
        lambda x: re.search(r'\(([FCDLRG])\)', str(x)).group(1) 
        if pd.notna(x) and re.search(r'\(([FCDLRG])\)', str(x)) else None
    )
    
    # Clean player names (remove position info)
    processed_df['player_name'] = processed_df['player_name'].apply(
        lambda x: re.sub(r'\s*\([FCDLRG]\)', '', str(x)) if pd.notna(x) else ''
    )
    
    # Set selection_made flag
    processed_df['selection_made'] = ~processed_df['player_name'].str.contains(
        'No selection was made', case=False, na=False
    )
    
    # CRITICAL FIX: Ensure draft_league is never null
    processed_df['draft_league'] = processed_df['draft_league'].fillna(draft_league_name)
    
    # Double-check no nulls in required fields
    processed_df['draft_league'] = processed_df['draft_league'].astype(str)
    processed_df['team_name'] = processed_df['team_name'].astype(str)
    
    # Match players to IDs
    logger.info(f"Matching {draft_league_name} players to existing IDs...")
    processed_df['player_id'] = processed_df.apply(
        lambda row: self._match_player_id(
            row['player_name'] if row['selection_made'] else None,
            None,
            row['player_position']
        ), axis=1
    )
    
    # Add missing required columns
    processed_df['team_id'] = None
    processed_df['draft_date'] = None
    processed_df['created_at'] = datetime.utcnow()
    processed_df['updated_at'] = datetime.utcnow()
    
    # Final validation - ensure no nulls in required fields
    if processed_df['draft_league'].isnull().any():
        logger.error("Found null values in draft_league after processing!")
        processed_df['draft_league'] = processed_df['draft_league'].fillna(draft_league_name)
    
    # Log matching results
    total_picks = len(processed_df)
    actual_selections = processed_df['selection_made'].sum()
    matched_players = processed_df['player_id'].notna().sum()
    
    logger.info(f"{draft_league_name} processing results:")
    logger.info(f"  Total picks: {total_picks}")
    logger.info(f"  Actual selections: {actual_selections}")
    logger.info(f"  Players matched: {matched_players}/{actual_selections} ({matched_players/actual_selections*100:.1f}%)")
    
    return processed_df