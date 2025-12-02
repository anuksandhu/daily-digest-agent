"""
Daily Digest Generator
Main entry point for generating the daily digest using Google ADK agents
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

from utils.logging import setup_logging, setup_tracing, get_logger
from utils.metrics import MetricsCollector
from utils.validation import DigestValidator

# Import tools
from tools.weather_tool import get_weather
from tools.sports_tool import get_sports_scores
from tools.tech_news_tool import get_tech_news
from tools.market_tool import get_market_data

from utils.config import get_config

async def generate_digest():
    """
    Main function to generate the daily digest
    Orchestrates all agents and tools to create the digest
    """
    
    # ========================================================================
    # Setup
    # ========================================================================
    config = get_config()
    setup_logging(config.log_level)
    tracer = setup_tracing(config.enable_tracing)
    logger = get_logger()
    metrics = MetricsCollector()
    
    logger.info("=" * 70)
    logger.info("Starting Daily Digest Generation")
    logger.info("=" * 70)
    
    metrics.start_timer("generation.total")
    
    try:
        # ====================================================================
        # Create Retry Configuration
        # ====================================================================
        retry_config = types.HttpRetryOptions(
            attempts=config.max_retries,
            exp_base=config.retry_exp_base,
            initial_delay=config.initial_retry_delay,
            http_status_codes=[429, 500, 503, 504]
        )
        
        logger.info(f"Using model: {config.model_name}")
        logger.info(f"Max retries: {config.max_retries}")
        
        # ====================================================================
        # Create Tools
        # ====================================================================
        logger.info("Creating function tools")
        
        weather_tool = FunctionTool(get_weather)
        sports_tool = FunctionTool(get_sports_scores)
        tech_tool = FunctionTool(get_tech_news)
        market_tool = FunctionTool(get_market_data)
        
        tools = [weather_tool, sports_tool, tech_tool, market_tool]
        logger.info(f"Created {len(tools)} tools")
        
        # ====================================================================
        # Create Coordinator Agent
        # ====================================================================
        logger.info("Creating coordinator agent")
        
        config = get_config()

        coordinator_agent = LlmAgent(
            model=Gemini(
                model=config.model_name,
                retry_options=retry_config
            ),
            name="digest_coordinator",
            description="Coordinates content gathering for Daily Digest",
            instruction=f"""
            You are the Daily Digest coordinator. Your job is to gather current, 
            factual information for today's digest.
            
            CRITICAL REQUIREMENTS:
            1. ALL data must be current (within last 24 hours)
            2. ALL data must be from reliable sources
            3. NO fabricated or mock information allowed
            4. Include source attribution for all data
            5. If a tool fails, note the error but continue with other sections
            
            YOUR TASKS:
            1. Use get_weather tool for {config.default_location} weather
            2. Use get_sports_scores tool for 49ers, Sharks, Warriors
            3. Use get_tech_news tool for AI and technology news (top 5)
            4. Use get_market_data tool for S&P 500, NASDAQ, DOW JONES
            
            OUTPUT FORMAT:
            Return a JSON object with this structure:
            {
                "date": "YYYY-MM-DD",
                "generated_at": "ISO timestamp",
                "sections": [
                    {
                        "name": "weather",
                        "data": <weather_tool_output>,
                        "timestamp": "ISO timestamp",
                        "source": "source name"
                    },
                    {
                        "name": "sports",
                        "data": <sports_tool_output>,
                        "timestamp": "ISO timestamp",
                        "source": "source name"
                    },
                    {
                        "name": "tech",
                        "data": <tech_tool_output>,
                        "timestamp": "ISO timestamp",
                        "source": "source name"
                    },
                    {
                        "name": "market",
                        "data": <market_tool_output>,
                        "timestamp": "ISO timestamp",
                        "source": "source name"
                    }
                ]
            }
            
            CRITICAL: Your response MUST be ONLY valid JSON in the exact format shown above. 
            Do NOT include any explanatory text. Do NOT use markdown code blocks.
            Output ONLY the raw JSON object starting with { and ending with }.
            """,
            tools=tools
        )
        
        # ====================================================================
        # Create Session and Runner
        # ====================================================================
        logger.info("Setting up session management")
        
        session_service = InMemorySessionService()
        session_id = f"digest-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        session = await session_service.create_session(
            app_name="daily-digest",
            user_id="system",
            session_id=session_id
        )
        
        logger.info(f"Created session: {session_id}")
        
        runner = Runner(
            agent=coordinator_agent,
            app_name="daily-digest",
            session_service=session_service
        )
        
        # ====================================================================
        # Execute Agent
        # ====================================================================
        logger.info("Executing coordinator agent")
        metrics.start_timer("agent.coordinator")
        
        user_message = types.Content(
            parts=[types.Part(text=f"""
            Generate today's Daily Digest ({datetime.now().strftime('%Y-%m-%d')}).
            
            Fetch data for:
            - Weather: {config.default_location}
            - Sports: San Francisco 49ers (NFL), San Jose Sharks (NHL), Golden State Warriors (NBA)
            - Tech News: Top 5 AI and technology stories
            - Markets: S&P 500 (^GSPC), NASDAQ (^IXIC), DOW JONES (^DJI)
            
            Return results as structured JSON following the format in your instructions.
            """)]
        )
        
        results = []
        async for event in runner.run_async(
            user_id="system",
            session_id=session_id,
            new_message=user_message
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text'):
                        results.append(part.text)
        
        coordinator_duration = metrics.stop_timer("agent.coordinator", {
            "agent": "coordinator",
            "type": "agent"
        })
        
        logger.info(f"Agent execution completed", duration_ms=coordinator_duration)
        
        # ====================================================================
        # Parse Results
        # ====================================================================
        logger.info("Parsing agent results")
        
        if not results:
            raise ValueError("No results from agent")
        
        # Extract JSON from agent response
        response_text = results[0]
        response_text = response_text.replace("False", "false").replace("True", "true")  # ← ADD THIS LINE
        logger.debug(f"Raw response: {response_text[:500]}...")
        
        # Try to extract JSON (agent might wrap it in markdown code blocks)
        json_text = response_text
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            digest_data = json.loads(json_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, trying to extract from text")
            # If JSON parsing fails, create structure from raw text
            digest_data = {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "generated_at": datetime.now().isoformat(),
                "sections": [],
                "raw_response": response_text
            }
        
        logger.info("Results parsed successfully")
        
        # ====================================================================
        # Validate Data Quality
        # ====================================================================
        logger.info("Validating data quality")
        
        validator = DigestValidator()
        is_valid, validation_errors = validator.validate(digest_data)
        quality_score = validator.calculate_quality_score(digest_data)
        
        metrics.record("quality.completeness.score", quality_score)
        metrics.record("quality.validation.errors", len(validation_errors))
        
        if not is_valid:
            logger.warning(
                f"Validation found {len(validation_errors)} issues",
                errors=validation_errors
            )
        else:
            logger.info("Data validation passed")
        
        # ====================================================================
        # Generate Outputs
        # ====================================================================
        logger.info("Generating output files")
        
        output_dir = Path(__file__).parent.parent / "docs"
        output_dir.mkdir(exist_ok=True)
        
        # Save JSON
        json_path = output_dir / "digest.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(digest_data, f, indent=2)
        logger.info(f"Saved: {json_path}")
        
        # Generate HTML
        html_path = output_dir / "index.html"
        html_content = generate_html(digest_data)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved: {html_path}")
        
        # Save metrics
        total_duration = metrics.stop_timer("generation.total")
        metrics.record("generation.success", 1.0)
        
        metrics_path = output_dir / "metrics.json"
        metrics.save(metrics_path)
        logger.info(f"Saved: {metrics_path}")
        
        # ====================================================================
        # Summary
        # ====================================================================
        logger.info("=" * 70)
        logger.info("Daily Digest Generation Complete!")
        logger.info("=" * 70)
        logger.info(f"Total duration: {total_duration:.0f}ms")
        logger.info(f"Quality score: {quality_score:.2f}")
        logger.info(f"Output files: {output_dir}/")
        logger.info("=" * 70)
        
        return digest_data
        
    except Exception as e:
        metrics.stop_timer("generation.total")
        metrics.increment("generation.error")
        logger.critical("Failed to generate digest", exception=e)
        raise


def generate_html(digest_data: dict) -> str:
    """
    Generate HTML from digest data
    Simple template for now - can be enhanced with Jinja2
    """
    
    date = digest_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    timestamp = digest_data.get('generated_at', datetime.now().isoformat())
    sections = digest_data.get('sections', [])
    
    # Find section data
    weather_data = next((s for s in sections if s.get('name') == 'weather'), {}).get('data', {})
    sports_data = next((s for s in sections if s.get('name') == 'sports'), {}).get('data', {})
    tech_data = next((s for s in sections if s.get('name') == 'tech'), {}).get('data', {})
    market_data = next((s for s in sections if s.get('name') == 'market'), {}).get('data', {})
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Digest - {date}</title>
    <meta name="description" content="Your personalized daily digest of weather, sports, tech news, and markets">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        h1 {{ font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .subtitle {{ font-size: 1.2em; opacity: 0.9; }}
        .timestamp {{ font-size: 0.9em; opacity: 0.7; margin-top: 10px; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        .card:hover {{ transform: translateY(-5px); }}
        
        .card-title {{
            font-size: 1.5em;
            margin-bottom: 16px;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-content {{ color: #333; line-height: 1.6; }}
        .item {{ margin: 12px 0; padding: 10px; background: #f8f9fa; border-radius: 6px; }}
        
        footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 2em; }}
            .grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📰 Daily Digest</h1>
            <div class="subtitle">Your Personalized News Hub</div>
            <div class="timestamp">Last updated: {timestamp}</div>
        </header>
        
        <div class="grid">
            {_render_weather_card(weather_data)}
            {_render_sports_card(sports_data)}
            {_render_tech_card(tech_data)}
            {_render_market_card(market_data)}
        </div>
        
        <footer>
            <p>Generated by Daily Digest Agent System</p>
            <p>Powered by Google ADK + Gemini AI</p>
            <p><small>View source on <a href="https://github.com" style="color: white;">GitHub</a></small></p>
        </footer>
    </div>
</body>
</html>"""
    
    return html


