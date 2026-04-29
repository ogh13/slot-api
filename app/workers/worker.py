from arq.connections import RedisSettings
from app.config import settings
from app.workers.tasks import send_reminder, send_waitlist_notification

async def startup(ctx):
    pass

async def shutdown(ctx):
    pass

class WorkerSettings:
    functions = [send_reminder, send_waitlist_notification]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown