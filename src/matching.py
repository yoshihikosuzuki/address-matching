#!/usr/bin/python
#coding: utf-8

import pandas as pd
import re
import subprocess

root_dir = "/Users/yoshihikosuzuki/work/scirex/ar_analysis/address-matching/"

data_dir = root_dir + "data/"
src_dir = root_dir + "src/"

lc_fname = data_dir + "listed_company_normalized"
pr_fname = data_dir + "pressrelease_test.csv"
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


def extract_bodysub(pr_data):

    bodysub = pr_data['bodysub']
    address_set = pr_data['address_set']

    offset_characters = 20   # 住所の位置から何文字前までの範囲で企業名を探すか

    ret = []
    for address in address_set:
        pat = re.compile(r'%s' % address)
        for match in pat.finditer(bodysub):
            start_pos = max([match.start() - offset_characters, 0])
            bodysub_part = bodysub[start_pos: match.start()]
            ret.append( (run_mecab(bodysub_part), split_address(address)) )

    return ret


def parse_content(lc_data):

    comp_name = lc_data['company_name']
    adr = lc_data['address']

    #return (run_mecab(comp_name), split_address(adr))
    print(' '.join(map(str, run_mecab(comp_name))) + "\t" + ' '.join(map(str, split_address(adr))))


if __name__ == "__main__":
    """
    ## プレスリリースデータから住所を抽出 -> 住所パース -> 直前20文字抽出 -> 形態素分解
    pr_data = pd.read_table(pr_fname, sep = '\t', header = None, names = ['article_id', 'date', 'bodysub'])

    pr_data['bodysub'] = pr_data['bodysub'].apply(lambda x: re.sub('[ã \u3000]', '', x))   # 空白を削除
    pr_data['address_set'] = pr_data['bodysub'].apply(extract_address)   # 住所の集合を抽出
    pr_data['to_be_compared'] = pr_data.apply(extract_bodysub, axis = 1)   # 住所の直前の文字列を抽出 -> (直前20文字の形態素セット、住所のパース)のタプル
    """

    ## 企業名リストも同様の処理をしたかったが、MeCabによる分解はなんとも言えない感じなので、後から"株式会社"などは直接マスクするか
    lc_data = pd.read_table(lc_fname, sep = '\t', header = None, names = ['company_name', 'address', 'company_code'])
    lc_data['to_be_compared'] = lc_data.apply(parse_content, axis = 1)

    #print(pr_data[:10])
