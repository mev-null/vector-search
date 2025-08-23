# NASA APOD Vector Search API

NASAの[Astronomy Picture of the Day (APOD)](https://apod.nasa.gov/apod/astropix.html)の膨大なアーカイブから、自然言語を使って画像を検索するためのベクトル検索API。「青くて美しい星雲」や「土星の輪がはっきりと写っている写真」のような曖昧なテキストクエリで、関連する画像をセマンティック（文脈的）に検索可能。

## 特徴 (Features)

  * **自然言語検索**: キーワードだけでなく、文章の意図を理解して画像を検索します。
  * **高速な類似度検索**: `pgvector`を利用し、高次元ベクトルデータの中から類似度の高い画像を高速に特定します。
  * **コンテナ化された環境**: Docker Composeにより、依存関係を気にすることなく誰でも簡単に環境を再現・起動できます。
  * **スケーラブルな設計**: FastAPIとSQLAlchemyを採用し、クリーンでメンテナンス性の高いコードベースを維持しています。

-----

## 🛠️ 技術スタック (Tech Stack)

| カテゴリ       | 技術                                                                                             | 目的                                                           |
| :------------- | :----------------------------------------------------------------------------------------------- | :------------------------------------------------------------- |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://www.google.com/search?q=https://docs.pydantic.dev/)                 | 高パフォーマンスな非同期APIサーバー、厳密なデータ型検証             |
| **Database** | [PostgreSQL](https://www.postgresql.org/), [pgvector](https://github.com/pgvector/pgvector)     | 信頼性の高いリレーショナルDB、ベクトルデータの格納と類似度検索      |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/)                                                        | PythonオブジェクトとDBテーブルのマッピング、安全なDB操作        |
| **DB Migration** | [Alembic](https://alembic.sqlalchemy.org/en/latest/)                                             | データベーススキーマのバージョン管理                           |
| **Infrastructure** | [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/)         | アプリケーションのコンテナ化、開発環境の再現性担保           |
| **ML Model** | [Sentence-Transformers](https://www.sbert.net/)                                                  | テキストデータをベクトル（Embedding）に変換するため               |

-----

## システム構成とデータフロー

このAPIは、以下のステップでユーザーのリクエストを処理。

1.  **リクエスト受信**: ユーザーが検索したいテキスト（例: "A photo of the Earth from space"）をFastAPIのエンドポイントにPOSTします。
2.  **テキストのベクトル化**: 受け取ったテキストを`sentence-transformers`モデルを使い、意味を捉えた高次元のベクトルデータに変換します。
3.  **データベース検索**: SQLAlchemyを通じて、変換したベクトルと最も類似度が高いベクトルをPostgreSQL（pgvector）に問い合わせます。pgvectorはコサイン類似度などの計算を高速に実行します。
4.  **結果の返却**: 検索結果（APODの画像URL、説明文、日付など）をFastAPIが受け取り、JSON形式でユーザーに返します。

-----

## 🚀 実行手順 (Getting Started)

### 1\. 前提条件

  * [Docker](https://www.docker.com/) と [Docker Compose](https://docs.docker.com/compose/) がインストールされていること。
  * [NASA APIキー](https://api.nasa.gov/) を取得していること。

### 2\. 環境設定

プロジェクトのルートに`.env`ファイルを作成し、以下の内容を記述します。

```.env
# PostgreSQL Database Settings
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# NASA API Key
NASA_API_KEY=YOUR_NASA_API_KEY_HERE
```

### 3\. アプリケーションの起動と初期設定

以下のコマンドを順番に実行してください。

```bash
# 1. Dockerコンテナをバックグラウンドでビルド・起動します
docker-compose up -d --build

# 2. データベースのテーブルを作成します（初回のみ）
docker-compose exec app alembic upgrade head

# 3. NASA APODから初期データを取得し、DBに投入します
# (デフォルトでは過去100日分。api/scirpts/load_data.pyで変更可能)
python api/scrpits/load_data.py
```

これで、APIサーバーが `http://localhost:8000` で起動します。
