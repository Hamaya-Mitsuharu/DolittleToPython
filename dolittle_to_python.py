import sys
import os

basepath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(basepath, 'pyparsing.zip'))
sys.path.append(os.path.join(basepath, 'colorama.zip'))
sys.path.append(os.path.join(basepath, 'jaconv.zip'))
sys.path.append(os.path.join(basepath, 'modules'))

import warnings
from tkinter import filedialog

from pyparsing import Combine, Word, alphas, ZeroOrMore, alphanums, nums, SkipTo, Literal, Suppress,\
    oneOf, Forward, Optional, Group, OneOrMore, infixNotation, opAssoc
import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

from preprocess import delete_comment, zenkaku_to_hankaku
from preprocess import japanese
import st_trans
import failInfo

dori_code = '''\
'''

def state_init():

    # --- トークンを定義 ----------------------------------
    _VARIABLE = Combine('(' + Word(alphas + japanese) + ZeroOrMore(Word(alphanums + japanese)) +
                        ')') | Combine(Word(alphas + japanese) + ZeroOrMore(Word(alphanums + japanese)))
    _CONST = Combine(Word(nums) + '.' + Word(nums)) | Word(nums)
    _STRING = Combine('"' + SkipTo('"') +
                      '"') | Combine("'" + SkipTo("'") + "'")

    def element_trans(li):
        return li[0] + '[' + li[2] + " - 1" + ']'
    _LISTELEMENT_HELPER = (_VARIABLE + '!' + _CONST + "読む") | (Suppress(
        Optional('(')) + _VARIABLE + '!' + _CONST + "読む" + Suppress(Optional(')')))
    _LISTELEMENT = _LISTELEMENT_HELPER.setParseAction(element_trans)

    def length_trans(li):
        return "len(" + li[0] + ')'
    _LENGTH = (_VARIABLE + '!' + "要素数" + '?').setParseAction(length_trans)

    _ASSIGN_VALUE = _LENGTH | _LISTELEMENT | _VARIABLE | _CONST | _STRING

    _EQ = Literal("=")
    _RTN = Literal("RETURN")
    _PM = oneOf("+ -")
    _MD = oneOf("* / %")
    _opLogic = oneOf("== != < <= > >= && ||")

    # 再帰評価
    _term = Forward()
    _factor = Forward()
    _block = Forward()
    _expr = Forward()
    recog = Forward()

    # 式、項、要素
    _expr << Combine(
        Optional(_PM) + _term +
        ZeroOrMore(_PM + _term)
    )
    _term << _factor + ZeroOrMore(_MD + _factor)
    _factor << _ASSIGN_VALUE | '(' + _expr + ')'

    # ブロック
    _block <<= ('['
                + Combine(
                    SkipTo(Word("[]"))
                    + ZeroOrMore(_block + SkipTo(Word("[]")))
                ) +
                ']')

    _blockWithOutBracket = Combine(
        SkipTo(Word("[]"))
        + ZeroOrMore(_block + SkipTo(Word("[]")))
    )
    # https://stackoverflow.com/questions/11133339/parsing-a-complex-logical-expression-in-pyparsing-in-a-binary-tree-fashion
    _condition = Combine(_expr + ZeroOrMore(_opLogic + _expr))
    _cond = Combine(infixNotation(_condition, [
        (_opLogic, 2, opAssoc.LEFT, ),
    ]))

    # 各ステートメント
    _return = _RTN + Optional(_ASSIGN_VALUE)
    _assign = Group((_LISTELEMENT | _VARIABLE) + _EQ + _expr) + '.'
    _if = Group('[' + _cond + ']' + '!' + "なら" + _block + '実行') + '.'
    _ifelse = Group('[' + _cond + ']' + '!' + "なら" +
                    _block + "そうでなければ" + _block + '実行') + '.'
    _for = Group('[' + Group(Optional('|' + _VARIABLE + '|')) + SkipTo(']' +
                 '!' + _expr + '繰り返す' + '.') + ']' + '!' + _expr + '繰り返す') + '.'
    _while = Group('[' + _cond + ']' + '!' + 'の間' + _block + '実行') + '.'
    _print = (Group("ラベル" + '!' + SkipTo(Optional('(') + _expr) + Suppress(
        Optional('(')) + _expr + Suppress(Optional(')')) + '作る' + SkipTo('.')) + '.')

    _list = Group(_VARIABLE + _EQ + "配列" + '!' +
                  Group(ZeroOrMore((_CONST | _STRING))) + "作る") + '.'
    _foreach = Group(
        _VARIABLE + '!' + '[' + '|' + _VARIABLE + '|' + _blockWithOutBracket + ']' + "それぞれ実行") + '.'

    _def_func = Group(_VARIABLE + _EQ + '[' + '|' + Group(ZeroOrMore(_VARIABLE)) + Suppress(
        Optional(';') + ZeroOrMore(_VARIABLE)) + '|' + _blockWithOutBracket + ']') + '.'
    _call_func = Group(
        _VARIABLE + '!' + Group(OneOrMore(Suppress('(') + _expr + Suppress(')'))) + "実行") + '.'
    _call_func_assign = Group(_VARIABLE + '=' + _VARIABLE + '!' + Group(
        OneOrMore(Suppress('(') + _expr + Suppress(')'))) + "実行") + '.'
    _return = Group(_ASSIGN_VALUE) + '.'

    _list_overwrite = Group(_VARIABLE + '!' + _CONST + _expr + "上書き") + '.'
    _list_push = Group(_VARIABLE + '!' + _expr + "書く") + '.'

    _system = Group(Combine("システム" + '!') + _STRING + "使う") + '.'
    _table = Group(_VARIABLE + _EQ + "テーブル" + '!' + SkipTo("作る") + "作る") + '.'
    _webapi = Group(_VARIABLE + _EQ + "webapi" + '!' + "作る") + '.'
    _list_concat = Group(_VARIABLE + _EQ + "配列" + '!' +
                         SkipTo("連結") + "連結" + SkipTo(".")) + '.'
    _turtle = Group(_VARIABLE + _EQ + "タートル" + '!' +
                    SkipTo("作る") + "作る" + SkipTo('.')) + '.'
    _random = Group("乱数" + SkipTo(".")) + '.'

    # --- ステートメントに名前付け ----------------------------
    assign_stmt = _assign.setResultsName("代入文")
    if_stmt = _if.setResultsName("IF文")
    ifelse_stmt = _ifelse.setResultsName("IF-ELSE文")
    for_stmt = _for.setResultsName("FOR文")
    while_stmt = _while.setResultsName("WHILE文")
    print_stmt = _print.setResultsName("文字を出力")

    list_stmt = _list.setResultsName("配列を作成")
    list_overwrite_stmt = _list_overwrite.setResultsName("配列の要素を上書き")
    list_push_stmt = _list_push.setResultsName("配列の末尾に要素を追加")
    foreach_stmt = _foreach.setResultsName("配列に対するFOR文")

    def_func_stmt = _def_func.setResultsName("関数定義（ドリトルでは命令定義）")
    call_func_stmt = _call_func.setResultsName("関数呼び出し")
    call_func_assign_stmt = _call_func_assign.setResultsName("関数呼び出しと代入")
    return_stmt = _return.setResultsName("Return文")

    system_stmt = _system.setResultsName("システム使用文")
    table_stmt = _table.setResultsName("テーブルの作成")
    webapi_stmt = _webapi.setResultsName("WebAPIを使用")
    list_concat_stmt = _list_concat.setResultsName("連結")
    turtle_stmt = _turtle.setResultsName("タートルの作成")
    random_stmt = _random.setResultsName("乱数")
    
    # --- 全体の認識 ------------------------------------
    # 左の方から優先して認識を行う
    recog << (list_overwrite_stmt ^ list_push_stmt ^ def_func_stmt ^ call_func_assign_stmt ^ call_func_stmt ^ while_stmt ^ foreach_stmt ^ for_stmt ^ if_stmt ^
              ifelse_stmt ^ print_stmt ^ list_stmt ^ assign_stmt ^ random_stmt ^ turtle_stmt ^ webapi_stmt ^ table_stmt ^ system_stmt ^ list_concat_stmt ^ return_stmt)
    return recog


