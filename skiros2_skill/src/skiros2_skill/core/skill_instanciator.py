from collections import defaultdict
import skiros2_common.tools.logger as log
from skiros2_common.core.abstract_skill import State
from copy import deepcopy
from skiros2_skill.core.skill import SkillDescription
from skiros2_common.tools.plugin_loader import PluginLoader

class SkillInstanciator:
    def __init__(self, wmi):
        self._plugin_manager = PluginLoader()
        self._available_descriptions = {}
        self._available_instances = defaultdict(list)
        self._wm = wmi

    def load_library(self, package, verbose):
        """
        @brief Load definitions from a package
        """
        self._plugin_manager.load(package, SkillDescription)
        if verbose:
            self._plugin_manager.list()

    def get_description(self, skill_type):
        if not skill_type in self._available_descriptions:
            type_without_prefix = skill_type if not ":" in skill_type else skill_type[skill_type.find(":")+1:]
            self._available_descriptions[skill_type] = self._plugin_manager.getPluginByName(type_without_prefix)()
        return self._available_descriptions[skill_type]

    def add_instance(self, skill_name):
        """
        @brief Add a new instance of a skill
        """
        skill = self._plugin_manager.getPluginByName(skill_name)()
        skill.init(self._wm, self)
        self._available_instances[skill.type].append(skill)
        return skill

    def expand_all(self):
        for _, ps in self._available_instances.items():
            for p in ps:
                p.expand(p)

    def assign_description(self, skill):
        """
        @brief Assign a description to an abstract skill.
        """
        skill.init(self._wm)
        skill.setDescription(deepcopy(self.get_description(skill.type)))
        #log.error("assignDescription", "No instances of type {} found. Debug: {}".format(skill.type, self._available_descriptions.keys()))

    def get_instances(self, ptype):
        return self._available_instances[ptype]

    def duplicate_instance(self, instance):
        """
        @brief Add a new instance of the skill in the available list
        """
        new = instance.__class__()
        new.init(self._wm, self)
        self._available_instances[new.type].append(new)
        return new

    def assign_instance(self, skill, ignore_list=list()):
        """
        @brief Assign an instance to an abstract skill.

        If an instance with same label is not found, assign the last instance of the type.
        """
        to_set = None
        for p in self._available_instances[skill.type]:
            if (p.label == skill._label or skill._label == "") and p.label not in ignore_list:
                to_set = p
                if not p.hasState(State.Running):  # The skill is available, just go forward
                    break
        if to_set is not None:
            if to_set.hasState(State.Running):  # The skill instance is busy, create a new one
                to_set = self.duplicate_instance(to_set)
            skill.setInstance(to_set)
        elif skill._label != "" and not ignore_list:  # No instance exist, try to load it
            skill.setInstance(self.add_instance(skill._label))
        else:
            log.error("assign_instance", "No instance of type {} found.".format(skill.type))
            return False
        return True

    def print_state(self, verbose=True, filter_type=""):
        s = 'Descriptions:\n'
        for t, p in self._available_descriptions.items():
            if p.type == filter_type or filter_type == "":
                s += p.printInfo(verbose)
                s += '\n'
        s += '\nInstances:\n'
        for k, l in self._available_instances.items():
            for p in l:
                if p.type == filter_type or filter_type == "":
                    s += p.printInfo(verbose)
                    s += '\n'
        return s
