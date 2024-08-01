from wujie_nft_server.models.order import Order, OrderStatus
from wujie_nft_server.models.goods import NormalBox, MysteryBox
from wujie_nft_server.app import app
from wujie_nft_server.models.base import db
from sqlalchemy.orm import joinedload
import logging


def cancle_order(order_id: int, is_user: bool = False):
    """自动取消订单

    Args:
        order_id (int): 订单id
    """
    # 修改订单状态时也需要锁order表, 因为微信回调和自动取消订单是并行执行的, 可能造成多次commit
    with app.app_context():
        try:
            with db.session.begin():
                order = (
                    db.session.query(Order)
                    .options(joinedload(Order.normal_boxs))
                    .options(joinedload(Order.mystery_boxs))
                    .filter_by(id=order_id)
                    .with_for_update()
                    .first()
                )
                if not order:
                    print(f"系统自动取消订单失败: {order_id} 订单未找到")
                    return False
                if order.status == OrderStatus.PENDING:
                    order.status = (
                        OrderStatus.SYSTEMCANCELLED
                        if not is_user
                        else OrderStatus.USERCANCELLED
                    )
                    order.normal_boxs.current_stock += 1
                    order.mystery_boxs.current_stock += 1
                    db.session.commit()
        except Exception as e:
            print(f"系统取消订单错误: {e}")
            return False

        print(f"系统取消订单成功: {order_id}")

    return True
