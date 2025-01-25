# PowerShellの実行ポリシーを一時的に変更
$currentPolicy = Get-ExecutionPolicy
try {
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

    # 作業ディレクトリを変更
    Set-Location "C:\ATM_dashboard"

    # Streamlitダッシュボードを起動
    Write-Host "ATM分析ダッシュボードを起動しています..."
    $env:PATH = "$env:PATH;C:\ATM_dashboard\.venv\Scripts"
    streamlit run dashboard.py

    # スクリプト終了時にウィンドウを開いたままにする
    Write-Host "`nダッシュボードが起動しました。このウィンドウは閉じないでください。"
    Write-Host "終了するには、このウィンドウを閉じてください。"
    Read-Host "Enterキーを押すと終了します"
}
finally {
    # 実行ポリシーを元に戻す
    Set-ExecutionPolicy -ExecutionPolicy $currentPolicy -Scope Process -Force
}