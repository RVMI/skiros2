import skiros2_common.tools.logger as log
from skiros2_common.tools.plugin_loader import PluginLoader
from skiros2_common.core.discrete_reasoner import DiscreteReasoner
from skiros2_common.core.property import Property
from datetime import datetime
import rospy

try:
    unicode
    def ispy2unicode(value):
        return isinstance(value, unicode)
except NameError:
    def ispy2unicode(value):
        return False
try:
    basestring
except NameError:
    basestring = str

class Element(object):
    """
    @brief A touple type, label, id, properties, relation, where:
        -type reference the class type in the ontology
        -label reference a template individual in the ontology
        -id is the individual uri
        -properties is a collection of Properties
        -relations is a collection of relations with other elements

    >>> e = Element()
    >>> e.setProperty("Hello", float)
    >>> e.setProperty("Hello", 0.0)
    >>> e.getProperty("Hello").value
    0.0
    >>> e.getProperty("Hello").values = 1.0
    >>> e.getProperty("Hello").values
    [1.0]
    >>> e.getProperty("Hello").value = 2.0
    >>> e.getProperty("Hello").values
    [2.0]
    """
    __slots__ = ['_last_update', '_type', '_label', '_id', '_properties', '_local_relations', '_relations', '_last_tf_timestamp']
    _plug_loader = None
    _property_reasoner_map = None

    def printState(self, verbose=False, filter=""):
        if self._id == "":
            to_ret = self._type
        else:
            to_ret = self._id
        to_ret = to_ret + "-" + self._label  # + self._properties
        if verbose:
            for k, p in self._properties.items():
                if k == filter or filter == "":
                    to_ret += "\n" + p.printState()
            for r in self._relations:
                to_ret += "\n" + str(r)
        return to_ret

    def __init__(self, etype="Unknown", elabel="", eid=""):
        # Description
        self._type = etype
        self._label = elabel
        self._id = eid
        self._properties = dict()
        self._local_relations = list()  # Reference to Elements
        self._relations = list()  # Reference to IDs
        self._last_tf_timestamp = 0
        self._setLastUpdate()

    def __repr__(self):
        return self.printState()

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, t):
        self._type = t

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, l):
        self._label = l

    @property
    def available_properties(self):
        return self._properties.keys()

    @property
    def properties(self):
        return self._properties.values()

    def isAbstract(self):
        """
        @brief Return True if the element is abstract, or False if it is instanciated in the world model
        """
        return self.id == ""

    def _setLastUpdate(self):
        self._last_update = datetime.now()

    def getLastUpdate(self):
        return self._last_update

    def _initPluginLoader(self):
        Element._plug_loader = PluginLoader()
        Element._property_reasoner_map = {}
        # TODO: remove dependency from ROSpy
        for package in rospy.get_param('wm/reasoners_pkgs', []):
            Element._plug_loader.load(package, DiscreteReasoner)
        for plugin in Element._plug_loader:
            r = plugin()
            Element._property_reasoner_map[r.__class__.__name__] = r
            for p in r.getAssociatedProperties():
                Element._property_reasoner_map[p] = r
            for p in r.getAssociatedRelations():
                Element._property_reasoner_map[p] = r

    def _getReasoner(self, get_code):
        """
        @brief Return the reasoner associated to get_code
        """
        if not isinstance(Element._plug_loader, PluginLoader):
            self._initPluginLoader()
        if get_code not in Element._property_reasoner_map:
            raise KeyError("No reasoner associated to key {}. Debug: {}".format(get_code, Element._property_reasoner_map))
        return Element._property_reasoner_map[get_code]

    def getAssociatedReasonerId(self, key):
        """
        @brief Returns the reasoner associated to a property, or an empty string otherwise
        """
        if not isinstance(Element._plug_loader, PluginLoader):
            self._initPluginLoader()
        for plugin in Element._plug_loader:
            r = plugin()
            if key in r.getAssociatedData():
                return r.__class__.__name__
        return ""

    def getIdNumber(self):
        """
        @brief Return the element id number as integer
        """
        hash_pos = self._id.find('#')
        # Search after # if there is one
        if hash_pos == -1:
            hash_pos = 0
        if self._id.find("-", hash_pos) < 0:
            return -1
        return int((self._id[hash_pos:]).split('-')[1])

    def setUri(self, eid):
        self._setLastUpdate()
        self._id = "{}-{}".format(self._type, eid)

    def setReasoner(self, name):
        """
        @brief Associate the element to a reasoner
        @name the name of the reasoner
        """
        self._getReasoner(name).addProperties(self)

    def unsetReasoner(self, name):
        """
        @brief Disassociate the element from a reasoner
        @name the name of the reasoner
        """
        self._getReasoner(name).removeProperties(self)

    def hasData(self, get_code):
        """
        @brief Check if the element has data using a reasoner
        """
        return self._getReasoner(get_code).hasData(self, get_code)

    def getData(self, get_code):
        """
        @brief Extract data using a reasoner
        """
        return self._getReasoner(get_code).getData(self, get_code)

    def setData(self, set_code, data):
        """
        @brief Set data using a reasoner
        """
        self._setLastUpdate()
        self._getReasoner(set_code).addProperties(self)
        return self._getReasoner(set_code).setData(self, data, set_code)

    def getRelation(self, subj="", pred=[], obj=""):
        """
        @brief Return the first relation matching with input filters or none
        """
        to_ret = self.getRelations(subj, pred, obj)
        if to_ret:
            return to_ret[0]
        else:
            return None

    def removeRelations(self, relations):
        """
        @brief Remove a list of relations from the element
        """
        for r in relations:
            self.removeRelation(r)

    def removeRelation(self, relation):
        """
        @brief Remove a relation from the element
        """
        self._relations.remove(relation)

    def removeRelation2(self, subj, predicate, obj, value=True, abstract=False):
        """
        @brief Remove a relation from the element
        """
        try:
            self._relations.remove({'src': subj, 'type': predicate, 'dst': obj, 'state': value, 'abstract': abstract})
        except BaseException:
            log.error("[removeRelation2]", "Can t remove {} from {}".format({'src': subj, 'type': predicate, 'dst': obj, 'state': value, 'abstract': abstract}, self._relations))

    def getRelations(self, subj="", pred=[], obj=""):
        """
        @brief Return a list of all relations matching with input filters
        """
        to_ret = []
        if isinstance(pred, str):
            pred = [pred]
        if pred:
            if pred[0] == "":
                pred = []
        for r in self._relations:
            if (r['src'] == subj or subj == "") and (r['type'] in pred or not pred) and (r['dst'] == obj or obj == ""):
                to_ret.append(r)
        return to_ret

    def setRelation(self, subj, predicate, obj):
        """
        @brief Set a relation, overriding previous definitions
        """
        self.removeRelations(self.getRelations(subj if subj == "-1" else "", predicate, obj if obj == "-1" else ""))
        self.addRelation(subj, predicate, obj)

    def addRelation(self, subj, predicate, obj, value=True, abstract=False):
        """
        @brief      Add a relation with another element

        @param      subj       An element id
        @param      predicate  The predicate
        @param      obj        An element or an element id
        @param      value      The state of the relation should be True or False
        @param      abstract   Whether the relation is between abstract objects
                               or instances
        """
        self._setLastUpdate()
        if isinstance(obj, Element):
            self._local_relations.append({'src': "-1", 'type': predicate, 'dst': obj})
        elif isinstance(subj, basestring) and isinstance(obj, basestring):
            r = {'src': subj, 'type': predicate, 'dst': obj, 'state': value, 'abstract': abstract}
            if not r in self._relations:
                self._relations.append(r)
        else:
            raise ValueError('Subject/Object must be of type string or Element: subject type is {}. object type is {}'.format(type(subj), type(obj)))

    def hasRelation(self, subj, predicate, obj, value=True, abstract=False):
        """
        @brief      Return true if element has the relation

        @param      subj       An element or an element id
        @param      predicate  The predicate
        @param      obj        An element or an element id
        @param      value      The state of the relation should be True or False
        @param      abstract   Whether the relation is between abstract objects
                               or instances

        @return     True if relation, False otherwise.
        """
        if {'src': subj, 'type': predicate, 'dst': obj, 'state': value, 'abstract': abstract} in self._relations:
            return True
        if not subj or subj == "-1":
            subj = self.id
        elif not obj or obj == "-1":
            obj = self.id
        return {'src': subj, 'type': predicate, 'dst': obj, 'state': value, 'abstract': abstract} in self._relations

    def hasProperty(self, key, value=None, not_none=False):
        """
        @brief      Return true if element has the property.

        @param      key       the property to check
        @param      value     if specified, return true if the property has that
                              value
        @param      not_none  when set to true, checks that the property doesn't
                              have none as value

        @return     True if property, False otherwise.
        """
        if key not in self._properties:
            return False
        if value is not None:
            return self.getProperty(key).find(value) != -1
        return self.getProperty(key).isSpecified() or not not_none

    def setProperty(self, key, value, datatype=None, force_convertion=False):
        """
        @brief Set the property to a value. If datatype is specified tries to convert.
        """
        self._setLastUpdate()

        if key == 'skiros:DiscreteReasoner':
            old_reasoners = []
            if self.hasProperty('skiros:DiscreteReasoner'):
                old_reasoners = self._properties[key].values

        if datatype:
            if datatype == "xsd:double" or datatype == "xsd:float":
                self._properties[key] = Property(key, float)
            elif datatype == "xsd:int" or datatype == "xsd:integer":
                self._properties[key] = Property(key, int)
            elif datatype == "xsd:boolean":
                self._properties[key] = Property(key, bool)
            elif datatype == "xsd:string":
                self._properties[key] = Property(key, str)
            else:
                log.warn("[Element]", "Datatype {} not recognized. Set default.".format(datatype))
                self._properties[key] = Property(key, value)

        if ispy2unicode(value):
            value = str(value)

        if self.hasProperty(key):
            if force_convertion:
                if isinstance(value, list):
                    value = [self._properties[key].dataType()(v) for v in value]
                else:
                    value = self._properties[key].dataType()(value)
            self._properties[key].setValues(value)
        else:
            self._properties[key] = Property(key, value)

        if key == 'skiros:DiscreteReasoner':
            new_reasoners = self._properties[key].values
            try:
                [self._getReasoner(r).removeProperties(self) for r in old_reasoners if r not in new_reasoners]
                [self._getReasoner(r).addProperties(self) for r in new_reasoners if r not in old_reasoners]
            except KeyError as e:
                log.error("WorldElement", str(e.args))

    def removeProperty(self, key):
        """
        @brief Remove the property
        """
        self._setLastUpdate()

        if key == 'skiros:DiscreteReasoner':
            [self._getReasoner(r).removeProperties(self) for r in self._properties[key].values]

        del self._properties[key]

    def appendProperty(self, key, value):
        """
        @brief Append a value to the property. If property doesn't exist it is created.
        >>> e = Element()
        >>> e.setProperty("Integer", 2, "xsd:int")
        >>> e.getProperty("Integer").value
        2
        >>> e.appendProperty("Integer", 3)
        >>> e.getProperty("Integer").values
        [2, 3]
        """
        self._setLastUpdate()
        if self.hasProperty(key):
            self._properties[key].addValue(value)
        else:
            self.setProperty(key, value)

    def getProperty(self, key):
        """
        @brief Get a property
        """
        return self._properties[key]

    def isInstance(self, abstract, wmi):
        """
        Compare the element to an abstract description
        Return true if this is a valid instance, false otherwise
        """
        # Filter by type
        if not self._type == abstract._type and not (wmi.add_prefix(self._type) in wmi.get_sub_classes(abstract._type, True)):
            return False
        # Filter by label
        if not (abstract._label == "" or abstract._label == "Unknown" or self._label == abstract._label):
            return False
        # Filter by properties
        for k, p in abstract._properties.items():
            if not self.hasProperty(k):
                return False
            for v in p.getValues():
                if not v in self.getProperty(k).values:
                    return False
        # Filter by relations
        for r in abstract._relations:
            if r["src"] == "-1" or r["src"] == abstract._id:  # -1 is the special autoreferencial value
                #print wmi.getRelations(self._id, r["type"], -1)
                if not wmi.get_relations(self._id, r["type"], "-1"):
                    return False
            else:
                #print wmi.getRelations(-1, r["type"], self._id)
                if not wmi.get_relations("-1", r["type"], self._id):
                    return False
        return True
