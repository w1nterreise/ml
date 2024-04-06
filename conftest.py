import pytest




@pytest.fixture
def simple_program_without_string_literals():
    return "main    = eq (0) (sum (4) (8) (15) (16)) (23) (42)"

@pytest.fixture
def simplest_program_with_comments_and_the_same_without_them():
    return ("""
$string "hello"
`тестовый комментарий`
test_function x y = `комментарий внутри строки, который не должен влиять на список токенов` eq x y
main = if (test_function (42) (42)) (write (0) ("foo")) (write (0) ("bar"))
""", """
$string "hello"

test_function x y = eq x y
main = if (test_function (42) (42)) (write (0) ("foo")) (write (0) ("bar"))
""")

@pytest.fixture
def two_progs_for_ast_formal_check():
    return("""
f x y = sum (x) (y)
main = f (1) (2)
""",
"""
f x y = g (x) (y) (0)
main = sum (1) (f (0) (9))
""")

@pytest.fixture
def basic_monkeytest():
    return """
$hello "угадай три числа"
$result "ну вот что получилось"
$good "угадал"
$bad "не угадал"
$magic_n 42


main = out (somefunc (inp (write (hello) (n1))) (sum (inp (n2)) (magic_n)))

$n1 "введите число a: "
$n2 "введите число b: "
$n3 "введите число c: "

inp x = read (x)
h x = if (x) (good) (bad)
somefunc x y = write (result) (h (eq (sum (x) (y)) (inp (n3))))
нраавица = inp ("понравилась игра? (1=да)")
konec = write (if (eq (1) (нраавица)) ("замечательно") ("очень жаль")) (0)
out a = eq (write (a) (0)) (konec)
"""