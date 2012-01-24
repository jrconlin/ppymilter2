TOP = $(shell pwd)
VE  = virtualenv
PY  = $(TOP)/bin/python
EZ  = $(TOP)/bin/easy_install
NO  = $(TOP)/bin/nosetests --with-xunit
PIP = $(TOP)/bin/pip

init:
	$(VE) --no-site-packages --distribute .
	$(PIP) install -r dev-reqs.txt

build:  init
	$(PY) setup.py sdist
    
