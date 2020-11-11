"""
psycopg3 connection objects
"""

# Copyright (C) 2020 The Psycopg Team

import logging
import asyncio
import threading
from types import TracebackType
from typing import Any, AsyncIterator, Callable, Iterator, List, NamedTuple
from typing import Optional, Type, cast
from weakref import ref, ReferenceType
from functools import partial

from . import pq
from . import errors as e
from . import cursor
from . import proto
from .pq import TransactionStatus, ExecStatus
from .conninfo import make_conninfo
from .waiting import wait, wait_async
from .generators import notifies

logger = logging.getLogger(__name__)
package_logger = logging.getLogger("psycopg3")

connect: Callable[[str], proto.PQGen[pq.proto.PGconn]]
execute: Callable[[pq.proto.PGconn], proto.PQGen[List[pq.proto.PGresult]]]

if pq.__impl__ == "c":
    from psycopg3_c import _psycopg3

    connect = _psycopg3.connect
    execute = _psycopg3.execute

else:
    from . import generators

    connect = generators.connect
    execute = generators.execute


class Notify(NamedTuple):
    """An asynchronous notification received from the database."""

    channel: str
    payload: str
    pid: int


NoticeHandler = Callable[[e.Diagnostic], None]
NotifyHandler = Callable[[Notify], None]


class BaseConnection:
    """
    Base class for different types of connections.

    Share common functionalities such as access to the wrapped PGconn, but
    allow different interfaces (sync/async).
    """

    # DBAPI2 exposed exceptions
    Warning = e.Warning
    Error = e.Error
    InterfaceError = e.InterfaceError
    DatabaseError = e.DatabaseError
    DataError = e.DataError
    OperationalError = e.OperationalError
    IntegrityError = e.IntegrityError
    InternalError = e.InternalError
    ProgrammingError = e.ProgrammingError
    NotSupportedError = e.NotSupportedError

    # Enums useful for the connection
    ConnStatus = pq.ConnStatus
    TransactionStatus = pq.TransactionStatus

    def __init__(self, pgconn: pq.proto.PGconn):
        self.pgconn = pgconn
        self.cursor_factory = cursor.BaseCursor
        self._autocommit = False
        self.dumpers: proto.DumpersMap = {}
        self.loaders: proto.LoadersMap = {}
        self._notice_handlers: List[NoticeHandler] = []
        self._notify_handlers: List[NotifyHandler] = []
        # postgres name of the client encoding (in bytes)
        self._pgenc = b""
        # python name of the client encoding
        self._pyenc = "utf-8"

        wself = ref(self)

        pgconn.notice_handler = partial(BaseConnection._notice_handler, wself)
        pgconn.notify_handler = partial(BaseConnection._notify_handler, wself)

    @property
    def closed(self) -> bool:
        """`true` if the connection is closed."""
        return self.status == self.ConnStatus.BAD

    @property
    def status(self) -> pq.ConnStatus:
        return self.pgconn.status

    @property
    def autocommit(self) -> bool:
        return self._autocommit

    @autocommit.setter
    def autocommit(self, value: bool) -> None:
        self._set_autocommit(value)

    def _set_autocommit(self, value: bool) -> None:
        # Base implementation, not thread safe
        # subclasses must call it holding a lock
        status = self.pgconn.transaction_status
        if status != TransactionStatus.IDLE:
            raise e.ProgrammingError(
                "couldn't change autocommit state: connection in"
                f" transaction status {TransactionStatus(status).name}"
            )
        self._autocommit = value

    def _cursor(
        self, name: str = "", format: pq.Format = pq.Format.TEXT
    ) -> cursor.BaseCursor:
        if name:
            raise NotImplementedError
        return self.cursor_factory(self, format=format)

    @property
    def pyenc(self) -> str:
        pgenc = self.pgconn.parameter_status(b"client_encoding") or b""
        if self._pgenc != pgenc:
            if pgenc:
                try:
                    self._pyenc = pq.py_codecs[pgenc]
                except KeyError:
                    raise e.NotSupportedError(
                        f"encoding {pgenc.decode('ascii')} not available in Python"
                    )

            self._pgenc = pgenc
        return self._pyenc

    @property
    def client_encoding(self) -> str:
        rv = self.pgconn.parameter_status(b"client_encoding")
        return rv.decode("utf-8") if rv else "UTF8"

    @client_encoding.setter
    def client_encoding(self, value: str) -> None:
        self._set_client_encoding(value)

    def _set_client_encoding(self, value: str) -> None:
        raise NotImplementedError

    def cancel(self) -> None:
        c = self.pgconn.get_cancel()
        c.cancel()

    def add_notice_handler(self, callback: NoticeHandler) -> None:
        self._notice_handlers.append(callback)

    def remove_notice_handler(self, callback: NoticeHandler) -> None:
        self._notice_handlers.remove(callback)

    @staticmethod
    def _notice_handler(
        wself: "ReferenceType[BaseConnection]", res: pq.proto.PGresult
    ) -> None:
        self = wself()
        if not (self and self._notice_handler):
            return

        diag = e.Diagnostic(res, self._pyenc)
        for cb in self._notice_handlers:
            try:
                cb(diag)
            except Exception as ex:
                package_logger.exception(
                    "error processing notice callback '%s': %s", cb, ex
                )

    def add_notify_handler(self, callback: NotifyHandler) -> None:
        """
        Register a callable to be invoked whenever a notification is received.
        """
        self._notify_handlers.append(callback)

    def remove_notify_handler(self, callback: NotifyHandler) -> None:
        """
        Unregister a notification callable previously registered.
        """
        self._notify_handlers.remove(callback)

    @staticmethod
    def _notify_handler(
        wself: "ReferenceType[BaseConnection]", pgn: pq.PGnotify
    ) -> None:
        self = wself()
        if not (self and self._notify_handlers):
            return

        n = Notify(
            pgn.relname.decode(self._pyenc),
            pgn.extra.decode(self._pyenc),
            pgn.be_pid,
        )
        for cb in self._notify_handlers:
            cb(n)


