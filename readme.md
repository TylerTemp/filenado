filenado
===========

a simple tornado server to share files on your PC


Install
---------

```bash
$ git clone https://github.com/TylerTemp/filenado.git
$ cd filenado
$ pip install -r requirement.txt
```

Usage
-----------

```bash
$ cd path/you/want/to/share
$ python /path/to/filenado/main.py
```
```
Usage:
main.py [options] [<path>...]

Options:
-r --root=<path>          the folder you want to share. This will shadow <path>
-p --port=<port>          listen to this port[default: 8000]
-l --logging=<level>      log level, can be "DEBUG", "INOF", "WARNING", "ERROR", "CRITICAL", or number from 0 to 50[default: INFO]
```

Note that if none of <path>, --root and "sharepath"(in "config.json")  is presented, it will shared the current working dir.


Licence
-------------

Under [GPL v3](http://www.gnu.org/licenses/gpl.txt)

Tech
------------

Filenado use the following project
* [tornado](www.tornadoweb.org/)
* [docopt](https://github.com/docopt/docopt)
* <[Python Cookbook](http://www.amazon.com/Python-Cookbook-Third-David-Beazley/dp/1449340377/ref=sr_1_1?ie=UTF8&qid=1422410102&sr=8-1&keywords=python+cookbook)> (lib/trace_more.py use some code from this book)


TODO
------------

* add seaching files
