from skiros2_common.core.world_element import Element
from skiros2_world_model.core.world_model_abstract_interface import WmException
import skiros2_common.core.params as params
from skiros2_skill.core.processors import Serial, ParallelFf, State
import skiros2_common.tools.logger as log
import numpy as np
from copy import deepcopy


class NodePrinter():
    def __init__(self):
        self._prefix = "->"
        self._indend = 0

    def setPrefix(self, prefix):
        self._prefix = prefix + "->"

    def indend(self):
        self._indend += 2

    def unindend(self):
        self._indend -= 2

    def printTree(self, skill, verbose=True):
        s = "-" * self._indend + self._prefix + skill.printState(verbose)
        #s = "-"*self._indend + self._prefix + skill.printInfo(verbose)
        print(s)

    def printParams(self, params):
        to_ret = "\n"
        for _, p in params.getParamMap().items():
            if isinstance(Element(), p.dataType()):
                to_ret += p._key + ": "
                for e in p.getValues():
                    to_ret += e.printState() + "\n"
            else:
                to_ret += p.printState() + "\n"
        return to_ret


class NodeExecutor():
    def __init__(self, wmi, instanciator):
        self._wm = wmi
        self._simulate = False
        self._verbose = False
        self._tracked_params = []
        self._params = params.ParamHandler()
        self._instanciator = instanciator
        self._last_print = ""

    def syncParams(self, params):
        for k, p in params.items():
            vs = p.values
            if p.dataTypeIs(Element):
                for i in reversed(range(0, len(vs))):
                    if vs[i].getIdNumber() >= 0:
                        try:
                            vs[i] = self._wm.get_element(vs[i].id)
                        except WmException:
                            log.info("[syncParams]", "{} was deleted, removing from parameters".format(vs[i].id))
                            vs.pop(i)
                p.values = vs

    def trackParam(self, key, prop="", relation="", print_all=False):
        """
        Prints out every update of the requested param key -> property or relation
        """
        self._tracked_params.append((key, prop, relation, print_all))

    def _printTracked(self, params, prefix):
        to_print = ""
        for key, prop, relation, print_all in self._tracked_params:
            if params.hasParam(key):
                es = params.getParamValues(key)
                for e in es:
                    if isinstance(e, Element):
                        to_print += "{} {} ".format(key, e.printState(print_all))
                        if e.hasProperty(prop):
                            to_print += '. {}: {}. '.format(prop, e.getProperty(prop).value)
                        if relation:
                            to_print += ' {} '.format(e.getRelations(pred=relation))
                    else:
                        to_print += "{} {} ".format(key, e)
            else:
                to_print += key + ' not available. '
        if to_print and to_print != self._last_print:
            self._last_print = to_print
            print(prefix + to_print)

    def setSimulate(self, sim=True):
        self._simulate = sim

