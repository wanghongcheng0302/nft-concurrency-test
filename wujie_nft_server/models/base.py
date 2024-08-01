from sqlalchemy.ext.declarative import declarative_base
from wujie_nft_server.settings import DATABASE_URL
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BaseModel = declarative_base()
