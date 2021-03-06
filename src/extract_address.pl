#!/usr/bin/perl

use strict;
use Geography::AddressExtract::Japan;
use encoding "utf8", STDIN => "utf8", STDOUT => "utf8";

## load data
#print $ARGV[0];
my $data = "";
open(IN,$ARGV[0]);
while (my $line = <IN>) {
	chomp($line);
	$data = $data . $line;
}
#print $data;

## convert zenkaku number and dash -> hankaku in order to make address extraction easier
#$data =~ tr/０-９ー－/0-9--/;
#print $data;

## extract address
my $res = Geography::AddressExtract::Japan->extract($data);
print map { $_->{"city"} . $_->{"aza"} . $_->{"number"} . "\n"; }@{$res};