class Connection(BaseConnection):
    """
    Wrapper for a connection to the database.
    """

    cursor_factory: Type[cursor.Cursor]

    def __init__(self, pgconn: pq.proto.PGconn):
        super().__init__(pgconn)
        self.lock = threading.Lock()
        self.cursor_factory = cursor.Cursor

    @classmethod
    def connect(
        cls, conninfo: str = "", *, autocommit: bool = False, **kwargs: Any
    ) -> "Connection":
        """
        Connect to a database server and return a new `Connection` instance.

        TODO: connection_timeout to be implemented.
        """

        conninfo = make_conninfo(conninfo, **kwargs)
        gen = connect(conninfo)
        pgconn = cls.wait(gen)
        conn = cls(pgconn)
        conn._autocommit = autocommit
        return conn

    def __enter__(self) -> "Connection":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type:
            self.rollback()
        else:
            self.commit()

        self.close()

    def close(self) -> None:
        """Close the database connection."""
        self.pgconn.finish()

    def cursor(
        self, name: str = "", format: pq.Format = pq.Format.TEXT
    ) -> cursor.Cursor:
        """Return a new cursor to send commands and query the connection."""
        cur = self._cursor(name, format=format)
        return cast(cursor.Cursor, cur)

    def _start_query(self) -> None:
        # the function is meant to be called by a cursor once the lock is taken
        if self._autocommit:
            return

        if self.pgconn.transaction_status != TransactionStatus.IDLE:
            return

        self.pgconn.send_query(b"begin")
        (pgres,) = self.wait(execute(self.pgconn))
        if pgres.status != ExecStatus.COMMAND_OK:
            raise e.OperationalError(
                "error on begin:"
                f" {pq.error_message(pgres, encoding=self._pyenc)}"
            )

    def commit(self) -> None:
        """Commit any pending transaction to the database."""
        with self.lock:
            self._exec_commit_rollback(b"commit")

    def rollback(self) -> None:
        """Roll back to the start of any pending transaction."""
        with self.lock:
            self._exec_commit_rollback(b"rollback")

    def _exec_commit_rollback(self, command: bytes) -> None:
        # Caller must hold self.lock
        status = self.pgconn.transaction_status
        if status == TransactionStatus.IDLE:
            return

        self.pgconn.send_query(command)
        results = self.wait(execute(self.pgconn))
        if results[-1].status != ExecStatus.COMMAND_OK:
            raise e.OperationalError(
                f"error on {command.decode('utf8')}:"
                f" {pq.error_message(results[-1], encoding=self._pyenc)}"
            )

    @classmethod
    def wait(
        cls, gen: proto.PQGen[proto.RV], timeout: Optional[float] = 0.1
    ) -> proto.RV:
        return wait(gen, timeout=timeout)

    def _set_client_encoding(self, value: str) -> None:
        with self.lock:
            self.pgconn.send_query_params(
                b"select set_config('client_encoding', $1, false)",
                [value.encode("ascii")],
            )
            gen = execute(self.pgconn)
            (result,) = self.wait(gen)
            if result.status != ExecStatus.TUPLES_OK:
                raise e.error_from_result(result, encoding=self._pyenc)

    def notifies(self) -> Iterator[Notify]:
        """Generate a stream of `Notify`"""
        while 1:
            with self.lock:
                ns = self.wait(notifies(self.pgconn))
            for pgn in ns:
                n = Notify(
                    pgn.relname.decode(self._pyenc),
                    pgn.extra.decode(self._pyenc),
                    pgn.be_pid,
                )
                yield n

    def _set_autocommit(self, value: bool) -> None:
        with self.lock:
            super()._set_autocommit(value)


