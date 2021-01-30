import asyncio
import logging
from pathlib import Path
from typing import Optional

from aiohttp import web
import aiofiles


from settings import CHUNK_SIZE, INTERVAL_SECS


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__file__)


class Archiver:
    """
    This class helps to run a process of creating a zip archive.
    """
    def __init__(self,
                 archive_path: Path,
                 logger: logging.Logger):
        self._archive_path = archive_path
        self._proc = None
        self._logger = logger

    async def __aenter__(self):
        self._proc = await asyncio.create_subprocess_exec(
            'zip', '-r', '-', self._archive_path.stem,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._archive_path.parent
        )
        return self

    async def __aexit__(self, exc_type, exc, exc_tb):
        if exc:
            self._logger.warning('Downloading data from a pipe was '
                                 'interrupted')
            try:
                self._proc.kill()
            except Exception as e:
                logger.error(f'Cannot kill an archiving process: {type(e)}')
            finally:
                logger.info('An archiving process was stopped')
                raise exc

    @property
    def process(self) -> asyncio.subprocess.Process:
        return self._proc

    async def read(self,
                   chunk_size: Optional[int] = CHUNK_SIZE * 1024) -> bytes:
        """
        Read chunked data from a stdin
        :param chunk_size: in kilobytes
        :return:
        """

        self._logger.info('Read chunked data from a pipe...')
        out = await self.process.stdout.read(chunk_size)
        if self.process.returncode:
            msg = 'Archiving process return non-zero code'
            logger.error(msg)
            raise RuntimeError(msg)

        self._logger.info('Success!')
        return out


async def archive(request: web.Request) -> web.StreamResponse:
    archive_hash = request.match_info.get('archive_hash', '')
    if not archive_hash:
        raise web.HTTPNotFound(reason='Archive does not exist or was deleted.')

    archive_path = Path.cwd() / f'test_photos/{archive_hash}'
    if not archive_path.exists():
        raise web.HTTPNotFound(reason='Archive does not exist or was deleted')

    stream_response = web.StreamResponse()
    stream_response.enable_chunked_encoding()
    stream_response['Content-Type'] = 'application/zip'
    stream_response.headers.add(f'Content-Disposition',
                                f'attachment;filename="{archive_hash}.zip"')

    await stream_response.prepare(request)

    try:
        async with Archiver(archive_path, logger) as archiver:
            while True:
                out = await archiver.read()
                await stream_response.write(out)

                if archiver.process.stdout.at_eof():
                    await stream_response.write_eof()
                    break
                await asyncio.sleep(INTERVAL_SECS)
    except asyncio.CancelledError:
        raise
    except RuntimeError:
        raise web.HTTPServerError(reason='Cannot archive data')
    except Exception:
        raise web.HTTPServerError(reason='Unknown error')

    return stream_response


async def handle_index_page(request: web.Request) -> web.Response:
    index_template_path = Path('templates') / 'index.html'
    async with aiofiles.open(index_template_path, mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
