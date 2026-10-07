"""
Credit: https://learncreategame.com/techart/maya-environment-setup/

AdenTK Maya environment plugin

Sets up the AdenTK tool environment on load:
- Adds plug-in, script, and shelf paths via a generated adentk.mod file
- Adds the Python root to sys.path
- Registers before-save, after-open, and after-new callbacks

Load via Windows > Settings/Preferences > Plug-in Manager.

"""


import maya.api.OpenMaya as OpenMaya
import traceback
import os
import sys
import inspect
import pymel.core.language
import pymel.util

pythonRoot = None
saveSceneJobId = -1
openSceneJobId = -1
newSceneJobId = -1

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


class AdenTKInitialize(OpenMaya.MPxCommand):
    kPluginCmdName = "adentkInitialize"

    @staticmethod
    def cmdCreator():
        return AdenTKInitialize()

    def __init__(self):
        super(AdenTKInitialize, self).__init__()

    def doIt(self, argList):
        # executed when command run via python or MEL
        # user should be going to plugin manager and browsing to the plugin to load it
        # so that we can set up the environment or reset it when they load/unload the plugin
        raise Exception('Plugin not supposed to be invoked - only loaded or unloaded.')



def initializePlugin(obj):
    """
    :param obj: OpenMaya.MObject
    :return: None
    """
    plugin = OpenMaya.MFnPlugin(obj, 'Aden TA Toolkit', '1.0', 'Any')
    try:
        plugin.registerCommand(AdenTKInitialize.kPluginCmdName, AdenTKInitialize.cmdCreator)
        load()

    except Exception as e:
        raise RuntimeError("Failed to register command: %s\nDetails:\n%s" % (e, traceback.format_exc()))


def uninitializePlugin(obj):
    """
    :param obj: OpenMaya.MObject
    :return: None
    """
    plugin = OpenMaya.MFnPlugin(obj)
    try:
        teardown()
        plugin.deregisterCommand(AdenTKInitialize.kPluginCmdName)
    except Exception as e:
        raise RuntimeError("Failed to unregister command: %s\nDetails:\n%s" % (e, traceback.format_exc()))

def load():
    """
    On initialization, this function gets called to:
    - Add plug in paths to the Maya environment
    - Add Python root path to sys.path
    - Create a mod file in user local that adds plug in path to this plug in to retain auto load
    - Create Maya before scene save callback
    - Create Maya after open scene callback
    - Create Maya new scene callback
    - Override incrementalSaveScene (due to AD bug)
    """

    # Declare globals so that we can modify the variables
    global pythonRoot
    global saveSceneJobId
    global openSceneJobId
    global newSceneJobId

    # This is where the plug in is currently being loaded from
    plugPath = inspect.getfile(inspect.currentframe())
    plugInRootFolderPath = os.path.abspath(os.path.join(plugPath, os.pardir)).replace('\\', '/')

    # Our framework's internal folder structure dictates that the python root folder path
    # is 4 levels up from .../adentk/maya/plugin/adentk_bootstrap.py which is the "plugPath" variable
    pythonRoot = '/'.join(plugPath.split('/')[0:-4])

    # Check if the modules directory exists in the user preference directory (if it doesn't, create it)
    mayaModuleDirectoryPath = '%s/modules' % pymel.util.getEnv('MAYA_APP_DIR')
    if not os.path.exists(mayaModuleDirectoryPath):
        os.makedirs(mayaModuleDirectoryPath)

    # Define the module file path
    mayaModuleFile = '%s/adentk.mod' % mayaModuleDirectoryPath

    # Given where the plug in is loaded from this the root dir of our framework (AdenTK)
    toolRoot = '/'.join(plugPath.split('/')[0:-5])

    # Write our module file
    with open(mayaModuleFile, 'w') as moduleFile:
        # String for adding the Maya site
        output = '+ AdenTK 1.0 %s/maya' % toolRoot
        # Add string for Python paths
        output += '\r\nPYTHONPATH += %s' % pythonRoot
        output += '\r\nPYTHONPATH += %s/adentk/lib' % pythonRoot

        # Dynamically add all subdirectories containing py files of the root maya plugin Python folder
        for directory, subDirectories, filenames in os.walk(plugInRootFolderPath):
            if len([filename for filename in filenames if
                    not '__init__' in filename and filename.lower().endswith('.py')]) == 0:
                continue
            plugInFolderPath = directory.replace('\\', '/')
            output += '\r\nMAYA_PLUG_IN_PATH += %s' % plugInFolderPath

            # First time that the module is written, the path will not yet be initialized - do it here
            if not plugInFolderPath in pymel.util.getEnv("MAYA_PLUG_IN_PATH"):
                pymel.util.putEnv("MAYA_PLUG_IN_PATH", [pymel.util.getEnv("MAYA_PLUG_IN_PATH"), plugInFolderPath])

        # Any shelf file in this directory will be automatically loaded on Maya startup
        output += '\r\nMAYA_SHELF_PATH += %s/maya/shelves' % toolRoot
        moduleFile.write(output)

    # The very first time the plug in is loaded Python path will not be initialized - do it here
    if not pythonRoot in sys.path:
        sys.path.append(pythonRoot)
        sys.path.append('%s/adentk/lib' % pythonRoot)

    # Now our framework is available to Maya.
    # Import modules to set up pre-save callback and scene configuration
    import adentk.maya.preSaveCallback
    import adentk.maya.sceneConfig
    import adentk.maya.about

    # Add pre save scene callback
    saveSceneJobId = OpenMaya.MSceneMessage.addCheckCallback(OpenMaya.MSceneMessage.kBeforeSaveCheck,
                                                             adentk.maya.preSaveCallback.run, None)
    # Add after open scene callback (for scene configuration)
    openSceneJobId = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterOpen, adentk.maya.sceneConfig.run,
                                                        None)
    # Add after new scene callback (for scene configuration)
    newSceneJobId = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterNew, adentk.maya.sceneConfig.run, None)

    # For incremental save we have to overload the global proc incrementalSaveScene because
    # Autodesk/Maya removes the file from file system when saving an iteration and then puts it back
    # We need to trigger our pre-save callback before that happens. The Overload script sits in the module folder's scripts directory (AdenTK/maya/scripts)
    try:
        # First make sure script path is added (first time plug in is loaded it will not be)
        scriptRootPath = '%s/maya/scripts' % toolRoot
        if not scriptRootPath in pymel.util.getEnv("MAYA_SCRIPT_PATH"):
            pymel.util.putEnv("MAYA_SCRIPT_PATH", [pymel.util.getEnv("MAYA_SCRIPT_PATH"), scriptRootPath])
        pymel.core.language.Mel.source('Overload_%s' % adentk.maya.about.version, language='mel')

    except Exception as e:
        pass

def teardown():
    """
    On uninitialization, this function gets called to:
    - Remove Python root path from sys.path
    - Remove Maya before scene callback
    - Remove Maya after open scene callback
    - Remove Maya new scene callback
    - Re-source the original incrementalSaveScene
    """

    # Remove our Python root from sys.path
    for sysPath in sys.path:
        if sysPath == pythonRoot:
            sys.path.remove(sysPath)

    # Remove Maya before scene callback
    OpenMaya.MSceneMessage.removeCallback(saveSceneJobId)
    # Remove Maya after open scene callback
    OpenMaya.MSceneMessage.removeCallback(openSceneJobId)
    # Remove Maya new scene callback
    OpenMaya.MSceneMessage.removeCallback(newSceneJobId)

    # Re-source the original incrementalSaveScene
    pymel.core.language.Mel.source('incrementalSaveScene', language='mel')
