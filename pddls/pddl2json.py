import sys
import argparse
import json
import yaml
from collections import OrderedDict
import antlr4
import pddlpy
from pddlpy.pddlLexer import pddlLexer
from pddlpy.pddlParser import pddlParser
from pddlpy.pddlListener import pddlListener


yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_data(dict(data)))
yaml.add_representer(str, lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data))


def isNonTerm(tree):
    return hasattr(tree, 'children')


def toText(tree):
    if not isNonTerm(tree):
        return tree.getText()
    else:
        result = ''
        isFirst = True
        for nonterm in tree.children:
            if isFirst:
                isFirst = False
            else:
                result += ' '
            result += toText(nonterm)
        return result


class Pddl2JsonVisitor(pddlListener):
    
    def __init__(self, out=sys.stdout):
        self.out = out
        self.stack = []
        self.result = None
    
    def push(self, current_obj):
        #print(">")
        self.stack.append(current_obj)

    def pop(self):
        #print("<")
        return self.stack.pop()

    def peek(self):
        return self.stack[-1]

    # Enter a parse tree produced by pddlParser#pddlDoc.
    def enterPddlDoc(self, ctx):
        self.result = obj = OrderedDict()
        self.push(obj)
        pass

    # Exit a parse tree produced by pddlParser#pddlDoc.
    def exitPddlDoc(self, ctx):
        pass

    # Enter a parse tree produced by pddlParser#domain.
    def enterDomain(self, ctx):
        self.isDomain = True
    
    # Exit a parse tree produced by pddlParser#domain.
    def exitDomain(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#domainName.
    # ( domain <name> )
    def exitDomainName(self, ctx):
        assert ctx.children[1].getText() == 'domain'
        name = ctx.children[-2].getText()
        self.peek()['domain'] = name
        # or a name for 'pddl:Domain'?

    # Exit a parse tree produced by pddlParser#typesDef.
    # ( :context <namespaceBinding>+ )
    def exitContextDef(self, ctx):
        assert ctx.children[1].getText() == ':context'
        assert ctx.getChildCount() >= 4
        bindings = OrderedDict()
        for tn in ctx.children[2:-1]:
            name = tn.children[0].getText()
            namespace = tn.children[2].getText()
            bindings[name] = namespace
        self.peek()['@context'] = bindings

    # Exit a parse tree produced by pddlParser#requireDef.
    # ( :requirements <REQUIRE_KEY>+ )
    def exitRequireDef(self, ctx):
        assert ctx.children[1].getText() == ':requirements'
        require_keys = [ t.getText() for t in ctx.children[2:ctx.getChildCount() - 1]]
        self.peek()['pddl:requirements'] = require_keys

    # Exit a parse tree produced by pddlParser#typesDef.
    # ( :types <typedNameList> )
    def exitTypesDef(self, ctx):
        assert ctx.children[1].getText() == ':types'
        assert ctx.getChildCount() == 4
        typedNameList = OrderedDict()
        for tn in ctx.children[2].children:
            name = tn.children[0].getText()
            typing = None if tn.getChildCount() < 2 else tn.children[2].getText()
            typedNameList[name] = typing
        self.peek()['pddl:types'] = typedNameList

    # Exit a parse tree produced by pddlParser#typedNameList.
    # <name> (- <type>)? | or its list
    def exitTypedNameList(self, ctx):
        #assert ctx.getChildCount() == 1 or ctx.getChildCount() == 3, "Unexpected children count {} in {}".format(ctx.getChildCount(), toText(ctx))
        #name = ctx.children[0].getText()
        #typing = None if ctx.getChildCount() < 2 else ctx.children[2].getText()
        #self.peek()[name] = typing
        pass

    # Enter a parse tree produced by pddlParser#functionsDef.
    # ( :functions <functionList> )
    def enterFunctionsDef(self, ctx):
        assert ctx.children[1].getText() == ':functions'
        functions = []
        self.peek()['pddl:functions'] = functions
        self.push(functions)

    # Exit a parse tree produced by pddlParser#functionsDef.
    def exitFunctionsDef(self, ctx):
        functions = self.pop()
        assert type(functions) is list

    # Enter a parse tree produced by pddlParser#functionList.
    # [ <atomicFunctionSkeleton> (- <functionType>)? ]*
    def enterFunctionList(self, ctx):
        #print('functionList {}'.format(ctx.getChildCount()))
        pass

    # Exit a parse tree produced by pddlParser#functionList.
    def exitFunctionList(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#atomicFunctionSkeleton.
    # ( <functionSymbol> <typedVariableList> )
    def enterAtomicFunctionSkeleton(self, ctx):
        assert ctx.getChildCount() == 4
        functionSymbol = ctx.children[1].getText()
        parameters = []
        func = { functionSymbol : parameters }
        self.peek().append(func)
        self.push(parameters)

    # Exit a parse tree produced by pddlParser#atomicFunctionSkeleton.
    def exitAtomicFunctionSkeleton(self, ctx):
        parameters = self.pop()
        assert type(parameters) is list

    # Enter a parse tree produced by pddlParser#functionSymbol.
    def enterFunctionSymbol(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#functionSymbol.
    def exitFunctionSymbol(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#functionType.
    def enterFunctionType(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#functionType.
    def exitFunctionType(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#constantsDef.
    def enterConstantsDef(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#constantsDef.
    def exitConstantsDef(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#predicatesDef.
    # ( :predicates formula+ )
    def enterPredicatesDef(self, ctx):
        assert ctx.children[1].getText() == ':predicates'
        #print('PredicatesDef {}'.format(ctx.getChildCount()))
        predicates = []
        self.peek()['pddl:predicates'] = predicates
        self.push(predicates)
    
    # Exit a parse tree produced by pddlParser#predicatesDef.
    def exitPredicatesDef(self, ctx):
        assert ctx.children[1].getText() == ':predicates'
        predicates = self.pop()
        assert type(predicates) is list
    
    # Exit a parse tree produced by pddlParser#atomicFormulaSkeleton.
    # ( predicate typedVariable* )
    def enterAtomicFormulaSkeleton(self, ctx):
        #print(json.dumps(self.peek()))
        assert type(self.peek()) is list
        predicate = ctx.children[1].getText()
        variables = []
        formula = { predicate: variables }
        self.peek().append(formula)
        self.push(variables)

    # Exit a parse tree produced by pddlParser#atomicFormulaSkeleton.
    # ( predicate typedVariable* )
    def exitAtomicFormulaSkeleton(self, ctx):
        variables = self.pop()
        assert type(variables) is list

    # Exit a parse tree produced by pddlParser#predicate.
    # name
    def exitPredicate(self, ctx):
        #self.peek()['predicate'] = ctx.getText()
        pass

    # Exit a parse tree produced by pddlParser#typedVariableList.
    #  <VARIABLE>* singleTypeVarList*
    def exitTypedVariableList(self, ctx):
        #print("typedVariableList {} {}".format(ctx.getChildCount(), ctx.getText()))
        if ctx.children:
            variables = self.peek()
            for v in ctx.children:
                if not isNonTerm(v): #VARIABLE
                    variables.append(v.getText())
                # delgate else cases to singleTypeVarList

    # Enter a parse tree produced by pddlParser#singleTypeVarList.
    def enterSingleTypeVarList(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#singleTypeVarList.
    def exitSingleTypeVarList(self, ctx):
        #print("singleTypeVarList {} {}".format(ctx.getChildCount(), ctx.getText()))
        assert ctx.children[-2].getText() == '-'
        typing = ctx.children[-1].getText()
        
        variables = self.peek()
        for v in ctx.children[:ctx.getChildCount() - 2]:
            variables.append({ toText(v): typing })
            # delgate else cases to singleTypeVarList


    # Enter a parse tree produced by pddlParser#constraints.
    def enterConstraints(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#constraints.
    def exitConstraints(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#structureDef.
    def enterStructureDef(self, ctx):
        self.peek()['structure'] = []

    # Exit a parse tree produced by pddlParser#structureDef.
    def exitStructureDef(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#actionDef.
    # ( :action <actionSymbol> :parameters ( <typedVariableList> )
    #       <actionDefBody> )
    def enterActionDef(self, ctx):
        assert ctx.getChildCount() == 9
        actionSymbol = ctx.children[2].getText()
        action = OrderedDict()
        action['pddl:action'] = actionSymbol
        parameters = []
        action['pddl:parameters'] = parameters
        self.peek()['structure'].append(action)
        self.push(action)
        self.push(parameters)

    # Exit a parse tree produced by pddlParser#actionDef.
    def exitActionDef(self, ctx):
        action = self.pop()
        assert type(action) is OrderedDict

    # Enter a parse tree produced by pddlParser#actionSymbol.
    def enterActionSymbol(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#actionSymbol.
    def exitActionSymbol(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#actionDefBody.
    def enterActionDefBody(self, ctx):
        self.pop() # parameters
        
        idx = 0
        if idx + 1 < ctx.getChildCount() and ctx.children[idx].getText() == ':precondition':
            self.peek()['pddl:precondition'] = toText(ctx.children[idx + 1])
            idx += 2
        if idx + 1 < ctx.getChildCount() and ctx.children[idx].getText() == ':effect':
            self.peek()['pddl:effect'] = toText(ctx.children[idx + 1])
            idx += 2
    
    # Exit a parse tree produced by pddlParser#actionDefBody.
    def exitActionDefBody(self, ctx):
        #self.peek()['body'] = ctx.getText()
        pass
    
    # Enter a parse tree produced by pddlParser#precondition.
    def enterPrecondition(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#precondition.
    def exitPrecondition(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#goalDesc.
    def enterGoalDesc(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#goalDesc.
    def exitGoalDesc(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#fComp.
    def enterFComp(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#fComp.
    def exitFComp(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#atomicTermFormula.
    def enterAtomicTermFormula(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#atomicTermFormula.
    def exitAtomicTermFormula(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#term.
    def enterTerm(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#term.
    def exitTerm(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#durativeActionDef.
    # ( :durative-action <actionSymbol> :parameters ( <typedVariableList> )
    #   daDefBody )
    def enterDurativeActionDef(self, ctx):
        assert ctx.getChildCount() == 9
        actionSymbol = ctx.children[2].getText()
        action = OrderedDict()
        action['pddl:durative-action'] = actionSymbol
        parameters = []
        action['pddl:parameters'] = parameters
        self.peek()['structure'].append(action)
        self.push(action)
        self.push(parameters)

    # Exit a parse tree produced by pddlParser#durativeActionDef.
    def exitDurativeActionDef(self, ctx):
        action = self.pop()
        assert type(action) is OrderedDict

    # Enter a parse tree produced by pddlParser#daDefBody.
    # ( :duration' <durationConstraint> )?
    # ( :condition [ () | daGD ] )?
    # ( :effect [ () | <effect> ] )?
    def enterDaDefBody(self, ctx):
        self.pop() # parameters
        
        idx = 0
        if idx + 1 < ctx.getChildCount() and ctx.children[idx].getText() == ':duration':
            self.peek()['pddl:duration'] = toText(ctx.children[idx + 1])
            idx += 2
        if idx + 1 < ctx.getChildCount() and ctx.children[idx].getText() == ':condition':
            self.peek()['pddl:condition'] = toText(ctx.children[idx + 1])
            idx += 2
        if idx + 1 < ctx.getChildCount() and ctx.children[idx].getText() == ':effect':
            self.peek()['pddl:precondition'] = toText(ctx.children[idx + 1])
            idx += 2

    # Exit a parse tree produced by pddlParser#daDefBody.
    def exitDaDefBody(self, ctx):
        #self.peek()['body'] = ctx.getText()
        pass


    # Enter a parse tree produced by pddlParser#daGD.
    def enterDaGD(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#daGD.
    def exitDaGD(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#prefTimedGD.
    def enterPrefTimedGD(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#prefTimedGD.
    def exitPrefTimedGD(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#timedGD.
    def enterTimedGD(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#timedGD.
    def exitTimedGD(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#timeSpecifier.
    def enterTimeSpecifier(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#timeSpecifier.
    def exitTimeSpecifier(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#interval.
    def enterInterval(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#interval.
    def exitInterval(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#derivedDef.
    def enterDerivedDef(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#derivedDef.
    def exitDerivedDef(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#fExp.
    def enterFExp(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#fExp.
    def exitFExp(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#fExp2.
    def enterFExp2(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#fExp2.
    def exitFExp2(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#fHead.
    def enterFHead(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#fHead.
    def exitFHead(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#effect.
    def enterEffect(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#effect.
    def exitEffect(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#cEffect.
    def enterCEffect(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#cEffect.
    def exitCEffect(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#pEffect.
    def enterPEffect(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#pEffect.
    def exitPEffect(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#condEffect.
    def enterCondEffect(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#condEffect.
    def exitCondEffect(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#binaryOp.
    def enterBinaryOp(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#binaryOp.
    def exitBinaryOp(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#binaryComp.
    def enterBinaryComp(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#binaryComp.
    def exitBinaryComp(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#assignOp.
    def enterAssignOp(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#assignOp.
    def exitAssignOp(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#durationConstraint.
    def enterDurationConstraint(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#durationConstraint.
    def exitDurationConstraint(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#simpleDurationConstraint.
    def enterSimpleDurationConstraint(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#simpleDurationConstraint.
    def exitSimpleDurationConstraint(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#durOp.
    def enterDurOp(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#durOp.
    def exitDurOp(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#durValue.
    def enterDurValue(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#durValue.
    def exitDurValue(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#daEffect.
    def enterDaEffect(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#daEffect.
    def exitDaEffect(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#timedEffect.
    def enterTimedEffect(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#timedEffect.
    def exitTimedEffect(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#fAssignDA.
    def enterFAssignDA(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#fAssignDA.
    def exitFAssignDA(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#fExpDA.
    def enterFExpDA(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#fExpDA.
    def exitFExpDA(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#assignOpT.
    def enterAssignOpT(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#assignOpT.
    def exitAssignOpT(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#problem.
    def enterProblem(self, ctx):
        self.isDomain = False

    # Exit a parse tree produced by pddlParser#problem.
    def exitProblem(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#problemDecl.
    # ( problem <name> )
    def exitProblemDecl(self, ctx):
        assert ctx.getChildCount() == 4
        assert ctx.children[1].getText() == 'problem'
        name = ctx.children[2].getText()
        self.peek()['problem'] = name
        # or name for 'pddl:Problem'?

    # Exit a parse tree produced by pddlParser#problemDomain.
    # ( :domain <name> )
    def exitProblemDomain(self, ctx):
        assert ctx.getChildCount() == 4
        assert ctx.children[1].getText() == ':domain'
        name = ctx.children[2].getText()
        self.peek()['pddl:problem_domain'] = name

    # Exit a parse tree produced by pddlParser#objectDecl.
    # ( :objects typedNameList )
    def exitObjectDecl(self, ctx):
        assert ctx.children[1].getText() == ':objects'
        assert ctx.getChildCount() == 4
        typedNameList = OrderedDict()
        for tn in ctx.children[2].children:
            name = tn.children[0].getText()
            typing = None if tn.getChildCount() < 2 else tn.children[2].getText()
            typedNameList[name] = typing
        self.peek()['pddl:objects'] = typedNameList


    # Enter a parse tree produced by pddlParser#init.
    def enterInit(self, ctx):
        assert not self.isDomain
        assert ctx.getChildCount() > 1, "Unexpected count {}".format(ctx.getChildCount())
        assert ctx.children[1].getText() == ':init'
        init = []
        self.peek()['pddl:init'] = init
        self.push(init)
        # delegates to InitEl

    # Exit a parse tree produced by pddlParser#init.
    # ( :init <initEl>* )
    def exitInit(self, ctx):
        init = self.pop()
        assert type(init) is list
        #self.peek()['pddl:init'] = toText(ctx.children[2])

    # Exit a parse tree produced by pddlParser#initEl.
    def exitInitEl(self, ctx):
        self.peek().append(toText(ctx))

    # Enter a parse tree produced by pddlParser#nameLiteral.
    def enterNameLiteral(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#nameLiteral.
    def exitNameLiteral(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#atomicNameFormula.
    def enterAtomicNameFormula(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#atomicNameFormula.
    def exitAtomicNameFormula(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#goal.
    # ( :goal goalDesc )
    def exitGoal(self, ctx):
        assert ctx.getChildCount() == 4
        assert ctx.children[1].getText() == ':goal'
        self.peek()['pddl:goal'] = toText(ctx.children[2])

    # Enter a parse tree produced by pddlParser#probConstraints.
    def enterProbConstraints(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#probConstraints.
    def exitProbConstraints(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#prefConGD.
    def enterPrefConGD(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#prefConGD.
    def exitPrefConGD(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#metricSpec.
    def enterMetricSpec(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#metricSpec.
    def exitMetricSpec(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#optimization.
    def enterOptimization(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#optimization.
    def exitOptimization(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#metricFExp.
    def enterMetricFExp(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#metricFExp.
    def exitMetricFExp(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#conGD.
    def enterConGD(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#conGD.
    def exitConGD(self, ctx):
        pass


    # Enter a parse tree produced by pddlParser#name.
    def enterName(self, ctx):
        pass

    # Exit a parse tree produced by pddlParser#name.
    def exitName(self, ctx):
        pass


def parse(pddlfile):
    # domain
    inp = antlr4.FileStream(pddlfile)
    lexer = pddlLexer(inp)
    stream = antlr4.CommonTokenStream(lexer)
    parser = pddlParser(stream)
    return parser.pddlDoc()


class GeneralHandler:
    def __init__(self, out):
        self.out = out
    
    def handleTree(self, tree):
        if isNonTerm(tree):
            self.out.write('{')
            self.out.write('{0} '.format(tree.getRuleIndex()))
            for child in tree.children:
                self.handleTree(child)
            self.out.write('}')
        else:
            self.out.write('"{0}"'.format(tree.getText()))

def main():
    ap = argparse.ArgumentParser(description='Convert PDDL to Json (or YAML).')
    ap.add_argument('input_pddl_file',
                    help='input PDDL')
    ap.add_argument('--yaml', action='store_true', default=False,
                    help='output YAML instead of JSON')
    args = ap.parse_args()
    doc = parseAsJson(args.input_pddl_file)
    if args.yaml:
        print(yaml.dump(dict(doc), default_flow_style=False, indent=4))
    else:
        print(json.dumps(doc, indent=True))


#
# The Parser API
def parseAsJson(input_file):
    """Return a jsonized PDDL for a given file"""
    
    tree = parse(input_file)
    visitor = Pddl2JsonVisitor()
    antlr4.ParseTreeWalker().walk(visitor, tree)
    return visitor.result
        

if __name__ == '__main__':
    main()
