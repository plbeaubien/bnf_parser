"""An implementation of a top-down, recursive descent, Backus-Naur form (BNF) 
parser and a finite-state, BNF grammar supporting n-ary branching structures."""

__authors__ = ['Aaron Levine', 'Zachary Yocum']
__emails__  = ['aclevine@brandeis.edu', 'zyocum@brandeis.edu']

import random
from argparse import ArgumentParser
from re import match, sub
from string import strip

START = '<START>'

class BNFGrammar(object):
    """A Backus-Naur form (BNF) grammar capable of generating sentences."""
    def __init__(self, rules):
        super(BNFGrammar, self).__init__()
        self.rules = rules
        self.root = self.rules[START]
    
    def generate(self, delimiter=' '):
        """Returns a sentence licensed by the grammar as a string."""
        return delimiter.join(filter(None, self.traverse(self.root)))
    
    def traverse(self, tree):
        """Traverse the tree to generate a sentence licensed by the grammar."""
        output = []
        if tree.attributes.has_key('terminal'): # Terminal
            output.append(tree.attributes['terminal'])
        if tree.attributes.has_key('rule'):     # Rule
            output.extend(self.traverse(self.rules[tree.attributes['rule']]))
        if tree.attributes.has_key('one-of'):   # Disjunction
            child = random.choice(tree.children)
            output.extend(self.traverse(child))
        if tree.attributes.has_key('all-of'):   # Conjunction
            for child in tree.children:
                output.extend(self.traverse(child))
        if tree.attributes.has_key('repeat'):   # Repetition
            n = random.choice(tree.attributes['repeat'])
            for i in range(n):
                for child in tree.children:
                    output.extend(self.traverse(child))
        return output

class BNFParser(object):
    """A top-down, recursive descent, Backus-Naur form (BNF) parser.
    
    Given a string containing a BNF grammar, a BNFParser instance parses
    the string to construct a finite-state grammar (FSG) stored in an n-ary 
    tree."""
    def __init__(self, text, repeat_max=3):
        super(BNFParser, self).__init__()
        self.text = self.normalize_text(text)
        self.repeat_max = repeat_max
        self.rules = self.compile_rules()
        self.parse()
    
    def compile_rules(self):
        """Builds a rules dictionary of A -> B key-value pairs.
        
        The left-hand-side keys (A) are rule name strings and the 
        right-hand-side rules values (B) are rule expansion strings.
        
        The rules conform to BNF such that A is a non-terminal that expands to 
        an expansion B that is composed of terminals, non-terminals, and 
        operators."""
        rules = dict([split_on('=', rule) for rule in split_on(';', self.text)])
        for rule in rules:
            rules[rule] = self.normalize_rule(rules[rule])
        return rules
    
    def normalize_text(self, text):
        """Normalizes raw BNF by removing comments and extraneous whitespace."""
        sub_patterns = [
            (r'//.+', ''), # remove comments
            (r'\n', ''),   # removes newlines
            (r'\s+', ' ')  # normalize whitespace
        ]
        for pattern, substitution in sub_patterns:
            text = sub(pattern, substitution, text)
        return text
    
    def normalize_rule(self, rule):
        """Normalizes raw BNF rules (i.e., the right-hand side of a rule) in 
        preparation for parsing by removing extraneous whitespace and wrapping 
        terminals and rule expansions with parentheses."""
        substitutions = [
            (r'\s*\|\s*', '|'),  # remove whitespace before and after |
            (r'([^()\[\]|*+\s]+)', r'(\1)'), # wrap terminals/rules with ()
            (r'([\])]+)\s+([\])]+)', r'\1\2'), # remove extraneous whitespace
            (r'([\[(]+)\s+([\[(]+)', r'\1\2'),
            (r'\]', r'])'), # ensure wrapping of non-terminals and optionals
            (r'\[', r'(['),
            (r'>', r'>)'),
            (r'<', r'(<'),
        ]
        for pattern, substitution in substitutions:
            rule = sub(pattern, substitution, rule)
        return rule
    
    def tokenize(self, rule):
        """Tokenizes normalized Backus-Naur Form (BNF) content."""
        operators = '()[]|+* '
        token_list = []
        token = ''
        for character in rule:
            if character in operators:
                if token:
                    token_list.append(token)
                token_list.append(character)
                token = ''
            else:
                token += character
        if token:
            token_list.append(token)
        return token_list

    def parse(self):
        """Convert BNF to an n-ary tree via a recursive-descent parse."""
        # Instantiate a stack to keep track of each nested level
        stack = Stack()
        for lhs, rhs in self.rules.iteritems():
            # Instantiate a tree to store the rule expansion
            root = Tree({'all-of' : None})
            stack.push(root)
            current = root
            # Iterate over all tokens in the right-hand side
            for token in self.tokenize('(' + rhs + ')'):
                if token == '(':                # We need to go deeper
                    temp = Tree({'all-of' : None})
                    current.children.append(temp)
                    temp.parent = current
                    stack.push(temp)
                    current = temp
                elif token == ')':              # Kick back up a level
                    stack.pop()
                    current = stack[-1]
                elif token == '[':              # Repeat once or not at all
                    temp = Tree({'repeat': [0, 1]})
                    current.children.append(temp)
                    temp.parent = current
                    stack.push(temp)
                    current = temp
                elif token == ']':              # Kick back up a level
                    stack.pop()
                    current = stack[-1]
                elif token == '|':             # Disjunction
                    stack[-1].attributes = {'one-of' : None}
                    current = stack[-1]
                elif token == ' ':             # Conjunction
                    if current.children:
                        child = current.children.pop()
                        temp = Tree({'all-of' : None})
                        temp.parent = current
                        current.children.append(temp)
                        child.parent = temp
                        temp.children.append(child)
                        current = temp
                elif token == '*':             # Repeat zero or more times
                    child = current.children[-1]
                    temp = Tree({'repeat': range(0, self.repeat_max+1)})
                    if child.children:
                        temp.children = [child.children.pop()]
                        child.children.append(temp)
                        temp.parent = child
                    else:
                        temp.children = [child]
                        temp.parent = current
                        current.children.pop()
                        current.children.append(temp)
                elif token == '+':             # Repeat one or more times
                    child = current.children[-1]
                    temp = Tree({'repeat': range(1, self.repeat_max+1)})
                    if child.children:
                        temp.children = [child.children.pop()]
                        child.children.append(temp)
                        temp.parent = child
                    else:
                        temp.children = [child]
                        temp.parent = current
                        current.children.pop()
                        current.children.append(temp)
                elif match(r'<.+>', token):    # Rule expansion
                    current.children.append(Tree({'rule' : token}))
                else:                          # Terminal
                    current.children.append(Tree({'terminal' : token}))
            self.rules[lhs] = root
        return root

