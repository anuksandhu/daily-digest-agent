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
    from datetime import datetime
    
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
            
            # Get last 15 events for this team (to find recent completed games)
            events_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventslast.php"
            events_params = {'id': team_id}
            
            events_response = requests.get(events_url, params=events_params, timeout=10)
            events_response.raise_for_status()
            events_data = events_response.json()
            
            events = events_data.get('results', [])
            
            # Get next 15 events for upcoming games
            next_url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsnext.php"
            next_params = {'id': team_id}
            
            next_response = requests.get(next_url, params=next_params, timeout=10)
            next_response.raise_for_status()
            next_data = next_response.json()
            
            upcoming_events = next_data.get('events', [])
            
            # Find most recent completed game with scores
            latest_game = "No recent games"
            if events:
                for event in events:
                    home_score = event.get('intHomeScore')
                    away_score = event.get('intAwayScore')
                    
                    # Skip if game hasn't been played yet (no scores)
                    if home_score is None or away_score is None:
                        continue
                    
                    home_team = event.get('strHomeTeam', '')
                    away_team = event.get('strAwayTeam', '')
                    event_date = event.get('dateEvent', '')
                    
                    # Determine if won or lost
                    is_home = full_name in home_team
                    team_score = int(home_score) if is_home else int(away_score)
                    opp_score = int(away_score) if is_home else int(home_score)
                    opponent = away_team if is_home else home_team
                    opponent_short = opponent.split()[-1]  # Get last word (team name)
                    result = "W" if team_score > opp_score else "L" if team_score < opp_score else "T"
                    
                    latest_game = f"{result} {team_score}-{opp_score} vs {opponent_short} ({event_date})"
                    break  # Use first completed game found
            
            # Get next game
            next_game = "No upcoming games scheduled"
            if upcoming_events:
                next_event = upcoming_events[0]
                home_team = next_event.get('strHomeTeam', '')
                away_team = next_event.get('strAwayTeam', '')
                event_date = next_event.get('dateEvent', '')
                
                is_home = full_name in home_team
                opponent = away_team if is_home else home_team
                opponent_short = opponent.split()[-1]
                location = "vs" if is_home else "@"
                
                next_game = f"{location} {opponent_short} on {event_date}"
            
            # Calculate season record from all available results
            wins = 0
            losses = 0
            for event in events:
                home_score = event.get('intHomeScore')
                away_score = event.get('intAwayScore')
                
                if home_score is None or away_score is None:
                    continue
                
                home_team = event.get('strHomeTeam', '')
                is_home = full_name in home_team
                team_score = int(home_score) if is_home else int(away_score)
                opp_score = int(away_score) if is_home else int(home_score)
                
                if team_score > opp_score:
                    wins += 1
                elif team_score < opp_score:
                    losses += 1
            
            # record = f"{wins}-{losses}" if wins > 0 or losses > 0 else "N/A"
            record = "Season in progress"

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
    
    if not teams_data:
        # If all teams failed, return mock data
        return {
            'teams': _generate_mock_teams(team_names),
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock Sports Data (API failed for all teams)'
        }
    
    return {
        'teams': teams_data,
        'timestamp': datetime.now().isoformat(),
        'source': 'The Sports DB API'
    }


def _generate_mock_teams(team_names: List[str]) -> List[Dict[str, Any]]:
    """Generate mock team data"""
    league_map = {
        "49ers": {"league": "NFL", "full_name": "San Francisco 49ers"},
        "Sharks": {"league": "NHL", "full_name": "San Jose Sharks"},
        "Warriors": {"league": "NBA", "full_name": "Golden State Warriors"}
    }
    
    teams = []
    for name in team_names:
        team_info = league_map.get(name, {"league": "Unknown", "full_name": name})
        
        wins = random.randint(5, 15)
        losses = random.randint(3, 12)
        yesterday = (datetime.now() - timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%d")
        team_score = random.randint(85, 120) if team_info["league"] == "NBA" else random.randint(17, 35)
        opponent_score = random.randint(85, 120) if team_info["league"] == "NBA" else random.randint(14, 31)
        result = "W" if team_score > opponent_score else "L"
        
        teams.append({
            'name': team_info["full_name"],
            'league': team_info["league"],
            'record': f"{wins}-{losses}",
            'latest_game': f"{result} {team_score}-{opponent_score} vs Opponent ({yesterday})",
            'next_game': f"vs Opponent on {(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')}",
            'standings': f"#{random.randint(1, 8)} in division"
        })
    
    return teams
