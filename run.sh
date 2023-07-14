pip install environment.txt
sudo docker run -d --restart=always --name qsign -p 8080:8080 -e ANDROID_ID=d318e1ae93d7fe2b xzhouqd/qsign:8.9.63
python src/main.py