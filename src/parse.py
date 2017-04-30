#!/usr/bin/python
#coding: utf-8

#import numpy as np
import pandas as pd
import re
import subprocess

root_dir = "/Users/yoshihikosuzuki/work/scirex/ar_analysis/address-matching/"

data_dir = root_dir + "data/"
src_dir = root_dir + "src/"

lc_fname = data_dir + "listed_company_normalized"
#pr_fname = data_dir + "pressrelease_test.csv"
pr_fname = data_dir + "pressrelease_all_normalized.csv"
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
            #ret.append( (run_mecab(bodysub_part), split_address(address)) )
            print(pr_data['article_id'] + "\t" + bodysub_part + "\t" + ' '.join(map(str, split_address(address))))

    #return ret


def parse_content(lc_data):   # 上場企業の住所をパースするために最初に1回だけ使用
    
    comp_name = lc_data['company_name']
    adr = lc_data['address']
    comp_code = lc_data['company_code']

    if adr != adr:
        return

    print(str(comp_code) + "\t" + str(comp_name) + "\t" + ' '.join(map(str, split_address(adr))))   # for listed_company



if __name__ == "__main__":

    ## プレスリリースデータから住所を抽出 -> 住所パース -> 直前20文字抽出 -> 形態素分解
    pr_data = pd.read_table(pr_fname, sep = '\t', header = None, names = ['article_id', 'date', 'bodysub'])

    pr_data['bodysub'] = pr_data['bodysub'].apply(lambda x: re.sub('[ã \u3000]', '', x))   # 空白を削除
    pr_data['address_set'] = pr_data['bodysub'].apply(extract_address)   # 住所の集合を抽出
    pr_data['to_be_compared'] = pr_data.apply(extract_bodysub, axis = 1)   # 住所の直前の文字列を抽出 -> (直前30文字の形態素セット、住所のパース)のタプル

    
    ## 企業名リストも同様の処理をしたかったが、MeCabによる分解はなんとも言えない感じなので、後から"株式会社"などは直接マスクするか
    #lc_data = pd.read_table(lc_fname, sep = '\t', header = None, names = ['company_code', 'company_name', 'address_list'])
    #lc_data['to_be_compared'] = lc_data.apply(parse_content, axis = 1)