class AsyncConnection(BaseConnection):
    """
    Asynchronous wrapper for a connection to the database.
    """

    cursor_factory: Type[cursor.AsyncCursor]

    def __init__(self, pgconn: pq.proto.PGconn):
        super().__init__(pgconn)
        self.lock = asyncio.Lock()
        self.cursor_factory = cursor.AsyncCursor

    @classmethod
    async def connect(
        cls, conninfo: str = "", *, autocommit: bool = False, **kwargs: Any
    ) -> "AsyncConnection":
        conninfo = make_conninfo(conninfo, **kwargs)
        gen = connect(conninfo)
        pgconn = await cls.wait(gen)
        conn = cls(pgconn)
        conn._autocommit = autocommit
        return conn

    async def __aenter__(self) -> "AsyncConnection":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

        await self.close()

    async def close(self) -> None:
        self.pgconn.finish()

    async def cursor(
        self, name: str = "", format: pq.Format = pq.Format.TEXT
    ) -> cursor.AsyncCursor:
        cur = self._cursor(name, format=format)
        return cast(cursor.AsyncCursor, cur)

    async def _start_query(self) -> None:
        # the function is meant to be called by a cursor once the lock is taken
        if self._autocommit:
            return

        if self.pgconn.transaction_status != TransactionStatus.IDLE:
            return

        self.pgconn.send_query(b"begin")
        (pgres,) = await self.wait(execute(self.pgconn))
        if pgres.status != ExecStatus.COMMAND_OK:
            raise e.OperationalError(
                "error on begin:"
                f" {pq.error_message(pgres, encoding=self._pyenc)}"
            )

    async def commit(self) -> None:
        async with self.lock:
            await self._exec_commit_rollback(b"commit")

    async def rollback(self) -> None:
        async with self.lock:
            await self._exec_commit_rollback(b"rollback")

    async def _exec_commit_rollback(self, command: bytes) -> None:
        # Caller must hold self.lock
        status = self.pgconn.transaction_status
        if status == TransactionStatus.IDLE:
            return

        self.pgconn.send_query(command)
        (pgres,) = await self.wait(execute(self.pgconn))
        if pgres.status != ExecStatus.COMMAND_OK:
            raise e.OperationalError(
                f"error on {command.decode('utf8')}:"
                f" {pq.error_message(pgres, encoding=self._pyenc)}"
            )

    @classmethod
    async def wait(cls, gen: proto.PQGen[proto.RV]) -> proto.RV:
        return await wait_async(gen)

    def _set_client_encoding(self, value: str) -> None:
        raise AttributeError(
            "'client_encoding' is read-only on async connections:"
            " please use await .set_client_encoding() instead."
        )

    async def set_client_encoding(self, value: str) -> None:
        async with self.lock:
            self.pgconn.send_query_params(
                b"select set_config('client_encoding', $1, false)",
                [value.encode("ascii")],
            )
            gen = execute(self.pgconn)
            (result,) = await self.wait(gen)
            if result.status != ExecStatus.TUPLES_OK:
                raise e.error_from_result(result, encoding=self._pyenc)

    async def notifies(self) -> AsyncIterator[Notify]:
        while 1:
            async with self.lock:
                ns = await self.wait(notifies(self.pgconn))
            for pgn in ns:
                n = Notify(
                    pgn.relname.decode(self._pyenc),
                    pgn.extra.decode(self._pyenc),
                    pgn.be_pid,
                )
                yield n

    def _set_autocommit(self, value: bool) -> None:
        raise AttributeError(
            "autocommit is read-only on async connections:"
            " please use await connection.set_autocommit() instead."
            " Note that you can pass an 'autocommit' value to 'connect()'"
            " if it doesn't need to change during the connection's lifetime."
        )

    async def set_autocommit(self, value: bool) -> None:
        async with self.lock:
            super()._set_autocommit(value)
