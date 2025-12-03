"""
Sports Tool for Daily Digest
Fetches sports scores and schedules for configured teams
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

from utils.config import get_config
from utils.logging import get_logger
from utils.metrics import get_metrics


logger = get_logger()
metrics = get_metrics()


def get_sports_scores(teams: List[str] = None) -> Dict[str, Any]:
    """
    Fetches recent scores and upcoming games for specified teams.
    
    Uses The Sports DB API if key is available, otherwise falls back to mock data.
    Get free API key from: https://www.thesportsdb.com/api.php
    
    Args:
        teams: List of team names (e.g., ["49ers", "Sharks", "Warriors"])
               If not provided, uses default teams from config.
    
    Returns:
        Dictionary containing:
        - teams: List of team data (name, league, record, latest_game, next_game)
        - timestamp: ISO format timestamp
        - source: Data source
        - error: Error message if failed
    
    Example:
        >>> sports = get_sports_scores(["49ers", "Warriors"])
        >>> print(sports['teams'][0]['record'])
        "10-3"
    """
    config = get_config()
    
    # Use provided teams or defaults
    if teams is None:
        teams = config.sports_teams
    
    logger.info("Fetching sports scores", teams=teams)
    metrics.start_timer("tool.get_sports_scores")
    
    try:
        # Use real Sports DB API if key is available
        if config.sports_api_key:
            logger.info("Using The Sports DB API for real data")
            result = _fetch_real_sports_data(config.sports_api_key, teams)
        else:
            logger.warning("No Sports API key - using mock data")
            result = {
                'teams': _generate_mock_teams(teams),
                'timestamp': datetime.now().isoformat(),
                'source': 'Mock Sports Data (add SPORTS_API_KEY for real data)'
            }
        
        duration = metrics.stop_timer("tool.get_sports_scores", {"tool": "get_sports_scores", "type": "tool"})
        logger.info(
            "Sports scores fetched successfully",
            teams=teams,
            duration_ms=duration
        )
        
        return result
        
    except Exception as e:
        duration = metrics.stop_timer("tool.get_sports_scores", {"tool": "get_sports_scores", "type": "tool"})
        metrics.increment("tool.error", {"tool": "get_sports_scores"})
        
        logger.error(
            "Failed to fetch sports scores",
            exception=e,
            teams=teams,
            duration_ms=duration
        )
        
        # Return mock data on error
        return {
            'teams': _generate_mock_teams(teams),
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock Sports Data (API failed)',
            'error': str(e)
        }


def _fetch_real_sports_data(api_key: str, team_names: List[str]) -> Dict[str, Any]:
    """
    Fetch real sports data from The Sports DB API
    
    Args:
        api_key: The Sports DB API key
        team_names: List of team nicknames (e.g., ["49ers", "Warriors"])
    
    Returns:
        Dictionary with teams data
    """
    import requests
    
    # Team name mapping for API searches
    full_names = {
        '49ers': 'San Francisco 49ers',
        'Sharks': 'San Jose Sharks',
        'Warriors': 'Golden State Warriors'
    }
    
    teams_data = []
    
    for nickname in team_names:
        full_name = full_names.get(nickname, nickname)
        
        try:
            # Search for team by name
            search_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/searchteams.php"
            search_params = {'t': full_name}
            
            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            teams = data.get('teams', [])
            if not teams:
                logger.warning(f"No team found for {full_name}")
                continue
            
            team = teams[0]
            team_id = team.get('idTeam')
            league = team.get('strLeague', 'Unknown')
            
            # Get last 5 events for this team
            events_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventslast.php"
            events_params = {'id': team_id}
            
            events_response = requests.get(events_url, params=events_params, timeout=10)
            events_response.raise_for_status()
            events_data = events_response.json()
            
            events = events_data.get('results', [])
            
            # Find most recent completed game
            latest_game = "No recent games"
            if events:
                last_event = events[0]
                home_team = last_event.get('strHomeTeam', '')
                away_team = last_event.get('strAwayTeam', '')
                home_score = last_event.get('intHomeScore', '0')
                away_score = last_event.get('intAwayScore', '0')
                event_date = last_event.get('dateEvent', '')
                
                # Determine if won or lost
                is_home = full_name in home_team
                team_score = int(home_score) if is_home else int(away_score)
                opp_score = int(away_score) if is_home else int(home_score)
                opponent = away_team if is_home else home_team
                result = "W" if team_score > opp_score else "L"
                
                latest_game = f"{result} {team_score}-{opp_score} vs {opponent.split()[-1]} ({event_date})"
            
            # Get next event (The Sports DB free tier may not have this)
            next_game = "Schedule unavailable"
            
            # Calculate record from last 5 games (approximate)
            wins = sum(1 for e in events[:5] if _is_win(e, full_name))
            losses = len(events[:5]) - wins
            record = f"{wins}-{losses}"
            
            teams_data.append({
                'name': full_name,
                'league': league,
                'record': record,
                'latest_game': latest_game,
                'next_game': next_game,
                'standings': 'N/A'  # Free tier doesn't provide standings
            })
            
        except Exception as e:
            logger.warning(f"Failed to fetch data for {nickname}: {e}")
            continue
    
    return {
        'teams': teams_data,
        'timestamp': datetime.now().isoformat(),
        'source': 'The Sports DB API'
    }


def _is_win(event: dict, team_name: str) -> bool:
    """Check if event was a win for the team"""
    home_team = event.get('strHomeTeam', '')
    home_score = int(event.get('intHomeScore', 0))
    away_score = int(event.get('intAwayScore', 0))
    
    is_home = team_name in home_team
    team_score = home_score if is_home else away_score
    opp_score = away_score if is_home else home_score
    
    return team_score > opp_score


def _generate_mock_team_data(team_name: str) -> Dict[str, Any]:
    """
    Generate realistic mock data for a team
    (Replace with real API calls in production)
    """
    
    # Detect league from team name
    league_map = {
        "49ers": {"league": "NFL", "full_name": "San Francisco 49ers"},
        "sharks": {"league": "NHL", "full_name": "San Jose Sharks"},
        "warriors": {"league": "NBA", "full_name": "Golden State Warriors"}
    }
    
    team_key = team_name.lower()
    team_info = league_map.get(team_key, {"league": "Unknown", "full_name": team_name})
    
    # Generate realistic record
    wins = random.randint(5, 15)
    losses = random.randint(3, 12)
    
    # Generate recent game (realistic scores)
    yesterday = (datetime.now() - timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%d")
    team_score = random.randint(85, 120) if team_info["league"] == "NBA" else random.randint(17, 35)
    opponent_score = random.randint(85, 120) if team_info["league"] == "NBA" else random.randint(14, 31)
    
    result = "W" if team_score > opponent_score else "L"
    opponent = _get_random_opponent(team_info["league"])
    
    # Generate upcoming game
    next_game_date = (datetime.now() + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d")
    next_opponent = _get_random_opponent(team_info["league"])
    
    return {
        'name': team_info["full_name"],
        'league': team_info["league"],
        'record': f"{wins}-{losses}",
        'latest_game': f"{result} {team_score}-{opponent_score} vs {opponent} ({yesterday})",
        'next_game': f"vs {next_opponent} on {next_game_date}",
        'standings': f"#{random.randint(1, 8)} in division"
    }


def _get_random_opponent(league: str) -> str:
    """Get a random opponent based on league"""
    opponents = {
        "NFL": ["Rams", "Cardinals", "Seahawks", "Cowboys", "Packers"],
        "NHL": ["Kings", "Ducks", "Golden Knights", "Avalanche", "Canucks"],
        "NBA": ["Lakers", "Clippers", "Suns", "Kings", "Blazers"]
    }
    return random.choice(opponents.get(league, ["Opponent"]))


# ============================================================================
# Production Implementation Guide
# ============================================================================
"""
To implement with real APIs, replace _generate_mock_team_data() with:

