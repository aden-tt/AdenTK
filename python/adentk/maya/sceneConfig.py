import pymel.core.system

def run(*args):
    print("Configuring Maya scene - %s" % pymel.core.system.sceneName())