@@ECHO OFF
python setup.py install
python setup.py sdist build
python setup.py bdist_wheel --universal
rd /s /q "G:\\Python27\\Lib\\site-packages\\pykl\\"
rd /s /q "G:\\Python27\\Lib\\site-packages\\pykl.egg-info\\"
XCOPY /e /y /c /h /r /I "pykl" "G:\\Python27\\Lib\\site-packages\\pykl"
xcopy /e /y /c /h /r /I "pykl.egg-info" "G:\\Python27\\Lib\\site-packages\\pykl.egg-info"
python setup.py sdist --formats=zip upload