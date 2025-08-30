"""
ChimpZone 2025 League Analysis
-----------------------------
Custom analysis script for the ChimpZone 2025 fantasy league.
Uses your specific roster and league scoring settings.

Your Current Roster:
- QB: Dak Prescott, Justin Herbert
- RB: Jonathan Taylor, James Conner, Keontay Johnson, Bucky Robinson  
- WR: CeeDee Lamb, Tee Higgins, DK Metcalf, DeVonta Smith, Darnell Mooney, Jaylen Waddle
- TE: Jaylen Smith
- K: Jake Elliott  
- DEF: Cincinnati
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed")

from betting_lines_fetcher import FantasyEdgeAnalyzer, Position
from fantasy_tools import FantasyTools, DFSConstraints
from league_configs import LeagueConfigs

def analyze_chimpzone_roster():
    """Analyze your ChimpZone 2025 roster with custom league settings"""
    
    print("🐒 CHIMPZONE 2025 ANALYSIS 🐒\n")
    
    # Initialize analyzer with ChimpZone settings
    analyzer = FantasyEdgeAnalyzer()
    tools = FantasyTools(analyzer)
    
    # Load ChimpZone 2025 league configuration
    chimpzone_config = LeagueConfigs.chimpzone_2025()
    analyzer.set_scoring(chimpzone_config.scoring)
    
    print(f"📊 League: {chimpzone_config.name}")
    print(f"   Passing TDs: {chimpzone_config.scoring.pass_td_points} pts")
    print(f"   Reception Points: {chimpzone_config.scoring.reception_points} (Full PPR)")
    print(f"   50+ Yard TD Bonus: +{chimpzone_config.scoring.long_td_bonus}")
    print(f"   Trade Deadline: Week {chimpzone_config.trade_deadline_week}")
    print(f"   Playoffs: Weeks {chimpzone_config.playoff_weeks}\n")
    
    # Your current roster (using exact player names)
    your_roster = {
        "starters": {
            "QB": ["Dak Prescott"],  # D Prescott
            "RB": ["Jonathan Taylor", "James Conner"],  # J Taylor, J Conner
            "WR": ["CeeDee Lamb", "Tee Higgins"],  # C Lamb, T Higgins
            "TE": ["Jaylen Smith"],  # J Smith (PIT)
            "K": ["Jake Elliott"],  # J Elliott
            "DEF": ["Cincinnati"]
        },
        "bench": {
            "QB": ["Justin Herbert"],  # J Herbert
            "RB": ["Keontay Johnson", "Bucky Robinson"],  # K Johnson, B Robinson
            "WR": ["DK Metcalf", "DeVonta Smith", "Darnell Mooney", "Jaylen Waddle"]  # D Metcalf, D Smith, D Mooney, J Waddle
        }
    }
    
    # All your players for analysis
    all_players = []
    for position_group in your_roster.values():
        for position, players in position_group.items():
            if position != "K" and position != "DEF":  # Skip kicker and defense for now
                all_players.extend(players)
    
    print("=" * 60)
    print("🎯 OPTIMAL LINEUP ANALYSIS")
    print("=" * 60)
    
    api_key = os.getenv('ODDS_API_KEY')
    if api_key:
        try:
            optimal = analyzer.optimize_lineup(all_players, chimpzone_config.roster_requirements)
            
            print("🏆 OPTIMAL STARTING LINEUP:")
            total_points = 0
            for position, players in optimal['optimal_lineup'].items():
                if players:  # Only show positions with players
                    print(f"   {position}: {', '.join(players)}")
            
            print(f"\n📈 Total Projected Points: {optimal['total_projected_points']:.2f}")
            
            # Show bench recommendations
            print("\n🪑 BENCH PLAYERS:")
            for position, players in optimal.get('bench_players', {}).items():
                if players:
                    print(f"   {position}: {', '.join(players)}")
                    
        except Exception as e:
            print(f"❌ Lineup optimization failed: {e}")
    else:
        print("🔄 Demo mode - add ODDS_API_KEY for live analysis")
    
    print("\n" + "=" * 60)
    print("🔥 START/SIT DECISIONS")
    print("=" * 60)
    
    # Key start/sit decisions
    key_decisions = [
        ("Dak Prescott", "Justin Herbert", "QB decision"),
        ("DK Metcalf", "DeVonta Smith", "WR2/WR3 decision"),
        ("Darnell Mooney", "Jaylen Waddle", "Flex consideration")
    ]
    
    for player1, player2, decision_type in key_decisions:
        print(f"\n🤔 {decision_type.upper()}:")
        print(f"   Comparing {player1} vs {player2}")
        
        if api_key:
            try:
                comparison = analyzer.compare_players(player1, player2)
                print(f"   ✅ {comparison['recommendation']}")
                print(f"   Point difference: {comparison['analysis']['point_difference']:.2f}")
            except Exception as e:
                print(f"   ❌ Comparison failed: {e}")
        else:
            print("   🔄 Add API key for live comparison")
    
    print("\n" + "=" * 60)
    print("📈 WAIVER WIRE TARGETS")
    print("=" * 60)
    
    # Potential waiver targets (you'd update these based on available players)
    waiver_candidates = [
        "Gus Edwards", "Jaylen Warren", "Tank Bigsby",  # RBs
        "Romeo Doubs", "Darius Slayton", "Elijah Moore",  # WRs
        "Tyler Higbee", "Cade Otton"  # TEs
    ]
    
    roster_needs = [Position.RB, Position.WR, Position.TE]  # Areas to improve
    
    print("Analyzing potential waiver targets...")
    print("Positions of need: RB depth, WR depth, TE backup")
    
    if api_key:
        try:
            targets = tools.get_waiver_targets(waiver_candidates, roster_needs, max_ownership=75)
            
            print("\n🎯 TOP WAIVER TARGETS:")
            for i, target in enumerate(targets[:3], 1):
                print(f"   {i}. {target.player_name} ({target.position.value})")
                print(f"      Projected: {target.projected_points:.1f} pts")
                print(f"      Priority Score: {target.priority_score:.1f}")
                print(f"      Reason: {target.reason}")
                
        except Exception as e:
            print(f"❌ Waiver analysis failed: {e}")
    else:
        print("🔄 Demo targets: Jaylen Warren (RB), Romeo Doubs (WR)")
    
    print("\n" + "=" * 60)
    print("🔄 TRADE OPPORTUNITIES") 
    print("=" * 60)
    
    # Potential trade scenarios
    print("Potential trade scenarios to consider:")
    print("1. Package deal: Upgrade at RB")
    print("   Give: James Conner + DK Metcalf")
    print("   Target: Elite RB1")
    
    print("\n2. QB depth trade:")
    print("   Give: Justin Herbert") 
    print("   Target: WR/RB depth")
    
    print("\n3. WR consolidation:")
    print("   Give: DeVonta Smith + Darnell Mooney")
    print("   Target: Consistent WR2")
    
    if api_key:
        print("\n🔍 Sample Trade Analysis:")
        try:
            # Example trade analysis
            trade = tools.analyze_trade(
                give_players=["James Conner", "DK Metcalf"],
                receive_players=["Saquon Barkley"]
            )
            print(f"   Trade: Give Conner + Metcalf for Saquon Barkley")
            print(f"   ✅ {trade.explanation}")
            print(f"   Value: {trade.trade_value:+.2f}")
        except Exception as e:
            print(f"   ❌ Trade analysis failed: {e}")
    
    print("\n" + "=" * 60)
    print("📊 SEASON OUTLOOK")
    print("=" * 60)
    
    print("🟢 STRENGTHS:")
    print("   • Elite WR1 in CeeDee Lamb")
    print("   • Strong RB1 in Jonathan Taylor")
    print("   • Solid QB depth with Dak/Herbert")
    print("   • Deep WR corps for bye weeks")
    
    print("\n🟡 AREAS TO MONITOR:")
    print("   • TE production from Jaylen Smith")
    print("   • RB2 consistency from James Conner")  
    print("   • Health of key players")
    
    print("\n🔴 POTENTIAL CONCERNS:")
    print("   • Lack of elite TE option")
    print("   • RB depth beyond Taylor/Conner")
    print("   • WR target share volatility")
    
    print("\n💡 WEEKLY TIPS:")
    print("   • Monitor weather for DAL @ PHI (Thursday)")
    print("   • Check injury reports Tuesday/Wednesday")
    print("   • Consider matchup-based start/sit decisions")
    print("   • Track target share trends for WRs")
    
    print("\n🏆 CHAMPIONSHIP STRATEGY:")
    print("   • Target playoff weeks 15-17 schedules")
    print("   • Consider late-season trades for playoff studs")
    print("   • Handcuff your key RBs if possible")
    print("   • Stream favorable matchups at TE/DEF")

if __name__ == "__main__":
    analyze_chimpzone_roster()
