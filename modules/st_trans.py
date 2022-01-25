from dolittle_to_python import translate
from re import compile, finditer
import failInfo

def assign_trans(li, recog, indent_num):
    return ' '.join([x for x in li]) + "\n"

# _if  = Group('[' + _cond + ']' + '!' + _IF + _block + '実行') + '.'
def if_trans(li, recog, indent_num):
    
    condition = li[1]
    blockStmt = li[6]
 
    st = "if " + condition + ":\n"
    st += translate(blockStmt, recog, indent_num+1)
    
    return st

# _ifelse = Group('[' + _cond + ']' + '!' + _IF + _block + _ELSE + _block + '実行') + '.'
def ifelse_trans(li, recog, indent_num):
    condition = li[1]
    blockStmtIf = li[6]
    blockStmtElse = li[10]
 
    st = "if " + condition + ":\n"
    st += translate(blockStmtIf, recog, indent_num+1)
    st += "else:\n"
    st += translate(blockStmtElse, recog, indent_num+1)
    
    return st

# _for = Group('[' + ZeroOrMore('|' + _VARIABLE + '|') + _blockWithOutBracket + ']' + '!' + (_expr) + '繰り返す') + '.'
def for_trans(li, recog, indent_num):
    blockStmt = li[2]
    # インデックスがあるか/ないかで処理を変える
    if len(li[1]) > 0:
        iterateVar = li[1][1]
    else:
        iterateVar = 'i'
    iterateTimes = li[5]

    st = "for " + iterateVar + " in range(1," + iterateTimes + "+1):\n"
    st += translate(blockStmt, recog, indent_num+1)
    return st

# _while = Group('[' + _cond + ']' + '!' + 'の間' + _block + '実行') + '.'
def while_trans(li, recog, indent_num):
    condition = li[1]
    blockStmt = li[6]
 
    st = "while " + condition + ":\n"
    st += translate(blockStmt, recog, indent_num+1)
    
    return st

def print_trans(li, recog, indent_num):
    print_arg = li[2]
    # 文字列subjectの中にある変数名・数値をstr()で覆った文にして返すローカル関数
    # subjectの中に文字列リテラルが無いことを前提としている
    def cover_var_or_num_with_strcast(subject):
        reg = r'[ぁ-んァ-ヶｱ-ﾝ一-龠a-zA-Z][ぁ-んァ-ヶｱ-ﾝ一-龠0-9a-zA-Z]*|[\-][ ]?([1-9]\d*|0)(\.\d+)?|([1-9]\d*|0)(\.\d+)?'
        var_num_pattern = compile(reg)
        var_num_bound_list = [m.span() for m in finditer(var_num_pattern, subject)]
        
        offset = 0
        for (match_bound) in (var_num_bound_list):
            start = match_bound[0] + offset
            stop = match_bound[1] + offset
            subject = subject[:start] + "str(" + subject[start:stop] + ')' + subject[stop:]
            offset += 5
        return subject
    
    # 量指定子(+ * ?など)はデフォルトでは最長マッチをするgreedy match
    # 量指定子の後に?を付けることでnon-greedy matchにできる
    str_pattern = compile(r'".*?"|\'.*?\'')
    str_bound_list = [m.span() for m in finditer(str_pattern, print_arg)]
    l = len(str_bound_list)
    
    if l > 0:
        result = ""
        
        # 文字列リテラル[0]の前を処理
        first_start = str_bound_list[0][0]
        result += cover_var_or_num_with_strcast(print_arg[:first_start])
        
        # 文字列リテラル[0]以降から文字列リテラル[l-1]の前を処理
        for i in range(l-1):
            start = str_bound_list[i][0]
            stop = str_bound_list[i][1]
            
            start2 = str_bound_list[i+1][0]
            
            result += print_arg[start:stop]
            result += cover_var_or_num_with_strcast(print_arg[stop:start2])
        
        # 文字列リテラル[l-1]を処理
        last_start = str_bound_list[l-1][0]
        last_stop = str_bound_list[l-1][1]
        result += print_arg[last_start:last_stop]
        result += cover_var_or_num_with_strcast(print_arg[last_stop:])
        
        print_arg = result

    return "print(" + print_arg + ")\n"

def list_trans(li, recog, indent_num):
    variable = li[0]
    arg = li[4]
    
    st = variable + '=' + '[' + ','.join(arg) +  "]\n" 
    return st

def foreach_trans(li, recog, indent_num):
    
    iterateVar = li[4]
    blockStmt = li[6]
    iterateArray = li[0]

    st = "for " + iterateVar + " in " + iterateArray + ":\n"
    st += translate(blockStmt, recog, indent_num+1)
    
    return st

def define_func_trans(li, recog, indent_num):
    func_name = li[0]
    block_stmt = li[6]
    
    param_list = li[4]
    
    st = "def " + func_name + '(' + ','.join(param_list) + "):\n"
    st += translate(block_stmt, recog, indent_num+1)
    return st

def call_func_trans(li, recog, indent_num):
    func_name = li[0]
    actual_arg_list = li[2]
    
    st = func_name + '(' + ','.join(actual_arg_list) + ')\n'
    return st

def call_func_assign_trans(li, recog, indent_num):
    assign_name = li[0] 
    func_name = li[2]
    actual_arg_list = li[4]
    
    st = assign_name + '=' + func_name + '(' + ','.join(actual_arg_list) + ')\n'
    return st

def return_trans(li, recog, indent_num):
    variable = li[0]
    st = "return " + variable + "\n"
    return st

def list_overwrite_trans(li, recog, indent_num):
    list_name = li[0]
    index = li[2]
    element = li[3]
    st = list_name + '[' + index + " - 1" + "] = " + element + "\n"
    return st

def list_push_trans(li, recog, indent_num):
    list_name = li[0]
    element = li[2]

    st = list_name + ".append(" + element + ")\n"
    return st

def system_stmt_process(li, recog, indent_num):
    failInfo.isFailed = True
    failInfo.failStatement += '翻訳は「' + li[0] + li[1] + li[2] + "」に対応していません\n"
    return "\n"

def table_stmt_process(li, recog, indent_num):
    failInfo.isFailed = True
    failInfo.failStatement += "翻訳は「テーブル」に対応していません\n"
    return "\n"

def webapi_stmt_process(li, recog, indent_num):
    failInfo.isFailed = True
    failInfo.failStatement += "翻訳は「WebAPI」に対応していません\n"
    return "\n"

def list_concat_stmt_process(li, recog, indent_num):
    failInfo.isFailed = True
    failInfo.failStatement += "翻訳は「連結」に対応していません\n"
    return "\n"

def turtle_stmt_process(li, recog, indent_num):
    failInfo.isFailed = True
    failInfo.failStatement += "翻訳は「タートル」に対応していません\n"
    return "\n"

def random_stmt_process(li, recog, indent_num):
    failInfo.isFailed = True
    failInfo.failStatement += "翻訳は「乱数」に対応していません\n"
    return "\n"