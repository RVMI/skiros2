import rospy
import rospkg

from skiros2_msgs.msg import RobotDescription
from std_msgs.msg import Empty

import skiros2_msgs.srv as srvs
import skiros2_msgs.msg as msgs
import actionlib
import skiros2_common.core.params as skirosp
import skiros2_common.core.conditions as cond

from skiros2_common.tools.decorators import PrettyObject
import skiros2_common.tools.logger as log
import skiros2_common.tools.time_keeper as tk

from copy import deepcopy
import skiros2_world_model.core.local_world_model as wm
import skiros2_world_model.ros.world_model_interface as wmi
import skiros2_skill.ros.skill_layer_interface as sli
import skiros2_task.core.pddl_interface as pddl
from skiros2_skill.ros.utils import SkillHolder


class TaskManagerNode(PrettyObject):
    """
    This class manage the robot task.
    A list of goals can be modified by external agent (e.g. users) with the service 'set_goals'
    The task manager plans a sequence of skills to reach the goals.
    In case of execution failure replans until all goals are reached.
    """


    def __init__(self):
        """Initialization of the task manager.

        Initialize task manager as a ros node.
        Establish access to the global and local world model, skill manager and the task planner.
        """
        rospy.init_node("task_manager", anonymous=False)
        self._author_name = rospy.get_name()

        self._goals = []
        self._task = []
        self._skills = {}
        self._abstract_objects = []

        self._wmi = wmi.WorldModelInterface()
        self._sli = sli.SkillLayerInterface(self._wmi, self._onMonitorMsg)
        self._pddl_interface = pddl.PddlInterface(rospkg.RosPack().get_path("skiros2_task"))

        self._verbose=rospy.get_param('~verbose', True)
        self._assign_task_action = actionlib.SimpleActionServer('~assign_task', msgs.AssignTaskAction, execute_cb = self._assign_task_cb, auto_start = False)
        self._assign_task_action.start()

        self._sub_robot_discovery = rospy.Subscriber('/skiros/robot_discovery', Empty, self._onRobotDiscovery)
        self._pub_robot_description = rospy.Publisher('/skiros/robot_description', RobotDescription, queue_size=10)
        self._is_ready = False


    @property
    def skills(self):
        """Get available skills.

        Return the updated list of skills available in the system

        Returns:
            dict: {Skill name : instance? }
        """
        if self._sli.hasChanges():
            self._skills.clear()
            for ak, e in self._sli._agents.iteritems():
                for sk, s in e._skill_list.iteritems():
                    s.manager = ak
                    self._skills[sk] = s
        return self._skills


    def _onMonitorMsg(self, msg):
        if self._assign_task_action.is_active() and self._is_ready:
            if msg.type=="Task":
                if msg.state==1:
                    self._done = True
                    self._result = msgs.AssignTaskResult(msg.state, msg.progress_message)
                    self._assign_task_action.set_succeeded(self._result)
                else:
                    if self._replan_count>20:
                        self._assign_task_action.set_aborted()
                    else:
                        log.info("Task execution failed. Replanning.")
                        self._replan_count += 1
                        self.plan_and_execute()
            else:
                self._feedback = msgs.AssignTaskFeedback(msg.state, msg.progress_message)
                self._assign_task_action.publish_feedback(self._feedback)

    def _onRobotDiscovery(self, msg):
        """Callback for robot discovery messages.

        Answers robot discovery messages by publishing robot name and its skills.

        Args:
            msg (std_msgs.msg.Empty): Empty ping message
        """
        log.debug(self.class_name, "Received robot discovery message")
        self._pub_robot_description.publish(self._author_name, self.skills.keys())

    def _assign_task_cb(self, msg):
        """Callback for setting new goals.

        Executed whenever we receive a service call to set a new goal.

        Args:
            msg (skiros2_msgs.srv.TmSetGoals): Service message containing the goals
        """
        self._done = False
        self._is_ready = False
        self._current_goals = msg.goals
        self._replan_count = 0
        rate = rospy.Rate(10.0)
        if self.plan_and_execute() is None:
            return
        if not self._task:
            self._result = msgs.AssignTaskResult(1, "No skills to execute.")
            self._assign_task_action.set_succeeded(self._result)
            return
        self._is_ready = True
        while (not self._assign_task_action.is_preempt_requested()) and (not rospy.is_shutdown()) and not self._done:
            rate.sleep()
        if not self._done:
            self.preempt()
            self._assign_task_action.set_preempted()

    def plan_and_execute(self):
        with tk.Timer(self.class_name) as timer:
            self._pddl_interface.clear()
            self.initDomain()
            timer.toc("Init domain")
            self.setGoal(self._current_goals)
            self.initProblem()
            timer.toc("Init problem")
            plan = self.plan()
            timer.toc("Planning sequence")
        if plan is not None:
            if self._verbose:
                log.info("[Plan]", plan)
            self._feedback = msgs.AssignTaskFeedback(0, plan)
            self._assign_task_action.publish_feedback(self._feedback)
            self.buildTask(plan)
            self.execute()
            return plan
        else:
            log.warn(self.class_name, "Planning failed for goals: {}".format(self._current_goals))
            self._assign_task_action.set_aborted()
            return None

    def buildTask(self, plan):
        """
        Decompose the plan (a string) into parameterized skills and append to self._task
        """
        self._task = list()
        skills = plan.splitlines()
        for s in skills:
            s = s[s.find('(')+1: s.find(')')]
            tokens = s.split(' ')
            skill = deepcopy(self.skills[tokens.pop(0)])
            planned_map = self._pddl_interface.getActionParamMap(skill.name, tokens)
