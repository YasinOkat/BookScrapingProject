import scrapy
from scrapy.utils.log import configure_logging
from scrapy_splash import SplashRequest
from smartmaple.email_extension import EmailExtension
from smartmaple.generate_user_agent import generate_random_user_agent
from smartmaple.items import BookItem
from smartmaple.settings import EMAIL_FROM, EMAIL_TO, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD


# The main spider that scrapes data from both kitapyurdu and kitapsepeti
class BookspiderSpider(scrapy.Spider):
    configure_logging()  # This configures the logging for the spider
    name = "bookspider"
    allowed_domains = ["kitapyurdu.com", "kitapsepeti.com"]
    kitapyurdu_page = 1
    kitapsepeti_page = 1
    email_extension = EmailExtension(from_email=EMAIL_FROM, to_email=EMAIL_TO,  # Sets the email extenstion
                                     smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT,
                                     smtp_username=SMTP_USERNAME, smtp_password=SMTP_PASSWORD)
    email_extension.open_spider(None)

    def start_requests(self):
        random_user_agent = generate_random_user_agent()  # Calls the function to generate user agent

        yield SplashRequest(
            url='https://www.kitapyurdu.com/index.php?route=product/'
                'search&filter_name=python&filter_in_stock=1&fuzzy=0&limit=20',  # The first url to scrape
            headers={'User-Agent': random_user_agent},  # Adds the user agent as headers
            callback=self.parse_kitap_yurdu)  # Function to handle the response
        yield SplashRequest(
            url='https://www.kitapsepeti.com/arama?q=python&'
                'customerType=Ziyaretci&pg=1&stock=1',  # The second url to scrape
            headers={'User-Agent': random_user_agent},
            callback=self.parse_kitap_sepeti)

    # The parser that scrapes from kitapyurdu.com
    def parse_kitap_yurdu(self, response):
        books = response.css('div.product-cr')  # This is the table row that has multiple books in it
        random_user_agent = generate_random_user_agent()

        for book in books:
            book_item = BookItem()
            book_url = book.css('div.name a::attr(href)').get()  # Gets the url of the book

            book_item['writers'] = book.css('div.author a span::text').getall()  # Gets all the writers
            book_item['publisher'] = book.css('div.publisher a span::text').get()  # Gets the publisher
            book_item['num_reviews'] = book.css('div.rating div::attr(title)').re_first(r'(\d+)')  # Extracts the number of reviews
            book_item['stars'] = len(book.css('div.rating i.fa-star.active')) or 0  # Counts how many stars it has, if it has none, set to 0
            book_item['price'] = book.css('div.price-new span.value::text').get()  # Gets the price

            yield scrapy.Request(
                book_url,  # Sends the book_url scraped from the table
                callback=self.parse_book_page_kitap_yurdu,  # Sends to the parser that goes over the details page of the book
                headers={'User-Agent': random_user_agent},
                meta={'book_item': book_item}  # Passes the book_item, the values gotten from the details will be added
            )

        if response.css('.product-not-found'):  # If the page return product not found, stops the loop
            self.logger.info("No results found for kitapyurdu.com. Stopping the loop.")
            return

        # Logic to iterate over next pages
        self.kitapyurdu_page += 1
        next_page_url = f"https://www.kitapyurdu.com/index.php?route=product/" \
                        f"search&page={self.kitapyurdu_page}&filter_name=python&filter_in_stock=1&fuzzy=0"

        yield scrapy.Request(
            next_page_url,
            callback=self.parse_kitap_yurdu
        )

    # The parser that scrapes the data of the book, after opening it's detailed page
    def parse_book_page_kitap_yurdu(self, response):
        book_item = response.meta['book_item']  # Gets the book_item passed from the main parser

        book_item['url'] = response.url
        book_item['title'] = response.css('h1.pr_header__heading::text').get()  # Gets the title
        book_item['category'] = response.xpath(
            '//h6[contains(@class, "text-custom-pink")]/text()').get()  # Gets the category

        if not book_item['writers']:  # If the main parser couldn't get the writers from the main page, it gets here
            book_item['writers'] = response.css('div.pr_producers__manufacturer a::text').get(),

        if book_item['category'] is None:  # If the parser couldn't get the category, this uses a different xpath
            book_item['category'] = response.xpath(
                "//ul[@class='rel-cats__list']/li[@class='rel-cats__item']/a/span[2]/text()").get()

        # Some books have their pages written in different row, this logic tries to find the one with the numbers
        page_number = response.xpath('//div[@class="attributes"]//tr[4]/td[2]/text()').get()
        if page_number and not page_number.isdigit():
            page_number = response.xpath('//div[@class="attributes"]//tr[5]/td[2]/text()').get()
        if page_number and not page_number.isdigit():
            page_number = response.xpath('//div[@class="attributes"]//tr[3]/td[2]/text()').get()
        book_item['page'] = page_number

        book_item['bought'] = response.xpath(  # Number of times bought
            "//div[@class='purchase-info']/p[@class='purchased']/text()[re:match(., '[0-9\.]+')]").get()
        book_item['description'] = response.css(".pr_description #description_text span::text").get()

        if book_item['description'] == "\xa0":
            book_item['description'] = response.css(".pr_description #description_text span::text").get()

        yield book_item

    # The parser that scrapes from kitapsepeti.com
    def parse_kitap_sepeti(self, response):
        books = response.css('div.col.col-12.drop-down.hover.lightBg')
        random_user_agent = generate_random_user_agent()

        for book in books:
            book_url = book.css('a.image-wrapper').attrib['href']
            absolute_url = response.urljoin(book_url)
            book_item = BookItem()

            book_item['writers'] = book.css('a#productModelText::text').getall()
            book_item['publisher'] = book.css('a.col.col-12.text-title.mt::text').get()
            book_item['price'] = book.css(
                'div.fl.col-12.tooltipWrapper div.fl.col-12.d-flex.productPrice div.fl.col-12.priceWrapper div.col.col-12.currentPrice::text').get()

            yield scrapy.Request(
                absolute_url,
                callback=self.parse_book_page_kitap_sepeti,
                headers={'User-Agent': random_user_agent},
                meta={'book_item': book_item}
            )

        self.kitapsepeti_page += 1
        next_page_url = f"https://www.kitapsepeti.com/arama?q=python&customerType=Ziyaretci&pg={self.kitapsepeti_page}&stock=1"
        yield response.follow(next_page_url, callback=self.parse_kitap_sepeti)

    def parse_book_page_kitap_sepeti(self, response):
        book_item = response.meta['book_item']

        book_item['url'] = response.url
        book_item['title'] = response.css('h1#productName::text').get()
        book_item['category'] = response.xpath(
            '//h6[contains(@class, "text-custom-pink")]/text()').get()

        book_item['page'] = response.xpath('//div[@class="col cilt col-12"]/div[2]/span[2]/text()').get()
        book_item['description'] = response.css('div#productDetailTab p:first-of-type::text').get()

        yield book_item
