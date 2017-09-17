import scrapy
from HTMLParser import HTMLParser
from datetime import datetime


class HalalMUIItem(scrapy.Item):
    name = scrapy.Field()
    category = scrapy.Field()
    certificate_number = scrapy.Field()
    producer = scrapy.Field()
    expiration_date = scrapy.Field()


class HalalMUISpider(scrapy.Spider):
    name = 'halalmui'

    def start_requests(self):
        urls = ['http://www.halalmui.org/mui14/index.php/main/produk_halal_masuk/1']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        category_hyperlinks = response.xpath(
            '//a[contains(@class, "linkhalal")]').extract()

        for hyperlink in category_hyperlinks:
            category_text = hyperlink.split("%22")[8][3:-4]
            category_url = hyperlink.split("%22")[7]

            # crawl product of each category
            category_url = category_url + '/offset/0'
            yield scrapy.Request(
                url=category_url,
                callback=self.crawl_product,
                meta={'category': category_text})

    def crawl_product(self, response):
        # initiate HTML escape characters parser
        h = HTMLParser()

        # crawl product of each category
        if self.is_available(response):
            url = response.url

            old_offset = int(response.url.split('/')[-1])
            new_offset = old_offset + 10
            new_url = url.replace(
                'offset/{}'.format(old_offset),
                'offset/{}'.format(new_offset)
            )

            product_rows = response.xpath('//tr//td')
            for product_row in product_rows:
                product_details = product_row.xpath('span/text()').extract()
                if product_details:
                    item = HalalMUIItem()
                    item['name'] = h.unescape(product_row.xpath('span/h4/text()').extract_first())
                    item['certificate_number'] = product_details[0].split(' : ')[-1]
                    item['category'] = response.meta['category']
                    item['producer'] = h.unescape(
                        product_details[1].split(' : ')[-1])
                    item['expiration_date'] = datetime.strptime(
                        product_details[2].split(' : ')[-1],
                        '%d %B %Y')

                    yield item

            yield scrapy.Request(
                url=new_url,
                callback=self.crawl_product,
                meta={'category': response.meta['category']})

    def is_available(self, response):
        if not response.xpath('//i/text()').extract_first() == 'no result found':
            return True
        else:
            return False
