import asyncio
import logging
from pathlib import Path

from aiohttp import web
import aiofiles


INTERVAL_SECS = 1
CHUNK_SIZE = 100


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__file__)


async def archivate(request):
    try:
        response = await _archivate(request)
    except asyncio.CancelledError:
        logger.warning('Downloading was interrupted!')
        raise

    return response


async def _archivate(request):
    """
    Create an archive.
    :return:
    """

    archive_hash = request.match_info.get('archive_hash', '')
    if not archive_hash:
        raise web.HTTPNotFound(reason='Archive does not exist or was deleted.')

    archive_path = Path.cwd() / f'test_photos/{archive_hash}'
    if not archive_path.exists():
        raise web.HTTPNotFound(reason='Archive does not exist or was deleted.')

    stream_response = web.StreamResponse()
    stream_response.enable_chunked_encoding(chunk_size=CHUNK_SIZE*1024)
    stream_response['Content-Type'] = 'application/zip'
    stream_response.headers.add(f'Content-Disposition',
                                f'attachment;filename="{archive_hash}.zip"')
    await stream_response.prepare(request)

    proc = await asyncio.create_subprocess_exec(
        'zip', '-r', '-', archive_hash,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path.cwd() / 'test_photos'
    )

    while True:
        out = await proc.stdout.read(CHUNK_SIZE * 1024)
        logger.debug('Sending archive chunk...')
        await stream_response.write(out)
        if proc.stdout.at_eof():
            await stream_response.write_eof()
            break

        await asyncio.sleep(INTERVAL_SECS)

    return stream_response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
