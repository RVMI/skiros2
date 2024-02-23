import rdflib
import skiros2_common.tools.logger as log
from rdflib.namespace import RDF, RDFS, OWL
import os.path
from wrapt.decorators import synchronized


class Ontology:
    def __init__(self, graph=None):
        """
        @brief      Manages an ontology using rdflib
        """
        if graph is not None:
            self._ontology = graph
        else:
            self._ontology = rdflib.ConjunctiveGraph()  # store='Sleepycat' #TODO:

    def ontology(self, context_id=""):
        """
        @brief Returns the ontology graph or a context graph, if contex_id is specified

        @param context_id can be a rdflib.Graph, an rdflib.URIRef or a string
        """
        if context_id == "" or context_id == self._ontology.identifier:
            return self._ontology
        else:
            return self._ontology.get_context(context_id)

    def _add_prefix(self, uri, prefix=None):
        if prefix is None:
            prefix = uri[uri.rfind("/") + 1:].lower()
            if prefix.rfind(".") != -1:
                prefix = prefix[:prefix.rfind(".")]
        uri = uri + "#"
        self._bind(prefix, uri)
        log.info("[{}]".format(self.__class__.__name__), "Set id: {} for ontology: {}".format(prefix, uri))
        return prefix

    def _bind(self, prefix, uri):
        self._ontology.namespace_manager.bind(prefix, uri, True, True)
        return rdflib.Namespace(uri)

    def set_default_prefix(self, prefix, uri):
        self._default_uri = self._bind(prefix, uri)

    def add_default_prefix(self, uri):
        return rdflib.term.URIRef(self._default_uri[uri])

    def uri2lightstring(self, uri):
        if not uri:
            return uri
        if isinstance(uri, rdflib.URIRef):
            uri = uri.n3()
            uri = uri.replace('<', '')
            uri = uri.replace('>', '')
        if uri.find("#") < 0:
            return uri
        tokens = uri.split("#")
        for prefix, uri1 in self._ontology.namespaces():
            if tokens[0] == uri1[:-1]:
                return "{}:{}".format(prefix, tokens[1])  # TODO: can it be optimized?
        return uri

    def lightstring2uri(self, name):
        if isinstance(name, rdflib.URIRef):
            return name
        if name == "":
            return None
        if name.find("#") > 0:
            return rdflib.term.URIRef(name)
        if name.find(":") < 1:
            if name.find(":") == 0:
                name = name[1:]
            return rdflib.term.URIRef(self.add_default_prefix(name))
        tokens = name.split(":")
        for prefix, uri in self._ontology.namespaces():
            if tokens[0] == prefix:
                return rdflib.term.URIRef("{}{}".format(uri, tokens[1]))  # TODO: can it be optimized?
        return rdflib.term.URIRef(name)

    def has_context(self, context_id):
        """
        @brief      Verify if an ontology context id is defined
        """
        raise NotImplementedError("NOT IMPLEMENTED.")

    def add_context(self, context_id, uri=None, imports=[]):
        """
        @brief      Creates a new ontology context

        @param      context_id  (string) The context identifier
        @param      uri         (string/None) if None the ontology uri
                                is set equal to context id
        @param      imports     list(string) A list of ontologies that
                                the new ontology is dependent from

        @return     { description_of_the_return_value }
        """
        new = self._ontology.get_context(context_id)
        if uri is None:
            uri = context_id
        rdfterm = rdflib.URIRef(uri.split('.')[0])
        new.add((rdfterm, RDF.type, OWL.Ontology))
        for i in imports:
            new.add((rdfterm, OWL.imports, self.lightstring2uri(i)))
        self._add_prefix(uri, context_id)
        return new

    def load(self, ontology_uri, context_id="", initialize=False):
        """
        @brief Load an ontology

        @param context_id the id for the ontology context. If None it is generated
        @param initialize if True the context is reinitialized

        @return A context id (string) if the file defines an ontology, None otherwise
        """
        log.info("[{}]".format(self.__class__.__name__), "Loading ontology: {}".format(ontology_uri))
        if initialize and context_id is not None:
            self._ontology.remove_context(context_id)
        if not context_id:
            context_id = ontology_uri[ontology_uri.rfind("/") + 1:ontology_uri.rfind(".")].lower()
        contextg = self._ontology.parse(ontology_uri, publicID=context_id)
        context = contextg.value(predicate=RDF.type, object=OWL.Ontology)
        if context:
            return self._add_prefix(context)

    def save(self, file, context_id=""):
        """
        @brief Save the ontology

        @param context_id If specified, only the context statements are saved in the file
        """
        self.ontology(context_id).serialize(destination=file, format='turtle')

    @synchronized
    def query(self, query, context_id=""):
        return self.ontology(context_id).query(query)

    def add_relation(self, r, context_id, author):
        self.ontology(context_id).add((self.lightstring2uri(r['src']), self.lightstring2uri(r['type']), self.lightstring2uri(r['dst'])))

    def remove_relation(self, r, context_id, author):
        self.ontology(context_id).remove((self.lightstring2uri(r['src']), self.lightstring2uri(r['type']), self.lightstring2uri(r['dst'])))

    def get_sub_classes(self, parent_class, context_id="", recursive=True):
        to_ret = []
        to_ret.append(parent_class)
        uri = self.lightstring2uri(parent_class)
        for subj in self.ontology(context_id).subjects(RDFS.subClassOf, uri):
            if recursive:
                to_ret += self.get_sub_classes(self.uri2lightstring(subj), context_id, True)
            else:
                to_ret.append(self.uri2lightstring(subj))
        return to_ret

    def get_sub_properties(self, parent_property="topDataProperty", context_id="", recursive=True):
        to_ret = []
        to_ret.append(parent_property)
        uri = self.lightstring2uri(parent_property)
        for subj in self.ontology(context_id).subjects(RDFS.subPropertyOf, uri):
            if recursive:
                to_ret += self.get_sub_properties(self.uri2lightstring(subj), context_id, True)
            else:
                to_ret.append(self.uri2lightstring(subj))
        return to_ret

    def get_sub_relations(self, parent_property="topObjectProperty", context_id="", recursive=True):
        to_ret = []
        to_ret.append(parent_property)
        uri = self.lightstring2uri(parent_property)
        for subj in self.ontology(context_id).subjects(RDFS.subPropertyOf, uri):
            if recursive:
                to_ret += self.get_sub_relations(self.uri2lightstring(subj), context_id, True)
            else:
                to_ret.append(self.uri2lightstring(subj))
        return to_ret
