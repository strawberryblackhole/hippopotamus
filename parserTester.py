from amulet.api.selection import SelectionGroup
from amulet.api.block import Block
from amulet.api.data_types import Dimension
from amulet import log
import amulet_nbt
from amulet.api.block_entity import BlockEntity
from ZIMply.zimply import ZIMFile
import os
import math
import time

from fillWithWiki import getFormatedArticle

zimfile = ZIMFile(os.path.dirname(os.path.realpath(__file__)) + "\\wikipedia_de_basketball_nopic_2020-04.zim","utf-8")
articleCount = list(zimfile)[-1][2]

count = 0

articles = list(zimfile)

for article in range(articleCount):
    print(article)

    start = time.perf_counter()

    article = [x for x in articles if x[2] == article]

    print(time.perf_counter() - start)
    print("articleSearch")

    if len(article) > 1:
        raise Exception()
    foundArticle = len(article) == 1
    
    articleStop = 0
    if foundArticle:
        article = article[0]
        articleTitle = article[1]
        articleId = article[2]  

        start = time.perf_counter()
        a = zimfile._get_article_by_index(articleId).data.decode("utf-8")
        print(time.perf_counter() - start)
        print("article read")

        start = time.perf_counter()
        formatedArticle = getFormatedArticle(a)
        print(time.perf_counter() - start)
        print("article parse")
        print(formatedArticle)
        if count > 4:
            break
        count += 1