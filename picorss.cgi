#!/usr/bin/perl

##
 # @package picoRSS
 # @version $Id: picorss.cgi,v 1.11 2010/01/23 09:15:40 matsuyan Exp $
 # @copyright Copyright (C) 2006-2010 Siotex <https://www.siotex.com/>
 #

# --- 環境に応じ設定する項目 -----

# picoBBS 本体の define.cgi のパス
require './define.cgi';

# 出力時の MIME タイプ. デフォルトは text/xml
# 他に application/xml や application/rdf+xml など
my $CONTENT_TYPE = 'text/xml';

# フィードの文字コード. デフォルトの UTF-8 を強く推奨
# ただし Shift_JIS 以外で出力するには Jcode.pm が必須
my $CHARSET = 'UTF-8';

# フィードの概要. 500 バイト以内に収めることを推奨
my $FEED_DESCRIPTION = "$TITLEに投稿された最新の記事を配信しています";

# 掲示板の URI. http(s):// から始める
my $BBS_URI = "http://www.example.com/~username/cgi-bin/picobbs.cgi";

# 管理者メール アドレス出力の有無. 出力するなら 1 に
# spam 防止の観点からはデフォルトの 0 を推奨
my $DISPLAY_MAIL = 0;

# 配信する新着記事の最大数. デフォルトは掲示板の表示数と同じ
my $DISPLAY_ARTICLES = $VIEW_CNT_MAX;

# UTC からの時差. 日本時間を基準とするならデフォルトの +09:00
my $TZ = '+09:00';

# --------------------------------

binmode(STDOUT);
my $output = '';
my $items = <<'EOT';
		<admin:generatorAgent rdf:resource="https://ultraexp.w1.siotex.com/dl/cgi/picorss.html"/>
		<items>
			<rdf:Seq>
EOT

if ($DISPLAY_MAIL) {
	$items = <<EOT;
		<admin:errorReportsTo rdf:resource="mailto:$OWNER_MAIL"/>
$items
EOT
	chomp($items);
}

&lock;

if (open(FH, $LOG_FILE)) {
	my $count = 0;
	my(@art_num, @delflag, @date, @creator, @title, @data);

	foreach (<FH>) {
		s/\n//g;
		tr/\r/\n/;
		(
			$art_num[$count],
			$delflag[$count],
			$date[$count],
			$creator[$count],
			$title[$count],
			$data[$count]
		) = (split("\c@"))[0, 1, 2, 4, 6, 7];
		$count++;
	}

	close(FH);
	&unlock;

	if ($count) {
		# 最新の投稿をフィードの最終更新日とする
		my $feed_date = $date[--$count];
		my $description;

		for (my $i = $count, my $j = 0; $i >= 0 and $j < $DISPLAY_ARTICLES; $i--, $j++) {
			$items .= <<EOT;
				<rdf:li rdf:resource="$BBS_URI?do=goto&amp;art_num=$art_num[$i]"/>
EOT

			if ($delflag[$i] !~ /\d/) {
				# 最新の投稿より後に記事が削除されていたら, その日時をフィードにも反映
				$feed_date = $date[$i] if $date[$i] gt $feed_date;
				$description = $title[$i] = $MSG_3140;
				$description .= $delflag[$i] eq 'XXX' ? $MSG_3150 : $MSG_3160;
				$creator[$i] = $delflag[$i] eq 'XXX' ? 'Guest' : 'Owner';
				$data[$i] = "<p>$description</p>";
			} else {
				escape_chars($title[$i]);
				escape_chars($data[$i]);
				$description = excerpt($data[$i]);
				escape_chars($creator[$i]);
				add_tags($data[$i]);
			}

			convert_w3cdtf($date[$i]);
			$output .= <<EOT;
	<item rdf:about="$BBS_URI?do=goto&amp;art_num=$art_num[$i]">
		<title>$title[$i]</title>
		<link>$BBS_URI?do=goto&amp;art_num=$art_num[$i]</link>
		<description>$description</description>
		<dc:creator>$creator[$i]</dc:creator>
		<dc:date>$date[$i]</dc:date>
		<content:encoded><![CDATA[$data[$i]]]></content:encoded>
	</item>
EOT
		}

		convert_w3cdtf($feed_date);
		$items = <<EOT;
		<dc:date>$feed_date</dc:date>
$items
EOT
		chomp($items);
	} else {
		$output .= set_msg('(None)', 'No article');
	}

	my $lastmod = gmtime((stat($LOG_FILE))[9]);
	$lastmod =~ /^(...) (...) (..) (..:..:..) (....)$/;
	print 'Last-Modified: ' . sprintf("%s, %02d %s %s %s GMT\n", $1, $3, $2, $5, $4);
} else {
	&unlock;
	$output .= set_msg('Fatal error!', 'Unable to open log file.');
}

$output = <<EOT;
<?xml version="1.0" encoding="$CHARSET"?>
<rdf:RDF
	xmlns="http://purl.org/rss/1.0/"
	xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:admin="http://webns.net/mvcb/"
	xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xml:lang="ja">
	<channel rdf:about="$BBS_URI">
		<title>$TITLE</title>
		<link>$BBS_URI</link>
		<description>$FEED_DESCRIPTION</description>
		<dc:creator>$OWNER_NAME</dc:creator>
