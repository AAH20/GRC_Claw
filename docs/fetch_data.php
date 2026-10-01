<?php
/**
 * Simple PHP script to fetch financial data without using cURL
 * 
 * Note: This is a basic implementation, and accessing APIs might be subject
 * to rate limiting or terms of service restrictions.
 */

$url = 'https://api.investing.com/api/financialdata/1068317/historical/chart/?interval=PT1M&pointscount=60';

// Initialize cURL session
$ch = curl_init();

// Set cURL options
curl_setopt($ch, CURLOPT_URL, $url); // Set the URL
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true); // Return the transfer as a string
curl_setopt($ch, CURLOPT_HEADER, false); // Don't include the header in the output
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true); // Follow redirects
curl_setopt($ch, CURLOPT_ENCODING, ""); // Handle all encodings
curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'); // Set a user agent
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 120); // Timeout on connect
curl_setopt($ch, CURLOPT_TIMEOUT, 120); // Timeout on response
curl_setopt($ch, CURLOPT_MAXREDIRS, 10); // Stop after 10 redirects
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true); // Verify SSL certificate
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2); // Check the existence of a common name and also verify that it matches the hostname provided

// Execute the cURL session
$response = curl_exec($ch);

// Check for cURL errors
if (curl_errno($ch)) {
    echo 'cURL error: ' . curl_error($ch);
    curl_close($ch);
    exit;
}

// Close the cURL session
curl_close($ch);

// Output the raw response
echo "Raw Response:\n";
echo $response;
echo "\n\n";

// Attempt to decode JSON response (assuming it's JSON based on the URL)
$data = json_decode($response, true); // true for associative array

// Check for JSON decoding errors
if (json_last_error() !== JSON_ERROR_NONE) {
    echo "JSON Decode Error: " . json_last_error_msg() . "\n";
} else {
    echo "Decoded Data (PHP Array):\n";
    print_r($data);
    
    // Explain the data structure
    echo "\nData structure explanation:\n";
    echo " - Each array in 'data' represents a single time point with:\n";
    echo "   [0]: Timestamp (milliseconds since epoch)\n";
    echo "   [1]: Open price\n";
    echo "   [2]: High price\n";
    echo "   [3]: Low price\n";
    echo "   [4]: Close price\n";
    echo "   [5]: Volume\n";
    echo "   [6]: Additional metric (possibly change or another indicator)\n";
}

?> 