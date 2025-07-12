from aiohttp import web
import aiofiles
import asyncio
import os
import logging
from environs import Env
import argparse
import configargparse


SIZE_OF_CHUNK = 409600


async def send_archieve(request):

    archive_hash = request.match_info['archive_hash']
    path = f'{args.path}/{archive_hash}'

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

    try:
        while True:
            chunk = await process.stdout.read(SIZE_OF_CHUNK)
            if not chunk:
                break
            await response.write(chunk)
            logging.info('Sending archive chunk')
            await asyncio.sleep(args.delay)
    except asyncio.CancelledError:
        logging.warning('Download was interrupted')
    finally:
        await process.wait()
        await response.write_eof()
        return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    env = Env()
    env.read_env()

    command_line_parser = configargparse.ArgumentParser(
        description='Запуск микросервиса для отправки архивов'
    )
    command_line_parser.add_argument('-p', '--path', type=str, default='test_photos', env_var='PATH_TO_PHOTOS',
                                     help='Путь до каталога, в которой лежат папки с фотографиями')
    command_line_parser.add_argument('-d', '--delay', type=int, default=1,
                                     env_var='PAUSE_TIME_OF_DOWNLOADING', help='Замедление загрузки архива')
    command_line_parser.add_argument(
        '-l', '--logging', action='store_true', help='Включить логирование')

    args = command_line_parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    if not args.logging:
        logging.disable(logging.CRITICAL)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', send_archieve),
    ])
    web.run_app(app)
