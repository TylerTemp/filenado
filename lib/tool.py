import sys
# get version
py3 = (sys.version_info[0] >= 3)
py2 = (not py3)


if not py3:
    import codecs
    import warnings
    def open(file, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None, closefd=True, opener=None):
        if newline is not None:
            warnings.warn('newline is not supported in py2')
        if not closefd:
            warnings.warn('closefd is not supported in py2')
        if opener is not None:
            warnings.warn('opener is not supported in py2')
        return codecs.open(filename=file, mode=mode, encoding=encoding,
                    errors=errors, buffering=buffering)
else:
    open = open     # for import

def size(b):
    unit = ('B', 'KB', 'MB', 'GB')
    for suffix in unit:
        if b < 1024:
            break
        if isinstance(b, int) and (not b%1024):
            b >>= 10
        else:
            b /= 1024.
    else:
        suffix = 'TB'

    if isinstance(b, int):
        return '%d%s'%(b, suffix)
    else:
        return '%.2f%s'%(b, suffix)


def split_endname(path):
    # related path not support.
    path = path.replace('\\', '/')
    # '/'
    if path == '/':
        return ('/', '')
    
    # /home/ -> /home; C:/ -> C:
    if path.endswith('/'):
        path = path[:-1]

    if path.startswith('/') and (path.count('/')==1):
        # '/home' -> ('/', 'home')
        return ('/', path[1:])

    if path.endswith(':'):
        return (path, '')
    
    return tuple(path.rsplit('/', 1))


if __name__ == '__main__':
    for case in (10, 20468, 999999, 99999999, 9999999999, 999999999999, 99999999999999):
        print(size(case))

    value = [
        '/',
        '/home',
        '/home/',
        '/home/tyler',
        '/home/tyler/',

        'C:\\',
        'C:\\Program Files (x86)',
        'C:\\Program Files (x86)\\',
    ]

    expect = [
        ('/', ''),
        ('/', 'home'),
        ('/', 'home'),
        ('/home', 'tyler'),
        ('/home', 'tyler'),

        ('C:', ''),
        ('C:', 'Program Files (x86)'),
        ('C:', 'Program Files (x86)'),
    ]

    for v, e in zip(value, expect):
        result = split_endname(v)
        print('%s -> %s (expect: %s)'%(v, result, e))
        assert(result == e)