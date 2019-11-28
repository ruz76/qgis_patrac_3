cd %1/xslt/
rem D:\jre1.8.0_144\bin\java.exe -jar saxon9he.jar %2 gpx.xsl start=%4 end=%5 >> %3
"C:\Program Files\JetBrains\PyCharm Community Edition 2017.3.3\jre64\bin\java.exe" -jar saxon9he.jar %2 gpx.xsl start=%4 end=%5 >> %3
rem set /p temp="Hit enter to continue"