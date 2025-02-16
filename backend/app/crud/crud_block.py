from app.crud.base import CRUDBase
from app.models.block import Block
from app.schemas.block import BlockCreate, BlockUpdate


class CRUDBlock(CRUDBase[Block, BlockCreate, BlockUpdate]):
    pass


block = CRUDBlock(Block)