#    def specifyParams(self, input_params):
#        self._params.reset(input_params)
#        self._printTracked(self._params, "[specifyParams] ")

    def mergeParams(self, skill):
        self._params.reset(self._params.merge(skill._params))
        self._printTracked(self._params, "[{}:mergeParams] ".format(skill.type))
        #print "Merge: {}".format(self._params.printState())

    def inferUnvalidParams(self, skill):
        #print '{}: {} '.format(skill._label, self.printParams(skill._params))
        unvalid_params = skill.checkPreCond(self._verbose)
        if unvalid_params:
            log.info("[{}] Reset unvalid params {}".format(skill._label, unvalid_params))
            for k in unvalid_params:
                skill._params.setDefault(k)
                p = skill._params.getParam(k)
                if p.dataTypeIs(Element()) and p.getValue().getIdNumber() >= 0:
                    skill._params.specify(k, self._wm.get_element(p.getValue()._id))
            return self._autoParametrizeBB(skill)
        return True

    def _importParentsConditions(self, skill, to_resolve):
        """
        @brief Import additional conditions coming from skill's parents

        The conditions applied on parameters of the skill are imported in the skill description,
        so they are taken into consideration when grounding
        """
        parents = [skill.parent]
        while parents[-1].parent is not None:
            parents.append(parents[-1].parent)
        for parent in parents:
            for pc in parent._pre_conditions:
                if [key for key in to_resolve if key in pc.getKeys()]:
                    dont_add = False
                    for sc in skill._pre_conditions:
                        if sc.isEqual(pc):
                            dont_add = True
                    if dont_add:
                        continue
                    print("{} Adding condition {}".format(skill.type, pc.getDescription()))
                    for key in pc.getKeys():
                        if not skill.params.hasParam(key):
                            skill.params[key] = deepcopy(parent.params[key])
                    skill.addPreCondition(pc)

    def _autoParametrizeBB(self, skill):
        """
        @brief ground undefined parameters with parameters in the Black Board
        """
        to_resolve = [key for key, param in skill._params.getParamMap().items() if param.paramType != params.ParamTypes.Optional and param.dataTypeIs(Element) and param.getValue().getIdNumber() < 0]
        if not to_resolve:
            return True
        log.assertInfo(self._verbose, "[Autoparametrize]", "Resolving {}:{}".format(skill.type, to_resolve))
        #self._importParentsConditions(skill, to_resolve)
        remap = {}
        cp = params.ParamHandler()
        cp.reset(skill._params.getCopy())
        for c in skill._pre_conditions:
            c.setDesiredState(cp)
        for key in to_resolve:
            remap[key] = []
            for k, p in self._params._params.items():
                if p.dataTypeIs(Element()):
                    if p.getValue().isInstance(cp.getParamValue(key), self._wm):
                        remap[key].append(k)
                    else:
                        pass # log.info("Not instance", "{} Model: {} Match: {}".format(key, cp.getParamValue(key).printState(True), p.getValue().printState(True)))
        return self._autoParametrizeWm(skill, to_resolve, cp)