def _render_weather_card(data: dict) -> str:
    if 'error' in data:
        return f"""
        <div class="card">
            <h2 class="card-title">🌤️ Weather</h2>
            <div class="card-content">
                <p>Error loading weather data: {data.get('error')}</p>
            </div>
        </div>
        """
    
    current = data.get('current', {})
    forecast = data.get('forecast', [])
    
    forecast_html = ""
    for day in forecast[:5]:
        forecast_html += f'<div class="item">{day.get("date", "")}: {day.get("temp", "")}°F - {day.get("description", "")}</div>'
    
    return f"""
    <div class="card">
        <h2 class="card-title">🌤️ Weather</h2>
        <div class="card-content">
            <h3 style="font-size: 2em;">{current.get('temp', 'N/A')}°F</h3>
            <p>{current.get('description', 'No data')}</p>
            <p>Feels like: {current.get('feels_like', 'N/A')}°F | Humidity: {current.get('humidity', 'N/A')}%</p>
            <h4 style="margin-top: 16px;">5-Day Forecast:</h4>
            {forecast_html}
        </div>
    </div>
    """


def _render_sports_card(data: dict) -> str:
    teams = data.get('teams', [])
    
    teams_html = ""
    for team in teams:
        teams_html += f"""
        <div class="item">
            <strong>{team.get('name', 'Unknown')}</strong> ({team.get('league', '')})<br>
            Record: {team.get('record', 'N/A')}<br>
            Latest: {team.get('latest_game', 'No recent games')}<br>
            Next: {team.get('next_game', 'No upcoming games')}
        </div>
        """
    
    return f"""
    <div class="card">
        <h2 class="card-title">🏈 Sports</h2>
        <div class="card-content">
            {teams_html if teams_html else '<p>No sports data available</p>'}
        </div>
    </div>
    """