1. The Sports DB (Free tier available):
   - API: https://www.thesportsdb.com/api.php
   - Endpoint: /api/v1/json/{API_KEY}/searchteams.php?t={team_name}
   - Get team ID, then fetch recent events

2. ESPN API (Unofficial):
   - Endpoint: http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard
   - Parse JSON for team schedules and scores

3. Official APIs:
   - NFL: https://api.sportsdata.io/
   - NBA: https://www.balldontlie.io/
   - NHL: https://statsapi.web.nhl.com/api/v1/

Example implementation with The Sports DB:

def _fetch_real_team_data(team_name: str, api_key: str) -> Dict[str, Any]:
    # Search for team
    search_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/searchteams.php"
    response = requests.get(search_url, params={'t': team_name}, timeout=10)
    teams = response.json().get('teams', [])
    
    if not teams:
        raise ValueError(f"Team '{team_name}' not found")
    
    team = teams[0]
    team_id = team['idTeam']
    
    # Get recent events
    events_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventslast.php"
    events_response = requests.get(events_url, params={'id': team_id}, timeout=10)
    events = events_response.json().get('results', [])
    
    # Parse and return structured data
    return {
        'name': team['strTeam'],
        'league': team['strLeague'],
        'record': f"{team.get('intWin', 0)}-{team.get('intLoss', 0)}",
        'latest_game': _parse_latest_event(events[0]) if events else "No recent games",
        'next_game': _fetch_next_game(team_id, api_key)
    }
"""
