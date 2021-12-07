"""
types stub for ctypes functions
"""

# Copyright (C) 2020-2021 The Psycopg Team

from typing import Any, Callable, Optional, Sequence
from ctypes import Array, pointer
from ctypes import c_char, c_char_p, c_int, c_ubyte, c_uint, c_ulong

class FILE: ...

def fdopen(fd: int, mode: bytes) -> pointer[FILE]: ...  # type: ignore[type-var]

Oid = c_uint

class PGconn_struct: ...
class PGresult_struct: ...
class PGcancel_struct: ...

class PQconninfoOption_struct:
    keyword: bytes
    envvar: bytes
    compiled: bytes
    val: bytes
    label: bytes
    dispchar: bytes
    dispsize: int

class PGnotify_struct:
    be_pid: int
    relname: bytes
    extra: bytes

class PGresAttDesc_struct:
    name: bytes
    tableid: int
    columnid: int
    format: int
    typid: int
    typlen: int
    atttypmod: int

def PQhostaddr(arg1: Optional[PGconn_struct]) -> bytes: ...
def PQerrorMessage(arg1: Optional[PGconn_struct]) -> bytes: ...
def PQresultErrorMessage(arg1: Optional[PGresult_struct]) -> bytes: ...
def PQexecPrepared(
    arg1: Optional[PGconn_struct],
    arg2: bytes,
    arg3: int,
    arg4: Optional[Array[c_char_p]],
    arg5: Optional[Array[c_int]],
    arg6: Optional[Array[c_int]],
    arg7: int,
) -> PGresult_struct: ...
def PQprepare(
    arg1: Optional[PGconn_struct],
    arg2: bytes,
    arg3: bytes,
    arg4: int,
    arg5: Optional[Array[c_uint]],
) -> PGresult_struct: ...
def PQgetvalue(
    arg1: Optional[PGresult_struct], arg2: int, arg3: int
) -> pointer[c_char]: ...
def PQcmdTuples(arg1: Optional[PGresult_struct]) -> bytes: ...
def PQescapeStringConn(
    arg1: Optional[PGconn_struct],
    arg2: c_char_p,
    arg3: bytes,
    arg4: int,
    arg5: pointer[c_int],
) -> int: ...
def PQescapeString(arg1: c_char_p, arg2: bytes, arg3: int) -> int: ...
def PQsendPrepare(
    arg1: Optional[PGconn_struct],
    arg2: bytes,
    arg3: bytes,
    arg4: int,
    arg5: Optional[Array[c_uint]],
) -> int: ...
def PQsendQueryPrepared(
    arg1: Optional[PGconn_struct],
    arg2: bytes,
    arg3: int,
    arg4: Optional[Array[c_char_p]],
    arg5: Optional[Array[c_int]],
    arg6: Optional[Array[c_int]],
    arg7: int,
) -> int: ...
def PQcancel(
    arg1: Optional[PGcancel_struct], arg2: c_char_p, arg3: int
) -> int: ...
def PQsetNoticeReceiver(
    arg1: PGconn_struct, arg2: Callable[[Any], PGresult_struct], arg3: Any
) -> Callable[[Any], PGresult_struct]: ...

# TODO: Ignoring type as getting an error on mypy/ctypes:
# Type argument "psycopg.pq._pq_ctypes.PGnotify_struct" of "pointer" must be
# a subtype of "ctypes._CData"
def PQnotifies(
    arg1: Optional[PGconn_struct],
) -> Optional[pointer[PGnotify_struct]]: ...  # type: ignore
def PQputCopyEnd(
    arg1: Optional[PGconn_struct], arg2: Optional[bytes]
) -> int: ...

# Arg 2 is a pointer, reported as _CArgObject by mypy
def PQgetCopyData(
    arg1: Optional[PGconn_struct], arg2: Any, arg3: int
) -> int: ...
def PQsetResultAttrs(
    arg1: Optional[PGresult_struct],
    arg2: int,
    arg3: Array[PGresAttDesc_struct],  # type: ignore
) -> int: ...
def PQtrace(
    arg1: Optional[PGconn_struct],
    arg2: pointer[FILE],  # type: ignore[type-var]
) -> None: ...
def PQencryptPasswordConn(
    arg1: Optional[PGconn_struct],
    arg2: bytes,
    arg3: bytes,
    arg4: Optional[bytes],
) -> bytes: ...
def PQpipelineStatus(pgconn: Optional[PGconn_struct]) -> int: ...
def PQenterPipelineMode(pgconn: Optional[PGconn_struct]) -> int: ...
def PQexitPipelineMode(pgconn: Optional[PGconn_struct]) -> int: ...
def PQpipelineSync(pgconn: Optional[PGconn_struct]) -> int: ...
def PQsendFlushRequest(pgconn: Optional[PGconn_struct]) -> int: ...

