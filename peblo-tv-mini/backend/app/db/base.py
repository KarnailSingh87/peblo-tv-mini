# Import all the models, so that Base has them before being imported by Alembic
from backend.app.db.session import Base
from backend.app.models.user import User
from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.models.publish_run import PublishRun
