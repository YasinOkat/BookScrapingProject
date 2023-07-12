# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SmartmapleItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    pass


class BookItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    writers = scrapy.Field()
    page = scrapy.Field()
    bought = scrapy.Field()
    num_reviews = scrapy.Field()
    publisher = scrapy.Field()
    stars = scrapy.Field()
    category = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()