#        l = np.zeros(len(to_resolve), dtype=int)
#        unvalid_params = to_resolve
#        loop = True
#        while loop:
#            loop = False
#            #Set params and check preCond
#            for index, key in enumerate(to_resolve):
#                #print '{}: {}'.format(key, remap[key])
#                if not remap[key]:
#                    return self._autoParametrizeWm(skill, to_resolve, cp)
#                skill._params.specify(key, self._params.getParamValues(remap[key][l[index]]))
#            unvalid_params = skill.checkPreCond()
#            #If there are unvalid params, increment 1 of the counters. Loop breaks when all counters are at last element
#            for key in unvalid_params:
#                if key in to_resolve:
#                    if l[to_resolve.index(key)]<len(remap[key])-1:
#                        l[to_resolve.index(key)] += 1
#                        loop = True
#                        break
#                    else:
#                        l[to_resolve.index(key)] = 0
#        if unvalid_params:
#            return self._autoParametrizeWm(skill, to_resolve, cp)
#        remapped = ''
#        for index, key in enumerate(to_resolve):
#            if key != remap[key][l[index]]:
#                skill.remap(key, remap[key][l[index]])
#                remapped += "[{}={}]".format(key, remap[key][l[index]])
#        log.info("MatchBB","{}: {}".format(skill.type, remapped))
#        return True

    def _autoParametrizeWm(self, skill, to_resolve, cp):
        """
        @brief ground undefined parameters with elements in the world model
        """
        matches = self._wm._resolve_elements2(to_resolve, cp)
        _grounded = ''
        for key, match in matches.items():
            if match.any():
                if isinstance(key, tuple):
                    for i, key2 in enumerate(key):
                        skill.params.specify(key2, match[0][i])
                        _grounded += '[{}={}]'.format(key2, match[0][i].printState())
                else:
                    skill.params.specify(key, match[0])
                    _grounded += '[{}={}]'.format(key, match[0].printState())
            else:
                #print '{}: {}'.format(skill._label, to_resolve)
                log.error("_autoParametrizeWm", "Can t autoparametrize param {}.".format(key))
                return False
        log.info("MatchWm", "{}:{}".format(skill.type, _grounded))
        return True

    def _ground(self, skill):
        skill.reset()
        skill.specifyParams(self._params)
        self.syncParams(skill.params)
        self._printTracked(skill._params, "[{}Params] ".format(skill.label))
        if not self._autoParametrizeBB(skill):
            log.info("[ground]", "Parametrization fail for skill {}".format(skill.printInfo()))
            return False
        # TODO: bring this back as optional
        # if not self.inferUnvalidParams(skill):
        #    log.info("[ground]", "Invalid parameters found for skill {}".format(skill.printInfo()))
        #    return False
        if skill.checkPreCond(self._verbose):
            if self._verbose:
                log.info("[ground]", "Pre-conditions fail for skill {}".format(skill.printInfo()))
            return False
        return True

    def tryOther(self, skill):
        """
        @brief If the skill label is not specified, try other instances
        """
        if skill._label != "":
            return False
        ignore_list = [skill._instance.label]
        while self._instanciator.assign_instance(skill, ignore_list):
            log.info("tryOther", "Trying skill {}".format(skill._instance.label))
            ignore_list.append(skill._instance.label)
            if self._ground(skill):
                return True
        return False

    def _execute(self, skill):
        if self._simulate:
            skill.hold()
            return State.Running
        else:
            return skill.start()

    def init(self, skill):
        """
        @brief Assign an instance to an abstract skill
        """
        if not skill.hasInstance() or skill._instance.hasState(State.Running):
            skill.specifyParams(self._params)
            if not self._instanciator.assign_instance(skill):
                raise Exception("Skill {} is not available.".format(skill.type))

    def execute(self, skill):
        """
        @brief Start a skill
        """
        self.init(skill)
        if not self._ground(skill):
            if not self.tryOther(skill):
                return State.Failure
        skill.wrapper_expand()
        state = self._execute(skill)
        if self._verbose:
            log.info("[VisitorStart]", "{}".format(skill.printState(self._verbose)))
        if state == State.Running:
            self.mergeParams(skill)  # Update params
        return state

    def _postExecute(self, skill):
        if self._simulate:
            return skill.simulate()  # Set post-cond to true
        else:
            return skill.tick()

    def postExecute(self, skill):
        """
        @brief Tick a skill
        """
        skill.specifyParams(self._params)#Re-apply parameters.... Important!
        self.syncParams(skill.params)
        self._printTracked(skill._params, "[{}:SetParams] ".format(skill.type))
        state = self._postExecute(skill)
        # Check postconditions if the node succeeded and fail if they fail
        if state == State.Success and skill.checkPostCond(self._verbose):
            if self._verbose:
                log.info("[PostCondition]", "Post-condition fail for skill {}".format(skill.printInfo()))
            state = State.Failure
            skill._setState(State.Failure)
        if self._verbose:
            log.info("[VisitorExecute]", "{}".format(skill.printState(self._verbose)))
        self.mergeParams(skill)  # Update params
        return state

    def checkHold(self, skill):
        """
        @brief Check hold conditions
        """
        if skill.checkHoldCond(self._verbose):
            if self._verbose:
                log.info("[ground]", "Hold-conditions fail for skill {}".format(skill.printInfo()))
            self.processPreempt(skill)
            skill.checkHoldCond()#This ensure the skill ends printing the failed conditions
            return skill.state
        else:
            return State.Running

    def processPreempt(self, skill):
        """
        @brief Stop a skill execution. Visit recursively all children
        """
        if skill.hasState(State.Running):
            skill.specifyParams(self._params)
            self.syncParams(skill.params)
            if self._verbose:
                log.info("[Preempt]", "{}".format(skill.printState(self._verbose)))
            #Preempt children
            for c in skill._children:
                c.visitPreempt(self)
            #Preempt skill
            skill.preempt()
            self.mergeParams(skill)


class NodeMemorizer:
    def __init__(self, name):
        self._name = name
        self._tree = []
        self._verbose = True

    def snapshot(self):
        return deepcopy(self._tree)

    def _debug(self, msg):
        if self._verbose:
            log.info(self._name, msg)

    def reset_memory(self):
        self._tree = []

    def hasMemory(self):
        return len(self._tree) > 0

    def memorize(self, skill, tag):
        #self._debug("Memorize " + str(tag))
        self._tree.append((skill, tag))

    def hasIndex(self, index):
        return abs(index) < len(self._tree)

    def recall(self, index=None):
        if self._tree:
            if index and abs(index) < len(self._tree):
                return self._tree[index]
            return self._tree[-1]
        return None

    def forget(self):
        if self._tree:
            skill = self._tree.pop()
            #self._debug("Forget " + skill[0].printInfo(False))
            return skill

    def printMemory(self):
        print(self._name + ":")
        for p in self._tree:
            print(p[0].printState() + '-' + p[1])


