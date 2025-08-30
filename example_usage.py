"""
Fantasy Edge Example Usage
--------------------------
Example script showing how to use the Fantasy Edge system for 
fantasy football analysis and decision making.

Run this script to see various features in action.
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
except ImportError:
    print("Warning: python-dotenv not installed")

from betting_lines_fetcher import FantasyEdgeAnalyzer, Position
from fantasy_tools import FantasyTools, DFSConstraints
from league_configs import LeagueConfigs

def main():
    """Main example function"""
    print("🏈 FANTASY EDGE - NFL ANALYSIS SYSTEM 🏈\n")
    
    # Check if API key is available
    api_key = os.getenv('ODDS_API_KEY')
    print(f"Debug: API key from environment: {'Found' if api_key else 'Not found'}")
    if api_key:
        print(f"Debug: API key starts with: {api_key[:8]}...")
    
    if not api_key:
        print("❌ No ODDS_API_KEY found in environment variables.")
        print("   Get a free API key at: https://the-odds-api.com")
        print("   Then add it to your .env file as: ODDS_API_KEY=your_key_here\n")
        print("🔄 Running in demo mode with mock data...\n")
    else:
        print("✅ API key found! Running with live data...\n")
    
    # Initialize the analyzer
    analyzer = FantasyEdgeAnalyzer()
    tools = FantasyTools(analyzer)
    
    # Set up league configuration
    league_config = LeagueConfigs.half_ppr()  # Use half PPR scoring
    analyzer.set_scoring(league_config.scoring)
    
    print(f"📊 League Configuration: {league_config.name}")
    print(f"   Reception Points: {league_config.scoring.reception_points}")
    print(f"   Pass TD Points: {league_config.scoring.pass_td_points}")
    print(f"   Rush/Rec TD Points: {league_config.scoring.rush_td_points}")
    print("\n💡 TIP: Run 'python chimpzone_analysis.py' for ChimpZone 2025 specific analysis\n")
    
    # Example 1: Compare two players
    print("=" * 50)
    print("🔥 PLAYER COMPARISON")
    print("=" * 50)
    
    player1 = "Josh Allen"
    player2 = "Lamar Jackson"
    
    print(f"Comparing {player1} vs {player2}...")
    
    if api_key:
        try:
            comparison = analyzer.compare_players(player1, player2)
            print(f"✅ {comparison['recommendation']}")
            print(f"   Point Difference: {comparison['analysis']['point_difference']:.2f}")
            print(f"   Confidence Gap: {comparison['analysis']['confidence_difference']:.2f}")
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
    else:
        print("🔄 Demo: Josh Allen projected for 22.5 points")
        print("🔄 Demo: Lamar Jackson projected for 21.8 points")
        print("✅ Recommendation: Start Josh Allen (+0.7 projected points)")
    
    print()
    
    # Example 2: Lineup Optimization
    print("=" * 50)
    print("🎯 LINEUP OPTIMIZATION")
    print("=" * 50)
    
    my_roster = [
        "Josh Allen", "Dak Prescott",  # QBs
        "Saquon Barkley", "Derrick Henry", "Alvin Kamara", "Josh Jacobs",  # RBs
        "Tyreek Hill", "Davante Adams", "Cooper Kupp", "Mike Evans",  # WRs
        "Travis Kelce", "Mark Andrews"  # TEs
    ]
    
    print("Your Roster:")
    print("   QBs: Josh Allen, Dak Prescott")
    print("   RBs: Saquon Barkley, Derrick Henry, Alvin Kamara, Josh Jacobs")
    print("   WRs: Tyreek Hill, Davante Adams, Cooper Kupp, Mike Evans")
    print("   TEs: Travis Kelce, Mark Andrews\n")
    
    if api_key:
        try:
            optimal = analyzer.optimize_lineup(my_roster, league_config.roster_requirements)
            print("🏆 OPTIMAL LINEUP:")
            for position, players in optimal['optimal_lineup'].items():
                print(f"   {position}: {', '.join(players)}")
            print(f"   Total Projected: {optimal['total_projected_points']:.2f} points")
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
    else:
        print("🔄 Demo Optimal Lineup:")
        print("   QB: Josh Allen")
        print("   RB: Saquon Barkley, Derrick Henry")
        print("   WR: Tyreek Hill, Davante Adams")
        print("   TE: Travis Kelce")
        print("   K: [Need to add kicker]")
        print("   DST: [Need to add defense]")
        print("   Total Projected: 142.3 points")
    
    print()
    
    # Example 3: Trade Analysis
    print("=" * 50)
    print("🔄 TRADE ANALYSIS")
    print("=" * 50)
    
    give_players = ["Derrick Henry", "Mike Evans"]
    receive_players = ["Christian McCaffrey"]
    
    print(f"Proposed Trade:")
    print(f"   You Give: {', '.join(give_players)}")
    print(f"   You Get: {', '.join(receive_players)}")
    
    if api_key:
        try:
            trade_analysis = tools.analyze_trade(give_players, receive_players)
            print(f"✅ {trade_analysis.explanation}")
            print(f"   Trade Value: {trade_analysis.trade_value:+.2f}")
            print(f"   Confidence: {trade_analysis.confidence:.2f}")
        except Exception as e:
            print(f"❌ Trade analysis failed: {e}")
    else:
        print("🔄 Demo: Fair trade - roughly equal value")
        print("   Trade Value: +0.8")
        print("   Confidence: 0.75")
    
    print()
    
    # Example 4: Waiver Wire Targets
    print("=" * 50)
    print("📈 WAIVER WIRE TARGETS")
    print("=" * 50)
    
    available_players = [
        "Gus Edwards", "Jaylen Warren", "Deon Jackson",
        "Elijah Moore", "Darius Slayton", "Romeo Doubs",
        "Tyler Higbee", "Cade Otton"
    ]
    
    roster_needs = [Position.RB, Position.WR]
    
    print("Available Players:", ", ".join(available_players))
    print("Roster Needs: RB depth, WR depth")
    
    if api_key:
        try:
            targets = tools.get_waiver_targets(available_players, roster_needs)
            print("\n🎯 TOP WAIVER TARGETS:")
            for i, target in enumerate(targets[:3], 1):
                print(f"   {i}. {target.player_name} ({target.position.value})")
                print(f"      Projected: {target.projected_points:.1f} pts")
                print(f"      Ownership: {target.ownership_percent:.1f}%")
                print(f"      Reason: {target.reason}")
        except Exception as e:
            print(f"❌ Waiver analysis failed: {e}")
    else:
        print("\n🔄 Demo Top Waiver Targets:")
        print("   1. Jaylen Warren (RB)")
        print("      Projected: 11.2 pts | Ownership: 23.4%")
        print("      Reason: High-upside play with strong projection confidence")
        print("   2. Elijah Moore (WR)")
        print("      Projected: 9.8 pts | Ownership: 18.7%")
        print("      Reason: Solid weekly starter with decent floor")
    
    print()
    
    # Example 5: DFS Lineup (if using DFS config)
    print("=" * 50)
    print("💰 DFS LINEUP OPTIMIZATION")
    print("=" * 50)
    
    # Switch to DFS configuration
    dfs_config = LeagueConfigs.draftkings_dfs()
    analyzer.set_scoring(dfs_config.scoring)
    
    dfs_player_pool = my_roster + available_players + [
        "Justin Jefferson", "Stefon Diggs", "CeeDee Lamb",  # More WRs
        "Nick Chubb", "Aaron Jones",  # More RBs
        "Justin Tucker"  # Kicker
    ]
    
    dfs_constraints = DFSConstraints(
        salary_cap=50000,
        max_players_per_team=3,
        must_include=["Josh Allen"]  # Stack with your QB
    )
    
    print(f"DFS Configuration: {dfs_config.name}")
    print(f"Salary Cap: ${dfs_constraints.salary_cap:,}")
    print(f"Must Include: {dfs_constraints.must_include}")
    
    if api_key:
        try:
            dfs_lineup = tools.optimize_dfs_lineup(dfs_player_pool, dfs_constraints, dfs_config.roster_requirements)
            print("\n💎 OPTIMAL DFS LINEUP:")
            for position, players in dfs_lineup['lineup'].items():
                print(f"   {position}: {', '.join(players)}")
            print(f"   Total Salary: ${dfs_lineup['total_salary']:,}")
            print(f"   Projected Points: {dfs_lineup['total_projected_points']:.2f}")
            print(f"   Salary Remaining: ${dfs_lineup['salary_remaining']:,}")
        except Exception as e:
            print(f"❌ DFS optimization failed: {e}")
    else:
        print("\n🔄 Demo DFS Lineup:")
        print("   QB: Josh Allen")
        print("   RB: Saquon Barkley, Nick Chubb")
        print("   WR: Tyreek Hill, Justin Jefferson, Cooper Kupp")
        print("   TE: Travis Kelce")
        print("   K: Justin Tucker")
        print("   DST: [Team Defense]")
        print("   Total Salary: $49,200")
        print("   Projected Points: 156.8")
        print("   Salary Remaining: $800")
    
    print()
    
    # Example 6: Breakout Candidates
    print("=" * 50)
    print("🚀 BREAKOUT CANDIDATES")
    print("=" * 50)
    
    extended_player_pool = dfs_player_pool + [
        "Zay Flowers", "Tank Dell", "Rashee Rice",
        "De'Von Achane", "Tyjae Spears", "Roschon Johnson"
    ]
    
    if api_key:
        try:
            breakouts = tools.get_breakout_candidates(extended_player_pool)
            print("🔥 TOP BREAKOUT CANDIDATES:")
            for i, candidate in enumerate(breakouts[:3], 1):
                print(f"   {i}. {candidate['player_name']} ({candidate['position']})")
                print(f"      Projected: {candidate['projected_points']:.1f} pts")
                print(f"      Breakout Score: {candidate['breakout_score']:.1f}")
                print(f"      Reasoning: {candidate['reasoning']}")
        except Exception as e:
            print(f"❌ Breakout analysis failed: {e}")
    else:
        print("🔄 Demo Breakout Candidates:")
        print("   1. Zay Flowers (WR)")
        print("      Projected: 13.4 pts | Breakout Score: 14.2")
        print("      Reasoning: Elite projection with multiple touchdown upside categories")
        print("   2. De'Von Achane (RB)")
        print("      Projected: 12.1 pts | Breakout Score: 13.8")
        print("      Reasoning: Strong multi-category potential with high confidence")
    
    print()
    print("=" * 50)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 50)
    
    print("\n💡 FANTASY TIPS:")
    print("• Higher confidence scores indicate more reliable projections")
    print("• Always consider injury reports and weather conditions")
    print("• Use matchup analysis for tough start/sit decisions")
    print("• Monitor target share and red zone opportunities")
    print("• Consider stacking QB with WR/TE in DFS formats")
    
    print("\n🔧 NEXT STEPS:")
    print("• Add your actual roster players to the roster lists")
    print("• Set up your specific league scoring in league_configs.py")
    print("• Run analysis weekly to optimize your lineups")
    print("• Use trade analyzer before making any deals")
    print("• Check waiver targets every Tuesday night")
    
    if not api_key:
        print("\n🚨 IMPORTANT:")
        print("This was a demo run. To get real betting line data:")
        print("1. Sign up at https://the-odds-api.com (free tier available)")
        print("2. Add your API key to .env file: ODDS_API_KEY=your_key_here")
        print("3. Run this script again for live data")


if __name__ == "__main__":
    main()
