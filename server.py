import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional

from aiohttp import web
import aiofiles

from settings import set_logger_settings, ServerSettings as sts


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
        """
        kill process if something wrong happens.
        """

        if exc:
            self._logger.warning('Downloading data from a pipe was '
                                 'interrupted')
            try:
                self.process.kill()
                await self.process.communicate()
            except Exception as e:
                logger.error(f'Cannot kill an archiving process: {type(e)}')
            finally:
                logger.info('An archiving process was stopped')
                raise exc

    @property
    def process(self) -> asyncio.subprocess.Process:
        return self._proc

    async def read(self,
                   chunk_size: Optional[int] = sts.CHUNK_SIZE * 1024) -> bytes:
        """
        Read chunked data from a stdin.
        If a process return non-zero code, RuntimeError exception is raised.
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

    archive_path = Path(f'{sts.STORAGE_PATH}') / archive_hash
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
                out = await archiver.read(sts.CHUNK_SIZE * 1024)
                await stream_response.write(out)

                if archiver.process.stdout.at_eof():
                    await stream_response.write_eof()
                    break
                await asyncio.sleep(sts.DELAY)
    except asyncio.CancelledError:
        raise
    except Exception:
        pass

    return stream_response


async def handle_index_page(request: web.Request) -> web.Response:
    index_template_path = Path('templates') / 'index.html'
    async with aiofiles.open(index_template_path, mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


class WebServer:
    def __init__(self):
        self._app = web.Application()

    def run(self,
            debug: Optional[bool] = True,
            host: Optional[str] = 'localhost',
            port: Optional[int] = 8080):
        routes = [web.get('/archive/{archive_hash}/', archive)]
        if debug:
            routes.append(web.get('/', handle_index_page))

        self._app.add_routes(routes)
        web.run_app(self._app, host=host, port=port)


def main(args: argparse.Namespace):
    debug = args.debug
    host = args.host
    port = args.port

    sts.STORAGE_PATH = args.storage_path
    sts.DELAY = args.delay
    sts.CHUNK_SIZE = args.chunk_size

    routes = [web.get('/archive/{archive_hash}/', archive)]
    if debug:
        routes.append(web.get('/', handle_index_page))
        level = logging.DEBUG
    else:
        level = logging.INFO

    set_logger_settings(args.log_file, level)

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        '--debug',
                        required=False,
                        action='store_true',
                        default=False,
                        help='If set you can use an index page for debugging.')
    parser.add_argument('-H',
                        '--host',
                        type=str,
                        required=False,
                        default='localhost',
                        help='A host where a server will be deployed. '
                             'By default, "localhost"')
    parser.add_argument('-P',
                        '--port',
                        type=int,
                        required=False,
                        default=8080,
                        help='A port where a server will be deployed. '
                             'By default, 8080')
    parser.add_argument('-S',
                        '--storage_path',
                        type=str,
                        required=False,
                        default='photos',
                        help='A directory with all photo. '
                             'By default, ./photos')
    parser.add_argument('-L',
                        '--log_file',
                        type=str,
                        required=False,
                        default='archive.log',
                        help='A path to a log file. By default, ./archive.log')
    parser.add_argument('-C',
                        '--chunk_size',
                        type=int,
                        required=False,
                        default=100,
                        help='A chunk size (in kilobytes) for chunks '
                             'which are sent to a client. By default, 100.')
    parser.add_argument('-D',
                        '--delay',
                        type=float,
                        required=False,
                        default=0.5,
                        help='Delay (in seconds) between sending chunk to '
                             'a client. By default, 1 second.')
    args = parser.parse_args()
    main(args)
