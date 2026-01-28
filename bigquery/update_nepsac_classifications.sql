-- =============================================================================
-- Update NEPSAC Teams with Official Classifications (2025-26 Season)
-- Source: NEPSAC-Boys-Ice-Hockey-Classification-BIH-25-26-2.pdf
-- =============================================================================

-- First, add classification and enrollment columns if they don't exist
-- (Run these ALTER statements separately if needed)

-- Step 1: Create a temp table with official classifications
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.nepsac_official_classifications` AS
SELECT * FROM UNNEST([
  -- LARGE SCHOOLS (28 teams)
  STRUCT('andover' AS team_id, 'Phillips Academy Andover' AS team_name, 'Andover' AS short_name, 'Large' AS classification, 585 AS enrollment),
  STRUCT('exeter', 'Phillips Exeter Academy', 'Exeter', 'Large', 545),
  STRUCT('brunswick', 'Brunswick School', 'Brunswick', 'Large', 440),
  STRUCT('choate', 'Choate Rosemary Hall', 'Choate', 'Large', 422),
  STRUCT('avon-old-farms', 'Avon Old Farms', 'Avon', 'Large', 401),
  STRUCT('milton', 'Milton Academy', 'Milton', 'Large', 357),
  STRUCT('deerfield', 'Deerfield Academy', 'Deerfield', 'Large', 355),
  STRUCT('loomis', 'Loomis Chaffee', 'Loomis', 'Large', 351),
  STRUCT('belmont-hill', 'Belmont Hill School', 'Belmont Hill', 'Large', 350),
  STRUCT('salisbury', 'Salisbury School', 'Salisbury', 'Large', 306),
  STRUCT('taft', 'Taft School', 'Taft', 'Large', 305),
  STRUCT('hotchkiss', 'Hotchkiss School', 'Hotchkiss', 'Large', 305),
  STRUCT('nmh', 'Northfield Mount Hermon', 'NMH', 'Large', 304),
  STRUCT('st-sebastians', 'St. Sebastians School', 'St. Sebs', 'Large', 285),
  STRUCT('bbn', 'Buckingham Browne & Nichols', 'BB&N', 'Large', 280),
  STRUCT('tabor', 'Tabor Academy', 'Tabor', 'Large', 279),
  STRUCT('thayer', 'Thayer Academy', 'Thayer', 'Large', 276),
  STRUCT('kent', 'Kent School', 'Kent', 'Large', 265),
  STRUCT('st-pauls', 'St. Pauls School', 'St. Pauls', 'Large', 264),
  STRUCT('austin-prep', 'Austin Prep', 'Austin Prep', 'Large', 257),
  STRUCT('dexter', 'Dexter Southfield', 'Dexter', 'Large', 257),
  STRUCT('nobles', 'Noble and Greenough School', 'Nobles', 'Large', 253),
  STRUCT('williston', 'Williston Northampton', 'Williston', 'Large', 245),
  STRUCT('trinity-pawling', 'Trinity-Pawling School', 'Trinity-Pawling', 'Large', 240),
  STRUCT('worcester', 'Worcester Academy', 'Worcester', 'Large', 235),
  STRUCT('cushing', 'Cushing Academy', 'Cushing', 'Large', 226),
  STRUCT('westminster', 'Westminster School', 'Westminster', 'Large', 225),
  STRUCT('lawrence', 'Lawrence Academy', 'Lawrence', 'Large', 225),

  -- SMALL SCHOOLS (29 teams)
  STRUCT('governors', 'Governors Academy', 'Governors', 'Small', 222),
  STRUCT('middlesex', 'Middlesex School', 'Middlesex', 'Small', 221),
  STRUCT('roxbury-latin', 'Roxbury Latin School', 'Roxbury Latin', 'Small', 218),
  STRUCT('berkshire', 'Berkshire School', 'Berkshire', 'Small', 217),
  STRUCT('proctor', 'Proctor Academy', 'Proctor', 'Small', 212),
  STRUCT('rivers', 'Rivers School', 'Rivers', 'Small', 205),
  STRUCT('kimball-union', 'Kimball Union Academy', 'KUA', 'Small', 199),
  STRUCT('st-marks', 'St. Marks School', 'St. Marks', 'Small', 193),
  STRUCT('albany-academy', 'Albany Academy', 'Albany', 'Small', 192),
  STRUCT('st-georges', 'St. Georges School', 'St. Georges', 'Small', 192),
  STRUCT('brooks', 'Brooks School', 'Brooks', 'Small', 191),
  STRUCT('groton', 'Groton School', 'Groton', 'Small', 189),
  STRUCT('new-hampton', 'New Hampton School', 'New Hampton', 'Small', 187),
  STRUCT('brewster', 'Brewster Academy', 'Brewster', 'Small', 186),
  STRUCT('pomfret', 'Pomfret School', 'Pomfret', 'Small', 183),
  STRUCT('canterbury', 'Canterbury School', 'Canterbury', 'Small', 180),
  STRUCT('wma', 'Wilbraham & Monson Academy', 'WMA', 'Small', 178),
  STRUCT('pingree', 'Pingree School', 'Pingree', 'Small', 177),
  STRUCT('portsmouth-abbey', 'Portsmouth Abbey School', 'Portsmouth Abbey', 'Small', 177),
  STRUCT('winchendon', 'Winchendon School', 'Winchendon', 'Small', 170),
  STRUCT('frederick-gunn', 'Frederick Gunn School', 'Frederick Gunn', 'Small', 170),
  STRUCT('hoosac', 'Hoosac School', 'Hoosac', 'Small', 169),
  STRUCT('millbrook', 'Millbrook School', 'Millbrook', 'Small', 165),
  STRUCT('holderness', 'Holderness School', 'Holderness', 'Small', 164),
  STRUCT('berwick', 'Berwick Academy', 'Berwick', 'Small', 143),
  STRUCT('vermont-academy', 'Vermont Academy', 'Vermont', 'Small', 137),
  STRUCT('hebron', 'Hebron Academy', 'Hebron', 'Small', 117),
  STRUCT('kents-hill', 'Kents Hill School', 'Kents Hill', 'Small', 110),
  STRUCT('tilton', 'Tilton School', 'Tilton', 'Small', 99)
]);

-- Step 2: Update nepsac_teams with classification and enrollment
-- First check what exists
SELECT
  t.team_id,
  t.team_name,
  t.division AS old_division,
  c.classification AS new_classification,
  c.enrollment
FROM `prodigy-ranking.algorithm_core.nepsac_teams` t
LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_official_classifications` c
  ON t.team_id = c.team_id
ORDER BY c.enrollment DESC NULLS LAST;

-- Step 3: Replace nepsac_teams with official data (preserves other columns)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.nepsac_teams` AS
SELECT
  c.team_id,
  c.team_name,
  c.short_name,
  c.classification,  -- 'Large' or 'Small'
  c.enrollment,
  t.logo_url,
  t.primary_color,
  t.secondary_color,
  t.venue,
  t.city,
  t.state,
  t.ep_team_id,
  t.mhr_team_id,
  COALESCE(t.created_at, CURRENT_TIMESTAMP()) AS created_at,
  CURRENT_TIMESTAMP() AS updated_at
FROM `prodigy-ranking.algorithm_core.nepsac_official_classifications` c
LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_teams` t
  ON c.team_id = t.team_id;

-- Verify the update
SELECT
  classification,
  COUNT(*) as team_count,
  MIN(enrollment) as min_enrollment,
  MAX(enrollment) as max_enrollment
FROM `prodigy-ranking.algorithm_core.nepsac_teams`
GROUP BY classification
ORDER BY classification;
