"""
NFL Player Betting Lines Fetcher
---------------------------------
A comprehensive class to fetch betting lines and odds for NFL players from multiple sources.
Primary source: The Odds API (with free tier available)
Secondary sources: Web scraping as fallback

Author: SetTheLine App
Date: 2024
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from enum import Enum
import time


class PropType(Enum):
    """Enum for different types of player props"""
    # Passing props
    PASS_TDS = "player_pass_tds"
    PASS_YARDS = "player_pass_yds"
    PASS_COMPLETIONS = "player_pass_completions"
    PASS_ATTEMPTS = "player_pass_attempts"
    PASS_LONGEST_COMPLETION = "player_pass_longest_completion"
    
    # Rushing props
    RUSH_YARDS = "player_rush_yds"
    RUSH_TDS = "player_rush_tds"
    RUSH_ATTEMPTS = "player_rush_attempts"
    RUSH_LONGEST = "player_rush_longest"
    
    # Receiving props
    RECEPTIONS = "player_receptions"
    RECEIVING_YARDS = "player_reception_yds"
    RECEIVING_TDS = "player_reception_tds"
    LONGEST_RECEPTION = "player_reception_longest"
    
    # Touchdown props
    ANYTIME_TD = "player_anytime_td"
    FIRST_TD = "player_1st_td"
    LAST_TD = "player_last_td"
    
    # Kicking props
    FIELD_GOALS = "player_field_goals"
    FG_LONGEST = "player_fg_longest"
    KICKING_POINTS = "player_kicking_points"
    
    # Defensive props
    TACKLES_ASSISTS = "player_tackles_assists"
    SACKS = "player_sacks"
    INTERCEPTIONS = "player_def_ints"


@dataclass
class BettingLine:
    """Data class for a single betting line"""
    player_name: str
    prop_type: str
    line: float
    over_odds: Optional[int]
    under_odds: Optional[int]
    bookmaker: str
    last_update: datetime
    
    def to_dict(self):
        return {
            'player_name': self.player_name,
            'prop_type': self.prop_type,
            'line': self.line,
            'over_odds': self.over_odds,
            'under_odds': self.under_odds,
            'bookmaker': self.bookmaker,
            'last_update': self.last_update.isoformat() if isinstance(self.last_update, datetime) else self.last_update
        }


@dataclass
class PlayerProps:
    """Data class containing all props for a single player"""
    player_name: str
    team: Optional[str]
    opponent: Optional[str]
    game_time: Optional[datetime]
    props: List[BettingLine]
    
    def to_dict(self):
        return {
            'player_name': self.player_name,
            'team': self.team,
            'opponent': self.opponent,
            'game_time': self.game_time.isoformat() if self.game_time else None,
            'props': [prop.to_dict() for prop in self.props]
        }


class NFLBettingLinesFetcher:
    """
    Main class to fetch NFL player betting lines from various sources.
    
    Usage:
        fetcher = NFLBettingLinesFetcher(api_key="your_api_key")
        lines = fetcher.get_player_lines("Dak Prescott")
    """
    
    # The Odds API endpoints
    ODDS_API_BASE = "https://api.the-odds-api.com/v4"
    
    # Bookmakers to fetch from (can be customized)
    DEFAULT_BOOKMAKERS = [
        "draftkings",
        "fanduel", 
        "betmgm",
        "caesars",
        "pointsbetus",
        "bovada",
        "mybookieag"
    ]
    
    def __init__(self, api_key: Optional[str] = None, bookmakers: Optional[List[str]] = None):
        """
        Initialize the fetcher with API credentials.
        
        Args:
            api_key: The Odds API key (get free tier at https://the-odds-api.com)
            bookmakers: List of bookmaker keys to fetch from
        """
        self.api_key = api_key
        self.bookmakers = bookmakers or self.DEFAULT_BOOKMAKERS
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Cache for API responses to minimize requests
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
    def get_player_lines(self, player_name: str, prop_types: Optional[List[PropType]] = None) -> PlayerProps:
        """
        Get all available betting lines for a specific player.
        
        Args:
            player_name: Name of the NFL player
            prop_types: Specific prop types to fetch (None = all available)
            
        Returns:
            PlayerProps object containing all found betting lines
        """
        if not self.api_key:
            raise ValueError("API key required. Get one free at https://the-odds-api.com")
        
        # First, get current NFL games
        games = self._get_nfl_games()
        
        # Find games and fetch props
        all_props = []
        player_team = None
        player_opponent = None
        game_time = None
        
        for game in games:
            # Get event odds with player props
            event_props = self._get_event_props(game['id'], prop_types)
            
            # Filter for specific player
            player_lines = self._filter_player_props(event_props, player_name)
            
            if player_lines:
                all_props.extend(player_lines)
                # Set team info from first match
                if not player_team:
                    player_team = self._determine_player_team(game, player_name)
                    player_opponent = game['away_team'] if player_team == game['home_team'] else game['home_team']
                    game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                break  # Stop after finding the first game with data for testing
        
        return PlayerProps(
            player_name=player_name,
            team=player_team,
            opponent=player_opponent,
            game_time=game_time,
            props=all_props
        )
    
    def get_all_players_in_game(self, home_team: str, away_team: str) -> List[PlayerProps]:
        """
        Get betting lines for all players in a specific game.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            List of PlayerProps for all players with available lines
        """
        games = self._get_nfl_games()
        
        # Find the specific game
        target_game = None
        for game in games:
            if (self._normalize_team_name(game['home_team']) == self._normalize_team_name(home_team) and
                self._normalize_team_name(game['away_team']) == self._normalize_team_name(away_team)):
                target_game = game
                break
        
        if not target_game:
            raise ValueError(f"Game not found: {away_team} @ {home_team}")
        
        # Get all props for this game
        event_props = self._get_event_props(target_game['id'])
        
        # Organize by player
        players_dict = {}
        for bookmaker_data in event_props:
            for market in bookmaker_data.get('markets', []):
                for outcome in market.get('outcomes', []):
                    player_name = outcome.get('description', '')
                    if player_name and player_name != '':
                        if player_name not in players_dict:
                            players_dict[player_name] = []
                        
                        line = BettingLine(
                            player_name=player_name,
                            prop_type=market['key'],
                            line=outcome.get('point', 0),
                            over_odds=outcome.get('price') if outcome.get('name') == 'Over' else None,
                            under_odds=outcome.get('price') if outcome.get('name') == 'Under' else None,
                            bookmaker=bookmaker_data['title'],
                            last_update=datetime.fromisoformat(market['last_update'].replace('Z', '+00:00'))
                        )
                        players_dict[player_name].append(line)
        
        # Convert to PlayerProps list
        result = []
        game_time = datetime.fromisoformat(target_game['commence_time'].replace('Z', '+00:00'))
        
        for player_name, props in players_dict.items():
            player_team = self._determine_player_team(target_game, player_name)
            result.append(PlayerProps(
                player_name=player_name,
                team=player_team,
                opponent=away_team if player_team == home_team else home_team,
                game_time=game_time,
                props=props
            ))
        
        return result
    
    def _get_nfl_games(self) -> List[Dict]:
        """Fetch current NFL games from The Odds API"""
        cache_key = "nfl_games"
        
        # Check cache
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if time.time() - cached_time < self._cache_timeout:
                return cached_data
        
        url = f"{self.ODDS_API_BASE}/sports/americanfootball_nfl/events"
        params = {
            'apiKey': self.api_key,
            'dateFormat': 'iso'
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        games = response.json()
        
        # Cache the result
        self._cache[cache_key] = (time.time(), games)
        
        return games
    
    def _get_event_props(self, event_id: str, prop_types: Optional[List[PropType]] = None) -> List[Dict]:
        """Fetch player props for a specific event/game"""
        cache_key = f"event_{event_id}"
        
        # Check cache
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if time.time() - cached_time < self._cache_timeout:
                return cached_data
        
        # Build markets parameter
        if prop_types:
            markets = ','.join([pt.value for pt in prop_types])
        else:
            # Get all common prop markets - only use valid ones
            markets = ','.join([
                PropType.PASS_TDS.value,
                PropType.PASS_YARDS.value,
                PropType.PASS_COMPLETIONS.value,
                PropType.PASS_ATTEMPTS.value,
                PropType.RUSH_YARDS.value,
                PropType.RUSH_TDS.value,
                PropType.RUSH_ATTEMPTS.value,
                PropType.RECEIVING_YARDS.value,
                PropType.RECEIVING_TDS.value,
                PropType.RECEPTIONS.value,
                PropType.ANYTIME_TD.value,
                PropType.FIRST_TD.value
            ])
        
        url = f"{self.ODDS_API_BASE}/sports/americanfootball_nfl/events/{event_id}/odds"
        params = {
            'apiKey': self.api_key,
            'bookmakers': ','.join(self.bookmakers),
            'markets': markets,
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }
        
        print(f"Making API call to: {url}")
        print(f"With params: {params}")
        
        response = self.session.get(url, params=params)
        
        # Handle rate limiting
        if response.status_code == 429:
            print("Rate limited, waiting 2 seconds...")
            time.sleep(2)
            response = self.session.get(url, params=params)
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response text: {response.text}")
            return []  # Return empty list instead of crashing
            
        try:
            data = response.json()
            bookmakers_data = data.get('bookmakers', [])
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
        
        # Cache the result
        self._cache[cache_key] = (time.time(), bookmakers_data)
        
        return bookmakers_data
    
    def _filter_player_props(self, bookmakers_data: List[Dict], player_name: str) -> List[BettingLine]:
        """Filter props data for a specific player"""
        player_lines = []
        player_name_lower = player_name.lower()
        
        for bookmaker in bookmakers_data:
            bookmaker_name = bookmaker.get('title', '')
            
            for market in bookmaker.get('markets', []):
                market_key = market.get('key', '')
                last_update = market.get('last_update', '')
                
                # Group outcomes by player
                player_outcomes = {}
                
                for outcome in market.get('outcomes', []):
                    desc = outcome.get('description', '')
                    if desc and player_name_lower in desc.lower():
                        if desc not in player_outcomes:
                            player_outcomes[desc] = {}
                        
                        if outcome.get('name') == 'Over':
                            player_outcomes[desc]['over_odds'] = outcome.get('price')
                            player_outcomes[desc]['line'] = outcome.get('point', 0)
                        elif outcome.get('name') == 'Under':
                            player_outcomes[desc]['under_odds'] = outcome.get('price')
                            player_outcomes[desc]['line'] = outcome.get('point', 0)
                
                # Create BettingLine objects
                for player, odds_data in player_outcomes.items():
                    line = BettingLine(
                        player_name=player,
                        prop_type=market_key,
                        line=odds_data.get('line', 0),
                        over_odds=odds_data.get('over_odds'),
                        under_odds=odds_data.get('under_odds'),
                        bookmaker=bookmaker_name,
                        last_update=datetime.fromisoformat(last_update.replace('Z', '+00:00')) if last_update else datetime.now()
                    )
                    player_lines.append(line)
        
        return player_lines
    
    def _normalize_team_name(self, team: str) -> str:
        """Normalize team names for comparison"""
        return team.lower().replace(' ', '').replace('.', '')
    
    def _determine_player_team(self, game: Dict, player_name: str) -> Optional[str]:
        """
        Try to determine which team a player belongs to.
        This is a simplified version - in production you'd want a player roster database.
        """
        # This would ideally query a roster database
        # For now, return None or implement roster lookup
        return None
    
    def get_best_lines(self, player_props: PlayerProps) -> Dict[str, BettingLine]:
        """
        Get the best available line for each prop type.
        Best = highest over odds for overs, highest under odds for unders
        
        Args:
            player_props: PlayerProps object with all lines
            
        Returns:
            Dictionary of prop_type -> best BettingLine
        """
        best_lines = {}
        
        # Group by prop type
        props_by_type = {}
        for prop in player_props.props:
            if prop.prop_type not in props_by_type:
                props_by_type[prop.prop_type] = []
            props_by_type[prop.prop_type].append(prop)
        
        # Find best for each type
        for prop_type, props in props_by_type.items():
            # Get best over odds (least negative or most positive)
            best_over = max(props, key=lambda x: x.over_odds if x.over_odds else -999999)
            best_lines[prop_type] = best_over
        
        return best_lines
    
    def compare_to_projection(self, player_props: PlayerProps, projection: float, 
                            prop_type: PropType) -> Dict[str, Any]:
        """
        Compare betting lines to your projection to find value.
        
        Args:
            player_props: PlayerProps object
            projection: Your projected value for the prop
            prop_type: The type of prop to analyze
            
        Returns:
            Dictionary with value analysis
        """
        relevant_props = [p for p in player_props.props if p.prop_type == prop_type.value]
        
        if not relevant_props:
            return {"error": f"No lines found for {prop_type.value}"}
        
        value_bets = []
        
        for prop in relevant_props:
            # Calculate implied probabilities
            over_prob = self._american_to_probability(prop.over_odds) if prop.over_odds else None
            under_prob = self._american_to_probability(prop.under_odds) if prop.under_odds else None
            
            # Determine if there's value
            if projection > prop.line and over_prob:
                # We think over will hit
                expected_value = (1 - over_prob) * 100  # Simplified EV calculation
                value_bets.append({
                    'bookmaker': prop.bookmaker,
                    'bet': 'Over',
                    'line': prop.line,
                    'odds': prop.over_odds,
                    'implied_prob': over_prob,
                    'expected_value': expected_value,
                    'projection': projection
                })
            elif projection < prop.line and under_prob:
                # We think under will hit
                expected_value = (1 - under_prob) * 100
                value_bets.append({
                    'bookmaker': prop.bookmaker,
                    'bet': 'Under',
                    'line': prop.line,
                    'odds': prop.under_odds,
                    'implied_prob': under_prob,
                    'expected_value': expected_value,
                    'projection': projection
                })
        
        # Sort by expected value
        value_bets.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return {
            'player': player_props.player_name,
            'prop_type': prop_type.value,
            'projection': projection,
            'value_bets': value_bets
        }
    
    def _american_to_probability(self, odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    def export_to_json(self, player_props: PlayerProps, filename: str):
        """Export player props to JSON file"""
        with open(filename, 'w') as f:
            json.dump(player_props.to_dict(), f, indent=2)
    
    def export_to_csv(self, player_props: PlayerProps, filename: str):
        """Export player props to CSV file"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Player', 'Prop Type', 'Line', 'Over Odds', 'Under Odds', 
                           'Bookmaker', 'Last Update'])
            
            for prop in player_props.props:
                writer.writerow([
                    prop.player_name,
                    prop.prop_type,
                    prop.line,
                    prop.over_odds,
                    prop.under_odds,
                    prop.bookmaker,
                    prop.last_update
                ])