def translate(code, recog, indent_num):
    result = ""
    for i in recog.scanString(code):
        stmt_type = [x for x in i[0].asDict()][0]

        print("  " * indent_num + '%-12s' % (stmt_type))

        # DEBUG
        if stmt_type == "条件式":
            print(i[0])

        without_dot_list = i[0][0]

        result += "  " * indent_num

        statements_dict = {
            "代入文": st_trans.assign_trans,
            "IF文": st_trans.if_trans,
            "IF-ELSE文": st_trans.ifelse_trans,
            "FOR文": st_trans.for_trans,
            "WHILE文": st_trans.while_trans,
            "文字を出力": st_trans.print_trans,
            "配列を作成": st_trans.list_trans,
            '配列の要素を上書き': st_trans.list_overwrite_trans,
            '配列の末尾に要素を追加': st_trans.list_push_trans,
            "配列に対するFOR文": st_trans.foreach_trans,
            "関数定義（ドリトルでは命令定義）": st_trans.define_func_trans,
            "関数呼び出し": st_trans.call_func_trans,
            "関数呼び出しと代入": st_trans.call_func_assign_trans,
            "Return文": st_trans.return_trans,
            "システム使用文": st_trans.system_stmt_process,
            "テーブルの作成": st_trans.table_stmt_process,
            "WebAPIを使用": st_trans.webapi_stmt_process,
            "連結": st_trans.list_concat_stmt_process,
            "タートルの作成": st_trans.turtle_stmt_process,
            "乱数": st_trans.random_stmt_process
        }

        # 関数を辞書から呼び出す
        result += statements_dict[stmt_type](without_dot_list,
                                             recog, indent_num)

    return result


