import schedule
import time
import subprocess


def run_spider():
    subprocess.run(["scrapy", "crawl", "bookspider", "-O", "data.json"])  # The command that will be executed when this script is run


schedule.every(10).seconds.do(run_spider)  # Runs the above command every 1 hour

while True:
    schedule.run_pending()
    time.sleep(1)
