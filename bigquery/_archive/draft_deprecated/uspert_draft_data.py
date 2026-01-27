#!/usr/bin/env python3
"""
Draft Data Upsert Script with Player Matching
Processes Canadian and USHL draft data, matches players, and upserts to BigQuery
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2 import service_account
import re
from datetime import datetime, date
from difflib import SequenceMatcher
from typing import Optional, Dict, List, Tuple
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
        
    def _load_players(self) -> pd.DataFrame:
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
        if not player_name:
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
        elif len(best_matches) == 1:
            return self.players_df.iloc[best_matches.index[0]]['player_id']
        else:
            # Multiple good matches, try filtering by birth year or position
            top_indices = best_matches.head(5).index
            candidates = self.players_df.iloc[top_indices]
            
            if birth_year:
                year_candidates = candidates[candidates['year_of_birth'] == birth_year]
                if len(year_candidates) == 1:
                    return year_candidates.iloc[0]['player_id']
                elif len(year_candidates) > 1:
                    candidates = year_candidates
            
            if position:
                pos_candidates = candidates[candidates['position'] == position]
                if len(pos_candidates) >= 1:
                    return pos_candidates.iloc[0]['player_id']
            
            # Return best similarity match
            return candidates.iloc[0]['player_id']
        
        return None
    
    def _process_canadian_draft_data(self, file_path: str) -> pd.DataFrame:
        """Process Canadian draft data CSV"""
        logger.info(f"Processing Canadian draft data from {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} Canadian draft records")
        
        # Standardize column names (adjust based on actual CSV structure)
        column_mapping = {
            'Draft Year': 'draft_year',
            'Round': 'draft_round', 
            'Pick': 'overall_pick',
            'Team': 'team_name',
            'Player': 'player_name',
            'Position': 'player_position',
            # Add other mappings as needed based on your CSV structure
        }
        
        df = df.rename(columns=column_mapping)
        
        # Add draft league identifier
        df['draft_league'] = 'Canadian'
        
        # Process player matching
        logger.info("Matching Canadian draft players to player IDs...")
        df['player_id'] = df.apply(
            lambda row: self._match_player_id(
                row.get('player_name'), 
                row.get('birth_year'),
                row.get('player_position')
            ), axis=1
        )
        
        matched_count = df['player_id'].notna().sum()
        logger.info(f"Matched {matched_count}/{len(df)} Canadian draft players to IDs")
        
        return self._standardize_draft_data(df)
    
    def _process_ushl_draft_data(self, file_path: str) -> pd.DataFrame:
        """Process USHL draft data CSV"""
        logger.info(f"Processing USHL draft data from {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} USHL draft records")
        
        # Standardize column names (adjust based on actual CSV structure)
        column_mapping = {
            'Draft Year': 'draft_year',
            'Round': 'draft_round',
            'Pick': 'overall_pick', 
            'Team': 'team_name',
            'Player': 'player_name',
            'Position': 'player_position',
            # Add other mappings as needed
        }
        
        df = df.rename(columns=column_mapping)
        
        # Add draft league identifier  
        df['draft_league'] = 'USHL'
        
        # Process player matching
        logger.info("Matching USHL draft players to player IDs...")
        df['player_id'] = df.apply(
            lambda row: self._match_player_id(
                row.get('player_name'),
                row.get('birth_year'), 
                row.get('player_position')
            ), axis=1
        )
        
        matched_count = df['player_id'].notna().sum()
        logger.info(f"Matched {matched_count}/{len(df)} USHL draft players to IDs")
        
        return self._standardize_draft_data(df)
    
    def _standardize_draft_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize draft data to match BigQuery schema"""
        
        # Ensure required columns exist
        required_columns = [
            'draft_league', 'draft_year', 'draft_round', 'overall_pick', 'team_name'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                if col == 'draft_league':
                    df[col] = 'Unknown'
                elif col in ['draft_year', 'draft_round', 'overall_pick']:
                    df[col] = 0
                else:
                    df[col] = ''
        
        # Optional columns with defaults
        optional_columns = {
            'team_id': None,
            'player_name': None,
            'player_position': None, 
            'player_id': None,
            'selection_made': True,
            'draft_date': None
        }
        
        for col, default_val in optional_columns.items():
            if col not in df.columns:
                df[col] = default_val
        
        # Add timestamps
        current_time = datetime.utcnow()
        df['created_at'] = current_time
        df['updated_at'] = current_time
        
        # Ensure correct data types
        df['draft_year'] = pd.to_numeric(df['draft_year'], errors='coerce').fillna(0).astype(int)
        df['draft_round'] = pd.to_numeric(df['draft_round'], errors='coerce').fillna(0).astype(int)
        df['overall_pick'] = pd.to_numeric(df['overall_pick'], errors='coerce').fillna(0).astype(int)
        df['selection_made'] = df['selection_made'].fillna(True).astype(bool)
        
        # Select and order columns to match schema
        columns_order = [
            'draft_league', 'draft_year', 'draft_round', 'overall_pick', 'team_name',
            'team_id', 'player_name', 'player_position', 'player_id', 'selection_made',
            'draft_date', 'created_at', 'updated_at'
        ]
        
        return df[columns_order]
    
    def _upsert_to_bigquery(self, df: pd.DataFrame, league_name: str):
        """Upsert draft data to BigQuery"""
        
        if df.empty:
            logger.warning(f"No {league_name} draft data to upsert")
            return
            
        logger.info(f"Upserting {len(df)} {league_name} draft records to BigQuery...")
        
        # Create table reference
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        
        # Configure job to replace data for this specific league
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
        )
        
        # First, delete existing records for this league if they exist
        delete_query = f"""
        DELETE FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE draft_league = '{league_name}'
        """
        
        try:
            logger.info(f"Deleting existing {league_name} records...")
            delete_job = self.client.query(delete_query)
            delete_job.result()  # Wait for completion
            logger.info(f"Deleted existing {league_name} records")
        except Exception as e:
            logger.warning(f"Could not delete existing {league_name} records: {e}")
        
        # Load new data
        try:
            job = self.client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            job.result()  # Wait for completion
            
            logger.info(f"Successfully upserted {len(df)} {league_name} draft records")
            
            # Verify the upsert
            verify_query = f"""
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE draft_league = '{league_name}'
            """
            result = self.client.query(verify_query).to_dataframe()
            logger.info(f"Verification: {result.iloc[0]['count']} {league_name} records in table")
            
        except Exception as e:
            logger.error(f"Error upserting {league_name} draft data: {e}")
            raise
    
    def process_draft_files(self, canadian_file_path: str, ushl_file_path: str):
        """Main method to process both draft files"""
        
        logger.info("Starting draft data processing...")
        
        # Process Canadian draft data
        try:
            canadian_df = self._process_canadian_draft_data(canadian_file_path)
            self._upsert_to_bigquery(canadian_df, 'Canadian')
        except Exception as e:
            logger.error(f"Error processing Canadian draft data: {e}")
            raise
        
        # Process USHL draft data  
        try:
            ushl_df = self._process_ushl_draft_data(ushl_file_path)
            self._upsert_to_bigquery(ushl_df, 'USHL')
        except Exception as e:
            logger.error(f"Error processing USHL draft data: {e}")
            raise
        
        logger.info("Draft data processing completed successfully!")
        
        # Generate summary report
        self._generate_summary_report()
    
    def _generate_summary_report(self):
        """Generate a summary report of the draft data"""
        
        summary_query = f"""
        SELECT 
            draft_league,
            COUNT(*) as total_picks,
            COUNT(DISTINCT draft_year) as years_covered,
            COUNT(player_id) as players_matched,
            ROUND(COUNT(player_id) * 100.0 / COUNT(*), 2) as match_rate_pct,
            MIN(draft_year) as earliest_year,
            MAX(draft_year) as latest_year
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        GROUP BY draft_league
        ORDER BY draft_league
        """
        
        summary_df = self.client.query(summary_query).to_dataframe()
        
        logger.info("\n" + "="*80)
        logger.info("DRAFT DATA SUMMARY REPORT")
        logger.info("="*80)
        
        for _, row in summary_df.iterrows():
            logger.info(f"""
{row['draft_league']} Draft:
  - Total picks: {row['total_picks']}
  - Years covered: {row['years_covered']} ({row['earliest_year']}-{row['latest_year']})
  - Players matched: {row['players_matched']} ({row['match_rate_pct']}%)
            """)
        
        logger.info("="*80)


def main():
    """Main execution function"""
    
    # Initialize processor
    processor = DraftDataProcessor()
    
    # File paths - update these with your actual file paths
    canadian_file_path = "canadian_drafts_master_consolidated.csv"
    ushl_file_path = "ushl_master_consolidated.csv"
    
    # Process both draft files
    processor.process_draft_files(canadian_file_path, ushl_file_path)
    
    print("\n✅ Draft data processing completed successfully!")
    print("\nThe data is now available in your BigQuery hockey.all_drafts table")
    print("You can now proceed with Factor 17 analysis!")


if __name__ == "__main__":
    main()