#!/usr/bin/env python3
"""
Draft Data Upsert Script - Corrected Version
Processes Canadian and USHL draft data with proper column mapping
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DraftDataProcessor:
    def __init__(self, project_id: str = "sterling-edge-advisors"):
        """Initialize the processor with BigQuery client"""
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = "hockey"
        self.table_id = "all_drafts"
        self.players_table_id = "players"
        
        # Load existing players for matching
        self.players_df = self._load_players()
        
    def _load_players(self):
        """Load players table for ID matching"""
        query = f"""
        SELECT 
            id as player_id,
            TRIM(UPPER(CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')))) as full_name,
            first_name,
            last_name,
            year_of_birth,
            position
        FROM `{self.project_id}.{self.dataset_id}.{self.players_table_id}`
        WHERE id IS NOT NULL
        AND first_name IS NOT NULL 
        AND last_name IS NOT NULL
        """
        
        logger.info("Loading players table for matching...")
        players_df = self.client.query(query).to_dataframe()
        logger.info(f"Loaded {len(players_df)} players for matching")
        return players_df

    def _normalize_name(self, name: str) -> str:
        """Normalize player names for matching"""
        if pd.isna(name) or not name:
            return ""
        
        # Remove common suffixes and prefixes
        name = re.sub(r'\b(Jr\.?|Sr\.?|II|III|IV)\b', '', str(name))
        # Remove extra whitespace and convert to uppercase
        name = re.sub(r'\s+', ' ', name.strip().upper())
        return name
        
    def _similarity_score(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        name1_norm = self._normalize_name(name1)
        name2_norm = self._normalize_name(name2)
        return SequenceMatcher(None, name1_norm, name2_norm).ratio()
        
    def _match_player_id(self, player_name: str, birth_year: Optional[int] = None, 
                        position: Optional[str] = None) -> Optional[str]:
        """Match player name to existing player ID"""
        if not player_name or player_name == "No selection was made":
            return None
            
        normalized_search_name = self._normalize_name(player_name)
        
        # First try exact match
        exact_matches = self.players_df[
            self.players_df['full_name'] == normalized_search_name
        ]
        
        if len(exact_matches) == 1:
            return exact_matches.iloc[0]['player_id']
        elif len(exact_matches) > 1:
            # If multiple exact matches, try to filter by birth year
            if birth_year:
                year_matches = exact_matches[
                    exact_matches['year_of_birth'] == birth_year
                ]
                if len(year_matches) == 1:
                    return year_matches.iloc[0]['player_id']
        
        # If no exact match, try fuzzy matching
        similarities = self.players_df['full_name'].apply(
            lambda x: self._similarity_score(normalized_search_name, x)
        )
        
        # Get best matches above threshold
        threshold = 0.85
        best_matches = similarities[similarities >= threshold].sort_values(ascending=False)
        
        if len(best_matches) == 0:
            return None
        else:
            # Return best similarity match
            return self.players_df.iloc[best_matches.index[0]]['player_id']
    
    def _read_csv_with_encoding(self, file_path: str):
        """Try to read CSV with different encodings"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Successfully read {file_path} with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, raise an error
        raise ValueError(f"Could not read {file_path} with any common encoding")
    
    def _process_draft_data(self, df, draft_league_name):
        """Process draft data and match players"""
        
        logger.info(f"Processing {len(df)} {draft_league_name} draft records")
        
        # Create standardized dataframe
        processed_df = pd.DataFrame()
        
        # Map columns from CSV to BigQuery schema
        processed_df['draft_league'] = draft_league_name
        processed_df['draft_year'] = pd.to_numeric(df['Draft Year'], errors='coerce').fillna(0).astype(int)
        processed_df['draft_round'] = pd.to_numeric(df['Round'], errors='coerce').fillna(0).astype(int)
        processed_df['overall_pick'] = pd.to_numeric(df['Pick'], errors='coerce').fillna(0).astype(int)
        processed_df['team_name'] = df['Team'].fillna('')
        processed_df['player_name'] = df['Player Name'].fillna('')
        
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
        
        # Match players to IDs
        logger.info(f"Matching {draft_league_name} players to existing IDs...")
        processed_df['player_id'] = processed_df.apply(
            lambda row: self._match_player_id(
                row['player_name'] if row['selection_made'] else None,
                None,  # We don't have birth year in this data
                row['player_position']
            ), axis=1
        )
        
        # Add missing required columns
        processed_df['team_id'] = None
        processed_df['draft_date'] = None
        processed_df['created_at'] = datetime.utcnow()
        processed_df['updated_at'] = datetime.utcnow()
        
        # Log matching results
        total_picks = len(processed_df)
        actual_selections = processed_df['selection_made'].sum()
        matched_players = processed_df['player_id'].notna().sum()
        
        logger.info(f"{draft_league_name} processing results:")
        logger.info(f"  Total picks: {total_picks}")
        logger.info(f"  Actual selections: {actual_selections}")
        logger.info(f"  Players matched: {matched_players}/{actual_selections} ({matched_players/actual_selections*100:.1f}%)")
        
        return processed_df
    
    def _upsert_to_bigquery(self, df, league_name):
        """Upsert data to BigQuery"""
        
        if df.empty:
            logger.warning(f"No {league_name} data to upload")
            return
            
        logger.info(f"Uploading {len(df)} {league_name} records to BigQuery...")
        
        # Delete existing records for this league
        delete_query = f"""
        DELETE FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE draft_league = '{league_name}'
        """
        
        try:
            logger.info(f"Deleting existing {league_name} records...")
            delete_job = self.client.query(delete_query)
            delete_job.result()
            logger.info(f"Deleted existing {league_name} records")
        except Exception as e:
            logger.warning(f"Could not delete existing {league_name} records: {e}")
        
        # Upload new data
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )
        
        try:
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            logger.info(f"Successfully uploaded {len(df)} {league_name} records!")
            
            # Verify upload
            verify_query = f"""
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE draft_league = '{league_name}'
            """
            result = self.client.query(verify_query).to_dataframe()
            logger.info(f"Verification: {result.iloc[0]['count']} {league_name} records in table")
            
        except Exception as e:
            logger.error(f"Error uploading {league_name} data: {e}")
            raise
    
    def process_draft_files(self, canadian_file: str, ushl_file: str):
        """Main processing method"""
        
        logger.info("Starting draft data processing...")
        
        # Process Canadian drafts
        try:
            canadian_df = self._read_csv_with_encoding(canadian_file)
            processed_canadian = self._process_draft_data(canadian_df, 'Canadian')
            self._upsert_to_bigquery(processed_canadian, 'Canadian')
        except Exception as e:
            logger.error(f"Error processing Canadian drafts: {e}")
            raise
        
        # Process USHL drafts
        try:
            ushl_df = self._read_csv_with_encoding(ushl_file)
            processed_ushl = self._process_draft_data(ushl_df, 'USHL')
            self._upsert_to_bigquery(processed_ushl, 'USHL')
        except Exception as e:
            logger.error(f"Error processing USHL drafts: {e}")
            raise
        
        logger.info("Draft processing completed successfully!")
        self._generate_summary_report()
    
    def _generate_summary_report(self):
        """Generate summary report"""
        summary_query = f"""
        SELECT 
            draft_league,
            COUNT(*) as total_picks,
            COUNT(CASE WHEN selection_made THEN 1 END) as actual_selections,
            COUNT(player_id) as players_matched,
            ROUND(COUNT(player_id) * 100.0 / COUNT(CASE WHEN selection_made THEN 1 END), 2) as match_rate_pct,
            MIN(draft_year) as earliest_year,
            MAX(draft_year) as latest_year
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        GROUP BY draft_league
        ORDER BY draft_league
        """
        
        try:
            summary_df = self.client.query(summary_query).to_dataframe()
            
            print("\n" + "="*60)
            print("DRAFT DATA SUMMARY REPORT")
            print("="*60)
            
            for _, row in summary_df.iterrows():
                print(f"""
{row['draft_league']} Draft:
  - Total picks: {row['total_picks']}
  - Actual selections: {row['actual_selections']}
  - Players matched: {row['players_matched']} ({row['match_rate_pct']}%)
  - Years covered: {row['earliest_year']}-{row['latest_year']}
                """)
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")


def main():
    """Main execution function"""
    
    try:
        # Initialize processor
        processor = DraftDataProcessor()
        
        # File paths
        canadian_file = "canadian_drafts_master_consolidated.csv"
        ushl_file = "ushl_master_consolidated.csv"
        
        # Check if files exist
        import os
        if not os.path.exists(canadian_file):
            print(f"❌ Canadian file not found: {canadian_file}")
            return
        if not os.path.exists(ushl_file):
            print(f"❌ USHL file not found: {ushl_file}")
            return
        
        # Process the files
        processor.process_draft_files(canadian_file, ushl_file)
        
        print("\n🎉 SUCCESS! Draft data processing completed!")
        print("✅ Canadian and USHL draft data uploaded to BigQuery")
        print("📊 Data is now ready for Factor 17 analysis!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Script failed: {e}")


if __name__ == "__main__":
    main()