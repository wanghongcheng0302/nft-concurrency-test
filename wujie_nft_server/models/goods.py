from wujie_nft_server.models.base import BaseModel, db
from sqlalchemy import Column, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship


# 普通商品、盲盒多对多关联表
normal_mystery_association_table = Table(
    "normal_mystery",
    db.Model.metadata,
    Column("normal_box_id", Integer, ForeignKey("normal-box.id")),
    Column("mystery_box_id", Integer, ForeignKey("mystery-box.id")),
)


class NormalBox(BaseModel, db.Model):
    """普通商品"""

    __tablename__ = "normal-box"
    id = Column(Integer, primary_key=True)

    orders = relationship("Order", back_populates="normal_boxs")
    mystery_boxs = relationship(
        "MysteryBox",
        secondary=normal_mystery_association_table,
        back_populates="normal_boxs",
    )
    current_stock = Column(Integer, comment="当前库存")
    total_stock = Column(Integer, comment="总库存")


class MysteryBox(BaseModel, db.Model):
    """盲盒"""

    __tablename__ = "mystery-box"
    id = Column(Integer, primary_key=True)
    normal_boxs = relationship(
        "NormalBox",
        secondary=normal_mystery_association_table,
        back_populates="mystery_boxs",
    )
    current_stock = Column(Integer, comment="当前库存")
    total_stock = Column(Integer, comment="总库存")

    orders = relationship("Order", back_populates="mystery_boxs")
