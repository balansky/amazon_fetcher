import json
import time

import bottlenose

from mdata import parse

item_path = ".//{0}Items//{0}Item"
attr_paths = {
    "goods_asin_path": ".//{0}ParentASIN",
    "goods_variation_asin_path": ".//{0}ASIN",
    "goods_brand_path": ".//{0}ItemAttributes//{0}Brand",
    "goods_main_image_url_path": ".//{0}LargeImage//{0}URL",
    "goods_color_path": ".//{0}ItemAttributes//{0}Color",
    "goods_model_path": ".//{0}ItemAttributes//{0}Model",
    "goods_mpn_path": ".//{0}ItemAttributes//{0}MPN",
    "goods_size_path": ".//{0}ItemAttributes//{0}Size",
    "goods_title_path": ".//{0}ItemAttributes//{0}Title",
    "goods_upc_path": ".//{0}ItemAttributes//{0}UPC",
    "goods_url_path": ".//{0}DetailPageURL",
    "goods_review_frame_path": ".//{0}CustomerReviews//{0}IFrameURL",
    "goods_currency_path": [".//{0}Offers//{0}Offer//{0}OfferListing//{0}SalePrice//{0}CurrencyCode",
                            ".//{0}Offer//{0}Price//{0}CurrencyCode",
                            ".//{0}OfferSummary//{0}LowestNewPrice//{0}CurrencyCode",
                            ".//{0}ItemAttributes//{0}ListPrice//{0}CurrencyCode"],
    "decimal_goods_original_price_path": [".//{0}Offers//{0}Offer//{0}OfferListing//{0}SalePrice//{0}FormattedPrice",
                           ".//{0}Offers//{0}Offer//{0}OfferListing//{0}Price//{0}FormattedPrice",
                           ".//{0}OfferSummary//{0}LowestNewPrice//{0}FormattedPrice",
                           ".//{0}ItemAttributes//{0}ListPrice//{0}FormattedPrice"],
    "decimal_goods_original_mrsp_price_path": [".//{0}Offers//{0}Offer//{0}OfferListing//{0}Price//{0}FormattedPrice",
                                               ".//{0}OfferSummary//{0}LowestNewPrice//{0}FormattedPrice",
                                               ".//{0}ItemAttributes//{0}ListPrice//{0}FormattedPrice"],
    "goods_browse_node_path": ".//{0}BrowseNodes//{0}BrowseNode//{0}BrowseNodeId",
    "goods_availability_path": ".//{0}Offer//{0}Availability",
    "goods_description_path": ".//{0}EditorialReviews//{0}EditorialReview//{0}Content",
    "list_goods_feature_path": ".//{0}ItemAttributes//{0}Feature",
    "list_goods_image_url_path": ".//{0}ImageSets//{0}ImageSet//{0}LargeImage//{0}URL",
    "dict_goods_dimensions_path": ".//{0}ItemAttributes//{0}ItemDimensions"
}

child_browse_node_path=".//{0}BrowseNodes//{0}BrowseNode//{0}Children//{0}BrowseNode"
is_category_path = ".//{0}IsCategoryRoot"
top_seller_asin_path = ".//{0}TopSellers//{0}TopSeller//{0}ASIN"
node_id_path = ".//{0}BrowseNodeId"


class AmazonApiError(Exception):
    def __init__(self, err_code):
        self.code = err_code

    def __str__(self):
        if self.code == 0:
            return "Connection Error!"
        else:
            return "Parse Error!"


class AmazonApiFetcher():

    def __init__(self,**kwargs):
        self.AWS_ACCESS_KEY_ID = kwargs['id']
        self.AWS_SECRET_ACCESS_KEY = kwargs['key']
        self.AWS_ASSOCIATE_TAG = kwargs['tag']
        self.item_path = item_path
        self.attr_paths = attr_paths
        self.amazon_api = bottlenose.Amazon(kwargs['id'],kwargs['key'],kwargs['tag'])

    def _parse_item_data(self, xml_parser,item_node):
        item = {}
        for attrname,path in self.attr_paths.items():
            attr_values = attrname.split('_',1)
            if attr_values[0] == 'list':
                list_values = xml_parser.parse_all_text_by_p(path,item_node)
                item[attr_values[1].split('_path')[0]] = json.dumps(list_values)
            elif attr_values[0] == 'dict':
                item[attr_values[1].split('_path')[0]] = xml_parser.parse_all_dict_by_path(path, item_node)
            elif attr_values[0] == 'decimal':
                item[attr_values[1].split('_path')[0]] = xml_parser.parse_decimal_by_p(path, item_node)
            else:
                item[attrname.split('_path')[0]] = xml_parser.parse_text_by_p(path,item_node)
        return item

    def _retrive_products(self, prod_xml):
        products = []
        try:
            xml_parser = parse.XmlParser(prod_xml)
            item_nodes = xml_parser.parse_all_nodes_by_path(self.item_path)
            for item in item_nodes:
                item_data = self._parse_item_data(xml_parser,item)
                products.append(item_data)
        except Exception as err:
            pass
        return products

    def fetch_all_child_nodes(self, browse_node):
        try:
            node_xml = self.amazon_api.BrowseNodeLookup(BrowseNodeId=browse_node).decode('utf-8')
            xml_parser = parse.XmlParser(node_xml)
            sub_nodes = []
            list_nodes = xml_parser.parse_all_nodes_by_path(child_browse_node_path)
            for node in list_nodes:
                if not xml_parser.parse_text_by_p(is_category_path,node):
                    sub_nodes.append(xml_parser.parse_text_by_p(node_id_path,node))
        except Exception:
            raise AmazonApiError(0)
        return sub_nodes


    def fetch_node_top_seller(self, browse_node):
        try:
            node_xml = self.amazon_api.BrowseNodeLookup(BrowseNodeId=browse_node,ResponseGroup="TopSellers").decode('utf-8')
            xml_parser = parse.XmlParser(node_xml)
            top_asins = xml_parser.parse_all_text_by_path(top_seller_asin_path)
        except Exception:
            raise AmazonApiError(0)
        return top_asins


    def fetch_product_by_asin(self, asin):
        product = ''
        try:
            resgroup ="Offers,EditorialReview,ItemAttributes,Images,Reviews,BrowseNodes"
            prod_xml = self.amazon_api.ItemLookup(ItemId=asin, Condition='New', ResponseGroup=resgroup).decode('utf-8')
            items = self._retrive_products(prod_xml)
            if items:
                product = items[0]
        except Exception:
            raise AmazonApiError(0)
        return product


    def fetch_products_by_search(self,searchindex,rest=0.5,maxpage=10,**kwargs):
        products = []
        for page in range(1,maxpage+1):
            resgroup = "Offers,EditorialReview,ItemAttributes,Images,Reviews,BrowseNodes"
            prod_xml = self.amazon_api.ItemSearch(ItemPage=page,SearchIndex=searchindex,ResponseGroup=resgroup,
                                                  **kwargs).decode('utf-8')
            page_products = self._retrive_products(prod_xml)
            if not page_products: break
            products.extend(page_products)
            time.sleep(rest)
        return products