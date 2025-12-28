/**
 * Supabase Connection Utility
 * Shared module for connecting to Supabase PostgreSQL
 */

const { createClient } = require('@supabase/supabase-js');

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.warn('Supabase credentials not configured. Blurb features will be unavailable.');
}

const supabase = supabaseUrl && supabaseServiceKey
  ? createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    })
  : null;

/**
 * Check if Supabase is configured
 */
function isConfigured() {
  return supabase !== null;
}

/**
 * Get a player's blurb
 * @param {number} playerId - Player ID from BigQuery
 * @returns {Promise<object|null>} Blurb data or null
 */
async function getBlurb(playerId) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('player_blurbs')
    .select('*')
    .eq('player_id', playerId)
    .eq('status', 'published')
    .single();

  if (error && error.code !== 'PGRST116') { // PGRST116 = no rows returned
    throw error;
  }

  return data;
}

/**
 * Create or update a player's blurb
 * @param {number} playerId - Player ID
 * @param {object} blurbData - Blurb content and metadata
 * @param {string} userId - User making the change
 * @returns {Promise<object>} Created/updated blurb
 */
async function upsertBlurb(playerId, blurbData, userId) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data: existing } = await supabase
    .from('player_blurbs')
    .select('id, version')
    .eq('player_id', playerId)
    .single();

  if (existing) {
    // Update existing
    const { data, error } = await supabase
      .from('player_blurbs')
      .update({
        content: blurbData.content,
        content_html: blurbData.contentHtml,
        ai_generated_chars: blurbData.aiGeneratedChars || 0,
        human_edited_chars: blurbData.humanEditedChars || 0,
        version: existing.version + 1,
        last_edited_by: userId,
        status: blurbData.status || 'published'
      })
      .eq('id', existing.id)
      .select()
      .single();

    if (error) throw error;
    return data;
  } else {
    // Create new
    const { data, error } = await supabase
      .from('player_blurbs')
      .insert({
        player_id: playerId,
        content: blurbData.content,
        content_html: blurbData.contentHtml,
        ai_generated_chars: blurbData.aiGeneratedChars || blurbData.content.length,
        human_edited_chars: blurbData.humanEditedChars || 0,
        created_by: userId,
        last_edited_by: userId,
        status: blurbData.status || 'published'
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  }
}

/**
 * Create a revision record
 * @param {string} blurbId - Blurb UUID
 * @param {number} playerId - Player ID
 * @param {object} revisionData - Revision details
 * @returns {Promise<object>} Created revision
 */
async function createRevision(blurbId, playerId, revisionData) {
  if (!supabase) throw new Error('Supabase not configured');

  // Mark all previous revisions as not current
  await supabase
    .from('blurb_revisions')
    .update({ is_current: false })
    .eq('blurb_id', blurbId);

  const { data, error } = await supabase
    .from('blurb_revisions')
    .insert({
      blurb_id: blurbId,
      player_id: playerId,
      content: revisionData.content,
      content_diff: revisionData.contentDiff,
      revision_type: revisionData.revisionType,
      edited_by: revisionData.editedBy,
      edit_summary: revisionData.editSummary,
      chars_added: revisionData.charsAdded || 0,
      chars_removed: revisionData.charsRemoved || 0,
      chars_from_ai: revisionData.charsFromAi || 0,
      version: revisionData.version,
      is_current: true
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

/**
 * Get revision history for a blurb
 * @param {number} playerId - Player ID
 * @param {number} limit - Max revisions to return
 * @returns {Promise<Array>} Revision history
 */
async function getRevisions(playerId, limit = 50) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('blurb_revisions')
    .select('*')
    .eq('player_id', playerId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error) throw error;
  return data || [];
}

/**
 * Submit an edit suggestion
 * @param {number} playerId - Player ID
 * @param {object} suggestion - Suggestion data
 * @param {string} userId - Submitting user
 * @returns {Promise<object>} Created suggestion
 */
async function submitSuggestion(playerId, suggestion, userId) {
  if (!supabase) throw new Error('Supabase not configured');

  // Handle anonymous users - use a fixed UUID for anonymous submissions
  // This UUID represents "anonymous" user in the system
  const ANONYMOUS_UUID = '00000000-0000-0000-0000-000000000000';
  const isAnonymous = !userId || userId === 'anonymous' || userId === 'null';
  const validUserId = isAnonymous ? ANONYMOUS_UUID : userId;

  // Check if user has auto-approve privileges (only for authenticated users)
  let canAutoApprove = false;
  if (!isAnonymous) {
    const { data: contributor } = await supabase
      .from('contributor_stats')
      .select('can_auto_approve, trust_level')
      .eq('account_id', validUserId)
      .single();

    canAutoApprove = contributor?.can_auto_approve ||
      ['trusted', 'moderator', 'admin'].includes(contributor?.trust_level);
  }

  // Get existing blurb ID if exists
  const { data: blurb } = await supabase
    .from('player_blurbs')
    .select('id')
    .eq('player_id', playerId)
    .single();

  const { data, error } = await supabase
    .from('blurb_suggestions')
    .insert({
      blurb_id: blurb?.id,
      player_id: playerId,
      suggested_content: suggestion.content,
      suggested_diff: suggestion.diff,
      edit_summary: suggestion.editSummary,
      submitted_by: validUserId,  // NULL for anonymous
      status: canAutoApprove ? 'auto_approved' : 'pending',
      auto_approved: canAutoApprove
    })
    .select()
    .single();

  if (error) throw error;

  // If auto-approved, apply the edit immediately
  if (canAutoApprove) {
    await applyApprovedSuggestion(data.id, userId);
  }

  return data;
}

/**
 * Get pending suggestions (moderation queue)
 * @param {number} limit - Max suggestions to return
 * @returns {Promise<Array>} Pending suggestions
 */
async function getPendingSuggestions(limit = 50) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('blurb_suggestions')
    .select(`
      id,
      player_id,
      suggested_content,
      suggested_diff,
      edit_summary,
      submitted_by,
      submitted_at,
      status
    `)
    .eq('status', 'pending')
    .order('submitted_at', { ascending: true })
    .limit(limit);

  if (error) throw error;
  return data || [];
}

/**
 * Review a suggestion (approve/reject)
 * @param {string} suggestionId - Suggestion UUID
 * @param {string} status - 'approved' or 'rejected'
 * @param {string} reviewerId - Reviewing moderator
 * @param {string} notes - Review notes
 * @returns {Promise<object>} Updated suggestion
 */
async function reviewSuggestion(suggestionId, status, reviewerId, notes = null) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('blurb_suggestions')
    .update({
      status,
      reviewed_by: reviewerId,
      reviewed_at: new Date().toISOString(),
      review_notes: notes
    })
    .eq('id', suggestionId)
    .select()
    .single();

  if (error) throw error;

  // If approved, apply the edit
  if (status === 'approved') {
    await applyApprovedSuggestion(suggestionId, reviewerId);
  }

  return data;
}

/**
 * Apply an approved suggestion to the blurb
 * @param {string} suggestionId - Suggestion UUID
 * @param {string} approverId - User who approved
 */
async function applyApprovedSuggestion(suggestionId, approverId) {
  if (!supabase) throw new Error('Supabase not configured');

  // Get the suggestion
  const { data: suggestion, error: fetchError } = await supabase
    .from('blurb_suggestions')
    .select('*')
    .eq('id', suggestionId)
    .single();

  if (fetchError) throw fetchError;

  // Get current blurb version
  const { data: currentBlurb } = await supabase
    .from('player_blurbs')
    .select('id, version, content')
    .eq('player_id', suggestion.player_id)
    .single();

  const newVersion = (currentBlurb?.version || 0) + 1;

  // Upsert the blurb with new content
  const blurbResult = await upsertBlurb(
    suggestion.player_id,
    {
      content: suggestion.suggested_content,
      humanEditedChars: suggestion.suggested_content.length,
      aiGeneratedChars: 0
    },
    suggestion.submitted_by
  );

  // Create revision record
  await createRevision(blurbResult.id, suggestion.player_id, {
    content: suggestion.suggested_content,
    contentDiff: suggestion.suggested_diff,
    revisionType: 'human_edit',
    editedBy: suggestion.submitted_by,
    editSummary: suggestion.edit_summary,
    charsAdded: suggestion.suggested_content.length - (currentBlurb?.content?.length || 0),
    charsRemoved: 0,
    charsFromAi: 0,
    version: newVersion
  });
}

/**
 * Get contributor stats
 * @param {string} userId - User UUID
 * @returns {Promise<object|null>} Contributor stats
 */
async function getContributorStats(userId) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('contributor_stats')
    .select('*')
    .eq('account_id', userId)
    .single();

  if (error && error.code !== 'PGRST116') {
    throw error;
  }

  return data;
}