class TreeBuilder:
    """
    Builds a new tree with root in self._execution_root
    self._execution_branch is used to know which are the immediate parents
    self._forget_branch is used to get back previous parents
    """

    def __init__(self, wmi):
        self._wm = wmi
        # list of parents
        self._execution_branch = []
        # list of previous parents
        self._forget_branch = []
        # list of previous parents
        self._static_branch = []

    def removeExecutionNode(self):
        if self._execution_branch:
            parent = self._execution_branch[-1].getParent()
            if parent:
                parent.popChild()
            return self._execution_branch.pop()

    def restoreParentNode(self):
        if self._forget_branch:
            self._execution_branch.append(self._forget_branch.pop())

    def popParentNode(self):
        self._forget_branch.append(self._execution_branch.pop())

    def makeParentStatic(self, parent_name, static=False):
        if self._execution_branch[-1]._label != parent_name and self._forget_branch[-1]._label != parent_name and static:
            log.error("makeParentStatic", "Exe: {} Forgot: {} Looking for: {}".format(self._execution_branch[-1]._label, self._forget_branch[-1]._label, parent_name))
            return

        if static:
            if self._execution_branch[-1]._label == parent_name:
                self._static_branch.append((self._execution_branch.pop(), True))
                log.info("makeParentStatic", "Storing: {} {}".format(parent_name, True))
            else:
                self._static_branch.append((self._forget_branch.pop(), False))
                log.info("makeParentStatic", "Storing: {} {}".format(parent_name, False))
        else:
            if self._static_branch:
                if parent_name == self._static_branch[-1][0]._label:
                    p, tag = self._static_branch.pop()
                    log.info("makeParentStatic", "Restoring: {} {}".format(parent_name, tag))
                    if tag:
                        self._execution_branch.append(p)
                    else:
                        self._forget_branch.append(p)

    def addExecutionNode(self, skill):
        p = skill.getLightCopy()
        p._children = []
        parent = self.getExecutionParent()
        self._execution_branch.append(p)
        if parent:
            parent.addChild(p)

    def getExecutionParent(self):
        if self._execution_branch:
            return self._execution_branch[-1]

    def getPrevious(self):
        if not self._forget_branch:
            return None
        else:
            return self._forget_branch[-1]

    def previousParentIsSameWithWrongProcessor(self, processor):
        parent = self.getExecutionParent()
        previous = self.getPrevious()
        if previous:
            if previous.getParent() == parent:
                if not isinstance(parent._children_processor, processor):
                    return True
        return False

    def getExecutionRoot(self):
        return self._execution_root

    def freezeExecutionTree(self):
        self._forget_branch = []


