__title__ = '選定図書総目録CD-ROMのデータ変換ツール'
__copyright__ = "Copyright (C) 2023 CALIL Inc."
__author__ = "Ryuuji Yoshimoto <ryuuji@calil.jp>"

import re
import json
import click
import isbnlib
import unicodedata


def normalize_isbn(isbn):
    """
    ISBNを集約用に正規化する
    :param isbn: 文字列
    :return: isbn 文字列 / None
    """
    if not isbn:
        return None
    _isbn = unicodedata.normalize('NFKC', isbn).strip()
    _isbn = isbnlib.canonical(_isbn)
    if isbnlib.is_isbn13(_isbn) and _isbn[0:3] == '978':
        return isbnlib.to_isbn10(_isbn)
    if isbnlib.is_isbn13('978' + _isbn):
        return isbnlib.to_isbn10('978' + _isbn)
    return _isbn if isbnlib.is_isbn10(_isbn) or isbnlib.is_isbn13(_isbn) else None


def convert_jla(filename):
    """選定図書総目録CD-ROMのデータ変換"""
    vals = []
    data = open(filename, 'rb').read()
    items = re.findall(b'00000000([^\x00]+)', data)
    for item in items:
        lines = re.split(r'\$A', item.decode("cp932", "replace"))
        index = 0  # ISBN Index
        if len(lines)==1:
            print(item)
            continue
        if lines[2] == "JP$B00000000":
            index = 1
        elif lines[3] == "JP$B00000000":
            index = 2
        if index == 0:
            isbn = ""
        else:
            isbn = lines[1]
        isbn = re.sub(r'\$M([^\$]+)', r'', isbn)
        title = lines[4 + index]
        if not re.search(r"\$", lines[5 + index]):
            title += " [" + lines[5 + index] + "]"
            publisher_ = lines[6 + index]
        else:
            if not re.search(r"\$F", lines[5 + index]):
                publisher_ = lines[5 + index]
            else:
                publisher_ = lines[6 + index]
        authors = re.findall(r'\$F([^\$]+)', title)
        author = ",".join(authors)
        title = re.sub(r'\$F([^\$]+)', r'', title)
        title = re.sub(r'\$B([^\$]+)', r' \1', title)
        publisher = ",".join(re.findall(r'\$B([^\$]+)', publisher_))
        year = ",".join(re.findall(r'\$D([^\$]+)', publisher_))
        if year == "":
            year = ",".join(re.findall(r'\$D([^\$]+)', title))
        title = re.sub(r'\$D([^\$]+)', r' \1', title)
        id_ = re.split(" ", lines[3 + index])[1]
        v = {
            'id': int(id_),
            'isbn': isbn,
            'title': title,
            'author': author,
            'publisher': publisher,
            'year': year
        }
        # print(json.dumps(v, ensure_ascii=False))
        vals.append(v)
        #if len(vals) % 500 == 0:
        #    print("%d 件処理しました." % len(vals))
    #print("%d 件処理しました." % len(vals))
    return vals


@click.command()
def convert():
    """
    変換処理
    """
    data = convert_jla('JBISCS2008')
    data += convert_jla('JBISCS2013')
    data += convert_jla('JBISCS2016')
    data = sorted(data, key=lambda x: x['id'])
    chk = {}
    for item in data:
        _i = normalize_isbn(item['isbn'])
        if _i:
            if _i in chk:
                continue
            chk[_i] = 1
            print(json.dumps({
                'year': item['id'],
                'isbn': _i
            }, ensure_ascii=False))


if __name__ == '__main__':
    convert()
