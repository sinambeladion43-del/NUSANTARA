import logging
from database import get_db

logger = logging.getLogger(__name__)

async def decrease_hunger_thirst(context):
    """Decrease hunger and thirst every hour for all players"""
    try:
        conn = get_db()
        conn.execute('''UPDATE players SET 
                        hunger = MAX(0, hunger - 5),
                        thirst = MAX(0, thirst - 8)
                        WHERE is_banned = 0''')
        # HP penalty for starving players
        conn.execute('''UPDATE players SET 
                        hp = MAX(1, hp - 5)
                        WHERE hunger = 0 OR thirst = 0''')
        conn.commit()
        conn.close()
        logger.info("Hunger/thirst decreased for all players")
    except Exception as e:
        logger.error(f"Error in decrease_hunger_thirst: {e}")

async def reset_daily_quests(context):
    """Reset daily quests every 24 hours"""
    try:
        conn = get_db()
        conn.execute("DELETE FROM player_quests WHERE claimed=1")
        conn.commit()
        conn.close()
        logger.info("Daily quests reset")
    except Exception as e:
        logger.error(f"Error in reset_daily_quests: {e}")

def setup_jobs(app):
    """Setup all scheduled jobs"""
    job_queue = app.job_queue

    # Decrease hunger/thirst every hour
    job_queue.run_repeating(
        decrease_hunger_thirst,
        interval=3600,
        first=60,
        name="hunger_thirst"
    )

    # Reset daily quests every 24 hours
    job_queue.run_repeating(
        reset_daily_quests,
        interval=86400,
        first=86400,
        name="daily_quest_reset"
    )

    logger.info("All scheduled jobs setup complete!")
