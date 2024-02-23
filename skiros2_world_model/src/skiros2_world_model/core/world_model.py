from os import path, makedirs
import skiros2_common.tools.logger as log
import skiros2_common.ros.utils as utils
from skiros2_common.core.world_element import Element
from skiros2_world_model.ros.ontology_server import Ontology
import rdflib
from rdflib.namespace import RDF, RDFS, OWL, XSD
from wrapt.decorators import synchronized
from skiros2_common.tools.id_generator import IdGen
from skiros2_common.tools.time_keeper import TimeKeepers
from collections import OrderedDict

try:
    unicode
except NameError:
    unicode = str

class IndividualsDataset(Ontology):
    def __init__(self, verbose, context_id, graph=None, init=False):
        """
        @brief      Manages a set of individuals using the Element class

        @param      verbose     The verbose
        @param      context_id  The context identifier
        @param      graph       The graph
        @param      init        The initialize
        """
        Ontology.__init__(self, graph)
        self._reasoners = {}
        self._verbose = verbose
        self._context = self.ontology(context_id)
        self._workspace = "~"
        self._filename = "{}.turtle".format(context_id)
        self._elements_cache = dict()
        self._times = TimeKeepers()
        if init:
            self.reset()

    @property
    def context(self):
        return self._context

    @property
    def filedir(self):
        return "{}/{}".format(self.workspace, self.filename)

    @property
    def filename(self):
        """
        @brief Default name for load/save operations
        """
        return self._filename

    @property
    def workspace(self):
        return self._workspace

    @workspace.setter
    def workspace(self, value):
        """
        @brief Set a folder for load/save operations
        """
        self._workspace = value

    def reset(self):
        """
        @brief Initialize the graph
        """
        self.ontology().remove_context(self.context)
        self._elements_cache.clear()

    def has_individual(self, name):
        """
        @brief Returns true if the individual exists in the ontology
        """
        return self.ontology().value(self.lightstring2uri(name), RDF.type) is not None

    @synchronized
    def get_individual(self, name, context_id=""):
        """
        @brief Builds an element from an individual

        @param context_id if defined look for the individual only in the context
        """
        subject = self.lightstring2uri(name)
        if not self.uri_exists(subject, context_id):
            raise Exception("Element {} doesn't exist in ontology. Uri: {}. Context: {}.".format(name, subject, context_id))
        e = Element()
        for predicate, obj in self.ontology(context_id).predicate_objects(subject):
            if OWL.DatatypeProperty in self.ontology().objects(predicate, RDF.type) or predicate == RDFS.comment:
                e.setProperty(self.uri2lightstring(predicate), obj.value, self.uri2lightstring(obj.datatype), force_convertion=True)
            elif OWL.ObjectProperty in self.ontology().objects(predicate, RDF.type):
                e.addRelation("-1", self.uri2lightstring(predicate), self.uri2lightstring(obj))
            elif predicate == RDF.type and obj != OWL.NamedIndividual:
                e._type = self.uri2lightstring(str(obj))
            elif obj == OWL.NamedIndividual:
                pass
            elif predicate == RDFS.label:
                e._label = obj.value
            else:
                log.error("[get_individual]", "Ignoring {}-{}-{}. Predicate is not defined in the ontology.".format(name, self.uri2lightstring(predicate), self.uri2lightstring(obj)))
        for subj, predicate in self.ontology(context_id).subject_predicates(subject):
            if (self.uri2lightstring(predicate) != "skiros:hasTemplate"):
                e.addRelation(self.uri2lightstring(subj), self.uri2lightstring(predicate), "-1")
        self._add_reasoners_prop(e)
        return e

    def get_template_individual(self, name):
        """
        @brief Builds an element from an ontology individual
        """
        e = self.get_individual(name)
        if e:
            e.label = name
            e.setProperty("skiros:Template", name)
        return e

    def uri_exists(self, uri, context_id=""):
        """
        @brief Check if an uri is defined in a context
        """
        return bool(self.ontology(context_id).value(uri, RDF.type))

    @synchronized
    def add_relation(self, r, author, is_relation):
        """
        @brief Add an rdf triple
        """
        self._add((self.lightstring2uri(r['src']), self.lightstring2uri(r['type']), self.lightstring2uri(r['dst'])), author, is_relation=is_relation)

    @synchronized
    def remove_relation(self, r, author, is_relation):
        """
        @brief Remove an rdf triple
        """
        self._remove((self.lightstring2uri(r['src']), self.lightstring2uri(r['type']), self.lightstring2uri(r['dst'])), author, is_relation=is_relation)

    def get_relations(self, r):
        to_ret = []
        predicates = self.context.predicates(self.lightstring2uri(r['src']), self.lightstring2uri(r['dst']))
        ptypes = self.get_sub_properties(r['type'])
        for p in predicates:
            p = self.uri2lightstring(p)
            if p in ptypes:
                to_ret.append(utils.makeRelation(r['src'], p, r['dst']))
        return to_ret

    def get_element(self, uri):
        """
        @brief Get an element from the scene
        """
        if uri in self._elements_cache:
            return self._elements_cache[uri]
        e = self.get_individual(uri, self.context.identifier)
        e._id = uri
        self._elements_cache[e.id] = e
        return e

    @synchronized
    def load_context(self, filename):
        """
        @brief Load context from file
        """
        if filename:
            self._filename = filename
        if not path.isfile(self.filedir):
            log.error("[load_context]", "Can't load {}. File not found. ".format(self.filename))
            return
        self._stop_reasoners()
        self.reset()
        self.context.parse(self.filedir, format='turtle')
        self._start_reasoners()
        log.info("[load_context]", "Loaded context {}. ".format(self.filename))

    @synchronized
    def save_context(self, filename):
        """
        @brief Save context to file
        """
        if filename:
            self._filename = filename
        directory = self.filedir[0:self.filedir.rfind("/")]
        if not path.exists(directory):
            makedirs(directory)
        self.context.serialize(self.filedir, format='turtle')

    @synchronized
    def add_element(self, e, author):
        """
        @brief Add an element to the context
        """
        self._make_unique_uri(e)
        for name, r in self._reasoners.items():
            if not r.parse(e, "add"):
                raise Exception("Reasoner {} rejected the element {} add".format(name, e))
        if e.hasProperty("skiros:Template"):
            e.addRelation("-1", "skiros:hasTemplate", e.getProperty("skiros:Template").value)
        statements = self._element2statements(e)
        for s, is_relation in statements:
            self._add(s, author, is_relation)
        self._elements_cache[e.id] = e
        return e

    @synchronized
    def update_element(self, e, author):
        """
        @brief Update an element in the scene
        """
        for name, r in self._reasoners.items():
            if not r.parse(e, "update"):
                raise Exception("Reasoner {} rejected the element {} update".format(name, e))
        prev = self._element2statements(self.get_element(e.id))
        curr = self._element2statements(e)
        c1, c2 = zip(*curr)
        for s, is_relation in prev:
            if not s in c1:
                self._remove(s, author, is_relation)
        p1, p2 = zip(*prev)
        for s, is_relation in curr:
            if not s in p1:
                self._add(s, author, is_relation)
        self._elements_cache[e.id] = e

    @synchronized
    def update_properties(self, e, author, reasoner=None):
        """
        @brief Update properties of an element in the scene
        """
        for name, r in self._reasoners.items():
            if not r.parse(e, "update"):
                raise Exception("Reasoner {} rejected the element {} update".format(name, e))
        old_e = self.get_element(e.id)
        subject = self.lightstring2uri(e.id)
        if reasoner is not None:
            prop_to_update = reasoner.getAssociatedData()
        else:
            prop_to_update = e.available_properties
            prop_to_remove = set(old_e.available_properties).difference(set(prop_to_update))
            for k in prop_to_remove:
                predicate = self.lightstring2uri(k)
                values = old_e.getProperty(k).values
                for v in values:
                    self._remove((subject, predicate, rdflib.term.Literal(v, datatype=self._get_datatype(old_e.getProperty(k)))), author)
            for k in prop_to_remove:
                if old_e.hasProperty(k):
                    old_e.removeProperty(k)
            # Horrible hack to update also the label. Label should be moved with other properties to make this clean
            old_e.label = e.label
            self._set((subject, RDFS.label, rdflib.term.Literal(e.label)), author)
        # Set properties
        for k in prop_to_update:
            predicate = self.lightstring2uri(k)
            p = e.getProperty(k)
            values = p.values
            if not old_e.hasProperty(k):
                old_e.setProperty(k, values)
                for i in range(0, len(values)):
                    self._add((subject, predicate, rdflib.term.Literal(values[i], datatype=self._get_datatype(p))), author)
            elif old_e.getProperty(k).values != values:
                if values:
                    self._set((subject, predicate, rdflib.term.Literal(values[0], datatype=self._get_datatype(p))), author)
                else:
                    for v in old_e.getProperty(k).values:
                        self._remove((subject, predicate, rdflib.term.Literal(v, datatype=self._get_datatype(old_e.getProperty(k)))), author)
                for i in range(1, len(values)):
                    self._add((subject, predicate, rdflib.term.Literal(values[i], datatype=self._get_datatype(p))), author)
                old_e.setProperty(k, values)
        self._elements_cache[e.id] = old_e

    @synchronized
    def resolve_elements(self, description):
        """
        @brief Return all elements matching the profile in input (type, label, properties)
        """
        first = []
        to_ret = []
        for e in self._get_types(description._type):
            if description._label == "" or description._label == "Unknown" or e._label == description._label:
                first.append(e)
        # Filter by properties
        for e in first:
            add = True
            for k, p in description._properties.items():
                if not e.hasProperty(k):
                    add = False
                    break
                for v in p.values:
                    if v == "" or v is None:
                        break
                    if not v in e.getProperty(k).values:
                        add = False
                        break
                if not add:
                    break
            if add:
                to_ret.append(e)
        return to_ret

    @synchronized
    def remove_element(self, e, author):
        """
        @brief Remove an element from the scene
        """
        try:
            e = self.get_element(e.id)
        except BaseException:
            log.warn("[remove_element]", "Trying to remove element {}, but doesn't exist.".format(e.id))
            return False
        for name, r in self._reasoners.items():
            if not r.parse(e, "remove"):
                raise Exception("Reasoner {} rejected the element {} removal".format(name, e))
        del self._elements_cache[e.id]
        statements = self._element2statements(e)
        for s, is_relation in statements:
            self._remove(s, author, is_relation)
        return True

    @synchronized
    def remove_recursive(self, e, author, rel_filter="", type_filter=""):
        """
        @brief Remove an element from the scene and all elements related to the initial one
        """
        rels_filter = []
        types_filter = []
        if rel_filter != "":
            rels_filter = self.get_sub_relations(rel_filter)
        if type_filter != "":
            types_filter = self.get_sub_classes(type_filter)
        self._remove_recursive(e, author, rels_filter, types_filter)

    def _remove_recursive(self, e, author, rels, types):
        self.remove_element(e, author)
        for r in e.getRelations("-1", rels):
            if self.uri_exists(self.lightstring2uri(r['dst']), self.context.identifier):
                e2 = self.get_element(r['dst'])
                if e2.type in types or not types:
                    self._remove_recursive(e2, author, rels, types)

    @synchronized
    def get_recursive(self, eid, rel_filter="", type_filter=""):
        """
        @brief Get an element from the scene and all elements related to the initial one
        """
        to_ret = OrderedDict()
        rels_filter = []
        types_filter = []
        if rel_filter != "":
            rels_filter = self.get_sub_relations(rel_filter)
        if type_filter != "":
            types_filter = self.get_sub_classes(type_filter)
        self._get_recursive(self.get_element(eid), rels_filter, types_filter, to_ret)
        return to_ret

    def get_reasoner(self, reasoner_class):
        if reasoner_class not in self._reasoners:
            return None
        return self._reasoners[reasoner_class]

    def load_reasoner(self, reasoner_class):
        self._reasoners[reasoner_class.__name__] = reasoner_class()
        self._reasoners[reasoner_class.__name__].init(self)
        self._reasoners[reasoner_class.__name__].execute()
        log.info("[load_reasoner] Loaded {}".format(reasoner_class.__name__))

    def _add_reasoners_prop(self, e):
        """
        if the object is marked as associated to a reasoner, check that all properties are present
        """
        if e.hasProperty("skiros:DiscreteReasoner"):
            for v in e.getProperty("skiros:DiscreteReasoner").values:
                if v in self._reasoners:
                    self._reasoners[v].addProperties(e)

    def _stop_reasoners(self):
        for r in self._reasoners.values():
            r.stop()

    def _start_reasoners(self):
        for r in self._reasoners.values():
            r.execute()

    def _make_unique_uri(self, e):
        if e.id == "":
            if not e.label:
                e.label = "unknown"
            e._id = e.label
        i = 1
        while self.uri_exists(self.lightstring2uri(e.id)):
            e._id = "{}_{}".format(e.label, i)
            i += 1

    def _get_recursive(self, e, rels_filter, types_filter, elist):
        """
        @brief Get all elements related to the initial one. Anti-loop guarded
        """
        elist[e.id] = e
        for r in e.getRelations("-1", rels_filter):
            if self.uri_exists(self.lightstring2uri(r['dst']), self.context.identifier):
                e2 = self.get_element(r['dst'])
                if (e2._type in types_filter or not types_filter) and e2._id not in elist:
                    self._get_recursive(e2, rels_filter, types_filter, elist)

    def _get_datatype(self, param):
        if param.dataTypeIs(str) or param.dataTypeIs(unicode):
            return XSD.string
        elif param.dataTypeIs(float):
            return XSD.float
        elif param.dataTypeIs(bool):
            return XSD.boolean
        elif param.dataTypeIs(int):
            return XSD.integer
        else:
            log.error("[Wm]", "Param {} has type {} that is not supported.".format(param.key, param.dataType()))
            return None

    def _set(self, statement, author, time=None, probability=1.0):
        """
        @brief Remove any existing triples for subject and predicate before adding
        (subject, predicate, object).

        Convenience method to update the value of object
        """
        self.context.set(statement)
        if self._verbose:
            log.info("{}->{}".format(author, self.context.identifier.n3()), log.logColor.RED + log.logColor.BOLD +
                     "[-] ({}) - ({}) - (*)) . ".format(self.uri2lightstring(statement[0]), self.uri2lightstring(statement[1])))
            log.info("{}->{}".format(author, self.context.identifier.n3()), log.logColor.GREEN + log.logColor.BOLD +
                     "[+] ({}) - ({}) - ({}) .".format(self.uri2lightstring(statement[0]), self.uri2lightstring(statement[1]), self.uri2lightstring(statement[2])))

    def _remove(self, statement, author, is_relation=False):
        """
        @brief Remove a statement from the scene
        """
        self.context.remove(statement)
        if is_relation:
            s0 = self.uri2lightstring(statement[0])
            s1 = self.uri2lightstring(statement[1])
            s2 = self.uri2lightstring(statement[2])
            if s0 in self._elements_cache:
                self._elements_cache[s0].removeRelation2("-1", s1, s2)
            if s2 in self._elements_cache:
                self._elements_cache[s2].removeRelation2(s0, s1, "-1")
        if self._verbose:
            log.info("{}->{}".format(author, self.context.identifier.n3()), log.logColor.RED + log.logColor.BOLD +
                     "[-] ({}) - ({}) - ({}) .".format(self.uri2lightstring(statement[0]), self.uri2lightstring(statement[1]), self.uri2lightstring(statement[2])))

    def _add(self, statement, author, is_relation=False):
        """
        @brief Add a statement to the scene
        """
        self.context.add(statement)
        if is_relation:
            s0 = self.uri2lightstring(statement[0])
            s1 = self.uri2lightstring(statement[1])
            s2 = self.uri2lightstring(statement[2])
            if s0 in self._elements_cache:
                self._elements_cache[s0].addRelation("-1", s1, s2)
            if s2 in self._elements_cache:
                self._elements_cache[s2].addRelation(s0, s1, "-1")
        if self._verbose:
            log.info("{}->{}".format(author, self.context.identifier.n3()), log.logColor.GREEN + log.logColor.BOLD +
                     "[+] ({}) - ({}) - ({}) . ".format(self.uri2lightstring(statement[0]), self.uri2lightstring(statement[1]), self.uri2lightstring(statement[2])))

    def _element2statements(self, e):
        to_ret = []
        subject = self.lightstring2uri(e.id)
        to_ret.append(((subject, RDF.type, OWL.NamedIndividual), False))
        to_ret.append(((subject, RDF.type, self.lightstring2uri(e.type)), False))
        to_ret.append(((subject, RDFS.label, rdflib.term.Literal(e.label)), False))
        for k, p in e._properties.items():
            predicate = self.lightstring2uri(k)
            for v in p.getValues():
                value = rdflib.term.Literal(v, datatype=self._get_datatype(p))
                to_ret.append(((subject, predicate, value), False))
        for r in list(e._relations):
            if r['src'] == "-1" or r['src'] == e.id:
                if not self.uri_exists(self.lightstring2uri(r['dst'])):
                    log.error("[element2statements]", "Element with key {} is not defined in ontology. Skipped relation: {}".format(r['dst'], r))
                    e.removeRelation(r)
                    continue
                to_ret.append(((subject, self.lightstring2uri(r['type']), self.lightstring2uri(r['dst'])), True))
            else:
                if not self.uri_exists(self.lightstring2uri(r['src'])):
                    log.error("[element2statements]", "Element with key {} is not defined in ontology. Skipped relation: {}".format(r['src'], r))
                    e.removeRelation(r)
                    continue
                to_ret.append(((self.lightstring2uri(r['src']), self.lightstring2uri(r['type']), subject), True))
        return to_ret

    def _get_types(self, eclass):
        """
        @brief Return all elements of a type
        """
        to_ret = []
        types_filter = self.get_sub_classes(eclass)
        for etype in types_filter:
            for subj in self.context.subjects(RDF.type, self.lightstring2uri(etype)):
                to_ret.append(self.get_element(self.uri2lightstring(subj)))
        return to_ret


