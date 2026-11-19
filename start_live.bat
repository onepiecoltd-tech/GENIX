@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title GENIX LIVE launcher

if not exist live.env (
  copy live.env.example live.env >nul
  echo Da tao live.env — hay mo file nay, dien TIKTOK_USER va ANTHROPIC_API_KEY roi chay lai.
  notepad live.env
  exit /b 0
)
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("live.env") do set "%%a=%%b"

where node >nul 2>nul || (echo Chua cai Node.js 20+ ^(https://nodejs.org^) & pause & exit /b 1)
where python >nul 2>nul || (echo Chua cai Python 3 ^(https://python.org^) & pause & exit /b 1)

if not exist server\node_modules (
  echo Cai thu vien server lan dau...
  pushd server & call npm install --omit=dev & popd
)
python -c "import TikTokLive" >nul 2>nul || (echo Cai thu vien TikTokLive... & python -m pip install TikTokLive)

echo [1/3] Bat server game (cong 8788)...
start "GENIX server" cmd /k "cd /d %~dp0server && set TRUST_PROXY=1 && set PORT=8788 && node server.js"

echo [2/3] Bat cau noi TikTok + AI Thien Dao (cong 8787)...
start "GENIX bridge" cmd /k "cd /d %~dp0 && python live_bridge.py"

echo [3/3] Mo duong ham Cloudflare cho khan gia vao choi cung...
where cloudflared >nul 2>nul
if errorlevel 1 (
  echo   Chua co cloudflared ^(https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/^) — khan gia chua vao choi cung duoc, nhung ban van live binh thuong.
) else (
  del cf.log >nul 2>nul
  start "GENIX tunnel" /min cmd /c "cloudflared tunnel --url http://127.0.0.1:8788 2> cf.log"
  echo   Dang lay link cong khai...
  for /l %%i in (1,1,20) do (
    timeout /t 1 >nul
    for /f "delims=" %%u in ('powershell -NoProfile -Command "$m=Select-String -Path cf.log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue; if($m){$m[0].Matches[0].Value}"') do (
      set "LINK=%%u"
      goto :gotlink
    )
  )
)
:gotlink
if defined LINK (
  echo.
  echo   LINK MOI KHAN GIA: %LINK%/?join=1
  echo   ^(ghim link nay vao binh luan live; da copy vao clipboard^)
  echo %LINK%/?join=1| clip
)
timeout /t 2 >nul
start "" "http://127.0.0.1:8788/"
echo.
echo Trong game: bam 🔴 LIVE -> tick "Cau noi chat that". Dong cac cua so server/bridge/tunnel de dung.
pause
