"""
Fantasy Edge - NFL Player Analysis & Lineup Optimization
--------------------------------------------------------
A comprehensive system to fetch betting lines and convert them into fantasy football
projections for optimal lineup decisions. Uses betting market data to project 
fantasy performance and compare players based on league scoring settings.

Primary source: The Odds API (with free tier available)
Focus: Fantasy football lineup optimization and player comparisons

Author: FantasyEdge
Date: 2024-2025
"""

import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from enum import Enum
import time
import os
import sys

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load immediately when module is imported
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")


class ProgressBar:
    """Simple progress bar for terminal"""
    def __init__(self, total, description="Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.width = 40
        
    def update(self, increment=1):
        self.current += increment
        self._display()
        
    def _display(self):
        if self.total == 0:
            return
            
        progress = self.current / self.total
        filled = int(self.width * progress)
        bar = "█" * filled + "░" * (self.width - filled)
        percent = int(progress * 100)
        
        sys.stdout.write(f"\r{self.description}: [{bar}] {percent}% ({self.current}/{self.total})")
        sys.stdout.flush()
        
        if self.current >= self.total:
            print()  # New line when complete


class Position(Enum):
    """Enum for fantasy football positions"""
    QB = "QB"
    RB = "RB" 
    WR = "WR"
    TE = "TE"
    K = "K"
    DST = "DST"


class PropType(Enum):
    """Enum for different types of player props that affect fantasy scoring"""
    # Passing props
    PASS_TDS = "player_pass_tds"
    PASS_YARDS = "player_pass_yds"
    PASS_COMPLETIONS = "player_pass_completions"
    PASS_ATTEMPTS = "player_pass_attempts"
    PASS_LONGEST_COMPLETION = "player_pass_longest_completion"
    PASS_INTERCEPTIONS = "player_pass_interceptions"
    
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
class FantasyScoring:
    """Data class for fantasy league scoring settings"""
    # Passing
    pass_yards_per_point: float = 25.0  # 1 point per 25 yards
    pass_td_points: float = 4.0
    pass_interception_points: float = -2.0
    pass_completion_points: float = 0.0
    
    # Rushing
    rush_yards_per_point: float = 10.0  # 1 point per 10 yards
    rush_td_points: float = 6.0
    
    # Receiving
    reception_points: float = 1.0  # PPR scoring
    receiving_yards_per_point: float = 10.0
    receiving_td_points: float = 6.0
    
    # Kicking
    fg_points: float = 3.0
    extra_point_points: float = 1.0
    
    # Bonuses
    long_td_bonus: float = 0.0  # Bonus for 40+ yard TDs
    long_pass_bonus: float = 0.0  # Bonus for 300+ passing yards
    long_rush_bonus: float = 0.0  # Bonus for 100+ rushing yards
    long_receiving_bonus: float = 0.0  # Bonus for 100+ receiving yards
    
    def to_dict(self):
        return asdict(self)


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
class FantasyProjection:
    """Data class for fantasy projections derived from betting lines"""
    player_name: str
    position: Position
    projected_points: float
    confidence: float  # 0-1 scale based on line consensus
    breakdown: Dict[str, float]  # Points breakdown by category
    
    def to_dict(self):
        return {
            'player_name': self.player_name,
            'position': self.position.value if self.position else None,
            'projected_points': self.projected_points,
            'confidence': self.confidence,
            'breakdown': self.breakdown
        }


@dataclass
class PlayerRosterInfo:
    """Data class for player roster information"""
    player_name: str
    position: Position
    team: str
    opponent: str
    game_time: datetime
    is_available: bool = True  # Whether player is on your roster/available
    salary: Optional[int] = None  # For DFS
    ownership_projection: Optional[float] = None  # For DFS
    
    def to_dict(self):
        return {
            'player_name': self.player_name,
            'position': self.position.value if self.position else None,
            'team': self.team,
            'opponent': self.opponent,
            'game_time': self.game_time.isoformat() if self.game_time else None,
            'is_available': self.is_available,
            'salary': self.salary,
            'ownership_projection': self.ownership_projection
        }


@dataclass
class PlayerProps:
    """Data class containing all props and fantasy analysis for a single player"""
    player_name: str
    position: Optional[Position]
    roster_info: Optional[PlayerRosterInfo]
    betting_lines: List[BettingLine]
    fantasy_projection: Optional[FantasyProjection]
    
    def to_dict(self):
        return {
            'player_name': self.player_name,
            'position': self.position.value if self.position else None,
            'roster_info': self.roster_info.to_dict() if self.roster_info else None,
            'betting_lines': [line.to_dict() for line in self.betting_lines],
            'fantasy_projection': self.fantasy_projection.to_dict() if self.fantasy_projection else None
        }


class FantasyEdgeAnalyzer:
    """
    Main class to fetch NFL player betting lines and convert them into fantasy projections
    for optimal lineup decisions and player comparisons.
    
    Usage:
        # API key will be loaded from .env file automatically
        analyzer = FantasyEdgeAnalyzer()
        
        # Set your league scoring
        scoring = FantasyScoring(reception_points=0.5)  # Half PPR
        analyzer.set_scoring(scoring)
        
        # Compare two players
        comparison = analyzer.compare_players("Josh Allen", "Lamar Jackson")
        
        # Get optimal lineup from your roster
        roster = ["Josh Allen", "Saquon Barkley", "Tyreek Hill", ...]
        lineup = analyzer.optimize_lineup(roster)
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
        Initialize the analyzer with API credentials.
        
        Args:
            api_key: The Odds API key (get free tier at https://the-odds-api.com).
                     If not provided, will attempt to load from ODDS_API_KEY environment variable.
            bookmakers: List of bookmaker keys to fetch from
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        
        # Debug: Print what we found (only show partial key for security)
        if self.api_key:
            print(f"✅ API key loaded: {self.api_key[:8]}..." + "*" * (len(self.api_key) - 8))
        else:
            print("❌ No API key found in environment or parameter")
            
        self.bookmakers = bookmakers or self.DEFAULT_BOOKMAKERS
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Cache for API responses to minimize requests
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
        # Default scoring system (can be updated)
        self.scoring = FantasyScoring()
        
        # Player position mapping (would ideally come from a database)
        self.position_map = self._load_position_map()
        
    def set_scoring(self, scoring: FantasyScoring):
        """Update the fantasy scoring settings"""
        self.scoring = scoring
        
    def _load_position_map(self) -> Dict[str, Position]:
        """
        Load player position mapping. In production, this would come from a database.
        For now, return a basic mapping that can be expanded.
        """
        # This is a simplified version - in production you'd have a complete player database
        return {
            # QBs
            "Josh Allen": Position.QB,
            "Lamar Jackson": Position.QB, 
            "Dak Prescott": Position.QB,
            "Patrick Mahomes": Position.QB,
            "Joe Burrow": Position.QB,
            "Justin Herbert": Position.QB,
            
            # RBs
            "Saquon Barkley": Position.RB,
            "Christian McCaffrey": Position.RB,
            "Derrick Henry": Position.RB,
            "Alvin Kamara": Position.RB,
            "Jonathan Taylor": Position.RB,
            "James Conner": Position.RB,
            "Keontay Johnson": Position.RB,
            "Bucky Robinson": Position.RB,
            
            # WRs
            "Tyreek Hill": Position.WR,
            "Davante Adams": Position.WR,
            "Cooper Kupp": Position.WR,
            "Stefon Diggs": Position.WR,
            "CeeDee Lamb": Position.WR,
            "Tee Higgins": Position.WR,
            "DK Metcalf": Position.WR,
            "DeVonta Smith": Position.WR,
            "Darnell Mooney": Position.WR,
            "Jaylen Waddle": Position.WR,
            "Mike Evans": Position.WR,
            
            # TEs
            "Travis Kelce": Position.TE,
            "Mark Andrews": Position.TE,
            "George Kittle": Position.TE,
            "Jaylen Smith": Position.TE,
        }
        
    def get_player_analysis(self, player_name: str, prop_types: Optional[List[PropType]] = None) -> PlayerProps:
        """
        Get comprehensive fantasy analysis for a specific player including betting lines and projections.
        
        Args:
            player_name: Name of the NFL player
            prop_types: Specific prop types to fetch (None = all available)
            
        Returns:
            PlayerProps object containing betting lines and fantasy projections
        """
        if not self.api_key:
            raise ValueError("API key required. Get one free at https://the-odds-api.com")
        
        print(f"🔍 Analyzing {player_name}...")
        
        # Get betting lines (using existing logic)
        games = self._get_nfl_games()
        all_props = []
        player_team = None
        player_opponent = None
        game_time = None
        
        # Progress bar for game analysis
        progress = ProgressBar(len(games), f"Searching for {player_name}")
        
        for game in games:
            progress.update()
            event_props = self._get_event_props(game['id'], prop_types)
            player_lines = self._filter_player_props(event_props, player_name)
            
            if player_lines:
                all_props.extend(player_lines)
                if not player_team:
                    player_team = self._determine_player_team(game, player_name)
                    player_opponent = game['away_team'] if player_team == game['home_team'] else game['home_team']
                    game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                break
        
        # Get player position
        position = self.position_map.get(player_name)
        
        # Create roster info
        roster_info = PlayerRosterInfo(
            player_name=player_name,
            position=position,
            team=player_team or "Unknown",
            opponent=player_opponent or "Unknown", 
            game_time=game_time or datetime.now()
        ) if player_team else None
        
        # Generate fantasy projection
        fantasy_projection = self._generate_fantasy_projection(player_name, position, all_props)
        
        return PlayerProps(
            player_name=player_name,
            position=position,
            roster_info=roster_info,
            betting_lines=all_props,
            fantasy_projection=fantasy_projection
        )
    
    def compare_players(self, player1_name: str, player2_name: str) -> Dict[str, Any]:
        """
        Compare two players and determine which is the better fantasy play.
        
        Args:
            player1_name: Name of first player
            player2_name: Name of second player
            
        Returns:
            Dictionary with comparison analysis
        """
        player1 = self.get_player_analysis(player1_name)
        player2 = self.get_player_analysis(player2_name)
        
        if not player1.fantasy_projection or not player2.fantasy_projection:
            return {"error": "Could not generate projections for one or both players"}
        
        proj1 = player1.fantasy_projection
        proj2 = player2.fantasy_projection
        
        # Calculate advantage
        point_advantage = proj1.projected_points - proj2.projected_points
        confidence_advantage = proj1.confidence - proj2.confidence
        
        # Determine recommendation
        if abs(point_advantage) < 1.0:
            recommendation = "Very close - consider other factors"
        elif point_advantage > 0:
            recommendation = f"Start {player1_name} (+{point_advantage:.2f} projected points)"
        else:
            recommendation = f"Start {player2_name} (+{abs(point_advantage):.2f} projected points)"
        
        return {
            'player1': player1.to_dict(),
            'player2': player2.to_dict(),
            'point_advantage': point_advantage,
            'confidence_advantage': confidence_advantage,
            'recommendation': recommendation,
            'analysis': {
                'closer_player': player1_name if point_advantage > 0 else player2_name,
                'point_difference': abs(point_advantage),
                'confidence_difference': abs(confidence_advantage)
            }
        }
    
    def optimize_lineup(self, roster_players: List[str], lineup_requirements: Optional[Dict[Position, int]] = None) -> Dict[str, Any]:
        """
        Optimize fantasy lineup from available roster players.
        
        Args:
            roster_players: List of player names on your roster
            lineup_requirements: Dictionary of position requirements (e.g., {Position.QB: 1, Position.RB: 2})
            
        Returns:
            Dictionary with optimal lineup and analysis
        """
        if not lineup_requirements:
            # Default lineup requirements (standard fantasy)
            lineup_requirements = {
                Position.QB: 1,
                Position.RB: 2, 
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1
            }
        
        print(f"🎯 Optimizing lineup from {len(roster_players)} players...")
        
        # Get analysis for all roster players
        player_analyses = {}
        progress = ProgressBar(len(roster_players), "Analyzing roster")
        
        for player_name in roster_players:
            progress.update()
            try:
                analysis = self.get_player_analysis(player_name)
                if analysis.fantasy_projection:
                    player_analyses[player_name] = analysis
            except Exception as e:
                print(f"\n⚠️  Could not analyze {player_name}: {e}")
                continue
        
        # Group by position
        players_by_position = {}
        for player_name, analysis in player_analyses.items():
            position = analysis.position
            if position not in players_by_position:
                players_by_position[position] = []
            players_by_position[position].append(analysis)
        
        # Sort each position by projected points
        for position in players_by_position:
            players_by_position[position].sort(
                key=lambda x: x.fantasy_projection.projected_points if x.fantasy_projection else 0,
                reverse=True
            )
        
        # Build optimal lineup
        optimal_lineup = {}
        total_projected_points = 0
        
        for position, required_count in lineup_requirements.items():
            if position in players_by_position:
                selected = players_by_position[position][:required_count]
                optimal_lineup[position] = selected
                total_projected_points += sum(
                    p.fantasy_projection.projected_points if p.fantasy_projection else 0
                    for p in selected
                )
        
        return {
            'optimal_lineup': {pos.value: [p.player_name for p in players] 
                             for pos, players in optimal_lineup.items()},
            'total_projected_points': total_projected_points,
            'lineup_details': {pos.value: [p.to_dict() for p in players] 
                             for pos, players in optimal_lineup.items()},
            'bench_players': {pos.value: [p.player_name for p in players[lineup_requirements.get(pos, 0):]] 
                            for pos, players in players_by_position.items() if pos in lineup_requirements}
        }
    
    def _generate_fantasy_projection(self, player_name: str, position: Optional[Position], 
                                   betting_lines: List[BettingLine]) -> Optional[FantasyProjection]:
        """
        Convert betting lines into fantasy point projections based on scoring settings.
        """
        if not betting_lines or not position:
            return None
        
        # Get consensus lines (average across bookmakers for each prop)
        consensus_lines = self._get_consensus_lines(betting_lines)
        
        projected_points = 0.0
        breakdown = {}
        confidence_scores = []
        
        # Convert each prop to fantasy points based on position
        if position == Position.QB:
            projected_points, breakdown, confidence_scores = self._project_qb_points(consensus_lines)
        elif position == Position.RB:
            projected_points, breakdown, confidence_scores = self._project_rb_points(consensus_lines)
        elif position == Position.WR:
            projected_points, breakdown, confidence_scores = self._project_wr_points(consensus_lines)
        elif position == Position.TE:
            projected_points, breakdown, confidence_scores = self._project_te_points(consensus_lines)
        
        # Calculate overall confidence (average of individual prop confidences)
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        return FantasyProjection(
            player_name=player_name,
            position=position,
            projected_points=projected_points,
            confidence=overall_confidence,
            breakdown=breakdown
        )
    
    def _get_consensus_lines(self, betting_lines: List[BettingLine]) -> Dict[str, float]:
        """Get consensus lines by averaging across bookmakers for each prop type"""
        prop_lines = {}
        
        for line in betting_lines:
            if line.prop_type not in prop_lines:
                prop_lines[line.prop_type] = []
            prop_lines[line.prop_type].append(line.line)
        
        # Return average line for each prop
        return {prop: sum(lines) / len(lines) for prop, lines in prop_lines.items()}
    
    def _project_qb_points(self, consensus_lines: Dict[str, float]) -> Tuple[float, Dict[str, float], List[float]]:
        """Project fantasy points for QB position"""
        points = 0.0
        breakdown = {}
        confidence_scores = []
        
        # Passing yards
        if PropType.PASS_YARDS.value in consensus_lines:
            yards = consensus_lines[PropType.PASS_YARDS.value]
            yard_points = yards / self.scoring.pass_yards_per_point
            points += yard_points
            breakdown['passing_yards'] = yard_points
            confidence_scores.append(0.8)  # High confidence for yards props
        
        # Passing TDs
        if PropType.PASS_TDS.value in consensus_lines:
            tds = consensus_lines[PropType.PASS_TDS.value]
            td_points = tds * self.scoring.pass_td_points
            points += td_points
            breakdown['passing_tds'] = td_points
            confidence_scores.append(0.7)
        
        # Rushing yards (for mobile QBs)
        if PropType.RUSH_YARDS.value in consensus_lines:
            rush_yards = consensus_lines[PropType.RUSH_YARDS.value]
            rush_points = rush_yards / self.scoring.rush_yards_per_point
            points += rush_points
            breakdown['rushing_yards'] = rush_points
            confidence_scores.append(0.6)
        
        # Rushing TDs
        if PropType.RUSH_TDS.value in consensus_lines:
            rush_tds = consensus_lines[PropType.RUSH_TDS.value]
            rush_td_points = rush_tds * self.scoring.rush_td_points
            points += rush_td_points
            breakdown['rushing_tds'] = rush_td_points
            confidence_scores.append(0.5)
        
        return points, breakdown, confidence_scores
    
    def _project_rb_points(self, consensus_lines: Dict[str, float]) -> Tuple[float, Dict[str, float], List[float]]:
        """Project fantasy points for RB position"""
        points = 0.0
        breakdown = {}
        confidence_scores = []
        
        # Rushing yards
        if PropType.RUSH_YARDS.value in consensus_lines:
            yards = consensus_lines[PropType.RUSH_YARDS.value]
            yard_points = yards / self.scoring.rush_yards_per_point
            points += yard_points
            breakdown['rushing_yards'] = yard_points
            confidence_scores.append(0.8)
        
        # Rushing TDs
        if PropType.RUSH_TDS.value in consensus_lines:
            tds = consensus_lines[PropType.RUSH_TDS.value]
            td_points = tds * self.scoring.rush_td_points
            points += td_points
            breakdown['rushing_tds'] = td_points
            confidence_scores.append(0.6)
        
        # Receiving (for pass-catching RBs)
        if PropType.RECEPTIONS.value in consensus_lines:
            receptions = consensus_lines[PropType.RECEPTIONS.value]
            rec_points = receptions * self.scoring.reception_points
            points += rec_points
            breakdown['receptions'] = rec_points
            confidence_scores.append(0.7)
        
        if PropType.RECEIVING_YARDS.value in consensus_lines:
            rec_yards = consensus_lines[PropType.RECEIVING_YARDS.value]
            rec_yard_points = rec_yards / self.scoring.receiving_yards_per_point
            points += rec_yard_points
            breakdown['receiving_yards'] = rec_yard_points
            confidence_scores.append(0.7)
        
        return points, breakdown, confidence_scores
    
    def _project_wr_points(self, consensus_lines: Dict[str, float]) -> Tuple[float, Dict[str, float], List[float]]:
        """Project fantasy points for WR position"""
        points = 0.0
        breakdown = {}
        confidence_scores = []
        
        # Receptions
        if PropType.RECEPTIONS.value in consensus_lines:
            receptions = consensus_lines[PropType.RECEPTIONS.value]
            rec_points = receptions * self.scoring.reception_points
            points += rec_points
            breakdown['receptions'] = rec_points
            confidence_scores.append(0.8)
        
        # Receiving yards
        if PropType.RECEIVING_YARDS.value in consensus_lines:
            yards = consensus_lines[PropType.RECEIVING_YARDS.value]
            yard_points = yards / self.scoring.receiving_yards_per_point
            points += yard_points
            breakdown['receiving_yards'] = yard_points
            confidence_scores.append(0.8)
        
        # Receiving TDs
        if PropType.RECEIVING_TDS.value in consensus_lines:
            tds = consensus_lines[PropType.RECEIVING_TDS.value]
            td_points = tds * self.scoring.receiving_td_points
            points += td_points
            breakdown['receiving_tds'] = td_points
            confidence_scores.append(0.6)
        
        return points, breakdown, confidence_scores
    
    def _project_te_points(self, consensus_lines: Dict[str, float]) -> Tuple[float, Dict[str, float], List[float]]:
        """Project fantasy points for TE position (same as WR for most leagues)"""
        return self._project_wr_points(consensus_lines)
    
    def get_all_players_in_game(self, home_team: str, away_team: str) -> List[PlayerProps]:
        """
        Get fantasy analysis for all players in a specific game.
        
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
        
        # Convert to PlayerProps list with fantasy analysis
        result = []
        game_time = datetime.fromisoformat(target_game['commence_time'].replace('Z', '+00:00'))
        
        for player_name, betting_lines in players_dict.items():
            position = self.position_map.get(player_name)
            player_team = self._determine_player_team(target_game, player_name)
            
            roster_info = PlayerRosterInfo(
                player_name=player_name,
                position=position,
                team=player_team or home_team,
                opponent=away_team if player_team == home_team else home_team,
                game_time=game_time
            )
            
            fantasy_projection = self._generate_fantasy_projection(player_name, position, betting_lines)
            
            result.append(PlayerProps(
                player_name=player_name,
                position=position,
                roster_info=roster_info,
                betting_lines=betting_lines,
                fantasy_projection=fantasy_projection
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
        
        print("📊 Fetching NFL games...")
        
        url = f"{self.ODDS_API_BASE}/sports/americanfootball_nfl/events"
        params = {
            'apiKey': self.api_key,
            'dateFormat': 'iso'
        }
        
        response = self.session.get(url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch games: {response.status_code}")
            return []
            
        response.raise_for_status()
        
        games = response.json()
        print(f"✅ Found {len(games)} games")
        
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
        
        response = self.session.get(url, params=params)
        
        # Handle rate limiting
        if response.status_code == 429:
            print("\n⏳ Rate limited, waiting 2 seconds...")
            time.sleep(2)
            response = self.session.get(url, params=params)
        
        if response.status_code != 200:
            print(f"\n❌ API Error {response.status_code}: {response.text}")
            return []  # Return empty list instead of crashing
            
        try:
            data = response.json()
            bookmakers_data = data.get('bookmakers', [])
        except requests.exceptions.JSONDecodeError as e:
            print(f"\n❌ JSON decode error: {e}")
            return []
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
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
        for prop in player_props.betting_lines:
            if prop.prop_type not in props_by_type:
                props_by_type[prop.prop_type] = []
            props_by_type[prop.prop_type].append(prop)
        
        # Find best for each type
        for prop_type, props in props_by_type.items():
            # Get best over odds (least negative or most positive)
            best_over = max(props, key=lambda x: x.over_odds if x.over_odds else -999999)
            best_lines[prop_type] = best_over
        
        return best_lines
    
    def find_value_plays(self, roster_players: List[str], threshold: float = 5.0) -> List[Dict[str, Any]]:
        """
        Find players who are projected to outperform expectations based on betting lines.
        
        Args:
            roster_players: List of player names to analyze
            threshold: Minimum confidence score to consider a value play
            
        Returns:
            List of value play analyses sorted by potential value
        """
        value_plays = []
        
        for player_name in roster_players:
            try:
                analysis = self.get_player_analysis(player_name)
                if analysis.fantasy_projection and analysis.fantasy_projection.confidence >= (threshold / 10):
                    # Calculate value based on confidence and projection
                    value_score = analysis.fantasy_projection.projected_points * analysis.fantasy_projection.confidence
                    
                    value_plays.append({
                        'player_name': player_name,
                        'position': analysis.position.value if analysis.position else 'Unknown',
                        'projected_points': analysis.fantasy_projection.projected_points,
                        'confidence': analysis.fantasy_projection.confidence,
                        'value_score': value_score,
                        'breakdown': analysis.fantasy_projection.breakdown,
                        'team': analysis.roster_info.team if analysis.roster_info else 'Unknown',
                        'opponent': analysis.roster_info.opponent if analysis.roster_info else 'Unknown'
                    })
            except Exception as e:
                print(f"Could not analyze {player_name}: {e}")
                continue
        
        # Sort by value score
        value_plays.sort(key=lambda x: x['value_score'], reverse=True)
        
        return value_plays
    
    def get_matchup_analysis(self, team1: str, team2: str) -> Dict[str, Any]:
        """
        Get comprehensive matchup analysis for all players in a game.
        
        Args:
            team1: First team name
            team2: Second team name
            
        Returns:
            Dictionary with matchup analysis
        """
        try:
            all_players = self.get_all_players_in_game(team1, team2)
        except ValueError:
            # Try reversed team order
            all_players = self.get_all_players_in_game(team2, team1)
        
        # Separate by team
        team1_players = []
        team2_players = []
        
        for player in all_players:
            if player.roster_info:
                if player.roster_info.team.lower() in team1.lower():
                    team1_players.append(player)
                else:
                    team2_players.append(player)
        
        # Sort by projected points
        team1_players.sort(key=lambda x: x.fantasy_projection.projected_points if x.fantasy_projection else 0, reverse=True)
        team2_players.sort(key=lambda x: x.fantasy_projection.projected_points if x.fantasy_projection else 0, reverse=True)
        
        # Calculate team totals
        team1_total = sum(p.fantasy_projection.projected_points if p.fantasy_projection else 0 for p in team1_players)
        team2_total = sum(p.fantasy_projection.projected_points if p.fantasy_projection else 0 for p in team2_players)
        
        return {
            'matchup': f"{team1} vs {team2}",
            'team1': {
                'name': team1,
                'total_projected_points': team1_total,
                'top_players': [p.to_dict() for p in team1_players[:5]],
                'player_count': len(team1_players)
            },
            'team2': {
                'name': team2,
                'total_projected_points': team2_total,
                'top_players': [p.to_dict() for p in team2_players[:5]],
                'player_count': len(team2_players)
            },
            'game_total': team1_total + team2_total,
            'projected_favorite': team1 if team1_total > team2_total else team2
        }
    
    def export_to_json(self, player_props: PlayerProps, filename: str):
        """Export player analysis to JSON file"""
        with open(filename, 'w') as f:
            json.dump(player_props.to_dict(), f, indent=2)
    
    def export_to_csv(self, player_props: PlayerProps, filename: str):
        """Export player analysis to CSV file"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Player', 'Position', 'Team', 'Opponent', 'Projected Points', 
                           'Confidence', 'Prop Type', 'Line', 'Over Odds', 'Under Odds', 'Bookmaker'])
            
            for line in player_props.betting_lines:
                writer.writerow([
                    player_props.player_name,
                    player_props.position.value if player_props.position else 'Unknown',
                    player_props.roster_info.team if player_props.roster_info else 'Unknown',
                    player_props.roster_info.opponent if player_props.roster_info else 'Unknown',
                    player_props.fantasy_projection.projected_points if player_props.fantasy_projection else 0,
                    player_props.fantasy_projection.confidence if player_props.fantasy_projection else 0,
                    line.prop_type,
                    line.line,
                    line.over_odds,
                    line.under_odds,
                    line.bookmaker
                ])


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer (API key loaded from .env file automatically)
    # Make sure you have ODDS_API_KEY set in your .env file
    # Get a free key at: https://the-odds-api.com
    analyzer = FantasyEdgeAnalyzer()
    
    # Set up your league scoring (example: half PPR)
    scoring = FantasyScoring(
        reception_points=0.5,  # Half PPR
        pass_yards_per_point=25,
        rush_yards_per_point=10,
        receiving_yards_per_point=10
    )
    analyzer.set_scoring(scoring)
    
    print("=== FANTASY EDGE ANALYZER ===\n")
    
    # Example 1: Compare two quarterbacks
    print("1. PLAYER COMPARISON")
    print("Comparing Josh Allen vs Lamar Jackson...")
    try:
        comparison = analyzer.compare_players("Josh Allen", "Lamar Jackson")
        print(f"Recommendation: {comparison['recommendation']}")
        print(f"Point difference: {comparison['analysis']['point_difference']:.2f}")
        print(f"Confidence difference: {comparison['analysis']['confidence_difference']:.2f}\n")
    except Exception as e:
        print(f"Comparison failed: {e}\n")
    
    # Example 2: Analyze a single player
    print("2. SINGLE PLAYER ANALYSIS")
    print("Analyzing Dak Prescott...")
    try:
        dak_analysis = analyzer.get_player_analysis("Dak Prescott")
        if dak_analysis.fantasy_projection:
            print(f"Projected Points: {dak_analysis.fantasy_projection.projected_points:.2f}")
            print(f"Confidence: {dak_analysis.fantasy_projection.confidence:.2f}")
            print("Point Breakdown:")
            for category, points in dak_analysis.fantasy_projection.breakdown.items():
                print(f"  {category}: {points:.2f}")
        print(f"Available betting lines: {len(dak_analysis.betting_lines)}\n")
    except Exception as e:
        print(f"Analysis failed: {e}\n")
    
    # Example 3: Optimize lineup from roster
    print("3. LINEUP OPTIMIZATION")
    my_roster = [
        "Josh Allen", "Dak Prescott",  # QBs
        "Saquon Barkley", "Derrick Henry", "Alvin Kamara",  # RBs  
        "Tyreek Hill", "Davante Adams", "Cooper Kupp",  # WRs
        "Travis Kelce", "Mark Andrews"  # TEs
    ]
    
    try:
        optimal_lineup = analyzer.optimize_lineup(my_roster)
        print("Optimal Lineup:")
        for position, players in optimal_lineup['optimal_lineup'].items():
            print(f"  {position}: {', '.join(players)}")
        print(f"Total Projected Points: {optimal_lineup['total_projected_points']:.2f}\n")
    except Exception as e:
        print(f"Lineup optimization failed: {e}\n")
    
    # Example 4: Find value plays
    print("4. VALUE PLAYS")
    try:
        value_plays = analyzer.find_value_plays(my_roster)
        print("Top 3 Value Plays:")
        for i, play in enumerate(value_plays[:3], 1):
            print(f"  {i}. {play['player_name']} ({play['position']}) - "
                  f"{play['projected_points']:.2f} pts (Confidence: {play['confidence']:.2f})")
        print()
    except Exception as e:
        print(f"Value analysis failed: {e}\n")
    
    # Example 5: Export data
    try:
        analyzer.export_to_json(dak_analysis, "dak_prescott_fantasy_analysis.json")
        analyzer.export_to_csv(dak_analysis, "dak_prescott_fantasy_analysis.csv")
        print("5. DATA EXPORT")
        print("Fantasy analysis exported to JSON and CSV files\n")
    except Exception as e:
        print(f"Export failed: {e}\n")
    
    print("=== Analysis Complete ===")
    print("Tips:")
    print("- Higher confidence scores indicate more reliable projections")
    print("- Compare players at the same position for best results")
    print("- Consider matchup context and injury reports")
    print("- Use value plays to identify potential sleepers")