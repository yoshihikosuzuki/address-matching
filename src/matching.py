#!/usr/bin/python
#coding: utf-8


def run_mecab(string):   # 未使用

    import os
    import subprocess
    
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
    return ddmmyyyy[4:] + ddmmyyyy[2:4] + ddmmyyyy[0:2]


def do_matching(pr, lc_dict, lc_list):

    article_id, sentence, address = pr

    for lc in lc_list:
        if lc in sentence:
            score_adr = compare_address(address, lc_dict[lc][1])
            if score_adr > 1:
                print('\t'.join(map(str, [article_id, extract_date(article_id), sentence, lc_dict[lc][0], lc, address, lc_dict[lc][1], score_adr])))


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description="preprocess for matching using address and company names")
    parser.add_argument('listed_company', help="list of company code, company name, and parsed address")
    parser.add_argument('pressrelease', help="list of ID, pressrelease, and parsed address")
    args = parser.parse_args()

    pr_list = []
    with open(args.pressrelease, 'r') as f:
        for line in f:
            pr_list.append(tuple(line.strip().split('\t')))

    lc_dict = {}
    with open(args.listed_company, 'r') as f:
        for line in f:
            comp_code, comp_name, adr_list = line.strip().split('\t')
            lc_dict[comp_name] = (comp_code, adr_list)

    lc_list = lc_dict.keys()

    for pr in pr_list:
        do_matching(pr, lc_dict, lc_list)