class NodeReversibleSimulator(NodeExecutor, TreeBuilder):
    def __init__(self):
        self._simulate = True
        self.static = NodeMemorizer('Static')
        self.forward = NodeMemorizer('Forward')
        self.back = NodeMemorizer('Backward')
        self._execution_branch = []
        self._forget_branch = []
        self._static_branch = []
        self._bound = {}

    def addInExecutionTree(self, skill, processor=Serial):
        if not self._execution_branch:
            self.addExecutionNode(skill)
            self._execution_root = self._execution_branch[0]
            return
        if processor is not None and self.previousParentIsSameWithWrongProcessor(processor):
            # Else wrap the previous and the current into a node with the right processor
            print('{} wants {}, parent is {}'.format(skill._label, processor().printType(), self.getExecutionParent()._label))
            self.undoPrevious()
            pp = skill(processor().printType(), processor(), self._wm)
            self.execute(pp)
            self.redoPrevious()
            self.parametrize(skill)
            self.addExecutionNode(skill)
            self._bound[id(skill)] = pp
        else:
            self.addExecutionNode(skill)

    def erase(self):
        self.undo()
        self.back.forget()

    def makeStaticPrevious(self):
        skill = self.forward.recall()[0]._label
        log.warn("makeStaticPrevious", "skill {}".format(skill))
        if not isinstance(self.getExecutionParent()._children_processor, ParallelFf):
            log.warn("makeStaticPrevious", "skill {} has a serial parent. Reverting till {}".format(skill, self.getExecutionParent()._label))
            skill = self.getExecutionParent()._label
        self.makeStatic(True)
        while skill != self.forward.recall()[0]._label:
            print(self.forward.recall()[0]._label)
            self.makeStatic(True)
        self.makeStatic(True)

    def makeStaticAll(self, static=False):
        if static:
            while self.forward.hasMemory():
                self.makeStatic(static)
        else:
            while self.static.hasMemory():
                self.makeStatic(static)

    def makeStatic(self, static=False):
        if static:
            self.makeParentStatic(self.forward.recall()[0]._label, static)
            self.static.memorize(*self.forward.forget())
        else:
            self.makeParentStatic(self.static.recall()[0]._label, static)
            self.forward.memorize(*self.static.forget())

    def undoPrevious(self):
        skill = self.forward.recall()[0]
        self.undo()
        while skill != self.forward.recall()[0]:
            self.undo()
        self.undo()

    def redoPrevious(self):
        skill = self.back.recall()[0]
        self.redo()
        while skill != self.back.recall()[0]:
            self.redo()
        self.redo()

    def forget(self):
        # TODO: possible mess with parentNode in execution tree...
        skill, tag = self.forward.forget()
        if self._verbose:
            log.info("Undo {} {}.".format(skill._label, tag))
        if tag == 'execute':
            self.revert(skill)
        elif tag == 'postExecute':
            self.postRevert(skill)
        return (skill, tag)

    def undo(self):
        if not self.forward.hasMemory():
            return False
        self.back.memorize(*self.forget())
        return True

    def undoAll(self):
        while self.forward._tree:
            if not self.undo():
                return False
        return True

    def redo(self, processor=None):
        if not self.back.hasMemory():
            return False
        skill, tag = self.back.recall()
        if tag == 'execute':
            if self.execute(skill, processor=processor):
                self.back.forget()
                return True
            else:
                return False
        elif tag == 'postExecute':
            if self.postExecute(skill):
                self.back.forget()
                return True
            else:
                return False

    def redoAll(self):
        while self.back.hasMemory():
            if not self.redo():
                return False
        return True

    def parametrize(self, skill):
        skill.specifyParams(self._params)
        if not self._ground(skill):
            if not self.tryOther(skill):
                return False
        return True

    def initAndParametrize(self, skill):
        self.init(skill)
        if not self.parametrize(skill):
            return False
        return True

    def execute(self, skill, processor=Serial):
        if not self.initAndParametrize(skill):
            return False
        if self._verbose:
            log.info("Execute {}.".format(skill._label))
        self.addInExecutionTree(skill, processor)
        skill.hold()
        self.mergeParams(skill)  # Update params
        self.forward.memorize(skill, "execute")
        return True

    def revert(self, skill):
        skill.revertHold()
        self.specifyParams(skill.revertInput())
        self.removeExecutionNode()
        return True

    def postExecute(self, skill, remember=True):
        skill.specifyParams(self._params)  # Re-apply parameters, after processing the sub-tree.... Important, thay have been modified by the subtree!
        if self._verbose:
            log.info("postExecute {}.".format(skill._label))
        if not self._postExecute(skill):
            return False
        self.mergeParams(skill)  # Update params
        self.forward.memorize(skill, "postExecute")
        if skill._label != self.getExecutionParent()._label:
            log.error("postExecution", "{} trying to close before the parent {}".format(skill._label, self.getExecutionParent()._label))
            raise KeyError()
        self.popParentNode()
        if id(skill) in self._bound:
            self.postExecute(self._bound.pop(id(skill)))
        return True

    def postRevert(self, skill):
        if not skill.revertSimulation():
            log.error("undo", "Can't revert {}".format(skill.printState()))
            return False
        self.specifyParams(skill.revertInput())
        self.restoreParentNode()
        #print 'miei ' + self.printParams(skill._params)
        return True
