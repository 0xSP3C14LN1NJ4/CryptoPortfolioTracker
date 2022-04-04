#!/bin/bash

echo "Creating necessary files"
touch transactions.json
touch transfers.json
touch balances.json
echo -e "Done!\n"


echo "Installing required libraries"
pip install -r requirements.txt
echo -e "Done!\n"


echo "Setting up Gemini API keys (you must already have created an API key for your main and/or a sandbox account)"

echo "Enter your Gemini API key (leave blank if you only want to use a Sandbox account):"
read api_key
echo $api_key > api-key.txt

echo "Enter your Gemini API secret (leave blank if you only want to use a Sandbox account):"
read api_secret
echo $api_secret > api-secret.txt

echo "Enter your Gemini Sandbox API key (leave blank if you only want to use your main account):"
read api_key_test
echo $api_key_test > api-key-test.txt

echo "Enter your Gemini Sandbox API secret (leave blank if you only want to use your main account):"
read api_secret_test
echo $api_secret_test > api-secret-test.txt
echo -e "Done!\n"


echo "Setting up the Cryptowatch API key (you must already have created an API key on cryptowat.ch)"
echo "Enter your Cryptowatch API key:"
read api_key_cw
echo $api_key_cw > api-key-cw.txt
echo -e "Done!\n"