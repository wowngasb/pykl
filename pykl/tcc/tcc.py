#-*- coding: utf-8 -*-

class TCCState(object):

    include_paths = []

    sysinclude_paths = []

    cmd_include_files = []

    error_opaque = None  # void *error_opaque;
    error_func = None   # void (*error_func)(void *opaque, const char *msg);


    include_stack = []  # BufferedFile *include_stack[INCLUDE_STACK_SIZE];
    include_stack_ptr = None  # BufferedFile **include_stack_ptr;

    ifdef_stack = []  #     int ifdef_stack[IFDEF_STACK_SIZE];
    ifdef_stack_ptr = None  #     int *ifdef_stack_ptr;

    cached_includes = []  #  CachedInclude **cached_includes;

    inline_fns = []  # struct InlineFunc **inline_fns;

    sections = []  # Section **sections;

    priv_sections = []  # Section **priv_sections;

    def __init__(self, include_path = [], sysinclude_path = [], symbol = {}):
        for pathname in include_path:
            self.add_include_path(pathname)

        for pathname in sysinclude_path:
            self.add_sysinclude_path(pathname)

        for sym, value in symbol.items():
            self.define_symbol(sym, value)

    def add_include_path(self, pathname):
        pass

    def add_sysinclude_path(self, pathname):
        pass

    def set_options(self, str):
        pass

    def define_symbol(self, sym, value):
        pass

    def undefine_symbol(self, sym):
        pass

    def compile_string(self, buf):
        pass

def main():
    tc = TCCState()
    ret = tc.compile_string(CODE_STR)
    print ret

CODE_STR = '''
#include "hello.h"
int main(){hello(); return 0;}
'''

if __name__ == '__main__':
    main()
