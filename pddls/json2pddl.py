import sys
import json
import yaml
from io import StringIO


def serializePredicateAxiom(predicate, args):
    if len(args) > 0:
        return "({} {})".format(predicate, ' '.join(args))
    else:
        return "({})".format(predicate)


class PDDLOut:
    
    def __init__(self, out):
        self.out = out

    def printPDDL(self, pddl):
        if 'domain' in pddl:
            self.printDomain(pddl)
        elif 'problem' in pddl:
            self.printProblem(pddl)
        else:
            raise RuntimeError('Illegal PDDL')
        
    def dumps(self, obj):
        if obj is None:
            pass
        elif type(obj) is list:
            for item in obj:
                self.dumps(item)
                self.out.write('\n')
        elif type(obj) is dict:
            self.out.write('(\n')
            for key in obj:
                if key[0] == '@':
                    continue
                self.out.write('({} '.format(key))
                self.dumps(obj[key])
                self.out.write(')\n')
            self.out.write(')')
        else:
            self.out.write(str(obj))

    def printDomain(self, pddl):
        domain = pddl['domain']
        self.out.write('(define (domain {})\n'.format(domain))
        if 'pddl:requirements' in pddl:
            self.printRequireDef(pddl['pddl:requirements'])
        if 'pddl:types' in pddl:
            self.printTypesDef(pddl['pddl:types'])
        if 'pddl:predicates' in pddl:
            self.printPredicatesDef(pddl['pddl:predicates'])
        if 'pddl:functions' in pddl:
            self.printFunctionsDef(pddl['pddl:functions'])
        if 'structure' in pddl:
            self.printStructureDef(pddl['structure'])
        self.out.write(')\n')
    
    def printRequireDef(self, requireKeys):
        self.out.write('    (:requirements {})\n'.format(' '.join(requireKeys)))

    def printTypesDef(self, typedNames):
        self.out.write('    (:types')
        self.printTypedNames(typedNames)
        self.out.write(')\n')

    def printTypedNames(self, typedNames):
        noparents = []
        for name in typedNames:
            if typedNames[name] is not None:
                self.out.write(' {} - {}'.format(name, typedNames[name]))
            else:
                noparents.append(name)
        if noparents:                
            self.out.write(' {}'.format(' '.join(noparents)))

    # '(' ':predicates' atomicFormulaSkeleton+ ')'
    def printPredicatesDef(self, predicates):
        self.out.write('    (:predicates\n')
        assert type(predicates) is list
        for predicate in predicates:
            assert type(predicate) is dict and len(predicate) == 1
            name, params = predicate.items()[0]
            self.out.write('        ({} '.format(name))
            self.printParameters(params)
            self.out.write(')\n')
        self.out.write('    )\n')
        
    def printParameters(self, params):
        assert type(params) is list
        is_first = True
        for param in params:
            if is_first:
               is_first = False
            else:
                self.out.write(' ')
            assert type(param) is dict and len(param) == 1
            paramname, paramtype = param.items()[0]
            if paramtype:
                self.out.write('{} - {}'.format(paramname, paramtype))
            else:
                self.out.write(paramname)

    # '(' ':functions' (atomicFunctionSkeleton+ ('-' functionType)? )* ')'
    def printFunctionsDef(self, functions):
        self.out.write('    (:functions\n')
        assert type(functions) is list
        for func in functions:
            assert type(func) is dict and len(func) == 1
            funcname, params = func.items()[0]
            self.out.write('        ({}'.format(funcname))
            self.printParameters(params)
            self.out.write(')\n')
        self.out.write('    )\n')

    # structureDef
    #    : actionDef
    #    | durativeActionDef
    #    | derivedDef
    #    ;
    def printStructureDef(self, structure):
        for actionlike in structure:
            if 'pddl:action' in actionlike:
                name = actionlike['pddl:action']
                parameters = actionlike['pddl:parameters']
                precondition = actionlike['pddl:precondition']
                effect = actionlike['pddl:effect']
                self.out.write('    (:action {}\n'.format(name))
                self.out.write('        :parameters (')
                self.printParameters(parameters)
                self.out.write(')\n')
                self.out.write('        :precondition {}\n'.format(precondition))
                self.out.write('        :effect {}\n'.format(effect))
                self.out.write('    )')
            elif 'pddl:durativeActionDef' in actionlike:
                pass
            elif 'pddl:derivedDef' in actionlike:
                pass
            else:
                self.dumps(actionlike)
                continue
            self.out.write('\n')

    # problem : '(' 'define' problemDecl
    # problemDomain
    # requireDef?
    # objectDecl?
    # init
    # goal
    # probConstraints?
    # metricSpec?
    # ')'
    # ;
    def printProblem(self, pddl):
        problem = pddl['problem']
        self.out.write('(define (problem {})\n'.format(problem))
        self.printProblemDomain(pddl['pddl:problem_domain'])
        if 'pddl:requirements' in pddl:
            self.printRequireDef(pddl['pddl:requirements'])
        if 'pddl:objects' in pddl:
            self.printObjectDecl(pddl['pddl:objects'])
        self.printInit(pddl['pddl:init'])
        self.printGoal(pddl['pddl:goal'])
        self.out.write(')\n')
        
    def printProblemDomain(self, problemDomain):
        self.out.write('    (:domain {})\n'.format(problemDomain))

    def printObjectDecl(self, objects):
        self.out.write('    (:objects\n')
        self.printTypedNames(objects)
        self.out.write('    )\n')

    def printInit(self, objects):
        self.out.write('    (:init\n')
        self.dumps(objects)
        self.out.write('    )\n')

    def printGoal(self, objects):
        self.out.write('    (:goal\n')
        self.dumps(objects)
        self.out.write('    )\n')


#
# The PDDL generation API
def serializePDDL(pddl):
    writer = StringIO()
    PDDLOut(writer).printPDDL(pddl)
    return writer.getvalue()

#
# The PDDL generation API
def printPDDL(pddl, out=sys.stdout):
    """Write the PDDL description into the specified stream.
    Default to standard output.
    """
    PDDLOut(out).printPDDL(pddl)


def main():
    pddl = None
    if sys.argv[1][-len('.yaml'):].lower() == '.yaml':
        pddl = yaml.load(open(sys.argv[1], 'r'))
    else:
        # json or jsonld
        pddl = json.load(open(sys.argv[1], 'r'))
    printPDDL(pddl)


if __name__ == '__main__':
    main()
