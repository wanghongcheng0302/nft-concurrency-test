from sqlalchemy import Enum
import enum
from wujie_nft_server.models.base import BaseModel, db
from sqlalchemy import Column, Integer, ForeignKey
from wujie_nft_server.models.goods import NormalBox
from sqlalchemy.orm import relationship


class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    USERCANCELLED = "user-cancelled"
    SYSTEMCANCELLED = "system-cancelled"
    FAILED = "failed"


class Order(BaseModel, db.Model):
    """订单"""

    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    status = Column(Enum(OrderStatus), nullable=True)

    normal_box_id = Column(Integer, ForeignKey("normal-box.id"))
    normal_boxs = relationship("NormalBox", back_populates="orders")

    mystery_box_id = Column(Integer, ForeignKey("mystery-box.id"))
    mystery_boxs = relationship("MysteryBox", back_populates="orders")
