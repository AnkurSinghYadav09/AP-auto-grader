import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.github_evaluator import GitHubProjectEvaluator
from src.google_api import GoogleAPIHandler
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'github_evaluation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def format_contributor_info(contributors_data: dict) -> str:
    """Format contributor data for spreadsheet"""
    if not contributors_data:
        return "No contributor data available"
    
    lines = []
    for username, data in contributors_data.items():
        name = data.get('name', username)
        commits = data.get('commits', 0)
        pct = data.get('contribution_percentage', 0)
        net = data.get('net_lines', 0)
        lines.append(f"{name}: {commits} commits ({pct}%) | {net:+d} lines")
    
    return '\n'.join(lines)

def format_evaluation_feedback(results: dict, contributors_data: dict) -> str:
    """Format evaluation results into readable feedback"""
    breakdown = results.get('breakdown', {})
    
    feedback = f"""SCORE: {results.get('total_score', 0)}/100

BREAKDOWN:
- Frontend: {breakdown.get('frontend', 0)}/25
- Backend: {breakdown.get('backend', 0)}/25
- Code Quality: {breakdown.get('code_quality', 0)}/20
- Git Practices: {breakdown.get('git_practices', 0)}/15
- Individual Contributions: {breakdown.get('individual_contributions', 0)}/15

INDIVIDUAL SCORES:"""
    
    individual_scores = results.get('individual_scores', {})
    if individual_scores:
        for username, score in individual_scores.items():
            # Try to get the real name from contributors data
            name = username
            if contributors_data and username in contributors_data:
                name = contributors_data[username].get('name', username)
            feedback += f"\n- {name}: {score}/100"
    else:
        feedback += "\n- No individual scores available"
    
    feedback += f"""

STRENGTHS:
{chr(10).join('- ' + s for s in results.get('strengths', ['None identified']))}

AREAS FOR IMPROVEMENT:
{chr(10).join('- ' + w for w in results.get('weaknesses', ['None identified']))}

RECOMMENDATIONS:
{chr(10).join('- ' + r for r in results.get('recommendations', ['None provided']))}

DETAILED FEEDBACK:
{results.get('detailed_feedback', 'No detailed feedback available')}
"""
    
    return feedback

def main():
    """Main execution function - Evaluates one project at a time"""
    try:
        logger.info("=" * 60)
        logger.info("Starting GitHub Repository Evaluation")
        logger.info("=" * 60)
        
        # Validate configuration
        try:
            Config.validate()
            logger.info("Configuration validated successfully")
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return
        
        # Initialize handlers
        logger.info("Initializing evaluator and Google API handler...")
        evaluator = GitHubProjectEvaluator()
        google_handler = GoogleAPIHandler()
        
        # Read repository links from Google Sheet
        logger.info(f"Reading data from Google Sheet: {Config.SPREADSHEET_ID}")
        logger.info(f"Sheet name: {Config.SHEET_NAME}")
        
        # Read rows from Google Sheet (starting from row 2 to skip header)
        range_notation = "B2:G"
        rows = google_handler.read_sheet_rows(range_notation)
        
        if not rows:
            logger.warning("No data found in the specified range")
            return
        
        logger.info(f"Found {len(rows)} repositories to evaluate")
        
        success_count = 0
        error_count = 0
        
        for i, row in enumerate(rows, start=2):
            # Row contains: B(0), C(1), D(2), E(3), F(4), G(5)
            # B = Team Name (index 0)
            # G = Repo URL (index 5)
            if len(row) < 6 or not row[5]:
                logger.warning(f"Row {i}: Skipping - no repository URL in column G")
                continue
            
            team_name = row[0].strip() if row[0] else f"Team_{i}"
            repo_url = row[5].strip()  # Column G is at index 5
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing Row {i}: {team_name}")
            logger.info(f"Repository: {repo_url}")
            logger.info(f"{'='*60}")
            
            try:
                # Step 1: Clone repository
                logger.info("Step 1: Cloning repository...")
                local_path = evaluator.clone_repo(repo_url, team_name)
                logger.info(f"✓ Repository cloned to: {local_path}")
                
                # Step 2: Analyze contributors (requires GitHub API token)
                logger.info("Step 2: Analyzing contributors...")
                contributors_data = evaluator.analyze_contributors(repo_url)
                if contributors_data:
                    logger.info(f"✓ Analyzed {len(contributors_data)} contributors")
                else:
                    logger.warning("⚠ No contributor data available (GitHub token may not be configured)")
                
                # Step 3: Evaluate project
                logger.info("Step 3: Evaluating project with AI...")
                evaluation_results = evaluator.evaluate_project(
                    local_path,
                    contributors_data
                )
                logger.info(f"✓ Evaluation complete. Score: {evaluation_results.get('total_score', 0)}/100")
                
                # Step 4: Format results
                logger.info("Step 4: Formatting results...")
                score = evaluation_results.get('total_score', 0)
                feedback = format_evaluation_feedback(evaluation_results, contributors_data)
                contributor_info = format_contributor_info(contributors_data)
                
                # Step 5: Write to Google Sheet IMMEDIATELY for this project
                logger.info("Step 5: Writing results to Google Sheet...")
                
                # Write score to column J
                score_cell = f"J{i}"
                google_handler.write_to_cell(score_cell, score)
                logger.info(f"✓ Score written to {score_cell}")
                
                # Write feedback to column K
                feedback_cell = f"K{i}"
                google_handler.write_to_cell(feedback_cell, feedback)
                logger.info(f"✓ Feedback written to {feedback_cell}")
                
                # Write contributor info to column L (if configured)
                if Config.CONTRIBUTORS_COLUMN and contributor_info:
                    contrib_cell = f"L{i}"
                    google_handler.write_to_cell(contrib_cell, contributor_info)
                    logger.info(f"✓ Contributors written to {contrib_cell}")
                
                # Step 6: Cleanup (optional - comment out to keep clones)
                logger.info("Step 6: Cleaning up...")
                evaluator.cleanup_clone(local_path)
                logger.info(f"✓ Cleaned up cloned repository")
                
                logger.info(f"\n✅ Successfully completed evaluation for {team_name}")
                success_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {team_name}: {e}", exc_info=True)
                
                # Write error message to feedback column
                try:
                    error_feedback = f"Evaluation failed: {str(e)}\n\nPlease check:\n- Repository URL is correct\n- Repository is public or token has access\n- Repository is not empty"
                    feedback_cell = f"K{i}"
                    google_handler.write_to_cell(feedback_cell, error_feedback)
                    logger.info(f"✓ Error message written to {feedback_cell}")
                except Exception as write_error:
                    logger.error(f"Failed to write error message to sheet: {write_error}")
                
                continue
        
        logger.info("\n" + "=" * 60)
        logger.info("GitHub Repository Evaluation Complete!")
        logger.info(f"✅ Success: {success_count} | ❌ Errors: {error_count}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\n\nEvaluation interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
