from mdata import disk
from mdata.database import Instance
from cores.fetcher import AmazonApiFetcher


def test():
    products = Fetcher.fetch_products_by_search("FashionWomen",Sort="salesrank,reviewrank",BrowseNode='9056995011')
    print(products)


if __name__=="__main__":
    DB_CFG = disk.read_json_configure("Confs/db_cfg.json")
    AWS_CFG = disk.read_json_configure("Confs/aws_cfg.json")
    DataBase = Instance(**DB_CFG)
    Fetcher = AmazonApiFetcher(**AWS_CFG)
    test()
