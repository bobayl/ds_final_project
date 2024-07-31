import scrapy


class AvheraldSpiderSpider(scrapy.Spider):
    name = "avherald_spider"
    allowed_domains = ["avherald.com"]
    start_urls = ["https://avherald.com"]

    def parse(self, response):
        pass
