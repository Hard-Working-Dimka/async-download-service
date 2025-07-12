from aiohttp import web
import aiofiles
import asyncio
import os

INTERVAL_SECS = 1


async def send_archieve(request):

    archieve_name = request.match_info['archive_hash']
    path = f'test_photos/{archieve_name}'

    if not os.path.exists(path):
        raise web.HTTPNotFound(
            text='Архив с фотографиями был удален или перемещен на другой адрес. Свяжитесь с администратором.')

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = f'attachment; filename="Photos.zip"'

    await response.prepare(request)

    process = await asyncio.create_subprocess_exec(
        'zip', '-r', '-', '.',
        stdout=asyncio.subprocess.PIPE,
        cwd=path
    )

    while True:
        chunk = await process.stdout.read(512000)
        if not chunk:
            await response.write_eof()
            break
        await response.write(chunk)

    await process.wait()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', send_archieve),
    ])
    web.run_app(app)
