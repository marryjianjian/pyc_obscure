#!/usr/bin/env python3
import xdis
import types
import os
import opcode
import struct
import marshal


def pack32(n):
    return struct.pack("<I", n)


def pack16(n):
    return struct.pack("<H", n)


class Obscure:
    '''Obscure() -> new empty Obscure object
    Obscure(filename) -> new Obscure object load from file
    '''

    def __init__(self, filename=None):
        self.float_version  : float
        self.magic_int      : int
        self.timestamp      : int
        self.co             : types.CodeType
        self.ispypy         : bool
        self.source_size    : int
        self.sip_hash       : int
        self.instr_offset   : set

        if filename is not None:
            self.load_pyc(filename)

    def _load_pyc(self, filename):
        return xdis.load_module(filename)

    def load_pyc(self, filename):
        (
            self.float_version,
            self.timestamp,
            self.magic_int,
            self.co,
            self.ispypy,
            self.source_size,
            self.sip_hash,
        ) = self._load_pyc(filename)

        self.instr_offset = self.get_instr_offset_from_lnotab(self.co.co_lnotab)

    def get_instr_offset_from_lnotab(self, lnotab):
        assert(type(lnotab) == bytes)
        assert(len(lnotab) & 1 == 0)
        res = set()
        offset = 0
        res.add(offset)
        for i in range(len(lnotab)//2):
            offset += lnotab[2 * i]
            res.add(offset)

        return res

    def _gen_obs37_opcode_from_offset(self, offset):
        return bytes((opcode.opmap['JUMP_ABSOLUTE'], offset + 4)) + os.urandom(2)

    def _get_obs_instr(self, offset):
        return self._gen_obs37_opcode_from_offset(offset)

    def new_code_object(self,
                        argcount       = None,
                        kwonlyargcount = None,
                        nlocals        = None,
                        stacksize      = None,
                        flags          = None,
                        code           = None,
                        consts         = None,
                        names          = None,
                        varnames       = None,
                        filename       = None,
                        name           = None,
                        firstlineno    = None,
                        lnotab         = None,
                        freevars       = None,
                        cellvars       = None,
                        ):
        if argcount is None:
            argcount = self.co.co_argcount
        if kwonlyargcount is None:
            kwonlyargcount = self.co.co_kwonlyargcount
        if nlocals is None:
            nlocals = self.co.co_nlocals
        if stacksize is None:
            stacksize = self.co.co_stacksize
        if flags is None:
            flags = self.co.co_flags
        if code is None:
            code = self.co.co_code
        if consts is None:
            consts = self.co.co_consts
        if names is None:
            names = self.co.co_names
        if varnames is None:
            varnames = self.co.co_varnames
        if filename is None:
            filename = self.co.co_filename
        if name is None:
            name = self.co.co_name
        if firstlineno is None:
            firstlineno = self.co.co_firstlineno
        if lnotab is None:
            lnotab = self.co.co_lnotab
        if freevars is None:
            freevars = self.co.co_freevars
        if cellvars is None:
            cellvars = self.co.co_cellvars

        return types.CodeType(
            argcount,
            kwonlyargcount,
            nlocals,
            stacksize,
            flags,
            code,
            tuple(consts),
            tuple(names),
            tuple(varnames),
            filename,
            name,
            firstlineno,
            lnotab,
            tuple(freevars),
            tuple(cellvars),
        )

    def basic_obscure(self):
        code = self.co.co_code
        res = b""
        index = 0
        for rel_offset in self.instr_offset:
            index += rel_offset
            obs_instr = self._get_obs_instr(index)
            res += code[index-rel_offset:index] + obs_instr

        res += code[index:]
        self.co = self.new_code_object(code=res)

    def write_pyc(self, filename):
        s = pack16(self.magic_int) + b"\r\n"
        s += pack32(0) + pack32(self.timestamp) + pack32(self.source_size)
        s += marshal.dumps(self.co)
        print(s)
        with open(filename, 'wb') as fw:
            fw.write(s)


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        obs = Obscure(filename)
        exec(obs.co)
        print(obs.co.co_code)
        obs.basic_obscure()
        print(obs.co.co_code)
        obs.write_pyc('asd.pyc')
        # exec(obs.co)
        # exec(obs.co)
        print(obs.co.co_code)

