"""
Truy xuất ngược & chia sẻ giá trị (Royalty)

Khi 1 giống lai được thương mại hoá, royalty được chia ngược cho người tạo ra
các Genesis Block tổ tiên, theo đúng tỉ lệ đóng góp gen thực tế (genesis_contributions).
Đây là logic sẽ nằm trong Smart Contract (xem contracts/GeneBlock.sol: distributeRoyalty).
"""


def royalty_split(dag, token_id: int, sale_amount: float, royalty_rate: float = 0.10) -> dict:
    """
    Trả về {creator: số tiền} cho các creator của genesis ancestors.
    Phần còn lại (1 - royalty_rate) thuộc về người bán/chủ sở hữu hiện tại.
    """
    pool = round(sale_amount * royalty_rate, 2)
    contrib = dag.genesis_contributions(token_id)
    split = {}
    for genesis_id, weight in contrib.items():
        creator = dag.get(genesis_id).creator
        split[creator] = round(split.get(creator, 0) + pool * weight, 2)
    return {"royalty_pool": pool, "seller_keeps": round(sale_amount - pool, 2),
            "contributions": contrib, "payouts": split}
