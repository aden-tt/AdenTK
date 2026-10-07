# Start up Maya, copy and paste the code below into the script editor
# and run it to verify that the paths have been added to your environment.

import pymel.util

print('-------------Start Maya Script Paths----------------------')
for path in pymel.util.getEnv("MAYA_SCRIPT_PATH").split(';'):
    print('Script path - %s' % path)
print('-------------End Maya Script Paths----------------------\n')



print('-------------Start Maya Icon Paths----------------------')
for path in pymel.util.getEnv("XBMLANGPATH").split(';'):
    print('Icon path - %s' % path)
print('-------------End Maya Icon Paths----------------------\n')



print('-------------Start Maya Shelf Paths----------------------')
for path in pymel.util.getEnv("MAYA_SHELF_PATH").split(';'):
    print('Shelf path - %s' % path)
print('-------------End Maya Shelf Paths----------------------\n')




print('-------------Start Maya Python Paths----------------------')
for path in pymel.util.getEnv("PYTHONPATH").split(';'):
    print('Python path - %s' % path)
print('-------------End Maya Python Paths----------------------\n')



print('-------------Start Maya Plug in Paths----------------------')
for path in pymel.util.getEnv("MAYA_PLUG_IN_PATH").split(';'):
    print('Plugin path - %s' % path)
print('-------------End Maya Plug in Paths----------------------\n')


import sys

print('-------------Start Sys Paths----------------------')
for path in sys.path:
    print('Sys path - %s' % path)
print('-------------End Sys Paths----------------------')