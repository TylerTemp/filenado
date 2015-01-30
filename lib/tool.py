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


def split_endname(paths):
    # related path not support.
    rtn = []
    for each in paths:
        each.replace('\\', '/')
        # '/'
        if each == '/':
            rtn.append(('/', ''))
            continue
        elif each.endswith(':/'):
            rtn.append((each, ''))
            continue
        elif each.endswith('/'):
            each = each[:-1]

        if each.startswith('/') and (each.count('/')==1):
            # '/home' -> ('/', 'home')
            rtn.append(('/', each[1:]))
        elif ':/' in each and (each.count('/')==2):
            # 'C://path' -> ('C://', 'path')
            # 'C://' -> ('C://', '') <- this will not get there
            idx = each.find('://')+3
            rtn.append((each[:idx], each[idx:]))
        # '/home/tyler/', '/home/tyler/'
        else:
            rtn.append(tuple(each.rsplit('/', 1)))
    return rtn


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
        'C:\\Program Files (x86)/',
    ]

    expect = [
        ('/', ''),
        ('/', 'home'),
        ('/', 'home'),
        ('/home', 'tyler'),
        ('/home', 'tyler'),

        ('C:/', ''),
        ('C:/', 'Program Files (x86)'),
        ('C:/', 'Program Files (x86)'),
    ]

    result = split_endname(value)
    for v, e, r in zip(value, expect, result):
        print(v, e, r)
        assert e == r
