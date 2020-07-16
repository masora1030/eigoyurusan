"""Main module."""
import click
import arxiv
import sys
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTContainer, LTTextBox, LTChar
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
import re
import urllib.request
import os


import eigoyurusan.translate as tr
import eigoyurusan.PDFparser as pr

@click.command(help='Thanks to using eigoyurusan\nPlease type a command like follows.\neigoyurusan -u https://arxiv.org/abs/1912.10985v2 [-l RU --small (optional)]')
@click.option('-u', '--url', 'url', type=str, help='arXiv base url', required=True)
@click.option('-l', '--lang', 'lang', type=str, help='your language', default='JA', required=False)
@click.option('--small', is_flag=True)
def main(url, lang, small):

    if not (lang in ['JA', 'RU', 'PL', 'NL', 'IT', 'PT', 'ES', 'FR', 'DE']):
        print('Error: NOT SUPPORT LANGUAGE', file=sys.stderr)
        sys.exit(1)
    else:
        print('Mode: {}'.format(lang))

    arXiv_id = url[22:]
    result_list = arxiv.query(id_list=[arXiv_id], max_results=1)

    if len(result_list) < 1:
        print('Error: NOT FOUND PAPER', file=sys.stderr)
        sys.exit(1)
    else:
        print('Done: Found paper')

    result = result_list[0]


# Prepare paper summary

    Summary = {}
    Summary["title"] = result.title.replace("\n", " ")
    Summary["author"] = result.author
    Summary["arxiv_url"] = result.arxiv_url
    Summary["pdf_url"] = result.pdf_url
    Summary["date"] = result.updated
    Summary["abstract"] = result.summary.replace("-\n", "").replace("\n", " ").replace(". ", ".\n")

    Summary_JP = {}
    Summary_JP["title"] = tr.traslateBydeepL(result.title.replace("\n", " "), lang)
    Summary_JP["author"] = result.author
    Summary_JP["arxiv_url"] = result.arxiv_url
    Summary_JP["pdf_url"] = result.pdf_url
    Summary_JP["date"] = result.updated
    Summary_JP["abstract"] = tr.traslateBydeepL(result.summary.replace("-\n", "").replace("\n", " ").replace(". ", ".\n"), lang)


# Download PDF

    def PDFdownload(url, title):
        urllib.request.urlretrieve(url, "{0}".format(title))

    now_path = os.path.dirname(os.path.abspath(__file__))

    data_path = now_path + '/data/{}'.format(arXiv_id.replace("/", "").replace(".", ""))
    os.makedirs(data_path, exist_ok=True)
    pdf_url = result.pdf_url
    pdf_title = ''.join([data_path, '/', arXiv_id.replace("/", "").replace(".", ""), '.pdf'])
    PDFdownload(pdf_url, pdf_title)


# Correct documents in PDF

# Chapter Class
    class Chapter:
        def __init__(self, title, pagenum):
            self.title = title
            self.body = ''
            self.pagenum = pagenum
            return

        def getTitle(self):
            return self.title

        def getPagenum(self):
            return self.pagenum

        def addBody(self, text):
            self.body = ''.join([self.body, text])

        def getBody(self):
            return self.body


    # Layout Analysisのパラメーターを設定。縦書きの検出を有効にする。
    laparams = LAParams(detect_vertical=True)

    # 共有のリソースを管理するリソースマネージャーを作成。
    resource_manager = PDFResourceManager()

    # ページを集めるPageAggregatorオブジェクトを作成。
    device = PDFPageAggregator(resource_manager, laparams=laparams)

    # Interpreterオブジェクトを作成。
    interpreter = PDFPageInterpreter(resource_manager, device)

    Chapters = []
    nowC = Chapter('Abstract', 1)

    print()
    print('-' * 30)  # 読みやすいよう区切り線を表示する。
    print('CHAPTER LIST')
    print('-' * 30)  # 読みやすいよう区切り線を表示する。
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

            emp = " "
            piriod = ". "
            chainp = ".. "

            for box in boxes:

                pdf_text = box.get_text()

