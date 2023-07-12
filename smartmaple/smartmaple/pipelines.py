# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
from pymongo.errors import DuplicateKeyError


class SmartmaplePipeline:

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # This removes the whitespaces from writers
        field_names = adapter.field_names()
        for field_name in field_names:
            if field_name == 'writers':
                values = adapter.get(field_name)
                try:
                    cleaned_values = [value.strip() for value in values]
                    adapter[field_name] = cleaned_values
                except AttributeError:
                    pass

        # Extracts the price as float
        price_list = item.get('price')
        new_price_string = price_list.strip().replace('\n', '').replace(',', '.').replace('TL', '')
        price_num = float(new_price_string)
        item['price'] = price_num

        # Extracts the number part of how many times bought
        bought = item.get('bought')
        if bought:
            number_bought = re.findall(r'\d+', bought)[0]
            number = int(number_bought)
            item['bought'] = number

        # Turns the page value to integer
        page = item.get('page')
        try:
            page_num = int(page)
            item['page'] = page_num
        except TypeError:
            item['page'] = 0

        # Turns the number of reviews to integer
        num_of_reviews = item.get('num_reviews')
        if num_of_reviews is not None:
            review_num = int(num_of_reviews)
            item['num_reviews'] = review_num
        else:
            item['num_reviews'] = 0

        return item


# The pipeline to save the data to MongoDB
class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # The logic that decides which collection the items should be saved
        if 'kitapyurdu.com' in item['url']:
            collection = self.db['kitapyurdu']
        elif 'kitapsepeti.com' in item['url']:
            collection = self.db['kitapsepeti']
        else:
            raise ValueError(f"Unknown website URL: {item['url']}")
        try:
            collection.insert_one(dict(item))
        except DuplicateKeyError:  # If a duplicate item exists based on the url, it updates the current one instead of inserting
            url = item['url']
            collection.update_one({'url': url}, {'$set': dict(item)})
            spider.logger.debug('Duplicate item found. Updating the record.')
        return item
