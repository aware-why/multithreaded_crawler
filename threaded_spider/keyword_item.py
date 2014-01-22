"""Define the Item consisting of some specific fields for KeyWordSpider"""

from threaded_spider.core.item import BaseItem, Field

class Item(BaseItem):
    root_url = Field()
    depth = Field()
    self_url = Field()
    html_content = Field()