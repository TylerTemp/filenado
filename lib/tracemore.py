import sys
import traceback
try:
    from io import StringIO
except ImportError:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

_tmp_stream = StringIO()

def print_exc_plus(stream=sys.stdout):
    '''print normal traceback information with some local arg values'''
    # code of this mothod is mainly from <Python Cookbook>
    write = stream.write    # assert the mothod exists
    flush = stream.flush
    tb = sys.exc_info()[2]
    while tb.tb_next:
        tb = tb.tb_next
    stack = list()
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    traceback.print_exc(None, stream)
    write('Locals by frame, innermost last\n')
    for frame in stack:
        write('\nFrame %s in %s at line %s\n' % (frame.f_code.co_name,
                                                     frame.f_code.co_filename,
                                                     frame.f_lineno))
    for key, value, in frame.f_locals.items():
        write('\t%20s = ' % key)
        try:
            write('%s\n'%value)
        except:
            write('<ERROR WHILE PRINTING VALUE>\n')
    flush()

def get_exc_plus():
    _tmp_stream.seek(0)
    _tmp_stream.truncate()
    print_exc_plus(_tmp_stream)
    _tmp_stream.seek(0)
    return _tmp_stream.read()

if __name__ == '__main__':
    def zero_error():
        local_1 = range(5)
        local_2 = 'a local arg'
        1/0

    stream = StringIO()
    try:
        zero_error()
    except Exception:
        print_exc_plus(stream)

    print('Err from stream:')
    print(stream.getvalue())
    stream.close()

    try:
        zero_error()
    except Exception:
        print('Err from get_exc_plus():')
        print(get_exc_plus())