# 整形処理
                # タイトル入っちゃってるやつ消す
                pdf_text = pdf_text.replace(Summary["title"] + '\n', "")
                # 単語の途中で改行対処(普通の単語に直す)
                pdf_text = pdf_text.replace("-\n", "")
                # 単語の間や文末に改行消去
                pdf_text = pdf_text.replace("\n", " ")
                # figのピリオド対処
                pdf_text = pdf_text.replace("fig.", "fig").replace("Fig.", "Fig")
                # 3以上の長さのスペース入り連続ピリオドを圧縮
                for i in range(3, 7):
                    pdf_text = pdf_text.replace(piriod * i, "...")
                pdf_text = pdf_text.replace(chainp, "..")
                # タイトルっぽいやつのピリオドスペースは消しとく
                if nowC.getTitle() != 'References' and nowC.getTitle() != 'REFERENCES':
                    for i in range(1, 10):
                        pdf_text = re.sub('{}\. '.format(i), '{} '.format(i), pdf_text)
                # ピリオドスペースで改行
                pdf_text = pdf_text.replace(". ", ".\n")
                # どんな長さのスペースも１つのスペースに
                for i in range(1, 7):
                    pdf_text = pdf_text.replace(emp * i, " ")

                if re.findall(
                        '^§?[A-Z]\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[A-Z]\.[1-9]+\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[A-Z]\.[1-9]\.[1-9]+\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+\.[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+\.[1-9]+\.[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^Acknowledgements*|^Acknowledgments*|^ACKNOWLEDGMENTS*|^References*|^REFERENCES*|^Introduction*|^INTRODUCTION*',
                        pdf_text) and len(pdf_text) > 8:
                    # Subtitleの処理
                    print(pdf_text)
                    Chapters.append(nowC)
                    nowC = Chapter(re.findall(
                        '^§?[A-Z]\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[A-Z]\.[1-9]+\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[A-Z]\.[1-9]\.[1-9]+\.? [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+\.[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^§?[1-9]+\.[1-9]+\.[1-9]+ [^\+−≤≥<>∧∨=＝∈×;∇/:]+$|^Acknowledgements*|^Acknowledgments*|^ACKNOWLEDGMENTS*|^References*|^REFERENCES*|^Introduction*|^INTRODUCTION*',
                        pdf_text)[0], page_num + 1)
                elif re.findall('^arXiv:*', pdf_text) and nowC.getTitle() != 'References' and nowC.getTitle() != 'REFERENCES' and nowC.getTitle() != 'References ':
                    # arxiv_infoの処理
                    arxiv_info = re.findall('^arXiv:*', pdf_text)
                else:
                    if re.findall('^References*|^REFERENCES*', nowC.getTitle()):
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
    Chapters.append(nowC)

    # 翻訳概要表示
    # 日本語概要

    print('-' * 30)  # 読みやすいよう区切り線を表示する。
    print('日本語概要')
    for k, v in Summary_JP.items():
        print('-' * 30)  # 読みやすいよう区切り線を表示する。
        if k == 'abstract':
            print('[概要]')
            print(v)
        else:
            print('{} : {}'.format(k, v))


    # 導入と結論だけ早めに出しちゃう
    translated_text_conclusion = ''
    translated_text_introduction = ''
    for c in Chapters:
        if re.findall('Conclusion*|CONCLUSION*', c.getTitle()):
            print('-' * 30)  # 読みやすいよう区切り線を表示する。
            print('[結論]')
            transtext = ""

            transtext_list = c.getBody().split(sep='\n')
            ind = 0
            while ind < len(transtext_list):
                while ind < len(transtext_list) and len(transtext) < 3000:
                    transtext = ''.join([transtext, transtext_list[ind], '\n'])
                    ind += 1
                translated_text_conclusion = ''.join([translated_text_conclusion, tr.traslateBydeepL(transtext, lang)])
                transtext = ''
            print(translated_text_conclusion)
        elif re.findall('Introduction*|INTRODUCTION*', c.getTitle()):
            print('-' * 30)  # 読みやすいよう区切り線を表示する。
            print('[導入]')
            transtext = ""

            transtext_list = c.getBody().split(sep='\n')
            ind = 0
            while ind < len(transtext_list):
                while ind < len(transtext_list) and len(transtext) < 3000:
                    transtext = ''.join([transtext, transtext_list[ind], '\n'])
                    ind += 1
                translated_text_introduction = ''.join([translated_text_introduction, tr.traslateBydeepL(transtext, lang)])
                transtext = ''
            print(translated_text_introduction)