/**
 * Get top contributors
 * @param {number} limit - Max contributors to return
 * @returns {Promise<Array>} Top contributors
 */
async function getTopContributors(limit = 20) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('contributor_stats')
    .select('*')
    .order('reputation_score', { ascending: false })
    .order('edits_approved', { ascending: false })
    .limit(limit);

  if (error) throw error;

  // Calculate approval_rate for each contributor
  return (data || []).map(c => ({
    ...c,
    approval_rate: c.edits_submitted > 0
      ? ((c.edits_approved / c.edits_submitted) * 100).toFixed(1)
      : 0
  }));
}

/**
 * Add a discussion comment
 * @param {number} playerId - Player ID
 * @param {string} content - Comment content
 * @param {string} authorId - Author UUID
 * @param {string} parentId - Parent comment UUID (for threading)
 * @returns {Promise<object>} Created comment
 */
async function addDiscussion(playerId, content, authorId, parentId = null) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('blurb_discussions')
    .insert({
      player_id: playerId,
      content,
      author_id: authorId,
      parent_id: parentId
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

/**
 * Get discussions for a player
 * @param {number} playerId - Player ID
 * @returns {Promise<Array>} Discussion threads
 */
async function getDiscussions(playerId) {
  if (!supabase) throw new Error('Supabase not configured');

  const { data, error } = await supabase
    .from('blurb_discussions')
    .select('*')
    .eq('player_id', playerId)
    .order('created_at', { ascending: true });

  if (error) throw error;
  return data || [];
}

// ============================================================
// PLAYER RANKINGS (Fast lookups from synced table)
// ============================================================

/**
 * Get a player by ID (fast Supabase lookup)
 * @param {number} playerId - Player ID
 * @returns {Promise<object|null>} Player data or null
 */
async function getPlayerById(playerId) {
  if (!supabase) return null;

  try {
    // Use the view which includes world_rank and country_rank
    const { data, error } = await supabase
      .from('vw_player_rankings')
      .select('*')
      .eq('player_id', playerId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') return null; // Not found
      console.error('Supabase getPlayerById error:', error);
      return null;
    }

    return data;
  } catch (err) {
    console.error('Supabase getPlayerById exception:', err);
    return null;
  }
}

/**
 * Search players by name (fast Supabase lookup)
 * @param {string} query - Search query
 * @param {number} limit - Max results
 * @returns {Promise<Array>} Matching players
 */
async function searchPlayers(query, limit = 10) {
  if (!supabase) return null;

  try {
    const { data, error } = await supabase
      .from('player_rankings')
      .select('player_id, player_name, position, birth_year, nationality_name, current_team, current_league, total_points')
      .ilike('player_name', `%${query}%`)
      .order('total_points', { ascending: false })
      .limit(limit);

    if (error) {
      console.error('Supabase searchPlayers error:', error);
      return null;
    }

    return data || [];
  } catch (err) {
    console.error('Supabase searchPlayers exception:', err);
    return null;
  }
}

/**
 * Get rankings (fast Supabase lookup with rank calculation)
 * @param {number} birthYear - Birth year filter
 * @param {string} scope - 'worldwide', 'north_american', or country name
 * @param {string} position - 'F', 'D', or 'G'
 * @param {number} limit - Max results
 * @returns {Promise<object|null>} Rankings data or null
 */
async function getRankings(birthYear, scope, position, limit = 250) {
  if (!supabase) return null;

  try {
    let query = supabase
      .from('player_rankings')
      .select('*')
      .eq('birth_year', birthYear)
      .eq('position', position.toUpperCase())
      .order('total_points', { ascending: false })
      .limit(limit);

    // Apply scope filter
    if (scope === 'north_american') {
      query = query.in('nationality_name', ['Canada', 'USA']);
    } else if (scope === 'european') {
      query = query.in('nationality_name', [
        'Sweden', 'Finland', 'Russia', 'Czechia', 'Switzerland', 'Germany',
        'Slovakia', 'Austria', 'Latvia', 'Belarus', 'Denmark', 'Norway',
        'France', 'Slovenia', 'Ukraine', 'Poland', 'Hungary', 'Italy'
      ]);
    } else if (scope !== 'worldwide') {
      // Assume country name
      const countryName = scope.charAt(0).toUpperCase() + scope.slice(1);
      query = query.eq('nationality_name', countryName);
    }

    const { data, error } = await query;

    if (error) {
      console.error('Supabase getRankings error:', error);
      return null;
    }

    // Add rank numbers
    const players = (data || []).map((player, index) => ({
      ...player,
      rank: index + 1
    }));

    return {
      birth_year: birthYear,
      position: position,
      scope: scope,
      count: players.length,
      players: players
    };
  } catch (err) {
    console.error('Supabase getRankings exception:', err);
    return null;
  }
}

/**
 * Get sync status (when was data last synced)
 * @returns {Promise<object|null>} Sync status
 */
async function getSyncStatus() {
  if (!supabase) return null;

  try {
    const { data, error } = await supabase
      .from('player_rankings')
      .select('synced_at')
      .order('synced_at', { ascending: false })
      .limit(1)
      .single();

    if (error) return null;

    // Get count
    const { count } = await supabase
      .from('player_rankings')
      .select('player_id', { count: 'exact', head: true });

    return {
      last_synced: data?.synced_at,
      total_players: count
    };
  } catch (err) {
    return null;
  }
}

module.exports = {
  supabase,
  isConfigured,
  // Blurbs
  getBlurb,
  upsertBlurb,
  // Revisions
  createRevision,
  getRevisions,
  // Suggestions
  submitSuggestion,
  getPendingSuggestions,
  reviewSuggestion,
  // Contributors
  getContributorStats,
  getTopContributors,
  // Discussions
  addDiscussion,
  getDiscussions,
  // Player Rankings (fast lookups)
  getPlayerById,
  searchPlayers,
  getRankings,
  getSyncStatus
};