$items			</rdf:Seq>
		</items>
	</channel>
$output</rdf:RDF>
EOT

if (lc($CHARSET) ne 'shift_jis') {
	my %charset_to_code = (
		'euc-jp' => 'euc',
		'iso-2022-jp' => 'jis',
		'utf-8' => 'utf8',
	);
	require Jcode;
	Jcode::convert(\$output, $charset_to_code{lc($CHARSET)}, 'sjis');
}

print "Content-Type: $CONTENT_TYPE; charset=$CHARSET\n\n$output";

##
 # 特殊文字を実体参照に置き換える.
 #
 # @param 特殊文字の置き換えを行う文字列
 #
sub escape_chars {
	$_[0] =~ s/&/&amp;/g;
	$_[0] =~ s/</&lt;/g;
	$_[0] =~ s/>/&gt;/g;
	$_[0] =~ s/"/&quot;/g;
}

##
 # description 要素の内容となる記事の先頭行を取得する.
 # 記事が引用で始まっている場合は, その次の本文の取得を試みる.
 #
 # @param 記事の文字列
 # @return 記事の先頭行の文字列
 #
sub excerpt {
	my @lines = split("\n", shift);
	/^&gt;/ or $_ and return $_ foreach (@lines);
	$_ and return $_ foreach (@lines);
}

##
 # 引用と段落および改行へのタグ付加.
 #
 # @param タグを付加する文字列
 #
sub add_tags {
	$_[0] =~ s!((s?https?|ftp)://[-.\!~*'()\w;/?:\@&=+$,%#]+)!<a href="$1">$1</a>!g;
	my @source = split("\n", $_[0]);
	my @result = ();
	my($cur_ql, $ql, $i, $is_p);
	$cur_ql = $i = $is_p = 0;

	foreach my $src (@source) {
		$ql = 0;

		# 引用のネスト数を数え, ">" を除去
		while ($src =~ /^&gt\;/) {
			$ql++;
			$src = $';
		}

		if ($ql > $cur_ql) {
			# 前行より引用レベル増加, 現在の段落を終了し新しいブロック引用を開始
			if ($is_p) {
				$result[$i++] .= "</p>";
				$is_p = 0;
			}

			for (my $j = $cur_ql; $j < $ql; $j++) {
				$result[$i++] = "\t" x $j . "<blockquote>";
			}
		} elsif ($ql < $cur_ql) {
			# 前行より引用レベル減少, 現在の段落とブロック引用を終了
			if ($is_p) {
				$result[$i++] .= "</p>";
				$is_p = 0;
			}

			for (my $j = $cur_ql - 1; $j >= $ql; $j--) {
				$result[$i++] = "\t" x $j . "</blockquote>";
			}
		}

		$cur_ql = $ql;

		# 空行を段落の終了に置換し, ループ先頭へ
		if (!$src) {
			if ($is_p) {
				$result[$i++] .= "</p>";
				$is_p = 0;
			}

			next;
		}

		# 新しい段落の開始
		if (!$is_p) {
			$result[$i] = "\t" x $ql . "<p>";
			$is_p = 1;
		}

		# 行末に br 要素を付加しておく
		$result[$i] .= "$src<br />";
	}

	$result[$i++] .= "</p>" if $is_p;

	for (my $j = $ql - 1; $j >= 0; $j--) {
		$result[$i++] = "\t" x $j . "</blockquote>";
	}

	$_[0] = join("\n", @result);
	$_[0] =~ s!<br />(</p>)!$1!g;
}

##
 # ログに記録されている日時を W3CDTF に変換する.
 #
 # @param ログの投稿日文字列
 #
sub convert_w3cdtf {
	$_[0] =~ s!/!-!g;
	$_[0] =~ s! !T!;
	$_[0] .= ":00$TZ";
}

##
 # 記事がない, ログが開けない場合のメッセージを準備する.
 #
 # @param title 要素の内容
 # @param description 要素の内容
 # @return メッセージを含む item 要素
 #
sub set_msg {
	$items .= <<EOT;
				<rdf:li rdf:resource="$BBS_URI"/>
EOT
	return <<EOT;
	<item rdf:about="$BBS_URI">
		<title>$_[0]</title>
		<link>$BBS_URI</link>
		<description>$_[1]</description>
	</item>
EOT
}

##
 # ロック処理.
 #
 # @param void
 #
sub lock {
	if ($LOCKTYPE == 1) {
		open(LOCK, $LOG_FILE);
		flock(LOCK, 1);
	} else {
		open(LOCK, "> $LOCK_DIR/$$");
		close(LOCK);
		my $retry = 0;
		my @files;

		while (1) {
			opendir(DIR, $LOCK_DIR);
			@files = readdir(DIR);
			closedir(DIR);
			last if @files == 3;

			if ($retry >= 3) {
				unlink("$LOCK_DIR/$$");
				print "Status: 503 Service Unavailable\n",
					"Content-Type: text/html\n\n";
				exit;
			}

			sleep(3);
			$retry++;
		}
	}
}

##
 # ロック解除.
 #
 # @param void
 #
sub unlock {
	if ($LOCKTYPE == 1) {
#		flock(LOCK, 8);
		close(LOCK);
	} else {
		unlink("$LOCK_DIR/$$");
	}
}
