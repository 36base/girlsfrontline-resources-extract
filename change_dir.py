import os
import sys


if os.getcwd() != os.path.split(sys.argv[0])[0]:
    os.chdir(os.path.split(sys.argv[0])[0])
