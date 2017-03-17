from mdata import disk
from mdata.log import Logger
from selenium import webdriver
from mdata.database import Instance
from cores.fetcher import AmazonApiFetcher,AmazonApiError
import os
import json
import time


logger = Logger()

def retrive_browse_nodes():
    sql = "select umpay_category, amazon_browse_node, id from umpay_cate_amz_nodes where is_parent_node=0 and is_fetch=0;"
    browse_nodes = DataBase.execute_select_sql(sql)
    return list(browse_nodes)

def update_node_status(node):
    sql = "update umpay_cate_amz_nodes set is_fetch=1 where id=%s;"
    DataBase.execute_update_sql(sql,(node[2],))



def fetch_review_info(product):
    product['goods_review_current_count'] = 0
    product['goods_review_current_stars'] = 0
    if product['goods_review_frame']:
        try:
            html = "<html><body><iframe src=\"{0}\" /></body></html>".format(product['goods_review_frame'])
            Browser.execute_script("document.write('{}')".format(json.dumps(html)))
            iframe_ele = Browser.find_element_by_xpath("//iframe")
            Browser.switch_to.frame(iframe_ele)
            review_star_ele = Browser.find_element_by_xpath("//span[@class='crAvgStars']/span//img")
            review_count_ele = Browser.find_element_by_xpath("//span[@class='crAvgStars']/a")
            review_count = review_count_ele.text.split(' ')[0].replace(',','')
            review_star = review_star_ele.get_attribute("title").split(' ')[0]
            product['goods_review_current_count'] = int(review_count)
            product['goods_review_current_stars'] = float(review_star)
        except Exception as err:
            logger.message(product["goods_asin"] + " : " + str(err))
        finally:
            Browser.switch_to.default_content()
            Browser.refresh()
    return product



def fetch_top_products(node):
    try:
        top_asins = Fetcher.fetch_node_top_seller(node[1])
        time.sleep(1.5)
        for asin in top_asins:
            product = Fetcher.fetch_product_by_asin(asin)
            if product:
                item = fetch_review_info(product)
                item['goods_asin'] = asin
                item['goods_browse_node'] = node[1]
                item['goods_category'] = node[0]
                item['goods_dimensions'] = json.dumps(item['goods_dimensions'])
                DataBase.insert_item_by_schema(item,"umpay_amazon_data",
                                               ["goods_review_current_count","goods_review_current_stars", "goods_browse_node"])
                logger.message("Successfully Fetched Product(" + item['goods_asin'] + ")")
            time.sleep(1.5)
        update_node_status(node)
    except Exception as err:
        logger.message(str(err))
    return False



def main():
    browse_nodes = retrive_browse_nodes()
    while True:
        node = browse_nodes.pop()
        logger.message("Fetch Products For Node: " + str(node[1]))
        fetch_top_products(node)
        if len(browse_nodes) == 0: break
    Browser.quit()



if __name__=="__main__":
    DB_CFG = disk.read_json_configure("Confs/db_cfg.json")
    AWS_CFG = disk.read_json_configure("Confs/aws_cfg.json")
    DataBase = Instance(**DB_CFG)
    Fetcher = AmazonApiFetcher(**AWS_CFG)
    Browser = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), 'chromedriver'))
    main()