class Stack(list):
    """A simple stack wrapping the built-in list."""
    def __init__(self):
        super(Stack, self).__init__()
    
    def push(self, item):
        """Push an item onto the stack."""
        self.append(item)
    
    def is_empty(self):
        """Returns True if the stack is empty and False otherwise."""
        return not self

class Tree(object):
    """An n-ary tree capable of storing a finite-state grammar (FSG)."""
    def __init__(self, attributes={}):
        super(Tree, self).__init__()
        self.attributes = attributes
        self.parent = None
        self.children = []

def pprint(tree, i=0):
    """A method for displaying n-ary trees in human-readable form."""
    print '\t' * i + str(tree.attributes)
    for child in tree.children:
        pprint(child, i+1)

def split_on(delimiter, text):
    """Split text based on a delimiter."""
    return filter(None, map(strip, text.split(delimiter)))

if __name__ == "__main__":
    # Setup commandline argument parser
    parser = ArgumentParser()
    parser.add_argument(
        '-g',
        '--grammar',
        required=True,
        help='path to BNF grammar file'
    )
    parser.add_argument(
        '-n',
        '--number',
        default=1,
        type=int,
        help='number of sentences to generate'
    )
    parser.add_argument(
        '-r',
        '--repeat-max',
        default=2,
        type=int,
        help="maximum number of '*' and '+' expansions"
    )
    args = parser.parse_args()
    # Read the specified file's contents
    with open(args.grammar, 'r') as file:
        contents = file.read()
    # Instantiate parser and grammar
    parser = BNFParser(contents, args.repeat_max)
    grammar = BNFGrammar(parser.rules)
    # Generate and print sentences
    for i in range(args.number):
        print grammar.generate()