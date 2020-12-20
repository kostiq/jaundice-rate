import asyncio
from unittest.mock import MagicMock

import pymorphy2
import pytest

from process_articles import process_article, ProcessingStatus, FETCH_TIMEOUT, PARSING_TIMEOUT


@pytest.fixture(scope='session')
def morph():
    return pymorphy2.MorphAnalyzer()


@pytest.fixture()
def score_list():
    return []


def test_unavailable_url(morph, score_list):
    unavailable_url = 'notexist.com'
    asyncio.run(process_article(score_list, morph, unavailable_url, []))

    result = score_list[0]

    assert result['status'] == ProcessingStatus.FETCH_ERROR.value
    assert result['url'] == unavailable_url
    assert result['score'] is None


def test_parsing_error(morph, score_list):
    url_wihtout_adapter = 'https://google.com'
    asyncio.run(process_article(score_list, morph, url_wihtout_adapter, []))

    result = score_list[0]

    assert result['status'] == ProcessingStatus.PARSING_ERROR.value
    assert result['url'] == url_wihtout_adapter
    assert result['score'] is None


def test_process_ok(morph, score_list):
    ok_url = 'https://inosmi.ru/politic/20201220/248788103.html'
    asyncio.run(process_article(score_list, morph, ok_url, []))

    result = score_list[0]

    assert result['status'] == ProcessingStatus.OK.value
    assert result['url'] == ok_url
    assert result['score'] is not None


class AsyncTimeoutMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        await asyncio.sleep(max(FETCH_TIMEOUT, PARSING_TIMEOUT) + 1)


def test_fetch_timeout(mocker, morph, score_list):
    url = 'https://inosmi.ru/politic/20201220/248788103.html'
    mocker.patch('process_articles.fetch', new_callable=AsyncTimeoutMock)
    asyncio.run(process_article(score_list, morph, url, []))

    result = score_list[0]

    assert result['status'] == ProcessingStatus.TIMEOUT.value
    assert result['url'] == url
    assert result['score'] is None


def test_parsing_timeout(mocker, morph, score_list):
    url = 'https://inosmi.ru/politic/20201220/248788103.html'
    mocker.patch('process_articles.split_by_words', new_callable=AsyncTimeoutMock)
    asyncio.run(process_article(score_list, morph, url, []))

    result = score_list[0]

    assert result['status'] == ProcessingStatus.TIMEOUT.value
    assert result['url'] == url
    assert result['score'] is None
