import rospy
import rospkg
from os import walk
import skiros2_common.tools.logger as log
import skiros2_common.ros.utils as utils
import skiros2_msgs.msg as msgs
import skiros2_msgs.srv as srvs
from skiros2_common.tools.plugin_loader import PluginLoader
from skiros2_common.core.discrete_reasoner import DiscreteReasoner
from skiros2_world_model.ros.ontology_server import OntologyServer
from skiros2_world_model.core.world_model import WorldModel, IndividualsDataset, Element
import uuid
from time import sleep

class WorldModelServer(OntologyServer):
    def __init__(self, anonymous=False):
        self._monitor = None
        rospy.init_node("wm", anonymous=anonymous)
        rospy.on_shutdown(self._wait_clients_disconnection)#TODO: make this work
        self._verbose = rospy.get_param('~verbose', False)
        self.contexts = dict()
        self._ontology = WorldModel(self._verbose, 'scene', self._wm_change_cb)
        self.contexts['scene'] = self._ontology
        self._plug_loader = PluginLoader()
        self._init_wm()
        self._load_reasoners()
        #================Snapshot======================
        self._curr_snapshot = uuid.uuid4() # random UUID
        #self._snapshots_log = []
        #================ROS======================
        self._set_relation = rospy.Service('~scene/set_relation', srvs.WmSetRelation, self._wm_set_rel_cb)
        self._query_relations = rospy.Service('~scene/query_relations', srvs.WmQueryRelations, self._wm_query_rel_cb)
        self._get = rospy.Service('~get', srvs.WmGet, self._wm_get_cb)
        self._modify = rospy.Service('~modify', srvs.WmModify, self._wm_modify_cb)
        self._monitor = rospy.Publisher("~monitor", msgs.WmMonitor, queue_size=20, latch=True)
        self._load_and_save = rospy.Service('~load_and_save', srvs.WoLoadAndSave, self._load_and_save_cb)
        self.init_ontology_services()

    def _init_wm(self):
        rospack = rospkg.RosPack()
        self._skiros_dir = rospack.get_path('skiros2')+'/owl'
        self._workspace = rospy.get_param('~workspace_dir', self._skiros_dir)
        for (dirpath, dirnames, filenames) in walk(self._skiros_dir):
            for name in filenames:
                if name.find('.owl')>=0:
                    self._ontology.load(dirpath+'/'+name)
        for (dirpath, dirnames, filenames) in walk(self._workspace):
            for name in filenames:
                if name.find('.owl')>=0:
                    self._ontology.load(dirpath+'/'+name)
        if not self._workspace:
            self._workspace = self._skiros_dir
        self._ontology.set_workspace(self._workspace)
        log.info("[{}]".format(self.__class__.__name__), "Workspace folder: {}".format(self._workspace))
        self._ontology.set_default_prefix('skiros', 'http://rvmi.aau.dk/ontologies/skiros.owl#')
        for prefix, uri1 in self._ontology._ontology.namespace_manager.store.namespaces():
            if prefix.find("default")>-1:
                self._ontology._bind(prefix, "")
        self._ontology._bind("", "")
        init_scene = rospy.get_param('~init_scene', "")
        if init_scene!="":
            self._ontology.load_context(init_scene)
        else:
            self._ontology.reset()

    def _load_reasoners(self):
        """
        Load reasoner plugins
        """
        #Load plugins descriptions
        for package in rospy.get_param('~reasoners_pkgs', []):
            self._plug_loader.load(package, DiscreteReasoner)
        #TODO: load reasoners in context
        for p in self._plug_loader:
            self._ontology.load_reasoner(p)

    def _wait_clients_disconnection(self):
        if self._monitor:
            while self._monitor.get_num_connections()>0:
                sleep(0.1)

    def _wm_change_cb(self, author, action, element=None, relation=None):
        if element is not None:
            self._publish_change(author, action, [utils.element2msg(element)])
        else:
            self._publish_change(author, action, relation=utils.relation2msg(relation))

    def _publish_change(self, author, action, elements=None, relation=None, context_id='scene'):
        if context_id=='scene':
            msg =  msgs.WmMonitor()
            msg.prev_snapshot_id = self._curr_snapshot.hex
            self._curr_snapshot = uuid.uuid4() # random UUID
            msg.snapshot_id = self._curr_snapshot.hex
            msg.stamp = rospy.Time.now()
            msg.author = author
            msg.action = action
            if elements:
                msg.elements = elements
            if relation:
                msg.relation.append(relation)
            self._monitor.publish(msg)

    def _get_context(self, context_id):
        if not self.contexts.has_key(context_id):
            log.info("[get_context]", "Creating context: {}.".format(context_id))
            self.contexts[context_id] = IndividualsDataset(self._verbose, context_id, self._ontology._ontology)
            self.contexts[context_id].set_default_prefix('skiros', 'http://rvmi.aau.dk/ontologies/skiros.owl#')
        return self.contexts[context_id]

    def _load_and_save_cb(self, msg):
        with self._times:
            if msg.action==msg.SAVE:
                self._get_context(msg.context).save_context(msg.filename)
            elif msg.action==msg.LOAD:
                self._get_context(msg.context).load_context(msg.filename)
                self._publish_change("", "reset", elements=[], context_id=msg.context)
        if self._verbose:
            log.info("[wmLoadAndSave]", "{} {} to file {}. Time: {:0.3f} secs".format(msg.action, msg.context, msg.filename, self._times.getLast()))
        return srvs.WoLoadAndSaveResponse(True)

    def _wm_query_rel_cb(self, msg):
        #TODO: get rid of this. Replace implementation with a standard SPARQL query
        to_ret = srvs.WmQueryRelationsResponse()
        with self._times:
            to_ret.matches = [utils.relation2msg(x) for x in self._ontology.get_relations(utils.msg2relation(msg.relation))]
        if self._verbose:
            log.info("[wmQueryRelation]", "Query: {} Answer: {}. Time: {:0.3f} secs".format(msg.relation, to_ret.matches, self._times.getLast()))
        return to_ret

    def _wm_get_cb(self, msg):
        with self._times:
            to_ret = srvs.WmGetResponse()
            if msg.action == msg.GET:
                to_ret.elements.append(utils.element2msg(self._get_context(msg.context).get_element(msg.element.id)))
            elif msg.action == msg.GET_TEMPLATE:
                to_ret.elements.append(utils.element2msg(self._get_context(msg.context).get_template_individual(msg.element.label)))
            elif msg.action == msg.GET_RECURSIVE:
                for _, e in self._get_context(msg.context).get_recursive(msg.element.id, msg.relation_filter, msg.type_filter).iteritems():
                    to_ret.elements.append(utils.element2msg(e))
            elif msg.action == msg.RESOLVE:
                for e in self._get_context(msg.context).resolve_elements(utils.msg2element(msg.element)):
                    to_ret.elements.append(utils.element2msg(e))
        output = ""
        einput = utils.msg2element(msg.element)
        for e in to_ret.elements:
            output += "{} ".format(e.id)
        if self._verbose:
            log.info("[WmGet]", "Done {} [{}]. Answer: {}. Time: {:0.3f} secs".format(msg.action, einput, output, self._times.getLast()))
        to_ret.snapshot_id = self._curr_snapshot.hex
        return to_ret

    def _wm_set_rel_cb(self, msg):
        with self._times:
            if msg.value:
                temp = "+"
                self._ontology.add_relation(utils.msg2relation(msg.relation), msg.author, is_relation=True)
                self._publish_change(msg.author, "add", relation=msg.relation)
            else:
                temp = "-"
                self._ontology.remove_relation(utils.msg2relation(msg.relation), msg.author, is_relation=True)
                self._publish_change(msg.author, "remove", relation=msg.relation)
        if self._verbose:
            log.info("[wmSetRelCb]", "[{}] {} Time: {:0.3f} secs".format(temp, msg.relation, self._times.getLast()))
        return srvs.WmSetRelationResponse(True)

    def _wm_modify_cb(self, msg):
        to_ret = srvs.WmModifyResponse()
        with self._times:
            if msg.action == msg.ADD:
                for e in msg.elements:
                    updated_e = self._get_context(msg.context).add_element(utils.msg2element(e), msg.author)
                    to_ret.elements.append(utils.element2msg(updated_e))
                self._publish_change(msg.author, "add", elements=to_ret.elements, context_id=msg.context)
            elif msg.action == msg.UPDATE:
                for e in msg.elements:
                    self._get_context(msg.context).update_element(utils.msg2element(e), msg.author)
                    er = utils.element2msg(self._get_context(msg.context).get_element(e.id))
                    to_ret.elements.append(er)
                self._publish_change(msg.author, "update", elements=to_ret.elements, context_id=msg.context)
            elif msg.action == msg.UPDATE_PROPERTIES:
                for e in msg.elements:
                    self._get_context(msg.context).update_properties(utils.msg2element(e), msg.author, self._ontology.get_reasoner(msg.type_filter), False)
                    er = utils.element2msg(self._get_context(msg.context).get_element(e.id))
                    to_ret.elements.append(er)
                self._publish_change(msg.author, "update", elements=to_ret.elements, context_id=msg.context)
            elif msg.action == msg.REMOVE:
                for e in msg.elements:
                    self._get_context(msg.context).remove_element(utils.msg2element(e), msg.author)
                self._publish_change(msg.author, "remove", elements=msg.elements, context_id=msg.context)
            elif msg.action == msg.REMOVE_RECURSIVE:
                for e in msg.elements:
                    self._get_context(msg.context).remove_recursive(utils.msg2element(e), msg.author, msg.relation_filter, msg.type_filter)
                self._publish_change(msg.author, "remove_recursive", elements=msg.elements, context_id=msg.context)
        if self._verbose:
            log.info("[WmModify]", "{} {} {}. Time: {:0.3f} secs".format(msg.author, msg.action, [e.id for e in to_ret.elements], self._times.getLast()))
        return to_ret

    def run(self):
        rospy.spin()