class WorldModel(IndividualsDataset):
    def __init__(self, verbose, context_id, change_cb):
        """
        @brief      Manages a set of individuals with unique ID
                    generation

        @param      verbose     The verbose
        @param      context_id  The context identifier
        @param      change_cb   The change cb
        """
        self._id_gen = IdGen()
        self._change_cb = change_cb
        IndividualsDataset.__init__(self, verbose, context_id, init=False)

    def reset(self, add_root=True, scene_name="skiros:blank_scene"):
        """
        @brief Initialize the scene
        """
        IndividualsDataset.reset(self)
        self._id_gen.clear()
        if add_root:
            if self.has_individual(scene_name):
                root = self.get_individual(scene_name)
            else:
                root = Element("skiros:Scene", scene_name)
            self.add_element(root, self.__class__.__name__)

    def _remove(self, statement, author, is_relation=False):
        """
        @brief Remove a statement from the scene
        """
        IndividualsDataset._remove(self, statement, author, is_relation)
        if is_relation:
            self._change_cb(author, "remove", relation={'src': self.uri2lightstring(
                statement[0]), 'type': self.uri2lightstring(statement[1]), 'dst': self.uri2lightstring(statement[2])})

    def _add(self, statement, author, is_relation=False):
        """
        @brief Add a statement to the scene
        """
        IndividualsDataset._add(self, statement, author, is_relation)
        if is_relation:
            self._change_cb(author, "add", relation={'src': self.uri2lightstring(
                statement[0]), 'type': self.uri2lightstring(statement[1]), 'dst': self.uri2lightstring(statement[2])})

    def _uri2type(self, uri):
        return uri.split('-')[0]

    def _uri2id(self, uri):
        hash_pos = uri.find('#')
        if hash_pos < 0 or uri.find("-", hash_pos) < 0:
            return -1
        return int((uri[hash_pos:]).split('-')[1])

    @synchronized
    def load_context(self, filename):
        """
        @brief Load scene from file
        """
        if filename:
            self._filename = filename
        if not path.isfile(self.filedir):
            log.error("[load_context]", "Can't load scene {}. File not found. ".format(self.filename))
            return
        self._stop_reasoners()
        self.reset(add_root=False)
        self.context.parse(self.filedir, format='turtle')
        individuals = self.context.query("SELECT ?x WHERE { ?x rdf:type <http://www.w3.org/2002/07/owl#NamedIndividual>. } ")
        for i in individuals:
            i = self.uri2lightstring(i[0])
            iid = self._uri2id(i)
            if iid >= 0:
                self._id_gen.getId(iid)
        self._start_reasoners()
        log.info("[load_scene]", "Loaded scene {}. ".format(self.filename))

    @synchronized
    def add_element(self, e, author):
        """
        @brief Add an element to the scene
        """
        e.setUri(self._id_gen.getId(e.getIdNumber()))
        IndividualsDataset.add_element(self, e, author)
        return e

    @synchronized
    def update_element(self, e, author):
        """
        @brief Update an element in the scene
        """
        if not self._id_gen.hasId(self._uri2id(e.id)):
            log.error("[update_element]", "Request update from {}, but Id {} is not present in the wm. ".format(author, self._uri2id(e.id)))
            return
        IndividualsDataset.update_element(self, e, author)

    @synchronized
    def update_properties(self, e, author, reasoner=None, publish=True):
        """
        @brief Update properties of an element in the scene
        """
        if not self._id_gen.hasId(self._uri2id(e.id)):
            log.error("[update_element]", "Request update from {}, but Id {} is not present in the wm. ".format(author, self._uri2id(e.id)))
            return
        IndividualsDataset.update_properties(self, e, author, reasoner)
        if publish:
            self._change_cb(author, "update", self.get_element(e.id))

    @synchronized
    def remove_element(self, e, author):
        """
        Remove an element from the scene
        """
        if IndividualsDataset.remove_element(self, e, author):
            self._id_gen.removeId(self._uri2id(e.id))
            return True
        return False