# smallだったらここで打ち切り
    if small:
        print('-' * 30)  # 読みやすいよう区切り線を表示する。
        print('Thank you !')
        return



# 本文翻訳
    print('-' * 30)  # 読みやすいよう区切り線を表示する。
    Chapters_JP = []
    nowC = Chapter('Abstract', 1)

    for c in Chapters:
        nowC = Chapter(tr.traslateBydeepL(c.getTitle(), lang), c.getPagenum())
        transtext = ""
        translated_text = ""

        transtext_list = c.getBody().split(sep='\n')
        ind = 0
        if c.getTitle() != 'References' and c.getTitle() != 'REFERENCES':
            if re.findall('Conclusion*|CONCLUSION*', c.getTitle()):
                nowC.addBody(translated_text_conclusion)
            elif re.findall('Introduction*|INTRODUCTION*', c.getTitle()):
                nowC.addBody(translated_text_introduction)
            else:
                while ind < len(transtext_list):
                    while ind < len(transtext_list) and len(transtext) < 3000:
                        transtext = ''.join([transtext, transtext_list[ind], '\n'])
                        ind += 1
                    translated_text = ''.join([translated_text, tr.traslateBydeepL(transtext, lang)])
                    transtext = ''
                nowC.addBody(translated_text)
        else:
            nowC.addBody(c.getBody())
        Chapters_JP.append(nowC)
        print('Done Translating : Chapter {}'.format(c.getTitle()))
    print('-' * 30)  # 読みやすいよう区切り線を表示する。

# 出力作業
    # 出力用のマークダウンファイル
    en_md = open('{}/output_{}_EN.md'.format(data_path, arXiv_id.replace("/", "").replace(".", "")), 'w')
    jp_md = open('{}/output_{}_JP.md'.format(data_path, arXiv_id.replace("/", "").replace(".", "")), 'w')

    # 目次マーカー付与
    en_md.write('[TOC]\n\n')
    jp_md.write('[TOC]\n\n')

    # 英語概要
    for k, v in Summary.items():

        for i in range(1, 30):
            v = re.sub('\[{}\]'.format(i), '\[\^{}\]'.format(i), v)
        if k == "arxiv_url" or k == "pdf_url":
            if k == "arxiv_url":
                en_md.write(''.join(['## ', 'URL']))
                en_md.write('\n')
            else:
                en_md.write('\n')
            en_md.write(''.join([k, ' : ', '[', v, ']', '(', v, ')']))
        else:
            if k == "title":
                en_md.write(''.join(['# ', v]))
            else:
                en_md.write(''.join(['## ', k]))
                en_md.write('\n')
                en_md.write(v.replace("\n", "<br>"))
        en_md.write('\n')

    # 訳語概要
    for k, v in Summary_JP.items():

        for i in range(1, 30):
            v = re.sub('\[{}\]'.format(i), '\[\^{}\]'.format(i), v)
        if k == "arxiv_url" or k == "pdf_url":
            if k == "arxiv_url":
                jp_md.write(''.join(['## ', 'URL']))
                jp_md.write('\n')
            else:
                jp_md.write('\n')
            jp_md.write(''.join([k, ' : ', '[', v, ']', '(', v, ')']))
        else:
            if k == "title":
                jp_md.write(''.join(['# ', v]))
            else:
                jp_md.write(''.join(['## ', k]))
                jp_md.write('\n')
                jp_md.write(v.replace("\n", "<br>"))
        jp_md.write('\n')

    # 英語本文
    for c in Chapters[1:]:
        if c.title[1] == '.':
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
    for c in Chapters_JP[1:]:
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

if __name__ == '__main__':
    main()