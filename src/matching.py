#!/usr/bin/python
#coding: utf-8

import pandas as pd
import re
import subprocess

root_dir = "/Users/yoshihikosuzuki/work/scirex/address-matching/"

data_dir = root_dir + "data/"
src_dir = root_dir + "src/"

lc_fname = data_dir + "listed_company"
pr_fname = data_dir + "test.csv"
#pr_fname = data_dir + "pressrelease_all.csv"
#pr_info_fname = data_dir + "pressrelease_info.csv"


def extract_address(bodysub):

    tmp_fname = "tmp.bodysub"
    with open(tmp_fname, 'w') as f:
        f.write(bodysub)
    ret = subprocess.getoutput(src_dir + "extract_address.pl " + tmp_fname).strip().split('\n')
    return set(ret[2:])


def split_address(adr):

    result = subprocess.check_output("curl http://asp.ncm-git.co.jp/eCapGCWebApi/keyword/geocode/?keyword=\"%s\"" % adr.replace(" ", "").replace("　", ""), shell = True).decode('utf-8')

    ret = []
    #print(result)
    
    def cut_at(num, r):
        import re
        pat = re.compile(r'<authorizedName index="%d">(.*?)<' % num)
        if pat.search(r):
            return pat.search(r).groups()[0]
            
    for i in range(11):
        r = cut_at(i, result)
        #if r != None:
        ret.append(r)

    #print(ret)
            
    return ret


def extract_bodysub(pr_data):

    bodysub = pr_data['bodysub']
    address_set = pr_data['address_set']

    offset_characters = 30   # 住所の位置から何文字前までの範囲で企業名を探すか

    ret = []
    for address in address_set:
        pat = re.compile(r'%s' % address)
        for match in pat.finditer(bodysub):
            start_pos = max([match.start() - offset_characters, 0])
            bodysub_part = bodysub[start_pos: match.start()]
            ret.append( (match.start(), bodysub_part, address, split_address(address)) )

    return ret


if __name__ == "__main__":

    lc_data = pd.read_table(lc_fname, sep = '\t', header = None, names = ['company_name', 'address', 'company_code'])
    pr_data = pd.read_table(pr_fname, sep = '\t', header = None, names = ['article_id', 'date', 'bodysub'])

    pr_data['bodysub'] = pr_data['bodysub'].apply(lambda x: re.sub('[ã \u3000]', '', x))   # 空白を削除
    pr_data['address_set'] = pr_data['bodysub'].apply(extract_address)   # 住所の集合を抽出
    pr_data['bodysub_part'] = pr_data.apply(extract_bodysub, axis = 1)   # 住所の直前の文字列を抽出 -> (終了位置、抽出した文字列、住所)のタプル

    # bodysub_partから企業名を検索
    
    print(pr_data[:10])
