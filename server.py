import pymorphy2
from aiohttp import web

from process_articles import process_urls


class ArticleAnalyzer:

    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()

    async def analyze(self, request):
        urls = request.query.get('urls')
        if not urls:
            return web.json_response({"ok": "use query parameter 'urls' to check article, for example "
                                            "http://127.0.0.1/?urls=https://ya.ru,https://inosmi.ru/politic/20201220/248782711.html"})

        urls = urls.split(',')
        if len(urls) > 10:
            return web.json_response({"error": "too many urls in request, should be 10 or less"}, status=400)

        processing_results = await process_urls(self.morph, urls)
        return web.json_response(processing_results)


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', ArticleAnalyzer().analyze),
    ])

    web.run_app(app, port=80)
