import sys
import os
import argparse
import subprocess
import tempfile
import StringIO


def redirect(commands):
    return subprocess.Popen(commands, stdout=subprocess.PIPE).communicate()[0]


def execSolver(pddl_domain, pddl_problem):
    tmpdir = tempfile.mkdtemp()
    domain_file = os.path.join(tmpdir, 'domain.pddl')
    problem_file = os.path.join(tmpdir, 'problem.pddl')
    with open(domain_file, 'w') as fd:
        fd.write(pddl_domain)
    with open(problem_file, 'w') as fd:
        fd.write(pddl_problem)
    
    output = redirect([
        '../src/3rd_party/Metric-FF-v2.1/ff',
        '-s', '0',
        '-o', domain_file,
        '-f', problem_file
    ])
    lines = output.split('\n')
    
    step_line_start = None
    step_line_end = None
    for i, line in enumerate(lines):
        if line[:len('step')] == 'step':
            step_line_start = i
        if step_line_start is not None and not line:
            step_line_end = i
            break

    if step_line_start and step_line_end:
        return [ line.split(': ')[1].split(' ') for line in lines[step_line_start:step_line_end]]
    else:
        print(output)
        raise RuntimeError('Failed in PDDL solver:\n{}'.format(output))


def prepareActions(steps, bindings):
    normSymbols = dict([(key.upper(), key) for key in bindings.keys()])
    actions = []
    for step in steps:
        symbol = normSymbols.get(step[0].upper(), step[0])
        params = [ normSymbols.get(p.upper(), p) for p in step[1:] ]
        action = { symbol: params }
        actions.append(action)
    return {
        "@context": bindings,
        "actions": actions
    }


def solve(pddl_domain, pddl_problem, bindings={}):
    steps = execSolver(pddl_domain, pddl_problem)
    return prepareActions(steps, bindings)
    

def main(args):
    actions = solve(args.domain_file.read(), args.problem_file.read(), {})
    print(actions)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Translate PDDLS to PDDL (or YAML).')
    ap.add_argument('-o', '--domain_file',
                    type=argparse.FileType('r'),
                    help='PDDL file for domain')
    ap.add_argument('-f', '--problem_file',
                    type=argparse.FileType('r'),
                    help='PDDL file for problem')
    args = ap.parse_args()
    
    main(args)
