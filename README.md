# picoRSS

picoBBS (http://say.vis.ne.jp/script/picobbs/index.htm) に投稿された記事 (のログ) を RSS 1.0 形式で配信 (出力) する Perl スクリプト (CGI) です。

## Features

* Shift_JIS で記録されている picoBBS の投稿を、RSS (1.0) で一般的に使用される UTF-8 に変換の上、XML 形式で出力します。
* 投稿の見出しだけでなく `content:encoded` に記事全文を出力します。

## Requirement

* Perl 5 以上
* Jcode モジュール (Jcode.pm)

元の Shift_JIS のまま、UTF-8 に出力を変換しないのであれば Jcode は不要

## Installation

* 行頭の `#!/usr/bin/perl` を、必要に応じ使用する環境の perl パスに合わせ修正します
* その他のオプションはスクリプト中のコメントに従い、任意に変更してください

変更後、サーバに配置したら、ファイルのパーミッションを 755 (rwxr-xr-x) または、SuEXEC 環境の場合は 700 (rwx------) に変更し、実行権限を付与してください。

## Usage

1. アップロード先の URL に、Web ブラウザおよび RSS リーダからアクセスします。設定した件数の、最新の投稿の一覧または XML が表示されることを確認してください。
2. 正常な動作を確認できたら、picoBBS 本体の define.cgi の `$HEAD_APPENDIX` に
~~~
<link rel="alternate" type="application/rss+xml" href="http://www.example.com/path/to/picorss.cgi" title="RSS 1.0">
~~~
などのように、Web ブラウザで掲示板にアクセスした際 RSS の存在がわかるよう追加するとよいでしょう。

## Author

* Written by MatsuYan
* https://twitter.com/MatsuYan
* Copyright &#169; 2006-2010 Siotex Computing Lab.
