from aiohttp import web

from process_articles import main


async def handle(request):
    urls = request.query.get('urls')
    if not urls:
        return web.json_response({"ok": "use query parameter 'urls' to check article, for example "
                                        "http://127.0.0.1/?urls=https://ya.ru,https://inosmi.ru/politic/20201220/248782711.html"})

    urls = urls.split(',')
    if len(urls) > 10:
        return web.json_response({"error": "too many urls in request, should be 10 or less"}, status=400)

    processed_results = await main(urls)
    return web.json_response(processed_results)


app = web.Application()
app.add_routes([
    web.get('/', handle),
])

if __name__ == '__main__':
    web.run_app(app, port=80)
