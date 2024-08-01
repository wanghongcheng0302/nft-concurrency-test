from wujie_nft_server.models.base import db
from wujie_nft_server.models.order import Order
from wujie_nft_server.models.goods import (
    MysteryBox,
    NormalBox,
    normal_mystery_association_table,
)


def cleanup_order():
    """清理订单表"""
    count = Order.query.count()
    if count:
        Order.query.delete()
        db.session.commit()
        return True, count
    return False, 0


def cleanup_mystery_box():
    """清理盲盒表"""
    count = MysteryBox.query.count()
    if count:
        for item in MysteryBox.query.all():
            item.normal_boxs.clear()
        MysteryBox.query.delete()
        db.session.commit()
        return True, count
    return False, 0


def cleanup_normal_box():
    """清理普通商品表"""
    count = NormalBox.query.count()
    if count:
        for item in NormalBox.query.all():
            item.mystery_boxs.clear()
        NormalBox.query.delete()
        db.session.commit()
        return True, count
    return False, 0
