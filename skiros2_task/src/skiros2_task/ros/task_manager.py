#################################################################################
# Software License Agreement (BSD License)
#
# Copyright (c) 2016, Francesco Rovida
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the
#   names of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#################################################################################

import rospy
import rospkg
import skiros2_msgs.srv as srvs
import skiros2_common.core.params as skirosp
import skiros2_common.core.conditions as cond
import skiros2_common.tools.time_keeper as tk
import skiros2_common.tools.logger as log
import skiros2_world_model.core.local_world_model as wm
import skiros2_world_model.ros.world_model_interface as wmi
import skiros2_skill.ros.skill_layer_interface as sli
import skiros2_task.core.pddl_interface as pddl
from skiros2_skill.ros.utils import SkillHolder

class TaskManagerNode(object):
    """
    This class manage the robot task.
    A list of goals can be modified by external agent (e.g. users) with the service 'set_goals'
    The task manager plans a sequence of skills to reach the goals. 
    In case of execution failure replans until all goals are reached.
    """
    def __init__(self):
        #Init ROS interfaces
        self._author_name = "task_manager"
        rospy.init_node("task_manager", anonymous=False)
        self._wmi = wmi.WorldModelInterface()
        self._sli = sli.SkillLayerInterface(self._wmi)
        self._goals = []
        self._task = []
        self._skills = {}
        self._abstract_objects = []
        #Init world model
        self._local_wm = wm.WorldModel(self._wmi)
        self._local_wm._verbose = False
        self._local_wm.sync()
        rospy.sleep(0.5)
        rospack = rospkg.RosPack()
        self._pddl_interface = pddl.PddlInterface(rospack.get_path("skiros2_task"))
        self._goal_modify = rospy.Service('~set_goals', srvs.TmSetGoals, self._setGoalsCb)
        self._time_keeper = tk.TimeKeeper()
        
    def getSkills(self):
        """
        Return the updated list of skills available in the system
        """
        if self._sli.hasChanges():
            self._skills.clear()
            for ak, e in self._sli._agents.iteritems():
                for sk, s in e._skill_list.iteritems():
                    s.manager = ak
                    self._skills[sk] = s     
        return self._skills
        
    def _setGoalsCb(self, msg):
        self._pddl_interface.clear()
        with self._time_keeper:
            self.initDomain()
        log.info(self.__class__.__name__, "Init domain in {}  secs".format(self._time_keeper.getLast()))
        with self._time_keeper:
            self.setGoal(msg.goals)
            self.initProblem()
        log.info(self.__class__.__name__, "Init problem in {} secs".format(self._time_keeper.getLast()))
        with self._time_keeper:
            plan = self.plan()
        if plan:
            log.info(self.__class__.__name__, "Planned sequence: \n{}in {} secs".format(plan, self._time_keeper.getLast()))
            self.buildTask(plan)
            self.execute()
        else:
            log.error(self.__class__.__name__, "No plan found in {} secs".format(self._time_keeper.getLast()))

    
    def buildTask(self, plan):
        """
        Decompose the plan (a string) into parameterized skills and append to self._task
        """
        self._task = list()
        skills = plan.splitlines()
        for s in skills:
            s = s[s.find('(')+1: s.find(')')]
            tokens = s.split(' ')
            skill = self.getSkills()[tokens[0]]
            i= 1
            for _, t in  skill.ph._params.items():
                t.setValue(self.getElement(tokens[i]))
                i += 1
            self._task.append(skill)            
        
    def initDomain(self):
        skills = self._wmi.resolveElements(wmi.Element(":Skill"))
        for skill in skills:
            params = {}
            preconds = []
            postconds = []
            for p in skill.getRelations(pred="skiros:hasParam"):
                e = self._wmi.getElement(p['dst'])
                params[e._label] = e.getProperty("skiros:DataType").value
            for p in skill.getRelations(pred="skiros:hasPreCondition"):
                e = self._wmi.getElement(p['dst'])
                if e._type.find("ConditionRelation")!=-1 or e._type == "skiros:ConditionProperty":
                    preconds.append(pddl.Predicate(e, params, e._type.find("Abs")!=-1))
            for p in skill.getRelations(pred="skiros:hasPostCondition"):
                e = self._wmi.getElement(p['dst'])
                if e._type.find("ConditionRelation")!=-1 or e._type == "skiros:ConditionProperty":
                    postconds.append(pddl.Predicate(e, params, e._type.find("Abs")!=-1))
            self._pddl_interface.addAction(pddl.Action(skill, params, preconds, postconds))
        #self._pddl_interface.printDomain(False)
        
    def getElement(self, uid):
        if uid.find("-")>0:
            return self._elements[uid[uid.find("-")+1:]]
        return self._elements[uid]
        
    def initProblem(self):
        objects = {}
        elements = {}
        self._elements = {}
        #Find objects
        for objType in self._pddl_interface._types._types["thing"]:   
            temp = self._wmi.resolveElements(wmi.Element(objType))
            elements[objType] = temp
            if len(temp)>0:
                objects[objType] = []
            for e in temp:
                objects[objType].append(e._id)
                self._elements[e._id[e._id.find("-")+1:]] = e
        for e in self._abstract_objects:
            ctype = self._wmi.getSuperClass(e._type)
            if not objects.has_key(e._type):
                 objects[ctype] = []
                 elements[ctype] = []
            e._id = e._label
            objects[ctype].append(e._label)
            elements[ctype].append(e)
            self._elements[e._id] = e
        self._pddl_interface.setObjects(objects)        
        #Evaluate inital state
        init_state = []
        for supertype, types in self._pddl_interface._types._types.iteritems():   
            elements[supertype] = []
            for t in types:
                elements[supertype] += elements[t]
        
        params = skirosp.ParamHandler()
        params.addParam("x", wm.Element(), skirosp.ParamTypes.World)
        params.addParam("y", wm.Element(), skirosp.ParamTypes.World)
        for p in self._pddl_interface._predicates:
            if len(p.params)==1:
                c = cond.ConditionProperty("", p.name, "x", p.operator, p.value, True)
                xtype = p.params[0]["valueType"]
                for xe in elements[xtype]:
                    params.specify("x", xe)
                    if c.evaluate(params, self._wmi):
                        init_state.append(pddl.GroundPredicate(p.name, [xe._id], p.operator, p.value))
            else:
                if p.abstracts:
                    c = cond.AbsConditionRelation("", p.name, "x", "y", True)
                else:
                    c = cond.ConditionRelation("", p.name, "x", "y", True)
                xtype = p.params[0]["valueType"]
                ytype = p.params[1]["valueType"]
                for xe in elements[xtype]:
                    params.specify("x", xe)
                    for ye in elements[ytype]:
                        params.specify("y", ye)
                        if c.evaluate(params, self._wmi):
                            init_state.append(pddl.GroundPredicate(p.name, [xe._id, ye._id]))
        for p in self._pddl_interface._functions:
            c = cond.ConditionProperty("", p.name, "x", p.operator, p.value, True)
            xtype = p.params[0]["valueType"]
            for xe in elements[xtype]:
                params.specify("x", xe)
                if c.evaluate(params, self._wmi):
                    init_state.append(pddl.GroundPredicate(p.name, [xe._id], p.operator, p.value))
        self._pddl_interface.setInitState(init_state)
                
    def setGoal(self, goal):
        for g in goal:
            g = g[1:-1]
            tokens = g.split(" ")            
            self._pddl_interface.addGoal(pddl.GroundPredicate(tokens[0], [tokens[1], tokens[2]]))
            if tokens[1].find("-")==-1: #If isAbstractObject
                self._abstract_objects.append(self._wmi.getTemplateElement(tokens[1]))
            if tokens[2].find("-")==-1: #If isAbstractObject
                self._abstract_objects.append(self._wmi.getTemplateElement(tokens[2]))
                
        
    def plan(self):
        return self._pddl_interface.invokePlanner()        
    
    def execute(self):
        self._sli.getAgent(self._task[0].manager).execute(self._task, self._author_name) 
        
    def run(self):
        rospy.spin()                    


if __name__ == '__main__':
    node = TaskManagerNode()
    node.run()