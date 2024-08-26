import scrapy
from urllib.parse import urlencode
import json
import re




class ProductsSpider(scrapy.Spider):
    name = "products"

    custom_settings = {
        'FEEDS': { 'data/%(name)s_%(time)s.csv': { 'format': 'csv',}}
    }


    def get_url(self,keyword,page,affinityOverride="default"):
        parameters = {"q" : keyword, "page": page, "affinityOverride" : affinityOverride}
        url = 'https://www.walmart.com/search?' + urlencode(parameters)
        return url

    def start_requests(self):
       keywords = ["laptops"]


       for keyword in keywords:
           walmart_search_url = self.get_url(keyword,1)
           yield scrapy.Request(url = walmart_search_url, callback = self.search_results_parse, meta = {"keyword" : keyword , "page" : 1})


    def search_results_parse(self, response):
        page = response.meta["page"]
        keyword = response.meta["keyword"]

        script_tag = response.css("script#__NEXT_DATA__::text").get()
        if script_tag is not None:
            json_blob = json.loads(script_tag)

        products = json_blob["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]["items"]


        for product in products:
            relative_url = product.get("canonicalUrl", '')
            product_url = "https://www.walmart.com" + relative_url
            yield scrapy.Request(url = product_url, callback = self.product_details_parse, meta = {"keyword" : keyword , "page" : page, "url" : product_url})




    def product_details_parse(self, response):
        page = response.meta["page"]
        keyword = response.meta["keyword"]
        url = response.meta["url"]

        script_tag = response.css("script#__NEXT_DATA__::text").get()
        if script_tag is not None:
            json_blob = json.loads(script_tag)
            data = json_blob["props"]["pageProps"]["initialData"]["data"]["product"]


        cleaner  = re.compile("<.*?>")
        description = data.get("shortDescription")

        clean_description = re.sub(cleaner, '', description)
        clean_description =  re.sub("/n", " ", clean_description)
        yield{

            "keyword"      : keyword,
            "page"         : page,
            "id"           : data.get("id"),
            "type"         : data.get("type"),
            "name"         : data.get("name"),
            "description"  : clean_description.strip(),
            "availability" : data.get("availabilityStatus"),
            "rating"       : data.get("averageRating"),
            "brand"        : data.get("brand"),
            "thumbanil"    : data["imageInfo"].get("thumbnailUrl"),
            "price"        : data["priceInfo"]["currentPrice"].get("priceString"),
            "upc"          : data.get("upc"),
            "Buy url"      : url,
            }


