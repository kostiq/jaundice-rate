import asyncio
import logging
import os
from enum import Enum

import aiohttp
import pymorphy2
from aiohttp import InvalidURL
from anyio import create_task_group
from async_timeout import timeout

from adapters import ArticleNotFound
from adapters.inosmi_ru import sanitize
from text_tools import split_by_words, calculate_jaundice_rate

FETCH_TIMEOUT = 2
PARSING_TIMEOUT = 3

TEST_ARTICLES = [
    'https://inosmi.ru/politic/20201220/248788103.html',
    'https://www.crummy.com/software/BeautifulSoup/bs4/doc/',
    'https://inosmi.ru/social/20201220/248758021.html',
    'https://inosmi.ru/politic/20201220/248782711.html',
    'notexist.com'
]


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


def get_charged_words(charged_words_folder):
    for filename in os.listdir(charged_words_folder):
        with open(os.path.join(charged_words_folder, filename)) as f:
            yield from f.read().splitlines()


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(article_score_list, morph, article_url, charged_words):
    score = None
    article_words_count = None

    async with aiohttp.ClientSession() as session:
        try:
            async with timeout(FETCH_TIMEOUT):
                html = await fetch(session, article_url)

            plain_text = sanitize(html, plaintext=True)
            async with timeout(PARSING_TIMEOUT) as t:
                article_words = await split_by_words(morph, plain_text)

            logging.info(f'Анализ {article_url} закончен за {PARSING_TIMEOUT - t.remaining:.3f} сек')

            status = ProcessingStatus.OK.value

            score = calculate_jaundice_rate(article_words, charged_words)
            article_words_count = len(article_words)

        except InvalidURL:
            status = ProcessingStatus.FETCH_ERROR.value

        except ArticleNotFound:
            status = ProcessingStatus.PARSING_ERROR.value

        except asyncio.TimeoutError:
            status = ProcessingStatus.TIMEOUT.value

        article_score_list.append({
            'status': status,
            'url': article_url,
            'score': score,
            'words_count': article_words_count
        })


async def process_urls(morph, article_list):
    charged_words_folder = 'charged_dict'
    charged_words = list(get_charged_words(charged_words_folder))
    article_score_list = []
    async with create_task_group() as tg:
        for article_url in article_list:
            await tg.spawn(process_article, article_score_list, morph, article_url, charged_words)

    return article_score_list


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    morph = pymorphy2.MorphAnalyzer()
    asyncio.run(process_urls(morph, TEST_ARTICLES))
