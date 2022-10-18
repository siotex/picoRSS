#!/usr/bin/perl

##
 # @package picoRSS
 # @version $Id: picorss.cgi,v 1.11 2010/01/23 09:15:40 matsuyan Exp $
 # @copyright Copyright (C) 2006-2010 Siotex <https://www.siotex.com/>
 #

# --- ���ɉ����ݒ肷�鍀�� -----

# picoBBS �{�̂� define.cgi �̃p�X
require './define.cgi';

# �o�͎��� MIME �^�C�v. �f�t�H���g�� text/xml
# ���� application/xml �� application/rdf+xml �Ȃ�
my $CONTENT_TYPE = 'text/xml';

# �t�B�[�h�̕����R�[�h. �f�t�H���g�� UTF-8 ����������
# ������ Shift_JIS �ȊO�ŏo�͂���ɂ� Jcode.pm ���K�{
my $CHARSET = 'UTF-8';

# �t�B�[�h�̊T�v. 500 �o�C�g�ȓ��Ɏ��߂邱�Ƃ𐄏�
my $FEED_DESCRIPTION = "$TITLE�ɓ��e���ꂽ�ŐV�̋L����z�M���Ă��܂�";

# �f���� URI. http(s):// ����n�߂�
my $BBS_URI = "http://www.example.com/~username/cgi-bin/picobbs.cgi";

# �Ǘ��҃��[�� �A�h���X�o�̗͂L��. �o�͂���Ȃ� 1 ��
# spam �h�~�̊ϓ_����̓f�t�H���g�� 0 �𐄏�
my $DISPLAY_MAIL = 0;

# �z�M����V���L���̍ő吔. �f�t�H���g�͌f���̕\�����Ɠ���
my $DISPLAY_ARTICLES = $VIEW_CNT_MAX;

# UTC ����̎���. ���{���Ԃ���Ƃ���Ȃ�f�t�H���g�� +09:00
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
		# �ŐV�̓��e���t�B�[�h�̍ŏI�X�V���Ƃ���
		my $feed_date = $date[--$count];
		my $description;

		for (my $i = $count, my $j = 0; $i >= 0 and $j < $DISPLAY_ARTICLES; $i--, $j++) {
			$items .= <<EOT;
				<rdf:li rdf:resource="$BBS_URI?do=goto&amp;art_num=$art_num[$i]"/>
EOT

			if ($delflag[$i] !~ /\d/) {
				# �ŐV�̓��e����ɋL�����폜����Ă�����, ���̓������t�B�[�h�ɂ����f
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
 # ���ꕶ�������̎Q�Ƃɒu��������.
 #
 # @param ���ꕶ���̒u���������s��������
 #
sub escape_chars {
	$_[0] =~ s/&/&amp;/g;
	$_[0] =~ s/</&lt;/g;
	$_[0] =~ s/>/&gt;/g;
	$_[0] =~ s/"/&quot;/g;
}

##
 # description �v�f�̓��e�ƂȂ�L���̐擪�s���擾����.
 # �L�������p�Ŏn�܂��Ă���ꍇ��, ���̎��̖{���̎擾�����݂�.
 #
 # @param �L���̕�����
 # @return �L���̐擪�s�̕�����
 #
sub excerpt {
	my @lines = split("\n", shift);
	/^&gt;/ or $_ and return $_ foreach (@lines);
	$_ and return $_ foreach (@lines);
}

##
 # ���p�ƒi������щ��s�ւ̃^�O�t��.
 #
 # @param �^�O��t�����镶����
 #
sub add_tags {
	$_[0] =~ s!((s?https?|ftp)://[-.\!~*'()\w;/?:\@&=+$,%#]+)!<a href="$1">$1</a>!g;
	my @source = split("\n", $_[0]);
	my @result = ();
	my($cur_ql, $ql, $i, $is_p);
	$cur_ql = $i = $is_p = 0;

	foreach my $src (@source) {
		$ql = 0;

		# ���p�̃l�X�g���𐔂�, ">" ������
		while ($src =~ /^&gt\;/) {
			$ql++;
			$src = $';
		}

		if ($ql > $cur_ql) {
			# �O�s�����p���x������, ���݂̒i�����I�����V�����u���b�N���p���J�n
			if ($is_p) {
				$result[$i++] .= "</p>";
				$is_p = 0;
			}

			for (my $j = $cur_ql; $j < $ql; $j++) {
				$result[$i++] = "\t" x $j . "<blockquote>";
			}
		} elsif ($ql < $cur_ql) {
			# �O�s�����p���x������, ���݂̒i���ƃu���b�N���p���I��
			if ($is_p) {
				$result[$i++] .= "</p>";
				$is_p = 0;
			}

			for (my $j = $cur_ql - 1; $j >= $ql; $j--) {
				$result[$i++] = "\t" x $j . "</blockquote>";
			}
		}

		$cur_ql = $ql;

		# ��s��i���̏I���ɒu����, ���[�v�擪��
		if (!$src) {
			if ($is_p) {
				$result[$i++] .= "</p>";
				$is_p = 0;
			}

			next;
		}

		# �V�����i���̊J�n
		if (!$is_p) {
			$result[$i] = "\t" x $ql . "<p>";
			$is_p = 1;
		}

		# �s���� br �v�f��t�����Ă���
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
 # ���O�ɋL�^����Ă�������� W3CDTF �ɕϊ�����.
 #
 # @param ���O�̓��e��������
 #
sub convert_w3cdtf {
	$_[0] =~ s!/!-!g;
	$_[0] =~ s! !T!;
	$_[0] .= ":00$TZ";
}

##
 # �L�����Ȃ�, ���O���J���Ȃ��ꍇ�̃��b�Z�[�W����������.
 #
 # @param title �v�f�̓��e
 # @param description �v�f�̓��e
 # @return ���b�Z�[�W���܂� item �v�f
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
 # ���b�N����.
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
 # ���b�N����.
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
