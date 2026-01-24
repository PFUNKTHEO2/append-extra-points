-- Update Shattuck St. Mary's player images in nepsac_rosters
-- All images sourced from Elite Prospects

-- Roberts Naudins
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/n20-naudins,-roberts-(10)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Roberts Naudins' AND season = '2025-26';

-- Luke Puchner
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/9-puchner,-luke-(10)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Luke Puchner' AND season = '2025-26';

-- Colin Grubb
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/n13-grubb,-colin-(52)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Colin Grubb' AND season = '2025-26';

-- Rennick Hendrickson
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/n11-hendrickson,-rennick-(16)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Rennick Hendrickson' AND season = '2025-26';

-- Payne Riffey
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/16-riffey,-john-payne-(18)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Payne Riffey' AND season = '2025-26';

-- Gavin Weber
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/23-weber,-gavin-(22)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Gavin Weber' AND season = '2025-26';

-- Davis Damrow
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/12-damrow,-davis-(35)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Davis Damrow' AND season = '2025-26';

-- JT Borland
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/7f3de-img-4738.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'JT Borland' AND season = '2025-26';

-- Cameron Garrity
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/4-garrity,-cameron-(13)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Cameron Garrity' AND season = '2025-26';

-- Garrett Glaser
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET image_url = 'https://files.eliteprospects.com/layout/players/n1-glaser,-garret-(5)-ep.jpg'
WHERE team_id = 'shattuck-st-mary-s' AND roster_name = 'Garrett Glaser' AND season = '2025-26';

-- Verify updates
SELECT
  roster_name,
  position,
  prodigy_points,
  image_url
FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
WHERE team_id = 'shattuck-st-mary-s' AND season = '2025-26'
ORDER BY prodigy_points DESC;
