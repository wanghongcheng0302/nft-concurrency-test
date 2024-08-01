from flask import Flask
from flask_migrate import Migrate
from wujie_nft_server.models.base import db, BaseModel
from wujie_nft_server.models.order import Order
from wujie_nft_server.handlers import db as db_handlers
from wujie_nft_server.models.goods import (
    MysteryBox,
    NormalBox,
    normal_mystery_association_table,
)
from wujie_nft_server.settings import DATABASE_URL
import click, time

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ECHO"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)


@app.cli.command()
def cleanup_mock():
    """清理mock数据"""
    start_time = time.time()
    result, count = db_handlers.cleanup_order()
    end_time = time.time()
    duration = end_time - start_time
    if result:
        click.echo(
            f"Deleted {count} records from the orders table in {duration:.2f} seconds."
        )
    else:
        click.echo(f"No records were deleted from the orders table.")

    start_time = time.time()
    result, count = db_handlers.cleanup_normal_box()
    end_time = time.time()
    duration = end_time - start_time
    if result:
        click.echo(
            f"Deleted {count} records from the normal-box table in {duration:.2f} seconds."
        )
    else:
        click.echo(f"No records were deleted from the normal-box table.")

    start_time = time.time()
    result, count = db_handlers.cleanup_mystery_box()
    end_time = time.time()

    duration = end_time - start_time
    if result:
        click.echo(
            f"Deleted {count} records from the mystery-box table in {duration:.2f} seconds."
        )
    else:
        click.echo(f"No records were deleted from the mystery-box table.")


@app.cli.command()
def setup_mock():
    """设置mock数据"""
    # 创建普通商品
    normal_box_1 = NormalBox(total_stock=10000)
    normal_box_2 = NormalBox(total_stock=10000)
    db.session.add(normal_box_1)
    db.session.add(normal_box_2)

    # 创建盲盒
    mystery_box = MysteryBox(total_stock=5000)
    mystery_box.normal_boxs.append(normal_box_1)
    mystery_box.normal_boxs.append(normal_box_2)
    db.session.add(mystery_box)

    db.session.commit()

    click.echo("done")


from wujie_nft_server.api import v1
from wujie_nft_server.api import v2


"""debug cases
$cwd=${workspaceFolder}/wujie_nft_server; python -m flask db init
$cwd=${workspaceFolder}/wujie_nft_server; python -m flask db migrate -m "Initial migration."
$cwd=${workspaceFolder}/wujie_nft_server; python -m flask db upgrade
$cwd=${workspaceFolder}/wujie_nft_server; python -m flask cleanup-mock
$cwd=${workspaceFolder}/wujie_nft_server; python -m flask setup-mock
$cwd=${workspaceFolder}/wujie_nft_server; python -m flask run --port 8080
$cwd=${workspaceFolder}; python -m gunicorn --bind 0.0.0.0:8080 --timeout 10 wujie_nft_server.app:app
"""
