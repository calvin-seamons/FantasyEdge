"""
Fantasy Tools - Advanced Fantasy Football Analysis
--------------------------------------------------
Additional tools and utilities for fantasy football analysis including
DFS optimization, trade analysis, waiver wire recommendations, and
season-long strategy tools.

Author: FantasyEdge
Date: 2024-2025
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import itertools
from datetime import datetime, timedelta

from betting_lines_fetcher import (
    FantasyEdgeAnalyzer, FantasyScoring, Position, PlayerProps, 
    FantasyProjection, PlayerRosterInfo, ProgressBar
)


class LeagueType(Enum):
    """Types of fantasy leagues"""
    REDRAFT = "redraft"
    DYNASTY = "dynasty"
    KEEPER = "keeper"
    DFS = "dfs"


class TradeDirection(Enum):
    """Direction of trade value"""
    GIVE = "give"
    RECEIVE = "receive"


@dataclass
class DFSConstraints:
    """Constraints for DFS lineup optimization"""
    salary_cap: int = 50000
    min_salary: Optional[int] = None
    max_players_per_team: int = 4
    stack_requirements: Optional[Dict[str, int]] = None  # e.g., {"QB-WR": 1, "QB-TE": 1}
    banned_players: Optional[List[str]] = None
    must_include: Optional[List[str]] = None


@dataclass
class TradeProposal:
    """Represents a fantasy trade proposal"""
    give_players: List[str]
    receive_players: List[str]
    trade_value: float  # Positive = good for you, negative = bad
    explanation: str
    confidence: float


@dataclass
class WaiverTarget:
    """Represents a waiver wire target"""
    player_name: str
    position: Position
    projected_points: float
    ownership_percent: float
    priority_score: float  # Higher = better pickup
    reason: str


class FantasyTools:
    """Advanced fantasy football tools and utilities"""
    
    def __init__(self, analyzer: FantasyEdgeAnalyzer):
        self.analyzer = analyzer
        
    def optimize_dfs_lineup(self, player_pool: List[str], constraints: DFSConstraints,
                          lineup_requirements: Optional[Dict[Position, int]] = None) -> Dict[str, Any]:
        """
        Optimize DFS lineup under salary and other constraints.
        
        Args:
            player_pool: List of available player names
            constraints: DFS constraints (salary, stacking, etc.)
            lineup_requirements: Position requirements
            
        Returns:
            Dictionary with optimal DFS lineup
        """
        if not lineup_requirements:
            # Default DFS lineup (DraftKings format)
            lineup_requirements = {
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 3,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            }
        
        print(f"💰 Optimizing DFS lineup from {len(player_pool)} players...")
        
        # Get player analyses
        player_analyses = {}
        progress = ProgressBar(len(player_pool), "Analyzing DFS pool")
        
        for player_name in player_pool:
            progress.update()
            try:
                analysis = self.analyzer.get_player_analysis(player_name)
                if analysis.fantasy_projection and analysis.roster_info:
                    player_analyses[player_name] = analysis
            except Exception as e:
                print(f"\n⚠️  Could not analyze {player_name}: {e}")
                continue
        
        # Filter out banned players
        if constraints.banned_players:
            for banned in constraints.banned_players:
                player_analyses.pop(banned, None)
        
        # Group by position
        players_by_position = {}
        for player_name, analysis in player_analyses.items():
            position = analysis.position
            if position not in players_by_position:
                players_by_position[position] = []
            
            # Calculate points per dollar for DFS value
            salary = analysis.roster_info.salary or 5000  # Default salary if not provided
            ppd = analysis.fantasy_projection.projected_points / (salary / 1000) if salary > 0 else 0
            
            players_by_position[position].append({
                'name': player_name,
                'analysis': analysis,
                'salary': salary,
                'projected_points': analysis.fantasy_projection.projected_points,
                'points_per_dollar': ppd,
                'team': analysis.roster_info.team
            })
        
        # Sort each position by points per dollar
        for position in players_by_position:
            players_by_position[position].sort(key=lambda x: x['points_per_dollar'], reverse=True)
        
        # Use greedy algorithm to build optimal lineup
        optimal_lineup = self._build_dfs_lineup(players_by_position, lineup_requirements, constraints)
        
        return optimal_lineup
    
    def _build_dfs_lineup(self, players_by_position: Dict[Position, List[Dict]], 
                         lineup_requirements: Dict[Position, int],
                         constraints: DFSConstraints) -> Dict[str, Any]:
        """Build DFS lineup using greedy algorithm with constraints"""
        
        lineup = {}
        total_salary = 0
        total_points = 0
        team_counts = {}
        
        # Must include players first
        if constraints.must_include:
            for player_name in constraints.must_include:
                for position, players in players_by_position.items():
                    player_found = False
                    for player in players:
                        if player['name'] == player_name:
                            if position not in lineup:
                                lineup[position] = []
                            if len(lineup[position]) < lineup_requirements.get(position, 0):
                                lineup[position].append(player)
                                total_salary += player['salary']
                                total_points += player['projected_points']
                                team = player['team']
                                team_counts[team] = team_counts.get(team, 0) + 1
                                players.remove(player)
                                player_found = True
                                break
                    if player_found:
                        break
        
        # Fill remaining positions
        for position, required_count in lineup_requirements.items():
            if position not in lineup:
                lineup[position] = []
                
            current_count = len(lineup[position])
            remaining_needed = required_count - current_count
            
            if remaining_needed > 0 and position in players_by_position:
                for player in players_by_position[position][:remaining_needed * 3]:  # Consider top options
                    if len(lineup[position]) >= required_count:
                        break
                        
                    # Check salary constraint
                    if total_salary + player['salary'] > constraints.salary_cap:
                        continue
                    
                    # Check team stacking constraint
                    team = player['team']
                    if team_counts.get(team, 0) >= constraints.max_players_per_team:
                        continue
                    
                    # Add player to lineup
                    lineup[position].append(player)
                    total_salary += player['salary']
                    total_points += player['projected_points']
                    team_counts[team] = team_counts.get(team, 0) + 1
        
        return {
            'lineup': {pos.value: [p['name'] for p in players] for pos, players in lineup.items()},
            'lineup_details': lineup,
            'total_salary': total_salary,
            'total_projected_points': total_points,
            'salary_remaining': constraints.salary_cap - total_salary,
            'team_distribution': team_counts
        }
    
    def analyze_trade(self, give_players: List[str], receive_players: List[str],
                     league_type: LeagueType = LeagueType.REDRAFT) -> TradeProposal:
        """
        Analyze a proposed trade and determine if it's favorable.
        
        Args:
            give_players: Players you would trade away
            receive_players: Players you would receive
            league_type: Type of league (affects valuation)
            
        Returns:
            TradeProposal with analysis
        """
        # Get analyses for all players
        give_analyses = []
        receive_analyses = []
        
        for player in give_players:
            try:
                analysis = self.analyzer.get_player_analysis(player)
                give_analyses.append(analysis)
            except Exception as e:
                print(f"Could not analyze {player}: {e}")
        
        for player in receive_players:
            try:
                analysis = self.analyzer.get_player_analysis(player)
                receive_analyses.append(analysis)
            except Exception as e:
                print(f"Could not analyze {player}: {e}")
        
        # Calculate total values
        give_value = sum(
            self._calculate_player_value(analysis, league_type) 
            for analysis in give_analyses
        )
        
        receive_value = sum(
            self._calculate_player_value(analysis, league_type) 
            for analysis in receive_analyses
        )
        
        trade_value = receive_value - give_value
        
        # Generate explanation
        if trade_value > 5:
            explanation = "Strongly favorable trade - you're getting significant value"
        elif trade_value > 1:
            explanation = "Favorable trade - slight advantage to you"
        elif trade_value > -1:
            explanation = "Fair trade - roughly equal value"
        elif trade_value > -5:
            explanation = "Unfavorable trade - you're giving up value"
        else:
            explanation = "Strongly unfavorable trade - avoid this deal"
        
        # Calculate confidence based on projection quality
        give_confidence = sum(a.fantasy_projection.confidence for a in give_analyses if a.fantasy_projection) / len(give_analyses) if give_analyses else 0
        receive_confidence = sum(a.fantasy_projection.confidence for a in receive_analyses if a.fantasy_projection) / len(receive_analyses) if receive_analyses else 0
        overall_confidence = (give_confidence + receive_confidence) / 2
        
        return TradeProposal(
            give_players=give_players,
            receive_players=receive_players,
            trade_value=trade_value,
            explanation=explanation,
            confidence=overall_confidence
        )
    
    def _calculate_player_value(self, analysis: PlayerProps, league_type: LeagueType) -> float:
        """Calculate player value based on projections and league type"""
        if not analysis.fantasy_projection:
            return 0.0
        
        base_value = analysis.fantasy_projection.projected_points
        
        # Adjust for league type
        if league_type == LeagueType.DYNASTY:
            # Factor in age and long-term value (simplified)
            # In a real implementation, you'd have player age data
            base_value *= 1.2  # Dynasty premium
        elif league_type == LeagueType.DFS:
            # DFS focuses on single-week performance
            base_value *= analysis.fantasy_projection.confidence
        
        return base_value
    
    def get_waiver_targets(self, available_players: List[str], roster_needs: List[Position],
                          max_ownership: float = 50.0) -> List[WaiverTarget]:
        """
        Identify the best waiver wire targets based on projections and availability.
        
        Args:
            available_players: List of available player names
            roster_needs: Positions you need to improve
            max_ownership: Maximum ownership percentage to consider
            
        Returns:
            List of WaiverTarget objects ranked by priority
        """
        print(f"📈 Analyzing {len(available_players)} waiver targets...")
        
        targets = []
        progress = ProgressBar(len(available_players), "Evaluating waiver wire")
        
        for player_name in available_players:
            progress.update()
            try:
                analysis = self.analyzer.get_player_analysis(player_name)
                
                if (analysis.fantasy_projection and 
                    analysis.position in roster_needs and
                    analysis.roster_info):
                    
                    # Calculate ownership (would come from external source in real implementation)
                    ownership = analysis.roster_info.ownership_projection or 25.0
                    
                    if ownership <= max_ownership:
                        # Calculate priority score
                        priority_score = self._calculate_waiver_priority(analysis, ownership)
                        
                        # Generate reason
                        reason = self._generate_waiver_reason(analysis)
                        
                        targets.append(WaiverTarget(
                            player_name=player_name,
                            position=analysis.position,
                            projected_points=analysis.fantasy_projection.projected_points,
                            ownership_percent=ownership,
                            priority_score=priority_score,
                            reason=reason
                        ))
                        
            except Exception as e:
                print(f"\n⚠️  Could not analyze {player_name}: {e}")
                continue
        
        # Sort by priority score
        targets.sort(key=lambda x: x.priority_score, reverse=True)
        
        return targets
    
    def _calculate_waiver_priority(self, analysis: PlayerProps, ownership: float) -> float:
        """Calculate waiver wire priority score"""
        if not analysis.fantasy_projection:
            return 0.0
        
        # Base score from projected points
        base_score = analysis.fantasy_projection.projected_points
        
        # Boost for low ownership (hidden gems)
        ownership_boost = (100 - ownership) / 100 * 5
        
        # Confidence boost
        confidence_boost = analysis.fantasy_projection.confidence * 3
        
        return base_score + ownership_boost + confidence_boost
    
    def _generate_waiver_reason(self, analysis: PlayerProps) -> str:
        """Generate explanation for waiver wire recommendation"""
        if not analysis.fantasy_projection:
            return "No projection available"
        
        points = analysis.fantasy_projection.projected_points
        confidence = analysis.fantasy_projection.confidence
        
        if points > 15 and confidence > 0.7:
            return "High-upside play with strong projection confidence"
        elif points > 12:
            return "Solid weekly starter with decent floor"
        elif confidence > 0.8:
            return "Low-risk add with reliable projection"
        else:
            return "Speculative add with potential upside"
    
    def simulate_season(self, roster_players: List[str], weeks: int = 17) -> Dict[str, Any]:
        """
        Simulate full season performance for roster evaluation.
        
        Args:
            roster_players: List of players on roster
            weeks: Number of weeks to simulate
            
        Returns:
            Dictionary with season simulation results
        """
        # This is a simplified simulation - in practice you'd want:
        # - Week-by-week projections
        # - Injury probabilities
        # - Bye week management
        # - Variance in performance
        
        weekly_scores = []
        player_totals = {}
        
        for week in range(1, weeks + 1):
            week_score = 0
            optimal_lineup = self.analyzer.optimize_lineup(roster_players)
            
            if 'total_projected_points' in optimal_lineup:
                # Add some variance (±20% standard deviation)
                import random
                variance = random.gauss(1.0, 0.2)
                week_score = optimal_lineup['total_projected_points'] * variance
            
            weekly_scores.append(week_score)
            
            # Track individual player performance
            for position, players in optimal_lineup.get('optimal_lineup', {}).items():
                for player in players:
                    if player not in player_totals:
                        player_totals[player] = 0
                    # Simplified individual scoring
                    player_totals[player] += week_score / len(players)
        
        return {
            'total_points': sum(weekly_scores),
            'average_weekly_score': sum(weekly_scores) / len(weekly_scores),
            'best_week': max(weekly_scores),
            'worst_week': min(weekly_scores),
            'weekly_scores': weekly_scores,
            'player_totals': player_totals,
            'projected_wins': len([score for score in weekly_scores if score > 110])  # Assuming 110 is average
        }
    
    def get_breakout_candidates(self, player_pool: List[str], 
                              min_confidence: float = 0.6) -> List[Dict[str, Any]]:
        """
        Identify potential breakout candidates based on betting market inefficiencies.
        
        Args:
            player_pool: List of players to analyze
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of breakout candidates with analysis
        """
        print(f"🚀 Analyzing {len(player_pool)} breakout candidates...")
        
        breakout_candidates = []
        progress = ProgressBar(len(player_pool), "Finding breakouts")
        
        for player_name in player_pool:
            progress.update()
            try:
                analysis = self.analyzer.get_player_analysis(player_name)
                
                if (analysis.fantasy_projection and 
                    analysis.fantasy_projection.confidence >= min_confidence):
                    
                    # Look for signs of breakout potential
                    breakout_score = self._calculate_breakout_potential(analysis)
                    
                    if breakout_score > 7.0:  # Arbitrary threshold
                        breakout_candidates.append({
                            'player_name': player_name,
                            'position': analysis.position.value if analysis.position else 'Unknown',
                            'projected_points': analysis.fantasy_projection.projected_points,
                            'confidence': analysis.fantasy_projection.confidence,
                            'breakout_score': breakout_score,
                            'team': analysis.roster_info.team if analysis.roster_info else 'Unknown',
                            'reasoning': self._generate_breakout_reasoning(analysis, breakout_score)
                        })
                        
            except Exception as e:
                print(f"\n⚠️  Could not analyze {player_name}: {e}")
                continue
        
        # Sort by breakout score
        breakout_candidates.sort(key=lambda x: x['breakout_score'], reverse=True)
        
        return breakout_candidates
    
    def _calculate_breakout_potential(self, analysis: PlayerProps) -> float:
        """Calculate breakout potential score"""
        if not analysis.fantasy_projection:
            return 0.0
        
        # Base on high projection with high confidence
        base_score = analysis.fantasy_projection.projected_points * analysis.fantasy_projection.confidence
        
        # Look for specific indicators in the breakdown
        rushing_upside = analysis.fantasy_projection.breakdown.get('rushing_yards', 0) > 30
        receiving_upside = analysis.fantasy_projection.breakdown.get('receiving_yards', 0) > 60
        td_upside = analysis.fantasy_projection.breakdown.get('receiving_tds', 0) > 0.5
        
        # Boost score for multi-category upside
        if rushing_upside:
            base_score += 2
        if receiving_upside:
            base_score += 2
        if td_upside:
            base_score += 3
            
        return base_score
    
    def _generate_breakout_reasoning(self, analysis: PlayerProps, breakout_score: float) -> str:
        """Generate reasoning for breakout candidate"""
        if breakout_score > 15:
            return "Elite projection with multiple touchdown upside categories"
        elif breakout_score > 12:
            return "Strong multi-category potential with high confidence"
        elif breakout_score > 9:
            return "Solid upside play with reliable floor"
        else:
            return "Speculative breakout candidate with moderate upside"
