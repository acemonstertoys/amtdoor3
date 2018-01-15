<?php
error_reporting(E_ALL);
ini_set('display_errors', true);

require(".codez.inc");

// Something in the certs for ssl.acemonstertoys.org and new OpenSSL/PHP is unhappy
// OpenSSL works find with helloworld.letsencrypt.org, the same cert chain, though...
$legacySSLStreamContext = stream_context_create([
  'ssl' => [
      'verify_peer'      => false,
      'verify_peer_name' => false
  ]
]);

$time=time();
$hash = sha1(sha1($time).sha1($secret));

$out = json_decode(file_get_contents("$url?ts=$time&hs=$hash", false, $legacySSLStreamContext));

//print_r($out);

if($out[0] == "OK") {
	$rfids = $out[1];
	if(count($rfids) < 10) {
		print("ERROR! Only ".count($rfids)." rfid tags...I'm expecting at least 10 of them. Aborting\n");
		die();
	}

	print("Got ".count($rfids)." tags\n");
	
	$str = "";
	foreach($rfids as $rfid) {
		$str .= $rfid."\n";
//		$str .= '"'.$rfid.'", '."\n";
	}
	file_put_contents("rfid.inc", $str);
} else {
print("error getting rfids: ".print_r($out,TRUE));
}