# fmt: off
# autogenerated: start
def PQlibVersion() -> int: ...
def PQconnectdb(arg1: bytes) -> PGconn_struct: ...
def PQconnectStart(arg1: bytes) -> PGconn_struct: ...
def PQconnectPoll(arg1: Optional[PGconn_struct]) -> int: ...
def PQconndefaults() -> Sequence[PQconninfoOption_struct]: ...
def PQconninfoFree(arg1: Sequence[PQconninfoOption_struct]) -> None: ...
def PQconninfo(arg1: Optional[PGconn_struct]) -> Sequence[PQconninfoOption_struct]: ...
def PQconninfoParse(arg1: bytes, arg2: pointer[c_char_p]) -> Sequence[PQconninfoOption_struct]: ...
def PQfinish(arg1: Optional[PGconn_struct]) -> None: ...
def PQreset(arg1: Optional[PGconn_struct]) -> None: ...
def PQresetStart(arg1: Optional[PGconn_struct]) -> int: ...
def PQresetPoll(arg1: Optional[PGconn_struct]) -> int: ...
def PQping(arg1: bytes) -> int: ...
def PQdb(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def PQuser(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def PQpass(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def PQhost(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def _PQhostaddr(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def PQport(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def PQtty(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def PQoptions(arg1: Optional[PGconn_struct]) -> Optional[bytes]: ...
def PQstatus(arg1: Optional[PGconn_struct]) -> int: ...
def PQtransactionStatus(arg1: Optional[PGconn_struct]) -> int: ...
def PQparameterStatus(arg1: Optional[PGconn_struct], arg2: bytes) -> Optional[bytes]: ...
def PQprotocolVersion(arg1: Optional[PGconn_struct]) -> int: ...
def PQserverVersion(arg1: Optional[PGconn_struct]) -> int: ...
def PQsocket(arg1: Optional[PGconn_struct]) -> int: ...
def PQbackendPID(arg1: Optional[PGconn_struct]) -> int: ...
def PQconnectionNeedsPassword(arg1: Optional[PGconn_struct]) -> int: ...
def PQconnectionUsedPassword(arg1: Optional[PGconn_struct]) -> int: ...
def PQsslInUse(arg1: Optional[PGconn_struct]) -> int: ...
def PQexec(arg1: Optional[PGconn_struct], arg2: bytes) -> PGresult_struct: ...
def PQexecParams(arg1: Optional[PGconn_struct], arg2: bytes, arg3: int, arg4: pointer[c_uint], arg5: pointer[c_char_p], arg6: pointer[c_int], arg7: pointer[c_int], arg8: int) -> PGresult_struct: ...
def PQdescribePrepared(arg1: Optional[PGconn_struct], arg2: bytes) -> PGresult_struct: ...
def PQdescribePortal(arg1: Optional[PGconn_struct], arg2: bytes) -> PGresult_struct: ...
def PQresultStatus(arg1: Optional[PGresult_struct]) -> int: ...
def PQresultErrorField(arg1: Optional[PGresult_struct], arg2: int) -> Optional[bytes]: ...
def PQclear(arg1: Optional[PGresult_struct]) -> None: ...
def PQntuples(arg1: Optional[PGresult_struct]) -> int: ...
def PQnfields(arg1: Optional[PGresult_struct]) -> int: ...
def PQfname(arg1: Optional[PGresult_struct], arg2: int) -> Optional[bytes]: ...
def PQftable(arg1: Optional[PGresult_struct], arg2: int) -> int: ...
def PQftablecol(arg1: Optional[PGresult_struct], arg2: int) -> int: ...
def PQfformat(arg1: Optional[PGresult_struct], arg2: int) -> int: ...
def PQftype(arg1: Optional[PGresult_struct], arg2: int) -> int: ...
def PQfmod(arg1: Optional[PGresult_struct], arg2: int) -> int: ...
def PQfsize(arg1: Optional[PGresult_struct], arg2: int) -> int: ...
def PQbinaryTuples(arg1: Optional[PGresult_struct]) -> int: ...
def PQgetisnull(arg1: Optional[PGresult_struct], arg2: int, arg3: int) -> int: ...
def PQgetlength(arg1: Optional[PGresult_struct], arg2: int, arg3: int) -> int: ...
def PQnparams(arg1: Optional[PGresult_struct]) -> int: ...
def PQparamtype(arg1: Optional[PGresult_struct], arg2: int) -> int: ...
def PQcmdStatus(arg1: Optional[PGresult_struct]) -> Optional[bytes]: ...
def PQoidValue(arg1: Optional[PGresult_struct]) -> int: ...
def PQescapeLiteral(arg1: Optional[PGconn_struct], arg2: bytes, arg3: int) -> Optional[bytes]: ...
def PQescapeIdentifier(arg1: Optional[PGconn_struct], arg2: bytes, arg3: int) -> Optional[bytes]: ...
def PQescapeByteaConn(arg1: Optional[PGconn_struct], arg2: bytes, arg3: int, arg4: pointer[c_ulong]) -> pointer[c_ubyte]: ...
def PQescapeBytea(arg1: bytes, arg2: int, arg3: pointer[c_ulong]) -> pointer[c_ubyte]: ...
def PQunescapeBytea(arg1: bytes, arg2: pointer[c_ulong]) -> pointer[c_ubyte]: ...
def PQsendQuery(arg1: Optional[PGconn_struct], arg2: bytes) -> int: ...
def PQsendQueryParams(arg1: Optional[PGconn_struct], arg2: bytes, arg3: int, arg4: pointer[c_uint], arg5: pointer[c_char_p], arg6: pointer[c_int], arg7: pointer[c_int], arg8: int) -> int: ...
def PQsendDescribePrepared(arg1: Optional[PGconn_struct], arg2: bytes) -> int: ...
def PQsendDescribePortal(arg1: Optional[PGconn_struct], arg2: bytes) -> int: ...
def PQgetResult(arg1: Optional[PGconn_struct]) -> PGresult_struct: ...
def PQconsumeInput(arg1: Optional[PGconn_struct]) -> int: ...
def PQisBusy(arg1: Optional[PGconn_struct]) -> int: ...
def PQsetnonblocking(arg1: Optional[PGconn_struct], arg2: int) -> int: ...
def PQisnonblocking(arg1: Optional[PGconn_struct]) -> int: ...
def PQflush(arg1: Optional[PGconn_struct]) -> int: ...
def PQsetSingleRowMode(arg1: Optional[PGconn_struct]) -> int: ...
def PQgetCancel(arg1: Optional[PGconn_struct]) -> PGcancel_struct: ...
def PQfreeCancel(arg1: Optional[PGcancel_struct]) -> None: ...
def PQputCopyData(arg1: Optional[PGconn_struct], arg2: bytes, arg3: int) -> int: ...
def PQsetTraceFlags(arg1: Optional[PGconn_struct], arg2: int) -> None: ...
def PQuntrace(arg1: Optional[PGconn_struct]) -> None: ...
def PQfreemem(arg1: Any) -> None: ...
def _PQencryptPasswordConn(arg1: Optional[PGconn_struct], arg2: bytes, arg3: bytes, arg4: bytes) -> Optional[bytes]: ...
def PQmakeEmptyPGresult(arg1: Optional[PGconn_struct], arg2: int) -> PGresult_struct: ...
def _PQpipelineStatus(arg1: Optional[PGconn_struct]) -> int: ...
def _PQenterPipelineMode(arg1: Optional[PGconn_struct]) -> int: ...
def _PQexitPipelineMode(arg1: Optional[PGconn_struct]) -> int: ...
def _PQpipelineSync(arg1: Optional[PGconn_struct]) -> int: ...
def _PQsendFlushRequest(arg1: Optional[PGconn_struct]) -> int: ...
def PQinitOpenSSL(arg1: int, arg2: int) -> None: ...
# autogenerated: end
# fmt: on

# vim: set syntax=python:
