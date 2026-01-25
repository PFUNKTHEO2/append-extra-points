-- Update January 21, 2026 NEPSAC game results
-- Run in BigQuery

-- Kent 2 @ Hotchkiss 6 (Correct - Hotchkiss predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=2, home_score=6 WHERE game_id='b678a605-097e-4dbe-a3d7-1bf649f585e0';

-- Dexter 10 @ Austin Prep 4 (Correct - Dexter predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=10, home_score=4 WHERE game_id='db8f5afd-780e-4f7d-8bb9-1d105b23cb7c';

-- Brewster 1 @ Tilton 3 (Correct - Tilton predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=3 WHERE game_id='82bac436-bdc1-4ced-945c-88053f732ca7';

-- Vermont Academy 1 @ Williston Northampton 12 (Correct - Williston predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=12 WHERE game_id='621a7621-4567-4786-a038-b4cd85e51a60';

-- BB&N 0 @ St. George's 4 (Correct - St. George's predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=0, home_score=4 WHERE game_id='d9e44362-c8e9-4cdf-bb19-8bbf0bfb169a';

-- Avon Old Farms 8 @ NMH 1 (Correct - Avon predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=8, home_score=1 WHERE game_id='9d4d64a5-e522-41aa-bee8-84cdc9246fec';

-- Taft 5 @ Loomis Chaffee 1 (Correct - Taft predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=5, home_score=1 WHERE game_id='ff7c6056-e5ba-4315-aca9-acdbb198be3d';

-- Thayer 2 @ Cushing 5 (Correct - Cushing predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=2, home_score=5 WHERE game_id='5b68234b-7e08-4ea8-9d61-882c3794cec1';

-- Hoosac 1 @ Winchendon 10 (Correct - Winchendon predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=10 WHERE game_id='ba7f62ad-d385-47b4-a858-e8bb129c0063';

-- Choate 1 @ Berkshire 4 (Correct - Berkshire predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=4 WHERE game_id='2cb3c8d3-b6e4-482a-9486-c048f056d1bd';

-- Holderness 10 @ North Yarmouth 1 (Correct - Holderness predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=10, home_score=1 WHERE game_id='9a5478a6-8d86-4ae4-9af3-242c90109fda';

-- Groton 1 @ Governor's 0 (Correct - Groton predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=0 WHERE game_id='df87f18a-cec6-47b9-a304-0b6251f70f09';

-- Pingree 4 @ Portsmouth Abbey 2 (Correct - Pingree predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=4, home_score=2 WHERE game_id='468d579c-edcd-4717-89c1-cdf16d4556fe';

-- Pomfret 6 @ Worcester Academy 1 (Correct - Pomfret predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=6, home_score=1 WHERE game_id='fe50ce0c-aaac-4721-adce-57db4a75e946';

-- Exeter 1 @ Tabor 3 (Correct - Tabor predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=3 WHERE game_id='94a5302d-f1af-42a3-9eef-138011442458';

-- Frederick Gunn 1 @ Millbrook 4 (Incorrect - Frederick Gunn predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=4 WHERE game_id='9e9319d8-85f3-4092-a7b3-93fea3946010';

-- Middlesex 4 @ Roxbury Latin 5 (Incorrect - Middlesex predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=4, home_score=5 WHERE game_id='352e6212-1d1a-4b55-b278-e7a8c4bd93e0';

-- Milton 1 @ Lawrence Academy 3 (Incorrect - Milton predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=3 WHERE game_id='888ec234-a77b-47fd-83e5-3414b0bf9618';

-- Deerfield 4 @ Kimball Union 1 (Incorrect - Kimball Union predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=4, home_score=1 WHERE game_id='2a40470c-f015-4a34-90bd-a4244fa6ba72';

-- Princeton Day 1 @ Lawrenceville 2 (Incorrect - Princeton Day predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=2 WHERE game_id='79998a84-f1ef-42e4-a558-2b5ea2a5be44';

-- Westminster 1 @ Canterbury 1 (Tie - Canterbury predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=1 WHERE game_id='6a4f3963-1d35-4d54-9edd-db1c184f4778';

-- Berwick 1 @ Kents Hill 1 (Tie - Kents Hill predicted)
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule` SET status='final', away_score=1, home_score=1 WHERE game_id='550ebf6c-e3e8-45a4-bd3e-d8586fff0d8c';

-- Games NOT in original static page (need results if available):
-- Mount @ Wilbraham | game_id: 9bc56f5a-8664-4a34-8622-33057cde56c6
-- St. Paul's @ Proctor | game_id: a6199c7e-18fe-4c9f-bc83-10c5444db78b
-- St. Sebastian's @ Andover | game_id: 425adef2-1e63-48f6-9b2a-20546bce39a4
-- TBD @ The (skip - TBD team) | game_id: b95b3b03-025e-45bd-b5ce-f0d5a931c3c1
-- Trinity-Pawling @ Salisbury | game_id: 1a5e0d99-9ee2-43ad-b05f-3b610e70d977
