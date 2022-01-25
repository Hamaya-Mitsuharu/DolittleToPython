import jaconv

def zenkaku_to_hankaku(statement):
    # 「全角パーレン」「全角演算子」「全角ドット」は半角になるが
    # 「ブラケット」「。」など半角版が存在しない記号はドリトルで使える半角にはならない 
    s = jaconv.z2h(statement, kana=False, ascii=True, digit=True)
    
    # 半角互換がない文字はこちらで変換する（日本語以外）
    checkChars = '「」。．”“×÷'
    newChars = '[]..""*/'
    for i in range(len(checkChars)):
        s = s.replace(checkChars[i], newChars[i])
    return s

def get_japanese():
    jps = ""
    hira = 'あ'
    code = ord(hira)
    while code <= ord('ん'):
        jps += hira
        code = ord(hira)
        code += 1
        hira = chr(code)
    kana = 'ア'
    code = ord(kana)
    while code <= ord('ン'):
        jps += kana
        code = ord(kana)
        code += 1
        kana = chr(code)
    kanji = '一'
    code = ord(kanji)
    while code <= ord('龠'):
        jps += kanji
        code = ord(kanji)
        code += 1
        kanji = chr(code)
    return jps

def delete_comment(line):
    index = line.find("//")
    if (index < 0):
        return line
    else:
        return line[0:index]

japanese = get_japanese() # "あいう...んアイウ...ン亜..."

