# Fantasy Edge - NFL Fantasy Football Analysis System

Transform NFL betting lines into actionable fantasy football insights. Make smarter lineup decisions, find value trades, and identify breakout candidates using real-time betting market data.

## 🏈 What This Does

Instead of just fetching betting lines, Fantasy Edge converts that market data into fantasy football projections and analysis tools:

- **Player Comparisons**: Compare any two players based on betting line projections
- **Lineup Optimization**: Build optimal lineups from your roster
- **Trade Analysis**: Evaluate trades with confidence scores  
- **Waiver Wire Targets**: Find undervalued players on waivers
- **DFS Optimization**: Build optimal DFS lineups with salary constraints
- **Breakout Candidates**: Identify players with breakout potential

## 🚀 Quick Start

1. **Get API Access** (Optional but recommended)
   ```bash
   # Get free API key from https://the-odds-api.com
   # Add to .env file:
   echo "ODDS_API_KEY=your_key_here" > .env
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Example**
   ```bash
   python example_usage.py
   ```

## 💡 Core Features

### Player Analysis & Comparison
```python
from betting_lines_fetcher import FantasyEdgeAnalyzer
from league_configs import LeagueConfigs

# Set up analyzer with your league scoring
analyzer = FantasyEdgeAnalyzer()
scoring = LeagueConfigs.half_ppr().scoring
analyzer.set_scoring(scoring)

# Compare two players
comparison = analyzer.compare_players("Josh Allen", "Lamar Jackson")
print(comparison['recommendation'])
# Output: "Start Josh Allen (+2.3 projected points)"
```

### Lineup Optimization
```python
# Your roster
my_roster = [
    "Josh Allen", "Dak Prescott",           # QBs
    "Saquon Barkley", "Derrick Henry",      # RBs  
    "Tyreek Hill", "Davante Adams",         # WRs
    "Travis Kelce"                          # TE
]

# Get optimal lineup
optimal = analyzer.optimize_lineup(my_roster)
print(f"Projected Points: {optimal['total_projected_points']:.1f}")

for position, players in optimal['optimal_lineup'].items():
    print(f"{position}: {', '.join(players)}")
```

### Trade Analysis
```python
from fantasy_tools import FantasyTools

tools = FantasyTools(analyzer)

# Analyze a trade
trade = tools.analyze_trade(
    give_players=["Derrick Henry", "Mike Evans"],
    receive_players=["Christian McCaffrey"]
)

print(trade.explanation)
print(f"Trade Value: {trade.trade_value:+.2f}")
```

### DFS Optimization  
```python
from fantasy_tools import DFSConstraints
from league_configs import LeagueConfigs

# Set up DFS constraints
dfs_config = LeagueConfigs.draftkings_dfs()
analyzer.set_scoring(dfs_config.scoring)

constraints = DFSConstraints(
    salary_cap=50000,
    max_players_per_team=3,
    must_include=["Josh Allen"]
)

# Optimize DFS lineup
dfs_lineup = tools.optimize_dfs_lineup(player_pool, constraints)
print(f"Total Salary: ${dfs_lineup['total_salary']:,}")
print(f"Projected: {dfs_lineup['total_projected_points']:.1f} points")
```

## ⚙️ League Configurations

Pre-configured scoring systems for popular league types:

```python
from league_configs import LeagueConfigs

# Available configurations:
configs = {
    "standard_ppr": LeagueConfigs.standard_ppr(),
    "half_ppr": LeagueConfigs.half_ppr(), 
    "standard_non_ppr": LeagueConfigs.standard_non_ppr(),
    "superflex": LeagueConfigs.superflex(),
    "draftkings_dfs": LeagueConfigs.draftkings_dfs(),
    "fanduel_dfs": LeagueConfigs.fanduel_dfs(),
    "dynasty_ppr": LeagueConfigs.dynasty_ppr(),
    "best_ball": LeagueConfigs.best_ball(),
    "two_qb": LeagueConfigs.two_qb()
}

# Use any configuration
analyzer.set_scoring(configs["half_ppr"].scoring)
```

## 📊 Advanced Analysis

### Find Value Plays
```python
# Find undervalued players on your roster
value_plays = tools.find_value_plays(my_roster, threshold=6.0)

for play in value_plays[:3]:
    print(f"{play['player_name']}: {play['projected_points']:.1f} pts")
    print(f"  Confidence: {play['confidence']:.2f}")
    print(f"  Value Score: {play['value_score']:.1f}")
```

### Waiver Wire Targets
```python
available_players = ["Gus Edwards", "Jaylen Warren", "Elijah Moore"]
roster_needs = [Position.RB, Position.WR]

targets = tools.get_waiver_targets(available_players, roster_needs)

for target in targets:
    print(f"{target.player_name} ({target.position.value})")
    print(f"  Projected: {target.projected_points:.1f} points")
    print(f"  Reason: {target.reason}")
```

### Breakout Candidates
```python
breakouts = tools.get_breakout_candidates(extended_player_pool)

for candidate in breakouts[:5]:
    print(f"{candidate['player_name']}: {candidate['breakout_score']:.1f}")
    print(f"  {candidate['reasoning']}")
```

## 🔧 File Structure

```
FantasyEdge/
├── betting_lines_fetcher.py    # Main analyzer class
├── fantasy_tools.py            # Advanced fantasy tools  
├── league_configs.py          # Pre-configured league settings
├── example_usage.py           # Example usage script
├── requirements.txt           # Python dependencies
└── .env                      # API key (create this)
```

## 📈 How It Works

1. **Fetches Betting Lines**: Uses The Odds API to get real-time player prop lines
2. **Converts to Fantasy Points**: Translates betting lines into fantasy projections based on your league scoring
3. **Analyzes Value**: Compares projections to find optimal plays and value opportunities
4. **Provides Recommendations**: Gives actionable advice for lineups, trades, and waiver moves

## 🎯 Use Cases

### Season-Long Leagues
- **Weekly Lineup Decisions**: Who to start/sit each week
- **Trade Evaluation**: Whether to accept/propose trades
- **Waiver Priority**: Which players to target on waivers
- **Breakout Identification**: Find players before they blow up

### Daily Fantasy (DFS)
- **Lineup Optimization**: Build optimal lineups under salary constraints
- **Value Identification**: Find players with best points/dollar ratio
- **Stack Analysis**: Optimize QB/WR/TE correlations
- **Contest Strategy**: Adjust for different contest types

### Dynasty Leagues
- **Long-term Value**: Factor in player age and potential
- **Trade Windows**: When to buy/sell players
- **Rookie Analysis**: Evaluate incoming talent
- **Rebuild Strategy**: Plan multi-year rebuilds

## 🚨 Important Notes

- **API Key Required**: Get free tier at [The Odds API](https://the-odds-api.com)
- **Rate Limits**: Free tier has request limits - use caching wisely
- **Market Efficiency**: Betting lines are generally efficient, look for edge cases
- **Injury Updates**: Always check injury reports before finalizing decisions
- **Weather Impact**: Consider weather for outdoor games

## 🤝 Contributing

This is designed to be extensible:

- Add new league configurations in `league_configs.py`
- Extend analysis tools in `fantasy_tools.py`  
- Add new prop types in `betting_lines_fetcher.py`
- Improve projection algorithms with your own models

## 📝 License

This project is for educational and personal use. Respect the terms of service for any APIs used.

---

**Good luck with your fantasy season! 🏆**
