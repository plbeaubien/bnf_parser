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
    """docstring for BNFParser"""
    def __init__(self, string, repmax=3):
        super(BNFParser, self).__init__()
        self.string = string
        self.normalize()
        self.repmax = repmax
        self.rules = dict(
            [split_on('=', rule) for rule in split_on(';', self.string)]
        )
        for x in self.rules.keys()[:1]:
            print tokenize(self.rules[x])
        self.parse()
        for x in self.rules.keys()[:1]:
            print self.rules[x]
    
    def __str__(self):
        return ' '.join(map(string.strip, self.generate(self.rules['<START>'], [])))
    
    def generate(self, tree, output=[]):
        """Traverse the tree to generate a sentence licensed by the FSG."""
        if tree.attrib.has_key('all-of'): # Conjunction
            for child in tree.children:
                self.generate(child, output)
        if tree.attrib.has_key('one-of'): # Disjunction
            chosen = random.choice(tree.children)
            self.generate(chosen, output)
        if tree.attrib.has_key('repeat'):   # Repetition
            n = random.choice(tree.attrib['repeat'])
            for i in range(n):
                for child in tree.children:
                    self.generate(child, output)
        if tree.attrib.has_key('token'):    # Terminal
            output.append(tree.attrib['token'])
            for child in tree.children:
                self.generate(child, output)
        if tree.attrib.has_key('rule'):
            for child in self.rules[tree.attrib['rule']].children:
                self.generate(child, output)
        return output

    def normalize(self):
        text = self.string
        text = re.sub('//.+', '', text) # strip comments        
        text = re.sub('\n', ' ', text) # normalize whitespace
        text = re.sub('\s+', ' ', text) # normalize whitespace
        text = re.sub(r'\s*([\|\)\(\[\]\+\*]+)\s*', r'\1', text) # normalize whitespace
        text = re.sub(r'\[', r'[(', text) # normalize whitespace
        text = re.sub(r'\]', r')]', text) # normalize whitespace
        self.string = text
    
    def parse(self, repmax=3):
        """Convert bnf to an n-ary tree via a recursive-descent parse."""
        # Instantiate a stack to keep track of each nested level
        stack = Stack()
        for lhs, rhs in self.rules.iteritems():
            root = Tree({'rule' : lhs})
            # Instantiate a tree to store the rule expansion
            current = root
            # Iterate over all tokens in the right-hand side
            for token in tokenize(rhs):
                if token =='(':   # We need to go deeper
                    temp = Tree({'all-of' : 'all-of'})
                    current.children.append(temp)
                    stack.push(current)
                    current = temp
                elif token ==')': # Kick back up a level
                    current = stack.pop()
                elif token =='[': # Repeat once or not at all
                    temp = Tree({'repeat': [0, 1]})
                    current.children.append(temp)
                    stack.push(current)
                    current = temp
                elif token ==']': # Kick back up a level
                    current = stack.pop()
                elif token == '|': # Disjunction
                    temp = Tree({'one-of' : 'one-of'})
                    child = current.children.pop()
                    current.children.append(temp)
                    temp.parent = current
                    temp.children.append(child)
                    current = temp
                elif token == ' ': # Disjunction
                    temp = Tree({'all-of' : 'all-of'})
                    child = current.children.pop()
                    current.children.append(temp)
                    temp.parent = current
                    temp.children.append(child)
                    current = temp                    
                elif token == '*': # Repeat zero or more times
                    temp = Tree({'repeat': range(0, repmax+1)})
                    temp.children = [current.children.pop()]
                    current.children.append(temp)
                    temp.parent = current            
                elif token == '+': # Repeat one or more times
                    temp = Tree({'repeat': range(1, repmax+1)})
                    temp.children = [current.children.pop()]
                    current.children.append(temp)
                    temp.parent = current
                elif re.match(r'<.+>', token):
                    current.children.append(Tree({'rule' : token}))
                else:
                    current.children.append(Tree({'token' : token}))
            self.rules[lhs] = root
        return root

class Tree(object):
    """An n-ary tree capable of storing a finite-state grammar (FSG)."""
    
    def __init__(self, attrib={}, repmax=3):
        super(Tree, self).__init__()
        self.attrib = attrib
        self.parent = None
        self.children = []

    def __str__(self):
        if self.children == []:
            return str([y for y in self.attrib.iteritems()][0][1])
        else:
            return '\n'.join([str(child) for child in self.children])
                    
def tokenize(rule):
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
            token = token + character
    if token:
        token_list.append(token)
    return token_list


def split_on(delimiter, s):
    """Split a string s based on a delimiter string."""
    from string import strip
    return map(strip, filter(None, s.split(delimiter)))
       
       
if __name__ == "__main__":

    with open('../grammars/grammar.wbnf', 'r') as fo:
        text = fo.read()

    grammar = BNFParser(text)
    for i in range(2):
        print grammar
    
#if __name__ == "__main__":
#    from sys import argv
#    from os import path
#    file_path = argv[1] # < comment this out if you want to hardcode a file path
#    # file_path = 'my_grammar.wbnf' # < uncomment this to hardcode a file path
#    if path.exists(file_path):
#        with open(file_path, 'r') as file:
#            contents = file.read()
#            contents = re.sub(r'//.+', '', contents, re.S) # strip comments
#            contents = re.sub(r'\s+', ' ', contents) # normalize whitespace
#            # parse out the rules
#            rules = split_on(';', contents)
#            rule_dict = dict([(split_on('=', rule)[0], rule) for rule in rules])
#            # partial parse of the FSG root
#            # TODO recursively parse and expand out to terminals
#            r = rules[0]
#            tree = parse(r)
#            print tree
#    else:
#        print """Usage: Provide a path to a text file containing a Backus-Naur form (BNF) grammar."""