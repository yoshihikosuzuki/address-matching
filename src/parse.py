#!/usr/bin/python
#coding: utf-8

import os
import re
import subprocess
import pandas as pd

tmp_fname = "tmp.bodysub"
offset_characters = 40   # 住所の位置から何文字前までの範囲で企業名を探すか


def extract_address(bodysub, script_extract):

    if not os.path.isfile(script_extract):
        print("[ERROR] Script for extracting address does not exist. Please specify it by the '--script_extract' option.")
        exit()

    with open(tmp_fname, 'w') as f:
        f.write(bodysub)
    ret = subprocess.getoutput(script_extract + " " + tmp_fname).strip().split('\n')
    return set(ret[2:])


def split_address(adr):

    result = subprocess.check_output("curl http://asp.ncm-git.co.jp/eCapGCWebApi/keyword/geocode/?keyword=\"%s\"" % adr.replace(" ", "").replace("　", ""), shell = True).decode('utf-8')

    ret = []
    
    def cut_at(num, r):
        import re
        pat = re.compile(r'<authorizedName index="%d">(.*?)<' % num)
        if pat.search(r):
            return pat.search(r).groups()[0]
            
    for i in range(11):
        r = cut_at(i, result)
        ret.append(r)
            
    return ret


def extract_bodysub(pr_data, pr_out):   # プレスリリースの住所をパースして直前の文字列を抽出

    bodysub = pr_data['bodysub']
    address_set = pr_data['address_set']

    for address in address_set:
        pat = re.compile(r'%s' % address)
        for match in pat.finditer(bodysub):
            start_pos = max([match.start() - offset_characters, 0])
            bodysub_part = bodysub[start_pos: match.start()]
            pr_out.write(pr_data['article_id'] + "\t" + bodysub_part + "\t" + ' '.join(map(str, split_address(address))) + "\n")


def parse_content(lc_data, lc_out):   # 上場企業の住所をパース
    
    comp_name = lc_data['company_name']
    adr = lc_data['company_address']
    comp_code = lc_data['company_code']

    if adr != adr:
        return

    lc_out.write(str(comp_code) + "\t" + str(comp_name) + "\t" + ' '.join(map(str, split_address(adr))) + "\n")

        
if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description="preprocess for matching using address and company names")
    parser.add_argument('listed_company', help="list of listed company name, address, and company code")
    parser.add_argument('pressrelease', help="list of ID, date, and pressrelease")
    parser.add_argument('--script_extract', type=str, default="./extract_address.pl", help="script for extracting address from sentences")
    args = parser.parse_args()

    lc_fname = args.listed_company
    pr_fname = args.pressrelease
    lc_outname = lc_fname + ".parsed"
    pr_outname = pr_fname + ".parsed"
    
    ## プレスリリースデータから住所を抽出 -> 住所パース -> 住所の直前の文字列抽出
    pr_data = pd.read_table(pr_fname, sep = '\t', header = None, names = ['article_id', 'date', 'bodysub'])
    pr_data['bodysub'] = pr_data['bodysub'].apply(lambda x: re.sub('[ã \u3000]', '', x))   # 空白を削除
    pr_data['address_set'] = pr_data['bodysub'].apply(lambda x: extract_address(x, args.script_extract))   # 住所の集合を抽出
    pr_out = open(pr_outname, 'w')
    pr_data.apply(lambda x: extract_bodysub(x, pr_out), axis = 1)   # 住所の直前の文字列を抽出 -> (直前文字列の形態素セット、住所のパース)のタプル
    pr_out.close()
    
    ## 企業名リストの住所をパース
    lc_data = pd.read_table(lc_fname, sep = '\t', header = None, names = ['company_name', 'company_address', 'company_code'])
    lc_out = open(lc_outname, 'w')
    lc_data.apply(lambda x: parse_content(x, lc_out), axis = 1)
    lc_out.close()
