# vector-search
Vector search API for NASA’s Astronomy Picture of the Day ([APOD](https://apod.nasa.gov/apod/astropix.html)) archive.

[Docs](https://chip-rooster-905.notion.site/253e3dc6115780eba6cdc4447a6d5417)


## 実行手順
### 環境設定ファイルの作成
プロジェクトのルートディレクトリに.envファイルを作成し、データベースの設定と，[NASA APIキー](https://api.nasa.gov/)を取得し記述します。

```.env

# PostgreSQL データベース設定
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# NASA APIキー
NASA_API_KEY=ここにあなたのNASA APIキーを記述
```
### アプリケーションの起動
Dockerコンテナをバックグラウンドでビルド・起動します。

```Bash

docker-compose up -d --build
```

### 初期データの投入
NASA APOD APIからデータを取得・ベクトル化し、データベースに保存するスクリプトを実行します。このコマンドはFastAPIサーバーが起動している状態で実行する必要があります。

```Bash

python scripts/load_data.py
```
このスクリプトは、デフォルトで過去100日分のデータを読み込みます。スクリプトを修正することで、より多くのデータを読み込むことも可能です。
