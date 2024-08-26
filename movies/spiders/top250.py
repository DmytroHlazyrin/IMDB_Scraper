import scrapy


class Top250Spider(scrapy.Spider):
    name = "top250"
    allowed_domains = ["www.imdb.com"]
    start_urls = ["https://www.imdb.com/chart/top/?ref_=nv_mv_250"]

    def parse(self, response):
        pass
