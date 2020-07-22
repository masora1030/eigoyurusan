"""Main PDF module."""
import sys
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTContainer, LTTextBox, LTChar
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
import re
import urllib.request
import os
import shutil


import eigoyurusan.translate as tr
import eigoyurusan.PDFparser as pr

def translate(path, small, lang):

    # pdf path setting
    now_path = os.path.dirname(os.path.abspath(__file__))
    arXiv_id = 'XXXXXXXX'
    data_path = now_path + '/data/{}'.format(arXiv_id.replace("/", "").replace(".", ""))
    os.makedirs(data_path, exist_ok=True)
    pdf_title = ''.join([data_path, '/', arXiv_id.replace("/", "").replace(".", ""), '.pdf'])
    shutil.copy2(path, pdf_title)

    # Chapter Class
    class Chapter:
        def __init__(self, title, pagenum):
            self.title = title
            self.body = ''
            self.pagenum = pagenum

        def getPagenum(self):
            return self.pagenum

        def addBody(self, text):
            self.body += text

    # Layout Analysisのパラメーターを設定。縦書きの検出を有効にする。
    laparams = LAParams(detect_vertical=True)

    # 共有のリソースを管理するリソースマネージャーを作成。
    resource_manager = PDFResourceManager()

    # ページを集めるPageAggregatorオブジェクトを作成。
    device = PDFPageAggregator(resource_manager, laparams=laparams)

    # Interpreterオブジェクトを作成。
    interpreter = PDFPageInterpreter(resource_manager, device)

    Chapters = [Chapter('metadata', 1)]
    nowC = Chapters[-1]

    print()
    # print('-' * 30)  # 読みやすいよう区切り線を表示する。
    # print('CHAPTER LIST')
    # print('-' * 30)  # 読みやすいよう区切り線を表示する。
    with open(pdf_title, 'rb') as f:
        # PDFPage.get_pages()にファイルオブジェクトを指定して、PDFPageオブジェクトを順に取得する。
        # 時間がかかるファイルは、キーワード引数pagenosで処理するページ番号（0始まり）のリストを指定するとよい。
        for page_num, page in enumerate(PDFPage.get_pages(f)):
            interpreter.process_page(page)  # ページを処理する。
            layout = device.get_result()  # LTPageオブジェクトを取得。

            # ページ内のテキストボックスのリストを取得する。
            boxes = pr.find_textboxes_recursively(layout)

            # テキストボックスの左上の座標の順でテキストボックスをソートする。
            # y1（Y座標の値）は上に行くほど大きくなるので、正負を反転させている。
            # boxes.sort(key=lambda b: (b.x0, -b.y1))

            for box in boxes:
                pdf_text = box.get_text()
                #################### 整形処理 ####################
                pdf_text = pdf_text.replace("-\n", "") # remove hyphenation
                pdf_text = pdf_text.replace("\n", " ") # remove newliner
                pdf_text = pdf_text.replace("fig.", "fig").replace("Fig.", "Fig")
                # 3以上の長さのスペース入り連続ピリオドを圧縮
                for i in range(3, 7):
                    pdf_text = pdf_text.replace(". " * i, "...")
                pdf_text = pdf_text.replace(".. ", "..")
                # タイトルっぽいやつのピリオドスペースは消しとく
                if nowC.title not in ['References','REFERENCES']:
                    for i in range(1, 10):
                        pdf_text = re.sub('{}\. '.format(i), '{} '.format(i), pdf_text)
                # ピリオドスペースで改行
                pdf_text = pdf_text.replace(". ", ".\n")
                # どんな長さのスペースも１つのスペースに
                for i in range(1, 7):
                    pdf_text = pdf_text.replace(" " * i, " ")
                ##################################################

                # extract plane sentences
                regix_extract_plane_english = '^§?[A-Z]\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[A-Z]\.[1-9]+\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[A-Z]\.[1-9]\.[1-9]+\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+\.[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+\.[1-9]+\.[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^Abstract*|^ABSTRACT*|^Acknowledgements*|^Acknowledgments*|^ACKNOWLEDGMENTS*|^References*|^REFERENCES*|^Introduction*|^INTRODUCTION*'
                if re.findall(regix_extract_plane_english, pdf_text) and len(pdf_text) > 8:
                    # Subtitleの処理
                    nowC = Chapter(re.findall(regix_extract_plane_english, pdf_text)[0], page_num + 1)
                    Chapters.append(nowC)
                elif re.findall('^arXiv:*', pdf_text) and nowC.title not in ['References','References ','REFERENCES']:
                    arxiv_info = re.findall('^arXiv:*', pdf_text) # arxiv_infoの処理
                else:
                    if re.findall('^References*|^REFERENCES*', nowC.title):
                        # 参考文献の処理
                        pdf_text = pdf_text.replace("\n", " ")
                        # .で終わってたら改行する
                        if len(pdf_text) > 2 and pdf_text[-2] == '.':
                            pdf_text += ('\n')
                    else:
                        if len(pdf_text) < 10:
                            # 短すぎるやつは多分数式とかなので改行を消す
                            pdf_text.replace("\n", " ")
                    nowC.addBody(pdf_text)

    ### 3000文字程度毎に分割する
    def split_by_charcount(textlist, count):
        ret = ""
        while len(textlist):
            pop = textlist.pop(0) + "\n"
            if len(ret+pop) > count:
                yield ret
                ret = ""
            ret += pop
        return ret

    # 概要と導入と結論だけ早めに出しちゃう
    rets = {"結論":"", "導入":"", "概要":""}
    for c in Chapters:
        subtitle = ""
        if re.findall('Conclusion*|CONCLUSION*', c.title): subtitle="結論"
        elif re.findall('Introduction*|INTRODUCTION*', c.title): subtitle="導入"
        elif re.findall('Abstract*|ABSTRACT*', c.title): subtitle="概要"

        if subtitle:
            print('-' * 30)  # 読みやすいよう区切り線を表示する。
            print(f'[{subtitle}]')
            for texts in split_by_charcount(c.body.split('\n'), 3000):
                rets[subtitle] += tr.traslateBydeepL(texts, lang)
            print(rets[subtitle])

    # smallだったらここで打ち切り
    if small:
        print('-' * 30)  # 読みやすいよう区切り線を表示する。
        print('Thank you !')
        return

    # 本文翻訳
    print('-' * 30)  # 読みやすいよう区切り線を表示する。
    Chapters_JP = [Chapter('Abstract', 1)]
    nowC = Chapters_JP[-1]

    for c in Chapters:
        nowC = Chapter(tr.traslateBydeepL(c.title, lang), c.getPagenum())
        Chapters_JP.append(nowC)

        transtext = ""
        translated_text = ""

        transtext_list = c.body.split(sep='\n')
        ind = 0
        if c.title not in ['References','REFERENCES']:
            if re.findall('Conclusion*|CONCLUSION*', c.title): nowC.addBody(rets["結論"])
            elif re.findall('Introduction*|INTRODUCTION*', c.title): nowC.addBody(rets["導入"])
            elif re.findall('Abstract*|ABSTRACT*', c.title): nowC.addBody(rets["概要"])
            else:
                ret = ""
                for texts in split_by_charcount(c.body.split('\n'), 3000):
                    ret += tr.traslateBydeepL(texts, lang)
                nowC.addBody(ret)
        else:
            nowC.addBody(c.body)
        print('Done Translating : Chapter {}'.format(c.title))
    print('-' * 30)  # 読みやすいよう区切り線を表示する。

    # 出力作業
    # 出力用のマークダウンファイル
    en_md = open('{}/output_{}_EN.md'.format(data_path, arXiv_id.replace("/", "").replace(".", "")), 'w')
    jp_md = open('{}/output_{}_JP.md'.format(data_path, arXiv_id.replace("/", "").replace(".", "")), 'w')

    # 目次マーカー付与
    en_md.write('[TOC]\n\n')
    jp_md.write('[TOC]\n\n')

    # 英語本文
    for c in Chapters:
        if len(c.title) > 1 and c.title[1] == '.':
            en_md.write(''.join(['### ', c.title, ' --------- P.{}'.format(c.pagenum)]))
        else:
            en_md.write(''.join(['## ', c.title, ' --------- P.{}'.format(c.pagenum)]))
        en_md.write('\n')

        if c.title != 'References' and c.title != 'References ' and c.title != 'REFERENCES':
            for i in range(1, 30):
                c.body = re.sub('\[{}\]'.format(i), '[^{}]'.format(i), c.body)
        else:
            for i in range(1, 30):
                c.body = re.sub('\[{}\]'.format(i), '[^{}]:'.format(i), c.body)

        en_md.write(c.body.replace("\n", "<br>"))
        en_md.write('\n')

    # 訳語本文
    for c in Chapters_JP:
        if len(c.title) > 1 and c.title[1] == '.':
            jp_md.write(''.join(['### ', c.title, ' --------- P.{}'.format(c.pagenum)]))
        else:
            jp_md.write(''.join(['## ', c.title, ' --------- P.{}'.format(c.pagenum)]))
        jp_md.write('\n')

        if c.title != '参考文献':
            for i in range(1, 30):
                c.body = re.sub('\[{}\]'.format(i), '[^{}]'.format(i), c.body)
        else:
            for i in range(1, 30):
                c.body = re.sub('\[{}\]'.format(i), '[^{}]:'.format(i), c.body)
        jp_md.write(c.body.replace("\n", "<br>"))
        jp_md.write('\n')

    en_md.close()
    jp_md.close()

    # Output HTML from MarkDown
    import markdown
    md = markdown.Markdown(extensions=['admonition', 'toc', 'footnotes'])

    with open('{}/output_{}_EN.md'.format(data_path, arXiv_id.replace("/", "").replace(".", ""))) as fen:
        with open('{}/output_{}_EN.html'.format(data_path, arXiv_id.replace("/", "").replace(".", "")), 'w') as hen:
            md_en = fen.read()
            body = md.convert(md_en)
            # HTML書式に合わせる
            html = '<html lang="ja"><meta charset="utf-8"><body>'
            html += (body + '</body></html>')
            hen.write(html)

    with open('{}/output_{}_JP.md'.format(data_path, arXiv_id.replace("/", "").replace(".", ""))) as fjp:
        with open('{}/output_{}_JP.html'.format(data_path, arXiv_id.replace("/", "").replace(".", "")), 'w') as hjp:
            md_jp = fjp.read()
            body = md.convert(md_jp)
            # HTML書式に合わせる
            html = '<html lang="ja"><meta charset="utf-8"><body>'
            html += (body + '</body></html>')
            hjp.write(html)

    # htmlファイルをブラウザ表示
    import webbrowser

    jp_url = 'file://{}/output_{}_JP.html'.format(
        data_path, arXiv_id.replace("/", "").replace(".", ""))
    en_url = 'file://{}/output_{}_EN.html'.format(
        data_path, arXiv_id.replace("/", "").replace(".", ""))

    webbrowser.open_new(jp_url)
    webbrowser.open_new(en_url)

    print('-' * 30)  # 読みやすいよう区切り線を表示する。
    print('Thank you !')