def _render_tech_card(data: dict) -> str:
    articles = data.get('articles', [])
    
    articles_html = ""
    for article in articles[:5]:
        articles_html += f"""
        <div class="item">
            <strong>{article.get('title', 'No title')}</strong><br>
            <small>{article.get('source', 'Unknown source')} • {article.get('published_at', '')[:10]}</small>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2 class="card-title">💻 Tech News</h2>
        <div class="card-content">
            {articles_html if articles_html else '<p>No tech news available</p>'}
        </div>
    </div>
    """


def _render_market_card(data: dict) -> str:
    indexes = data.get('indexes', [])
    summary = data.get('market_summary', 'Market data unavailable')
    
    indexes_html = ""
    for index in indexes:
        change_class = 'positive' if index.get('is_positive') else 'negative'
        color = '#22c55e' if index.get('is_positive') else '#ef4444'
        indexes_html += f"""
        <div class="item" style="display: flex; justify-content: space-between;">
            <span>{index.get('name', 'Unknown')}</span>
            <span style="color: {color};">{index.get('value', 0)} ({index.get('change_percent', 0):+.2f}%)</span>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2 class="card-title">📈 Markets</h2>
        <div class="card-content">
            <p style="margin-bottom: 16px;"><em>{summary}</em></p>
            {indexes_html if indexes_html else '<p>No market data available</p>'}
        </div>
    </div>
    """


if __name__ == "__main__":
    asyncio.run(generate_digest())
