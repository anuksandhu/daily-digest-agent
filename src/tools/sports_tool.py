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
    
    NOTE: This is a mock implementation. In production, replace with:
    - The Sports DB API (https://www.thesportsdb.com/)
    - ESPN API
    - Official team APIs
    
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
        teams_config = config.sports_teams
        teams = [
            teams_config.get("nfl", "49ers"),
            teams_config.get("nhl", "Sharks"),
            teams_config.get("nba", "Warriors")
        ]
    
    logger.info("Fetching sports scores", teams=teams)
    metrics.start_timer("tool.get_sports_scores")
    
    try:
        # Check if real API key is available
        if config.sports_api_key:
            logger.warning("Sports API key detected but not implemented yet - using mock data")
        
        # Mock data (replace with real API calls)
        result = {
            'teams': [],
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock Sports Data (replace with The Sports DB or ESPN API)'
        }
        
        # Generate realistic mock data for each team
        for team_name in teams:
            team_data = _generate_mock_team_data(team_name)
            result['teams'].append(team_data)
        
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
        
        return {
            'error': str(e),
            'teams': teams,
            'timestamp': datetime.now().isoformat(),
            'source': 'Sports API (failed)'
        }


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
