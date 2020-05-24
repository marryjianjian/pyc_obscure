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
        self.instr_offset   : list

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
        res = []
        offset = 0
        res.append(offset)
        for i in range(len(lnotab)//2):
            offset += lnotab[2 * i]
            res.append(offset)

        res.append(len(self.co.co_code))
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
        offsets = self.instr_offset
        res = b""
        index = 0
        for i in range(1, len(offsets)):
            obs_instr = self._get_obs_instr(len(res))
            res += obs_instr + code[offsets[i-1]:offsets[i]]

        self.co = self.new_code_object(code=res)

    def write_pyc(self, filename):
        s = pack16(self.magic_int) + b"\r\n"
        s += pack32(0) + pack32(self.timestamp) + pack32(self.source_size)
        s += marshal.dumps(self.co)
        # print(s)
        with open(filename, 'wb') as fw:
            fw.write(s)

    def modify_filename(self, modified_filename):
        self.co = self.new_code_object(filename=modified_filename)

    def add_string(self, string):
        assert(type(string) == str)
        consts = self.co.co_consts + (string,)
        self.co = self.new_code_object(consts=consts)

    def add_strings(self, strings):
        assert(type(strings) == list)
        consts = self.co.co_consts + tuple([i for i in strings])
        self.co = self.new_code_object(consts=consts)

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        obs = Obscure(filename)
        exec(obs.co)
        #print(len(obs.co.co_code), obs.co.co_code)
        obs.basic_obscure()
        obs.add_string('test add string')
        obs.add_strings(['a', 'b', 'd'])
        #print(len(obs.co.co_code), obs.co.co_code)
        obs.write_pyc('asd.pyc')
        exec(obs.co)

