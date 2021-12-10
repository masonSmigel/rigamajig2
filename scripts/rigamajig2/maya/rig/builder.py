"""
This module contains our rig builder
"""
import os
import time

import maya.cmds as cmds
import rigamajig2.shared.common as common
import rigamajig2.shared.runScript as runScript
import rigamajig2.maya.data.abstract_data as abstract_data
import rigamajig2.maya.file as file
import rigamajig2.maya.meta as meta
from rigamajig2.maya.cmpts import *

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


class Builder(object):
    def __init__(self, rigFile=None):
        """
        Initalize the builder
        :param rigFile: path to the rig file
        """
        self.set_rig_file(rigFile)
        self.cmpts = list()

        self._cmpts_path_dict = dict()
        self._available_cmpts = list()
        self.getComponents()

        # varibles we need
        self.top_skeleton_nodes = list()

    def getComponents(self):
        path = CMPT_PATH
        self.__lookForComponents(path)

    def __lookForComponents(self, path):
        res = os.listdir(path)
        toReturn = list()
        for r in res:
            if r not in _EXCLUDED_FOLDERS and os.path.isdir(path + '/' + r) == True:
                self.__lookForComponents()
            if r.find('.py') != -1 and r.find('.pyc') == -1 and r not in _EXCLUDED_FILES:
                if r.find('reload') == -1:
                    toReturn.append(r)
                    self._cmpts_path_dict[r] = path + r
        self._available_cmpts += toReturn

    def absPath(self, path):
        return os.path.join(self.path, path)

    # RIG BUILD STEPS
    def import_model(self, path=None):
        if path and os.path.exists(path=path):
            model = file.import_(path, ns=None)
        elif os.path.exists(self.absPath(self.get_rig_data(self.rig_file, MODEL_FILE))):
            model = file.import_(self.absPath(self.get_rig_data(self.rig_file, MODEL_FILE)), ns=None)
        else:
            return

    def import_skeleton(self, path=None):
        if path and os.path.exists(path=path):
            nodes = file.import_(path, ns=None)
        elif os.path.exists(self.absPath(self.get_rig_data(self.rig_file, SKELETON_FILE))):
            nodes = file.import_(self.absPath(self.get_rig_data(self.rig_file, SKELETON_FILE)), ns=None)
        else:
            return

        # get top level nodes in the skeleton
        for node in cmds.ls(nodes, l=True, type='transform'):
            if not len(node.split('|')) > 2:
                # self.top_skeleton_nodes.append(node)
                meta.tag(node, 'skeleton_root')

        logger.info("skeleton imported")

    def load_joint_positions(self, path=None):
        import rigamajig2.maya.data.joint_data as joint_data
        if path and os.path.exists(path=path):
            joint_pos_path = path
        elif os.path.exists(self.absPath(self.get_rig_data(self.rig_file, SKELETON_POS))):
            joint_pos_path = self.absPath(self.get_rig_data(self.rig_file, SKELETON_POS))
        else:
            return

        if os.path.exists(joint_pos_path):
            data_obj = joint_data.JointData()
            data_obj.read(joint_pos_path)
            data_obj.applyData(data_obj.getData().keys())
            logger.info("Joint positions loaded from: {}".format(joint_pos_path))

    def save_joint_positions(self, path=None):
        import rigamajig2.maya.data.joint_data as joint_data

        if path:
            joint_pos_path = path
        elif self.get_rig_data(self.rig_file, SKELETON_POS):
            joint_pos_path = self.absPath(self.get_rig_data(self.rig_file, SKELETON_POS))
        else:
            return

        # find all skeleton roots and get the positions of their children
        skeleton_roots = common.toList(meta.getTagged('skeleton_root'))
        if len(skeleton_roots) > 0:
            data_obj = joint_data.JointData()
            for root in skeleton_roots:
                logger.debug("Gathering data of joints under skeleton root: {}".format(root))
                data_obj.gatherDataIterate(cmds.listRelatives(root, allDescendents=True, type='joint'))
            data_obj.write(joint_pos_path)
            logger.info("Joint positions saved to: {}".format(joint_pos_path))
        else:
            raise RuntimeError("the root joint {} does not exists".format(skeleton_roots))

    def initalize(self):
        """Initalize rig (this is where the user can make changes)"""
        for cmpt in self.cmpts:
            logger.info('Initalizing: {}'.format(cmpt.name))
            cmpt._intialize_cmpt()
        logger.info("initalize -- complete")

    def build(self):
        """build rig"""
        for cmpt in self.cmpts:
            logger.info('Building: {}'.format(cmpt.name))
            cmpt._build_cmpt()
            # if the component is not a main parent the cmpt.root to the rig
            if cmds.objExists('rig') and not isinstance(cmpt, main.Main):
                cmds.parent(cmpt.root, 'rig')

        # parent the bind joints to the bind group. if one exists
        if cmds.objExists('bind'):
            top_skeleton_nodes = meta.getTagged('skeleton_root')
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

    def load_controlShapes(self, path=None, applyColor=True):
        """
        Load the control shapes
        :param path: path to control shape
        :param applyColor: Apply the control colors.
        :return:
        """
        import rigamajig2.maya.data.curve_data as curve_data

        if path and os.path.exists(path=path):
            control_shape_path = path
        elif os.path.exists(self.absPath(self.get_rig_data(self.rig_file, CONTROL_SHAPES))):
            control_shape_path = self.absPath(self.get_rig_data(self.rig_file, CONTROL_SHAPES))
        else:
            return

        cd = curve_data.CurveData()
        cd.read(control_shape_path)

        controls = cd.getData().keys()
        logger.info("loading shapes for {} controls".format(len(controls)))
        cd.applyData(controls, applyColor=applyColor)
        logger.info("control shapes -- complete")

    def save_controlShapes(self, path=None):
        import rigamajig2.maya.data.curve_data as curve_data

        if path:
            control_shape_path = path
        elif self.get_rig_data(self.rig_file, CONTROL_SHAPES):
            control_shape_path = self.absPath(self.get_rig_data(self.rig_file, CONTROL_SHAPES))
        else:
            return

        print control_shape_path
        cd = curve_data.CurveData()
        cd.gatherDataIterate(meta.getTagged("control"))
        cd.write(control_shape_path)
        logger.info("control shapes saved to: {}".format(control_shape_path))

    def load_data(self):
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
            if cmpt.get_step()  >= 2:
                logger.warning("component {} is already build. No use creating proxy feedback".format(cmpt))
            else:
                cmpt.showAdvancedProxy()

    def delete_advanced_proxy(self):
        for cmpt in self.cmpts:
            if cmpt.proxy_setup_exists():
                cmpt.deleteAdvancedProxy()

    # RUN SCRIPTS
    def pre_script(self, scripts=[]):
        """
        Run pre scripts. You can add scripts by path, but the main use is through the PRE SCRIPT path
        :param scripts: path to scripts to run
        """
        if self.path:
            scripts_path = self.absPath(PRE_SCRIPT_PATH)
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
            scripts_path = self.absPath(POST_SCRIPT_PATH)
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
            scripts_path = self.absPath(PUB_SCRIPT_PATH)
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
        self.pre_script()
        self.import_model()
        self.import_skeleton()
        self.initalize()
        self.build()
        self.connect()
        self.finalize()
        self.load_controlShapes()
        self.load_data()
        self.post_script()
        if optimize: self.optimize()
        end_time = time.time()
        final_time = end_time - start_time

        print('\nCompleted Rig Build \t -- time elapsed: {0}\n{1}'.format(final_time, '-' * 70))

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
        if not data.has_key("rig_env"):
            rig_env_path = '../'
        else:
            rig_env_path = data["rig_env"]
        self.path = os.path.abspath(os.path.join(self.rig_file, rig_env_path))
        logger.info('Rig Enviornment path: {0}'.format(self.path))

    def get_path(self):
        return self.path

    def get_rig_file(self):
        return self.rig_file

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
        if data.getData().has_key(key):
            return data.getData()[key]
        return None


def build_directory():
    pass
