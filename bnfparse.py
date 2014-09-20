__authors__ = ['Aaron Levine', 'Zachary Yocum']
__emails__  = ['', 'zyocum@brandeis.edu']

import re, random, string

class Stack(list):
    """docstring for Stack"""
    def __init__(self):
        super(Stack, self).__init__()
    
    def push(self, item):
        """docstring for push"""
        self.append(item)
    
    def is_empty(self):
        """docstring for push"""
        return not self

class BNFParser(object):
    """A Backus-Naur form (BNF) recursive descent parser.
    
    Given a string containing a BNF grammar, a BNFParser instance parses
    the string to construct a finite-state grammar (FSG) stored in an n-ary 
    tree.  Once the tree is formed, sentences licensed by the grammar can 
    be generated."""
    def __init__(self, string, max_repeats=3):
        super(BNFParser, self).__init__()
        self.string = self.normalize(string)
        self.max_repeats = max_repeats
        self.rules = dict(
            [split_on('=', rule) for rule in split_on(';', self.string)]
        )
        self.parse()
    
    def __str__(self):
        return ' '.join(map(string.strip, self.generate(self.rules['<START>'])))
    
    def normalize(self, string):
        """Normalizes the raw BNF in preparation for parsing."""
        sub_patterns = [
            ('//.+', ''),                 # remove comments
            ('\n', ' '),                  # transduce newlines to spaces
            ('\s+', ' '),                 # normalize whitespace
            (r'\s*([\|\+\*]+)\s*', r'\1') # normalize spaces around operators
        ]
        for pattern, substitution in sub_patterns:
            string = re.sub(pattern, substitution, string)
        return string
    
    def tokenize(self, rule):
        """Tokenizes raw Backus-Naur Form (BNF) content."""
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
    
    def generate(self, tree):
        """Traverse the tree to generate a sentence licensed by the FSG."""
        output = []
        if tree.attrib.has_key('terminal'):   # Terminal
            output.append(tree.attrib['terminal']) 
        if tree.attrib.has_key('rule'):    # Rule
            output.extend(self.generate(self.rules[tree.attrib['rule']]))
        if tree.attrib.has_key('one-of'):  # Disjunction
            child = random.choice(tree.children)
            output.extend(self.generate(child))
        if tree.attrib.has_key('all-of'):  # Conjunction
            for child in tree.children:
                output.extend(self.generate(child))
        if tree.attrib.has_key('repeat'):  # Repetition
            n = random.choice(tree.attrib['repeat'])
            for i in range(n):
                for child in tree.children:
                    output.extend(self.generate(child))
        return output

    def parse(self):
        """Convert bnf to an n-ary tree via a recursive-descent parse."""
        # Instantiate a stack to keep track of each nested level
        stack = Stack()
        for lhs, rhs in self.rules.iteritems():
            root = Tree({'all-of' : None})
            # Instantiate a tree to store the rule expansion
            stack.push(root)
            current = root
            # Iterate over all tokens in the right-hand side
            for token in self.tokenize(rhs):
                if token =='(':                # We need to go deeper
                    temp = Tree({'all-of' : None})
                    current.children.append(temp)
                    temp.parent = current
                    stack.push(temp)
                    current = temp
                elif token ==')':              # Kick back up a level
                    stack.pop()
                    current = stack[-1]
                elif token =='[':              # Repeat once or not at all
                    temp = Tree({'repeat': [0, 1]})
                    current.children.append(temp)
                    temp.parent = current
                    stack.push(temp)
                    current = temp
                elif token ==']':              # Kick back up a level
                    stack.pop()
                    current = stack[-1]
                elif token == '|':             # Disjunction
                    stack[-1].attrib = {'one-of' : None}
                    current = stack[-1]
                elif token == ' ':             # Conjunction
                    temp = Tree({'all-of' : None})
                    temp.parent = current
                    child = current.children.pop()
                    current.children.append(temp)
                    child.parent = temp
                    temp.children.append(child)
                    current = temp
                elif token == '*':             # Repeat zero or more times
                    temp = Tree({'repeat': range(0, self.max_repeats+1)})
                    temp.children = [current.children.pop()]
                    current.children.append(temp)
                    temp.parent = current            
                elif token == '+':             # Repeat one or more times
                    temp = Tree({'repeat': range(1, self.max_repeats+1)})
                    temp.children = [current.children.pop()]
                    current.children.append(temp)
                    temp.parent = current
                elif re.match(r'<.+>', token): # Rule expansion
                    current.children.append(Tree({'rule' : token}))
                else:                          # Terminal
                    current.children.append(Tree({'terminal' : token}))
            self.rules[lhs] = root
        return root

class Tree(object):
    """An n-ary tree capable of storing a finite-state grammar (FSG)."""
    def __init__(self, attrib={}):
        super(Tree, self).__init__()
        self.attrib = attrib
        self.parent = None
        self.children = []

def pprint(tree, i=0):
    """A method for displaying n-ary trees in human-readable form."""
    print '\t' * i + str(tree.attrib)
    for child in tree.children:
        pprint(child, i+1)

def split_on(delimiter, s):
    """Split a string s based on a delimiter string."""
    from string import strip
    return map(strip, filter(None, s.split(delimiter)))

if __name__ == "__main__":
    from sys import argv
    from os import path
    # TODO use argparse to parse commandline arguments
    try:
        if len(argv) in [2, 3]:
            file_path = argv[1]
        if len(argv) in [3]:
            n = argv[2]
    except IndexError: # < comment this to hardcode values
        file_path = 'my_grammar.wbnf' # < this hardcodes a file path
        n = 10 # < this to hardcodes a number of sentences to generate
    if path.exists(file_path):
        with open(file_path, 'r') as file:
            grammar = BNFParser(file.read())
        print grammar
    else:
        print """Usage: Provide a path to a text file containing a Backus-Naur form (BNF) grammar."""