"""
Fantasy League Configurations
-----------------------------
Pre-configured scoring systems and league settings for popular fantasy formats.
Makes it easy to switch between different league types and scoring systems.

Author: FantasyEdge
Date: 2024-2025
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from betting_lines_fetcher import FantasyScoring, Position


@dataclass
class LeagueConfig:
    """Complete league configuration including scoring and roster requirements"""
    name: str
    scoring: FantasyScoring
    roster_requirements: Dict[Position, int]
    bench_spots: int = 6
    total_roster_size: int = 16
    trade_deadline_week: int = 10
    playoff_weeks: List[int] = None
    
    def __post_init__(self):
        if self.playoff_weeks is None:
            self.playoff_weeks = [14, 15, 16]


class LeagueConfigs:
    """Pre-defined league configurations for popular formats"""
    
    @staticmethod
    def standard_ppr() -> LeagueConfig:
        """Standard PPR (Point Per Reception) league"""
        return LeagueConfig(
            name="Standard PPR",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=4.0,
                pass_interception_points=-2.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=1.0,  # Full PPR
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=6
        )
    
    @staticmethod
    def half_ppr() -> LeagueConfig:
        """Half PPR league"""
        return LeagueConfig(
            name="Half PPR",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=4.0,
                pass_interception_points=-2.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=0.5,  # Half PPR
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=6
        )
    
    @staticmethod
    def standard_non_ppr() -> LeagueConfig:
        """Standard non-PPR league"""
        return LeagueConfig(
            name="Standard (Non-PPR)",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=4.0,
                pass_interception_points=-2.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=0.0,  # No PPR
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=6
        )
    
    @staticmethod
    def superflex() -> LeagueConfig:
        """Superflex league (QB premium)"""
        return LeagueConfig(
            name="Superflex",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=6.0,  # QB premium
                pass_interception_points=-2.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=1.0,
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
                # Note: Superflex spot would be handled as a FLEX position
            },
            bench_spots=6
        )
    
    @staticmethod
    def draftkings_dfs() -> LeagueConfig:
        """DraftKings DFS scoring"""
        return LeagueConfig(
            name="DraftKings DFS",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=4.0,
                pass_interception_points=-1.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=1.0,
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0,
                long_td_bonus=3.0,  # 40+ yard TD bonus
                long_pass_bonus=3.0,  # 300+ yard bonus
                long_rush_bonus=3.0,  # 100+ yard bonus
                long_receiving_bonus=3.0  # 100+ yard bonus
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 3,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=0  # No bench in DFS
        )
    
    @staticmethod
    def fanduel_dfs() -> LeagueConfig:
        """FanDuel DFS scoring"""
        return LeagueConfig(
            name="FanDuel DFS",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=4.0,
                pass_interception_points=-1.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=0.5,  # Half PPR
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=0  # No bench in DFS
        )
    
    @staticmethod
    def dynasty_ppr() -> LeagueConfig:
        """Dynasty league with deeper rosters"""
        return LeagueConfig(
            name="Dynasty PPR",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=4.0,
                pass_interception_points=-2.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=1.0,
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=15,  # Deeper benches for dynasty
            total_roster_size=22,
            trade_deadline_week=12  # Later trade deadline
        )
    
    @staticmethod
    def best_ball() -> LeagueConfig:
        """Best Ball league (no weekly lineup changes)"""
        return LeagueConfig(
            name="Best Ball",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=4.0,
                pass_interception_points=-2.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=0.5,  # Half PPR common in best ball
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=11,  # Larger roster for best ball
            total_roster_size=18
        )
    
    @staticmethod
    def two_qb() -> LeagueConfig:
        """Two QB league"""
        return LeagueConfig(
            name="Two QB",
            scoring=FantasyScoring(
                pass_yards_per_point=25.0,
                pass_td_points=6.0,  # QB premium
                pass_interception_points=-2.0,
                rush_yards_per_point=10.0,
                rush_td_points=6.0,
                reception_points=1.0,
                receiving_yards_per_point=10.0,
                receiving_td_points=6.0,
                fg_points=3.0,
                extra_point_points=1.0
            ),
            roster_requirements={
                Position.QB: 2,  # Two QBs required
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=6
        )
    
    @staticmethod
    def chimpzone_2025() -> LeagueConfig:
        """ChimpZone 2025 league with custom scoring"""
        return LeagueConfig(
            name="ChimpZone 2025",
            scoring=FantasyScoring(
                # Passing - 6 pt passing TDs, 0.04 per yard
                pass_yards_per_point=25.0,  # 25 yards = 1 point
                pass_td_points=6.0,  # 6 points per passing TD
                pass_interception_points=-1.0,  # -1 for interceptions
                pass_completion_points=0.0,
                
                # Rushing - standard 0.1 per yard, 6 pt TDs
                rush_yards_per_point=10.0,  # 10 yards = 1 point
                rush_td_points=6.0,
                
                # Receiving - Full PPR, 0.1 per yard, 6 pt TDs
                reception_points=1.0,  # Full PPR
                receiving_yards_per_point=10.0,  # 10 yards = 1 point
                receiving_td_points=6.0,
                
                # Kicking - Variable FG scoring
                fg_points=3.0,  # Base FG points (0-39 yards)
                extra_point_points=1.0,
                
                # Bonuses - ChimpZone specific
                long_td_bonus=2.5,  # 50+ yard TD bonus
                long_pass_bonus=2.5,  # 400+ yard passing bonus
                long_rush_bonus=2.5,  # 200+ yard rushing bonus
                long_receiving_bonus=2.5  # 200+ yard receiving bonus
            ),
            roster_requirements={
                Position.QB: 1,
                Position.RB: 2,
                Position.WR: 2,
                Position.TE: 1,
                Position.K: 1,
                Position.DST: 1
            },
            bench_spots=6,
            total_roster_size=13,  # 7 starters + 6 bench
            trade_deadline_week=11,
            playoff_weeks=[15, 16, 17]  # Playoffs start week 15
        )

    @staticmethod
    def get_all_configs() -> Dict[str, LeagueConfig]:
        """Get all available league configurations"""
        return {
            "standard_ppr": LeagueConfigs.standard_ppr(),
            "half_ppr": LeagueConfigs.half_ppr(),
            "standard_non_ppr": LeagueConfigs.standard_non_ppr(),
            "superflex": LeagueConfigs.superflex(),
            "draftkings_dfs": LeagueConfigs.draftkings_dfs(),
            "fanduel_dfs": LeagueConfigs.fanduel_dfs(),
            "dynasty_ppr": LeagueConfigs.dynasty_ppr(),
            "best_ball": LeagueConfigs.best_ball(),
            "two_qb": LeagueConfigs.two_qb(),
            "chimpzone_2025": LeagueConfigs.chimpzone_2025()
        }
    
    @staticmethod
    def get_config_by_name(name: str) -> Optional[LeagueConfig]:
        """Get a specific league configuration by name"""
        configs = LeagueConfigs.get_all_configs()
        return configs.get(name.lower().replace(" ", "_").replace("-", "_"))


# Position requirements for different league formats
class PositionRequirements:
    """Standard position requirements for different league formats"""
    
    STANDARD = {
        Position.QB: 1,
        Position.RB: 2,
        Position.WR: 2,
        Position.TE: 1,
        Position.K: 1,
        Position.DST: 1
    }
    
    DRAFTKINGS = {
        Position.QB: 1,
        Position.RB: 2,
        Position.WR: 3,
        Position.TE: 1,
        Position.K: 1,
        Position.DST: 1
    }
    
    FANDUEL = {
        Position.QB: 1,
        Position.RB: 2,
        Position.WR: 2,
        Position.TE: 1,
        Position.K: 1,
        Position.DST: 1
    }
    
    SUPERFLEX = {
        Position.QB: 1,
        Position.RB: 2,
        Position.WR: 2,
        Position.TE: 1,
        Position.K: 1,
        Position.DST: 1
        # Additional QB/RB/WR/TE flex spot would be handled separately
    }
    
    TWO_QB = {
        Position.QB: 2,
        Position.RB: 2,
        Position.WR: 2,
        Position.TE: 1,
        Position.K: 1,
        Position.DST: 1
    }


# Common salary caps for DFS sites
class DFSSalaryCaps:
    """DFS salary caps for different sites"""
    DRAFTKINGS = 50000
    FANDUEL = 60000
    SUPERDRAFT = 50000
    YAHOO = 200  # Yahoo uses a different budget system
