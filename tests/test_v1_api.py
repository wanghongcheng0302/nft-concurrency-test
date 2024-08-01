from .users import V1User
from locust import env, runners
import pytest
import time
from wujie_nft_server.app import app
from wujie_nft_server.models.goods import NormalBox, MysteryBox
from wujie_nft_server.models.order import Order, OrderStatus


@pytest.fixture(scope="module")
def environment():
    environment = env.Environment(user_classes=[V1User])
    runner = runners.LocalRunner(environment)
    environment.runner = runner
    return environment


@pytest.fixture(scope="module")
def web_ui(environment):
    web_ui = environment.create_web_ui("127.0.0.1", 8089)
    yield web_ui
    web_ui.stop()


# @pytest.mark.usefixtures("db_session")
def test_create_order(environment, web_ui):

    # Start the runner with 10 users and a spawn rate of 2 users per second
    environment.runner.start(1000, spawn_rate=30)

    # Run the test for 10 seconds
    environment.runner.greenlet.join(timeout=30)

    # Stop the runner
    environment.runner.quit()

    # 等待系统自动关闭订单
    time.sleep(30)

    # 统计销售库存、异常库存、剩余库存, assert
    with app.app_context():
        completed_orders = Order.query.filter(
            Order.status == OrderStatus.COMPLETED
        ).all()
        mystery_box = MysteryBox.query.first()

        # 断言盲盒库存
        assert (
            (mystery_box.current_stock or mystery_box.total_stock) + len(completed_orders) == mystery_box.total_stock
        )

        # 断言商品库存
        normal_boxs = mystery_box.normal_boxs
        for item in normal_boxs:
            normal_box_orders = [
                o for o in completed_orders if o.normal_box_id == item.id
            ]
            assert (item.current_stock or item.total_stock) + len(normal_box_orders) == item.total_stock

"""
environment.runner.start(1000, spawn_rate=10) 简写成 1000/10  1000个用户, 每个用户每秒10个请求

1. 客户端超时时间3s, 用1000/30运行, 五分之一会失败, 两个容器cpu和mem都没有跑满, cpu 数据库20%以内, flask 50%以内
    * rps: 166.3 
    * 失败率: 19%

    Q: 为什么db/server性能有冗余, 但失败率高达19%(3秒内没响应)
    A: gunicorn 模式是同步, workers数量和cpu核数有关系, 在当前环境下通过`ps -ef`看到两个workers
        假设每个请求理论耗时50ms, 1000 / 50 = 20, 也就是说2个workers, 1秒最多处理40个请求, 如果此时有100个请求进来, 60个会排队, 而不是直接中断
        在3秒内始终保持每秒40个请求, 排队超过3秒的请求会关闭连接

    验证: 将gunicorn设置为4个workers, cpu会跑满, 并且qps翻倍, 失败率为0
    结果: rps = 215.4, 失败率: 1%

2. 并发优化的原则:
    * rps, 每秒请求数, 在保证失败率为0的情况下, 应该尽可能提高rps
    * 提高cpu利用率, 可以间接提高rps, 也就是增加workers
    * 满足以下4个条件, 就是高并发高可用系统
        1) rps高
        2) 失败率低(0)
        3) cpu使用率高(间接提高rps)(80%)
        4) 在任何情况下(即使有失败率)业务逻辑都应该正确
"""

"""debug cases
$cwd=${workspaceFolder}/tests; GEVENT_SUPPORT=true; python -m pytest -s test_v1_api.py::test_create_order
"""
