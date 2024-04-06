import pytest
import random
import ml




def test_lexer_spaces():
    assert ml.Lexer.read_program("main = sum (42) (24)") == ml.Lexer.read_program("main   =     sum   (42)     (24)")
    assert ml.Lexer.read_program("main = sum (42) (24)") != ml.Lexer.read_program("ma in = sum (42) (24)")
    assert ml.Lexer.read_program("main = write (0) (\"hello\")") != ml.Lexer.read_program("main = write (0) (\"hel lo\")")


def test_lexer_spaces_random(simple_program_without_string_literals):
    p = simple_program_without_string_literals
    def any_space_char_index(text):
        return random.choice([x for x in range(len(text)) if text[x] in [' ', '\t']])
    def any_not_space_char_index(text):
        return random.choice([x for x in range(1, len(text)) if text[x] not in [' ', '\t'] and text[x-1] not in [' ', '\t']])
    def insert (source_str, insert_str, pos):
        return source_str[:pos] + insert_str + source_str[pos:]
    
    size = 100
    arr1 = [insert(a, random.choice([' ', '\t']) * random.randint(0,4), any_space_char_index(p)) for a in [p] * size]
    arr2 = [insert(a, random.choice([' ', '\t']) * random.randint(0,4), any_space_char_index(p)) for a in [p] * size]

    arr3 = [p] * size
    arr4 = [insert(a, random.choice([' ', '\t']) * random.randint(1,4), any_not_space_char_index(p)) for a in [p] * size]

    assert [ml.Lexer.read_program(x) for x in arr1] == [ml.Lexer.read_program(x) for x in arr2]
    assert all([ml.Lexer.read_program(arr3[i]) != ml.Lexer.read_program(arr4[i]) for i in range(size - 1)])
    

def test_lexer_comments(simplest_program_with_comments_and_the_same_without_them):
    with_comments = simplest_program_with_comments_and_the_same_without_them[0]
    without_comments = simplest_program_with_comments_and_the_same_without_them[1]
    assert ml.Lexer.read_program(with_comments) == ml.Lexer.read_program(without_comments)


def test_lexer_unknown_token():
    assert ml.Lexer.read_program("main = sum (0) (1)")
    with pytest.raises(Exception) as e_info:
        assert ml.Lexer.read_program("main = :sum (0) (1)")




def test_ast_empty_lines_will_not_fail():
    assert ml.Parser.try_reduce_program(ml.Lexer.read_program("main = sum (0) (0) \n    "))

def test_ast_formal_checker(two_progs_for_ast_formal_check):
    program_that_ok = ml.Parser.try_reduce_program(ml.Lexer.read_program(two_progs_for_ast_formal_check[0]))
    tree_that_ok = ml.AbstractSyntaxTree.expand(program_that_ok)
    assert ml.AbstractSyntaxTree.check(tree_that_ok) == True

    program_that_fails = ml.Parser.try_reduce_program(ml.Lexer.read_program(two_progs_for_ast_formal_check[1]))
    tree_that_fails = ml.AbstractSyntaxTree.expand(program_that_fails)
    assert ml.AbstractSyntaxTree.check(tree_that_fails) == False


def test_base_monkeytest(basic_monkeytest, capfd, monkeypatch):
    code = basic_monkeytest

    tokens = ml.Lexer.read_program(code)
    program = ml.Parser.try_reduce_program(tokens)
    tree = ml.AbstractSyntaxTree.expand(program)

    greeting = 'угадай три числа\nну вот что получилось\n'
    pos1, neg1 = 'угадал', 'не угадал'
    pos2, neg2 = 'замечательно', 'очень жаль'

    test_cases = [(['1', '2', '45', '1'], f'{greeting}{pos1}\n{pos2}\n'),
                  (['1', '2', '45', '0'], f'{greeting}{pos1}\n{neg2}\n'),
                  (['1', '2', '46', '1'], f'{greeting}{neg1}\n{pos2}\n'),
                  (['1', '2', '46', '0'], f'{greeting}{neg1}\n{neg2}\n')] 

    for tc in test_cases:

        inputs = iter(tc[0])
        monkeypatch.setattr('builtins.input', lambda msg: next(inputs))
        ml.AbstractSyntaxTree.evaluate(tree)  
        out, err = capfd.readouterr()
        assert out == tc[1]


def test_game_monkeytest(capfd, monkeypatch):
    with open('dungeon_game', 'r', encoding='utf8') as f:
        code = f.read()

    tokens = ml.Lexer.read_program(code)
    program = ml.Parser.try_reduce_program(tokens)
    tree = ml.AbstractSyntaxTree.expand(program)

    test_cases = [(['', '', '', '2', '', '', '1', '', '', '2', '', '', '2', ''], '100'),
                  (['', '', '', '1', '', '', '1', '', '', '1', '', '', '1', ''], '150'),
                  (['', '', '', '2', '', '', '2', '', '', '2', '', '', '2', ''], '75'),
                  (['', '', '', '3', '', '', '3', '', '', '3', '', '', '3', ''], '55'),
                  (['', '', '', '4', '', '', '4', '', '', '4', '', '', '4', ''], '120'),
                  (['', '', '', '', '', '', '', '', '', '', '', '', '', ''],    '-200')]
    
    for tc in test_cases: 
        inputs = iter(tc[0])
        monkeypatch.setattr('builtins.input', lambda msg: next(inputs))
        ml.AbstractSyntaxTree.evaluate(tree)
        out, err = capfd.readouterr()
        assert out.splitlines()[-3] == tc[1]

