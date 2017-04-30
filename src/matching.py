#!/usr/bin/python
#coding: utf-8

#import numpy as np
import pandas as pd
import re
import subprocess


def run_mecab(string):

    import os
    
    fname = "tmp." + str(os.getpid())
    with open(fname, 'w') as f:
        f.write(string)
    subprocess.call("mecab -O wakati -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd/ %s > out.%s" % (fname, fname), shell = True)   # MeCabがバッファが足りないと言うので標準エラー出力を排除
    #subprocess.call("mecab -O wakati %s > out.%s" % (fname, fname), shell = True)
    ret = subprocess.getoutput("head -1 out.%s | iconv -c -t UTF-8" % fname).strip().split(' ')   #  iconvでUTF-8変換できないところを排除、上に関連？
    subprocess.call("rm %s out.%s" % (fname, fname), shell = True)

    #ret_split = [x.split('\t')[0] for x in ret][:-1]
    return set(ret)


def compare_address(adr1, adr2):

    adr1_list = adr1.split(' ')
    adr2_list = adr2.split(' ')
    
    score = 0
    for i in range(9):
        if adr1_list[i] == "None" or adr2_list[i] == "None":
            continue
        elif adr1_list[i] != adr2_list[i]:
            return 0
        else:
            score = i

    return score + 1
    

def extract_date(article_id):

    pre, ddmmyyyy = article_id.strip().split('_')
    #print(article_id, pre, ddmmyyyy, ddmmyyyy[4:], ddmmyyyy[2:4], ddmmyyyy[0:2])
    return ddmmyyyy[4:] + ddmmyyyy[2:4] + ddmmyyyy[0:2]


def do_matching(pr, lc_dict, lc_list):

    #article_id = pr['article_id']
    #sentence = pr['sentence']
    #address = pr['address']

    article_id, sentence, address = pr

    #print(sentence)
    for lc in lc_list:
        if lc in sentence:
            #print("in")
            #print("hit:", lc)
            score_adr = compare_address(address, lc_dict[lc][1])
            #print(address, lc_dict[lc][1], score_adr)
            if score_adr > 1:
                #return pd.Series([article_id, extract_date(article_id), sentence, lc_dict[lc][0], address, lc_dict[lc][1], score_adr], index = ['article_id', 'date', 'sentence', 'comp_code', 'address_pr', 'add_ress_lc', 'score'])
                print('\t'.join(map(str, [article_id, extract_date(article_id), sentence, lc_dict[lc][0], lc, address, lc_dict[lc][1], score_adr])))

    #return None


if __name__ == "__main__":

    import sys
    pr_fname, lc_fname = sys.argv[1:3]

    ## プレスリリースデータから住所を抽出 -> 住所パース -> 直前20文字抽出 -> 形態素分解
    #pr_data = pd.read_table(pr_fname, sep = '\t', header = None, names = ['article_id', 'sentence', 'address'])
    #print(pr_data)
    pr_list = []
    with open(pr_fname, 'r') as f:
        for line in f:
            pr_list.append(tuple(line.strip().split('\t')))

    ## 企業名リストも同様の処理をしたかったが、MeCabによる分解はなんとも言えない感じなので、後から"株式会社"などは直接マスクするか
    #lc_data = pd.read_table(lc_fname, sep = '\t', header = None, names = ['company_code', 'company_name', 'address_list'])
    #print(lc_data)
    lc_dict = {}
    with open(lc_fname, 'r') as f:
        for line in f:
            comp_code, comp_name, adr_list = line.strip().split('\t')
            lc_dict[comp_name] = (comp_code, adr_list)

    lc_list = lc_dict.keys()
    #print(lc_set)

    #results = pd.DataFrame(columns = ('article_id', 'date', 'sentence', 'comp_code', 'address_pr', 'add_ress_lc', 'score'))

    #retults = []
    #results = pr_data.apply(lambda x: do_matching(x, lc_dict, lc_list), axis = 1)
    #results.dropna().to_csv(sys.stdout, sep = '\t', index = False)

    for pr in pr_list:
        do_matching(pr, lc_dict, lc_list)
    
    #print(results)
    #print(pr_data[:10])