def color_print(message, color):
    if color == "blue":
        print(Fore.BLUE + message)
        # print("\033[34m" + message + "\033[0m")
    elif color == "red":
        print(Fore.RED + message)
        # print("\033[31m" + message + "\033[0m")
    else:
        print("color_print():色指定を間違えています")


def main():
    # pyparsingでFutureWarningが出る。修正不可能なので非表示にする
    warnings.simplefilter('ignore', FutureWarning)

    #
    # ドリトルコードの読み込み
    #
    # グローバル変数を代わりに使う場合はこれのコメントを外す
    # global dori_code

    fileType = [('ドリトルファイル', '*.dtl')]
    dir = os.path.split(os.path.realpath(__file__))[0]
    path = filedialog.askopenfilename(filetypes=fileType, initialdir=dir)
    if path == "":
        color_print("ファイル読み込みキャンセル", "red")
        print("翻訳を中止します")
        return

    with open(path, encoding="utf-8") as f:
        dori_code = f.read()

    color_print("ドリトルコード", "blue")
    print(dori_code)

    dori_code_nocomment = ""
    for line in dori_code.splitlines():
        dori_code_nocomment += delete_comment(line) + "\n"
    # print()
    # color_print("コメントを削除", "blue")
    # print(dori_code_nocomment)

    dori_code_hankaku = zenkaku_to_hankaku(dori_code_nocomment)
    # print()
    # color_print("コードを半角に変換", "blue")
    # print(dori_code_hankaku)

    print()
    color_print("解析", "blue")
    pyCode = translate(dori_code_hankaku, state_init(), 0)

    if failInfo.isFailed:
        print()
        color_print("翻訳失敗", "red")
        print(failInfo.failStatement)
        print()
        print("翻訳を中止します")
        return

    print()
    color_print("翻訳", "blue")
    print(pyCode)

    print()
    color_print("実行", "blue")
    exec(pyCode)


if __name__ == "__main__":
    main()
