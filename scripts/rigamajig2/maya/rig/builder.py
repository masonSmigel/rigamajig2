"""
This module contains our rig builder
"""
import sys
import os
import time
import inspect
from collections import OrderedDict

import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.shared.runScript as runScript
import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta

import rigamajig2.maya.cmpts.main as main

import logging

logger = logging.getLogger(__name__)

CMPT_PATH = os.path.abspath(os.path.join(__file__, '../../cmpts'))

_EXCLUDED_FOLDERS = []
_EXCLUDED_FILES = ['__init__.py', 'base.py']

# BUILD ENVIORNMENT GLOBLALS
PRE_SCRIPT_PATH = 'pre_script'
POST_SCRIPT_PATH = 'post_script'
PUB_SCRIPT_PATH = 'pub_script'

# RIG FILE KEYS
MODEL_FILE = "model_file"
SKELETON_FILE = "skeleton_file"
SKELETON_POS = "skeleton_pos"
CONTROL_SHAPES = "control_shapes"
GUIDES = "guides"
COMPONENTS = "components"


class Builder(object):
    def __init__(self, rigFile=None):
        """
        Initalize the builder
        :param rigFile: path to the rig file
        """
        self.path = None
        self.set_rig_file(rigFile)
        self.cmpts = list()

        self._available_cmpts = list()
        self.__lookForComponents(CMPT_PATH)

        # varibles we need
        self.top_skeleton_nodes = list()
        self.load_cmpts_from_file = False

    def getComponents(self):
        return self._available_cmpts

    def __lookForComponents(self, path):
        res = os.listdir(path)
        toReturn = list()
        for r in res:
            full_path = os.path.join(path, r)
            if r not in _EXCLUDED_FOLDERS and os.path.isdir(path + '/' + r) == True:
                self.__lookForComponents(full_path)
            if r.find('.py') != -1 and r.find('.pyc') == -1 and r not in _EXCLUDED_FILES:
                if r.find('reload') == -1:

                    # find classes in the file path
                    module_file = r.split('.')[0]
                    modulesPath = 'rigamajig2.maya.cmpts.{}'
                    module_name = modulesPath.format(module_file)
                    module_object = __import__(module_name, globals(), locals(), ["*"], 0)
                    for cls in inspect.getmembers(module_object, inspect.isclass):
                        toReturn.append("{}.{}".format(module_file, cls[0]))

        self._available_cmpts += toReturn

    def _absPath(self, path):
        if path:
            return os.path.join(self.path, path)

    # RIG BUILD STEPS
    def import_model(self, path=None):
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, MODEL_FILE))

        if path and os.path.exists(path):
            file.import_(path, ns=None)
            logger.info("model imported")

    def import_skeleton(self, path=None):
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, SKELETON_FILE))

        if os.path.exists(path):
            nodes = file.import_(path, ns=None)
            logger.info("skeleton imported")

        # tag all bind joints
        for jnt in cmds.ls("*_bind", type='joint'):
            meta.tag(jnt, "bind")

        # get top level nodes in the skeleton
        for node in cmds.ls(nodes, l=True, type='transform'):
            if not len(node.split('|')) > 2:
                # self.top_skeleton_nodes.append(node)
                meta.tag(node, 'skeleton_root')

    def load_joint_positions(self, path=None):
        import rigamajig2.maya.data.joint_data as joint_data
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, SKELETON_POS))

        if os.path.exists(path):
            data_obj = joint_data.JointData()
            data_obj.read(path)
            data_obj.applyData(data_obj.getData().keys())
            logger.info("Joint positions loaded")

    def save_joint_positions(self, path=None):
        import rigamajig2.maya.data.joint_data as joint_data

        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, SKELETON_POS))

        # find all skeleton roots and get the positions of their children
        skeleton_roots = common.toList(meta.getTagged('skeleton_root'))
        if len(skeleton_roots) > 0:
            data_obj = joint_data.JointData()
            for root in skeleton_roots:
                logger.debug("Gathering data of joints under skeleton root_hrc: {}".format(root))
                data_obj.gatherDataIterate(cmds.listRelatives(root, allDescendents=True, type='joint'))
            data_obj.write(path)
            logger.info("Joint positions saved to: {}".format(path))
        else:
            raise RuntimeError("the root_hrc joint {} does not exists".format(skeleton_roots))

    def initalize(self):
        """Initalize rig (this is where the user can make changes)"""
        for cmpt in self.cmpts:
            logger.info('Initalizing: {}'.format(cmpt.name))
            cmpt._intialize_cmpt()
        self.load_guide_data()
        logger.info("initalize -- complete")

    def build(self):
        """build rig"""
        for cmpt in self.cmpts:
            logger.info('Building: {}'.format(cmpt.name))
            cmpt._build_cmpt()
            # if the component is not a main parent the cmpt.root_hrc to the rig
            if cmds.objExists('rig') and not isinstance(cmpt, main.Main):
                if hasattr(cmpt, "root_hrc"):
                    if not cmds.listRelatives(cmpt.root_hrc, p=True):
                        cmds.parent(cmpt.root_hrc, 'rig')

        # parent the bind joints to the bind group. if one exists
        if cmds.objExists('bind'):
            top_skeleton_nodes = meta.getTagged('skeleton_root')
            if not cmds.listRelatives(top_skeleton_nodes, p=True):
                cmds.parent(top_skeleton_nodes, 'bind')

        logger.info("build -- complete")

    def connect(self):
        """connect rig"""
        for cmpt in self.cmpts:
            logger.info('Connecting: {}'.format(cmpt.name))
            cmpt._connect_cmpt()
        logger.info("connect -- complete")

    def finalize(self):
        """finalize rig"""
        for cmpt in self.cmpts:
            logger.info('Finalizing: {}'.format(cmpt.name))
            cmpt._finalize_cmpt()
        logger.info("finalize -- complete")

    def optimize(self):
        """optimize rig"""
        for cmpt in self.cmpts:
            logger.info('Optimizing {}'.format(cmpt.name))
            cmpt._optimize_cmpt()
        logger.info("optimize -- complete")

    def save_components(self, path=None):
        """
        Save out components
        :param path: path to components
        :return:
        """
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, COMPONENTS))

        cmpt_data = OrderedDict()
        cd = abstract_data.AbstractData()
        for cmpt in self.cmpts:
            cmpt_data[cmpt.name] = cmpt.get_cmpt_data()

        cd.setData(cmpt_data)
        cd.write(path)
        logger.info("Components saved to: {}".format(path))

    def load_components(self, path=None):
        """
        Load components
        :param path:
        :return:
        """
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, COMPONENTS))
        cd = abstract_data.AbstractData()
        cd.read(path)
        cmpt_data = cd.getData()

        self.set_cmpts(list())
        for cmpt in list(cmpt_data.keys()):
            # dynamically load component module into python
            module_name, class_name = cmpt_data[cmpt]['type'].split(".")
            modulesPath = 'rigamajig2.maya.cmpts.{}'
            module_name = modulesPath.format(module_name)
            module_object = __import__(module_name, globals(), locals(), ["*"], 0)

            cmpt_class = getattr(module_object, class_name)
            instance = cmpt_class(cmpt_data[cmpt]['name'], cmpt_data[cmpt]['input'])
            self.append_cmpts(instance)
            self.load_cmpts_from_file = True

        logger.info("components loaded -- complete")

    def load_component_settings(self, path=None):
        """
        load_settings component settings
        :param path:
        :return:
        """
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, COMPONENTS))

        if self.load_cmpts_from_file:
            cd = abstract_data.AbstractData()
            cd.read(path)
            cmpt_data = cd.getData()
            for cmpt in self.cmpts:
                cmpt.load_settings(cmpt_data[cmpt.name])

    def load_controlShapes(self, path=None, applyColor=True):
        """
        Load the control shapes
        :param path: path to control shape
        :param applyColor: Apply the control colors.
        :return:
        """
        import rigamajig2.maya.data.curve_data as curve_data

        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, CONTROL_SHAPES))

        cd = curve_data.CurveData()
        cd.read(path)

        if os.path.exists(path):
            controls = [ctl for ctl in cd.getData().keys() if cmds.objExists(ctl)]
            logger.info("loading shapes for {} controls".format(len(controls)))
            cd.applyData(controls, applyColor=applyColor)
            logger.info("control shapes -- complete")

    def save_controlShapes(self, path=None):
        import rigamajig2.maya.data.curve_data as curve_data

        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, CONTROL_SHAPES))

        if path:
            cd = curve_data.CurveData()
            cd.gatherDataIterate(meta.getTagged("control"))
            cd.write(path)
            logger.info("control shapes saved to: {}".format(path))

    def load_guide_data(self, path=None):
        """
        Load guide data
        :return:
        """
        import rigamajig2.maya.data.node_data as node_data
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, GUIDES))

        if os.path.exists(path):
            nd = node_data.NodeData()
            nd.read(path)
            nd.applyData(nodes=nd.getData().keys())
            logger.info("guides loaded")

    def save_guide_data(self, path=None):
        """
        Save guides data
        :param path:
        :return:
        """
        import rigamajig2.maya.data.node_data as node_data
        if not path:
            path = self._absPath(self.get_rig_data(self.rig_file, GUIDES))

        if path:
            nd = node_data.NodeData()
            nd.gatherDataIterate(meta.getTagged("guide"))
            nd.write(path)
            logger.info("guides saved to: {}".format(path))

    def load_deform_data(self):
        """
        Load other data, this is stuff like skinweights, blendshapes, clusters etc.
        :return:
        """
        logger.info("data loading -- complete")

    def show_advanced_proxy(self):
        """
        Show the advanced proxy attributes for the components
        :return:
        """
        for cmpt in self.cmpts:
            if cmpt.get_step() >= 2:
                logger.warning("component {} is already build. No use creating proxy feedback".format(cmpt))
            else:
                cmpt._show_advanced_proxy()

    def delete_advanced_proxy(self):
        for cmpt in self.cmpts:
            if cmpt.proxy_setup_exists():
                cmpt._delete_advanced_proxy()

    # RUN SCRIPTS
    def load_required_plugins(self):
        """
        load_settings required plugins
        NOTE: there are plugins REQUIRED for rigamajig. for other plug-ins needed in production add them as a pre-script.
        """
        loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True)

        for plugin in common.REQUIRED_PLUGINS:
            if plugin not in loaded_plugins:
                cmds.loadPlugin(plugin)

    def pre_script(self, scripts=[]):
        """
        Run pre scripts. You can add scripts by path, but the main use is through the PRE SCRIPT path
        :param scripts: path to scripts to run
        """
        if self.path:
            scripts_path = self._absPath(PRE_SCRIPT_PATH)
            for script in runScript.find_scripts(scripts_path):
                scripts.append(script)

        for script in scripts:
            runScript.run_script(script)
        logger.info("pre scripts -- complete")

    def post_script(self, scripts=[]):
        """
        Run post scripts. You can add scripts by path, but the main use is through the POST SCRIPT path
        :param scripts: path to scripts to run
        """
        if self.path:
            scripts_path = self._absPath(POST_SCRIPT_PATH)
            for script in runScript.find_scripts(scripts_path):
                scripts.append(script)

        for script in scripts:
            runScript.run_script(script)
        logger.info("post scripts -- complete")

    def pub_script(self, scripts=[]):
        """
        Run Post Scripts. You can add scripts by path, but the main use is through the POST SCRIPT path
        :param scripts:
        :return:
        """
        if self.path:
            scripts_path = self._absPath(PUB_SCRIPT_PATH)
            for script in runScript.find_scripts(scripts_path):
                scripts.append(script)

        for script in scripts:
            runScript.run_script(script)
        logger.info("publish scripts -- complete")

    # ULITITY FUNCTION TO BUILD THE ENTIRE RIG
    def run(self, optimize=True):
        if not self.path:
            logger.error('you must provide a build enviornment path. Use Bulder.set_rig_file()')
            return

        start_time = time.time()
        print('\nBegin Rig Build\n{0}\nbuild env: {1}\n'.format('-' * 70, self.path))
        self.load_required_plugins()
        self.pre_script()
        self.import_model()
        self.import_skeleton()
        self.load_joint_positions()
        self.load_components()
        self.initalize()
        self.load_component_settings()
        self.build()
        self.connect()
        self.finalize()
        self.load_controlShapes()
        self.load_deform_data()
        self.post_script()
        if optimize: self.optimize()
        end_time = time.time()
        final_time = end_time - start_time

        print('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}\n'.format(final_time, '-' * 70))

    # UTILITY FUNCTIONS
    def set_rig_file(self, rigFile):
        if not rigFile:
            return

        if not os.path.exists(rigFile):
            # TODO: give the user the option to create a rig file somewhere
            raise RuntimeError("'{0}' does not exist".format(rigFile))
        self.rig_file = rigFile

        rig_data = abstract_data.AbstractData()
        rig_data.read(self.rig_file)
        data = rig_data.getData()
        if "rig_env" not in data:
            rig_env_path = '../'
        else:
            rig_env_path = data["rig_env"]
        self.path = os.path.abspath(os.path.join(self.rig_file, rig_env_path))
        logger.info('\n\nRig Enviornment path: {0}'.format(self.path))

    # GET
    def get_path(self):
        return self.path

    def get_rig_file(self):
        return self.rig_file

    # SET
    def set_cmpts(self, cmpts):
        """
        Set the self.cmpts
        :param cmpts: list of components to set
        """
        cmpts = common.toList(cmpts)
        self.cmpts = cmpts

    def append_cmpts(self, cmpts):
        """
        append a component
        :param cmpts: list of components to append
        :return:
        """
        cmpts = common.toList(cmpts)
        for cmpt in cmpts:
            self.cmpts.append(cmpt)

    @classmethod
    def get_rig_data(cls, rig_file, key):
        """
        read the data from the self.rig_file
        :param rig_file:
        :param key:
        :return:
        """
        if not os.path.exists(rig_file):
            raise RuntimeError('rig file at {} does not exist'.format(rig_file))

        data = abstract_data.AbstractData()
        data.read(rig_file)
        if key in data.getData():
            return data.getData()[key]
        return None


def build_directory():
    pass
