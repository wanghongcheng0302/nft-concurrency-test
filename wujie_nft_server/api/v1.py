from wujie_nft_server.app import app
import time
from wujie_nft_server.models.base import db
from wujie_nft_server.models.goods import MysteryBox
from wujie_nft_server.models.order import Order, OrderStatus
from flask import jsonify, request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload
import random
from threading import Timer
from functools import partial
from wujie_nft_server.handlers.order import cancle_order


@app.route("/v1/mystery-box/detail/")
def mystery_box_detail_v1():
    box = MysteryBox.query.first()
    box_dict = jsonable_encoder(box)
    return jsonify(box_dict)


@app.route("/v1/mystery-box/order/")
def mystery_box_order_v1():
    """盲盒下单

    下单流程:

        1. 获取第一条盲盒记录A
        2. 获取盲盒A名下所有普通商品a, b, c ...
        3. 将a, b, c ... 表锁住, 并从其中所有记录中抽取1条, a1, a2, b1, b2, c1, c2 ... 抽取b1
        4. 若抽取到X, 则返回支付链接, 同时发起5分钟订单监控, 并将订单状态设置为 pending
        5. 若用户支付成功, 则触发微信回调接口
        6. 若任何异常情况包括取消支付, 则在5分钟后, 关闭订单, 状态设置为 system-cancelled


    验证:
        1. 所有状态为 completed 的订单总数 + 未交易的商品数, 应等于商品总数

    """

    """
    执行这行完成, 并打断点

    在mysql命令行执行`SELECT * FROM performance_schema.data_locks;`
    INNODB,5155524504:1064:5307951272,1904,64,12,nft,mystery-box,,,,5307951272,TABLE,IX,GRANTED,
    INNODB,5155524504:3:4:2:5310586904,1904,64,12,nft,mystery-box,,,PRIMARY,5310586904,RECORD,"X,REC_NOT_GAP",GRANTED,1

    同时有TABLE和RECORD锁
    此时执行`UPDATE `mystery-box` SET total_stock = 5000 WHERE id=1;` 会被阻塞, 说明行锁生效
    可以执行INSERT, 可能因为表锁的类型是 意向排他锁 (Intent Exclusive lock)，表示事务有意图获得排他锁

    默认情况会在接口执行完释放锁
    主动释放可以使用`db.session.commit()`或者`with db.session.begin_nested()`
    
    """

    # 校验盲盒库存
    try:
        # joinedload会构造join语句, 同时把关联表锁住
        with db.session.begin():
            mystery_box = (
                db.session.query(MysteryBox)
                .options(joinedload(MysteryBox.normal_boxs))
                .filter()
                .with_for_update()
                .first()
            )

            if mystery_box.current_stock is None:
                mystery_box.current_stock = mystery_box.total_stock

            if mystery_box.current_stock <= 0:
                return "盲盒库存不足", 400

            # 校验普通商品库存
            # 筛选出库存数量为None或者大于0的商品
            normal_boxs = [
                item
                for item in mystery_box.normal_boxs
                if item.current_stock is None or item.current_stock > 0
            ]
            # 随机抽取一个商品, 并扣减库存
            for_sale = random.choice(normal_boxs)
            if for_sale.current_stock is None:
                for_sale.current_stock = for_sale.total_stock - 1
            else:
                for_sale.current_stock -= 1

            # 扣减盲盒库存
            mystery_box.current_stock -= 1

            # 创建订单
            order = Order()
            order.status = OrderStatus.PENDING
            order.normal_box_id = for_sale.id
            order.mystery_box_id = mystery_box.id
            db.session.add(order)
            db.session.commit()

    except Exception as e:
        db.session.rollback()
        return f"未知错误: {e}, 执行回滚", 400

    # 创建后台订单监控任务
    timer = Timer(
        30,
        partial(
            cancle_order,
            order.id,
        ),
    )
    timer.start()

    return str(order.id)


@app.route("/v1/mystery-box/order-callback/")
def mystery_box_order_callback_v1():
    order_id = request.form.get("order_id")
    order_id = int(order_id)
    # 修改订单状态时也需要锁order表, 因为微信回调和自动取消订单是并行执行的, 可能造成多次commit
    try:
        with db.session.begin():
            order = Order.query.filter_by(id=order_id).with_for_update().first()
            if order.status != OrderStatus.PENDING:
                return "订单状态异常", 400
            order.status = OrderStatus.COMPLETED
    except Exception as e:
        app.logger.error(f"微信回调遇到异常: {e}, 执行库存回滚")

        # FIXME: 如何保证下面的逻辑一定执行成功?
        with db.session.begin():
            order = Order.query.filter_by(id=order_id).with_for_update().first()
            order.status = OrderStatus.FAILED
            order.mystery_boxs.current_stock += 1
            order.normal_boxs.current_stock += 1
            db.session.commit()

        return f"微信回调遇到异常: {e}, 执行库存回滚", 400

    return "订单已完成"


@app.route("/v1/mystery-box/order-cancle/")
def mystery_box_order_cancle_v1():
    order_id = request.form.get("order_id")
    order_id = int(order_id)
    result = cancle_order(order_id, True)
    if result:
        return "取消订单成功"
    return "取消订单失败"