#            print "{}".format(planned_map)
            for k,v in planned_map.iteritems():
                skill.ph[k].setValue(self.getElement(v))
            self._task.append(skill)


    def initDomain(self):
        skills = self._wmi.resolveElements(wmi.Element(":Skill"))
        for skill in skills:
            params = {}
            preconds = []
            postconds = []
            #Note: Only skills with pre AND post conditions are considered for planning
            for p in skill.getRelations(pred="skiros:hasParam"):
                e = self._wmi.getElement(p['dst'])
                params[e._label] = e.getProperty("skiros:DataType").value
            for p in skill.getRelations(pred="skiros:hasPreCondition"):
                e = self._wmi.getElement(p['dst'])
                if e._type.find("ConditionRelation")!=-1 or e._type == "skiros:ConditionProperty" or e._type == "skiros:ConditionHasProperty":
                    preconds.append(pddl.Predicate(e, params, e._type.find("Abs")!=-1))
            for p in skill.getRelations(pred="skiros:hasPostCondition"):
                e = self._wmi.getElement(p['dst'])
                if e._type.find("ConditionRelation")!=-1 or e._type == "skiros:ConditionProperty" or e._type == "skiros:ConditionHasProperty":
                    postconds.append(pddl.Predicate(e, params, e._type.find("Abs")!=-1))
            self._pddl_interface.addAction(pddl.Action(skill, params, preconds, postconds))
        if self._verbose:
            log.info("[Domain]", self._pddl_interface.printDomain(False))


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
            if not objects.has_key(ctype):
                 objects[ctype] = []
                 elements[ctype] = []
            e._id = e._label
            if not e._label in objects[ctype]:#Avoids duplicates
                objects[ctype].append(e._label)
                elements[ctype].append(e)
                self._elements[e._id] = e
        self._pddl_interface.setObjects(objects)
        #Evaluate inital state
        for supertype, types in self._pddl_interface._types._types.iteritems():
            elements[supertype] = []
            for t in types:
                elements[supertype] += elements[t]

        params = skirosp.ParamHandler()
        params.addParam("x", wm.Element(), skirosp.ParamTypes.Required)
        params.addParam("y", wm.Element(), skirosp.ParamTypes.Required)
        for p in self._pddl_interface._predicates:
            if len(p.params)==1:
                if p.value!=None:
                    c = cond.ConditionProperty("", p.name, "x", p.operator, p.value, True)
                else:
                    c = cond.ConditionHasProperty("", p.name, "x", True)
                xtype = p.params[0]["valueType"]
                for xe in elements[xtype]:
                    params.specify("x", xe)
                    if c.evaluate(params, self._wmi):
                        self._pddl_interface.addInitState(pddl.GroundPredicate(p.name, [xe._id], p.operator, p.value))
            else:
                if p.abstracts:
                    c = cond.AbstractConditionRelation("", p.name, "x", "y", True)
                else:
                    c = cond.ConditionRelation("", p.name, "x", "y", True)
                xtype = p.params[0]["valueType"]
                ytype = p.params[1]["valueType"]
                for xe in elements[xtype]:
                    params.specify("x", xe)
                    for ye in elements[ytype]:
                        params.specify("y", ye)
                        if c.evaluate(params, self._wmi):
                            self._pddl_interface.addInitState(pddl.GroundPredicate(p.name, [xe._id, ye._id]))
        for p in self._pddl_interface._functions:
            c = cond.ConditionProperty("", p.name, "x", p.operator, p.value, True)
            xtype = p.params[0]["valueType"]
            for xe in elements[xtype]:
                params.specify("x", xe)
                if c.evaluate(params, self._wmi):
                    self._pddl_interface.addInitState(pddl.GroundPredicate(p.name, [xe._id], p.operator, p.value))
        if self._verbose:
            log.info("[Problem]", self._pddl_interface.printProblem(False))

    def setGoal(self, goal):
        try:
            for g in goal:
                if g.find("forall")!=-1:
                    self._pddl_interface.addGoal(pddl.ForallPredicate(g))
                else:
                    g = g[1:-1]
                    tokens = g.split(" ")
                    if len(tokens)==3:
                        self._pddl_interface.addGoal(pddl.GroundPredicate(tokens[0], [tokens[1], tokens[2]]))
                        if tokens[1].find("-")==-1: #If isAbstractObject
                            self._abstract_objects.append(self._wmi.getTemplateElement(tokens[1]))
                        if tokens[2].find("-")==-1: #If isAbstractObject
                            self._abstract_objects.append(self._wmi.getTemplateElement(tokens[2]))
                    else:
                        self._pddl_interface.addGoal(pddl.GroundPredicate(tokens[0], [tokens[1]]))
                        if tokens[1].find("-")==-1: #If isAbstractObject
                            self._abstract_objects.append(self._wmi.getTemplateElement(tokens[1]))
        except:
            raise Exception("Error while parsing input goal: {}".format(goal))


    def plan(self):
        return self._pddl_interface.invokePlanner()

    def execute(self):
        if self._task:
            self._curr_task = (self._task[0].manager, self._sli.getAgent(self._task[0].manager).execute(self._task, self._author_name))

    def preempt(self):
        self._sli.getAgent(self._curr_task[0]).preempt(self._curr_task[1], self._author_name)

    def run(self):
        rospy.spin()



if __name__ == '__main__':
    node = TaskManagerNode()
    node.run()
