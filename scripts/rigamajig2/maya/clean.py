"""
Clean scene functions
"""
import maya.cmds as cmds
import maya.mel as mel
import logging

logger = logging.getLogger(__name__)


def cleanNodes():
    """
    Clean up unused nodes
    """
    # source the new MLdeleteUnused to solve a bug deleting the default aiStandard shader in Maya2020
    ovMLdeleteUnusedPath = '/'.join(__file__.split('/')[:-1]) + '/MLdeleteUnused.mel'
    mel.eval('source "{}"'.format(ovMLdeleteUnusedPath))

    mel.eval("MLdeleteUnused")
    nodes = cmds.ls(typ=['groupId', 'nodeGraphEditorInfo', 'nodeGraphEditorBookmarkInfo', 'unknown'])
    if nodes:
        for node in nodes:
            nodeType = cmds.nodeType(node)
            isConnected = cmds.listHistory(node, f=True, il=True)
            if ("GraphEditor" in nodeType) or ("unknown" in nodeType) or not isConnected:
                try:
                    cmds.lockNode(node, l=False)
                    cmds.delete('node')
                    logger.info("Cleaned Node: '{}'".format(node))
                except:
                    pass


def cleanPlugins():
    """
    Clean unknown plugins
    """
    plugins = cmds.unknownPlugin(q=True, l=True)
    if plugins:
        for plugin in plugins:
            try:
                cmds.unknownPlugin(plugin, r=True)
                logger.info("Cleaned Plugin: '{}'".format(plugin))
            except:
                pass


def cleanRougePanels():
    """
    cleanup rouge procedures from all modelPanels
    It will remove errors like:
        // Error: line 1: Cannot find procedure "CgAbBlastPanelOptChangeCallback". //
        // Error: line 1: Cannot find procedure "DCF_updateViewportList". //
    """

    EVIL_METHOD_NAMES = ['DCF_updateViewportList', 'CgAbBlastPanelOptChangeCallback']
    capitalEvilMethodNames = [name.upper() for name in EVIL_METHOD_NAMES]
    modelPanelLabel = mel.eval('localizedPanelLabel("ModelPanel")')
    processedPanelNames = []
    panelName = cmds.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel))
    while panelName and panelName not in processedPanelNames:
        editorChangedValue = cmds.modelEditor(panelName, query=True, editorChanged=True)
        parts = editorChangedValue.split(';')
        newParts = []
        changed = False
        for part in parts:
            for evilMethodName in capitalEvilMethodNames:
                if evilMethodName in part.upper():
                    changed = True
                    logger.info("removed callback '{}' from pannel '{}'".format(part, panelName))
                    break
            else:
                newParts.append(part)
        if changed:
            cmds.modelEditor(panelName, edit=True, editorChanged=';'.join(newParts))
        processedPanelNames.append(panelName)
        panelName = cmds.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel)) or None


def cleanScene():
    """
    Cleanup maya scene
    :return:
    """
    print('\n{}\n \tCLEAN MAYA SCENE'.format('-' * 80))

    print('{}\n\tClean Nodes: '.format('-' * 80))
    cleanNodes()

    print('{}\n\tClean Plugins: '.format('-' * 80))
    cleanPlugins()

    print('{}\n\tClean RougePanels: '.format('-' * 80))
    cleanRougePanels()
    print('-' * 80)
