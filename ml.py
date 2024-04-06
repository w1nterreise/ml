import re
from enum import Enum
from itertools import groupby
from sys import argv




class TokenType(Enum):
    def __str__(self):
        return self.name
    
tokenType = TokenType('tokenType',  ['MAIN', 'ID', 'EQ', 'CONST', 'STR', 'NUM', 'LB', 'RB', 'ENDL', 'SPACE'])


class Token:

    TOKEN_REGEX = [(    r'main'                     ,tokenType.MAIN      ),
                   (    r'[a-zA-Z_][a-zA-Z0-9_]*'   ,tokenType.ID        ),
                   (    r'[а-яА-Я_][а-яА-Я0-9_]*'   ,tokenType.ID        ),
                   (    r'='                        ,tokenType.EQ        ),
                   (    r'\$'                       ,tokenType.CONST     ),
                   (    r'"([^"]|\n)*"'             ,tokenType.STR       ),
                   (    r'-?[0-9]+'                 ,tokenType.NUM       ),
                   (    r'\('                       ,tokenType.LB        ),
                   (    r'\)'                       ,tokenType.RB        ),
                   (    r'\n'                       ,tokenType.ENDL      ),
                   (    r'[ \t]*[\n]+'              ,tokenType.ENDL      ),                 
                   (    r'[ \t]+'                   ,tokenType.SPACE     )]


    def __init__(self, token_type, token_value, position):
        self.token_type = token_type
        self.token_value = token_value
        self.position = position


    def __repr__(self):
        return f"{self.token_type} {str(self.token_value).strip()}"


    def __eq__(self, other):
        if [self.token_type, other.token_type] == [tokenType.SPACE] * 2: return True
        if [self.token_type, other.token_type] == [tokenType.ENDL] * 2: return True
        if self.token_type != other.token_type: return False
        return self.token_value == other.token_value




class Lexer:

    def __remove_comments(text):
            return re.sub(r'`.*?`', ' ', text)


    def read_program(text):
        token_list = []
        position = 0
        program = Lexer.__remove_comments(text)

        def match_token(pattern, token_type):
            nonlocal position

            match = re.match(pattern, program[position:])
            if match:
                token_value = match.group(0)
                if token_type is tokenType.STR: token_value = token_value.strip('\"')
                token_list.append(Token(token_type, token_value, position))
                position += match.end()
                return True
            return False

        while position < len(program):
            if not any(match_token(pattern, token_type) for pattern, token_type in Token.TOKEN_REGEX):
                raise SyntaxError(f"поз. {program[position]}: неизвестный токен")

        return token_list
       

class Expression:

    def __init__(self, head, body):
        self.head = head
        self.body = body


    def equals(self, another_expr):
        if self.head.token_value != another_expr.head.token_value:
            return False
        if len(self.body) != len(another_expr.body):
            return False
        return all(a.token_value == b.token_value for a, b in zip(self.body, another_expr.body))

   
    def __repr__(self):
        return super().__repr__() + f" = {self.head} : {self.body}"


class Function:
    def __init__(self, name, body, params):
        self.name = name
        self.body = body
        self.params = params


class Constant:
    def __init__(self, name, value):
        self.name = name
        self.value = value

       
class Entry(Expression):
    pass




class Basics:
        
    def equals(args): return all([a == args[0] for a in args[1:]])        
    
    def read(x):
        a = input(x[0])
        return int(a) if a.isdigit() else a
    
    def summ(args): return sum(args) if all([type(a) is int for a in args]) else ''.join([str(a) for a in args])
    
    def iff(args): return args[1] if args[0] else args[2]
    
    def write(args):
        print(args[0])
        return args[1]
    
    def writurn(args):
        print(args[0])
        return args[0]
    
    def select(args):
        n = args[0]
        for i in range(2, len(args), 2):
            if args[i] == n:
                return args[i + 1]
        return args[1]
    



