#!/usr/bin/env python3
"""
Single Repository Evaluator - Test script
Evaluates a single GitHub repository without Google Sheets integration
Useful for testing and development
"""

import sys
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.github_evaluator import GitHubProjectEvaluator
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def format_results(results: dict, contributors: dict):
    """Format evaluation results for display"""
    output = []
    output.append("\n" + "=" * 70)
    output.append("EVALUATION RESULTS")
    output.append("=" * 70)
    
    # Check for AI detection
    ai_detection = results.get('ai_detection', {})
    total_score = results.get('total_score', 0)
    output.append(f"\nTotal Score: {total_score}/100")
    
    # Show AI detection if any indicators found (not just when detected)
    if ai_detection and ai_detection.get('confidence', 0) > 0:
        detected = ai_detection.get('detected', False)
        confidence = ai_detection.get('confidence', 0)
        impact = ai_detection.get('impact_on_score', 'No impact')
        indicators = ai_detection.get('indicators', [])
        
        if detected:
            output.append("\n⚠️  AI-GENERATED CODE DETECTED")
        else:
            output.append("\n⚠️  AI CODE INDICATORS FOUND (Below Threshold)")
        output.append(f"Confidence: {confidence}%")
        output.append(f"Indicators: {', '.join(indicators) if indicators else 'None'}")
        output.append(f"Impact: {impact}")
    
    breakdown = results.get('breakdown', {})
    output.append("\nSCORE BREAKDOWN:")
    output.append(f"- Frontend: {breakdown.get('frontend', 0)}/25")
    output.append(f"- Backend: {breakdown.get('backend', 0)}/25")
    output.append(f"- Code Quality: {breakdown.get('code_quality', 0)}/20")
    output.append(f"- Git Practices: {breakdown.get('git_practices', 0)}/15")
    output.append(f"- Individual Contributions: {breakdown.get('individual_contributions', 0)}/15")
    
    individual = results.get('individual_scores', {})
    if individual:
        output.append("\nINDIVIDUAL SCORES:")
        for username, score in individual.items():
            name = username
            quality_info = ""
            if contributors and username in contributors:
                name = contributors[username].get('name', username)
                quality_score = contributors[username].get('quality_score', 0)
                if quality_score > 0:
                    quality_info = f" (Quality: {quality_score}/100)"
            output.append(f"- {name}: {score}/100{quality_info}")
    
    # Contributors analysis
    if contributors:
        output.append("\n📈 CONTRIBUTION ANALYSIS:")
        for username, data in contributors.items():
            name = data.get('name', username)
            commits = data.get('commits', 0)
            pct = data.get('contribution_percentage', 0)
            net_lines = data.get('net_lines', 0)
            
            output.append(f"\n   {name}:")
            output.append(f"      Commits: {commits} ({pct}%)")
            output.append(f"      Lines:   {net_lines:+,d}")
            output.append(f"      Files:   {data.get('files_modified', 0)}")
    
    strengths = results.get('strengths', [])
    if strengths:
        output.append("\nSTRENGTHS:")
        for strength in strengths:
            output.append(f"- {strength}")
    
    weaknesses = results.get('weaknesses', [])
    if weaknesses:
        output.append("\nAREAS FOR IMPROVEMENT:")
        for weakness in weaknesses:
            output.append(f"- {weakness}")
    
    recommendations = results.get('recommendations', [])
    if recommendations:
        output.append("\nRECOMMENDATIONS:")
        for rec in recommendations:
            output.append(f"- {rec}")
    
    detailed = results.get('detailed_feedback', '')
    if detailed:
        output.append("\nDETAILED FEEDBACK:")
        output.append(detailed)
    
    output.append("\n" + "=" * 70)
    
    return '\n'.join(output)

def main():
    parser = argparse.ArgumentParser(
        description='Evaluate a single GitHub repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate a repository with automatic team name
  python scripts/evaluate_single_repo.py https://github.com/user/repo

  # Evaluate with custom team name
  python scripts/evaluate_single_repo.py https://github.com/user/repo --team "Team Alpha"

  # Keep the cloned repository after evaluation
  python scripts/evaluate_single_repo.py https://github.com/user/repo --keep
        """
    )
    
    parser.add_argument(
        'repo_url',
        help='GitHub repository URL (e.g., https://github.com/user/repo)'
    )
    
    parser.add_argument(
        '--team',
        default=None,
        help='Team name (default: extracted from repo name)'
    )
    
    parser.add_argument(
        '--keep',
        action='store_true',
        help='Keep cloned repository after evaluation (default: cleanup)'
    )
    
    parser.add_argument(
        '--no-contributors',
        action='store_true',
        help='Skip contributor analysis (faster but less detailed)'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 70)
        logger.info("GitHub Repository Evaluator - Single Repo Mode")
        logger.info("=" * 70)
        
        # Extract team name from URL if not provided
        team_name = args.team
        if not team_name:
            # Extract from URL: https://github.com/user/repo -> repo
            team_name = args.repo_url.rstrip('/').split('/')[-1]
        
        logger.info(f"Repository: {args.repo_url}")
        logger.info(f"Team Name: {team_name}")
        logger.info("")
        
        # Initialize evaluator
        evaluator = GitHubProjectEvaluator()
        
        # Step 1: Clone repository
        logger.info("📥 Step 1: Cloning repository...")
        local_path = evaluator.clone_repo(args.repo_url, team_name)
        logger.info(f"✓ Cloned to: {local_path}")
        
        # Step 2: Analyze contributors
        contributors_data = {}
        if not args.no_contributors:
            logger.info("\n📊 Step 2: Analyzing contributors...")
            contributors_data = evaluator.analyze_contributors(args.repo_url)
            if contributors_data:
                logger.info(f"✓ Found {len(contributors_data)} contributors")
            else:
                logger.warning("⚠ No contributor data (GitHub token may not be configured)")
        else:
            logger.info("\n⏭️  Step 2: Skipping contributor analysis (--no-contributors flag)")
        
        # Step 3: Evaluate project
        logger.info("\n🤖 Step 3: Evaluating with AI (this may take a minute)...")
        evaluation_results = evaluator.evaluate_project(local_path, contributors_data)
        logger.info(f"✓ Evaluation complete")
        
        # Step 4: Display results
        output = format_results(evaluation_results, contributors_data)
        print(output)
        
        # Step 5: Cleanup
        if not args.keep:
            logger.info("\n🧹 Cleaning up...")
            evaluator.cleanup_clone(local_path)
            logger.info(f"✓ Removed {local_path}")
        else:
            logger.info(f"\n📁 Repository kept at: {local_path}")
        
        logger.info("\n✅ Evaluation complete!")
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
