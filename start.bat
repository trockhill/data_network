@echo off
chcp 65001 > nul
echo ============================================
echo  データネットワーク可視化ツール
echo ============================================
echo.
echo 依存パッケージをインストール中...
python -m pip install -r requirements.txt -q
echo.
echo サーバーを起動します...
echo ブラウザが自動的に開きます (http://localhost:8000)
echo 終了するには このウィンドウを閉じるか Ctrl+C を押してください
echo.
python app.py
pause
