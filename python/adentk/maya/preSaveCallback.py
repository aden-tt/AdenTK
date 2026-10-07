import pymel.core.system

def run(*args):
	sceneName = pymel.core.system.sceneName()
	print("Run any code you want to execute before maya saves the scene here (maybe checking out the Maya file from source control if it is read only)")
	return True