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

#共通の画像処理用関数
def apply_popart_filter(image,shift_value):
    #以下、画像をHSVに変換して色相(Hue)をシフト
    #1.まずRGB画像をHSVに変換
    hsv_image = image.convert('HSV')

    #2.ピクセルデータを取得
    hsv_data = hsv_image.getdata() #getdata()でimageからh,s,vを取得(タプルのリスト?らしい)

    new_data = []
    for h,s,v in hsv_data:
        #3.色相(h)をシフトさせ、0-255の範囲に収める
        new_h=(h+shift_value)%256
        new_data.append((new_h,s,v))
    
    #4.新しいピクセルデータを画像に適用
    hsv_image.putdata(new_data)

    #5.HSV画像を再びRGBに変換して返す
    return hsv_image.convert("RGB")

def apply_mosaic_filter(image,level):
    #画像を収縮・拡大してモザイクを書ける処理
        original_width,original_height = image.size #画像の元のサイズを取得
        #新しいサイズを設定
        new_width = original_width // level
        new_height = original_height // level
        #画像を縮小してモザイク効果を作成

        #実際に収縮させる
        small_image = image.resize((new_width,new_height),Image.NEAREST)
        #NEARESTは最近傍補間法で、画像を縮小する際に最も近いピクセルの色をそのまま使う方法

        #元のサイズに拡大
        mosaic_image = small_image.resize((original_width,original_height),Image.NEAREST)
        return mosaic_image

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
    
    mode = request.form.get('mode')
    image=Image.open(file.stream).convert("RGB") #Pillowを使って画像を開く&必ずRGBに変換してから処理を開始
    #image = Image.open(file.stream)でrequest.filesの中のfileに格納されているバイトデータを画像として扱えるようimageオブジェクトに格納している
    #file.streamはrequest.filesから取得したファイルデータの中身そのものを指す(ストリームオブジェクト・バイトデータを読み書きするためのインタフェース)
    #streamってのはファイル全体を一度にメモリに書き込むのではなく、必要な部分を少しずつ読み書きするための仕組み.データが時間の経過とともに連続的に流れるように扱われる概念のこと


    #request.formで受け取れるのは テキスト入力欄、ラジオボタン、スライダー、チェックボックスなどの非ファイルのデータ。
    #request.filesで受け取れるのは ファイル入力欄からアップロードされたファイルデータ。
    #request.form.get('mode')でindex.htmlのinputタグのname属性で指定したmodeの値を取得している
    if mode=='mosaic':
        try: #パラメータの取得と例外処理
            level=int(request.form.get('mosaic_level',10))
            if level < 2 or level > 50:
                level=10
        except ValueError:
            level=10
        
        processed_image = apply_mosaic_filter(image,level)
    
    elif mode=='popart':
        try:
            shift=int(request.form.get('hue_shift',100))
            if shift < 0 or shift > 255:
                shift=100
        except ValueError:
            shift=100
        
        processed_image=apply_popart_filter(image,shift)
    
    else:#例外処理。modeがmosaicでもpopartでもない場合は元の画像を返す
        processed_image=image

    #処理後の画像をメモリ上にpng形式で保存
    img_io = io.BytesIO() #メモリ上にバイナリデータを扱うためのオブジェクトを作成
    #io.BytesIO()がコンピュータのメモリ上に仮想的なファイルを作るためのメソッドで、img_ioはその仮想ファイルを指す変数(一時的な保存場所)
    processed_image.save(img_io, 'PNG') #画像をPNG形式で保存
    #処理でいじったimageオブジェクトをimage_ioというメモリ上の仮想ファイルにPNG形式で保存
    img_io.seek(0) #ファイルポインタを先頭に戻す
    #imageで色々いじったからストリーム(データの流れ=ファイルポインタ)が最後まで行ってしまっているので、ブラウザに送り返す時にデータが見つからないことを防ぐためseek(0)でポインタを先頭に戻している


    #メモリ上のデータをブラウザに送り返す
    return send_file(img_io,mimetype='image/png')
    #mimetypeの所で今から送るファイルがpng形式の画像ですよと知らせる。
    #このmimetypeを指定しないと、ブラウザ側が送られてきたデータを単なるバイナリデータとして表示しようとするらしい


if __name__ == '__main__':  #このファイルが直接実行された時のみwebサーバーを起動する
    app.run(debug=True)

