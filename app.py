from flask import Flask,render_template,request,send_file,redirect,url_for
#render_templateはHTMLファイルを読み込んでwebに表示するために使う
#requestはHTMLファイルから送信されたデータを受け取るために使う
#send_fileはサーバー側(app.py)からwebページ(HTMLファイル)の方にファイルを送信するために使う
#PillowはPythonで画像処理を行うためのライブラリ(Python Imaging Library)で、PILという名前でインポートされることが多い
#具体的には、Pythonプログラム内で画像の読み込み、相さ、保存を簡単に行えるようにする
from PIL import Image
import io #メモリ上でデータを扱うためのライブラリらしい

app = Flask(__name__)
#これを書くことでFlaskアプリがどのファイルから起動されているかを教えることができる。
#__name__で今実行されているファイル(app.py)の名前を取得している。

#トップページ
@app.route('/') 
def index():
    return render_template('index.html')

#画像の受付&返却
@app.route('/process',methods=['POST'])
def process_image():
    #ファイルがリクエストに含まれているかどうか
    if 'file' not in request.files: #'file'はindex.htmlのinputタグのname属性で指定した名前,request.filesは送信されたファイルの情報が入っている
        return redirect(url_for('index'))
    
    file = request.files['file']

    #ファイル名が空(ファイルが選択されていない)の場合
    if file.filename == '':
        return redirect(url_for('index'))
    
    #index.htmlからデータがrequest.filesに格納されて送られる→request.filesの中にfileという名前のデータがない場合またはfileはあるがその名前が空の場合はリダイレクトをしている
    
    if file: #もしfileの中身があれば…
        try: #パラメータの取得と例外処理
            mosaic_level=int(request.form.get('mosaic_level',10))
            if mosaic_level < 2 or mosaic_level > 50:
                mosaic_level=10
        except ValueError:
            mosaic_level=10
        #ここから画像処理
        image = Image.open(file.stream) #Pillowを使って画像を開く
        #image = Image.open(file.stream)でrequest.filesの中のfileに格納されているバイトデータを画像として扱えるようimageオブジェクトに格納している
        #file.streamはrequest.filesから取得したファイルデータの中身そのものを指す(ストリームオブジェクト・バイトデータを読み書きするためのインタフェース)
        #streamってのはファイル全体を一度にメモリに書き込むのではなく、必要な部分を少しずつ読み書きするための仕組み.データが時間の経過とともに連続的に流れるように扱われる概念のこと

        original_width,original_height = image.size #画像の元のサイズを取得
        #新しいサイズを設定
        new_width = original_width // mosaic_level
        new_height = original_height // mosaic_level
        #画像を縮小してモザイク効果を作成

        #実際に収縮させる
        small_image = image.resize((new_width,new_height),Image.NEAREST)
        #NEARESTは最近傍補間法で、画像を縮小する際に最も近いピクセルの色をそのまま使う方法

        #元のサイズに拡大
        mosaic_image = small_image.resize((original_width,original_height),Image.NEAREST)

        #処理後の画像をメモリ上にpng形式で保存
        img_io = io.BytesIO() #メモリ上にバイナリデータを扱うためのオブジェクトを作成
        #io.BytesIO()がコンピュータのメモリ上に仮想的なファイルを作るためのメソッドで、img_ioはその仮想ファイルを指す変数(一時的な保存場所)
        mosaic_image.save(img_io, 'PNG') #画像をPNG形式で保存
        #処理でいじったimageオブジェクトをimage_ioというメモリ上の仮想ファイルにPNG形式で保存
        img_io.seek(0) #ファイルポインタを先頭に戻す
        #imageで色々いじったからストリーム(データの流れ=ファイルポインタ)が最後まで行ってしまっているので、ブラウザに送り返す時にデータが見つからないことを防ぐためseek(0)でポインタを先頭に戻している


        #メモリ上のデータをブラウザに送り返す
        return send_file(img_io,mimetype='image/png')
        #mimetypeの所で今から送るファイルがpng形式の画像ですよと知らせる。
        #このmimetypeを指定しないと、ブラウザ側が送られてきたデータを単なるバイナリデータとして表示しようとするらしい
    return redirect(url_for('index'))

if __name__ == '__main__':  #このファイルが直接実行された時のみwebサーバーを起動する
    app.run(debug=True)

