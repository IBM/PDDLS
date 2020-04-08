import sys
import argparse
import json
import yaml
import rdflib
from rdflib import Namespace, URIRef, Literal
from io import StringIO

from .pddl2json import parseAsJson
from .json2pddl import serializePredicateAxiom, serializePDDL

def extractObjectURIs(problem):
    problemContext = problem.get('@context', {})
    result = {}
    for obj in problem['pddl:objects'].keys():
        if obj in problemContext:
            result[problemContext[obj]] = obj
    return result


def extractPredicateURIs(domains):
    result = {}
    for pddlDomain in domains:
        domainContext = pddlDomain.get('@context', {})
        for predicateStmt in pddlDomain['pddl:predicates']:
            symbol = next(iter(predicateStmt.keys())) # first key
            params = predicateStmt[symbol]
            if symbol in domainContext:
                result[domainContext[symbol]] = (symbol, params)
    return result


def anyIn(uriRefs, objset):
    for uriRef in uriRefs:
        if not (str(uriRef) in objset):
            print("Excluded axiom with an object {}".format(uriRef))
            return False
    return True


ESTABLISHED_WITH = URIRef(u'uri:pddls#establishedWith')


def uriRefs2Symbols(uriRefs, objectURIs):
    return [objectURIs[str(uriRef)] for uriRef in uriRefs]


def resolvePredicateAxioms(predicateURI, objectURIs, ontology):
    predicateURI = URIRef(predicateURI) if not type(predicateURI) is URIRef else predicateURI
    formula = None
    formulas = ontology.objects(predicateURI, ESTABLISHED_WITH)
    for f in formulas:
        if type(f) is Literal and f.language == 'sparql':
            print("SPARQL formula Found")
            formula = str(f)
            break
        else:
            if type(f) is URIRef:
                print("Unsupported graph formula found {}".format(f))
                pass
            else:
                print("Unsupported formula found with language {}".format(f.language))
    if formula:
        qres = ontology.query(formula)
        #return qres
        return [ objs for objs in qres if anyIn(objs, objectURIs) ]
    else:
        return []


def translate(problem, objects_ontology, domains, common_ontology=rdflib.Graph()):
    onto_graph = objects_ontology + common_ontology

    predicateURIs = extractPredicateURIs(domains)
    print("Extracted predicates:")
    print(yaml.dump(dict(predicateURIs), default_flow_style=False, indent=4))
    objectURIs = extractObjectURIs(problem)
    print("Extracted objects:")
    print(yaml.dump(dict(objectURIs), default_flow_style=False, indent=4))

    axioms = []
    for predURI, (symbol, _params) in predicateURIs.items():
        print("Resolving predicate {}".format(predURI))
        qres = resolvePredicateAxioms(predURI, objectURIs, onto_graph)
        for uriRefs in qres:
            #print("{} insertable {}".format(pillar, hole))
            axiom_args = uriRefs2Symbols(uriRefs, objectURIs)
            axiom = serializePredicateAxiom(symbol, axiom_args)
            axioms.append(axiom)

    result_problem = problem.copy()
    if '@context' in result_problem:
        result_problem.pop('@context')
    result_problem['pddl:init'] += axioms

    result_domains = []
    for domain in domains:
        result_domain = domain.copy()
        if '@context' in result_domain:
            result_domain.pop('@context')
        result_domains.append(result_domain)

    return (result_problem, result_domains)


def main(args):
    if args.input_pddls_file[-5:] == '.json' or args.input_pddls_file[-7:] == '.jsonld':
        with open(args.input_pddls_file, 'r') as fd:
            problem = json.load(fd)
    else:
        problem = parseAsJson(args.input_pddls_file)

    domains = [parseAsJson(domain_file) for domain_file in args.domain_file]

    onto_graph = rdflib.Graph()
    for onto_file in args.ontology_file:
        rdf_format = rdflib.util.guess_format(onto_file)
        onto_graph.parse(onto_file, format=rdf_format)

    #print(yaml.dump(dict(problem), default_flow_style=False, indent=4))

    resultProblem, _resultDomains = translate(problem, onto_graph, domains)
    args.output_file.write(serializePDDL(resultProblem))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Translate PDDLS to PDDL (or YAML).')
    ap.add_argument('input_pddls_file', type=str,
                    help='source problem PDDLS')
    ap.add_argument('-d', '--domain_file',
                    nargs='+', type=str,
                    help='PDDLS file(s) for domain')
    ap.add_argument('-r', '--ontology_file',
                    nargs='+', type=str, default=[],
                    help='RDF file(s) for ontology')
    ap.add_argument('-o', '--output_file',
                    type=argparse.FileType('w'), default=sys.stdout,
                    help='Output problem PDDL file')
    args = ap.parse_args()

    main(args)