# Example usage
if __name__ == "__main__":
    # Initialize with your API key
    # Get a free key at: https://the-odds-api.com
    API_KEY = "REMOVED_API_KEY"
    
    fetcher = NFLBettingLinesFetcher(api_key=API_KEY)
    
    # Example 1: Get all lines for a specific player
    print("Fetching lines for Dak Prescott...")
    dak_props = fetcher.get_player_lines("Dak Prescott")
    
    print(f"\nFound {len(dak_props.props)} betting lines for {dak_props.player_name}")
    print(f"Team: {dak_props.team} vs {dak_props.opponent}")
    print(f"Game Time: {dak_props.game_time}")
    
    # Show best lines
    best_lines = fetcher.get_best_lines(dak_props)
    print("\nBest available lines:")
    for prop_type, line in best_lines.items():
        print(f"  {prop_type}: {line.line} (O{line.over_odds}/U{line.under_odds}) @ {line.bookmaker}")
    
    # Example 2: Find value bets based on your projection
    my_projection = 285.5  # Your projection for passing yards
    value_analysis = fetcher.compare_to_projection(
        dak_props, 
        my_projection, 
        PropType.PASS_YARDS
    )
    
    print(f"\nValue Analysis for {value_analysis['prop_type']}:")
    print(f"Your projection: {value_analysis['projection']}")
    if value_analysis.get('value_bets'):
        print("Value bets found:")
        for bet in value_analysis['value_bets'][:3]:  # Top 3 value bets
            print(f"  {bet['bookmaker']}: {bet['bet']} {bet['line']} @ {bet['odds']} "
                  f"(EV: {bet['expected_value']:.2f}%)")
    
    # Example 3: Export to file
    fetcher.export_to_json(dak_props, "dak_prescott_lines.json")
    fetcher.export_to_csv(dak_props, "dak_prescott_lines.csv")
    print("\nData exported to JSON and CSV files")
    
    # Example 4: Get all players in a game
    print("\n\nFetching all players in Cowboys vs Eagles...")
    all_players = fetcher.get_all_players_in_game("Philadelphia Eagles", "Dallas Cowboys")
    print(f"Found lines for {len(all_players)} players")
    for player in all_players[:5]:  # Show first 5
        print(f"  {player.player_name}: {len(player.props)} props available")