from os import environ
from cachetools import cached
from datetime import datetime
from pytz import timezone
from notion.client import NotionClient

class Config():
    @cached(cache={})
    def notion_token(self):
        return environ['NOTION_TOKEN']

    def client(self):
        return NotionClient(token_v2=self.notion_token, monitor=True, start_monitoring=True)

    @cached(cache={})
    def topics_collection_url(self):
        return environ['TOPICS_COLLECTION_URL']

    @cached(cache={})
    def daily_collection_url(self):
        return environ['DAILY_COLLECTION_URL']

    @cached(cache={})
    def localTZ(self):
        return timezone(environ['LOCAL_TIME_ZONE'])

    def nowGMT8(self):
        x = datetime.now()
        x = x.astimezone(self.localTZ)
        return x