class Parser:
      
    basics = {
        "read" : Basics.read,
        "sum" : Basics.summ,
        "eq" : Basics.equals,
        "write" : Basics.write,
        "writurn" : Basics.writurn,
        "if" : Basics.iff,
        "select" : Basics.select      
        }  

    __scope = {}
    __program = []
    __consts = {}
    __entry_point = None


    def __catch(message):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    raise SyntaxError(f"{args[0][0]} поз. {args[0][0].position}: {message}. {e}")
            return wrapper
        return decorator


    def __initialize():
        Parser.__scope.clear()
        Parser.__program.clear()
        Parser.__consts.clear()
        Parser.__entry_point = None


    @__catch(message="не удалось выполнить редуцирование программы")
    def try_reduce_program(token_list):
        Parser.__initialize()
        for code_line in Parser.split_tokens(token_list, tokenType.ENDL):
            Parser.__program.append(Parser.__parse(code_line))
        Parser.__place_consts()
        return Parser.__reduce_expression(Parser.__entry_point)


    def __place_consts():
        for code_line in Parser.__program:
            if code_line is None:
                continue

            if isinstance(code_line, Constant):
                continue

            for i in range(len(code_line.body)):
                token = code_line.body[i]
                if token.token_type is tokenType.ID and token.token_value in Parser.__consts:
                    value = Parser.__consts[token.token_value]
                    token_type = tokenType.NUM if value.isdigit() else tokenType.STR
                    code_line.body[i] = Token(token_type, int(value) if token_type is tokenType.NUM else value, token.position)

    
    def __parse(tokens):
        parse = {tokenType.CONST : Parser.__try_parse_const,
                 tokenType.MAIN  : Parser.__try_parse_entrypoint,
                 tokenType.ID    : Parser.__try_parse_function,
                 tokenType.SPACE : lambda _ : None}
        return parse[tokens[0].token_type](tokens)
    

    def __filter_spaces(tokens): return list(filter(lambda x: x.token_type is not tokenType.SPACE, tokens))


    @__catch(message="неверно определена константа")
    def __try_parse_const(tokens):
        constant = Constant(tokens[1].token_value, tokens[3].token_value)
        Parser.__consts[constant.name] = constant.value
        return constant


    @__catch(message="ошибка в определении функции")
    def __try_parse_function(tokens):
        declaration, definition = map(Parser.__filter_spaces, Parser.split_tokens(tokens, tokenType.EQ))
        name, *params = declaration
        function = Function(name=name, body=definition, params=params)
        Parser.__scope[name.token_value] = function
        return function


    @__catch(message="не удалось установить точку входа")
    def __try_parse_entrypoint(tokens):
        if Parser.__entry_point is not None:
            raise SyntaxError(f"поз. {tokens[0].position}: повторное определение точки входа")
        
        _, definition = Parser.split_tokens(tokens, tokenType.EQ)        
        head, *body = [x for x in definition if x.token_type is not tokenType.SPACE]

        entry = Entry(head, body)
        Parser.__entry_point = entry
        return entry


    def parse_expression(tokens):
        head, *body = tokens
        return Expression(head, body)
        

    def parse_args(tokens):
        level = 0
        parsed_args = []
        sub = []
    
        for token in tokens:
            if token.token_type is tokenType.LB:
                level += 1
            elif token.token_type is tokenType.RB:
                level -= 1    
            
            sub.append(token)
            
            if level == 0:
                parsed_args.append(sub[1:-1])
                sub = []
        
        return parsed_args

   
    def __reduce_expression(entry : Expression):
        e = entry
        while (True):
            y = Parser.__reduce_helper(e)
            if y.equals(e):
                return y;
            e = y
    
    
    def __reduce_helper(expression : Expression):
        result = expression
        if expression.head.token_value in Parser.__scope:
            result = Parser.__subtitution(expression, Parser.__scope[expression.head.token_value])
        else:
            for token in expression.body:
                if token.token_value in Parser.__scope:
                    begin = expression.body.index(token)
                    end = begin
                    level = 0
                    while (True):
                        end += 1
                        if expression.body[end].token_type is tokenType.LB:
                            level += 1
                        if expression.body[end].token_type is tokenType.RB:
                            level -= 1
                        if level < 0:
                            break

                    subexpression_for_reduce = expression.body[begin:end]
                    parsed = Parser.parse_expression(subexpression_for_reduce)
                    reduced = Parser.__subtitution(parsed, Parser.__scope[token.token_value])
                    tokenize = [reduced.head]+reduced.body
                    reduced_body = expression.body[:begin] + tokenize + expression.body[end:]
                    result = Expression(expression.head, reduced_body)    
        return result


    def __subtitution(expression : Expression, function : Function) -> Expression:
            head, *new_expression = function.body
            args = Parser.parse_args(expression.body)
            repl = {}
            for x in range(len(new_expression)):
                for y in function.params:
                    if y.token_value == new_expression[x].token_value:
                        repl[x] = args[function.params.index(y)]

            ret = [repl[i] if i in repl else [new_expression[i]] for i in range(len(new_expression))]
            flatten = [i for s in ret for i in s]
            return Expression(head, flatten)   


    def split_tokens(ls, separator):
        return [list(group) for k, group in groupby(ls, lambda x: x.token_type is separator) if not k]




class Node:

    def __init__(self, expression : Expression):
        self.function = expression.head
        self.params = expression.body
        self.branches = []
   
   
    def expand(self):
        self.branches = [Node(Parser.parse_expression(x)) for x in Parser.parse_args(self.params)]
        for b in self.branches:
            b.expand()


    def check(self):
        token_type = self.function.token_type
        token_value = self.function.token_value
        result = False
        if token_type in [tokenType.NUM, tokenType.STR]:
            result = True
        else:
            if token_value in Parser.basics:
                result = True

        return result and all([n.check() for n in self.branches]) 


    def evaluate(self):              
        if self.function.token_type is tokenType.ID:
            delegate = Parser.basics[self.function.token_value]
            if len(self.branches) == 0: return delegate
            return delegate([x.evaluate() for x in self.branches])
        else:
            delegate = (lambda : str(self.function.token_value)) if self.function.token_type is tokenType.STR else (lambda : int(self.function.token_value))
            return delegate()
        

    def __repr__(self):
        ch = "".join([x.__repr__() for x in self.branches])
        repr = f"(узел {self.function}" + (f" ветви {ch})" if len(self.branches) != 0 else ")")
        return repr




class AbstractSyntaxTree:

    def expand(expr : Expression):
        node = Node(expr)
        node.expand()
        return node


    def check(root : Node):
        return root.check()


    def evaluate(root : Node):
        return root.evaluate()



        



def main(args):

    filename = args[1]
    with open(filename, mode="r", encoding="utf8") as f:
        code = f.read()

    tokens = Lexer.read_program(code)
    if '-l' in args: [[print(l, end='\t') for l in tokens], [print() for _ in range(4)]]
   
    program = Parser.try_reduce_program(tokens)
    tree = AbstractSyntaxTree.expand(program)
    if '-t' in args: [print(tree), [print() for _ in range(4)]]

    if(AbstractSyntaxTree.check(tree)):
        AbstractSyntaxTree.evaluate(tree)
    else:
        print("данная программа невычислима")




if __name__ == "__main__":
    main(args=argv)
    