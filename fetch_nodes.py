from mdata import disk
from mdata.log import Logger
from mdata.database import Instance
from cores.fetcher import AmazonApiFetcher,AmazonApiError
import time

logger = Logger()

def _retrive_bn_frm_db():
    sql = "select umpay_category, amazon_browse_node from umpay_cate_amz_nodes where id in (4,5,6,7,4568,4569);"
    browse_nodes = DataBase.execute_select_sql(sql)
    return list(browse_nodes)

def _save_node_to_db(data):
    sql = "insert into umpay_cate_amz_nodes (umpay_category, amazon_browse_node, is_parent_node) values (%s,%s,0);"
    try:
        DataBase.execute_update_sql(sql,data)
    except Exception:
        pass


def start_fetch_sub_nodes(parent_nodes):
    fetched_node = []
    endFetch = False
    while not endFetch:
        node = parent_nodes.pop()
        logger.message("Fetch Node: " + str(node[1]))
        try:
            sub_nodes = Fetcher.fetch_all_child_nodes(node[1])
            fetched_node.append(node[1])
            for n in sub_nodes:
                if n not in fetched_node:
                    insert_data = (node[0], n)
                    parent_nodes.append(insert_data)
                    _save_node_to_db(insert_data)
            time.sleep(1.5)
            if len(parent_nodes) == 0 : endFetch = True
        except AmazonApiError as err:
            if err.code == 0: parent_nodes.append(node)


def main():
    parent_nodes = _retrive_bn_frm_db()
    start_fetch_sub_nodes(parent_nodes)



if __name__=="__main__":
    DB_CFG = disk.read_json_configure("Confs/db_cfg.json")
    AWS_CFG = disk.read_json_configure("Confs/aws_cfg.json")
    DataBase = Instance(**DB_CFG)
    Fetcher = AmazonApiFetcher(**AWS_CFG)
    main()
